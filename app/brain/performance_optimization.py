"""
Performance Optimization Module
===============================
Efficiency and trim optimization algorithms
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from scipy import interpolate
from .config_manager import config

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Advanced performance optimization algorithms"""
    
    def __init__(self, brain, validator):
        """
        Initialize with reference to main Brain and validator.
        
        Args:
            brain: Parent PumpBrain instance
            validator: PerformanceValidator instance
        """
        self.brain = brain
        self.validator = validator
        
        # Load configuration values for performance optimization
        # Basic thresholds
        self.min_efficiency = config.get('performance_optimization', 'minimum_acceptable_efficiency_percentage')
        self.min_trim_percent = config.get('performance_optimization', 'industry_standard_minimum_trim_percentage_15_max_trim')
        self.max_trim_percent = config.get('performance_optimization', 'maximum_trim_percentage_full_impeller')
        
        # Tolerance factors
        self.bep_precision_tolerance = config.get('performance_optimization', 'bep_precision_tolerance_factor_5_tolerance')
        self.head_safety_margin = config.get('performance_optimization', 'head_safety_margin_factor_2_safety_margin')
        self.head_requirement_tolerance = config.get('performance_optimization', 'head_requirement_tolerance_factor_98_minimum')
        
        # Algorithm tuning
        self.trim_test_start_increment = config.get('performance_optimization', 'trim_test_start_increment_percentage')
        self.trim_test_increment = config.get('performance_optimization', 'trim_test_increment_percentage')
        self.default_diameter_ratio = config.get('performance_optimization', 'default_minimum_diameter_ratio_fallback')
        
        # Efficiency baselines
        self.baseline_efficiency = config.get('performance_optimization', 'baseline_modern_pump_efficiency_percentage')
        self.fallback_efficiency = config.get('performance_optimization', 'conservative_fallback_efficiency_percentage')
        self.efficiency_floor = config.get('performance_optimization', 'minimum_efficiency_floor_percentage')
        self.bep_proximity_min = config.get('performance_optimization', 'bep_proximity_minimum_efficiency_factor')
        self.bep_proximity_max = config.get('performance_optimization', 'bep_proximity_maximum_efficiency_factor')
        self.default_flow_deviation = config.get('performance_optimization', 'default_flow_deviation_from_bep_fallback')
        
        # Penalty factors
        self.trim_penalty_rate = config.get('performance_optimization', 'trim_efficiency_penalty_per_percent_02_per_1_trim')
        self.bep_deviation_threshold = config.get('performance_optimization', 'bep_deviation_threshold_percentage')
        self.max_bep_penalty = config.get('performance_optimization', 'maximum_bep_penalty_percentage')
        self.bep_penalty_factor = config.get('performance_optimization', 'bep_deviation_penalty_factor')
        
        # Scoring weights
        self.efficiency_weight = config.get('performance_optimization', 'efficiency_score_weight_50_weight')
        self.bep_weight = config.get('performance_optimization', 'bep_proximity_score_weight_30_weight')
        self.head_weight = config.get('performance_optimization', 'head_margin_score_weight_20_weight')
        self.head_score_factor = config.get('performance_optimization', 'head_margin_score_factor')
        self.base_score = config.get('performance_optimization', 'base_score_for_calculations_100')

    def calculate_efficiency_optimized_trim(self, flows_sorted: List[float], heads_sorted: List[float], 
                                           largest_diameter: float, target_flow: float, target_head: float,
                                           original_bep_flow: float, original_bep_head: float, 
                                           pump_code: str, physics_exponents: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
        """
        Calculate optimal impeller trim that balances efficiency and head requirements.
        
        This method evaluates multiple trim levels to find the best overall performance,
        considering efficiency at operating point, BEP migration, and head margin.
        """
        try:
            logger.info(f"[EFFICIENCY TRIM] {pump_code}: Optimizing trim for {target_flow} m³/hr @ {target_head}m")
            
            # Step 1: Calculate minimum diameter needed to meet head requirements
            head_interp = interpolate.interp1d(flows_sorted, heads_sorted, 
                                            kind='linear', bounds_error=False, fill_value=0.0)
            deliverable_head = float(head_interp(target_flow))
            
            # Special tolerance for BEP testing - allow small precision differences
            if deliverable_head <= 0 or target_head > deliverable_head * self.bep_precision_tolerance:
                if target_head <= deliverable_head * self.head_safety_margin:
                    logger.info(f"[BEP TOLERANCE] {pump_code}: Allowing BEP precision difference - target {target_head}m vs max {deliverable_head:.1f}m")
                else:
                    logger.warning(f"[EFFICIENCY TRIM] {pump_code}: Cannot meet head requirement {target_head}m (max: {deliverable_head:.1f}m)")
                    return None
                
            # Calculate minimum diameter to meet head (with configured safety margin)
            min_head_ratio = (target_head * self.head_safety_margin) / deliverable_head  # Add safety margin
            min_diameter_ratio = np.sqrt(min_head_ratio) if min_head_ratio > 0 else self.default_diameter_ratio
            min_diameter = largest_diameter * min_diameter_ratio
            min_trim_for_head = min_diameter_ratio * 100
            
            # Ensure minimum diameter respects physical limits - but if impossible, fall back to minimum allowed
            if min_trim_for_head < self.min_trim_percent:
                logger.info(f"[EFFICIENCY TRIM] {pump_code}: Calculated min trim {min_trim_for_head:.1f}% below limit, using {self.min_trim_percent}%")
                min_trim_for_head = self.min_trim_percent  # Use minimum allowed instead of failing
                
            logger.info(f"[EFFICIENCY TRIM] {pump_code}: Minimum trim for head: {min_trim_for_head:.1f}% ({min_diameter:.1f}mm)")
            
            # Step 2: Define test trim levels from minimum to 100%
            test_trims = []
            
            # Always include minimum trim needed for head
            test_trims.append(min_trim_for_head)
            
            # Add incremental trims up to 100%
            current_trim = max(self.min_trim_percent, min_trim_for_head + self.trim_test_start_increment)  # Start increment above minimum
            while current_trim <= 100.0:
                test_trims.append(current_trim)
                current_trim += self.trim_test_increment  # Test in configured increments
                
            # Always include maximum trim (full impeller)
            if self.max_trim_percent not in test_trims:
                test_trims.append(self.max_trim_percent)
                
            logger.info(f"[EFFICIENCY TRIM] {pump_code}: Testing {len(test_trims)} trim levels: {[f'{t:.1f}%' for t in test_trims]}")
            
            # Step 3: Evaluate each trim level
            trim_evaluations = []
            
            for trim_percent in test_trims:
                diameter_ratio = trim_percent / 100.0
                test_diameter = largest_diameter * diameter_ratio
                
                # Calculate performance at this trim level using pump-type-specific exponent
                head_exponent = physics_exponents['head_exponent_y'] if physics_exponents else 2.0
                test_head = deliverable_head * (diameter_ratio ** head_exponent)
                
                # Skip if this trim doesn't meet head requirements
                if test_head < target_head * self.head_requirement_tolerance:  # Configured tolerance
                    logger.debug(f"[EFFICIENCY TRIM] {pump_code}: Trim {trim_percent:.1f}% gives {test_head:.1f}m < required {target_head * self.head_requirement_tolerance:.1f}m - skipping")
                    continue
                    
                # Calculate BEP migration for this trim level
                shifted_bep_flow = original_bep_flow
                shifted_bep_head = original_bep_head
                true_qbp_percent = 100.0
                
                if original_bep_flow > 0 and original_bep_head > 0 and diameter_ratio < 1.0:
                    # Apply BEP shift using pump-type-specific physics engine
                    flow_exponent = physics_exponents['flow_exponent_x'] if physics_exponents else self.validator.get_calibration_factor('bep_shift_flow_exponent', 1.2)
                    head_exponent = physics_exponents['head_exponent_y'] if physics_exponents else self.validator.get_calibration_factor('bep_shift_head_exponent', 2.2)
                    
                    shifted_bep_flow = original_bep_flow * (diameter_ratio ** flow_exponent)
                    shifted_bep_head = original_bep_head * (diameter_ratio ** head_exponent)
                    true_qbp_percent = (target_flow / shifted_bep_flow) * 100 if shifted_bep_flow > 0 else 100
                
                # Calculate efficiency at this operating point
                try:
                    # Use a physics-based estimate based on proximity to BEP
                    base_efficiency = self.baseline_efficiency  # Configured baseline efficiency
                    
                    # Adjust based on flow proximity to BEP (efficiency typically peaks at BEP)
                    if original_bep_flow > 0:
                        flow_deviation_from_bep = abs(target_flow - shifted_bep_flow) / shifted_bep_flow if shifted_bep_flow > 0 else self.default_flow_deviation
                        bep_proximity_factor = max(self.bep_proximity_min, self.bep_proximity_max - flow_deviation_from_bep)  # Efficiency drops away from BEP
                        base_efficiency = base_efficiency * bep_proximity_factor
                    
                except Exception:
                    base_efficiency = self.fallback_efficiency  # Conservative fallback
                
                # Apply trim penalty (gentler than legacy systems)
                trim_penalty = (self.base_score - trim_percent) * self.trim_penalty_rate  # Configured penalty rate
                estimated_efficiency = max(self.efficiency_floor, base_efficiency - trim_penalty)
                
                # Apply BEP deviation penalty
                qbp_deviation = abs(true_qbp_percent - self.base_score)
                if qbp_deviation > self.bep_deviation_threshold:  # Operating beyond configured threshold from BEP
                    bep_penalty = min(self.max_bep_penalty, (qbp_deviation - self.bep_deviation_threshold) * self.bep_penalty_factor)  # Up to configured max penalty
                    estimated_efficiency -= bep_penalty
                
                # Calculate overall score (higher is better)
                # Factors: configured weights for efficiency, BEP proximity, and head margin
                efficiency_score = estimated_efficiency  # 0-100 scale
                bep_score = max(0, self.base_score - qbp_deviation)  # Base score at BEP, decreases with deviation
                head_margin_m = test_head - target_head
                head_score = min(self.base_score, max(0, self.base_score - head_margin_m * self.head_score_factor))  # Prefer small positive margins
                
                overall_score = (efficiency_score * self.efficiency_weight + bep_score * self.bep_weight + head_score * self.head_weight)
                
                trim_evaluations.append({
                    'trim_percent': trim_percent,
                    'diameter_mm': test_diameter,
                    'head_m': test_head,
                    'head_margin_m': head_margin_m,
                    'efficiency_pct': estimated_efficiency,
                    'true_qbp_percent': true_qbp_percent,
                    'shifted_bep_flow': shifted_bep_flow,
                    'shifted_bep_head': shifted_bep_head,
                    'overall_score': overall_score,
                    'efficiency_score': efficiency_score,
                    'bep_score': bep_score,
                    'head_score': head_score
                })
                
            if not trim_evaluations:
                logger.warning(f"[EFFICIENCY TRIM] {pump_code}: No viable trim levels found")
                return None
                
            # Step 4: Select optimal trim level
            best_option = max(trim_evaluations, key=lambda x: x['overall_score'])
            
            logger.info(f"[EFFICIENCY TRIM] {pump_code}: Optimal trim {best_option['trim_percent']:.1f}% "
                       f"({best_option['diameter_mm']:.1f}mm) - Score: {best_option['overall_score']:.1f}")
            
            return {
                'required_diameter_mm': best_option['diameter_mm'],
                'trim_percent': best_option['trim_percent'],
                'estimated_efficiency': best_option['efficiency_pct'],
                'true_qbp_percent': best_option['true_qbp_percent'],
                'shifted_bep_flow': best_option['shifted_bep_flow'],
                'shifted_bep_head': best_option['shifted_bep_head'],
                'optimization_score': best_option['overall_score'],
                'head_margin_m': best_option['head_margin_m'],
                'evaluation_count': len(trim_evaluations)
            }
            
        except Exception as e:
            logger.error(f"[EFFICIENCY TRIM] Error optimizing trim for {pump_code}: {str(e)}")
            return None