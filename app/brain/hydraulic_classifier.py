"""
Hydraulic Classifier Module
===========================
Pump hydraulic type classification and trimming calculations
"""

import logging
import math
from typing import Dict, Any
from .config_manager import config

logger = logging.getLogger(__name__)

# Message templates
SPECIFIC_SPEED_ERROR_MSG = "Error calculating specific speed: {}"
TRIM_LIMIT_EXCEEDED_MSG = "Trim requirement {:.1f}% exceeds {:.0f}% limit"
TRIM_CALCULATION_ERROR_MSG = "Error calculating trim requirement: {}"


class HydraulicClassifier:
    """Handles pump hydraulic type classification and trimming calculations"""
    
    @staticmethod
    def calculate_specific_speed(flow_m3hr: float, head_m: float, speed_rpm: float = None) -> float:
        """
        Calculate specific speed (Ns) using SI definition: Ns = N√Q / H^(3/4)
        where N is in rpm, Q in m³/s, H in m
        
        Args:
            flow_m3hr: Flow rate in m³/hr (will be converted to m³/s)
            head_m: Head in meters
            speed_rpm: Pump speed in RPM (default from config for 2-pole at 50Hz)
        
        Returns:
            Specific speed (dimensionless SI units)
        """
        try:
            if flow_m3hr <= 0 or head_m <= 0:
                return 0
            
            # Use default speed from config if not provided
            if speed_rpm is None:
                speed_rpm = config.get('hydraulic_classifier', 'default_pump_speed_for_2pole_motor_at_50hz_rpm')
            
            # Convert flow to m³/s
            seconds_per_hour = config.get('hydraulic_classifier', 'seconds_per_hour_conversion_constant')
            flow_m3s = flow_m3hr / seconds_per_hour
            
            # Calculate specific speed: Ns = N√Q / H^(3/4)
            ns = speed_rpm * math.sqrt(flow_m3s) / (head_m ** 0.75)
            
            return ns
            
        except Exception as e:
            logger.debug(SPECIFIC_SPEED_ERROR_MSG.format(e))
            return 0
    
    @staticmethod
    def classify_pump_hydraulic_type(specific_speed: float) -> Dict[str, Any]:
        """
        Classify pump hydraulic type based on specific speed
        Returns classification with scoring weights and expected characteristics
        
        Args:
            specific_speed: Calculated specific speed
            
        Returns:
            Dictionary with hydraulic type classification and parameters
        """
        if specific_speed <= 0:
            return {
                'type': 'unknown',
                'description': 'Unknown hydraulic type',
                'flow_weight': 0.5,
                'head_weight': 0.5,
                'trim_flow_exp': 1.0,
                'trim_head_exp': 2.0,
                'efficiency_drop_per_trim': 0.1  # Per percent of trim
            }
        
        # Based on industry standards and provided documentation
        low_ns_threshold = config.get('hydraulic_classifier', 'low_specific_speed_threshold_for_radial_pumps')
        if specific_speed < low_ns_threshold:
            return {
                'type': 'radial_low',
                'description': 'Radial - Low Ns (steep H-Q curve)',
                'flow_weight': 0.4,  # Head more important for radial
                'head_weight': 0.6,
                'trim_flow_exp': 1.0,
                'trim_head_exp': 2.0,
                'efficiency_drop_per_trim': 0.1  # 0.5-1.5% for typical 5-15% trim
            }
        elif specific_speed < config.get('hydraulic_classifier', 'mid_specific_speed_threshold_for_radial_pumps'):
            return {
                'type': 'radial_mid',
                'description': 'Radial - Mid Ns (broader curve)',
                'flow_weight': 0.45,
                'head_weight': 0.55,
                'trim_flow_exp': 1.0,
                'trim_head_exp': 1.95,
                'efficiency_drop_per_trim': 0.15  # 0.8-2.0% for typical trim
            }
        elif specific_speed < config.get('hydraulic_classifier', 'high_specific_speed_threshold_for_mixed_flow_pumps'):
            return {
                'type': 'mixed_flow',
                'description': 'Mixed-flow',
                'flow_weight': 0.5,
                'head_weight': 0.5,
                'trim_flow_exp': 0.97,
                'trim_head_exp': 1.85,
                'efficiency_drop_per_trim': 0.25  # 1.5-3.0% for typical trim
            }
        else:  # specific_speed >= 120
            return {
                'type': 'axial_flow',
                'description': 'Axial-flow (propeller)',
                'flow_weight': 0.55,  # Flow more important for axial
                'head_weight': 0.45,
                'trim_flow_exp': 0.95,
                'trim_head_exp': 1.65,
                'efficiency_drop_per_trim': 0.35  # 2.0-4.0% for typical trim
            }
    
    @staticmethod
    def calculate_trim_requirement(current_head: float, required_head: float, 
                                 trim_head_exp: float = 2.0) -> float:
        """
        Calculate required trim percentage to achieve target head
        Using D2/D1 = (H2/H1)^(1/exp) where exp is pump-type specific
        
        Args:
            current_head: Current pump head at BEP
            required_head: Required head for application
            trim_head_exp: Pump-type specific head exponent
        
        Returns:
            Trim ratio (1.0 = no trim, 0.85 = 15% trim)
        """
        MIN_TRIM_RATIO = config.get('hydraulic_classifier', 'minimum_trim_ratio_15_maximum_trim_limit')
        
        try:
            if current_head <= 0 or required_head <= 0:
                return 1.0
            
            if required_head > current_head:
                return 1.0  # Cannot trim up
            
            # Calculate trim ratio: D2/D1 = (H2/H1)^(1/exp)
            trim_ratio = math.pow(required_head / current_head, 1.0 / trim_head_exp)
            
            # Enforce maximum trim limit
            if trim_ratio < MIN_TRIM_RATIO:
                logger.debug(TRIM_LIMIT_EXCEEDED_MSG.format((1-trim_ratio)*100, (1-MIN_TRIM_RATIO)*100))
                return MIN_TRIM_RATIO
            
            return trim_ratio
            
        except Exception as e:
            logger.debug(TRIM_CALCULATION_ERROR_MSG.format(e))
            return 1.0