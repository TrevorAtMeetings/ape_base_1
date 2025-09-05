"""
Performance Advanced Module
============================
Advanced performance calculations delegating to specialized modules
"""

import logging
from typing import Dict, Any, Optional
from .performance_industry_standard import IndustryStandardCalculator
from .performance_validation import PerformanceValidator
from .performance_optimization import PerformanceOptimizer
from .performance_vfd import VFDCalculator

logger = logging.getLogger(__name__)


class PerformanceAdvancedCalculator:
    """Advanced performance calculations using specialized delegation modules"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain and create specialized calculators.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        
        # Initialize specialized calculation modules
        self.validator = PerformanceValidator(brain)
        self.optimizer = PerformanceOptimizer(brain, self.validator)
        self.vfd_calculator = VFDCalculator(brain)
        self.industry_calculator = IndustryStandardCalculator(brain, self.validator, self.optimizer)

    def calculate_at_point_industry_standard(self, pump_data: Dict[str, Any], flow: float, 
                          head: float, impeller_trim: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Delegate to specialized industry standard calculator.
        """
        return self.industry_calculator.calculate_at_point_industry_standard(
            pump_data, flow, head, impeller_trim
        )

    def calculate_performance_with_speed_variation(self, pump_data: Dict[str, Any], 
                                                   target_flow: float, 
                                                   target_head: float,
                                                   h_static_ratio: float = 0.4) -> Optional[Dict[str, Any]]:
        """
        Delegate to specialized VFD calculator.
        """
        return self.vfd_calculator.calculate_performance_with_speed_variation(
            pump_data, target_flow, target_head, h_static_ratio
        )

    def validate_envelope(self, pump: Dict[str, Any], flow: float, head: float) -> Dict[str, Any]:
        """
        Delegate to specialized validator.
        """
        return self.validator.validate_envelope(pump, flow, head)