"""
Performance Core Module
========================
Core performance calculations and affinity law applications
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import interpolate
from .physics_models import get_exponents_for_pump_type
from ..process_logger import process_logger
from .performance_curves import CurveAnalyzer
from .performance_affinity import AffinityCalculator
from .config_manager import config

logger = logging.getLogger(__name__)


class PerformanceError(Exception):
    """Custom performance error for when performance calculations fail"""
    pass


class PerformanceCoreCalculator:
    """Core performance calculations using affinity laws and interpolation"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain and create specialized calculators.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        
        # Performance thresholds
        self.min_efficiency = config.get('performance_core', 'minimum_acceptable_efficiency_percentage')
        self.min_trim_percent = config.get('performance_core', 'minimum_trim_percentage_industry_standard')  # Industry standard - 15% maximum trim, non-negotiable
        self.max_trim_percent = config.get('performance_core', 'maximum_trim_percentage')
        
        # Industry standard affinity law exponents
        self.affinity_flow_exp = config.get('performance_core', 'default_flow_exponent_for_affinity_laws')      # Q2/Q1 = (D2/D1)^1
        self.affinity_head_exp = config.get('performance_core', 'default_head_exponent_for_affinity_laws')      # H2/H1 = (D2/D1)^2  
        self.affinity_power_exp = config.get('performance_core', 'default_power_exponent_for_affinity_laws')     # P2/P1 = (D2/D1)^3
        self.affinity_efficiency_exp = config.get('performance_core', 'default_efficiency_exponent_for_affinity_laws') # η2/η1 ≈ (D2/D1)^0.8 (industry standard)
        
        # Initialize specialized calculators
        self.curve_analyzer = CurveAnalyzer(brain)
        self.affinity_calculator = AffinityCalculator(brain)
        
        # Load BEP migration calibration factors from configuration service
        self._load_calibration_factors()
    
    def _load_calibration_factors(self):
        """
        Load BEP migration calibration factors from configuration service.
        This allows for tunable physics model parameters.
        """
        self.calibration_factors = {}
        
        if hasattr(self.brain, 'get_config_service'):
            try:
                config_service = self.brain.get_config_service()
                self.calibration_factors = config_service.get_calibration_factors()
                logger.debug(f"Loaded {len(self.calibration_factors)} calibration factors from config service")
            except Exception as e:
                logger.debug(f"Could not load calibration factors: {e}")
                self.calibration_factors = {}
        
        # Set defaults for critical factors
        default_factors = {
            'bep_shift_flow_exponent': config.get('performance_core', 'bep_shift_flow_exponent_calibration_factor'),
            'bep_shift_head_exponent': config.get('performance_core', 'bep_shift_head_exponent_calibration_factor'),
            'trim_dependent_small_exponent': config.get('performance_core', 'trim_dependent_small_exponent_calibration_factor'),
            'trim_dependent_large_exponent': config.get('performance_core', 'trim_dependent_large_exponent_calibration_factor'),
            'efficiency_penalty_volute': config.get('performance_core', 'efficiency_penalty_volute_calibration_factor'),
            'efficiency_penalty_diffuser': config.get('performance_core', 'efficiency_penalty_diffuser_calibration_factor'),
            'npsh_degradation_threshold': config.get('performance_core', 'npsh_degradation_threshold'),
            'npsh_degradation_factor': config.get('performance_core', 'npsh_degradation_factor')
        }
        
        for factor, default in default_factors.items():
            if factor not in self.calibration_factors:
                self.calibration_factors[factor] = default
                
        logger.debug(f"Calibration factors loaded: {list(self.calibration_factors.keys())}")

    def get_calibration_factor(self, factor_name: str, default_value: float = None) -> float:
        """
        Get a calibration factor by name with fallback to default.
        
        Args:
            factor_name: Name of calibration factor
            default_value: Default value if factor not found
            
        Returns:
            Calibration factor value
        """
        if default_value is None:
            default_value = config.get('performance_core', 'default_calibration_factor_value')
        return self.calibration_factors.get(factor_name, default_value)
    
    def _get_exponents_for_pump(self, pump_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get the pump-type-specific physics model exponents.
        Delegates to curve analyzer.
        """
        return self.curve_analyzer.get_exponents_for_pump(pump_data)

    def calculate_performance_at_flow(self, pump_data: Dict[str, Any], 
                                     flow: float, allow_excessive_trim: bool = False,
                                     forced_diameter: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Delegate to affinity calculator for performance at flow calculations.
        """
        return self.affinity_calculator.calculate_performance_at_flow(
            pump_data, flow, allow_excessive_trim, forced_diameter
        )

    def calculate_at_point(self, pump_data: Dict[str, Any], flow: float, 
                          head: float, impeller_trim: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        INDUSTRY STANDARD: Calculate pump performance using proper affinity law trimming.
        Always starts with largest impeller and trims DOWN using affinity laws.
        
        Args:
            pump_data: Pump data with curves
            flow: Operating flow rate (m³/hr)
            head: Operating head (m)
            impeller_trim: Optional trim percentage
        
        Returns:
            Performance calculations using industry-standard methodology
        """
        pump_code = pump_data.get('pump_code', 'Unknown')
        
        # Get pump type and physics model for detailed logging
        pump_type = pump_data.get('pump_type', 'Unknown')
        physics_exponents = get_exponents_for_pump_type(pump_type)
        
        # Log performance calculation entry with detailed formulas
        process_logger.log(f"PERFORMANCE CALCULATION: {pump_code}")
        process_logger.log(f"  Method: Industry Standard Affinity Laws")
        process_logger.log(f"  Target: {flow:.2f} m³/hr @ {head:.2f} m")
        process_logger.log(f"  Pump Type: {pump_type}")
        
        # Log physics model and formulas being used
        if physics_exponents:
            process_logger.log(f"  Physics Model: {physics_exponents.get('description', 'Unknown')}")
            process_logger.log(f"  Affinity Law Formulas:")
            # Default physics exponents for affinity laws
            default_flow_exp = self.affinity_flow_exp
            default_head_exp = self.affinity_head_exp
            default_power_exp = self.affinity_power_exp
            default_npshr_exp = config.get('performance_core', 'default_npshr_exponent')
            
            process_logger.log(f"    Flow: Q₂ = Q₁ × (D₂/D₁)^{physics_exponents.get('flow_exponent_x', default_flow_exp)}")
            process_logger.log(f"    Head: H₂ = H₁ × (D₂/D₁)^{physics_exponents.get('head_exponent_y', default_head_exp)}")
            process_logger.log(f"    Power: P₂ = P₁ × (D₂/D₁)^{physics_exponents.get('power_exponent_z', default_power_exp)}")
            process_logger.log(f"    NPSH: NPSH₂ = NPSH₁ × (D₂/D₁)^{physics_exponents.get('npshr_exponent_alpha', default_npshr_exp)}")
            process_logger.log(f"  Calculation: D₂ = D₁ × (H₂/H₁)^(1/{physics_exponents.get('head_exponent_y', default_head_exp)})")
        
        # Log calibration factors if available
        if hasattr(self, 'calibration_factors'):
            process_logger.log(f"  Calibration Factors:")
            for factor_name, factor_value in self.calibration_factors.items():
                process_logger.log(f"    {factor_name}: {factor_value}")
        
        if impeller_trim:
            process_logger.log(f"  Requested Trim: {impeller_trim:.1f}%")
        
        # Import the advanced calculator for industry standard method
        from .performance_advanced import PerformanceAdvancedCalculator
        advanced_calc = PerformanceAdvancedCalculator(self.brain)
        
        # Use industry-standard method from advanced module
        result = advanced_calc.calculate_at_point_industry_standard(pump_data, flow, head, impeller_trim)
        
        # Log results
        if result:
            process_logger.log(f"  Results:")
            process_logger.log(f"    Efficiency: {result.get('efficiency_pct', 0):.1f}%")
            process_logger.log(f"    Power: {result.get('power_kw', 0):.1f} kW")
            process_logger.log(f"    NPSH: {result.get('npshr_m', 0):.1f} m")
            process_logger.log(f"    Impeller: {result.get('impeller_diameter_mm', 0):.1f} mm")
            process_logger.log(f"    Trim: {result.get('trim_percent', 100):.1f}%")
        else:
            process_logger.log(f"  Result: FAILED - Unable to calculate performance", "WARNING")
        
        return result

    def _calculate_required_diameter_direct(self, flows_sorted, heads_sorted, 
                                          largest_diameter, target_flow, target_head, pump_code, physics_exponents=None):
        """
        Delegate to affinity calculator for direct diameter calculations.
        """
        return self.affinity_calculator.calculate_required_diameter_direct(
            flows_sorted, heads_sorted, largest_diameter, target_flow, target_head, pump_code, physics_exponents
        )

    def _find_best_impeller_curve_for_head(self, pump_data, flow, head, pump_code):
        """
        Delegate to curve analyzer for finding best impeller curve.
        """
        return self.curve_analyzer.find_best_impeller_curve_for_head(pump_data, flow, head, pump_code)

    def _calculate_performance_for_curve(self, pump_data, curve, diameter, flows_sorted, heads_sorted, flow, head, pump_code):
        """
        Delegate to curve analyzer for performance calculations on specific curves.
        """
        return self.curve_analyzer.calculate_performance_for_curve(
            pump_data, curve, diameter, flows_sorted, heads_sorted, flow, head, pump_code
        )

    def apply_affinity_laws(self, base_curve: Dict[str, Any],
                           target_diameter: float, target_flow: float, target_head: float,
                           pump_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate to affinity calculator for affinity law applications.
        """
        return self.affinity_calculator.apply_affinity_laws(
            base_curve, target_diameter, target_flow, target_head, pump_data
        )

    def _calculate_hydraulic_power(self, flow_m3hr: float, head_m: float, 
                                  efficiency_pct: float) -> float:
        """
        Delegate to affinity calculator for hydraulic power calculations.
        """
        return self.affinity_calculator.calculate_hydraulic_power(flow_m3hr, head_m, efficiency_pct)