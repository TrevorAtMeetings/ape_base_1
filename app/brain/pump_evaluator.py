"""
Pump Evaluator Module
=====================
Single pump evaluation logic and scoring
"""

import logging
from typing import Dict, Any

from ..process_logger import process_logger
from .physical_validator import PhysicalValidator
from .scoring_utils import ScoringUtils

logger = logging.getLogger(__name__)


class PumpEvaluator:
    """Handles single pump evaluation and scoring"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        self.physical_validator = PhysicalValidator()
        self.scoring_utils = ScoringUtils()
        
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
    
    def evaluate_single_pump(self, pump_data: Dict[str, Any], 
                            flow: float, head: float, pump_code: str) -> Dict[str, Any]:
        """
        Evaluate a single pump at operating conditions.
        Implements Three-Path Selection Logic based on variable_speed and variable_diameter flags.
        
        Args:
            pump_data: Pump data dictionary
            flow: Operating flow rate
            head: Operating head
            pump_code: Pump code for logging
        
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
            
            # Log the path decision for ALL pumps - COMPREHENSIVE DECISION TRACKING
            process_logger.log("=" * 80)
            process_logger.log(f"PATH DECISION: {pump_code}")
            process_logger.log("=" * 80)
            process_logger.log(f"  Variable Speed: {variable_speed}")
            process_logger.log(f"  Variable Diameter: {variable_diameter}")
            process_logger.log(f"  → SELECTED PATH: {operation_mode} ({selection_method})")
            process_logger.log(f"  → Pump Flexibility: {evaluation.get('pump_flexibility', 'Not specified')}")
            
            # Debug logging for path decisions
            logger.debug(f"[THREE-PATH DECISION] {pump_code}: Mode={operation_mode}, Method={selection_method}")
            logger.debug(f"[THREE-PATH DECISION] {pump_code}: variable_speed={variable_speed}, variable_diameter={variable_diameter}")
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
            
            # Debug QBP calculation for all pumps
            logger.debug(f"[QBP DEBUG] {pump_data.get('pump_code', 'Unknown')}: BEP Flow: {bep_flow} m³/hr, Required: {flow} m³/hr")
            
            if bep_flow > 0 and bep_head > 0:
                # Calculate QBP (% of BEP flow)
                qbp = (flow / bep_flow) * 100
                
                # TIERED evaluation - NO REJECTIONS (show all pumps categorized by performance)
                if 80 <= qbp <= 110:
                    operating_zone = 'preferred'  # Optimal operating range
                    tier = 1
                    qbp_reasoning = "Sweet spot - optimal pump efficiency and performance"
                elif 60 <= qbp < 80 or 110 < qbp <= 140:
                    operating_zone = 'allowable'  # Good operating range
                    tier = 2
                    if qbp < 80:
                        qbp_reasoning = "Light loading - pump runs below optimal but efficient"
                    else:
                        qbp_reasoning = "Moderate overload - pump handles higher flow acceptably"
                elif 50 <= qbp < 60 or 140 < qbp <= 200:
                    operating_zone = 'acceptable'  # Acceptable for industrial use
                    tier = 3
                    if qbp < 60:
                        qbp_reasoning = "Significant under-loading - consider smaller pump"
                    else:
                        qbp_reasoning = "Heavy overload - monitor for cavitation and efficiency drop"
                else:
                    operating_zone = 'marginal'  # Outside typical range but still usable
                    tier = 4
                    if qbp < 50:
                        qbp_reasoning = "Severe under-loading - pump running far below design point"
                    else:
                        qbp_reasoning = "Extreme overload - high risk of cavitation and mechanical stress"
                
                # Log Operating Zone Classification decision
                process_logger.log(f"OPERATING ZONE ANALYSIS: {pump_code}")
                process_logger.log(f"  BEP Flow: {bep_flow:.1f} m³/hr")
                process_logger.log(f"  Target Flow: {flow:.1f} m³/hr") 
                process_logger.log(f"  QBP: {qbp:.1f}% of BEP")
                process_logger.log(f"  → ZONE DECISION: {operating_zone} (Tier {tier})")
                process_logger.log(f"  → REASONING: {qbp_reasoning}")
                
                evaluation['operating_zone'] = operating_zone
                evaluation['tier'] = tier
                evaluation['qbp_reasoning'] = qbp_reasoning
                
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
                        logger.info(f"Pump {pump_data.get('pump_code')}: SEVERE head oversizing {head_ratio_pct:.1f}% (>{self.severe_oversizing_threshold:.0f}%) - BEP {bep_head}m vs required {head}m")
                    else:
                        # Moderate oversizing (150-300% above requirement) - moderate penalty
                        oversizing_penalty = -15 - (head_ratio_pct - self.head_oversizing_threshold) * 0.1
                        logger.info(f"Pump {pump_data.get('pump_code')}: Head oversizing {head_ratio_pct:.1f}% ({self.head_oversizing_threshold:.0f}-{self.severe_oversizing_threshold:.0f}%) - BEP {bep_head}m vs required {head}m")
                    
                    evaluation['score_components']['head_oversizing_penalty'] = oversizing_penalty
                else:
                    # No penalty for reasonable BEP head ratios
                    evaluation['score_components']['head_oversizing_penalty'] = 0
            
            # Physical capability check - CONVERT TO SCORING PENALTY (no rejection)
            physical_capable, capability_reason = self.physical_validator.validate_physical_capability_at_point(pump_data, flow, head)
            if not physical_capable:
                # Apply severe scoring penalty but keep pump in results
                evaluation['score_components']['physical_limitation_penalty'] = -50
                evaluation['operating_zone'] = 'marginal'  # Force to marginal tier
                evaluation['tier'] = 4
                evaluation['physical_limitation_detail'] = capability_reason
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
                # Performance analyzer returned None - determine specific reason
                # Get more specific failure reason by checking pump data
                specs = pump_data.get('specifications', {})
                curves = pump_data.get('curves', [])
                
                failure_reasons = []
                
                # Check for missing critical specifications
                if not specs.get('bep_flow_m3hr') or specs.get('bep_flow_m3hr', 0) <= 0:
                    failure_reasons.append("Missing BEP flow specification")
                
                if not specs.get('bep_head_m') or specs.get('bep_head_m', 0) <= 0:
                    failure_reasons.append("Missing BEP head specification")
                
                if not specs.get('max_impeller_diameter_mm') or specs.get('max_impeller_diameter_mm', 0) <= 0:
                    failure_reasons.append("Missing maximum impeller diameter")
                
                # Check for curve data issues
                if not curves:
                    failure_reasons.append("No performance curves available")
                else:
                    valid_curves = 0
                    for curve in curves:
                        if curve.get('performance_points') and len(curve.get('performance_points', [])) >= 2:
                            valid_curves += 1
                    
                    if valid_curves == 0:
                        failure_reasons.append(f"All {len(curves)} curves have insufficient data points")
                    elif valid_curves < len(curves):
                        failure_reasons.append(f"Only {valid_curves}/{len(curves)} curves have valid data")
                
                # Check if affinity law calculation failed due to physical impossibility
                if physical_capable:
                    # Physical capability OK but performance calc failed - likely affinity law issue
                    failure_reasons.append("Affinity law calculation failed - cannot achieve target with impeller trimming")
                else:
                    # Add the physical capability failure detail
                    failure_reasons.append(f"Physical limitation: {capability_reason}")
                
                # Build comprehensive exclusion reason
                if failure_reasons:
                    detailed_reason = " | ".join(failure_reasons)
                else:
                    detailed_reason = "Performance calculation failed - unknown reason"
                
                process_logger.log(f"    {pump_code}: PERFORMANCE CALC FAILED - {detailed_reason}")
                logger.warning(f"[SELECTION] {pump_code}: Excluded - {detailed_reason}")
                evaluation['feasible'] = False
                evaluation['exclusion_reasons'].append(detailed_reason)
                return evaluation  # Return early - don't include in results
            
            # Log comprehensive scoring breakdown for ALL pumps
            process_logger.log(f"SCORING BREAKDOWN: {pump_code}")
            score_components = evaluation.get('score_components', {})
            total_score = 0
            
            for component, score in score_components.items():
                total_score += score
                # Add reasoning for each score component
                reasoning = self.scoring_utils.get_scoring_reason(component, score, evaluation)
                process_logger.log(f"  {component}: {score:.1f} pts ({reasoning})")
            
            process_logger.log(f"  → TOTAL SCORE: {total_score:.1f} pts")
            process_logger.log(f"  → FINAL TIER: {evaluation.get('operating_zone', 'unknown')} (Tier {evaluation.get('tier', '?')})")
            
            # Calculate total score
            evaluation['total_score'] = total_score
            
        except Exception as e:
            logger.error(f"Error in pump evaluation: {str(e)}")
            evaluation['feasible'] = False
            evaluation['exclusion_reasons'].append(f'Evaluation error: {str(e)}')
        
        return evaluation