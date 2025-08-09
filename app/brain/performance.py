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
        self.min_trim_percent = 85.0
        self.max_trim_percent = 100.0
    
    def calculate_at_point(self, pump_data: Dict[str, Any], flow: float, 
                          head: float, impeller_trim: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Calculate pump performance at operating point using working catalog engine logic.
        
        Args:
            pump_data: Pump data with curves
            flow: Operating flow rate (m³/hr)
            head: Operating head (m)
            impeller_trim: Optional trim percentage
        
        Returns:
            Performance calculations
        """
        try:
            curves = pump_data.get('curves', [])
            if not curves:
                return None
            
            pump_code = pump_data.get('pump_code')
            
            # Find best curve that can deliver required head at flow
            best_performance = None
            best_trim = 200  # Start with impossible trim to find best
            
            for curve in curves:
                curve_points = curve.get('performance_points', [])
                if not curve_points or len(curve_points) < 2:
                    continue
                
                # Extract curve data, handling None values
                flows = [p.get('flow_m3hr', 0) for p in curve_points if p.get('flow_m3hr') is not None]
                heads = [p.get('head_m', 0) for p in curve_points if p.get('head_m') is not None]
                effs = [p.get('efficiency_pct', 0) for p in curve_points if p.get('efficiency_pct') is not None]
                
                # Handle None power values - estimate if needed
                powers = []
                for p in curve_points:
                    power = p.get('power_kw')
                    if power is not None:
                        powers.append(power)
                    else:
                        # Estimate power from head, flow, efficiency if efficiency exists
                        flow_val = p.get('flow_m3hr', 0)
                        head_val = p.get('head_m', 0) 
                        eff_val = p.get('efficiency_pct', 60) or 60  # Default 60% if None
                        if flow_val > 0 and head_val > 0 and eff_val > 0:
                            # P = (Q * H * ρ * g) / (3600 * η) where ρ=1000 kg/m³, g=9.81 m/s²
                            power_estimate = (flow_val * head_val * 1000 * 9.81) / (3600 * (eff_val/100))
                            powers.append(power_estimate / 1000)  # Convert W to kW
                        else:
                            powers.append(10)  # Fallback estimate
                
                # Debug: Check if we have valid data
                if pump_code == "150-400 2F":  # Debug specific pump
                    logger.debug(f"Debug {pump_code}: flows={flows[:3]}...")
                    logger.debug(f"Debug {pump_code}: heads={heads[:3]}...")
                    logger.debug(f"Debug {pump_code}: effs={effs[:3]}...")
                    logger.debug(f"Debug {pump_code}: powers={powers[:3]}...")
                
                # Check if flow is within curve range
                if not flows or not heads:
                    continue
                    
                min_flow, max_flow = min(flows), max(flows)
                if not (min_flow * 0.9 <= flow <= max_flow * 1.1):
                    if pump_code == "150-400 2F":  # Debug specific pump
                        logger.debug(f"Debug {pump_code}: Flow {flow} outside range {min_flow}-{max_flow}")
                    continue
                
                try:
                    # Interpolate values at operating flow
                    sorted_data = sorted(zip(flows, heads, effs, powers))
                    flows_sorted, heads_sorted, effs_sorted, powers_sorted = zip(*sorted_data)
                    
                    head_interp = interpolate.interp1d(flows_sorted, heads_sorted, 
                                                     kind='linear', bounds_error=False)
                    eff_interp = interpolate.interp1d(flows_sorted, effs_sorted, 
                                                    kind='linear', bounds_error=False)
                    power_interp = interpolate.interp1d(flows_sorted, powers_sorted, 
                                                      kind='linear', bounds_error=False)
                    
                    delivered_head = float(head_interp(flow))
                    efficiency = float(eff_interp(flow))
                    power = float(power_interp(flow))
                    
                    # Check if this curve can deliver required head
                    if delivered_head < head * 0.98:  # 2% tolerance
                        continue
                    
                    # Calculate impeller trim needed
                    curve_diameter = curve.get('impeller_diameter_mm', 0)
                    if curve_diameter <= 0:
                        continue
                    
                    # Calculate trim percentage based on affinity laws
                    head_ratio = head / delivered_head if delivered_head > 0 else 1.0
                    trim_ratio = np.sqrt(head_ratio) if head_ratio <= 1.0 else 1.0
                    required_diameter = curve_diameter * trim_ratio
                    trim_percent = (required_diameter / curve_diameter) * 100
                    
                    # Skip if trim is too aggressive
                    if trim_percent < 85.0:
                        continue
                    
                    # Prefer curves with minimal trim
                    trim_penalty = abs(100 - trim_percent)
                    if trim_penalty < best_trim:
                        best_trim = trim_penalty
                        
                        # Apply affinity laws for trimmed performance
                        trim_factor = trim_percent / 100.0
                        final_head = delivered_head * (trim_factor ** 2)
                        final_efficiency = efficiency * (0.8 + 0.2 * trim_factor)  # Efficiency penalty
                        final_power = power * (trim_factor ** 3)
                        
                        best_performance = {
                            'flow_m3hr': flow,
                            'head_m': final_head,
                            'efficiency_pct': final_efficiency,
                            'power_kw': final_power,
                            'npshr_m': curve_points[0].get('npshr_m'),  # Use first point's NPSH
                            'impeller_diameter_mm': required_diameter,
                            'base_diameter_mm': curve_diameter,
                            'trim_percent': trim_percent,
                            'meets_requirements': final_head >= head * 0.98,
                            'head_margin_m': final_head - head
                        }
                        
                except Exception as curve_error:
                    logger.debug(f"Error interpolating curve for {pump_code}: {curve_error}")
                    continue
            
            if best_performance:
                logger.debug(f"Brain performance for {pump_code}: {best_performance['efficiency_pct']:.1f}% eff, {best_performance['power_kw']:.1f} kW, {best_performance['trim_percent']:.1f}% trim")
                return best_performance
            
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