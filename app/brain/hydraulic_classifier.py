"""
Hydraulic Classifier Module
===========================
Pump hydraulic type classification and trimming calculations
"""

import logging
import math
from typing import Dict, Any
from .config_manager import config
from ..process_logger import process_logger

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
        # Log function entry with parameters
        process_logger.log(f"Executing: {HydraulicClassifier.__module__}.HydraulicClassifier.calculate_specific_speed(Q={flow_m3hr:.1f}, H={head_m:.1f}, N={speed_rpm})")
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
            ns = speed_rpm * math.sqrt(flow_m3s) / (head_m ** config.get('hydraulic_classifier', 'head_exponent_for_specific_speed_calculation'))
            
            # Log calculation result
            process_logger.log(f"  Specific Speed Calculation: Ns = {speed_rpm} × √({flow_m3s:.4f}) / {head_m:.2f}^0.75 = {ns:.2f}")
            
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
        # Log function entry
        process_logger.log(f"Executing: {HydraulicClassifier.__module__}.HydraulicClassifier.classify_pump_hydraulic_type(Ns={specific_speed:.2f})")
        if specific_speed <= 0:
            classification = {
                'type': 'unknown',
                'description': 'Unknown hydraulic type',
                'flow_weight': config.get('hydraulic_classifier', 'unknown_type_flow_weight'),
                'head_weight': config.get('hydraulic_classifier', 'unknown_type_head_weight'),
                'trim_flow_exp': config.get('hydraulic_classifier', 'unknown_type_trim_flow_exponent'),
                'trim_head_exp': config.get('hydraulic_classifier', 'unknown_type_trim_head_exponent'),
                'efficiency_drop_per_trim': config.get('hydraulic_classifier', 'unknown_type_efficiency_drop_per_percent_trim')  # Per percent of trim
            }
            process_logger.log(f"  → HYDRAULIC CLASSIFICATION: {classification['type']} - {classification['description']} (Ns={specific_speed:.2f})")
            return classification
        
        # Based on industry standards and provided documentation
        low_ns_threshold = config.get('hydraulic_classifier', 'low_specific_speed_threshold_for_radial_pumps')
        if specific_speed < low_ns_threshold:
            classification = {
                'type': 'radial_low',
                'description': 'Radial - Low Ns (steep H-Q curve)',
                'flow_weight': config.get('hydraulic_classifier', 'radial_low_ns_flow_weight'),  # Head more important for radial
                'head_weight': config.get('hydraulic_classifier', 'radial_low_ns_head_weight'),
                'trim_flow_exp': config.get('hydraulic_classifier', 'radial_low_ns_trim_flow_exponent'),
                'trim_head_exp': config.get('hydraulic_classifier', 'radial_low_ns_trim_head_exponent'),
                'efficiency_drop_per_trim': config.get('hydraulic_classifier', 'radial_low_ns_efficiency_drop_per_percent_trim')  # 0.5-1.5% for typical 5-15% trim
            }
            process_logger.log(f"  → HYDRAULIC CLASSIFICATION: {classification['type']} - {classification['description']} (Ns={specific_speed:.2f} < {low_ns_threshold})")
            return classification
        elif specific_speed < config.get('hydraulic_classifier', 'mid_specific_speed_threshold_for_radial_pumps'):
            mid_threshold = config.get('hydraulic_classifier', 'mid_specific_speed_threshold_for_radial_pumps')
            classification = {
                'type': 'radial_mid',
                'description': 'Radial - Mid Ns (broader curve)',
                'flow_weight': config.get('hydraulic_classifier', 'radial_mid_ns_flow_weight'),
                'head_weight': config.get('hydraulic_classifier', 'radial_mid_ns_head_weight'),
                'trim_flow_exp': config.get('hydraulic_classifier', 'radial_mid_ns_trim_flow_exponent'),
                'trim_head_exp': config.get('hydraulic_classifier', 'radial_mid_ns_trim_head_exponent'),
                'efficiency_drop_per_trim': config.get('hydraulic_classifier', 'radial_mid_ns_efficiency_drop_per_percent_trim')  # 0.8-2.0% for typical trim
            }
            process_logger.log(f"  → HYDRAULIC CLASSIFICATION: {classification['type']} - {classification['description']} (Ns={specific_speed:.2f} < {mid_threshold})")
            return classification
        elif specific_speed < config.get('hydraulic_classifier', 'high_specific_speed_threshold_for_mixed_flow_pumps'):
            return {
                'type': 'mixed_flow',
                'description': 'Mixed-flow',
                'flow_weight': config.get('hydraulic_classifier', 'mixed_flow_flow_weight'),
                'head_weight': config.get('hydraulic_classifier', 'mixed_flow_head_weight'),
                'trim_flow_exp': config.get('hydraulic_classifier', 'mixed_flow_trim_flow_exponent'),
                'trim_head_exp': config.get('hydraulic_classifier', 'mixed_flow_trim_head_exponent'),
                'efficiency_drop_per_trim': config.get('hydraulic_classifier', 'mixed_flow_efficiency_drop_per_percent_trim')  # 1.5-3.0% for typical trim
            }
        else:  # specific_speed >= 120
            return {
                'type': 'axial_flow',
                'description': 'Axial-flow (propeller)',
                'flow_weight': config.get('hydraulic_classifier', 'axial_flow_flow_weight'),  # Flow more important for axial
                'head_weight': config.get('hydraulic_classifier', 'axial_flow_head_weight'),
                'trim_flow_exp': config.get('hydraulic_classifier', 'axial_flow_trim_flow_exponent'),
                'trim_head_exp': config.get('hydraulic_classifier', 'axial_flow_trim_head_exponent'),
                'efficiency_drop_per_trim': config.get('hydraulic_classifier', 'axial_flow_efficiency_drop_per_percent_trim')  # 2.0-4.0% for typical trim
            }
    
    @staticmethod
    def calculate_trim_requirement(current_head: float, required_head: float, 
                                 trim_head_exp: float = None) -> float:
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
            # Use default trim head exponent if not provided
            if trim_head_exp is None:
                trim_head_exp = config.get('hydraulic_classifier', 'default_trim_head_exponent')
            
            trim_ratio = math.pow(required_head / current_head, config.get('hydraulic_classifier', 'default_trim_ratio_no_trim') / trim_head_exp)
            
            # Enforce maximum trim limit
            if trim_ratio < MIN_TRIM_RATIO:
                percentage_factor = config.get('hydraulic_classifier', 'percentage_conversion_factor')
                logger.debug(TRIM_LIMIT_EXCEEDED_MSG.format((1-trim_ratio)*percentage_factor, (1-MIN_TRIM_RATIO)*percentage_factor))
                return MIN_TRIM_RATIO
            
            return trim_ratio
            
        except Exception as e:
            logger.debug(TRIM_CALCULATION_ERROR_MSG.format(e))
            return 1.0