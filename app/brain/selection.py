"""
Selection Intelligence Module
=============================
Brain-based pump selection intelligence
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
from ..data_models import SiteRequirements, PumpEvaluation, ExclusionReason

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
        
        # Get all pumps from repository
        all_pumps = self.brain.repository.get_pump_models()
        if not all_pumps:
            logger.warning("No pump models available in repository")
            return {'ranked_pumps': [], 'exclusion_details': None}
        
        # COMPREHENSIVE HC PUMP PIPELINE ANALYSIS
        logger.error(f"🔍 [PIPELINE STEP 1] Repository loaded {len(all_pumps)} total pumps")
        
        # Check if HC pumps are in repository - INCLUDING 8P models
        target_hc_pumps = [p for p in all_pumps if p.get('pump_code') in ['32 HC 6P', '30 HC 6P', '28 HC 6P', '32 HC 8P']]
        logger.error(f"🔍 [PIPELINE STEP 1] Found {len(target_hc_pumps)} target HC pumps in repository")
        
        # Check specifically for 32 HC 8P which user says should handle 2000 m³/hr @ 100m
        hc_8p_pump = [p for p in all_pumps if p.get('pump_code') == '32 HC 8P']
        if hc_8p_pump:
            specs = hc_8p_pump[0].get('specifications', {})
            logger.error(f"🎯 [32 HC 8P CHECK] Found 32 HC 8P in database:")
            logger.error(f"🎯 [32 HC 8P CHECK] BEP: {specs.get('bep_flow_m3hr', 0)} m³/hr @ {specs.get('bep_head_m', 0)}m")
            logger.error(f"🎯 [32 HC 8P CHECK] Max impeller: {specs.get('max_impeller_diameter_mm', 0)}mm")
            logger.error(f"🎯 [32 HC 8P CHECK] Pump type: {hc_8p_pump[0].get('pump_type', 'Unknown')}")
        else:
            logger.error(f"🚨 [32 HC 8P CHECK] 32 HC 8P NOT FOUND in repository!")
        
        if not target_hc_pumps:
            all_hc = [p for p in all_pumps if 'HC' in str(p.get('pump_code', ''))]
            logger.error(f"🚨 [PIPELINE STEP 1] NO target HC pumps! Found {len(all_hc)} other HC pumps: {[p.get('pump_code') for p in all_hc[:5]]}")
            return {'ranked_pumps': [], 'exclusion_details': None}
        
        # Log HC pump details
        for target_pump in target_hc_pumps:
            specs = target_pump.get('specifications', {})
            curves = target_pump.get('curves', [])
            logger.error(f"🔍 [PIPELINE STEP 1] {target_pump.get('pump_code')}: BEP {specs.get('bep_flow_m3hr', 0)} m³/hr @ {specs.get('bep_head_m', 0)}m, {len(curves)} curves")
        
        # Debug: Check if 6 WLN 18A is in loaded pumps
        wln_pumps = [p for p in all_pumps if "6 WLN 18A" in str(p.get('pump_code', ''))]
        logger.error(f"[DEBUG] Found {len(wln_pumps)} 6 WLN 18A pumps in {len(all_pumps)} total loaded pumps")
        for pump in wln_pumps:
            logger.error(f"[DEBUG] 6 WLN 18A found: code='{pump.get('pump_code')}' name='{pump.get('pump_name')}'")
        
        # Also check variations
        wln_variations = [p for p in all_pumps if "WLN" in str(p.get('pump_code', '')).upper()]
        logger.error(f"[DEBUG] Found {len(wln_variations)} WLN pumps total")
        for pump in wln_variations[:5]:  # Show first 5
            logger.error(f"[DEBUG] WLN variant: '{pump.get('pump_code')}'")  
        
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
        
        pump_models = []
        pre_filtered_count = 0
        flow_filtered_count = 0
        head_filtered_count = 0
        
        for pump in all_pumps:
            specs = pump.get('specifications', {})
            bep_flow = specs.get('bep_flow_m3hr', 0)
            bep_head = specs.get('bep_head_m', 0)
            
            # Pre-filter by flow range
            pump_code = pump.get('pump_code', 'Unknown')
            if not (bep_flow > 0 and min_flow_threshold <= bep_flow <= max_flow_threshold):
                if pump_code in ['32 HC 6P', '30 HC 6P', '28 HC 6P', '32 HC 8P']:
                    logger.error(f"🚨 [FLOW PRE-FILTER] {pump_code} EXCLUDED: BEP {bep_flow} not in range {min_flow_threshold:.1f}-{max_flow_threshold:.1f}")
                flow_filtered_count += 1
                continue
            
            # Head compatibility check with trimming consideration
            # Allow pumps with lower BEP heads since trimming can increase head output
            if bep_head > 0 and not (min_head_threshold <= bep_head <= max_head_threshold):
                if pump_code in ['32 HC 6P', '30 HC 6P', '28 HC 6P', '32 HC 8P']:
                    logger.error(f"🚨 [HEAD PRE-FILTER] {pump_code} EXCLUDED: BEP {bep_head:.1f}m not in range {min_head_threshold:.1f}-{max_head_threshold:.1f}m")
                    logger.error(f"🚨 [HEAD PRE-FILTER] {pump_code}: Required head {head}m, thresholds: {min_head_threshold:.1f}-{max_head_threshold:.1f}m")
                head_filtered_count += 1
                logger.debug(f"[PRE-FILTER] {pump_code}: Head incompatible - BEP {bep_head:.1f}m outside range {min_head_threshold:.1f}-{max_head_threshold:.1f}m")
                continue
            
            # HC pump passed pre-filtering
            if pump_code in ['32 HC 6P', '30 HC 6P', '28 HC 6P', '32 HC 8P']:
                logger.error(f"✅ [PRE-FILTER] {pump_code} PASSED PRE-FILTERING!")
                
            pump_models.append(pump)
        
        pre_filtered_count = flow_filtered_count + head_filtered_count
        logger.info(f"Smart pre-filtering: {len(pump_models)} pumps selected from {len(all_pumps)} total")
        logger.info(f"Filtered out: {flow_filtered_count} flow-incompatible + {head_filtered_count} head-incompatible = {pre_filtered_count} total")
        
        logger.info(f"Smart pre-filtering: {len(pump_models)} pumps selected from {len(all_pumps)} total (filtered out {pre_filtered_count} inappropriate pumps)")
        
        feasible_pumps = []
        excluded_pumps = []
        exclusion_summary = {}
        
        for pump_data in pump_models:
            try:
                # Apply pump type constraint early
                pump_code = pump_data.get('pump_code', 'Unknown')
                if constraints.get('pump_type') and constraints['pump_type'] != 'GENERAL':
                    pump_type = pump_data.get('pump_type', '').upper()
                    constraint_type = constraints['pump_type'].upper()
                    
                    # DEBUG: Log pump type filtering for HC pumps
                    if pump_code in ['32 HC 6P', '30 HC 6P', '28 HC 6P']:
                        logger.error(f"🔍 [PUMP TYPE FILTER] {pump_code}: pump_type='{pump_type}', constraint='{constraint_type}'")
                    
                    if pump_type != constraint_type:
                        # DEBUG: Log HC pump exclusions due to pump type
                        if pump_code in ['32 HC 6P', '30 HC 6P', '28 HC 6P']:
                            logger.error(f"🚨 [PUMP TYPE FILTER] {pump_code}: EXCLUDED - type '{pump_type}' != constraint '{constraint_type}'")
                        
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
                    if pump_code in ['32 HC 6P', '30 HC 6P', '28 HC 6P']:
                        constraint_value = constraints.get('pump_type', 'None')
                        logger.error(f"✅ [PUMP TYPE FILTER] {pump_code}: BYPASSED pump type filter (constraint='{constraint_value}')")
                
                # CRITICAL: Evaluate physical capability at specific operating point
                pump_code = pump_data.get('pump_code', 'Unknown')
                
                # Add debugging for HC pumps that manufacturer found viable
                if pump_code and any(hc in str(pump_code) for hc in ['32 HC', '30 HC', '28 HC']):
                    logger.error(f"[HC SELECTION DEBUG] {pump_code}: Starting evaluation for {flow} m³/hr @ {head}m")
                    logger.error(f"[HC SELECTION DEBUG] {pump_code}: Pump data keys: {list(pump_data.keys())}")
                    specs = pump_data.get('specifications', {})
                    logger.error(f"[HC SELECTION DEBUG] {pump_code}: BEP {specs.get('bep_flow_m3hr', 0)} m³/hr @ {specs.get('bep_head_m', 0)}m")
                    logger.error(f"[HC SELECTION DEBUG] {pump_code}: Max impeller: {specs.get('max_impeller_diameter_mm', 0)}mm")
                
                evaluation = self.evaluate_single_pump(pump_data, flow, head)
                
                # Check if HC pump was excluded and why
                if pump_code in ['32 HC 6P', '30 HC 6P', '28 HC 6P']:
                    if evaluation.get('feasible', False):
                        logger.error(f"✅ [PIPELINE STEP 4] {pump_code}: PASSED evaluation - feasible with score {evaluation.get('total_score', 0):.1f}!")
                    else:
                        logger.error(f"🚨 [PIPELINE STEP 4] {pump_code}: FAILED evaluation")
                        logger.error(f"🚨 [PIPELINE STEP 4] {pump_code}: Exclusion reasons: {evaluation.get('exclusion_reasons', [])}")
                        logger.error(f"🚨 [PIPELINE STEP 4] {pump_code}: Score components: {evaluation.get('score_components', {})}")
                        logger.error(f"🚨 [PIPELINE STEP 4] {pump_code}: Performance data: {evaluation.get('performance', 'None')}")
                
                # Apply additional constraints
                # NPSH constraint removed - data is collected for display but not used as hard gate
                
                if constraints.get('max_power_kw'):
                    max_power = constraints['max_power_kw']
                    if evaluation.get('power_kw', 0) > max_power:
                        evaluation['feasible'] = False
                        evaluation['exclusion_reasons'].append('Power exceeds limit')
                
                if evaluation.get('feasible', False):
                    feasible_pumps.append(evaluation)
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
            
            result['exclusion_details'] = {
                'excluded_pumps': excluded_pumps[:20],  # Top 20 excluded for analysis
                'exclusion_summary': exclusion_summary,
                'total_evaluated': len(all_pumps),
                'feasible_count': len(feasible_pumps),
                'excluded_count': len(excluded_pumps)
            }
        
        return result
    
    def evaluate_single_pump(self, pump_data: Dict[str, Any], 
                            flow: float, head: float) -> Dict[str, Any]:
        """
        Evaluate a single pump at operating conditions.
        Implements Three-Path Selection Logic based on variable_speed and variable_diameter flags.
        
        Args:
            pump_data: Pump data dictionary
            flow: Operating flow rate
            head: Operating head
        
        Returns:
            Evaluation results with scoring
        """
        evaluation = {
            'pump_code': pump_data.get('pump_code'),
            'pump_name': pump_data.get('pump_name'),
            'feasible': True,
            'exclusion_reasons': [],
            'score_components': {},
            'total_score': 0.0
        }
        
        try:
            # Get pump specifications
            specs = pump_data.get('specifications', {})
            
            # ========================================================================
            # THREE-PATH SELECTION LOGIC IMPLEMENTATION
            # ========================================================================
            # Extract variable_speed and variable_diameter flags
            variable_speed = specs.get('variable_speed', False)  # Default to False if missing
            variable_diameter = specs.get('variable_diameter', True)  # Default to True if missing (traditional)
            
            # Determine the pump operation mode and selection path
            if variable_speed and variable_diameter:
                # PATH A: FLEXIBLE PUMPS (Both = True)
                # These pumps can use EITHER method - defaulting to impeller trimming for now
                operation_mode = 'FLEXIBLE'
                selection_method = 'IMPELLER_TRIM'  # Default choice for flexible pumps
                evaluation['operation_mode'] = operation_mode
                evaluation['selection_method'] = selection_method
                evaluation['pump_flexibility'] = 'Can use either impeller trimming or VFD'
                
                logger.debug(f"[THREE-PATH] {pump_data.get('pump_code')}: FLEXIBLE pump - defaulting to impeller trimming")
                
            elif not variable_speed and variable_diameter:
                # PATH B: TRIM-ONLY PUMPS (Traditional fixed-speed)
                operation_mode = 'TRIM_ONLY'
                selection_method = 'IMPELLER_TRIM'
                evaluation['operation_mode'] = operation_mode
                evaluation['selection_method'] = selection_method
                evaluation['pump_flexibility'] = 'Fixed-speed pump with impeller trimming only'
                
                logger.debug(f"[THREE-PATH] {pump_data.get('pump_code')}: TRIM-ONLY pump - using impeller trimming")
                
            elif variable_speed and not variable_diameter:
                # PATH C: VFD-ONLY PUMPS (Modern variable-speed)
                operation_mode = 'VFD_ONLY'
                selection_method = 'SPEED_VARIATION'
                evaluation['operation_mode'] = operation_mode
                evaluation['selection_method'] = selection_method
                evaluation['pump_flexibility'] = 'Variable-speed pump (VFD required)'
                evaluation['vfd_required'] = True
                
                logger.info(f"[THREE-PATH] {pump_data.get('pump_code')}: VFD-ONLY pump - calculating speed variation")
                
            else:
                # EDGE CASE: Both FALSE (Fixed configuration)
                operation_mode = 'FIXED'
                selection_method = 'NONE'
                evaluation['operation_mode'] = operation_mode
                evaluation['selection_method'] = selection_method
                evaluation['pump_flexibility'] = 'Fixed configuration pump (no adjustment possible)'
                
                # These pumps cannot be adjusted - evaluate at fixed configuration only
                logger.warning(f"[THREE-PATH] {pump_data.get('pump_code')}: FIXED pump - no adjustment possible")
            
            # Log the decision for important pumps
            pump_code = pump_data.get('pump_code', '')
            if any(keyword in str(pump_code) for keyword in ['HC', 'WLN', 'MC', 'LC']):
                logger.info(f"[THREE-PATH DECISION] {pump_code}: Mode={operation_mode}, Method={selection_method}")
                logger.info(f"[THREE-PATH DECISION] {pump_code}: variable_speed={variable_speed}, variable_diameter={variable_diameter}")
            # ========================================================================
            # END OF THREE-PATH SELECTION LOGIC
            # ========================================================================
            
            # Store the selection method in the evaluation for later use in reporting
            evaluation['selection_path'] = {
                'operation_mode': operation_mode,
                'selection_method': selection_method,
                'variable_speed': variable_speed,
                'variable_diameter': variable_diameter
            }
            
            # Get BEP data from specifications (authentic manufacturer data)
            bep_flow = specs.get('bep_flow_m3hr', 0)
            bep_head = specs.get('bep_head_m', 0)
            
            logger.debug(f"[SCORE] {pump_data.get('pump_code')}: BEP from specs - flow: {bep_flow:.1f} m³/hr, head: {bep_head:.1f}m")
            
            # Special debug for 6 WLN 18A
            if "6 WLN 18A" in str(pump_data.get('pump_code', '')):
                logger.error(f"[DEBUG 6WLN QBP] Found pump: {pump_data.get('pump_code')}")
                logger.error(f"[DEBUG 6WLN QBP] BEP Flow: {bep_flow} m³/hr, BEP Head: {bep_head} m")
                logger.error(f"[DEBUG 6WLN QBP] Required Flow: {flow} m³/hr")
            
            if bep_flow > 0 and bep_head > 0:
                # Calculate QBP (% of BEP flow)
                qbp = (flow / bep_flow) * 100
                
                # TIERED evaluation - NO REJECTIONS (show all pumps categorized by performance)
                if 80 <= qbp <= 110:
                    operating_zone = 'preferred'  # Optimal operating range
                    tier = 1
                elif 60 <= qbp < 80 or 110 < qbp <= 140:
                    operating_zone = 'allowable'  # Good operating range
                    tier = 2
                elif 50 <= qbp < 60 or 140 < qbp <= 200:
                    operating_zone = 'acceptable'  # Acceptable for industrial use
                    tier = 3
                else:
                    operating_zone = 'marginal'  # Outside typical range but still usable
                    tier = 4
                
                evaluation['operating_zone'] = operating_zone
                evaluation['tier'] = tier
                
                # LOG but DO NOT REJECT - show all pumps in tiered results
                if tier > 2:
                    logger.info(f"[SELECTION] {pump_data.get('pump_code')}: QBP {qbp:.0f}% in {operating_zone} range (BEP: {bep_flow:.1f} m³/hr)")
                
                # ALL PUMPS REMAIN FEASIBLE - categorized by tier for user selection
                
                # BEP proximity score (Legacy v6.0 tiered scoring - 45 points max)
                flow_ratio = flow / bep_flow
                
                if 0.95 <= flow_ratio <= 1.05:  # Sweet spot
                    bep_score = 45
                elif 0.90 <= flow_ratio < 0.95 or 1.05 < flow_ratio <= 1.10:
                    bep_score = 40
                elif 0.80 <= flow_ratio < 0.90 or 1.10 < flow_ratio <= 1.20:
                    bep_score = 30
                elif 0.70 <= flow_ratio < 0.80 or 1.20 < flow_ratio <= 1.30:
                    bep_score = 20
                else:  # 0.60-0.70 or 1.30-1.40
                    bep_score = 10
                
                evaluation['score_components']['bep_proximity'] = bep_score
                evaluation['qbp_percent'] = qbp
                
                # FIXED: Head oversizing penalty - now uses realistic thresholds and is scoring-only
                head_ratio_pct = ((bep_head - head) / head) * 100 if head > 0 else 0
                evaluation['bep_head_oversizing_pct'] = head_ratio_pct
                
                # Apply penalty only for truly excessive oversizing (not a hard gate)
                if head_ratio_pct > self.head_oversizing_threshold:
                    if head_ratio_pct > self.severe_oversizing_threshold:
                        # Severe oversizing (>300% above requirement) - massive penalty
                        oversizing_penalty = -30  # Heavy penalty but not elimination
                        logger.info(f"Pump {pump_data.get('pump_code')}: SEVERE head oversizing {head_ratio_pct:.1f}% - BEP {bep_head}m vs required {head}m")
                    else:
                        # Moderate oversizing (150-300% above requirement) - moderate penalty
                        oversizing_penalty = -15 - (head_ratio_pct - self.head_oversizing_threshold) * 0.1
                        logger.info(f"Pump {pump_data.get('pump_code')}: Head oversizing {head_ratio_pct:.1f}% - BEP {bep_head}m vs required {head}m")
                    
                    evaluation['score_components']['head_oversizing_penalty'] = oversizing_penalty
                else:
                    # No penalty for reasonable BEP head ratios
                    evaluation['score_components']['head_oversizing_penalty'] = 0
            
            # Physical capability check - CONVERT TO SCORING PENALTY (no rejection)
            physical_capable = self._validate_physical_capability_at_point(pump_data, flow, head)
            if not physical_capable:
                # Apply severe scoring penalty but keep pump in results
                evaluation['score_components']['physical_limitation_penalty'] = -50
                evaluation['operating_zone'] = 'marginal'  # Force to marginal tier
                evaluation['tier'] = 4
                logger.info(f"[SELECTION] {pump_data.get('pump_code')}: Physical capability limited - applying penalty but keeping in results")

            # Get performance at operating point based on selection method
            if selection_method == 'IMPELLER_TRIM':
                # Use existing impeller trimming calculation
                performance = self.brain.performance.calculate_at_point(pump_data, flow, head)
                
            elif selection_method == 'SPEED_VARIATION':
                # Use VFD calculation for speed variation
                performance = self.brain.performance.calculate_performance_with_speed_variation(pump_data, flow, head)
                if performance:
                    # Add VFD-specific information to evaluation
                    evaluation['sizing_method'] = 'Speed Variation'
                    evaluation['required_speed_rpm'] = performance.get('required_speed_rpm')
                    evaluation['speed_ratio'] = performance.get('speed_ratio')
                    evaluation['operating_frequency_hz'] = performance.get('operating_frequency_hz')
                    evaluation['vfd_details'] = {
                        'required_speed_rpm': performance.get('required_speed_rpm'),
                        'reference_speed_rpm': performance.get('reference_speed_rpm'),
                        'speed_ratio': performance.get('speed_ratio'),
                        'operating_frequency_hz': performance.get('operating_frequency_hz'),
                        'reference_point': performance.get('reference_point'),
                        'system_curve_k': performance.get('system_curve_k'),
                        'h_static': performance.get('h_static')
                    }
                    logger.info(f"[VFD] {pump_data.get('pump_code')}: VFD calculation successful - {performance.get('required_speed_rpm')} RPM ({performance.get('speed_ratio')}% speed)")
                else:
                    # VFD not feasible (speed out of range)
                    logger.warning(f"[VFD] {pump_data.get('pump_code')}: VFD not feasible - likely speed out of range")
                    evaluation['feasible'] = False
                    evaluation['exclusion_reasons'].append('VFD speed required is outside pump operational range')
                    return evaluation
                    
            elif selection_method == 'NONE':
                # Fixed configuration pump - evaluate at nominal conditions
                performance = self.brain.performance.calculate_at_point(pump_data, flow, head)
                
            else:
                # For FLEXIBLE pumps, try both methods and select the best
                # First try impeller trimming
                trim_performance = self.brain.performance.calculate_at_point(pump_data, flow, head)
                
                # Then try VFD
                vfd_performance = self.brain.performance.calculate_performance_with_speed_variation(pump_data, flow, head)
                
                # Select the better option based on efficiency or feasibility
                if trim_performance and vfd_performance:
                    # Both methods work - choose based on efficiency
                    if vfd_performance.get('efficiency_pct', 0) > trim_performance.get('efficiency_pct', 0):
                        performance = vfd_performance
                        evaluation['sizing_method'] = 'Speed Variation'
                        evaluation['required_speed_rpm'] = vfd_performance.get('required_speed_rpm')
                        evaluation['speed_ratio'] = vfd_performance.get('speed_ratio')
                        evaluation['operating_frequency_hz'] = vfd_performance.get('operating_frequency_hz')
                        evaluation['vfd_details'] = {
                            'required_speed_rpm': vfd_performance.get('required_speed_rpm'),
                            'reference_speed_rpm': vfd_performance.get('reference_speed_rpm'),
                            'speed_ratio': vfd_performance.get('speed_ratio'),
                            'operating_frequency_hz': vfd_performance.get('operating_frequency_hz'),
                            'reference_point': vfd_performance.get('reference_point'),
                            'system_curve_k': vfd_performance.get('system_curve_k'),
                            'h_static': vfd_performance.get('h_static')
                        }
                        logger.info(f"[FLEXIBLE] {pump_data.get('pump_code')}: Selected VFD over trimming (better efficiency)")
                    else:
                        performance = trim_performance
                        evaluation['sizing_method'] = 'Impeller Trim'
                        logger.info(f"[FLEXIBLE] {pump_data.get('pump_code')}: Selected trimming over VFD (better efficiency)")
                elif trim_performance:
                    # Only trimming works
                    performance = trim_performance
                    evaluation['sizing_method'] = 'Impeller Trim'
                    logger.info(f"[FLEXIBLE] {pump_data.get('pump_code')}: Using trimming (VFD not feasible)")
                elif vfd_performance:
                    # Only VFD works
                    performance = vfd_performance
                    evaluation['sizing_method'] = 'Speed Variation'
                    evaluation['required_speed_rpm'] = vfd_performance.get('required_speed_rpm')
                    evaluation['speed_ratio'] = vfd_performance.get('speed_ratio')
                    evaluation['operating_frequency_hz'] = vfd_performance.get('operating_frequency_hz')
                    evaluation['vfd_details'] = {
                        'required_speed_rpm': vfd_performance.get('required_speed_rpm'),
                        'reference_speed_rpm': vfd_performance.get('reference_speed_rpm'),
                        'speed_ratio': vfd_performance.get('speed_ratio'),
                        'operating_frequency_hz': vfd_performance.get('operating_frequency_hz'),
                        'reference_point': vfd_performance.get('reference_point'),
                        'system_curve_k': vfd_performance.get('system_curve_k'),
                        'h_static': vfd_performance.get('h_static')
                    }
                    logger.info(f"[FLEXIBLE] {pump_data.get('pump_code')}: Using VFD (trimming not feasible)")
                else:
                    # Neither method works
                    performance = None
                    logger.warning(f"[FLEXIBLE] {pump_data.get('pump_code')}: Neither trimming nor VFD feasible")
            
            # Validate performance data contract
            if performance:
                required_keys = ['meets_requirements', 'efficiency_pct', 'head_m', 'power_kw']
                missing_keys = [k for k in required_keys if k not in performance]
                if missing_keys:
                    logger.error(f"Performance data for pump {pump_data.get('pump_code')} is missing keys: {missing_keys}")
                    evaluation['feasible'] = False
                    evaluation['exclusion_reasons'].append('Invalid performance data')
                    return evaluation
            
            # Be more lenient like Legacy - accept if performance exists even if marginal
            if performance:
                # Check if we have BEP migration data (from Hydraulic Institute Correction Model)
                if 'true_qbp_percent' in performance and performance.get('trim_percent', 100) < 100:
                    # Use TRUE QBP that accounts for BEP migration with trimming
                    true_qbp = performance.get('true_qbp_percent', 100)
                    original_qbp = evaluation.get('qbp_percent', 100)
                    
                    logger.info(f"[BEP SCORING] {pump_data.get('pump_code')}: Using TRUE QBP {true_qbp:.1f}% (vs simple {original_qbp:.1f}%)")
                    
                    # Update QBP percent with the more accurate value
                    evaluation['qbp_percent'] = true_qbp
                    evaluation['bep_migration_corrected'] = True
                    
                    # Recalculate operating zone with TRUE QBP - TIERED APPROACH
                    if 80 <= true_qbp <= 110:
                        operating_zone = 'preferred'
                        tier = 1
                    elif 60 <= true_qbp < 80 or 110 < true_qbp <= 140:
                        operating_zone = 'allowable'
                        tier = 2
                    elif 50 <= true_qbp < 60 or 140 < true_qbp <= 200:
                        operating_zone = 'acceptable'
                        tier = 3
                    else:
                        operating_zone = 'marginal'
                        tier = 4
                    
                    evaluation['operating_zone'] = operating_zone
                    evaluation['tier'] = tier
                    
                    # LOG but DO NOT REJECT - TRUE QBP pumps also remain feasible
                    if tier > 2:
                        logger.info(f"[SELECTION] {pump_data.get('pump_code')}: TRUE QBP {true_qbp:.0f}% in {operating_zone} range after BEP migration")
                    
                    # ALL PUMPS REMAIN FEASIBLE - even with BEP migration correction
                    
                    # Recalculate BEP proximity score with TRUE QBP
                    flow_ratio = true_qbp / 100  # Convert back to ratio
                    
                    if 0.95 <= flow_ratio <= 1.05:  # Sweet spot
                        bep_score = 45
                    elif 0.90 <= flow_ratio < 0.95 or 1.05 < flow_ratio <= 1.10:
                        bep_score = 40
                    elif 0.80 <= flow_ratio < 0.90 or 1.10 < flow_ratio <= 1.20:
                        bep_score = 30
                    elif 0.70 <= flow_ratio < 0.80 or 1.20 < flow_ratio <= 1.30:
                        bep_score = 20
                    else:  # 0.60-0.70 or 1.30-1.40
                        bep_score = 10
                    
                    evaluation['score_components']['bep_proximity'] = bep_score
                    
                    # Store shifted BEP data for transparency
                    if 'shifted_bep_flow' in performance:
                        evaluation['shifted_bep_flow'] = performance['shifted_bep_flow']
                        evaluation['shifted_bep_head'] = performance['shifted_bep_head']
                        evaluation['original_bep_flow'] = performance.get('original_bep_flow', 0)
                        evaluation['original_bep_head'] = performance.get('original_bep_head', 0)
                
                # Efficiency score (Legacy v6.0 - 35 points max)
                efficiency = performance.get('efficiency_pct', 0)
                if efficiency >= 85:
                    eff_score = 35
                elif efficiency >= 75:
                    eff_score = 30 + (efficiency - 75) * 0.5
                elif efficiency >= 65:
                    eff_score = 25 + (efficiency - 65) * 0.5
                elif efficiency >= 45:
                    eff_score = 10 + (efficiency - 45) * 0.75
                else:  # 40-45%
                    eff_score = max(0, (efficiency - 40) * 2)
                
                evaluation['score_components']['efficiency'] = eff_score
                evaluation['efficiency_pct'] = efficiency
                
                # CRITICAL FIX: Store actual head delivered by pump AND flow rate
                actual_pump_head = performance.get('head_m')
                if actual_pump_head is None:
                    logger.error(f"[CHART BUG FIX] No actual head in performance data for {pump_data.get('pump_code')}")
                    evaluation['head_m'] = head  # Fallback to required head only if performance calculation failed
                else:
                    evaluation['head_m'] = actual_pump_head  # Use ACTUAL pump head for chart plotting
                    logger.debug(f"[CHART BUG FIX] {pump_data.get('pump_code')}: Chart will show operating point at {flow}m³/hr @ {actual_pump_head}m (actual pump head)")
                
                evaluation['flow_m3hr'] = flow  # Store the operating flow rate
                
                # Head margin score (Legacy v6.0 - 20 points max)
                head_margin_m = performance.get('head_margin_m', 0)
                head_margin_pct = (head_margin_m / head) * 100 if head > 0 else 0
                
                if head_margin_pct <= 5:  # Perfect sizing
                    margin_score = 20
                elif 5 < head_margin_pct <= 10:  # Good sizing
                    margin_score = 20 - (head_margin_pct - 5) * 2
                elif 10 < head_margin_pct <= 15:  # Acceptable sizing
                    margin_score = 10 - (head_margin_pct - 10) * 1
                else:  # 15-20%
                    margin_score = 5 - (head_margin_pct - 15) * 2
                    margin_score = max(0, margin_score)
                
                evaluation['score_components']['head_margin'] = margin_score
                evaluation['head_margin_m'] = head_margin_m
                evaluation['head_margin_pct'] = head_margin_pct
                
                # NPSH collected for informational display only (no hard gate or scoring)
                npshr = performance.get('npshr_m')
                if npshr:
                    evaluation['npshr_m'] = npshr
                
                # Power consumption (for tie-breaking)
                evaluation['power_kw'] = performance.get('power_kw', 0)
                
                # Store complete performance data for UI display
                evaluation['npshr_m'] = performance.get('npshr_m', 0)
                
                # Impeller trim penalty (Legacy v6.0)
                impeller_diameter = performance.get('impeller_diameter_mm')
                if impeller_diameter:
                    evaluation['impeller_diameter_mm'] = impeller_diameter
                    # Calculate trim percent from performance data
                    base_diameter = performance.get('base_diameter_mm', impeller_diameter)
                    trim_percent = (impeller_diameter / base_diameter * 100) if base_diameter else 100
                    evaluation['trim_percent'] = trim_percent
                    
                    # Apply trim penalty
                    if trim_percent < 95:
                        if trim_percent >= 90:
                            trim_penalty = -2  # Small penalty
                        elif trim_percent >= 85:
                            trim_penalty = -5  # Moderate penalty
                        else:
                            trim_penalty = -10  # Large penalty
                        evaluation['score_components']['trim_penalty'] = trim_penalty
                
            else:
                # When performance analyzer returns None, it could be due to:
                # 1. Missing data (keep with penalty)  
                # 2. Physical impossibility (exclude entirely)
                
                # Check if this pump was rejected for physical reasons by looking at recent log messages
                pump_code = pump_data.get('pump_code', 'Unknown')
                
                # If the performance analyzer rejected this pump for physical reasons, exclude it entirely
                # This is indicated by the performance data being None after analyzer evaluation
                logger.warning(f"[SELECTION] {pump_code}: Excluded due to physical impossibility or missing critical data")
                evaluation['feasible'] = False
                evaluation['exclusion_reasons'].append('Physical capability exceeded or critical data missing')
                return evaluation  # Return early - don't include in results
            
            # Calculate total score
            evaluation['total_score'] = sum(evaluation['score_components'].values())
            
        except Exception as e:
            logger.error(f"Error in pump evaluation: {str(e)}")
            evaluation['feasible'] = False
            evaluation['exclusion_reasons'].append(f'Evaluation error: {str(e)}')
        
        return evaluation
    
    def rank_pumps(self, pump_list: List[str], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank pumps based on criteria.
        
        Args:
            pump_list: List of pump codes
            criteria: Ranking criteria
        
        Returns:
            Ranked list with analysis
        """
        flow = criteria.get('flow', 0)
        head = criteria.get('head', 0)
        
        if not flow or not head:
            logger.error("Flow and head required for ranking")
            return []
        
        evaluations = []
        
        for pump_code in pump_list:
            try:
                # Get pump data
                pump_data = self.brain.repository.get_pump_by_code(pump_code)
                if not pump_data:
                    logger.warning(f"Pump {pump_code} not found")
                    continue
                
                # Evaluate pump
                evaluation = self.evaluate_single_pump(pump_data, flow, head)
                evaluations.append(evaluation)
                
            except Exception as e:
                logger.error(f"Error ranking pump {pump_code}: {str(e)}")
                continue
        
        # Sort by score
        evaluations.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        return evaluations
    
    def _validate_physical_capability_at_point(self, pump_data: Dict[str, Any], 
                                             flow_m3hr: float, head_m: float) -> bool:
        """
        CRITICAL: Validate pump can physically deliver required head at specific flow rate.
        This is the core validation that was missing in the catalog engine.
        """
        curves = pump_data.get('curves', [])
        if not curves:
            logger.debug(f"Pump {pump_data.get('pump_code')}: No curves available")
            return False
        
        # Check curves starting with maximum impeller diameter first (authentic manufacturer design)
        sorted_curves = sorted(curves, key=lambda x: x.get('impeller_diameter_mm', 0), reverse=True)
        
        for curve in sorted_curves:
            curve_points = curve.get('performance_points', [])
            if not curve_points or len(curve_points) < 2:
                continue
                
            # Extract curve data
            curve_flows = [p['flow_m3hr'] for p in curve_points]
            curve_heads = [p['head_m'] for p in curve_points]
            
            # Check if flow is within curve range (with 10% tolerance)
            min_flow = min(curve_flows)
            max_flow = max(curve_flows)
            
            if not (min_flow * 0.9 <= flow_m3hr <= max_flow * 1.1):
                continue  # Flow outside this curve's range
            
            try:
                # Interpolate head at required flow rate
                from scipy import interpolate
                
                # Sort points by flow for interpolation
                sorted_points = sorted(zip(curve_flows, curve_heads))
                flows_sorted, heads_sorted = zip(*sorted_points)
                
                # Use linear interpolation to find head at required flow
                head_interp = interpolate.interp1d(
                    flows_sorted, heads_sorted, 
                    kind='linear', 
                    bounds_error=False
                )
                
                delivered_head = float(head_interp(flow_m3hr))
                
                # Check if pump can deliver AT LEAST the required head (2% tolerance)
                if delivered_head >= head_m * 0.98:
                    logger.debug(f"Pump {pump_data.get('pump_code')}: Can deliver {delivered_head:.1f}m at {flow_m3hr} m³/hr (required: {head_m}m) - VALID")
                    return True
                else:
                    logger.debug(f"Pump {pump_data.get('pump_code')}: Can only deliver {delivered_head:.1f}m at {flow_m3hr} m³/hr (required: {head_m}m) - INSUFFICIENT")
                    
            except Exception as e:
                logger.debug(f"Error interpolating curve for {pump_data.get('pump_code')}: {e}")
                continue
        
        logger.debug(f"Pump {pump_data.get('pump_code')}: Cannot deliver required head {head_m}m at flow {flow_m3hr} m³/hr")
        return False
    
    def _calculate_bep_from_curves(self, pump_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate BEP from performance curves when missing from specifications.
        This is authentic engineering practice - BEP is the point of maximum efficiency.
        """
        try:
            curves = pump_data.get('curves', [])
            if not curves:
                return None
            
            best_bep = None
            highest_efficiency = 0
            
            # Check all curves to find the one with highest efficiency point
            for curve in curves:
                points = curve.get('performance_points', [])
                if len(points) < 3:  # Need multiple points to find maximum
                    continue
                
                # Find maximum efficiency point in this curve
                for point in points:
                    efficiency = point.get('efficiency_pct', 0)
                    if efficiency > highest_efficiency:
                        highest_efficiency = efficiency
                        best_bep = {
                            'flow_m3hr': point.get('flow_m3hr', 0),
                            'head_m': point.get('head_m', 0),
                            'efficiency_pct': efficiency
                        }
            
            if best_bep and best_bep['flow_m3hr'] > 0 and best_bep['head_m'] > 0:
                logger.debug(f"[BEP] {pump_data.get('pump_code')}: Found BEP at {best_bep['flow_m3hr']:.1f} m³/hr, {best_bep['head_m']:.1f}m, {best_bep['efficiency_pct']:.1f}%")
                return best_bep
            
            return None
            
        except Exception as e:
            logger.debug(f"Error calculating BEP from curves for {pump_data.get('pump_code')}: {e}")
            return None

    def _calculate_specific_speed(self, flow_m3hr: float, head_m: float, speed_rpm: float = 2960) -> float:
        """
        Calculate specific speed (Ns) using SI definition: Ns = N√Q / H^(3/4)
        where N is in rpm, Q in m³/s, H in m
        
        Args:
            flow_m3hr: Flow rate in m³/hr (will be converted to m³/s)
            head_m: Head in meters
            speed_rpm: Pump speed in RPM (default 2960 for 2-pole at 50Hz)
        
        Returns:
            Specific speed (dimensionless SI units)
        """
        try:
            if flow_m3hr <= 0 or head_m <= 0:
                return 0
            
            # Convert flow to m³/s
            flow_m3s = flow_m3hr / 3600
            
            # Calculate specific speed: Ns = N√Q / H^(3/4)
            import math
            ns = speed_rpm * math.sqrt(flow_m3s) / (head_m ** 0.75)
            
            return ns
            
        except Exception as e:
            logger.debug(f"Error calculating specific speed: {e}")
            return 0
    
    def _classify_pump_hydraulic_type(self, specific_speed: float) -> Dict[str, Any]:
        """
        Classify pump hydraulic type based on specific speed
        Returns classification with scoring weights and expected characteristics
        """
        if specific_speed <= 0:
            return {
                'type': 'unknown',
                'description': 'Unknown hydraulic type',
                'flow_weight': 0.5,
                'head_weight': 0.5,
                'trim_flow_exp': 1.0,
                'trim_head_exp': 2.0,
                'efficiency_drop_per_trim': 0.1  # Per percent of trim
            }
        
        # Based on industry standards and provided documentation
        if specific_speed < 30:
            return {
                'type': 'radial_low',
                'description': 'Radial - Low Ns (steep H-Q curve)',
                'flow_weight': 0.4,  # Head more important for radial
                'head_weight': 0.6,
                'trim_flow_exp': 1.0,
                'trim_head_exp': 2.0,
                'efficiency_drop_per_trim': 0.1  # 0.5-1.5% for typical 5-15% trim
            }
        elif specific_speed < 60:
            return {
                'type': 'radial_mid',
                'description': 'Radial - Mid Ns (broader curve)',
                'flow_weight': 0.45,
                'head_weight': 0.55,
                'trim_flow_exp': 1.0,
                'trim_head_exp': 1.95,
                'efficiency_drop_per_trim': 0.15  # 0.8-2.0% for typical trim
            }
        elif specific_speed < 120:
            return {
                'type': 'mixed_flow',
                'description': 'Mixed-flow',
                'flow_weight': 0.5,
                'head_weight': 0.5,
                'trim_flow_exp': 0.97,
                'trim_head_exp': 1.85,
                'efficiency_drop_per_trim': 0.25  # 1.5-3.0% for typical trim
            }
        else:  # specific_speed >= 120
            return {
                'type': 'axial_flow',
                'description': 'Axial-flow (propeller)',
                'flow_weight': 0.55,  # Flow more important for axial
                'head_weight': 0.45,
                'trim_flow_exp': 0.95,
                'trim_head_exp': 1.65,
                'efficiency_drop_per_trim': 0.35  # 2.0-4.0% for typical trim
            }
    
    def _calculate_trim_requirement(self, current_head: float, required_head: float, 
                                   trim_head_exp: float = 2.0) -> float:
        """
        Calculate required trim percentage to achieve target head
        Using D2/D1 = (H2/H1)^(1/exp) where exp is pump-type specific
        
        Returns:
            Trim ratio (1.0 = no trim, 0.85 = 15% trim)
        """
        try:
            if current_head <= 0 or required_head <= 0:
                return 1.0
            
            if required_head > current_head:
                return 1.0  # Cannot trim up
            
            # Calculate trim ratio: D2/D1 = (H2/H1)^(1/exp)
            import math
            trim_ratio = math.pow(required_head / current_head, 1.0 / trim_head_exp)
            
            # Enforce 15% maximum trim limit
            if trim_ratio < 0.85:
                logger.debug(f"Trim requirement {(1-trim_ratio)*100:.1f}% exceeds 15% limit")
                return 0.85
            
            return trim_ratio
            
        except Exception as e:
            logger.debug(f"Error calculating trim requirement: {e}")
            return 1.0

    def _calculate_bep_from_curves_intelligent(self, pump_data: Dict[str, Any], 
                                              target_flow: float, target_head: float) -> Optional[Dict[str, Any]]:
        """
        Intelligently calculate BEP from curves by selecting the most appropriate curve
        for the target operating conditions, then finding maximum efficiency.
        """
        try:
            curves = pump_data.get('curves', [])
            if not curves:
                return None
            
            # Score each curve based on how well it matches the target conditions
            curve_scores = []
            
            for curve in curves:
                points = curve.get('performance_points', [])
                if len(points) < 3:
                    continue
                
                # Get curve operating range
                flows = [p.get('flow_m3hr', 0) for p in points if p.get('flow_m3hr', 0) > 0]
                heads = [p.get('head_m', 0) for p in points if p.get('head_m', 0) > 0]
                
                if not flows or not heads:
                    continue
                
                min_flow, max_flow = min(flows), max(flows)
                min_head, max_head = min(heads), max(heads)
                
                # Calculate how well this curve covers the target point
                flow_coverage = 1.0
                if target_flow < min_flow:
                    flow_coverage = min_flow / target_flow if target_flow > 0 else 0
                elif target_flow > max_flow:
                    flow_coverage = max_flow / target_flow if target_flow > 0 else 0
                
                head_coverage = 1.0
                if target_head < min_head:
                    head_coverage = min_head / target_head if target_head > 0 else 0
                elif target_head > max_head:
                    head_coverage = max_head / target_head if target_head > 0 else 0
                
                # Prefer curves that can handle the target conditions
                coverage_score = min(flow_coverage, head_coverage)
                
                # Get curve diameter for tie-breaking (larger = higher flow capability)
                diameter = curve.get('impeller_diameter_mm', 0)
                
                curve_scores.append({
                    'curve': curve,
                    'coverage_score': coverage_score,
                    'diameter': diameter,
                    'points': points
                })
            
            if not curve_scores:
                return None
            
            # Sort by coverage (best coverage first), then by diameter (larger first)
            curve_scores.sort(key=lambda x: (-x['coverage_score'], -x['diameter']))
            best_curve = curve_scores[0]['curve']
            best_points = curve_scores[0]['points']
            
            # Find BEP (maximum efficiency) in the selected curve
            best_bep = None
            highest_efficiency = 0
            
            for point in best_points:
                efficiency = point.get('efficiency_pct', 0)
                if efficiency > highest_efficiency:
                    highest_efficiency = efficiency
                    best_bep = {
                        'flow_m3hr': point.get('flow_m3hr', 0),
                        'head_m': point.get('head_m', 0),
                        'efficiency_pct': efficiency,
                        'diameter_mm': best_curve.get('impeller_diameter_mm', 0)
                    }
            
            if best_bep and best_bep['flow_m3hr'] > 0 and best_bep['head_m'] > 0:
                pump_code = pump_data.get('pump_code', 'Unknown')
                logger.debug(f"[BEP INTELLIGENT] {pump_code}: Selected {best_bep['diameter_mm']}mm curve - "
                           f"BEP at {best_bep['flow_m3hr']:.1f} m³/hr, {best_bep['head_m']:.1f}m, {best_bep['efficiency_pct']:.1f}%")
                return best_bep
            
            return None
            
        except Exception as e:
            logger.debug(f"Error in intelligent BEP calculation for {pump_data.get('pump_code')}: {e}")
            # Fallback to simple method
            return self._calculate_bep_from_curves(pump_data)
    
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
        import math
        
        logger.info(f"[BEP PROXIMITY] Finding pumps near flow={flow} m³/hr, head={head}m")
        
        if not self.brain.repository:
            logger.error("[BEP PROXIMITY] Repository not available")
            return []
        
        # Enhanced input validation
        if flow <= 0 or head <= 0:
            logger.error(f"[BEP PROXIMITY] Invalid inputs: flow={flow}, head={head}")
            return []
        
        # Additional safety checks
        if flow > 20000:  # Unrealistic for centrifugal pumps
            logger.warning(f"[BEP PROXIMITY] Unusually high flow rate: {flow} m³/hr")
        
        if head > 2000:  # Unrealistic for centrifugal pumps
            logger.warning(f"[BEP PROXIMITY] Unusually high head: {head} m")
        
        # Get all pumps from repository
        all_pumps = self.brain.repository.get_pump_models()
        candidate_pumps = []
        
        for pump in all_pumps:
            pump_code = pump.get('pump_code', 'Unknown')
            
            # Apply pump type filter if specified
            if pump_type:
                pump_type_actual = pump.get('pump_type', '')
                if pump_type.upper() not in pump_type_actual.upper():
                    continue
            
            # Get BEP data from specifications (authentic manufacturer data)
            specs = pump.get('specifications', {})
            bep_flow = specs.get('bep_flow_m3hr')
            bep_head = specs.get('bep_head_m')
            bep_efficiency = specs.get('bep_efficiency_pct')
            
            # Skip pumps without valid BEP data
            if not bep_flow or not bep_head or bep_flow <= 0 or bep_head <= 0:
                logger.debug(f"[BEP PROXIMITY] {pump_code}: Skipping - no valid BEP data")
                continue
            
            # Get speed from specifications or use default
            speed_rpm = specs.get('speed_rpm', 2960)  # Default 2-pole motor at 50Hz
            
            # Calculate specific speed for pump classification
            specific_speed = self._calculate_specific_speed(bep_flow, bep_head, speed_rpm)
            hydraulic_type = self._classify_pump_hydraulic_type(specific_speed)
            
            # Calculate symmetric normalized differences
            flow_delta = abs(flow - bep_flow) / max(flow, bep_flow)
            head_delta = abs(head - bep_head) / max(head, bep_head)
            
            # Apply pump-type-specific weighting to distance calculation
            weighted_distance = math.sqrt(
                hydraulic_type['flow_weight'] * (flow_delta ** 2) + 
                hydraulic_type['head_weight'] * (head_delta ** 2)
            )
            
            # Convert to percentage for display
            proximity_score_pct = weighted_distance * 100
            
            # Enhanced categorization with pump-type consideration
            if proximity_score_pct < 10:
                proximity_category = "Excellent"
                category_color = "#4CAF50"
            elif proximity_score_pct < 25:
                proximity_category = "Good"
                category_color = "#8BC34A"
            elif proximity_score_pct < 50:
                proximity_category = "Moderate"
                category_color = "#FF9800"
            else:
                proximity_category = "Poor"
                category_color = "#F44336"
            
            # Get BEP efficiency if missing
            if not bep_efficiency:
                bep_data = self._calculate_bep_from_curves_intelligent(pump, flow, head)
                bep_efficiency = bep_data.get('efficiency_pct', 0) if bep_data else 0
                if bep_data:
                    # Update BEP values and recalculate
                    bep_flow = bep_data.get('flow_m3hr', bep_flow)
                    bep_head = bep_data.get('head_m', bep_head)
                    flow_delta = abs(flow - bep_flow) / max(flow, bep_flow)
                    head_delta = abs(head - bep_head) / max(head, bep_head)
                    weighted_distance = math.sqrt(
                        hydraulic_type['flow_weight'] * (flow_delta ** 2) + 
                        hydraulic_type['head_weight'] * (head_delta ** 2)
                    )
                    proximity_score_pct = weighted_distance * 100
            
            # Validate BEP efficiency
            if bep_efficiency and (bep_efficiency < 30 or bep_efficiency > 95):
                logger.warning(f"[BEP PROXIMITY] {pump_code}: Questionable BEP efficiency {bep_efficiency}%")
            
            # Calculate trim requirement if pump BEP head is higher than required
            trim_ratio = 1.0
            predicted_efficiency = bep_efficiency
            if bep_head > head:
                trim_ratio = self._calculate_trim_requirement(
                    bep_head, head, hydraulic_type['trim_head_exp']
                )
                # Predict efficiency drop from trimming
                trim_percent = (1 - trim_ratio) * 100
                efficiency_drop = trim_percent * hydraulic_type['efficiency_drop_per_trim']
                predicted_efficiency = max(bep_efficiency - efficiency_drop, 30)  # Floor at 30%
            
            # Calculate operating range score (how well pump can handle flow variations)
            # Wider operating range is better for variable conditions
            operating_range_score = 100.0
            if specific_speed < 60:  # Radial pumps have wider stable range
                operating_range_score = 100.0
            elif specific_speed < 120:  # Mixed flow moderate range
                operating_range_score = 85.0
            else:  # Axial narrow stable range
                operating_range_score = 70.0
            
            candidate_pumps.append({
                'pump_code': pump_code,
                'pump': pump,  # Include full pump data
                'proximity_score': weighted_distance,  # Raw weighted score for sorting
                'proximity_score_pct': proximity_score_pct,  # Percentage for display
                'proximity_category': proximity_category,
                'category_color': category_color,
                'bep_efficiency': bep_efficiency or 0,
                'predicted_efficiency': predicted_efficiency,  # After trimming
                'bep_flow': bep_flow,
                'bep_head': bep_head,
                'flow_delta_pct': flow_delta * 100,
                'head_delta_pct': head_delta * 100,
                'specific_speed': specific_speed,
                'hydraulic_type': hydraulic_type['type'],
                'hydraulic_description': hydraulic_type['description'],
                'trim_ratio': trim_ratio,
                'trim_percent': (1 - trim_ratio) * 100,
                'operating_range_score': operating_range_score,
                'flow_weight': hydraulic_type['flow_weight'],
                'head_weight': hydraulic_type['head_weight']
            })
        
        # Enhanced multi-level sort:
        # 1. Proximity score (lower is better)
        # 2. Predicted efficiency after trim (higher is better)
        # 3. Operating range score (higher is better for flexibility)
        candidate_pumps.sort(key=lambda x: (
            x['proximity_score'], 
            -x['predicted_efficiency'],
            -x['operating_range_score']
        ))
        
        # Return top 20 pumps
        top_pumps = candidate_pumps[:20]
        
        logger.info(f"[BEP PROXIMITY] Found {len(candidate_pumps)} pumps with BEP data, returning top 20")
        if top_pumps:
            best = top_pumps[0]
            logger.info(f"[BEP PROXIMITY] Best match: {best['pump_code']} - "
                      f"Proximity: {best['proximity_score_pct']:.1f}%, "
                      f"Ns: {best['specific_speed']:.1f}, "
                      f"Type: {best['hydraulic_type']}, "
                      f"Trim: {best['trim_percent']:.1f}%, "
                      f"Predicted Eff: {best['predicted_efficiency']:.1f}%")
        
        return top_pumps