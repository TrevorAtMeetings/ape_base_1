"""
Selection Intelligence Module
=============================
Consolidates pump selection logic from catalog_engine.py
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
        
        # Selection parameters (from catalog_engine v6.0)
        # Legacy uses point-based scoring, not percentage weights
        self.scoring_weights = {
            'bep_proximity': 45,  # Max points (was 40% weight)
            'efficiency': 35,     # Max points (was 30% weight)
            'head_margin': 20,    # Max points (was 15% weight)
            'npsh_margin': 0      # Removed in v6.0 (now hard gate only)
        }
        
        # Operating constraints
        self.min_trim_percent = 85.0
        self.max_trim_percent = 100.0
        self.npsh_safety_factor = 1.5
        self.qbp_min_percent = 60.0
        self.qbp_max_percent = 130.0
        
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
        
        # Get all pumps from repository
        all_pumps = self.brain.repository.get_pump_models()
        if not all_pumps:
            logger.warning("No pump models available in repository")
            return {'ranked_pumps': [], 'exclusion_details': None}
        
        # INTELLIGENT PRE-FILTERING: Only evaluate pumps in reasonable range
        # This prevents evaluating 0.1 m³/hr pumps for 350 m³/hr applications
        min_flow_threshold = max(flow * 0.4, 5.0)  # At least 40% of required flow, minimum 5 m³/hr
        max_flow_threshold = flow * 3.0  # Maximum 300% of required flow
        
        pump_models = []
        pre_filtered_count = 0
        
        for pump in all_pumps:
            specs = pump.get('specifications', {})
            bep_flow = specs.get('bep_flow_m3hr', 0)
            
            # Pre-filter by flow range - intelligent range matching
            if bep_flow > 0 and min_flow_threshold <= bep_flow <= max_flow_threshold:
                pump_models.append(pump)
            else:
                pre_filtered_count += 1
        
        logger.info(f"Smart pre-filtering: {len(pump_models)} pumps selected from {len(all_pumps)} total (filtered out {pre_filtered_count} inappropriate pumps)")
        
        feasible_pumps = []
        excluded_pumps = []
        exclusion_summary = {}
        
        for pump_data in pump_models:
            try:
                # Apply pump type constraint early
                if constraints.get('pump_type') and constraints['pump_type'] != 'GENERAL':
                    pump_type = pump_data.get('pump_type', '').upper()
                    if pump_type != constraints['pump_type'].upper():
                        if include_exclusions:
                            excluded_pumps.append({
                                'pump_code': pump_data.get('pump_code'),
                                'pump_name': pump_data.get('pump_name', ''),
                                'exclusion_reasons': ['Wrong pump type'],
                                'score_components': {}
                            })
                            exclusion_summary['Wrong pump type'] = exclusion_summary.get('Wrong pump type', 0) + 1
                        continue
                
                # CRITICAL: Evaluate physical capability at specific operating point
                evaluation = self.evaluate_single_pump(pump_data, flow, head)
                
                # Apply additional constraints
                if constraints.get('npsh_available'):
                    npsh_available = constraints['npsh_available']
                    if evaluation.get('npshr_m', 0) > npsh_available / self.npsh_safety_factor:
                        evaluation['feasible'] = False
                        evaluation['exclusion_reasons'].append('NPSH insufficient')
                
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
                'total_evaluated': len(pump_models),
                'feasible_count': len(feasible_pumps),
                'excluded_count': len(excluded_pumps)
            }
        
        return result
    
    def evaluate_single_pump(self, pump_data: Dict[str, Any], 
                            flow: float, head: float) -> Dict[str, Any]:
        """
        Evaluate a single pump at operating conditions.
        
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
            
            # Get BEP data from specifications (authentic manufacturer data)
            bep_flow = specs.get('bep_flow_m3hr', 0)
            bep_head = specs.get('bep_head_m', 0)
            
            logger.debug(f"[SCORE] {pump_data.get('pump_code')}: BEP from specs - flow: {bep_flow:.1f} m³/hr, head: {bep_head:.1f}m")
            
            if bep_flow > 0 and bep_head > 0:
                # Calculate QBP (% of BEP flow)
                qbp = (flow / bep_flow) * 100
                
                # Operating zone classification (proper engineering standards)
                operating_zone = 'disqualified'
                if 70 <= qbp <= 120:
                    operating_zone = 'preferred'  # Best reliability and efficiency zone
                elif 60 <= qbp < 70 or 120 < qbp <= 130:
                    operating_zone = 'allowable'  # Acceptable but not optimal zone
                
                evaluation['operating_zone'] = operating_zone
                
                # Check QBP gates - disqualify anything outside 60-130% (proper engineering standards)
                if operating_zone == 'disqualified':
                    evaluation['feasible'] = False
                    evaluation['exclusion_reasons'].append(f'QBP {qbp:.0f}% outside allowable range')
                    return evaluation
                
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
            
            # CRITICAL: Physical capability validation at operating point
            if not self._validate_physical_capability_at_point(pump_data, flow, head):
                evaluation['feasible'] = False
                evaluation['excluded'] = True
                evaluation['exclusion_reasons'].append('Cannot deliver required head at operating flow')
                logger.debug(f"Pump {pump_data.get('pump_code')} excluded: Physical capability failed")
                return evaluation

            # Get performance at operating point
            performance = self.brain.performance.calculate_at_point(pump_data, flow, head)
            
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
                evaluation['head_m'] = performance.get('head_m', head)
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
                
                # NPSH handled as hard gate only in Legacy v6.0 (no scoring)
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
                evaluation['feasible'] = False
                evaluation['exclusion_reasons'].append('Cannot meet requirements')
                return evaluation
            
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