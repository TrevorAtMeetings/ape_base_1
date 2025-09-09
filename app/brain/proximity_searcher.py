"""
Proximity Searcher Module
=========================
BEP proximity search and pump ranking functionality
"""

import logging
import math
from typing import Dict, List, Any, Optional

from .hydraulic_classifier import HydraulicClassifier
from .bep_calculator import BEPCalculator
from .config_manager import config

logger = logging.getLogger(__name__)


class ProximitySearcher:
    """Handles BEP proximity search and pump ranking"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        self.hydraulic_classifier = HydraulicClassifier()
        self.bep_calculator = BEPCalculator()
    
    def find_pumps_by_bep_proximity(self, flow: float, head: float, 
                                   pump_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Enhanced BEP proximity search with pump-type-specific weighting.
        Uses specific speed to classify pumps and apply appropriate distance metrics.
        
        Args:
            flow: Required flow rate (m³/hr)
            head: Required head (m)
            pump_type: Optional pump type filter
        
        Returns:
            List of top 20 pumps with enhanced scoring based on hydraulic type
        """
        logger.info(f"[BEP PROXIMITY] Finding pumps near flow={flow} m³/hr, head={head}m")
        
        if not self.brain.repository:
            logger.error("[BEP PROXIMITY] Repository not available")
            return []
        
        # Enhanced input validation
        if flow <= 0 or head <= 0:
            logger.error(f"[BEP PROXIMITY] Invalid inputs: flow={flow}, head={head}")
            return []
        
        # Additional safety checks
        max_realistic_flow = config.get('proximity_searcher', 'maximum_realistic_flow_rate_for_centrifugal_pumps')  # Unrealistic for centrifugal pumps
        max_realistic_head = config.get('proximity_searcher', 'maximum_realistic_head_for_centrifugal_pumps')   # Unrealistic for centrifugal pumps
        
        if flow > max_realistic_flow:
            logger.warning(f"[BEP PROXIMITY] Unusually high flow rate: {flow} m³/hr (>{max_realistic_flow:,} limit)")
        
        if head > max_realistic_head:
            logger.warning(f"[BEP PROXIMITY] Unusually high head: {head} m (>{max_realistic_head:,} limit)")
        
        # Get all pumps from repository
        all_pumps = self.brain.repository.get_pump_models()
        candidate_pumps = []
        
        for pump in all_pumps:
            pump_code = pump.get('pump_code', 'Unknown')
            
            # Apply pump type filter if specified
            if pump_type:
                pump_type_actual = pump.get('pump_type', '')
                if pump_type.upper() not in pump_type_actual.upper():
                    continue
            
            # Get BEP data from specifications (authentic manufacturer data)
            specs = pump.get('specifications', {})
            bep_flow = specs.get('bep_flow_m3hr')
            bep_head = specs.get('bep_head_m')
            bep_efficiency = specs.get('bep_efficiency_pct')
            
            # Skip pumps without valid BEP data
            if not bep_flow or not bep_head or bep_flow <= 0 or bep_head <= 0:
                logger.debug(f"[BEP PROXIMITY] {pump_code}: Skipping - no valid BEP data")
                continue
            
            # Get speed from specifications or use default
            default_motor_speed = config.get('proximity_searcher', 'default_2pole_motor_speed_at_50hz_rpm')
            speed_rpm = specs.get('speed_rpm', default_motor_speed)
            
            # Calculate specific speed for pump classification
            specific_speed = self.hydraulic_classifier.calculate_specific_speed(bep_flow, bep_head, speed_rpm)
            hydraulic_type = self.hydraulic_classifier.classify_pump_hydraulic_type(specific_speed)
            
            # Calculate symmetric normalized differences
            flow_delta = abs(flow - bep_flow) / max(flow, bep_flow)
            head_delta = abs(head - bep_head) / max(head, bep_head)
            
            # Apply pump-type-specific weighting to distance calculation
            weighted_distance = math.sqrt(
                hydraulic_type['flow_weight'] * (flow_delta ** 2) + 
                hydraulic_type['head_weight'] * (head_delta ** 2)
            )
            
            # Convert to percentage for display
            proximity_score_pct = weighted_distance * config.get('proximity_searcher', 'percentage_conversion_factor')
            
            # Enhanced categorization with pump-type consideration
            excellent_threshold = config.get('proximity_searcher', 'excellent_proximity_scoring_threshold')
            good_threshold = config.get('proximity_searcher', 'good_proximity_scoring_threshold')
            fair_threshold = config.get('proximity_searcher', 'fair_proximity_scoring_threshold')
            
            if proximity_score_pct < excellent_threshold:
                proximity_category = "Excellent"
                category_color = "#4CAF50"
            elif proximity_score_pct < good_threshold:
                proximity_category = "Good"
                category_color = "#8BC34A"
            elif proximity_score_pct < fair_threshold:
                proximity_category = "Moderate"
                category_color = "#FF9800"
            else:
                proximity_category = "Poor"
                category_color = "#F44336"
            
            # Get BEP efficiency if missing
            if not bep_efficiency:
                bep_data = self.bep_calculator.calculate_bep_from_curves_intelligent(pump, flow, head)
                bep_efficiency = bep_data.get('efficiency_pct', 0) if bep_data else 0
                if bep_data:
                    # Update BEP values and recalculate
                    bep_flow = bep_data.get('flow_m3hr', bep_flow)
                    bep_head = bep_data.get('head_m', bep_head)
                    flow_delta = abs(flow - bep_flow) / max(flow, bep_flow)
                    head_delta = abs(head - bep_head) / max(head, bep_head)
                    weighted_distance = math.sqrt(
                        hydraulic_type['flow_weight'] * (flow_delta ** 2) + 
                        hydraulic_type['head_weight'] * (head_delta ** 2)
                    )
                    proximity_score_pct = weighted_distance * config.get('proximity_searcher', 'percentage_conversion_factor')
            
            # Validate BEP efficiency
            min_efficiency_floor = config.get('proximity_searcher', 'minimum_realistic_efficiency_floor_percentage')
            max_efficiency_ceiling = config.get('proximity_searcher', 'maximum_realistic_bep_efficiency_percentage')
            if bep_efficiency and (bep_efficiency < min_efficiency_floor or bep_efficiency > max_efficiency_ceiling):
                logger.warning(f"[BEP PROXIMITY] {pump_code}: Questionable BEP efficiency {bep_efficiency}%")
            
            # Calculate trim requirement if pump BEP head is higher than required
            trim_ratio = config.get('proximity_searcher', 'default_trim_ratio_no_trim')
            predicted_efficiency = bep_efficiency
            if bep_head > head:
                trim_ratio = self.hydraulic_classifier.calculate_trim_requirement(
                    bep_head, head, hydraulic_type['trim_head_exp']
                )
                # Predict efficiency drop from trimming
                trim_percent = (1 - trim_ratio) * config.get('proximity_searcher', 'percentage_conversion_factor')
                efficiency_drop = trim_percent * hydraulic_type['efficiency_drop_per_trim']
                min_efficiency_floor = config.get('proximity_searcher', 'minimum_realistic_efficiency_floor_percentage')
                predicted_efficiency = max(bep_efficiency - efficiency_drop, min_efficiency_floor)
            
            # Calculate operating range score (how well pump can handle flow variations)
            # Wider operating range is better for variable conditions
            radial_threshold = config.get('proximity_searcher', 'specific_speed_threshold_for_radial_pumps')
            mixed_flow_threshold = config.get('proximity_searcher', 'specific_speed_threshold_for_mixed_flow_pumps')
            
            if specific_speed < radial_threshold:  # Radial pumps have wider stable range
                operating_range_score = config.get('proximity_searcher', 'operating_range_score_for_radial_pumps')
            elif specific_speed < mixed_flow_threshold:  # Mixed flow moderate range
                operating_range_score = config.get('proximity_searcher', 'operating_range_score_for_mixed_flow_pumps')
            else:  # Axial narrow stable range
                operating_range_score = config.get('proximity_searcher', 'operating_range_score_for_axial_pumps')
            
            candidate_pumps.append({
                'pump_code': pump_code,
                'pump': pump,  # Include full pump data
                'proximity_score': weighted_distance,  # Raw weighted score for sorting
                'proximity_score_pct': proximity_score_pct,  # Percentage for display
                'proximity_category': proximity_category,
                'category_color': category_color,
                'bep_efficiency': bep_efficiency or 0,
                'predicted_efficiency': predicted_efficiency,  # After trimming
                'bep_flow': bep_flow,
                'bep_head': bep_head,
                'flow_delta_pct': flow_delta * config.get('proximity_searcher', 'percentage_conversion_factor'),
                'head_delta_pct': head_delta * config.get('proximity_searcher', 'percentage_conversion_factor'),
                'specific_speed': specific_speed,
                'hydraulic_type': hydraulic_type['type'],
                'hydraulic_description': hydraulic_type['description'],
                'trim_ratio': trim_ratio,
                'trim_percent': (1 - trim_ratio) * config.get('proximity_searcher', 'percentage_conversion_factor'),
                'operating_range_score': operating_range_score,
                'flow_weight': hydraulic_type['flow_weight'],
                'head_weight': hydraulic_type['head_weight']
            })
        
        # Enhanced multi-level sort:
        # 1. Proximity score (lower is better)
        # 2. Predicted efficiency after trim (higher is better)
        # 3. Operating range score (higher is better for flexibility)
        candidate_pumps.sort(key=lambda x: (
            x['proximity_score'], 
            -x['predicted_efficiency'],
            -x['operating_range_score']
        ))
        
        # Return top N pumps
        num_top_pumps = config.get('proximity_searcher', 'number_of_top_pumps_to_return_from_proximity_search')
        top_pumps = candidate_pumps[:num_top_pumps]
        
        top_pump_count = config.get('proximity_searcher', 'number_of_top_pumps_to_return_from_proximity_search')
        logger.info(f"[BEP PROXIMITY] Found {len(candidate_pumps)} pumps with BEP data, returning top {top_pump_count}")
        if top_pumps:
            best = top_pumps[0]
            logger.info(f"[BEP PROXIMITY] Best match: {best['pump_code']} - "
                      f"Proximity: {best['proximity_score_pct']:.1f}%, "
                      f"Ns: {best['specific_speed']:.1f}, "
                      f"Type: {best['hydraulic_type']}, "
                      f"Trim: {best['trim_percent']:.1f}%, "
                      f"Predicted Eff: {best['predicted_efficiency']:.1f}%")
        
        return top_pumps
    
    def rank_pumps(self, pump_list: List[str], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank pumps based on criteria.
        
        Args:
            pump_list: List of pump codes
            criteria: Ranking criteria
        
        Returns:
            Ranked list with analysis
        """
        flow = criteria.get('flow', 0)
        head = criteria.get('head', 0)
        
        if not flow or not head:
            logger.error("Flow and head required for ranking")
            return []
        
        evaluations = []
        
        # Import here to avoid circular imports
        from .pump_evaluator import PumpEvaluator
        pump_evaluator = PumpEvaluator(self.brain)
        
        for pump_code in pump_list:
            try:
                # Get pump data
                pump_data = self.brain.repository.get_pump_by_code(pump_code)
                if not pump_data:
                    logger.warning(f"Pump {pump_code} not found")
                    continue
                
                # Evaluate pump
                evaluation = pump_evaluator.evaluate_single_pump(pump_data, flow, head, pump_code)
                evaluations.append(evaluation)
                
            except Exception as e:
                logger.error(f"Error ranking pump {pump_code}: {str(e)}")
                continue
        
        # Sort by score
        evaluations.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        return evaluations