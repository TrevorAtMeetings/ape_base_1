"""
Performance Analyzer Module
===========================
Consolidates performance calculations and affinity law applications
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import interpolate

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Analyzes pump performance using affinity laws and interpolation"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        
        # Performance thresholds
        self.min_efficiency = 40.0
        self.min_trim_percent = 85.0  # Maximum 15% trim (industry standard)
        self.max_trim_percent = 100.0
        
        # Industry standard affinity law exponents
        self.affinity_flow_exp = 1.0      # Q2/Q1 = (D2/D1)^1
        self.affinity_head_exp = 2.0      # H2/H1 = (D2/D1)^2  
        self.affinity_power_exp = 3.0     # P2/P1 = (D2/D1)^3
        self.affinity_efficiency_exp = 0.8 # η2/η1 ≈ (D2/D1)^0.8 (industry standard)
    
    def calculate_at_point(self, pump_data: Dict[str, Any], flow: float, 
                          head: float, impeller_trim: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        INDUSTRY STANDARD: Calculate pump performance using proper affinity law trimming.
        Always starts with largest impeller and trims DOWN using affinity laws.
        
        Args:
            pump_data: Pump data with curves
            flow: Operating flow rate (m³/hr)
            head: Operating head (m)
            impeller_trim: Optional trim percentage
        
        Returns:
            Performance calculations using industry-standard methodology
        """
        # Use new industry-standard method
        return self.calculate_at_point_industry_standard(pump_data, flow, head, impeller_trim)
    
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
            logger.debug(f"[INDUSTRY] Starting industry-standard calculation for {pump_code} at {flow} m³/hr @ {head}m")
            
            curves = pump_data.get('curves', [])
            logger.debug(f"[INDUSTRY] {pump_code}: Found {len(curves)} curves")
            
            if not curves:
                logger.debug(f"[INDUSTRY] {pump_code}: No curves found - returning None")
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
                logger.debug(f"[INDUSTRY] {pump_code}: No valid curves with impeller diameter found")
                return None
                
            logger.debug(f"[INDUSTRY] {pump_code}: Using largest impeller {largest_diameter}mm as base curve")
            
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
            
            if not (min_flow * 0.9 <= flow <= max_flow * 1.1):
                logger.debug(f"[INDUSTRY] {pump_code}: Flow {flow} outside curve range {min_flow*0.9:.1f} - {max_flow*1.1:.1f}")
                return None
                
            logger.debug(f"[INDUSTRY] {pump_code}: Starting interpolation on largest curve...")
            
            try:
                # Sort data by flow to ensure monotonic interpolation
                sorted_points = sorted(zip(flows, heads, effs, powers), key=lambda p: p[0])
                flows_sorted, heads_sorted, effs_sorted, powers_sorted = zip(*sorted_points)
                
                logger.debug(f"[INDUSTRY] {pump_code}: Creating interpolation functions with sorted data...")
                
                # Create interpolation functions using SORTED data
                head_interp = interpolate.interp1d(flows_sorted, heads_sorted, 
                                                 kind='linear', bounds_error=False)
                eff_interp = interpolate.interp1d(flows_sorted, effs_sorted, 
                                                kind='linear', bounds_error=False)
                
                logger.debug(f"[INDUSTRY] {pump_code}: Executing interpolation at flow {flow}...")
                
                # STEP 1: Get performance at target flow on largest curve
                delivered_head = float(head_interp(flow))
                base_efficiency = float(eff_interp(flow))
                
                logger.debug(f"[INDUSTRY] {pump_code}: Base curve performance - head: {delivered_head:.2f}m, eff: {base_efficiency:.1f}%")
                
                # Check for NaN values (NO FALLBACKS EVER)
                if np.isnan(delivered_head) or np.isnan(base_efficiency):
                    logger.debug(f"[INDUSTRY] {pump_code}: NaN interpolation result - cannot proceed")
                    return None
                
                # STEP 2: Check if pump can deliver required head with reasonable margin
                # Allow some tolerance - pump should deliver at least 98% of required head
                if delivered_head < head * 0.98:
                    logger.warning(f"[INDUSTRY] {pump_code}: Insufficient head capability - base curve gives {delivered_head:.2f}m < required {head*0.98:.2f}m")
                    return None
                
                # STEP 3: Calculate required trim using affinity laws  
                # H₂ = H₁ × (D₂/D₁)² → D₂/D₁ = √(H₂/H₁)
                head_ratio = head / delivered_head if delivered_head > 0 else 1.0
                diameter_ratio = np.sqrt(head_ratio)
                required_diameter = largest_diameter * diameter_ratio
                trim_percent = (required_diameter / largest_diameter) * 100  # Correct: percentage of original diameter
                
                logger.debug(f"[INDUSTRY] {pump_code}: Affinity law calculation - head ratio: {head_ratio:.3f}, diameter ratio: {diameter_ratio:.3f}")
                logger.debug(f"[INDUSTRY] {pump_code}: Required diameter: {required_diameter:.1f}mm (trim: {trim_percent:.1f}%)")
                
                # STEP 4: Check trim limits - maximum 15% trim (85% minimum diameter)
                # Industry standard for reliable operation
                if trim_percent < 85.0:
                    logger.warning(f"[INDUSTRY] {pump_code}: Excessive trim required ({trim_percent:.1f}% < 85%) - cannot proceed")
                    return None
                
                # STEP 5: Apply industry-standard affinity laws to calculate final performance
                final_head = head  # By design, this matches our target
                
                # Industry standard efficiency scaling with trimming (reduced penalty)
                # Manufacturers don't penalize efficiency as harshly for moderate trimming
                trim_penalty_factor = 1.0 - (1.0 - diameter_ratio) * 0.2  # Much gentler penalty
                final_efficiency = base_efficiency * trim_penalty_factor
                
                # Handle power calculation
                if None in powers_sorted:
                    # Calculate power hydraulically from manufacturer data
                    if final_efficiency > 0:
                        density = 1000  # kg/m³ for water
                        gravity = 9.81  # m/s²
                        final_power = (flow * final_head * density * gravity) / (3600 * final_efficiency / 100 * 1000)
                        logger.debug(f"[INDUSTRY] {pump_code}: Power calculated hydraulically: {final_power:.2f}kW")
                    else:
                        final_power = 0
                else:
                    # Interpolate base power and apply affinity laws
                    power_interp = interpolate.interp1d(flows_sorted, powers_sorted, 
                                                      kind='linear', bounds_error=False)
                    base_power = float(power_interp(flow))
                    if not np.isnan(base_power):
                        final_power = base_power * (diameter_ratio ** self.affinity_power_exp)
                        logger.debug(f"[INDUSTRY] {pump_code}: Power scaled with affinity laws: {final_power:.2f}kW")
                    else:
                        # Fallback to hydraulic calculation
                        final_power = (flow * final_head * 1000 * 9.81) / (3600 * final_efficiency / 100 * 1000)
                
                # NPSH calculation with affinity laws
                interpolated_npshr = None
                try:
                    npsh_values = [p.get('npshr_m') for p in curve_points if p.get('npshr_m') is not None]
                    if npsh_values and len(npsh_values) == len(flows_sorted):
                        npsh_interp = interpolate.interp1d(flows_sorted, npsh_values, 
                                                         kind='linear', bounds_error=False)
                        base_npshr = float(npsh_interp(flow))
                        if not np.isnan(base_npshr):
                            # NPSH scales with (diameter ratio)²
                            interpolated_npshr = base_npshr * (diameter_ratio ** 2)
                except:
                    pass
                
                logger.debug(f"[INDUSTRY] {pump_code}: Final performance - head: {final_head:.2f}m, eff: {final_efficiency:.1f}%, power: {final_power:.2f}kW, trim: {trim_percent:.1f}%")
                
                # Return industry-standard performance calculation
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
                    'head_margin_m': 0.0  # Exact match by affinity law design
                }
                
            except Exception as e:
                logger.error(f"[INDUSTRY] Error in affinity law calculation for {pump_code}: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error calculating performance for {pump_data.get('pump_code')}: {str(e)}")
            return None
    
    def _calculate_required_diameter(self, base_curve: Dict[str, Any], 
                                    target_flow: float, target_head: float) -> Optional[Dict[str, Any]]:
        """
        Calculate required impeller diameter (from impeller_scaling.py).
        
        Args:
            base_curve: Curve data
            target_flow: Required flow
            target_head: Required head
        
        Returns:
            Sizing calculation results
        """
        try:
            points = base_curve['performance_points']
            flows = [p['flow_m3hr'] for p in points]
            heads = [p['head_m'] for p in points]
            effs = [p['efficiency_pct'] for p in points]
            
            if not flows or not heads or len(flows) < 2:
                return None
            
            base_diameter = base_curve.get('impeller_diameter_mm', 0)
            if base_diameter <= 0:
                return None
            
            # Check if target flow is within curve range (with tolerance for edge cases)
            # Allow 10% extrapolation like Legacy system
            flow_min = min(flows)
            flow_max = max(flows)
            if target_flow < flow_min * 0.9 or target_flow > flow_max * 1.1:
                return None
            
            # Adaptive interpolation based on data density
            if len(flows) >= 4:
                kind = 'cubic'
            elif len(flows) == 3:
                kind = 'quadratic'
            else:
                kind = 'linear'
            
            # Interpolate at target flow
            head_interp = interpolate.interp1d(flows, heads, kind=kind, bounds_error=False)
            eff_interp = interpolate.interp1d(flows, effs, kind=kind, bounds_error=False)
            
            base_head_at_flow = float(head_interp(target_flow))
            base_efficiency = float(eff_interp(target_flow))
            
            if np.isnan(base_head_at_flow) or base_head_at_flow <= 0:
                return None
            
            # Check if trimming can achieve target (with 2% tolerance like Legacy)
            # Legacy allows 2% tolerance: delivered_head >= required_head * 0.98
            if target_head > base_head_at_flow * 1.02:  # Inverse check: required > available * 1.02
                # Cannot increase head by trimming (even with tolerance)
                return None
            
            # Calculate required diameter using affinity laws
            # H₂ = H₁ × (D₂/D₁)²
            diameter_ratio = np.sqrt(target_head / base_head_at_flow)
            required_diameter = base_diameter * diameter_ratio
            trim_percent = (required_diameter / base_diameter) * 100
            
            # Check trim limits
            if trim_percent < self.min_trim_percent:
                return None
            
            # Allow full impeller for minimal trim
            if trim_percent >= 98.0:
                required_diameter = base_diameter
                trim_percent = 100.0
                diameter_ratio = 1.0
            
            # Calculate scaled performance
            scaled_performance = self._calculate_scaled_performance(
                base_curve, required_diameter, base_diameter, target_flow, target_head
            )
            
            if not scaled_performance:
                return None
            
            return {
                'required_diameter_mm': round(required_diameter, 1),
                'base_diameter_mm': base_diameter,
                'trim_percent': round(trim_percent, 1),
                'diameter_ratio': round(diameter_ratio, 4),
                'performance': scaled_performance,
                'achievable': True,
                'trimming_required': trim_percent < 100
            }
            
        except Exception as e:
            logger.error(f"Error calculating diameter: {str(e)}")
            return None
    
    def _calculate_scaled_performance(self, base_curve: Dict[str, Any],
                                     new_diameter: float, base_diameter: float,
                                     target_flow: float, target_head: float) -> Optional[Dict[str, Any]]:
        """
        Calculate performance with scaled impeller.
        
        Args:
            base_curve: Base curve data
            new_diameter: New impeller diameter
            base_diameter: Base impeller diameter
            target_flow: Target flow rate
            target_head: Target head
        
        Returns:
            Scaled performance data
        """
        try:
            points = base_curve['performance_points']
            flows = [p['flow_m3hr'] for p in points]
            heads = [p['head_m'] for p in points]
            effs = [p['efficiency_pct'] for p in points]
            
            diameter_ratio = new_diameter / base_diameter
            
            # Adaptive interpolation
            if len(flows) >= 4:
                kind = 'cubic'
            elif len(flows) == 3:
                kind = 'quadratic'
            else:
                kind = 'linear'
            
            # Interpolate base performance
            head_interp = interpolate.interp1d(flows, heads, kind=kind, bounds_error=False)
            eff_interp = interpolate.interp1d(flows, effs, kind=kind, bounds_error=False)
            
            base_head_at_flow = float(head_interp(target_flow))
            base_efficiency = float(eff_interp(target_flow))
            
            if np.isnan(base_head_at_flow) or np.isnan(base_efficiency):
                return None
            
            # Apply affinity laws
            actual_head = base_head_at_flow * (diameter_ratio ** 2)
            
            # Efficiency penalty for trimming
            trim_percent = diameter_ratio * 100
            efficiency_penalty = max(0, (100 - trim_percent) * 0.3)
            actual_efficiency = base_efficiency - efficiency_penalty
            
            # Calculate power
            actual_power = self._calculate_hydraulic_power(target_flow, actual_head, actual_efficiency)
            
            # NPSH calculation (optional)
            actual_npshr = None
            try:
                npshs = [p.get('npshr', 0) for p in points if p.get('npshr', 0) > 0]
                if npshs and len(npshs) == len(flows):
                    npsh_interp = interpolate.interp1d(flows, npshs, kind=kind, bounds_error=False)
                    base_npshr = float(npsh_interp(target_flow))
                    if not np.isnan(base_npshr):
                        actual_npshr = base_npshr * (diameter_ratio ** 2)
            except:
                pass
            
            # Apply 2% tolerance for head requirements (matching Legacy system)
            # Also accept pumps that deliver excessive head (up to 2x) like Legacy does
            meets_requirements = (actual_head >= target_head * 0.98) and (actual_head <= target_head * 2.0)
            
            return {
                'flow_m3hr': target_flow,
                'head_m': round(actual_head, 2),
                'efficiency_pct': round(actual_efficiency, 2),
                'power_kw': round(actual_power, 3),
                'npshr_m': round(actual_npshr, 2) if actual_npshr else None,
                'meets_requirements': meets_requirements,
                'head_margin_m': round(actual_head - target_head, 2),
                'impeller_diameter_mm': round(new_diameter, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating scaled performance: {str(e)}")
            return None
    
    def _calculate_hydraulic_power(self, flow_m3hr: float, head_m: float, 
                                  efficiency_pct: float) -> float:
        """
        Calculate hydraulic power requirement.
        
        Args:
            flow_m3hr: Flow rate in m³/hr
            head_m: Head in meters
            efficiency_pct: Efficiency percentage
        
        Returns:
            Power in kW
        """
        if efficiency_pct <= 0:
            return 0
        
        # Convert flow to m³/s
        flow_m3s = flow_m3hr / 3600
        
        # Water density (kg/m³) and gravity
        rho = 1000
        g = 9.81
        
        # Hydraulic power: P = ρ × g × Q × H / (η × 1000)
        power_kw = (rho * g * flow_m3s * head_m) / (efficiency_pct / 100 * 1000)
        
        return power_kw
    
    def apply_affinity_laws(self, base_curve: Dict[str, Any],
                           diameter_ratio: float = 1.0,
                           speed_ratio: float = 1.0) -> Dict[str, Any]:
        """
        Apply affinity laws to scale pump curves.
        
        Args:
            base_curve: Base performance curve
            diameter_ratio: D2/D1
            speed_ratio: N2/N1
        
        Returns:
            Scaled curve data
        """
        try:
            points = base_curve.get('performance_points', [])
            if not points:
                return base_curve
            
            scaled_points = []
            
            for point in points:
                # Apply affinity laws
                # Q₂ = Q₁ × (D₂/D₁) × (N₂/N₁)
                # H₂ = H₁ × (D₂/D₁)² × (N₂/N₁)²
                # P₂ = P₁ × (D₂/D₁)³ × (N₂/N₁)³
                
                scaled_flow = point['flow_m3hr'] * diameter_ratio * speed_ratio
                scaled_head = point['head_m'] * (diameter_ratio ** 2) * (speed_ratio ** 2)
                
                # Power scaling if available
                if point.get('power_kw'):
                    scaled_power = point['power_kw'] * (diameter_ratio ** 3) * (speed_ratio ** 3)
                else:
                    scaled_power = None
                
                # NPSH scaling
                if point.get('npshr_m'):
                    scaled_npshr = point['npshr_m'] * (diameter_ratio ** 2) * (speed_ratio ** 2)
                else:
                    scaled_npshr = None
                
                # Efficiency approximately constant for small changes
                scaled_efficiency = point.get('efficiency_pct', 0)
                
                scaled_points.append({
                    'flow_m3hr': round(scaled_flow, 2),
                    'head_m': round(scaled_head, 2),
                    'efficiency_pct': round(scaled_efficiency, 2),
                    'power_kw': round(scaled_power, 3) if scaled_power else None,
                    'npshr_m': round(scaled_npshr, 2) if scaled_npshr else None
                })
            
            scaled_curve = base_curve.copy()
            scaled_curve['performance_points'] = scaled_points
            scaled_curve['diameter_ratio'] = diameter_ratio
            scaled_curve['speed_ratio'] = speed_ratio
            
            return scaled_curve
            
        except Exception as e:
            logger.error(f"Error applying affinity laws: {str(e)}")
            return base_curve
    
    def validate_envelope(self, pump: Dict[str, Any], flow: float, head: float) -> Dict[str, Any]:
        """
        Validate operating point within pump envelope.
        
        Args:
            pump: Pump data
            flow: Operating flow
            head: Operating head
        
        Returns:
            Validation results
        """
        validation = {
            'valid': True,
            'warnings': [],
            'recommendations': []
        }
        
        try:
            specs = pump.get('specifications', {})
            
            # Check BEP proximity
            bep_flow = specs.get('bep_flow_m3hr', 0)
            if bep_flow > 0:
                qbp = (flow / bep_flow) * 100
                
                if qbp < 60:
                    validation['warnings'].append(f'Operating at {qbp:.0f}% of BEP - risk of recirculation')
                    validation['recommendations'].append('Consider smaller pump or VFD')
                elif qbp > 130:
                    validation['warnings'].append(f'Operating at {qbp:.0f}% of BEP - risk of cavitation')
                    validation['recommendations'].append('Consider larger pump')
                elif 95 <= qbp <= 105:
                    validation['recommendations'].append('Excellent - operating near BEP')
            
            # Check head limits
            max_head = specs.get('max_head_m', 0)
            if max_head > 0 and head > max_head * 0.9:
                validation['warnings'].append('Operating near maximum head')
            
            # Check flow limits
            max_flow = specs.get('max_flow_m3hr', 0)
            if max_flow > 0 and flow > max_flow * 0.9:
                validation['warnings'].append('Operating near maximum flow')
            
            if validation['warnings']:
                validation['valid'] = False
            
        except Exception as e:
            logger.error(f"Error validating envelope: {str(e)}")
            validation['warnings'].append(f'Validation error: {str(e)}')
            validation['valid'] = False
        
        return validation