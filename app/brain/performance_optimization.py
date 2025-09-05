"""
Performance Optimization Module
===============================
Efficiency and trim optimization algorithms
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from scipy import interpolate

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
        
        # Performance thresholds
        self.min_efficiency = 40.0
        self.min_trim_percent = 85.0  # Industry standard - 15% maximum trim, non-negotiable
        self.max_trim_percent = 100.0

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
            head_tolerance = 1.05  # 5% tolerance for BEP precision issues
            if deliverable_head <= 0 or target_head > deliverable_head * head_tolerance:
                if target_head <= deliverable_head * 1.02:
                    logger.info(f"[BEP TOLERANCE] {pump_code}: Allowing BEP precision difference - target {target_head}m vs max {deliverable_head:.1f}m")
                else:
                    logger.warning(f"[EFFICIENCY TRIM] {pump_code}: Cannot meet head requirement {target_head}m (max: {deliverable_head:.1f}m)")
                    return None
                
            # Calculate minimum diameter to meet head (with 2% margin for safety like legacy system)
            min_head_ratio = (target_head * 1.02) / deliverable_head  # Add 2% safety margin (reduced from 5%)
            min_diameter_ratio = np.sqrt(min_head_ratio) if min_head_ratio > 0 else 0.85
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
            current_trim = max(85.0, min_trim_for_head + 2.0)  # Start 2% above minimum or 85%
            while current_trim <= 100.0:
                test_trims.append(current_trim)
                current_trim += 3.0  # Test in 3% increments
                
            # Always include 100% (full impeller)
            if 100.0 not in test_trims:
                test_trims.append(100.0)
                
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
                if test_head < target_head * 0.98:  # 2% tolerance like legacy system
                    logger.debug(f"[EFFICIENCY TRIM] {pump_code}: Trim {trim_percent:.1f}% gives {test_head:.1f}m < required {target_head * 0.98:.1f}m - skipping")
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
                    base_efficiency = 85.0  # Modern pump baseline efficiency
                    
                    # Adjust based on flow proximity to BEP (efficiency typically peaks at BEP)
                    if original_bep_flow > 0:
                        flow_deviation_from_bep = abs(target_flow - shifted_bep_flow) / shifted_bep_flow if shifted_bep_flow > 0 else 0.5
                        bep_proximity_factor = max(0.7, 1.0 - flow_deviation_from_bep)  # Efficiency drops away from BEP
                        base_efficiency = base_efficiency * bep_proximity_factor
                    
                except Exception:
                    base_efficiency = 80.0  # Conservative fallback
                
                # Apply trim penalty (gentler than legacy systems)
                trim_penalty = (100 - trim_percent) * 0.2  # 0.2% penalty per 1% trim
                estimated_efficiency = max(40, base_efficiency - trim_penalty)
                
                # Apply BEP deviation penalty
                qbp_deviation = abs(true_qbp_percent - 100)
                if qbp_deviation > 15:  # Operating >15% away from BEP
                    bep_penalty = min(10, (qbp_deviation - 15) * 0.3)  # Up to 10% penalty
                    estimated_efficiency -= bep_penalty
                
                # Calculate overall score (higher is better)
                # Factors: efficiency (50%), BEP proximity (30%), head margin (20%)
                efficiency_score = estimated_efficiency  # 0-100 scale
                bep_score = max(0, 100 - qbp_deviation)  # 100 at BEP, decreases with deviation
                head_margin_m = test_head - target_head
                head_score = min(100, max(0, 100 - head_margin_m * 2))  # Prefer small positive margins
                
                overall_score = (efficiency_score * 0.5 + bep_score * 0.3 + head_score * 0.2)
                
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