"""
Performance Affinity Module
===========================
Affinity law calculations, diameter computations, and performance mathematics
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import interpolate
from .physics_models import get_exponents_for_pump_type
from ..process_logger import process_logger
from .config_manager import config

logger = logging.getLogger(__name__)


class AffinityCalculator:
    """Affinity law calculations and performance mathematics"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        
        # Performance thresholds
        self.min_efficiency = config.get('performance_affinity', 'minimum_acceptable_pump_efficiency_percentage')
        self.min_trim_percent = config.get('performance_affinity', 'industry_standard_minimum_trim_percentage_15_max_trim')  # Industry standard - 15% maximum trim, non-negotiable
        self.max_trim_percent = config.get('performance_affinity', 'maximum_trim_percentage_full_impeller')
        
        # Industry standard affinity law exponents
        self.affinity_flow_exp = config.get('performance_affinity', 'flow_scaling_exponent_in_affinity_laws_q2_q1__d2_d11')      # Q2/Q1 = (D2/D1)^1
        self.affinity_head_exp = config.get('performance_affinity', 'head_scaling_exponent_in_affinity_laws_h2_h1__d2_d12')      # H2/H1 = (D2/D1)^2  
        self.affinity_power_exp = config.get('performance_affinity', 'power_scaling_exponent_in_affinity_laws_p2_p1__d2_d13')     # P2/P1 = (D2/D1)^3
        self.affinity_efficiency_exp = config.get('performance_affinity', 'efficiency_scaling_exponent_in_affinity_laws') # η2/η1 ≈ (D2/D1)^0.8 (industry standard)
        
        # Load calibration factors
        self._load_calibration_factors()
    
    def _load_calibration_factors(self):
        """
        Load BEP migration calibration factors from configuration service.
        This allows for tunable physics model parameters.
        """
        self.calibration_factors = {}
        
        if hasattr(self.brain, 'get_config_service'):
            try:
                config_service = self.brain.get_config_service()
                self.calibration_factors = config_service.get_calibration_factors()
                logger.debug(f"Loaded {len(self.calibration_factors)} calibration factors from config service")
            except Exception as e:
                logger.debug(f"Could not load calibration factors: {e}")
                self.calibration_factors = {}
        
        # Set defaults for critical factors
        default_factors = {
            'bep_shift_flow_exponent': config.get('performance_affinity', 'bep_shift_flow_exponent_calibration_factor'),
            'bep_shift_head_exponent': config.get('performance_affinity', 'bep_shift_head_exponent_calibration_factor'),
            'trim_dependent_small_exponent': config.get('performance_affinity', 'trim_dependent_small_exponent'),
            'trim_dependent_large_exponent': config.get('performance_affinity', 'trim_dependent_large_exponent'),
            'efficiency_penalty_volute': config.get('performance_affinity', 'efficiency_penalty_factor_for_volute_pumps'),
            'efficiency_penalty_diffuser': config.get('performance_affinity', 'efficiency_penalty_factor_for_diffuser_pumps'),
            'npsh_degradation_threshold': config.get('performance_affinity', 'npsh_degradation_threshold_percentage'),
            'npsh_degradation_factor': config.get('performance_affinity', 'npsh_degradation_factor_for_heavy_trimming')
        }
        
        for factor, default in default_factors.items():
            if factor not in self.calibration_factors:
                self.calibration_factors[factor] = default
                
        logger.debug(f"Calibration factors loaded: {list(self.calibration_factors.keys())}")

    def calculate_specific_speed(self, rpm: float, bep_flow_m3hr: float, bep_head_m: float) -> float:
        """
        Calculate specific speed in US customary units for pump classification.
        Formula: Ns = (RPM * (Flow_GPM)^0.5) / (Head_ft)^0.75
        
        Args:
            rpm: Pump rotational speed
            bep_flow_m3hr: BEP flow rate in m³/hr
            bep_head_m: BEP head in meters
            
        Returns:
            Specific speed (dimensionless, US units)
        """
        if bep_head_m <= 0:
            logger.warning(f"[SPECIFIC SPEED] Invalid head value: {bep_head_m}m - returning 0")
            return 0
        
        # Convert to US units for standard Ns calculation
        gpm_conversion = config.get('dynamic_physics', 'gpm_to_m3hr_conversion_factor')
        ft_conversion = config.get('dynamic_physics', 'meters_to_feet_conversion_factor')
        
        bep_flow_gpm = bep_flow_m3hr / gpm_conversion
        bep_head_ft = bep_head_m * ft_conversion
        
        # Standard specific speed formula
        ns = (rpm * (bep_flow_gpm ** 0.5)) / (bep_head_ft ** 0.75)
        
        logger.debug(f"[SPECIFIC SPEED] RPM: {rpm}, Flow: {bep_flow_gpm:.1f} GPM, Head: {bep_head_ft:.1f} ft → Ns: {ns:.0f}")
        
        return ns

    def get_dynamic_physics_factors(self, pump_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get pump-specific physics factors based on specific speed classification.
        This replaces static calibration factors with intelligent, data-driven selection.
        
        Args:
            pump_data: Pump data dictionary
            
        Returns:
            Dictionary of dynamic physics factors for this specific pump
        """
        specs = pump_data.get('specifications', {})
        pump_code = pump_data.get('pump_code', 'Unknown')
        
        # Get BEP data and RPM
        bep_flow = specs.get('bep_flow_m3hr', 0)
        bep_head = specs.get('bep_head_m', 0)
        rpm = specs.get('speed_rpm', 1450)  # Default if missing
        
        # Calculate specific speed for classification
        ns = self.calculate_specific_speed(rpm, bep_flow, bep_head)
        
        # Dynamic factor selection based on Ns threshold
        ns_threshold = config.get('dynamic_physics', 'specific_speed_threshold_radial_to_mixed_flow')
        
        if ns < ns_threshold:
            # Low Specific Speed - Radial Flow Pump
            bep_shift_flow_exponent = config.get('dynamic_physics', 'bep_shift_flow_exponent_low_specific_speed_radial')
            pump_classification = 'RADIAL_FLOW'
            hydraulic_characteristics = 'Low specific speed - radial flow impeller design'
        else:
            # High Specific Speed - Mixed Flow Pump
            bep_shift_flow_exponent = config.get('dynamic_physics', 'bep_shift_flow_exponent_high_specific_speed_mixed')
            pump_classification = 'MIXED_FLOW'
            hydraulic_characteristics = 'High specific speed - mixed flow impeller design'
        
        # Get BEP prediction exponent (advanced physics)
        bep_shift_head_exponent = config.get('dynamic_physics', 'bep_shift_head_exponent_for_prediction')
        
        logger.info(f"[DYNAMIC PHYSICS] {pump_code}: Ns={ns:.0f} → {pump_classification} (threshold: {ns_threshold})")
        logger.info(f"[DYNAMIC PHYSICS] {pump_code}: Flow exponent: {bep_shift_flow_exponent} (vs static 1.2)")
        
        return {
            'bep_shift_flow_exponent': bep_shift_flow_exponent,
            'bep_shift_head_exponent': bep_shift_head_exponent,
            'specific_speed': ns,
            'pump_classification': pump_classification,
            'hydraulic_characteristics': hydraulic_characteristics,
            'ns_threshold': ns_threshold,
            'physics_source': 'DYNAMIC_DATA_DRIVEN'
        }

    def get_dynamic_efficiency_penalty(self, trim_percent: float) -> float:
        """
        Calculate efficiency penalty based on data-driven trim analysis.
        Replaces static penalty factors with trim-dependent logic.
        
        Args:
            trim_percent: Trim percentage (100 = full impeller, 85 = 15% trim)
            
        Returns:
            Efficiency penalty factor (epsilon)
        """
        # Convert to trim amount (how much was removed)
        trim_amount = 100 - trim_percent
        
        # Get thresholds from config
        penalty_threshold = config.get('dynamic_physics', 'trim_percentage_threshold_for_efficiency_penalty')
        
        if trim_amount <= 15.0:
            # For all practical trims, data shows zero penalty
            epsilon = config.get('dynamic_physics', 'efficiency_penalty_factor_for_standard_trim_range')
            rationale = "Within industry standard 15% trim limit - no penalty"
        elif trim_amount < penalty_threshold:
            # Extended range - still no penalty
            epsilon = config.get('dynamic_physics', 'efficiency_penalty_factor_for_standard_trim_range')
            rationale = f"Extended trim {trim_amount:.1f}% - no penalty below {penalty_threshold}%"
        else:
            # Excessive trim - apply penalty
            epsilon = config.get('dynamic_physics', 'efficiency_penalty_factor_for_excessive_trim')
            rationale = f"Excessive trim {trim_amount:.1f}% - applying penalty factor {epsilon}"
        
        logger.debug(f"[EFFICIENCY PENALTY] Trim: {trim_percent:.1f}% → Penalty: {epsilon} ({rationale})")
        
        return epsilon

    def get_calibration_factor(self, factor_name: str, default_value: float = 1.0) -> float:
        """
        Get a calibration factor by name with fallback to default.
        
        Args:
            factor_name: Name of calibration factor
            default_value: Default value if factor not found
            
        Returns:
            Calibration factor value
        """
        return self.calibration_factors.get(factor_name, default_value)

    def calculate_performance_at_flow(self, pump_data: Dict[str, Any], 
                                     flow: float, allow_excessive_trim: bool = False,
                                     forced_diameter: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Calculate pump performance at a specific flow rate.
        Used for BEP proximity analysis where we want to see what the pump can deliver.
        
        Args:
            pump_data: Pump data dictionary
            flow: Target flow rate (m3/hr)
            allow_excessive_trim: If True, show performance even with excessive trim
            forced_diameter: If provided, calculate at this exact diameter (mm) without optimization
        
        Returns:
            Performance data at the given flow, or None if pump cannot operate at this flow
        """
        # Log function entry
        process_logger.log(f"Executing: {__name__}.AffinityCalculator.calculate_performance_at_flow({pump_data.get('pump_code', 'Unknown')})")
        try:
            curves = pump_data.get('curves', [])
            if not curves:
                return None
            
            # Find the largest diameter curve
            largest_curve = max(curves, key=lambda c: c.get('impeller_diameter_mm', 0))
            curve_points = largest_curve.get('performance_points', [])
            
            if not curve_points:
                return None
            
            # FORCED DIAMETER CONSTRAINT: If a specific diameter is provided, use it
            if forced_diameter is not None:
                pump_code = pump_data.get('pump_code', 'Unknown')
                logger.info(f"[FORCED CONSTRAINT] {pump_code}: Using forced diameter {forced_diameter}mm for {flow} m3/hr")
                
                largest_diameter = largest_curve.get('impeller_diameter_mm', 0)
                if largest_diameter <= 0:
                    logger.error(f"[FORCED CONSTRAINT] {pump_code}: Invalid reference diameter")
                    return None
                
                # Get all available diameters from pump specifications (pump_diameters table)
                all_diameters = []
                if 'available_diameters' in pump_data and pump_data['available_diameters']:
                    # Use actual diameter specifications from database
                    all_diameters = [d for d in pump_data['available_diameters'] if d > 0]
                    all_diameters.sort()
                elif 'curves' in pump_data:
                    # Fallback to curve diameters if no specifications available
                    all_diameters = [c.get('impeller_diameter_mm', 0) for c in pump_data['curves'] if c.get('impeller_diameter_mm', 0) > 0]
                    all_diameters.sort()
                
                # Use actual diameter specifications instead of calculated ranges
                if all_diameters:
                    min_diameter = min(all_diameters)  # Use actual minimum from specifications
                    max_diameter = max(all_diameters)  # Use actual maximum from specifications
                else:
                    # Fallback calculation if no diameter data available
                    min_diameter = largest_diameter * config.get('performance_affinity', 'fallback_minimum_diameter_ratio_when_no_specifications_available')  
                    max_diameter = largest_diameter * config.get('performance_affinity', 'fallback_maximum_diameter_ratio_when_no_specifications_available')
                
                if forced_diameter < min_diameter or forced_diameter > max_diameter:
                    logger.error(f"[FORCED CONSTRAINT] {pump_code}: Forced diameter {forced_diameter}mm is outside calibration range [{min_diameter:.0f}-{max_diameter:.0f}mm]")
                    logger.error(f"[FORCED CONSTRAINT] {pump_code}: Available curves: {all_diameters}")
                    # For calibration analysis, return with warning instead of failure
                    logger.warning(f"[FORCED CONSTRAINT] {pump_code}: Proceeding with extrapolated performance - results may be inaccurate")
                    # Don't return None - continue with calculation using closest available diameter
                
                # Sort points by flow for interpolation
                sorted_points = sorted(curve_points, key=lambda p: p.get('flow_m3hr', 0))
                flows = [p['flow_m3hr'] for p in sorted_points if 'flow_m3hr' in p and 'head_m' in p]
                heads = [p['head_m'] for p in sorted_points if 'flow_m3hr' in p and 'head_m' in p]
                
                if len(flows) < 2:
                    return None
                
                # Interpolate reference performance at target flow
                head_interp = interpolate.interp1d(flows, heads, kind='linear',
                                                 bounds_error=False, fill_value=0.0)
                reference_head = float(head_interp(flow))
                
                if np.isnan(reference_head) or reference_head <= 0:
                    logger.error(f"[FORCED CONSTRAINT] {pump_code}: Invalid interpolated head")
                    return None
                
                # Apply affinity laws using forced diameter
                diameter_ratio = forced_diameter / largest_diameter
                delivered_head = reference_head * (diameter_ratio ** 2)  # Head scales with D^2
                
                logger.info(f"[FORCED CONSTRAINT] {pump_code}: Reference {largest_diameter}mm @ {flow} m3/hr = {reference_head:.2f}m")
                logger.info(f"[FORCED CONSTRAINT] {pump_code}: Forced to {forced_diameter}mm = {delivered_head:.2f}m (ratio: {diameter_ratio:.3f})")
                
                # Get efficiency with trim degradation
                efficiencies = [p.get('efficiency_pct', 0) for p in sorted_points if 'efficiency_pct' in p]
                if efficiencies and len(efficiencies) == len(flows):
                    eff_interp = interpolate.interp1d(flows, efficiencies, kind='linear',
                                                     bounds_error=False, fill_value=0.0)
                    base_efficiency = float(eff_interp(flow))
                else:
                    base_efficiency = config.get('performance_affinity', 'default_base_efficiency_when_interpolation_unavailable')  # Default
                
                # Apply efficiency degradation for excessive trimming
                trim_threshold = config.get('performance_affinity', 'trim_ratio_threshold_for_efficiency_degradation_15_trim')
                if diameter_ratio < trim_threshold:  # More than 15% trim
                    penalty_multiplier = config.get('performance_affinity', 'efficiency_penalty_multiplier_for_excessive_trimming')
                    efficiency_penalty = (trim_threshold - diameter_ratio) * penalty_multiplier
                    min_efficiency_floor = config.get('performance_affinity', 'minimum_efficiency_floor_after_trim_penalty')
                    efficiency = max(base_efficiency - efficiency_penalty, min_efficiency_floor)
                else:
                    efficiency = base_efficiency
                
                # Calculate power using affinity laws
                if efficiency > 0:
                    # Correct power calculation: P = ρ * g * Q * H / η
                    # Units: (kg/m3) * (m/s2) * (m3/hr) * (m) / efficiency / conversion = kW
                    water_density = config.get('performance_affinity', 'water_density_kg_m_')
                    gravity = config.get('performance_affinity', 'gravitational_acceleration_m_s')
                    seconds_per_hour = config.get('performance_affinity', 'seconds_per_hour_for_flow_conversions')
                    power_kw = (flow * delivered_head * water_density * gravity) / (seconds_per_hour * efficiency / 100 * 1000)
                else:
                    power_kw = 0
                
                # Calculate trim percentage
                trim_percent = (1 - diameter_ratio) * 100
                
                absolute_min_efficiency = config.get('performance_affinity', 'absolute_minimum_efficiency_floor')
                return {
                    'flow_m3hr': flow,
                    'head_m': delivered_head,
                    'efficiency_pct': max(efficiency, absolute_min_efficiency),
                    'power_kw': power_kw,
                    'npsh_r': 0,  # Would need more complex calculation
                    'diameter_mm': forced_diameter,
                    'impeller_diameter_mm': forced_diameter,
                    'trim_percent': trim_percent,
                    'reference_diameter_mm': largest_diameter,
                    'calculation_method': 'forced_constraint',
                    'note': f'Forced calculation at {forced_diameter}mm diameter'
                }
            
            # NORMAL FLOW: Continue with existing optimization logic if no forced_diameter
            
            # Sort points by flow
            sorted_points = sorted(curve_points, key=lambda p: p.get('flow_m3hr', 0))
            flows = [p['flow_m3hr'] for p in sorted_points if 'flow_m3hr' in p and 'head_m' in p]
            heads = [p['head_m'] for p in sorted_points if 'flow_m3hr' in p and 'head_m' in p]
            
            if len(flows) < 2:
                return None
            
            # Check if flow is within pump's range (with some tolerance)
            min_tolerance = config.get('performance_affinity', 'minimum_flow_tolerance_multiplier_50_below_minimum')
            max_tolerance = config.get('performance_affinity', 'maximum_flow_tolerance_multiplier_50_above_maximum')
            min_flow = min(flows) * min_tolerance  # Allow 50% below minimum
            max_flow = max(flows) * max_tolerance  # Allow 50% above maximum
            
            if not allow_excessive_trim and (flow < min_flow or flow > max_flow):
                return None
            
            # Interpolate head at the given flow
            # Use linear interpolation for head
            head_interp = interpolate.interp1d(flows, heads, kind='linear', 
                                              fill_value='extrapolate', bounds_error=False)
            delivered_head = float(head_interp(flow))
            
            # Get efficiency at this flow (if available)
            efficiencies = [p.get('efficiency_pct', 0) for p in sorted_points if 'efficiency_pct' in p]
            if efficiencies and len(efficiencies) == len(flows):
                eff_interp = interpolate.interp1d(flows, efficiencies, kind='linear',
                                                 fill_value='extrapolate', bounds_error=False)
                efficiency = float(eff_interp(flow))
            else:
                # Estimate efficiency based on BEP
                specs = pump_data.get('specifications', {})
                default_bep_efficiency = config.get('performance_affinity', 'default_bep_efficiency_for_estimation')
                bep_efficiency = specs.get('bep_efficiency_pct', default_bep_efficiency)
                bep_flow = specs.get('bep_flow_m3hr', flow)
                
                # Simple efficiency curve estimation
                flow_ratio = flow / bep_flow if bep_flow > 0 else 1.0
                lower_boundary = config.get('performance_affinity', 'lower_flow_ratio_boundary_for_good_efficiency')
                upper_boundary = config.get('performance_affinity', 'upper_flow_ratio_boundary_for_good_efficiency')
                efficiency_reduction_factor = config.get('performance_affinity', 'efficiency_reduction_factor_per_unit_flow_ratio_deviation')
                off_bep_multiplier = config.get('performance_affinity', 'efficiency_multiplier_for_significant_off_bep_operation')
                
                if lower_boundary <= flow_ratio <= upper_boundary:
                    efficiency = bep_efficiency * (1 - efficiency_reduction_factor * abs(1 - flow_ratio))
                else:
                    efficiency = bep_efficiency * off_bep_multiplier  # Significant drop off-BEP
            
            # Calculate power
            if efficiency > 0:
                # Correct power calculation: P = ρ * g * Q * H / η
                water_density = config.get('performance_affinity', 'water_density_kg_m_')
                gravity = config.get('performance_affinity', 'gravitational_acceleration_m_s')
                seconds_per_hour = config.get('performance_affinity', 'seconds_per_hour_for_flow_conversions')
                power_kw = (flow * delivered_head * water_density * gravity) / (seconds_per_hour * efficiency / 100 * 1000)
            else:
                power_kw = 0
            
            # Get NPSH if available
            npsh_r = 0
            flow_proximity_threshold = config.get('performance_affinity', 'flow_proximity_threshold_for_npsh_lookup_m3hr')
            for point in sorted_points:
                if abs(point.get('flow_m3hr', 0) - flow) < flow_proximity_threshold:  # Close to our flow
                    npsh_r = point.get('npsh_r', 0)
                    break
            
            absolute_min_efficiency = config.get('performance_affinity', 'absolute_minimum_efficiency_floor')
            return {
                'flow_m3hr': flow,
                'head_m': delivered_head,
                'efficiency_pct': max(efficiency, absolute_min_efficiency),  # Floor at configurable minimum
                'power_kw': power_kw,
                'npsh_r': npsh_r,
                'diameter_mm': largest_curve.get('impeller_diameter_mm', 0),
                'trim_percent': 0,  # Will be calculated if trimming is needed
                'note': f'Performance at {flow:.1f} m3/hr'
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance at flow: {e}")
            return None

    def calculate_required_diameter_direct(self, flows_sorted, heads_sorted, 
                                          largest_diameter, target_flow, target_head, pump_code, physics_exponents=None):
        """
        ENHANCED: Calculate required impeller diameter using direct affinity law formula.
        
        Uses the mathematically precise formula: D2 = D1 * sqrt(H2 / H1)
        where H1 is interpolated head at target flow on largest curve.
        
        Args:
            flows_sorted: Sorted flow data from largest curve
            heads_sorted: Sorted head data from largest curve  
            largest_diameter: Diameter of largest available impeller
            target_flow: Required flow rate (m3/hr)
            target_head: Required head (m)
            pump_code: Pump identifier for logging
            
        Returns:
            Tuple[float, float]: (required_diameter, trim_percent) or (None, None) if failed
        """
        try:
            # STEP 1: Interpolate head at target flow on largest curve (H1)
            if len(flows_sorted) < 2 or len(heads_sorted) < 2:
                return None, None
                
            head_interp = interpolate.interp1d(flows_sorted, heads_sorted, 
                                             kind='linear', bounds_error=False)
            
            # Check flow range coverage
            min_flow, max_flow = min(flows_sorted), max(flows_sorted)
            lower_tolerance = config.get('performance_affinity', 'lower_flow_range_tolerance_for_interpolation')
            upper_tolerance = config.get('performance_affinity', 'upper_flow_range_tolerance_for_interpolation')
            if not (min_flow * lower_tolerance <= target_flow <= max_flow * upper_tolerance):
                return None, None
            
            # Get head delivered by largest impeller at target flow (H1)
            base_head_at_flow = float(head_interp(target_flow))
            
            logger.debug(f"[AFFINITY] Interpolated head at {target_flow} m3/hr: {base_head_at_flow}m")
            
            if np.isnan(base_head_at_flow) or base_head_at_flow <= 0:
                logger.debug(f"[AFFINITY] Returning None due to invalid head")
                return None, None
            
            
            # STEP 2: Apply Direct Affinity Law Formula
            # H2 = H1 * (D2/D1)^2  →  D2 = D1 * sqrt(H2/H1)
            
            # FIXED: Trimming REDUCES head, so we can only trim if target < base head
            # We cannot achieve a head higher than what the full-diameter impeller delivers
            # Special tolerance for BEP testing - allow small precision differences
            bep_tolerance = config.get('performance_affinity', 'bep_precision_tolerance_for_head_comparison')  # 5% tolerance for BEP precision issues
            safety_margin = config.get('performance_affinity', 'head_safety_margin_for_bep_calculations')
            if target_head > base_head_at_flow * bep_tolerance:
                logger.debug(f"[AFFINITY] Target {target_head:.2f}m > max {base_head_at_flow * bep_tolerance:.2f}m - returning None")
                return None, None
            elif target_head > base_head_at_flow * safety_margin:
                logger.info(f"[BEP TOLERANCE] {pump_code}: Allowing BEP precision difference - target {target_head:.2f}m vs base {base_head_at_flow:.2f}m")
            
            logger.debug(f"[AFFINITY] Head check passed: {target_head:.2f}m <= {base_head_at_flow * safety_margin:.2f}m")
            
            # Good case: target_head < base_head_at_flow means we can trim to reduce head
            
            # Calculate required diameter using RESEARCH-BASED trim-dependent physics
            # Research: Exponent varies from 2.8-3.0 for small trims to 2.0-2.2 for large trims
            # Use pump-type-specific head exponent from physics model
            if physics_exponents and 'head_exponent_y' in physics_exponents:
                head_exponent = physics_exponents['head_exponent_y']
                process_logger.log(f"    Using physics model exponent: {head_exponent}")
            else:
                # Fallback to trim-dependent exponents if physics model not provided
                trim_exponent = config.get('performance_affinity', 'exponent_for_trim_percentage_estimation')
                estimated_trim_pct = (1.0 - (target_head / base_head_at_flow) ** trim_exponent) * config.get('performance_affinity', 'percentage_conversion_factor')
                
                small_trim_threshold_pct = config.get('performance_affinity', 'small_trim_threshold_percentage')
                default_small_exponent = config.get('performance_affinity', 'default_small_trim_head_exponent')
                default_large_exponent = config.get('performance_affinity', 'default_large_trim_head_exponent')
                
                if estimated_trim_pct < small_trim_threshold_pct:
                    # Small trim: Use higher exponent (research: 2.8-3.0)
                    head_exponent = self.get_calibration_factor('trim_dependent_small_exponent', default_small_exponent)
                    small_trim_threshold = "small"  # Reference to classification logic
                    process_logger.log(f"    {small_trim_threshold.title()} trim (~{estimated_trim_pct:.1f}%): Using exponent {head_exponent}")
                else:
                    # Larger trim: Use standard exponent (research: 2.0-2.2)
                    head_exponent = self.get_calibration_factor('trim_dependent_large_exponent', default_large_exponent)
                    large_trim_threshold = "large"  # Reference to classification logic  
                    process_logger.log(f"    {large_trim_threshold.title()} trim (~{estimated_trim_pct:.1f}%): Using exponent {head_exponent}")
            
            # H2/H1 = (D2/D1)^head_exp  →  D2 = D1 * (H2/H1)^(1/head_exp)
            # FIXED: Ensure all values are float to avoid decimal/float mixing in power operations
            target_head_float = float(target_head)
            base_head_float = float(base_head_at_flow)
            largest_diameter_float = float(largest_diameter)
            head_exponent_float = float(head_exponent)
            
            # Log the actual formula calculation with real values
            process_logger.log(f"    Affinity Law Calculation:")
            process_logger.log(f"      D1 (largest): {largest_diameter_float:.1f} mm")
            process_logger.log(f"      H1 (at target flow): {base_head_float:.2f} m")
            process_logger.log(f"      H2 (target): {target_head_float:.2f} m")
            process_logger.log(f"      Head exponent: {head_exponent_float}")
            process_logger.log(f"      Formula: D2 = {largest_diameter_float:.1f} * ({target_head_float:.2f}/{base_head_float:.2f})^(1/{head_exponent_float})")
            
            diameter_ratio = np.power(target_head_float / base_head_float, 1.0 / head_exponent_float)
            required_diameter = largest_diameter_float * diameter_ratio
            trim_percent = diameter_ratio * config.get('performance_affinity', 'percentage_conversion_factor')
            
            process_logger.log(f"      Result: D2 = {largest_diameter_float:.1f} * {diameter_ratio:.4f} = {required_diameter:.1f} mm")
            process_logger.log(f"      Trim: {trim_percent:.2f}%")
            
            logger.info(f"[TUNABLE AFFINITY] {pump_code}: Using head exponent {head_exponent} (vs standard 2.0)")
            
            logger.info(f"[TUNABLE AFFINITY] {pump_code}: Diameter ratio = ({target_head:.2f}/{base_head_at_flow:.2f})^(1/{head_exponent}) = {diameter_ratio:.4f}")
            logger.info(f"[TUNABLE AFFINITY] {pump_code}: Required diameter = {largest_diameter:.1f} * {diameter_ratio:.4f} = {required_diameter:.1f}mm")
            logger.info(f"[TUNABLE AFFINITY] {pump_code}: Trim percentage = {trim_percent:.2f}%")
            
            # STEP 3: Validate trim limits (industry standard: 85-100%)
            logger.debug(f"[AFFINITY] Checking trim limits: {trim_percent:.2f}% vs [{self.min_trim_percent}, {self.max_trim_percent}]")
            
            if trim_percent < self.min_trim_percent:
                logger.debug(f"[AFFINITY] Trim too small: {trim_percent:.1f}% < {self.min_trim_percent}%")
                return None, None
            
            if trim_percent > self.max_trim_percent:
                logger.debug(f"[AFFINITY] Trim too large: {trim_percent:.1f}% > {self.max_trim_percent}%")
                return None, None
            
            # STEP 4: Enhanced validation - verify result makes physical sense
            # Calculate what head this diameter would actually deliver using SAME trim-dependent physics
            verification_head = base_head_at_flow * (diameter_ratio ** head_exponent)
            error_percent = abs(verification_head - target_head) / target_head * 100
            
            
            error_threshold = config.get('performance_affinity', 'error_percent_threshold_for_validation_warning')
            if error_percent > error_threshold:  # Should be essentially zero for direct calculation
                logger.warning(f"[DIRECT AFFINITY] {pump_code}: Unexpected calculation error: {error_percent:.2f}%")
            
            # Enhanced logging for calculations
            logger.debug(f"[TRIM] {pump_code}: Direct calculation complete")
            logger.debug(f"[TRIM] {pump_code}: H1 = {base_head_at_flow:.2f}m, H2 = {target_head:.2f}m")
            logger.debug(f"[TRIM] {pump_code}: D1 = {largest_diameter:.1f}mm, D2 = {required_diameter:.1f}mm")
            logger.debug(f"[TRIM] {pump_code}: Trim = {trim_percent:.2f}% (vs iterative method)")
            
            return required_diameter, trim_percent
            
        except Exception as e:
            logger.error(f"[DIRECT AFFINITY ERROR] {pump_code}: {e}")
            logger.debug(f"[AFFINITY DEBUG] Exception details: {e}")
            logger.debug(f"[AFFINITY DEBUG] flows_sorted length: {len(flows_sorted) if flows_sorted else 'None'}")
            logger.debug(f"[AFFINITY DEBUG] heads_sorted length: {len(heads_sorted) if heads_sorted else 'None'}")
            return None, None

    def apply_affinity_laws(self, base_curve: Dict[str, Any],
                           target_diameter: float, target_flow: float, target_head: float,
                           pump_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply affinity laws to scale performance from base curve to target conditions.
        
        Args:
            base_curve: Base impeller curve data
            target_diameter: Target impeller diameter (mm)
            target_flow: Target flow rate (m3/hr)
            target_head: Target head (m)
            pump_data: Complete pump data for context
            
        Returns:
            Scaled performance data
        """
        try:
            base_diameter = base_curve.get('impeller_diameter_mm', 0)
            if base_diameter <= 0 or target_diameter <= 0:
                return {}
            
            # Calculate diameter ratio
            diameter_ratio = target_diameter / base_diameter
            
            # Apply affinity laws
            # Q2/Q1 = (D2/D1)^1
            # H2/H1 = (D2/D1)^2
            # P2/P1 = (D2/D1)^3
            # η2/η1 ≈ (D2/D1)^0.8 (approximate)
            
            # Base performance at target flow (interpolated)
            curve_points = base_curve.get('performance_points', [])
            if not curve_points:
                return {}
            
            # Sort and extract data
            sorted_points = sorted(curve_points, key=lambda p: p.get('flow_m3hr', 0))
            flows = [p['flow_m3hr'] for p in sorted_points if 'flow_m3hr' in p and 'head_m' in p]
            heads = [p['head_m'] for p in sorted_points if 'flow_m3hr' in p and 'head_m' in p]
            
            if len(flows) < 2:
                return {}
            
            # Calculate equivalent flow on base curve
            # Q_base = Q_target / (D_target/D_base)^1
            base_equivalent_flow = target_flow / (diameter_ratio ** self.affinity_flow_exp)
            
            # Interpolate base curve performance
            head_interp = interpolate.interp1d(flows, heads, kind='linear',
                                             bounds_error=False, fill_value=0.0)
            base_head = float(head_interp(base_equivalent_flow))
            
            # Get base efficiency
            efficiencies = [p.get('efficiency_pct', 0) for p in sorted_points if 'efficiency_pct' in p]
            if efficiencies and len(efficiencies) == len(flows):
                fill_value = config.get('performance_affinity', 'fill_value_for_efficiency_interpolation')
                eff_interp = interpolate.interp1d(flows, efficiencies, kind='linear',
                                                 bounds_error=False, fill_value=fill_value)
                base_efficiency = float(eff_interp(base_equivalent_flow))
            else:
                base_efficiency = config.get('performance_affinity', 'default_base_efficiency_when_interpolation_unavailable')  # Default
            
            # Apply affinity laws
            scaled_head = base_head * (diameter_ratio ** self.affinity_head_exp)
            scaled_efficiency = base_efficiency * (diameter_ratio ** self.affinity_efficiency_exp)
            
            # Calculate power
            if scaled_efficiency > 0:
                scaled_power = self.calculate_hydraulic_power(target_flow, scaled_head, scaled_efficiency)
            else:
                scaled_power = 0
            
            return {
                'flow_m3hr': target_flow,
                'head_m': scaled_head,
                'efficiency_pct': max(scaled_efficiency, self.min_efficiency),
                'power_kw': scaled_power,
                'impeller_diameter_mm': target_diameter,
                'base_diameter_mm': base_diameter,
                'diameter_ratio': diameter_ratio,
                'scaling_method': 'affinity_laws'
            }
            
        except Exception as e:
            logger.error(f"Error applying affinity laws: {e}")
            return {}

    def calculate_hydraulic_power(self, flow_m3hr: float, head_m: float, 
                                  efficiency_pct: float) -> float:
        """
        Calculate hydraulic power requirement.
        
        Args:
            flow_m3hr: Flow rate in m3/hr
            head_m: Head in meters
            efficiency_pct: Pump efficiency percentage
            
        Returns:
            Power in kW
        """
        if efficiency_pct <= 0 or flow_m3hr <= 0 or head_m <= 0:
            return 0.0
        
        # P = ρ * g * Q * H / η
        # Where: ρ = 1000 kg/m3, g = 9.81 m/s2, Q in m3/s, H in m
        water_density = config.get('performance_affinity', 'water_density_kg_m_')
        gravity = config.get('performance_affinity', 'gravitational_acceleration_m_s')
        seconds_per_hour = config.get('performance_affinity', 'seconds_per_hour_for_flow_conversions')
        flow_m3s = flow_m3hr / seconds_per_hour  # Convert to m3/s
        power_w = (water_density * gravity * flow_m3s * head_m) / (efficiency_pct / 100)
        power_kw = power_w / 1000  # Convert to kW
        
        return power_kw