"""
Performance VFD Module
======================
Variable Frequency Drive calculations and speed variation analysis
"""

import logging
import numpy as np
from typing import Dict, Any, Optional
from scipy import interpolate
from .config_manager import config

logger = logging.getLogger(__name__)


class VFDCalculator:
    """Variable Frequency Drive performance calculations"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain

    def calculate_performance_with_speed_variation(self, pump_data: Dict[str, Any], 
                                                   target_flow: float, 
                                                   target_head: float,
                                                   h_static_ratio: float = None) -> Optional[Dict[str, Any]]:
        """
        Calculate pump performance using Variable Frequency Drive (VFD) speed variation.
        Implements affinity laws for speed change to meet target duty point.
        """
        if h_static_ratio is None:
            h_static_ratio = config.get('performance_vfd', 'default_static_head_ratio_for_system_curves')
        
        try:
            pump_code = pump_data.get('pump_code', 'Unknown')
            logger.info(f"[VFD CALC] {pump_code}: Starting VFD calculation for {target_flow:.1f} m³/hr @ {target_head:.1f}m")
            
            # Get pump specifications
            specs = pump_data.get('specifications', {})
            min_speed_rpm = specs.get('min_speed_rpm', 0)
            max_speed_rpm = specs.get('max_speed_rpm', 0) 
            test_speed_rpm = specs.get('test_speed_rpm', 0)
            
            # Validate speed range data
            if not test_speed_rpm or test_speed_rpm <= 0:
                default_speed = config.get('performance_vfd', 'default_4pole_motor_speed_rpm')
                logger.warning(f"[VFD CALC] {pump_code}: No test speed data, using default {default_speed} RPM")
                test_speed_rpm = default_speed  # Common 4-pole motor speed
            
            if not min_speed_rpm or min_speed_rpm <= 0:
                min_speed_ratio = config.get('performance_vfd', 'default_minimum_vfd_speed_percentage')
                min_speed_rpm = test_speed_rpm * min_speed_ratio  # Default minimum speed ratio
                logger.debug(f"[VFD CALC] {pump_code}: Using default min speed {min_speed_rpm:.0f} RPM")
            
            if not max_speed_rpm or max_speed_rpm <= 0:
                max_speed_ratio = config.get('performance_vfd', 'default_maximum_vfd_speed_percentage')
                max_speed_rpm = test_speed_rpm * max_speed_ratio  # Default maximum speed ratio
                logger.debug(f"[VFD CALC] {pump_code}: Using default max speed {max_speed_rpm:.0f} RPM")
            
            # Get curves and find the largest impeller diameter curve (reference curve)
            curves = pump_data.get('curves', [])
            if not curves:
                logger.warning(f"[VFD CALC] {pump_code}: No curves available")
                return None
            
            # Find the largest diameter curve as reference (100% speed curve)
            reference_curve = max(curves, key=lambda c: c.get('impeller_diameter_mm', 0))
            reference_diameter = reference_curve.get('impeller_diameter_mm', 0)
            curve_points = reference_curve.get('performance_points', [])
            
            if not curve_points or len(curve_points) < 2:
                logger.warning(f"[VFD CALC] {pump_code}: Insufficient curve points")
                return None
            
            logger.debug(f"[VFD CALC] {pump_code}: Using reference curve with diameter {reference_diameter}mm, {len(curve_points)} points")
            
            # Sort points by flow for interpolation
            sorted_points = sorted(curve_points, key=lambda p: p.get('flow_m3hr', 0))
            
            # Extract flow and head arrays
            reference_flows = [p['flow_m3hr'] for p in sorted_points if 'flow_m3hr' in p and 'head_m' in p]
            reference_heads = [p['head_m'] for p in sorted_points if 'flow_m3hr' in p and 'head_m' in p]
            
            if len(reference_flows) < 2:
                logger.warning(f"[VFD CALC] {pump_code}: Insufficient valid points on reference curve")
                return None
            
            # Calculate system curve parameters
            # System curve: H = H_static + k * Q²
            # For the target point: H₂ = H_static + k * Q₂²
            h_static = target_head * h_static_ratio
            
            # Calculate system curve constant k
            if target_flow > 0:
                k_system = (target_head - h_static) / (target_flow ** 2)
            else:
                logger.warning(f"[VFD CALC] {pump_code}: Invalid target flow (zero)")
                return None
            
            logger.debug(f"[VFD CALC] {pump_code}: System curve: H_static={h_static:.1f}m, k={k_system:.6f}")
            
            # Find corresponding point on reference curve
            # We need to find (Q₁, H₁) on the reference curve such that:
            # (H₁ - H_static) / Q₁² = k_system
            
            best_point = None
            best_error = float('inf')
            
            # First try interpolation at regular intervals
            flow_min = min(reference_flows)
            flow_max = max(reference_flows)
            
            # Create interpolation function for the reference curve
            head_interp = interpolate.interp1d(reference_flows, reference_heads, 
                                             kind='cubic' if len(reference_flows) > 3 else 'linear',
                                             bounds_error=False, fill_value='extrapolate')
            
            # Search for the best matching point
            search_flows = np.linspace(flow_min * 0.5, flow_max * 1.5, 100)
            
            for q1 in search_flows:
                if q1 <= 0:
                    continue
                    
                h1 = float(head_interp(q1))
                if h1 <= h_static:
                    continue  # Head must be above static head
                
                # Calculate k for this point
                k_point = (h1 - h_static) / (q1 ** 2)
                
                # Calculate error
                error = abs(k_point - k_system) / k_system if k_system != 0 else abs(k_point)
                
                if error < best_error:
                    best_error = error
                    best_point = {'flow': q1, 'head': h1, 'k': k_point}
            
            if best_point is None or best_error > 0.1:  # Allow 10% error in k matching
                logger.warning(f"[VFD CALC] {pump_code}: Could not find matching point on system curve (best error: {best_error:.2%})")
                # Try alternative approach: use pump BEP as reference point
                bep_flow = specs.get('bep_flow_m3hr', 0)
                bep_head = specs.get('bep_head_m', 0)
                
                if bep_flow > 0 and bep_head > 0:
                    logger.info(f"[VFD CALC] {pump_code}: Using BEP as reference point")
                    best_point = {'flow': bep_flow, 'head': bep_head}
                else:
                    return None
            
            q1 = best_point['flow']
            h1 = best_point['head']
            
            logger.info(f"[VFD CALC] {pump_code}: Found reference point Q₁={q1:.1f} m³/hr, H₁={h1:.1f}m")
            
            # Calculate required speed using affinity laws
            # H₂/H₁ = (n₂/n₁)²
            # Therefore: n₂ = n₁ * sqrt(H₂/H₁)
            
            if h1 <= 0:
                logger.warning(f"[VFD CALC] {pump_code}: Invalid reference head")
                return None
            
            speed_ratio = np.sqrt(target_head / h1)
            required_speed = test_speed_rpm * speed_ratio
            
            logger.info(f"[VFD CALC] {pump_code}: Calculated speed ratio: {speed_ratio:.3f}, Required speed: {required_speed:.0f} RPM")
            
            # Validate speed is within pump's operational limits
            if required_speed < min_speed_rpm:
                logger.warning(f"[VFD CALC] {pump_code}: Required speed {required_speed:.0f} RPM below minimum {min_speed_rpm:.0f} RPM")
                return None
            
            if required_speed > max_speed_rpm:
                logger.warning(f"[VFD CALC] {pump_code}: Required speed {required_speed:.0f} RPM above maximum {max_speed_rpm:.0f} RPM")
                return None
            
            # Calculate performance at the new operating point
            # The actual operating flow should be our target flow
            operating_flow = target_flow
            operating_head = target_head
            
            # Get efficiency at reference point (efficiency remains approximately constant)
            # Find efficiency at Q₁ on the reference curve
            efficiency = None
            for point in sorted_points:
                if abs(point.get('flow_m3hr', 0) - q1) < (flow_max - flow_min) * 0.05:  # Within 5% of range
                    efficiency = point.get('efficiency_pct')
                    break
            
            if efficiency is None:
                # Interpolate efficiency
                efficiencies = [p.get('efficiency_pct', 0) for p in sorted_points if 'efficiency_pct' in p]
                if efficiencies and len(efficiencies) == len(reference_flows):
                    eff_interp = interpolate.interp1d(reference_flows, efficiencies,
                                                     kind='linear', bounds_error=False,
                                                     fill_value='extrapolate')
                    efficiency = float(eff_interp(q1))
                else:
                    # Use a conservative estimate
                    efficiency = 65.0  # Conservative default
                    logger.debug(f"[VFD CALC] {pump_code}: Using default efficiency {efficiency}%")
            
            # Calculate power using affinity laws
            # First get power at reference point using correct formula: P = ρ × g × Q × H / η
            if efficiency > 0:
                power_ref = (q1 * h1 * 1000 * 9.81) / (3600 * efficiency / 100 * 1000)
                # Power scales with speed cubed: P₂ = P₁ * (n₂/n₁)³
                operating_power = power_ref * (speed_ratio ** 3)
            else:
                operating_power = 0
            
            # Calculate NPSH at new conditions (scales with speed squared)
            npshr = None
            for point in sorted_points:
                if abs(point.get('flow_m3hr', 0) - q1) < (flow_max - flow_min) * 0.05:
                    ref_npshr = point.get('npshr_m')
                    if ref_npshr:
                        npshr = ref_npshr * (speed_ratio ** 2)
                    break
            
            # Build complete performance dictionary
            performance = {
                'meets_requirements': True,
                'flow_m3hr': operating_flow,
                'head_m': operating_head,
                'efficiency_pct': max(efficiency, 30),  # Floor at 30%
                'power_kw': operating_power,
                'npshr_m': npshr,
                'sizing_method': 'Speed Variation',
                'required_speed_rpm': round(required_speed),
                'reference_speed_rpm': test_speed_rpm,
                'speed_ratio': round(speed_ratio * 100, 1),  # As percentage
                'reference_point': {
                    'flow_m3hr': round(q1, 1),
                    'head_m': round(h1, 1)
                },
                'system_curve_k': k_system,
                'h_static': h_static,
                'impeller_diameter_mm': reference_diameter,
                'trim_percent': 100.0,  # No trimming with VFD
                'vfd_required': True,
                'operating_frequency_hz': round(50 * speed_ratio, 1)  # Assuming 50Hz base frequency
            }
            
            logger.info(f"[VFD CALC] {pump_code}: VFD calculation successful - {required_speed:.0f} RPM ({speed_ratio*100:.1f}% speed)")
            return performance
            
        except Exception as e:
            logger.error(f"[VFD CALC] Error calculating VFD performance: {str(e)}", exc_info=True)
            return None