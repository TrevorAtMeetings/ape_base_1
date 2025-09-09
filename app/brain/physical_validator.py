"""
Physical Validator Module
=========================
Validates pump physical capability at specific operating points
"""

import logging
from typing import Dict, Any, Tuple
from ..process_logger import process_logger
from .config_manager import config

logger = logging.getLogger(__name__)


class PhysicalValidator:
    """Validates pump physical capabilities at operating conditions"""
    
    @staticmethod
    def validate_physical_capability_at_point(pump_data: Dict[str, Any], 
                                            flow_m3hr: float, head_m: float) -> Tuple[bool, str]:
        """
        CRITICAL: Validate pump can physically deliver required head at specific flow rate.
        This is the core validation that was missing in the catalog engine.
        
        Args:
            pump_data: Pump data dictionary
            flow_m3hr: Required flow rate in m³/hr
            head_m: Required head in meters
        
        Returns:
            tuple: (is_capable: bool, failure_reason: str)
        """
        # Log function entry
        process_logger.log(f"Executing: {PhysicalValidator.__module__}.PhysicalValidator.validate_physical_capability_at_point({pump_data.get('pump_code', 'Unknown')})")
        pump_code = pump_data.get('pump_code', 'Unknown')
        curves = pump_data.get('curves', [])
        
        if not curves:
            reason = f"No performance curves available"
            process_logger.log(f"    {pump_code}: EXCLUDED - {reason}")
            logger.debug(f"Pump {pump_code}: {reason}")
            return False, reason
        
        # Check curves starting with maximum impeller diameter first (authentic manufacturer design)
        sorted_curves = sorted(curves, key=lambda x: x.get('impeller_diameter_mm', 0), reverse=True)
        
        # Track specific failure reasons
        no_valid_curves = 0
        flow_range_failures = []
        head_insufficient_details = []
        
        for curve in sorted_curves:
            curve_points = curve.get('performance_points', [])
            min_curve_points = config.get('physical_validator', 'minimum_curve_points_required_for_validation')
            if not curve_points or len(curve_points) < min_curve_points:
                no_valid_curves += 1
                continue
                
            # Extract curve data
            curve_flows = [p['flow_m3hr'] for p in curve_points]
            curve_heads = [p['head_m'] for p in curve_points]
            
            # Check if flow is within curve range (with configurable tolerance)
            min_flow = min(curve_flows)
            max_flow = max(curve_flows)
            
            flow_tolerance = config.get('physical_validator', 'flow_tolerance_for_curve_range_validation_10')
            if not (min_flow * (1-flow_tolerance) <= flow_m3hr <= max_flow * (1+flow_tolerance)):
                percentage_factor = config.get('physical_validator', 'percentage_conversion_factor_for_tolerance_display')
                flow_range_failures.append(f"{curve.get('impeller_diameter_mm', 0):.0f}mm impeller: flow range {min_flow:.1f}-{max_flow:.1f} m³/hr (±{flow_tolerance*percentage_factor:.0f}% tolerance)")
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
                
                # Check if pump can deliver AT LEAST the required head
                head_tolerance = config.get('physical_validator', 'head_tolerance_for_capability_validation_2')
                if delivered_head >= head_m * (1-head_tolerance):
                    percentage_factor = config.get('physical_validator', 'percentage_conversion_factor_for_tolerance_display')
                    process_logger.log(f"    {pump_code}: PHYSICALLY CAPABLE - Can deliver {delivered_head:.1f}m at {flow_m3hr} m³/hr (±{head_tolerance*percentage_factor:.0f}% tolerance)")
                    logger.debug(f"Pump {pump_code}: Can deliver {delivered_head:.1f}m at {flow_m3hr} m³/hr (required: {head_m}m) - VALID")
                    return True, "Physically capable"
                else:
                    head_insufficient_details.append(f"{curve.get('impeller_diameter_mm', 0):.0f}mm impeller: delivers {delivered_head:.1f}m (need {head_m:.1f}m)")
                    logger.debug(f"Pump {pump_code}: Can only deliver {delivered_head:.1f}m at {flow_m3hr} m³/hr (required: {head_m}m) - INSUFFICIENT")
                    
            except Exception as e:
                logger.debug(f"Error interpolating curve for {pump_data.get('pump_code')}: {e}")
                continue
        
        # Build detailed failure reason
        failure_parts = []
        
        if no_valid_curves > 0:
            failure_parts.append(f"{no_valid_curves} curves have insufficient data points")
        
        if flow_range_failures:
            max_flow_failures = config.get('physical_validator', 'maximum_flow_range_failures_to_display_in_error_messages')
            failure_parts.append(f"Flow {flow_m3hr:.1f} m³/hr outside all curve ranges: " + "; ".join(flow_range_failures[:max_flow_failures]))
        
        if head_insufficient_details:
            max_head_details = config.get('physical_validator', 'maximum_head_insufficient_details_to_display_in_error_messages')
            failure_parts.append(f"Insufficient head delivery: " + "; ".join(head_insufficient_details[:max_head_details]))
        
        if not failure_parts:
            failure_parts.append(f"Cannot deliver {head_m:.1f}m at {flow_m3hr:.1f} m³/hr")
        
        reason = " | ".join(failure_parts)
        process_logger.log(f"    {pump_code}: EXCLUDED - {reason}")
        logger.debug(f"Pump {pump_code}: {reason}")
        return False, reason