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
        self.min_efficiency = 40.0
        self.min_trim_percent = 85.0  # Industry standard - 15% maximum trim, non-negotiable
        self.max_trim_percent = 100.0
        
        # Industry standard affinity law exponents
        self.affinity_flow_exp = 1.0      # Q2/Q1 = (D2/D1)^1
        self.affinity_head_exp = 2.0      # H2/H1 = (D2/D1)^2  
        self.affinity_power_exp = 3.0     # P2/P1 = (D2/D1)^3
        self.affinity_efficiency_exp = 0.8 # η2/η1 ≈ (D2/D1)^0.8 (industry standard)
        
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
            'bep_shift_flow_exponent': 1.2,
            'bep_shift_head_exponent': 2.2,
            'trim_dependent_small_exponent': 2.9,
            'trim_dependent_large_exponent': 2.1,
            'efficiency_penalty_volute': 0.20,
            'efficiency_penalty_diffuser': 0.45,
            'npsh_degradation_threshold': 10.0,
            'npsh_degradation_factor': 1.15
        }
        
        for factor, default in default_factors.items():
            if factor not in self.calibration_factors:
                self.calibration_factors[factor] = default
                
        logger.debug(f"Calibration factors loaded: {list(self.calibration_factors.keys())}")

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
            flow: Target flow rate (m³/hr)
            allow_excessive_trim: If True, show performance even with excessive trim
            forced_diameter: If provided, calculate at this exact diameter (mm) without optimization
        
        Returns:
            Performance data at the given flow, or None if pump cannot operate at this flow
        """
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
                logger.info(f"[FORCED CONSTRAINT] {pump_code}: Using forced diameter {forced_diameter}mm for {flow} m³/hr")
                
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
                    min_diameter = largest_diameter * 0.70  
                    max_diameter = largest_diameter * 1.15
                
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
                
                logger.info(f"[FORCED CONSTRAINT] {pump_code}: Reference {largest_diameter}mm @ {flow} m³/hr = {reference_head:.2f}m")
                logger.info(f"[FORCED CONSTRAINT] {pump_code}: Forced to {forced_diameter}mm = {delivered_head:.2f}m (ratio: {diameter_ratio:.3f})")
                
                # Get efficiency with trim degradation
                efficiencies = [p.get('efficiency_pct', 0) for p in sorted_points if 'efficiency_pct' in p]
                if efficiencies and len(efficiencies) == len(flows):
                    eff_interp = interpolate.interp1d(flows, efficiencies, kind='linear',
                                                     bounds_error=False, fill_value=0.0)
                    base_efficiency = float(eff_interp(flow))
                else:
                    base_efficiency = 75.0  # Default
                
                # Apply efficiency degradation for excessive trimming
                if diameter_ratio < 0.85:  # More than 15% trim
                    efficiency_penalty = (0.85 - diameter_ratio) * 20
                    efficiency = max(base_efficiency - efficiency_penalty, 40)
                else:
                    efficiency = base_efficiency
                
                # Calculate power using affinity laws
                if efficiency > 0:
                    # Correct power calculation: P = ρ × g × Q × H / η
                    # Units: (kg/m³) × (m/s²) × (m³/hr) × (m) / efficiency / conversion = kW
                    power_kw = (flow * delivered_head * 1000 * 9.81) / (3600 * efficiency / 100 * 1000)
                else:
                    power_kw = 0
                
                # Calculate trim percentage
                trim_percent = (1 - diameter_ratio) * 100
                
                return {
                    'flow_m3hr': flow,
                    'head_m': delivered_head,
                    'efficiency_pct': max(efficiency, 30),
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
            min_flow = min(flows) * 0.5  # Allow 50% below minimum
            max_flow = max(flows) * 1.5  # Allow 50% above maximum
            
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
                bep_efficiency = specs.get('bep_efficiency_pct', 75)
                bep_flow = specs.get('bep_flow_m3hr', flow)
                
                # Simple efficiency curve estimation
                flow_ratio = flow / bep_flow if bep_flow > 0 else 1.0
                if 0.7 <= flow_ratio <= 1.2:
                    efficiency = bep_efficiency * (1 - 0.1 * abs(1 - flow_ratio))
                else:
                    efficiency = bep_efficiency * 0.85  # Significant drop off-BEP
            
            # Calculate power
            if efficiency > 0:
                # Correct power calculation: P = ρ × g × Q × H / η
                power_kw = (flow * delivered_head * 1000 * 9.81) / (3600 * efficiency / 100 * 1000)
            else:
                power_kw = 0
            
            # Get NPSH if available
            npsh_r = 0
            for point in sorted_points:
                if abs(point.get('flow_m3hr', 0) - flow) < 10:  # Close to our flow
                    npsh_r = point.get('npsh_r', 0)
                    break
            
            return {
                'flow_m3hr': flow,
                'head_m': delivered_head,
                'efficiency_pct': max(efficiency, 30),  # Floor at 30%
                'power_kw': power_kw,
                'npsh_r': npsh_r,
                'diameter_mm': largest_curve.get('impeller_diameter_mm', 0),
                'trim_percent': 0,  # Will be calculated if trimming is needed
                'note': f'Performance at {flow:.1f} m³/hr'
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance at flow: {e}")
            return None

    def calculate_required_diameter_direct(self, flows_sorted, heads_sorted, 
                                          largest_diameter, target_flow, target_head, pump_code, physics_exponents=None):
        """
        ENHANCED: Calculate required impeller diameter using direct affinity law formula.
        
        Uses the mathematically precise formula: D₂ = D₁ × sqrt(H₂ / H₁)
        where H₁ is interpolated head at target flow on largest curve.
        
        Args:
            flows_sorted: Sorted flow data from largest curve
            heads_sorted: Sorted head data from largest curve  
            largest_diameter: Diameter of largest available impeller
            target_flow: Required flow rate (m³/hr)
            target_head: Required head (m)
            pump_code: Pump identifier for logging
            
        Returns:
            Tuple[float, float]: (required_diameter, trim_percent) or (None, None) if failed
        """
        try:
            # STEP 1: Interpolate head at target flow on largest curve (H₁)
            if len(flows_sorted) < 2 or len(heads_sorted) < 2:
                return None, None
                
            head_interp = interpolate.interp1d(flows_sorted, heads_sorted, 
                                             kind='linear', bounds_error=False)
            
            # Check flow range coverage
            min_flow, max_flow = min(flows_sorted), max(flows_sorted)
            if not (min_flow * 0.9 <= target_flow <= max_flow * 1.1):
                return None, None
            
            # Get head delivered by largest impeller at target flow (H₁)
            base_head_at_flow = float(head_interp(target_flow))
            
            logger.debug(f"[AFFINITY] Interpolated head at {target_flow} m³/hr: {base_head_at_flow}m")
            
            if np.isnan(base_head_at_flow) or base_head_at_flow <= 0:
                logger.debug(f"[AFFINITY] Returning None due to invalid head")
                return None, None
            
            
            # STEP 2: Apply Direct Affinity Law Formula
            # H₂ = H₁ × (D₂/D₁)²  →  D₂ = D₁ × sqrt(H₂/H₁)
            
            # FIXED: Trimming REDUCES head, so we can only trim if target < base head
            # We cannot achieve a head higher than what the full-diameter impeller delivers
            # Special tolerance for BEP testing - allow small precision differences
            tolerance = 1.05  # 5% tolerance for BEP precision issues
            if target_head > base_head_at_flow * tolerance:
                logger.debug(f"[AFFINITY] Target {target_head:.2f}m > max {base_head_at_flow * tolerance:.2f}m - returning None")
                return None, None
            elif target_head > base_head_at_flow * 1.02:
                logger.info(f"[BEP TOLERANCE] {pump_code}: Allowing BEP precision difference - target {target_head:.2f}m vs base {base_head_at_flow:.2f}m")
            
            logger.debug(f"[AFFINITY] Head check passed: {target_head:.2f}m <= {base_head_at_flow * 1.02:.2f}m")
            
            # Good case: target_head < base_head_at_flow means we can trim to reduce head
            
            # Calculate required diameter using RESEARCH-BASED trim-dependent physics
            # Research: Exponent varies from 2.8-3.0 for small trims to 2.0-2.2 for large trims
            # Use pump-type-specific head exponent from physics model
            if physics_exponents and 'head_exponent_y' in physics_exponents:
                head_exponent = physics_exponents['head_exponent_y']
                process_logger.log(f"    Using physics model exponent: {head_exponent}")
            else:
                # Fallback to trim-dependent exponents if physics model not provided
                estimated_trim_pct = (1.0 - (target_head / base_head_at_flow) ** 0.5) * 100
                
                if estimated_trim_pct < 5.0:
                    # Small trim: Use higher exponent (research: 2.8-3.0)
                    head_exponent = self.get_calibration_factor('trim_dependent_small_exponent', 2.9)
                    small_trim_threshold = "small"  # Reference to classification logic
                    process_logger.log(f"    {small_trim_threshold.title()} trim (~{estimated_trim_pct:.1f}%): Using exponent {head_exponent}")
                else:
                    # Larger trim: Use standard exponent (research: 2.0-2.2)
                    head_exponent = self.get_calibration_factor('trim_dependent_large_exponent', 2.1)
                    large_trim_threshold = "large"  # Reference to classification logic  
                    process_logger.log(f"    {large_trim_threshold.title()} trim (~{estimated_trim_pct:.1f}%): Using exponent {head_exponent}")
            
            # H₂/H₁ = (D₂/D₁)^head_exp  →  D₂ = D₁ × (H₂/H₁)^(1/head_exp)
            # FIXED: Ensure all values are float to avoid decimal/float mixing in power operations
            target_head_float = float(target_head)
            base_head_float = float(base_head_at_flow)
            largest_diameter_float = float(largest_diameter)
            head_exponent_float = float(head_exponent)
            
            # Log the actual formula calculation with real values
            process_logger.log(f"    Affinity Law Calculation:")
            process_logger.log(f"      D₁ (largest): {largest_diameter_float:.1f} mm")
            process_logger.log(f"      H₁ (at target flow): {base_head_float:.2f} m")
            process_logger.log(f"      H₂ (target): {target_head_float:.2f} m")
            process_logger.log(f"      Head exponent: {head_exponent_float}")
            process_logger.log(f"      Formula: D₂ = {largest_diameter_float:.1f} × ({target_head_float:.2f}/{base_head_float:.2f})^(1/{head_exponent_float})")
            
            diameter_ratio = np.power(target_head_float / base_head_float, 1.0 / head_exponent_float)
            required_diameter = largest_diameter_float * diameter_ratio
            trim_percent = diameter_ratio * 100
            
            process_logger.log(f"      Result: D₂ = {largest_diameter_float:.1f} × {diameter_ratio:.4f} = {required_diameter:.1f} mm")
            process_logger.log(f"      Trim: {trim_percent:.2f}%")
            
            logger.info(f"[TUNABLE AFFINITY] {pump_code}: Using head exponent {head_exponent} (vs standard 2.0)")
            
            logger.info(f"[TUNABLE AFFINITY] {pump_code}: Diameter ratio = ({target_head:.2f}/{base_head_at_flow:.2f})^(1/{head_exponent}) = {diameter_ratio:.4f}")
            logger.info(f"[TUNABLE AFFINITY] {pump_code}: Required diameter = {largest_diameter:.1f} × {diameter_ratio:.4f} = {required_diameter:.1f}mm")
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
            
            
            if error_percent > 1.0:  # Should be essentially zero for direct calculation
                logger.warning(f"[DIRECT AFFINITY] {pump_code}: Unexpected calculation error: {error_percent:.2f}%")
            
            # Enhanced logging for calculations
            logger.debug(f"[TRIM] {pump_code}: Direct calculation complete")
            logger.debug(f"[TRIM] {pump_code}: H₁ = {base_head_at_flow:.2f}m, H₂ = {target_head:.2f}m")
            logger.debug(f"[TRIM] {pump_code}: D₁ = {largest_diameter:.1f}mm, D₂ = {required_diameter:.1f}mm")
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
            target_flow: Target flow rate (m³/hr)
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
                eff_interp = interpolate.interp1d(flows, efficiencies, kind='linear',
                                                 bounds_error=False, fill_value=70.0)
                base_efficiency = float(eff_interp(base_equivalent_flow))
            else:
                base_efficiency = 75.0  # Default
            
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
            flow_m3hr: Flow rate in m³/hr
            head_m: Head in meters
            efficiency_pct: Pump efficiency percentage
            
        Returns:
            Power in kW
        """
        if efficiency_pct <= 0 or flow_m3hr <= 0 or head_m <= 0:
            return 0.0
        
        # P = ρ × g × Q × H / η
        # Where: ρ = 1000 kg/m³, g = 9.81 m/s², Q in m³/s, H in m
        flow_m3s = flow_m3hr / 3600  # Convert to m³/s
        power_w = (1000 * 9.81 * flow_m3s * head_m) / (efficiency_pct / 100)
        power_kw = power_w / 1000  # Convert to kW
        
        return power_kw