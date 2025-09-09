"""
Performance Curves Module
=========================
Curve analysis, impeller selection, and interpolation utilities
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import interpolate
from .physics_models import get_exponents_for_pump_type
from .config_manager import config

logger = logging.getLogger(__name__)


class CurveAnalyzer:
    """Curve analysis, impeller selection, and interpolation methods"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        logger.info("Entering performance_curves.py file")
        self.brain = brain
        
        # Performance thresholds
        self.min_efficiency = config.get('performance_curves', 'minimum_acceptable_pump_efficiency_percentage')
        self.min_trim_percent = config.get('performance_curves', 'industry_standard_minimum_trim_percentage_15_max_trim')
        self.max_trim_percent = config.get('performance_curves', 'maximum_trim_percentage_full_impeller')

    def get_exponents_for_pump(self, pump_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get the pump-type-specific physics model exponents.
        
        This method implements the Polymorphic Physics Model by selecting
        the correct set of affinity law exponents based on the pump type.
        Different pump types (axial, radial, mixed flow) have different
        scaling behaviors when their impellers are trimmed.
        
        Args:
            pump_data: Pump data dictionary containing pump_type
            
        Returns:
            Dictionary of physics exponents for this pump type
        """
        pump_type = pump_data.get('pump_type', '')
        pump_code = pump_data.get('pump_code', 'Unknown')
        
        # Get pump-type-specific exponents from physics model
        exponents = get_exponents_for_pump_type(pump_type)
        
        # Log which physics model is being used
        model_type = exponents.get('description', 'Unknown model')
        
        return exponents

    def find_best_impeller_curve_for_head(self, pump_data, flow, head, pump_code):
        """
        ENHANCED: Find the best impeller curve when target head is below largest curve capability.
        
        Checks smaller impeller curves to find one that naturally delivers closer to the target head.
        
        Args:
            pump_data: Complete pump data with all curves
            flow: Required flow rate (m³/hr) 
            head: Required head (m)
            pump_code: Pump identifier for logging
            
        Returns:
            Tuple (curve_dict, diameter) for the best matching curve, or (None, None) if none found
        """
        try:
            curves = pump_data.get('curves', [])
            if not curves:
                logger.debug(f"[CURVE FINDER] {pump_code}: No curves available")
                return None, None
            
            # Sort curves by diameter descending (largest first)
            curves_by_size = sorted(curves, key=lambda c: c.get('impeller_diameter_mm', 0), reverse=True)
            
            best_curve = None
            best_diameter = None
            best_head_match_score = float('inf')  # Lower is better (closer to target head)
            
            logger.debug(f"[CURVE FINDER] {pump_code}: Evaluating {len(curves_by_size)} curves for {flow} m³/hr @ {head}m")
            
            for curve in curves_by_size:
                diameter = curve.get('impeller_diameter_mm', 0)
                if diameter <= 0:
                    continue
                    
                curve_points = curve.get('performance_points', [])
                min_points_required = config.get('performance_curves', 'minimum_number_of_curve_points_required_for_interpolation')
                if not curve_points or len(curve_points) < min_points_required:
                    logger.debug(f"[CURVE FINDER] {pump_code}: Curve {diameter}mm has insufficient points")
                    continue
                
                # Extract valid flow and head data
                flows = [p.get('flow_m3hr', 0) for p in curve_points if p.get('flow_m3hr') is not None and p.get('head_m') is not None]
                heads = [p.get('head_m', 0) for p in curve_points if p.get('flow_m3hr') is not None and p.get('head_m') is not None]
                
                min_points_required = config.get('performance_curves', 'minimum_number_of_curve_points_required_for_interpolation')
                if len(flows) < min_points_required or len(heads) < min_points_required:
                    logger.debug(f"[CURVE FINDER] {pump_code}: Curve {diameter}mm has insufficient valid data")
                    continue
                
                # Check if flow is within this curve's range (with 10% tolerance)
                min_flow, max_flow = min(flows), max(flows)
                flow_min_tolerance = config.get('performance_curves', 'flow_range_minimum_tolerance_factor_90')
                flow_max_tolerance = config.get('performance_curves', 'flow_range_maximum_tolerance_factor_110')
                if not (min_flow * flow_min_tolerance <= flow <= max_flow * flow_max_tolerance):
                    logger.debug(f"[CURVE FINDER] {pump_code}: Flow {flow} outside curve {diameter}mm range [{min_flow:.1f}, {max_flow:.1f}]")
                    continue
                
                try:
                    # Sort points by flow for interpolation
                    sorted_data = sorted(zip(flows, heads), key=lambda p: p[0])
                    flows_sorted, heads_sorted = zip(*sorted_data)
                    
                    # Interpolate head at target flow
                    head_interp = interpolate.interp1d(flows_sorted, heads_sorted, 
                                                     kind='linear', bounds_error=False)
                    delivered_head = float(head_interp(flow))
                    
                    if np.isnan(delivered_head) or delivered_head <= 0:
                        logger.debug(f"[CURVE FINDER] {pump_code}: Invalid interpolated head for curve {diameter}mm")
                        continue
                    
                    # Calculate match score - how close is delivered head to target head
                    head_difference = abs(delivered_head - head)
                    head_match_score = head_difference
                    
                    # Prefer curves that deliver slightly more than target (safety margin)
                    min_head_factor = config.get('performance_curves', 'minimum_head_requirement_factor_98')
                    if delivered_head >= head * min_head_factor:  # Must meet at least 98% of target
                        # Bonus for delivering close to target (within 10% over)
                        max_preferred_head_factor = config.get('performance_curves', 'maximum_preferred_head_factor_110')
                        head_match_bonus = config.get('performance_curves', 'head_match_bonus_factor_30_bonus')
                        if head <= delivered_head <= head * max_preferred_head_factor:
                            head_match_score *= head_match_bonus  # 30% bonus for good match
                        
                        logger.debug(f"[CURVE FINDER] {pump_code}: Curve {diameter}mm delivers {delivered_head:.1f}m (score: {head_match_score:.2f})")
                        
                        if head_match_score < best_head_match_score:
                            best_head_match_score = head_match_score
                            best_curve = curve
                            best_diameter = diameter
                    else:
                        min_head_factor = config.get('performance_curves', 'hard_coded_head_requirement_factor_for_validation')
                        logger.debug(f"[CURVE FINDER] {pump_code}: Curve {diameter}mm delivers {delivered_head:.1f}m < required {head*min_head_factor:.1f}m")
                
                except Exception as e:
                    logger.debug(f"[CURVE FINDER] {pump_code}: Error evaluating curve {diameter}mm: {e}")
                    continue
            
            if best_curve is not None:
                logger.info(f"[CURVE FINDER] {pump_code}: Selected {best_diameter}mm curve (score: {best_head_match_score:.2f})")
                return best_curve, best_diameter
            else:
                logger.debug(f"[CURVE FINDER] {pump_code}: No suitable curve found")
                return None, None
                
        except Exception as e:
            logger.error(f"[CURVE FINDER] {pump_code}: Unexpected error: {e}")
            return None, None

    def calculate_performance_for_curve(self, pump_data, curve, diameter, flows_sorted, heads_sorted, flow, head, pump_code):
        """
        Calculate performance metrics for a specific impeller curve at target operating point.
        
        Args:
            pump_data: Complete pump data dictionary
            curve: Specific impeller curve data
            diameter: Impeller diameter for this curve (mm)
            flows_sorted: Sorted flow data for interpolation
            heads_sorted: Sorted head data for interpolation  
            flow: Target operating flow (m³/hr)
            head: Target operating head (m)
            pump_code: Pump identifier for logging
            
        Returns:
            Dictionary with performance metrics or None if calculation fails
        """
        try:
            curve_points = curve.get('performance_points', [])
            if not curve_points:
                return None
            
            # Create interpolation functions
            head_interp = interpolate.interp1d(flows_sorted, heads_sorted, 
                                             kind='linear', bounds_error=False)
            
            # Get efficiency data
            efficiencies = [p.get('efficiency_pct', 0) for p in curve_points if p.get('efficiency_pct') is not None]
            if efficiencies and len(efficiencies) == len(flows_sorted):
                eff_interp = interpolate.interp1d(flows_sorted, efficiencies, 
                                                kind='linear', bounds_error=False)
                efficiency = float(eff_interp(flow))
                if np.isnan(efficiency):
                    efficiency = config.get('performance_curves', 'conservative_fallback_efficiency_percentage')  # Conservative fallback
            else:
                efficiency = config.get('performance_curves', 'conservative_fallback_efficiency_percentage')  # Conservative fallback when no efficiency data
            
            # Get power data
            powers = [p.get('power_kw') for p in curve_points if p.get('power_kw') is not None]
            if powers and len(powers) == len(flows_sorted):
                power_interp = interpolate.interp1d(flows_sorted, powers, 
                                                  kind='linear', bounds_error=False)
                power = float(power_interp(flow))
                if np.isnan(power):
                    power = None
            else:
                power = None
            
            # Calculate hydraulic power if needed
            if power is None and efficiency > 0:
                # P = ρ × g × Q × H / η
                water_density = config.get('performance_curves', 'water_density_kgm3')
                gravity = config.get('performance_curves', 'gravitational_acceleration_ms2')
                seconds_per_hour = config.get('performance_curves', 'seconds_per_hour_for_flow_conversions')
                flow_m3s = flow / seconds_per_hour  # Convert to m³/s
                watts_to_kw = config.get('performance_curves', 'watts_to_kilowatts_conversion_factor')
                percentage_factor = config.get('performance_curves', 'percentage_conversion_factor')
                power = (water_density * gravity * flow_m3s * head) / (efficiency / percentage_factor) / watts_to_kw  # kW
            
            # Get NPSH data
            npsh_values = [p.get('npshr_m') for p in curve_points if p.get('npshr_m') is not None]
            npshr = None
            if npsh_values and len(npsh_values) == len(flows_sorted):
                npsh_interp = interpolate.interp1d(flows_sorted, npsh_values,
                                                 kind='linear', bounds_error=False)
                npshr = float(npsh_interp(flow))
                if np.isnan(npshr):
                    npshr = None
            
            # Calculate head delivered by this curve
            delivered_head = float(head_interp(flow))
            if np.isnan(delivered_head):
                return None
            
            return {
                'flow_m3hr': flow,
                'head_m': delivered_head,  # What this curve actually delivers
                'efficiency_pct': max(self.min_efficiency, efficiency),
                'power_kw': power if power else config.get('performance_curves', 'default_power_value_when_none_available'),
                'npshr_m': npshr,
                'impeller_diameter_mm': diameter,
                'trim_percent': config.get('performance_curves', 'percentage_conversion_factor'),  # No trimming - using curve as-is
                'meets_requirements': delivered_head >= head * config.get('performance_curves', 'minimum_head_requirement_factor_98'),  # Does it meet 98% of target head?
                'head_margin_m': delivered_head - head,  # Excess head available
                'curve_match': True  # This is a direct curve match, not trimmed
            }
            
        except Exception as e:
            logger.error(f"[CURVE PERFORMANCE] {pump_code}: Error calculating curve performance: {e}")
            return None