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
                          head: float, impeller_trim: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate pump performance at operating point.
        Consolidates logic from impeller_scaling.py
        
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
                logger.warning(f"No curves for pump {pump_data.get('pump_code')}")
                return None
            
            # Find best curve for operating point
            best_curve = None
            best_score = float('inf')
            
            for curve in curves:
                if not curve.get('performance_points'):
                    continue
                
                # Get curve impeller diameter
                curve_diameter = curve.get('impeller_diameter_mm', 0)
                if curve_diameter <= 0:
                    continue
                
                # Calculate required diameter for this curve
                result = self._calculate_required_diameter(curve, flow, head)
                if result and result['achievable']:
                    # Score based on how close to full impeller
                    score = abs(100 - result['trim_percent'])
                    if score < best_score:
                        best_score = score
                        best_curve = result
            
            if not best_curve:
                return None
            
            # Return performance data
            return {
                'flow_m3hr': flow,
                'head_m': best_curve['performance']['head_m'],
                'efficiency_pct': best_curve['performance']['efficiency_pct'],
                'power_kw': best_curve['performance']['power_kw'],
                'npshr_m': best_curve['performance'].get('npshr_m'),
                'impeller_diameter_mm': best_curve['required_diameter_mm'],
                'base_diameter_mm': best_curve['base_diameter_mm'],
                'trim_percent': best_curve['trim_percent'],
                'meets_requirements': best_curve['performance']['meets_requirements'],
                'head_margin_m': best_curve['performance']['head_margin_m']
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance: {str(e)}")
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
            
            # Check if target flow is within curve range
            if target_flow < min(flows) or target_flow > max(flows):
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
            
            # Check if trimming can achieve target
            if target_head > base_head_at_flow:
                # Cannot increase head by trimming
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
            
            return {
                'flow_m3hr': target_flow,
                'head_m': round(actual_head, 2),
                'efficiency_pct': round(actual_efficiency, 2),
                'power_kw': round(actual_power, 3),
                'npshr_m': round(actual_npshr, 2) if actual_npshr else None,
                'meets_requirements': actual_head >= target_head,
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