"""
Selection Validation Service for V2 Enhanced Reports
===================================================
Provides direct selection validation logic for V2 template features
without impacting existing functionality.

Author: APE Pumps Engineering
Date: August 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional
from ..pump_brain import get_pump_brain

logger = logging.getLogger(__name__)


class SelectionValidator:
    """
    Validates pump selection choices and provides optimization insights.
    Used exclusively by V2 enhanced reports to show selection quality.
    """
    
    def __init__(self, brain_instance=None):
        """
        Initialize validator with Brain instance.
        
        Args:
            brain_instance: Optional PumpBrain instance (auto-loaded if None)
        """
        self.brain = brain_instance or get_pump_brain()
        logger.debug("SelectionValidator initialized")
    
    def generate_direct_selection_validation(self, pump_code: str, flow: float, head: float, 
                                          evaluation_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate direct selection validation data for V2 template.
        
        This method analyzes whether a directly selected pump is optimal by
        running optimization in the background and comparing results.
        
        Args:
            pump_code: Selected pump code
            flow: Operating flow rate in m³/hr
            head: Operating head in meters
            evaluation_result: Optional existing evaluation result
            
        Returns:
            Dict containing validation data for V2 template
        """
        logger.debug(f"Generating selection validation for {pump_code} at {flow}m³/hr, {head}m")
        
        try:
            # Run optimization to find best alternatives (non-destructive)
            site_requirements = {
                'flow_m3hr': flow,
                'head_m': head,
                'pump_type': 'GENERAL'
            }
            brain_results = self.brain.find_best_pumps(
                site_requirements=site_requirements,
                constraints={'pump_type': 'GENERAL'}
            )
            optimal_results = brain_results.get('ranked_pumps', []) if isinstance(brain_results, dict) else brain_results
            
            # Find ranking of current pump
            current_pump_rank = self._find_pump_ranking(pump_code, optimal_results)
            
            # Get current pump efficiency
            if evaluation_result:
                current_efficiency = evaluation_result.get('efficiency_pct', 0)
            else:
                # Fallback: evaluate pump if not provided
                current_evaluation = self.brain.evaluate_pump(pump_code, flow, head)
                current_efficiency = current_evaluation.get('efficiency_pct', 0) if current_evaluation else 0
            
            # Get best alternative information
            best_alternative = optimal_results[0] if optimal_results else None
            best_alternative_code = best_alternative.get('pump_code') if best_alternative else None
            best_alternative_efficiency = best_alternative.get('efficiency_pct', 0) if best_alternative else 0
            
            # Determine if this was optimal choice
            is_optimal = current_pump_rank == 1 if current_pump_rank else False
            
            validation_data = {
                'is_direct_selection': True,  # Always true for direct selections
                'is_optimal_choice': is_optimal,
                'efficiency_pct': current_efficiency,
                'optimal_rank': current_pump_rank or 999,  # High rank if not found
                'best_alternative_code': best_alternative_code,
                'best_alternative_efficiency': best_alternative_efficiency,
                'efficiency_difference': best_alternative_efficiency - current_efficiency if best_alternative_efficiency else 0,
                'total_alternatives': len(optimal_results),
                'selection_quality': self._assess_selection_quality(current_pump_rank, current_efficiency)
            }
            
            logger.debug(f"Selection validation completed: rank {current_pump_rank}, efficiency {current_efficiency}%")
            return validation_data
            
        except Exception as e:
            logger.error(f"Error generating selection validation for {pump_code}: {str(e)}")
            # Return safe fallback data
            return {
                'is_direct_selection': True,
                'is_optimal_choice': False,
                'efficiency_pct': evaluation_result.get('efficiency_pct', 0) if evaluation_result else 0,
                'optimal_rank': 999,
                'best_alternative_code': None,
                'best_alternative_efficiency': 0,
                'efficiency_difference': 0,
                'total_alternatives': 0,
                'selection_quality': 'unknown',
                'error': str(e)
            }
    
    def _find_pump_ranking(self, pump_code: str, optimal_results: List[Dict[str, Any]]) -> Optional[int]:
        """
        Find the ranking of a specific pump in optimization results.
        
        Args:
            pump_code: Pump code to find
            optimal_results: List of optimization results
            
        Returns:
            Ranking (1-based) or None if not found
        """
        for index, result in enumerate(optimal_results):
            if result.get('pump_code') == pump_code:
                return index + 1  # 1-based ranking
        return None
    
    def _assess_selection_quality(self, rank: Optional[int], efficiency: float) -> str:
        """
        Assess the quality of a pump selection.
        
        Args:
            rank: Ranking in optimization results (1-based)
            efficiency: Pump efficiency percentage
            
        Returns:
            Quality assessment string
        """
        if not rank:
            return 'unknown'
        
        if rank == 1:
            return 'optimal'
        elif rank <= 3:
            return 'excellent'
        elif rank <= 5:
            return 'good'
        elif rank <= 10:
            return 'acceptable'
        else:
            return 'poor'
    
    def get_alternative_recommendations(self, pump_code: str, flow: float, head: float, 
                                      limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get alternative pump recommendations for comparison.
        
        Args:
            pump_code: Currently selected pump code
            flow: Operating flow rate in m³/hr
            head: Operating head in meters
            limit: Maximum number of alternatives to return
            
        Returns:
            List of alternative pump recommendations
        """
        try:
            # Get optimization results
            site_requirements = {
                'flow_m3hr': flow,
                'head_m': head,
                'pump_type': 'GENERAL'
            }
            brain_results = self.brain.find_best_pumps(
                site_requirements=site_requirements,
                constraints={'pump_type': 'GENERAL'}
            )
            optimal_results = brain_results.get('ranked_pumps', []) if isinstance(brain_results, dict) else brain_results
            
            # Filter out current pump and limit results
            alternatives = [
                pump for pump in optimal_results 
                if pump.get('pump_code') != pump_code
            ][:limit]
            
            logger.debug(f"Found {len(alternatives)} alternatives for {pump_code}")
            return alternatives
            
        except Exception as e:
            logger.error(f"Error getting alternatives for {pump_code}: {str(e)}")
            return []