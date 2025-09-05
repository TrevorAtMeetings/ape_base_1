"""
Brain System Sub-modules
========================
Intelligence components for the centralized Brain system.
"""

from .selection_core import SelectionIntelligence
from .performance_core import PerformanceCoreCalculator, PerformanceError
from .performance_advanced import PerformanceAdvancedCalculator

# Create unified PerformanceAnalyzer class combining both calculators
class PerformanceAnalyzer:
    """Unified Performance Analyzer combining core and advanced functionality."""
    
    def __init__(self, brain):
        self.core_calc = PerformanceCoreCalculator(brain)
        self.advanced_calc = PerformanceAdvancedCalculator(brain)
        
        # Expose properties for compatibility
        self.brain = brain
        self.min_efficiency = self.core_calc.min_efficiency
        self.min_trim_percent = self.core_calc.min_trim_percent
        self.max_trim_percent = self.core_calc.max_trim_percent
        self.affinity_flow_exp = self.core_calc.affinity_flow_exp
        self.affinity_head_exp = self.core_calc.affinity_head_exp
        self.affinity_power_exp = self.core_calc.affinity_power_exp
        self.affinity_efficiency_exp = self.core_calc.affinity_efficiency_exp
        self.calibration_factors = self.core_calc.calibration_factors
    
    # Delegate all methods to appropriate calculator
    def __getattr__(self, name):
        """Delegate method calls to the appropriate calculator."""
        if hasattr(self.core_calc, name):
            return getattr(self.core_calc, name)
        elif hasattr(self.advanced_calc, name):
            return getattr(self.advanced_calc, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
from .charts import ChartIntelligence
from .validation import DataValidator
from .cache import BrainCache
from .ai_analyst import AIAnalyst

__all__ = [
    'SelectionIntelligence',
    'PerformanceAnalyzer',
    'ChartIntelligence',
    'DataValidator',
    'BrainCache',
    'AIAnalyst'
]