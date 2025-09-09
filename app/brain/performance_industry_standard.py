"""
Performance Industry Standard Module
====================================
Core industry-standard performance calculations and affinity law applications
"""

import logging
import numpy as np
from typing import Dict, Any, Optional
from scipy import interpolate
from .physics_models import get_exponents_for_pump_type
from .config_manager import config

logger = logging.getLogger(__name__)


class IndustryStandardCalculator:
    """Industry standard performance calculations"""
    
    def __init__(self, brain, validator, optimizer):
        """
        Initialize with reference to main Brain and other calculators.
        
        Args:
            brain: Parent PumpBrain instance
            validator: PerformanceValidator instance
            optimizer: PerformanceOptimizer instance
        """
        self.brain = brain
        self.validator = validator
        self.optimizer = optimizer
        
        # Load configuration values for industry standard calculations
        self.flow_range_min = config.get('performance_industry_standard', 'flow_range_tolerance_minimum_multiplier_90')
        self.flow_range_max = config.get('performance_industry_standard', 'flow_range_tolerance_maximum_multiplier_110')
        self.bep_flow_threshold = config.get('performance_industry_standard', 'flow_deviation_threshold_for_authentic_bep_efficiency_15')
        self.head_capability_threshold = config.get('performance_industry_standard', 'head_capability_threshold_multiplier_115_above_target')
        self.min_head_delivery = config.get('performance_industry_standard', 'minimum_head_delivery_factor_98_of_required')
        self.severe_shortfall_threshold = config.get('performance_industry_standard', 'severe_head_shortfall_threshold_70_of_target')
        # Trim percentage is not in performance_industry_standard section, use fallback from performance_affinity
        self.min_trim_percent = config.get('performance_affinity', 'industry_standard_minimum_trim_percentage_15_max_trim')
        self.qbp_penalty_threshold = config.get('performance_industry_standard', 'qbp_efficiency_penalty_threshold_percentage')
        self.qbp_penalty_base = config.get('performance_industry_standard', 'qbp_efficiency_penalty_base_factor_10')
        self.qbp_penalty_divisor = config.get('performance_industry_standard', 'qbp_efficiency_penalty_divisor_for_calculations')
        self.qbp_penalty_lower_bound = config.get('performance_industry_standard', 'qbp_efficiency_penalty_lower_bound_percentage')
        
        # Physical constants and conversion factors - access by finding keys dynamically to avoid Unicode issues
        section = config.performance_industry_standard
        
        # Find water density key (contains special characters)
        water_key = None
        for key in section.keys():
            if key.startswith('water_density') and 'hydraulic' in key and key.endswith('_value'):
                water_key = key[:-6]  # Remove '_value' suffix
                break
        
        # Find gravitational acceleration key (contains special characters)
        gravity_key = None
        for key in section.keys():
            if key.startswith('gravitational') and key.endswith('_value'):
                gravity_key = key[:-6]  # Remove '_value' suffix
                break
        
        # Set values using found keys
        self.water_density = config.get('performance_industry_standard', water_key) if water_key else 1000
        self.gravitational_acceleration = config.get('performance_industry_standard', gravity_key) if gravity_key else 9.81
        self.seconds_per_hour = config.get('performance_industry_standard', 'seconds_per_hour_conversion')
        self.percentage_conversion = config.get('performance_industry_standard', 'percentage_conversion_factor')
        
        # Manufacturer reference values - using actual available keys
        self.manufacturer_diameter_ratio = config.get('performance_industry_standard', 'manufacturer_diameter_ratio_reference_8835')
        self.expected_delivered_head = config.get('performance_industry_standard', 'expected_delivered_head_for_manufacturer_analysis_m')
        self.trim_analysis_reference = config.get('performance_industry_standard', 'trim_analysis_reference_value')
        self.manufacturer_trim_reference = config.get('performance_industry_standard', 'manufacturer_trim_reference_percentage')
        
        # Efficiency calculation factors - using actual available keys
        self.efficiency_drop_base_factor = config.get('performance_industry_standard', 'efficiency_drop_calculation_base_factor')
        self.efficiency_penalty_diffuser_default = config.get('performance_industry_standard', 'efficiency_penalty_diffuser_default_factor')
        self.efficiency_penalty_volute_default = config.get('performance_industry_standard', 'efficiency_penalty_volute_default_factor')
        
        # NPSH calculations - using actual available keys
        self.npsh_degradation_threshold = config.get('performance_industry_standard', 'npsh_degradation_threshold_default')
        self.npsh_degradation_factor = config.get('performance_industry_standard', 'npsh_degradation_factor_default')
        
        # QBP calculations - using actual available keys  
        self.default_true_qbp_percentage = config.get('performance_industry_standard', 'default_true_qbp_percentage')

    def calculate_at_point_industry_standard(self, pump_data: Dict[str, Any], flow: float, 
                          head: float, impeller_trim: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        INDUSTRY STANDARD: Calculate pump performance using proper affinity law trimming from largest impeller.
        
        Methodology:
        1. Find largest available impeller curve (e.g., 450mm)
        2. Interpolate performance at target flow on this curve
        3. Use affinity laws to trim DOWN to meet target head
        4. Limit trimming to 15% maximum (85% of max diameter)
        
        Args:
            pump_data: Pump data with curves
            flow: Operating flow rate (m³/hr) 
            head: Operating head (m)
            impeller_trim: Optional trim percentage
            
        Returns:
            Performance calculations using manufacturer methodology
        """
        try:
            pump_code = pump_data.get('pump_code')
            
            # Get pump-type-specific physics model exponents
            physics_exponents = self.validator.get_exponents_for_pump(pump_data)
            
            # Enhanced debugging for HC pumps and 8/8 DME
            if pump_code and ("HC" in str(pump_code)):
                logger.error(f"[DEBUG] Starting calculation for {pump_code}")
                logger.error(f"[DEBUG] Requirements: {flow} m³/hr @ {head}m")
                logger.error(f"[DEBUG] Pump data keys: {list(pump_data.keys())}")
                logger.error(f"[DEBUG] Using physics model - Flow exp: {physics_exponents['flow_exponent_x']}, Head exp: {physics_exponents['head_exponent_y']}")
            
            curves = pump_data.get('curves', [])
            
            if pump_code and ("HC" in str(pump_code)):
                logger.error(f"[DEBUG] Found {len(curves)} curves")
                if curves:
                    for i, curve in enumerate(curves):
                        logger.error(f"[DEBUG] Curve {i}: diameter={curve.get('impeller_diameter_mm')}, points={len(curve.get('performance_points', []))}")
            
            if not curves:
                if pump_code and "HC" in str(pump_code):
                    logger.error(f"[DEBUG] {pump_code}: NO CURVES FOUND - This is why calculation fails!")
                return None
            
            # INDUSTRY STANDARD: Find largest impeller curve (manufacturer approach)
            largest_curve = None
            largest_diameter = 0
            
            for curve in curves:
                diameter = curve.get('impeller_diameter_mm', 0)
                if diameter > largest_diameter:
                    largest_diameter = diameter
                    largest_curve = curve
            
            if not largest_curve or largest_diameter <= 0:
                if pump_code and ("HC" in str(pump_code)):
                    logger.error(f"[DEBUG] No valid curves found - largest_diameter: {largest_diameter}")
                    logger.error(f"[DEBUG] {pump_code}: INVALID CURVES - This is why calculation fails!")
                return None
                
            logger.debug(f"[INDUSTRY] {pump_code}: Using largest impeller {largest_diameter}mm as base curve")
            
            if pump_code:
                logger.error(f"[{pump_code}] Using largest impeller {largest_diameter}mm")
            
            # Get performance points from largest curve
            curve_points = largest_curve.get('performance_points', [])
            logger.debug(f"[INDUSTRY] {pump_code}: Largest curve has {len(curve_points)} performance points")
            
            if not curve_points or len(curve_points) < 2:
                logger.debug(f"[INDUSTRY] {pump_code}: Largest curve has insufficient points - cannot proceed")
                return None
                
            # Extract curve data, handling None values  
            flows = [p.get('flow_m3hr', 0) for p in curve_points if p.get('flow_m3hr') is not None]
            heads = [p.get('head_m', 0) for p in curve_points if p.get('head_m') is not None] 
            effs = [p.get('efficiency_pct', 0) for p in curve_points if p.get('efficiency_pct') is not None]
            
            logger.debug(f"[INDUSTRY] {pump_code}: Largest curve data - flows: {len(flows)}, heads: {len(heads)}, effs: {len(effs)}")
            if flows:
                logger.debug(f"[INDUSTRY] {pump_code}: Flow range: {min(flows):.1f} - {max(flows):.1f} m³/hr")
                
           # Handle None power values - mark as missing (NO FALLBACKS EVER)
            powers = []
            for p in curve_points:
                power = p.get('power_kw')
                if power is not None:
                    powers.append(power)
                else:
                    powers.append(None)  # Mark missing data explicitly
            
            # Check if flow is within curve range
            if not flows or not heads:
                logger.debug(f"[INDUSTRY] {pump_code}: Largest curve missing flow or head data")
                return None
            
            min_flow, max_flow = min(flows), max(flows)
            logger.debug(f"[INDUSTRY] {pump_code}: Checking flow range: {min_flow:.1f} - {max_flow:.1f} vs required {flow}")
            
            if not (min_flow * self.flow_range_min <= flow <= max_flow * self.flow_range_max):
                logger.debug(f"[INDUSTRY] {pump_code}: Flow {flow} outside curve range {min_flow*self.flow_range_min:.1f} - {max_flow*self.flow_range_max:.1f}")
                if pump_code and "8/8 DME" in str(pump_code):
                    logger.error(f"[8/8 DME DEBUG] Flow {flow} outside range {min_flow*self.flow_range_min:.1f} - {max_flow*self.flow_range_max:.1f}")
                return None
                
            logger.debug(f"[INDUSTRY] {pump_code}: Starting interpolation on largest curve...")
            
            try:
                # Sort data by flow to ensure monotonic interpolation
                sorted_points = sorted(zip(flows, heads, effs, powers), key=lambda p: p[0])
                flows_sorted, heads_sorted, effs_sorted, powers_sorted = zip(*sorted_points)
                
                logger.debug(f"[INDUSTRY] {pump_code}: Creating interpolation functions with sorted data...")
                
                # CRITICAL DEBUG: Show actual performance points for problematic pumps
                if pump_code:
                    logger.error(f"[CURVE DEBUG] {pump_code}: Using {largest_diameter}mm diameter curve")
                    logger.error(f"[CURVE DEBUG] {pump_code}: Performance points: {list(zip(flows_sorted, heads_sorted))}")
                
                # Create interpolation functions using SORTED data
                head_interp = interpolate.interp1d(flows_sorted, heads_sorted, 
                                                 kind='linear', bounds_error=False)
                eff_interp = interpolate.interp1d(flows_sorted, effs_sorted, 
                                                kind='linear', bounds_error=False)
                
                logger.debug(f"[INDUSTRY] {pump_code}: Executing interpolation at flow {flow}...")
                
                # STEP 1: Get performance at target flow on largest curve
                delivered_head = float(head_interp(flow))
                
                # CRITICAL FIX: Use authentic BEP efficiency from specifications when available
                specs = pump_data.get('specifications', {})
                authentic_bep_efficiency = specs.get('bep_efficiency', 0)
                bep_flow = specs.get('bep_flow_m3hr', 0)
                
                # If operating near BEP flow and authentic efficiency is available, use it
                if authentic_bep_efficiency > 0 and bep_flow > 0:
                    flow_deviation = abs(flow - bep_flow) / bep_flow
                    if flow_deviation < self.bep_flow_threshold:  # Within configured threshold of BEP flow
                        base_efficiency = authentic_bep_efficiency
                        logger.debug(f"[INDUSTRY] {pump_code}: Using authentic BEP efficiency {base_efficiency:.1f}% (near BEP flow)")
                    else:
                        # Interpolate efficiency at target flow (industry standard)
                        base_efficiency = float(eff_interp(flow))
                        logger.debug(f"[INDUSTRY] {pump_code}: Using interpolated efficiency {base_efficiency:.1f}% (away from BEP)")
                else:
                    # Fallback to interpolation when no authentic data
                    base_efficiency = float(eff_interp(flow))
                    logger.debug(f"[INDUSTRY] {pump_code}: Using interpolated efficiency {base_efficiency:.1f}% (no authentic BEP data)")
                
                logger.debug(f"[INDUSTRY] {pump_code}: Base curve performance - head: {delivered_head:.2f}m, eff: {base_efficiency:.1f}%")
                
                # Special debug for 6 WLN 18A
                if pump_code:
                    logger.error(f"[{pump_code}] Flow: {flow}, Required head: {head}")
                    logger.error(f"[DEBUG {pump_code}] Delivered head: {delivered_head:.2f}m")
                    logger.error(f"[DEBUG {pump_code}] Largest diameter: {largest_diameter}mm")
                    logger.error(f"[DEBUG {pump_code}] Performance points: {len(curve_points)}")
                    logger.error(f"[DEBUG {pump_code}] Flow range: {min(flows)} to {max(flows)} m³/hr")
                    logger.error(f"[DEBUG {pump_code}] Head range: {min(heads)} to {max(heads)} m")
                    
                    # CRITICAL ANALYSIS: Compare with manufacturer expectation
                    # Manufacturer shows 11.65% trim, which means 88.35% diameter
                    # This corresponds to head ratio: (88.35/100)² = 0.781
                    # Expected delivered head: 50m / 0.781 = 64.0m
                    manufacturer_head_ratio = self.manufacturer_diameter_ratio ** 2
                    expected_delivered_head = head / manufacturer_head_ratio
                    logger.error(f"[TRIM ANALYSIS] Manufacturer expects: {self.expected_delivered_head}m delivered head for {self.manufacturer_trim_reference}% trim")
                    logger.error(f"[TRIM ANALYSIS] Our data shows: {delivered_head:.2f}m delivered head")
                    logger.error(f"[TRIM ANALYSIS] Difference: {delivered_head - self.expected_delivered_head:.2f}m higher than expected")
                    trim_diff = self.trim_analysis_reference - self.manufacturer_trim_reference
                    logger.error(f"[TRIM ANALYSIS] This explains why our trim is {trim_diff + self.manufacturer_trim_reference:.1f}% vs manufacturer's {self.manufacturer_trim_reference}%")
                
                # Check for NaN values (NO FALLBACKS EVER)
                if np.isnan(delivered_head) or np.isnan(base_efficiency):
                    logger.debug(f"[INDUSTRY] {pump_code}: NaN interpolation result - cannot proceed")
                    return None
                
                # STEP 2: ALWAYS USE LARGEST IMPELLER AS REFERENCE (Industry Standard)
                # Even if target head is below the largest curve's capability,
                # we should trim from the largest impeller for best hydraulic design
                if delivered_head > head * self.head_capability_threshold:  # Target head is significantly below largest curve capability
                    logger.debug(f"[INDUSTRY] {pump_code}: Target head {head:.2f}m below largest curve {delivered_head:.2f}m - will trim from largest impeller")
                    
                    if pump_code:
                        logger.error(f"[{pump_code} DEBUG] Target {head:.2f}m below largest curve {delivered_head:.2f}m")
                        logger.error(f"[{pump_code} DEBUG] Will trim from largest impeller 527mm (industry standard)")
                    
                    # REMOVED: Smaller curve selection logic - always use largest impeller
                    # Industry best practice is to use the largest impeller and trim down
                    logger.debug(f"[INDUSTRY] {pump_code}: Using largest impeller {largest_diameter}mm as reference")
                
                # Allow some tolerance - pump should deliver at least configured percentage of required head
                if delivered_head < head * self.min_head_delivery:
                    logger.warning(f"[INDUSTRY] {pump_code}: Insufficient head capability - base curve gives {delivered_head:.2f}m < required {head*self.min_head_delivery:.2f}m")
                    # Only provide capability estimate if the pump could theoretically work with reasonable trim
                    # Check if using maximum impeller would require impossible trim to reach target
                    max_possible_head = delivered_head  # This is what pump can deliver at full impeller
                    if max_possible_head < head * self.severe_shortfall_threshold:  # If pump can't even get close
                        logger.warning(f"[PHYSICAL LIMIT] {pump_code}: Head shortfall too severe ({max_possible_head:.1f}m vs {head:.1f}m required) - pump rejected")
                        return None
                    
                    logger.info(f"[FALLBACK] {pump_code or 'Unknown'}: Capability estimate fallback disabled - pump rejected")
                    return None  # Explicit rejection - no capability estimates allowed
                            
                # Get BEP data for efficiency optimization
                original_bep_flow = specs.get('bep_flow_m3hr', 0)
                original_bep_head = specs.get('bep_head_m', 0)
                
                optimal_trim_result = self.optimizer.calculate_efficiency_optimized_trim(
                    flows_sorted, heads_sorted, largest_diameter, flow, head, 
                    original_bep_flow, original_bep_head, pump_code or "Unknown", physics_exponents
                )
                
                # Extract diameter and trim for compatibility with existing code
                if optimal_trim_result:
                    required_diameter = optimal_trim_result['required_diameter_mm']
                    trim_percent = optimal_trim_result['trim_percent']
                    logger.info(f"[EFFICIENCY OPTIMIZED] {pump_code}: Selected {trim_percent:.1f}% trim (score: {optimal_trim_result.get('optimization_score', 'N/A'):.1f})")
                else:
                    # If efficiency optimization fails, use standard affinity law calculation
                    logger.info(f"[STANDARD AFFINITY] {pump_code}: Using standard affinity law calculation")
                    
                    # Calculate required diameter using standard affinity laws
                    # D2/D1 = sqrt(H2/H1) for constant flow
                    import math
                    if delivered_head > 0 and head <= delivered_head:
                        diameter_ratio = math.sqrt(head / delivered_head)
                        required_diameter = largest_diameter * diameter_ratio
                        trim_percent = (1 - diameter_ratio) * 100
                        
                        logger.info(f"[STANDARD AFFINITY] {pump_code}: Required diameter {required_diameter:.1f}mm, trim {trim_percent:.1f}%")
                    else:
                        logger.warning(f"[STANDARD AFFINITY] {pump_code}: Cannot achieve required head - pump may not be suitable")
                        return None
          
                if required_diameter is None or required_diameter <= 0:
                    logger.error(f"[NO FALLBACKS] {pump_code}: Could not determine required diameter using affinity laws - pump rejected")
                    return None  # Explicit rejection - no hydraulic approximations
                    
                logger.debug(f"[INDUSTRY] {pump_code}: Affinity law result - required diameter: {required_diameter:.1f}mm (trim: {trim_percent:.1f}%)")
                
                # STEP 4: Check trim limits - use configured minimum
                if trim_percent is not None and trim_percent < self.min_trim_percent:
                    logger.warning(f"[INDUSTRY] {pump_code}: Excessive trim required ({trim_percent:.1f}% < {self.min_trim_percent}%) - beyond safe limits")
                    # CRITICAL DIAGNOSIS: Log the exact values causing excessive trim
                    logger.error(f"[TRIM DEBUG] {pump_code}: Required {head}m but delivered {delivered_head:.1f}m at {flow} m³/hr")
                    # Calculate these values for debugging (they're needed for the error message)
                    head_ratio = head / delivered_head if delivered_head > 0 else 0
                    diameter_ratio = required_diameter / largest_diameter if largest_diameter > 0 else 0
                    logger.error(f"[TRIM DEBUG] {pump_code}: head_ratio={head_ratio:.3f}, diameter_ratio={diameter_ratio:.3f}")
                    logger.error(f"[TRIM DEBUG] {pump_code}: Using curve with {largest_diameter}mm diameter, {len(curve_points)} points")
                    
                    # PHYSICAL LIMIT ENFORCEMENT: Do not provide estimates for impossible trim scenarios
                    logger.warning(f"[PHYSICAL LIMIT] {pump_code}: Trim {trim_percent:.1f}% exceeds physical capability - pump rejected")
                    return None
                
                # STEP 5: Calculate performance at the required diameter using affinity laws
                diameter_ratio = required_diameter / largest_diameter
                # CRITICAL FIX: Use ACTUAL head delivered by pump, not required head
                # The pump delivers more head than required (e.g., 92m vs 50m requirement)
                # Use pump-type-specific head exponent from physics model
                final_head = delivered_head * (diameter_ratio ** physics_exponents['head_exponent_y'])  # Apply affinity law to get actual head
                
                # Research-based efficiency penalty calculation based on pump type
                # Research: Δη = ε(1-d2'/d2) where ε = 0.15-0.25 for volute, 0.4-0.5 for diffuser
                pump_type = specs.get('pump_type', '').lower()
                
                if 'diffuser' in pump_type or 'turbine' in pump_type:
                    # Diffuser pumps: Higher efficiency penalty (research: 0.4-0.5)
                    efficiency_penalty_factor = self.validator.get_calibration_factor('efficiency_penalty_diffuser', self.efficiency_penalty_diffuser_default)
                    pump_type_classification = "diffuser"
                else:
                    # Volute pumps (default): Lower efficiency penalty (research: 0.15-0.25)
                    efficiency_penalty_factor = self.validator.get_calibration_factor('efficiency_penalty_volute', self.efficiency_penalty_volute_default)
                    pump_type_classification = "volute"
                
                # Calculate efficiency drop: Δη = ε × (1 - D_trim/D_full)
                trim_ratio = diameter_ratio  # D_trim/D_full
                efficiency_drop_percentage = efficiency_penalty_factor * (self.efficiency_drop_base_factor - trim_ratio) * self.percentage_conversion
                final_efficiency = base_efficiency - efficiency_drop_percentage
                
                logger.debug(f"[EFFICIENCY PENALTY] {pump_code}: {pump_type_classification} pump, trim ratio {trim_ratio:.3f}")
                logger.debug(f"[EFFICIENCY PENALTY] {pump_code}: Efficiency drop {efficiency_drop_percentage:.2f}% (factor: {efficiency_penalty_factor})")
                logger.debug(f"[EFFICIENCY PENALTY] {pump_code}: Base efficiency {base_efficiency:.1f}% → Final {final_efficiency:.1f}%")
                
                # Handle power calculation
                if None in powers_sorted:
                    # Calculate power hydraulically from manufacturer data
                    # CRITICAL: Use the actual operating head, not the pump's capability
                    if final_efficiency > 0:
                        # Use the required head (operating point), not final_head (pump capability)
                        actual_operating_head = head  # The head we're actually operating at
                        final_power = (flow * actual_operating_head * self.water_density * self.gravitational_acceleration) / (self.seconds_per_hour * final_efficiency / self.percentage_conversion * 1000)
                        logger.debug(f"[INDUSTRY] {pump_code}: Power calculated hydraulically at {actual_operating_head:.1f}m (operating point): {final_power:.2f}kW")
                    else:
                        final_power = 0
                else:
                    # Interpolate base power and apply affinity laws
                    power_interp = interpolate.interp1d(flows_sorted, powers_sorted, 
                                                      kind='linear', bounds_error=False)
                    base_power = float(power_interp(flow))
                    if not np.isnan(base_power):
                        # Use pump-type-specific power exponent from physics model
                        final_power = base_power * (diameter_ratio ** physics_exponents['power_exponent_z'])
                        logger.debug(f"[INDUSTRY] {pump_code}: Power scaled with affinity laws (exp={physics_exponents['power_exponent_z']}): {final_power:.2f}kW")
                    else:
                        # Fallback to hydraulic calculation
                        # CRITICAL: Use the actual operating head, not the pump's capability
                        actual_operating_head = head  # The head we're actually operating at
                        final_power = (flow * actual_operating_head * self.water_density * self.gravitational_acceleration) / (self.seconds_per_hour * final_efficiency / self.percentage_conversion * 1000)
                
                # NPSH calculation with affinity laws
                interpolated_npshr = None
                try:
                    npsh_values = [p.get('npshr_m') for p in curve_points if p.get('npshr_m') is not None]
                    if npsh_values and len(npsh_values) == len(flows_sorted):
                        npsh_interp = interpolate.interp1d(flows_sorted, npsh_values, 
                                                         kind='linear', bounds_error=False)
                        base_npshr = float(npsh_interp(flow))
                        if not np.isnan(base_npshr):
                            # NPSH scales with pump-type-specific exponent from physics model
                            interpolated_npshr = base_npshr * (diameter_ratio ** physics_exponents['npshr_exponent_alpha'])
                            
                            # Research-based NPSH degradation for heavy trimming (>10%)
                            npsh_threshold = self.validator.get_calibration_factor('npsh_degradation_threshold', self.npsh_degradation_threshold)
                            if trim_percent is not None and trim_percent < (self.percentage_conversion - npsh_threshold):  # More than 10% trim
                                npsh_degradation_factor = self.validator.get_calibration_factor('npsh_degradation_factor', self.npsh_degradation_factor)
                                interpolated_npshr *= npsh_degradation_factor
                                actual_trim_amount = self.percentage_conversion - trim_percent if trim_percent is not None else 0
                                logger.warning(f"[NPSH DEGRADATION] {pump_code}: Heavy trim ({actual_trim_amount:.1f}%) - NPSH increased by {(npsh_degradation_factor-1)*self.percentage_conversion:.1f}%")
                except:
                    pass
                
                logger.debug(f"[INDUSTRY] {pump_code}: Final performance - head: {final_head:.2f}m, eff: {final_efficiency:.1f}%, power: {final_power:.2f}kW, trim: {trim_percent:.1f}%")
                
                # ===============================================================
                # STEP 6: BEP MIGRATION & CORRECTION (Hydraulic Institute Model)
                # ===============================================================
                
                # Get original BEP from specifications (manufacturer data)
                original_bep_flow = specs.get('bep_flow_m3hr', 0)
                original_bep_head = specs.get('bep_head_m', 0)
                
                shifted_bep_flow = original_bep_flow
                shifted_bep_head = original_bep_head
                true_qbp_percent = self.default_true_qbp_percentage
                
                if original_bep_flow > 0 and original_bep_head > 0 and diameter_ratio < 1.0:
                    logger.info(f"[BEP MIGRATION] {pump_code}: Calculating shifted BEP for {trim_percent:.1f}% trim")
                    logger.info(f"[BEP MIGRATION] {pump_code}: Original BEP: {original_bep_flow:.1f} m³/hr @ {original_bep_head:.1f}m")
                    
                    # Apply exponential BEP shift formulas (Hydraulic Institute methodology)
                    # These exponents account for the non-linear BEP migration with trimming
                    # Use pump-type-specific exponents from physics model for BEP migration
                    # These account for how different pump types respond to trimming
                    
                    flow_exponent = physics_exponents['flow_exponent_x']
                    head_exponent = physics_exponents['head_exponent_y']
                    
                    # Calculate shifted BEP using exponential formulas  
                    # FIXED: Ensure all values are float to avoid decimal/float mixing
                    shifted_bep_flow = float(original_bep_flow) * (float(diameter_ratio) ** float(flow_exponent))
                    shifted_bep_head = float(original_bep_head) * (float(diameter_ratio) ** float(head_exponent))
                    
                    logger.info(f"[BEP MIGRATION] {pump_code}: Diameter ratio: {diameter_ratio:.4f}")
                    logger.info(f"[BEP MIGRATION] {pump_code}: Flow shift factor: {diameter_ratio ** flow_exponent:.4f} (using exponent {flow_exponent})")
                    logger.info(f"[BEP MIGRATION] {pump_code}: Head shift factor: {diameter_ratio ** head_exponent:.4f} (using exponent {head_exponent})")
                    logger.info(f"[BEP MIGRATION] {pump_code}: Shifted BEP: {shifted_bep_flow:.1f} m³/hr @ {shifted_bep_head:.1f}m")
                    
                    # Calculate TRUE QBP (operating flow as % of SHIFTED BEP flow)
                    true_qbp_percent = (flow / shifted_bep_flow) * self.percentage_conversion if shifted_bep_flow > 0 else self.percentage_conversion
                    simple_qbp_percent = (flow / original_bep_flow) * self.percentage_conversion if original_bep_flow > 0 else self.percentage_conversion
                    
                    logger.info(f"[BEP MIGRATION] {pump_code}: Simple QBP (ignoring shift): {simple_qbp_percent:.1f}%")
                    logger.info(f"[BEP MIGRATION] {pump_code}: TRUE QBP (with BEP shift): {true_qbp_percent:.1f}%")
                    logger.info(f"[BEP MIGRATION] {pump_code}: QBP difference: {true_qbp_percent - simple_qbp_percent:.1f}%")
                    
                    # Apply performance corrections based on curve rotation
                    # The curve "rotates" counterclockwise, affecting efficiency more at higher flows
                    if true_qbp_percent > self.qbp_penalty_threshold:  # Operating significantly above shifted BEP
                        # Efficiency correction factor from tunable physics engine
                        efficiency_correction_factor = self.validator.get_calibration_factor('efficiency_correction_exponent', self.qbp_penalty_base)
                        qbp_efficiency_penalty = min(self.qbp_penalty_divisor, (true_qbp_percent - self.qbp_penalty_threshold) * efficiency_correction_factor)
                        final_efficiency = max(self.qbp_penalty_lower_bound, final_efficiency - qbp_efficiency_penalty)
                        logger.info(f"[BEP MIGRATION] {pump_code}: Applied {qbp_efficiency_penalty:.1f}% efficiency penalty for QBP {true_qbp_percent:.1f}% (factor: {efficiency_correction_factor})")
                    
                                    
                else:
                    # No trimming or no BEP data - use original values
                    if original_bep_flow > 0:
                        true_qbp_percent = (flow / original_bep_flow) * self.percentage_conversion
                    logger.debug(f"[BEP MIGRATION] {pump_code}: No trimming or BEP data - using original values")
                
                # Return industry-standard performance calculation with BEP migration data
                return {
                    'flow_m3hr': flow,
                    'head_m': final_head,
                    'efficiency_pct': final_efficiency,
                    'power_kw': final_power,
                    'npshr_m': interpolated_npshr,
                    'impeller_diameter_mm': required_diameter,
                    'base_diameter_mm': largest_diameter,
                    'trim_percent': trim_percent,
                    'meets_requirements': True,  # By design, this meets requirements
                    'head_margin_m': final_head - head,  # Actual head delivered minus required head
                    # NEW: BEP Migration data for enhanced accuracy
                    'shifted_bep_flow': shifted_bep_flow,
                    'shifted_bep_head': shifted_bep_head,
                    'true_qbp_percent': true_qbp_percent,
                    'original_bep_flow': original_bep_flow,
                    'original_bep_head': original_bep_head
                }
                
            except Exception as e:
                logger.error(f"[INDUSTRY] Error in affinity law calculation for {pump_code}: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error calculating performance for {pump_data.get('pump_code')}: {str(e)}")
            return None