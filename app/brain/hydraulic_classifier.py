"""
Hydraulic Classifier Module
===========================
Pump hydraulic type classification and trimming calculations
"""

import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HydraulicClassifier:
    """Handles pump hydraulic type classification and trimming calculations"""
    
    @staticmethod
    def calculate_specific_speed(flow_m3hr: float, head_m: float, speed_rpm: float = 2960) -> float:
        """
        Calculate specific speed (Ns) using SI definition: Ns = N√Q / H^(3/4)
        where N is in rpm, Q in m³/s, H in m
        
        Args:
            flow_m3hr: Flow rate in m³/hr (will be converted to m³/s)
            head_m: Head in meters
            speed_rpm: Pump speed in RPM (default 2960 for 2-pole at 50Hz)
        
        Returns:
            Specific speed (dimensionless SI units)
        """
        try:
            if flow_m3hr <= 0 or head_m <= 0:
                return 0
            
            # Convert flow to m³/s
            flow_m3s = flow_m3hr / 3600
            
            # Calculate specific speed: Ns = N√Q / H^(3/4)
            ns = speed_rpm * math.sqrt(flow_m3s) / (head_m ** 0.75)
            
            return ns
            
        except Exception as e:
            logger.debug(f"Error calculating specific speed: {e}")
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
        if specific_speed < 30:
            return {
                'type': 'radial_low',
                'description': 'Radial - Low Ns (steep H-Q curve)',
                'flow_weight': 0.4,  # Head more important for radial
                'head_weight': 0.6,
                'trim_flow_exp': 1.0,
                'trim_head_exp': 2.0,
                'efficiency_drop_per_trim': 0.1  # 0.5-1.5% for typical 5-15% trim
            }
        elif specific_speed < 60:
            return {
                'type': 'radial_mid',
                'description': 'Radial - Mid Ns (broader curve)',
                'flow_weight': 0.45,
                'head_weight': 0.55,
                'trim_flow_exp': 1.0,
                'trim_head_exp': 1.95,
                'efficiency_drop_per_trim': 0.15  # 0.8-2.0% for typical trim
            }
        elif specific_speed < 120:
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
        try:
            if current_head <= 0 or required_head <= 0:
                return 1.0
            
            if required_head > current_head:
                return 1.0  # Cannot trim up
            
            # Calculate trim ratio: D2/D1 = (H2/H1)^(1/exp)
            trim_ratio = math.pow(required_head / current_head, 1.0 / trim_head_exp)
            
            # Enforce 15% maximum trim limit
            if trim_ratio < 0.85:
                logger.debug(f"Trim requirement {(1-trim_ratio)*100:.1f}% exceeds 15% limit")
                return 0.85
            
            return trim_ratio
            
        except Exception as e:
            logger.debug(f"Error calculating trim requirement: {e}")
            return 1.0