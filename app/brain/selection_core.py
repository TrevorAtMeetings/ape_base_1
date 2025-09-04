"""
Selection Core Module
=====================
Main SelectionIntelligence class - orchestrates pump selection process
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional

from ..data_models import SiteRequirements, PumpEvaluation, ExclusionReason
from ..process_logger import process_logger
from .pump_evaluator import PumpEvaluator
from .proximity_searcher import ProximitySearcher

logger = logging.getLogger(__name__)


class SelectionIntelligence:
    """Intelligence for pump selection and ranking"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        
        # Initialize sub-components
        self.pump_evaluator = PumpEvaluator(brain)
        self.proximity_searcher = ProximitySearcher(brain)
        
        # Brain system selection parameters
        # Legacy uses point-based scoring, not percentage weights
        self.scoring_weights = {
            'bep_proximity': 45,  # Max points (was 40% weight)
            'efficiency': 35,     # Max points (was 30% weight)
            'head_margin': 20,    # Max points (was 15% weight)
            'npsh_margin': 0      # Removed in v6.0 (informational only, no gates)
        }
        
        # Operating constraints
        self.min_trim_percent = 85.0
        self.max_trim_percent = 100.0
        self.npsh_safety_factor = 1.5
        
        # More realistic QBP ranges for industrial applications
        # The old 60-130% range was too restrictive for practical pump selection
        self.qbp_min_percent = 50.0  # Allow pumps running at 50% of BEP (more realistic)
        self.qbp_max_percent = 200.0  # Allow pumps running at 200% of BEP (more realistic)
        
        # FIXED: Head oversizing constraints - much more realistic thresholds
        self.head_oversizing_threshold = 150.0  # % above requirement triggers penalty (was 40%)
        self.severe_oversizing_threshold = 300.0  # % above requirement for severe penalty (was 70%)
    
    def find_best_pumps(self, flow: float, head: float, 
                       constraints: Optional[Dict[str, Any]] = None, 
                       include_exclusions: bool = False) -> Dict[str, Any]:
        """
        Find best pumps for given conditions with optional exclusion details.
        
        Args:
            flow: Required flow rate (m³/hr)
            head: Required head (m)
            constraints: Optional constraints
            include_exclusions: If True, return detailed exclusion data
        
        Returns:
            Dictionary with 'ranked_pumps' and optionally 'exclusion_details'
        """
        if not self.brain.repository:
            logger.error("Repository not available for pump selection")
            return {'ranked_pumps': [], 'exclusion_details': None}
        
        constraints = constraints or {}
        
        # CRITICAL DEBUG: Log Brain selection entry point
        logger.error(f"🎯 [BRAIN ENTRY] find_best_pumps called: flow={flow}, head={head}")
        logger.error(f"🎯 [BRAIN ENTRY] Constraints: {constraints}")
        
        # Set pump selection context for descriptive log filename
        process_logger.set_pump_selection_context(flow, head)
        
        process_logger.log_section("BRAIN SELECTION INTELLIGENCE")
        process_logger.log(f"Target Operating Point: {flow:.2f} m³/hr @ {head:.2f} m")
        process_logger.log_data("Constraints", constraints)
        
        # Get all pumps from repository
        all_pumps = self.brain.repository.get_pump_models()
        if not all_pumps:
            logger.warning("No pump models available in repository")
            process_logger.log("ERROR: No pump models in repository!", "ERROR")
            return {'ranked_pumps': [], 'exclusion_details': None}
        
        # Log all pumps loaded from repository
        process_logger.log_separator()
        process_logger.log(f"REPOSITORY: Loaded {len(all_pumps)} pumps")
        for pump in all_pumps[:10]:  # Log first 10 pumps as sample
            specs = pump.get('specifications', {})
            process_logger.log(f"  - {pump.get('pump_code', 'N/A')}: "
                             f"BEP={specs.get('bep_flow_m3hr', 0):.1f}@{specs.get('bep_head_m', 0):.1f}m, "
                             f"Type={pump.get('pump_type', 'N/A')}")
        if len(all_pumps) > 10:
            process_logger.log(f"  ... and {len(all_pumps) - 10} more pumps")
        
        # COMPREHENSIVE HC PUMP PIPELINE ANALYSIS
        logger.error(f"🔍 [PIPELINE STEP 1] Repository loaded {len(all_pumps)} total pumps")
        
        # Log repository pump analysis
        logger.debug(f"[PIPELINE] Repository loaded {len(all_pumps)} total pumps")
        
        # Sample pump analysis - show first 10 for debugging
        sample_pumps = all_pumps[:10]
        for pump in sample_pumps:
            specs = pump.get('specifications', {})
            curves = pump.get('curves', [])
            logger.debug(f"[PIPELINE] {pump.get('pump_code', 'Unknown')}: BEP {specs.get('bep_flow_m3hr', 0)} m³/hr @ {specs.get('bep_head_m', 0)}m, {len(curves)} curves")
        
        # Debug: Log pump series analysis
        pump_series_count = {}
        for pump in all_pumps:
            pump_code = str(pump.get('pump_code', 'Unknown'))
            # Extract pump series (first part before space or number)
            series = pump_code.split()[0] if pump_code.split() else 'Unknown'
            pump_series_count[series] = pump_series_count.get(series, 0) + 1
        
        logger.debug(f"[DEBUG] Pump series breakdown: {dict(list(pump_series_count.items())[:10])}")
        
        # INTELLIGENT PRE-FILTERING: Only evaluate pumps in reasonable flow AND head range
        # This prevents evaluating 0.1 m³/hr pumps for 350 m³/hr applications
        # AND prevents 100m+ head pumps for 50m applications (excessive trim)
        min_flow_threshold = max(flow * 0.4, 5.0)  # At least 40% of required flow, minimum 5 m³/hr
        max_flow_threshold = flow * 3.0  # Maximum 300% of required flow
        
        # CRITICAL FIX: Add head-based pre-filtering to prevent excessive trim
        # ADJUSTED: More permissive thresholds to allow for impeller trimming effects
        # Trimming can increase head output, so lower BEP heads can still meet requirements
        min_head_threshold = head * 0.3   # Minimum 30% of required head (was 80% - too restrictive!)
        max_head_threshold = head * 2.0   # Maximum 200% of required head (increased from 160%)
        
        process_logger.log_separator()
        process_logger.log("PRE-FILTERING STAGE")
        process_logger.log(f"Flow Range: [{min_flow_threshold:.1f} - {max_flow_threshold:.1f}] m³/hr")
        process_logger.log(f"Head Range: [{min_head_threshold:.1f} - {max_head_threshold:.1f}] m")
        
        pump_models = []
        pre_filtered_count = 0
        flow_filtered_count = 0
        head_filtered_count = 0
        flow_excluded_list = []
        head_excluded_list = []
        
        for pump in all_pumps:
            specs = pump.get('specifications', {})
            bep_flow = specs.get('bep_flow_m3hr', 0)
            bep_head = specs.get('bep_head_m', 0)
            pump_code = pump.get('pump_code', 'Unknown')
            pump_type = pump.get('pump_type', 'Unknown')
            
            # Comprehensive pre-filtering decision logging for ALL pumps
            process_logger.log_separator()
            process_logger.log(f"PRE-FILTER ANALYSIS: {pump_code}")
            
            # Flow compatibility check
            flow_ok = bep_flow > 0 and min_flow_threshold <= bep_flow <= max_flow_threshold
            process_logger.log(f"  BEP Flow Check: {bep_flow:.1f} vs [{min_flow_threshold:.1f}-{max_flow_threshold:.1f}] → {'PASS' if flow_ok else 'FAIL'}")
            
            if not flow_ok:
                logger.debug(f"[FLOW PRE-FILTER] {pump_code} EXCLUDED: BEP {bep_flow} not in range {min_flow_threshold:.1f}-{max_flow_threshold:.1f}")
                
                if bep_flow <= 0:
                    process_logger.log(f"  → EXCLUSION REASON: Invalid BEP flow data (≤0)")
                elif bep_flow < min_flow_threshold:
                    process_logger.log(f"  → EXCLUSION REASON: Pump too small - BEP flow {bep_flow:.1f} < {min_flow_threshold:.1f} m³/hr ({0.4*100:.0f}% of target)")
                else:
                    process_logger.log(f"  → EXCLUSION REASON: Pump too large - BEP flow {bep_flow:.1f} > {max_flow_threshold:.1f} m³/hr ({3.0*100:.0f}% of target)")
                
                flow_filtered_count += 1
                flow_excluded_list.append(f"{pump_code}: BEP={bep_flow:.1f} m³/hr")
                continue
            
            # Head compatibility check
            head_ok = not (bep_head > 0 and not (min_head_threshold <= bep_head <= max_head_threshold))
            process_logger.log(f"  BEP Head Check: {bep_head:.1f} vs [{min_head_threshold:.1f}-{max_head_threshold:.1f}] → {'PASS' if head_ok else 'FAIL'}")
            
            if not head_ok:
                logger.debug(f"[HEAD PRE-FILTER] {pump_code} EXCLUDED: BEP {bep_head:.1f}m not in range {min_head_threshold:.1f}-{max_head_threshold:.1f}m")
                logger.debug(f"[HEAD PRE-FILTER] {pump_code}: Required head {head}m, thresholds: {min_head_threshold:.1f}-{max_head_threshold:.1f}m")
                
                if bep_head < min_head_threshold:
                    process_logger.log(f"  → EXCLUSION REASON: Insufficient head - BEP head {bep_head:.1f} < {min_head_threshold:.1f} m ({0.3*100:.0f}% of target)")
                else:
                    process_logger.log(f"  → EXCLUSION REASON: Excessive head - BEP head {bep_head:.1f} > {max_head_threshold:.1f} m ({2.0*100:.0f}% of target)")
                
                head_filtered_count += 1
                head_excluded_list.append(f"{pump_code}: BEP={bep_head:.1f} m")
                continue
            
            # Pump type filtering (if constraint applied)
            type_constraint = constraints.get('pump_type', 'GENERAL')
            if type_constraint != 'GENERAL':
                type_ok = pump_type.upper() == type_constraint.upper()
                process_logger.log(f"  Type Filter: {pump_type} vs {type_constraint} → {'PASS' if type_ok else 'FAIL'}")
                if not type_ok:
                    process_logger.log(f"  → EXCLUSION REASON: Pump type mismatch - required {type_constraint}, got {pump_type}")
                    # Note: Type filtering handled elsewhere in code, this is just for logging visibility
            
            # Pump passed all pre-filters
            process_logger.log(f"  → RESULT: ✅ PASSED PRE-FILTERING - proceeding to evaluation")
            
            # Log successful pre-filtering
            logger.debug(f"[PRE-FILTER] {pump_code} PASSED PRE-FILTERING")
                
            pump_models.append(pump)
        
        pre_filtered_count = flow_filtered_count + head_filtered_count
        logger.info(f"Smart pre-filtering: {len(pump_models)} pumps selected from {len(all_pumps)} total")
        logger.info(f"Filtered out: {flow_filtered_count} flow-incompatible + {head_filtered_count} head-incompatible = {pre_filtered_count} total")
        
        # Log pre-filtering results
        process_logger.log_separator()
        process_logger.log("PRE-FILTERING RESULTS:")
        process_logger.log(f"  Total Repository Pumps: {len(all_pumps)}")
        process_logger.log(f"  Flow Range Excluded: {flow_filtered_count} pumps")
        if flow_excluded_list and len(flow_excluded_list) <= 10:
            for pump_info in flow_excluded_list:
                process_logger.log(f"    - {pump_info}")
        elif flow_excluded_list:
            for pump_info in flow_excluded_list[:5]:
                process_logger.log(f"    - {pump_info}")
            process_logger.log(f"    ... and {len(flow_excluded_list) - 5} more")
        
        process_logger.log(f"  Head Range Excluded: {head_filtered_count} pumps")
        if head_excluded_list and len(head_excluded_list) <= 10:
            for pump_info in head_excluded_list:
                process_logger.log(f"    - {pump_info}")
        elif head_excluded_list:
            for pump_info in head_excluded_list[:5]:
                process_logger.log(f"    - {pump_info}")
            process_logger.log(f"    ... and {len(head_excluded_list) - 5} more")
        
        process_logger.log(f"  Pumps Remaining for Evaluation: {len(pump_models)}")
        
        logger.info(f"Smart pre-filtering: {len(pump_models)} pumps selected from {len(all_pumps)} total (filtered out {pre_filtered_count} inappropriate pumps)")
        
        feasible_pumps = []
        excluded_pumps = []
        exclusion_summary = {}
        
        process_logger.log_separator()
        process_logger.log("INDIVIDUAL PUMP EVALUATION")
        process_logger.log(f"Evaluating {len(pump_models)} pumps...")
        
        # PASS 1: Evaluate all pumps without detailed logging to determine rankings
        pump_evaluations = []  # Store all evaluations for ranking calculation
        
        for pump_data in pump_models:
            try:
                # Extract pump code for this iteration
                pump_code = pump_data.get('pump_code', 'Unknown')
                
                # Apply pump type constraint early
                if constraints.get('pump_type') and constraints['pump_type'] != 'GENERAL':
                    pump_type = pump_data.get('pump_type', '').upper()
                    constraint_type = constraints['pump_type'].upper()
                    
                    # DEBUG: Log pump type filtering 
                    logger.debug(f"[PUMP TYPE FILTER] {pump_code}: pump_type='{pump_type}', constraint='{constraint_type}'")
                    
                    if pump_type != constraint_type:
                        # DEBUG: Log pump exclusions due to pump type
                        logger.debug(f"[PUMP TYPE FILTER] {pump_code}: EXCLUDED - type '{pump_type}' != constraint '{constraint_type}'")
                        
                        if include_exclusions:
                            excluded_pumps.append({
                                'pump_code': pump_data.get('pump_code'),
                                'pump_name': pump_data.get('pump_name', ''),
                                'exclusion_reasons': ['Wrong pump type'],
                                'score_components': {}
                            })
                            exclusion_summary['Wrong pump type'] = exclusion_summary.get('Wrong pump type', 0) + 1
                        continue
                else:
                    # DEBUG: Log when pump type constraint is bypassed
                    constraint_value = constraints.get('pump_type', 'None')
                    logger.debug(f"[PUMP TYPE FILTER] {pump_code}: BYPASSED pump type filter (constraint='{constraint_value}')")
                
                # CRITICAL: Evaluate physical capability at specific operating point
                logger.debug(f"[SELECTION DEBUG] {pump_code}: Starting evaluation for {flow} m³/hr @ {head}m")
                specs = pump_data.get('specifications', {})
                logger.debug(f"[SELECTION DEBUG] {pump_code}: BEP {specs.get('bep_flow_m3hr', 0)} m³/hr @ {specs.get('bep_head_m', 0)}m")
                logger.debug(f"[SELECTION DEBUG] {pump_code}: Max impeller: {specs.get('max_impeller_diameter_mm', 0)}mm")
                
                # PASS 1: Evaluate pump without detailed logging
                evaluation = self.pump_evaluator.evaluate_single_pump(pump_data, flow, head, pump_code)
                
                # Store evaluation with pump data for ranking calculation
                pump_evaluations.append({
                    'pump_data': pump_data,
                    'pump_code': pump_code,
                    'evaluation': evaluation,
                    'flow': flow,
                    'head': head
                })
                
                # Apply additional constraints
                if constraints.get('max_power_kw'):
                    max_power = constraints['max_power_kw']
                    if evaluation.get('power_kw', 0) > max_power:
                        evaluation['feasible'] = False
                        evaluation['exclusion_reasons'].append('Power exceeds limit')
                
            except Exception as e:
                logger.error(f"Error evaluating pump {pump_data.get('pump_code')}: {str(e)}")
                if include_exclusions:
                    excluded_pumps.append({
                        'pump_code': pump_data.get('pump_code'),
                        'pump_name': pump_data.get('pump_name', ''),
                        'exclusion_reasons': [f'Evaluation error: {str(e)}'],
                        'score_components': {}
                    })
                    exclusion_summary['Evaluation error'] = exclusion_summary.get('Evaluation error', 0) + 1
                continue
        
        # Separate feasible and excluded pumps
        for pump_eval in pump_evaluations:
            evaluation = pump_eval['evaluation']
            pump_data = pump_eval['pump_data']
            pump_code = pump_eval['pump_code']
            
            # Log evaluation results
            if evaluation.get('feasible', False):
                logger.debug(f"[EVALUATION] {pump_code}: PASSED - feasible with score {evaluation.get('total_score', 0):.1f}")
            else:
                logger.debug(f"[EVALUATION] {pump_code}: FAILED - exclusion reasons: {evaluation.get('exclusion_reasons', [])}")
                logger.debug(f"[EVALUATION] {pump_code}: Score components: {evaluation.get('score_components', {})}")
            
            if evaluation.get('feasible', False):
                feasible_pumps.append(evaluation)
                
                # Log feasible pump evaluation with detailed logging
                process_logger.log_pump_evaluation(pump_code, pump_data, flow, head, evaluation)
                # Add separator after each pump evaluation
                process_logger.log("." * 80)
            else:
                # Track exclusions with authentic Brain reasons
                if include_exclusions:
                    exclusion_info = {
                        'pump_code': pump_data.get('pump_code'),
                        'pump_name': pump_data.get('pump_name', ''),
                        'exclusion_reasons': evaluation.get('exclusion_reasons', []),
                        'score_components': evaluation.get('score_components', {})
                    }
                    excluded_pumps.append(exclusion_info)
                    
                    # Build authentic exclusion summary
                    for reason in evaluation.get('exclusion_reasons', []):
                        exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1
                
                # Log excluded pump evaluation with detailed logging
                process_logger.log_pump_evaluation(pump_code, pump_data, flow, head, evaluation)
                # Add separator after each pump evaluation
                process_logger.log("." * 80)
        
        # Sort by score (descending)
        feasible_pumps.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        # Prepare result structure
        max_results = constraints.get('max_results', 5)
        result = {
            'ranked_pumps': feasible_pumps[:max_results]
        }
        
        # Add authentic exclusion details if requested
        if include_exclusions:
            # Sort excluded pumps by best score components to show "almost suitable" pumps first
            excluded_pumps.sort(key=lambda x: sum(x.get('score_components', {}).values()), reverse=True)
            
            exclusion_details = {
                'excluded_pumps': excluded_pumps[:20],  # Top 20 excluded for analysis
                'exclusion_summary': exclusion_summary,
                'total_evaluated': len(all_pumps),
                'feasible_count': len(feasible_pumps),
                'excluded_count': len(excluded_pumps)
            }
            result.update({'exclusion_details': exclusion_details})
        
        # Log final rankings
        process_logger.log_final_rankings(feasible_pumps, excluded_pumps)
        
        return result
    
    def rank_pumps(self, pump_list: List[str], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank pumps based on criteria.
        
        Args:
            pump_list: List of pump codes
            criteria: Ranking criteria
        
        Returns:
            Ranked list with analysis
        """
        return self.proximity_searcher.rank_pumps(pump_list, criteria)
    
    def find_pumps_by_bep_proximity(self, flow: float, head: float, 
                                   pump_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Enhanced BEP proximity search with pump-type-specific weighting.
        Uses specific speed to classify pumps and apply appropriate distance metrics.
        
        Args:
            flow: Required flow rate (m³/hr)
            head: Required head (m)
            pump_type: Optional pump type filter
        
        Returns:
            List of top 20 pumps with enhanced scoring based on hydraulic type
        """
        return self.proximity_searcher.find_pumps_by_bep_proximity(flow, head, pump_type)