"""
Pump Comparison Module
Advanced comparison capabilities for multiple pump alternatives
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pump_engine import ParsedPumpData, SiteRequirements

logger = logging.getLogger(__name__)

@dataclass
class ComparisonMetrics:
    """Comparison metrics between pumps"""
    efficiency_difference: float
    power_difference: float
    cost_difference: float
    environmental_difference: float
    overall_ranking: int

class PumpComparator:
    """Advanced pump comparison and ranking system"""
    
    def __init__(self):
        self.comparison_weights = {
            'efficiency': 0.3,
            'power_consumption': 0.25,
            'lifecycle_cost': 0.25,
            'environmental_impact': 0.2
        }
    
    def generate_detailed_comparison(self, 
                                   pump_evaluations: List[Dict[str, Any]],
                                   parsed_pumps: List[ParsedPumpData]) -> Dict[str, Any]:
        """Generate comprehensive comparison between multiple pumps"""
        try:
            if len(pump_evaluations) < 2:
                return {'comparison_available': False, 'reason': 'Need at least 2 pumps for comparison'}
            
            comparison_data = {
                'comparison_available': True,
                'pump_count': len(pump_evaluations),
                'comparison_matrix': self._create_comparison_matrix(pump_evaluations),
                'ranking_analysis': self._analyze_rankings(pump_evaluations),
                'key_differentiators': self._identify_key_differentiators(pump_evaluations),
                'decision_guidance': self._generate_decision_guidance(pump_evaluations),
                'trade_off_analysis': self._analyze_trade_offs(pump_evaluations)
            }
            
            return comparison_data
            
        except Exception as e:
            logger.error(f"Error generating pump comparison: {str(e)}")
            return {'comparison_available': False, 'reason': f'Error: {str(e)}'}
    
    def _create_comparison_matrix(self, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create detailed comparison matrix"""
        matrix = []
        
        for i, eval_data in enumerate(evaluations[:3]):  # Compare top 3
            operating_point = eval_data.get('operating_point', {})
            lifecycle_cost = eval_data.get('lifecycle_cost', {})
            environmental = eval_data.get('environmental_impact', {})
            
            pump_comparison = {
                'rank': i + 1,
                'pump_code': eval_data.get('pump_code', 'Unknown'),
                'overall_score': round(eval_data.get('overall_score', 0), 1),
                'efficiency_pct': round(operating_point.get('efficiency_pct', 0), 1),
                'power_kw': round(operating_point.get('power_kw', 0), 2),
                'annual_energy_cost': lifecycle_cost.get('annual_energy_cost', 0),
                'total_10_year_cost': lifecycle_cost.get('total_10_year_cost', 0),
                'annual_co2_kg': environmental.get('annual_co2_kg', 0),
                'advantages': self._identify_pump_advantages(eval_data, i),
                'considerations': self._identify_pump_considerations(eval_data, i)
            }
            
            matrix.append(pump_comparison)
        
        return matrix
    
    def _analyze_rankings(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze ranking differences and closeness"""
        if len(evaluations) < 2:
            return {}
        
        top_score = evaluations[0].get('overall_score', 0)
        second_score = evaluations[1].get('overall_score', 0)
        score_gap = top_score - second_score
        
        analysis = {
            'score_gap': round(score_gap, 1),
            'competition_level': 'Close' if score_gap < 10 else 'Clear leader',
            'top_pump_advantages': [],
            'alternative_benefits': []
        }
        
        # Analyze top pump advantages
        top_eval = evaluations[0]
        top_op = top_eval.get('operating_point', {})
        
        if top_op.get('efficiency_pct', 0) > 85:
            analysis['top_pump_advantages'].append('Exceptional efficiency performance')
        
        if score_gap > 15:
            analysis['top_pump_advantages'].append('Significantly superior overall performance')
        
        # Analyze alternative benefits
        if len(evaluations) > 1:
            alt_eval = evaluations[1]
            alt_lifecycle = alt_eval.get('lifecycle_cost', {})
            top_lifecycle = top_eval.get('lifecycle_cost', {})
            
            if (alt_lifecycle.get('total_10_year_cost', float('inf')) < 
                top_lifecycle.get('total_10_year_cost', float('inf'))):
                analysis['alternative_benefits'].append('Lower total lifecycle cost')
        
        return analysis
    
    def _identify_key_differentiators(self, evaluations: List[Dict[str, Any]]) -> List[str]:
        """Identify key factors that differentiate the pumps"""
        differentiators = []
        
        if len(evaluations) < 2:
            return differentiators
        
        # Compare efficiency
        top_eff = evaluations[0].get('operating_point', {}).get('efficiency_pct', 0)
        second_eff = evaluations[1].get('operating_point', {}).get('efficiency_pct', 0)
        eff_diff = abs(top_eff - second_eff)
        
        if eff_diff > 5:
            differentiators.append(f"Significant efficiency difference ({eff_diff:.1f}% points)")
        
        # Compare power consumption
        top_power = evaluations[0].get('operating_point', {}).get('power_kw', 0)
        second_power = evaluations[1].get('operating_point', {}).get('power_kw', 0)
        power_diff = abs(top_power - second_power)
        
        if power_diff > 5:
            differentiators.append(f"Notable power consumption difference ({power_diff:.1f} kW)")
        
        # Compare lifecycle costs
        top_cost = evaluations[0].get('lifecycle_cost', {}).get('total_10_year_cost', 0)
        second_cost = evaluations[1].get('lifecycle_cost', {}).get('total_10_year_cost', 0)
        cost_diff = abs(top_cost - second_cost)
        
        if cost_diff > 10000:
            differentiators.append(f"Substantial lifecycle cost difference (R{cost_diff:,.0f})")
        
        return differentiators
    
    def _generate_decision_guidance(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate decision guidance based on comparison"""
        guidance = {
            'primary_recommendation': '',
            'alternative_scenarios': [],
            'decision_factors': []
        }
        
        if not evaluations:
            return guidance
        
        top_eval = evaluations[0]
        top_score = top_eval.get('overall_score', 0)
        
        # Primary recommendation
        if top_score > 85:
            guidance['primary_recommendation'] = "Strong recommendation - excellent match for requirements"
        elif top_score > 75:
            guidance['primary_recommendation'] = "Good recommendation - suitable for application"
        else:
            guidance['primary_recommendation'] = "Acceptable option - consider alternatives"
        
        # Alternative scenarios
        if len(evaluations) > 1:
            second_eval = evaluations[1]
            score_gap = top_score - second_eval.get('overall_score', 0)
            
            if score_gap < 5:
                guidance['alternative_scenarios'].append("Very close competition - either pump suitable")
            
            # Check for cost considerations
            top_cost = top_eval.get('lifecycle_cost', {}).get('total_10_year_cost', 0)
            second_cost = second_eval.get('lifecycle_cost', {}).get('total_10_year_cost', 0)
            
            if second_cost > 0 and second_cost < top_cost * 0.9:
                guidance['alternative_scenarios'].append("Consider alternative for lower operating costs")
        
        # Decision factors
        top_eff = top_eval.get('operating_point', {}).get('efficiency_pct', 0)
        if top_eff > 85:
            guidance['decision_factors'].append("High efficiency supports energy cost savings")
        
        if top_eval.get('vfd_analysis', {}).get('vfd_recommended', False):
            guidance['decision_factors'].append("VFD compatibility offers additional energy savings")
        
        return guidance
    
    def _analyze_trade_offs(self, evaluations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Analyze trade-offs between different pump options"""
        trade_offs = []
        
        if len(evaluations) < 2:
            return trade_offs
        
        for i in range(min(2, len(evaluations) - 1)):
            current = evaluations[i]
            next_option = evaluations[i + 1]
            
            trade_off = {
                'comparison': f"Option {i + 1} vs Option {i + 2}",
                'higher_performance': '',
                'lower_cost': '',
                'recommendation': ''
            }
            
            # Performance comparison
            current_eff = current.get('operating_point', {}).get('efficiency_pct', 0)
            next_eff = next_option.get('operating_point', {}).get('efficiency_pct', 0)
            
            if current_eff > next_eff:
                trade_off['higher_performance'] = f"Option {i + 1}: {current_eff:.1f}% efficiency"
            else:
                trade_off['higher_performance'] = f"Option {i + 2}: {next_eff:.1f}% efficiency"
            
            # Cost comparison
            current_cost = current.get('lifecycle_cost', {}).get('total_10_year_cost', 0)
            next_cost = next_option.get('lifecycle_cost', {}).get('total_10_year_cost', 0)
            
            if current_cost > 0 and next_cost > 0:
                if current_cost < next_cost:
                    trade_off['lower_cost'] = f"Option {i + 1}: £{current_cost:,.0f} total cost"
                else:
                    trade_off['lower_cost'] = f"Option {i + 2}: £{next_cost:,.0f} total cost"
            
            # Recommendation
            score_diff = current.get('overall_score', 0) - next_option.get('overall_score', 0)
            if score_diff > 10:
                trade_off['recommendation'] = f"Option {i + 1} clearly superior"
            elif score_diff < 5:
                trade_off['recommendation'] = "Close decision - consider specific priorities"
            else:
                trade_off['recommendation'] = f"Option {i + 1} preferred with moderate advantage"
            
            trade_offs.append(trade_off)
        
        return trade_offs
    
    def _identify_pump_advantages(self, evaluation: Dict[str, Any], rank: int) -> List[str]:
        """Identify specific advantages of a pump"""
        advantages = []
        
        operating_point = evaluation.get('operating_point', {})
        efficiency = operating_point.get('efficiency_pct', 0)
        
        if rank == 0:
            advantages.append("Top recommended choice")
        
        if efficiency > 85:
            advantages.append("Excellent efficiency performance")
        elif efficiency > 80:
            advantages.append("Very good efficiency")
        
        if evaluation.get('vfd_analysis', {}).get('vfd_recommended', False):
            advantages.append("VFD compatibility for energy savings")
        
        environmental = evaluation.get('environmental_impact', {})
        if environmental.get('efficiency_rating') == 'Excellent':
            advantages.append("Outstanding environmental performance")
        
        return advantages
    
    def _identify_pump_considerations(self, evaluation: Dict[str, Any], rank: int) -> List[str]:
        """Identify considerations or limitations of a pump"""
        considerations = []
        
        operating_point = evaluation.get('operating_point', {})
        efficiency = operating_point.get('efficiency_pct', 0)
        
        if rank > 0:
            considerations.append(f"Alternative option (rank {rank + 1})")
        
        if efficiency < 75:
            considerations.append("Lower efficiency may increase operating costs")
        
        lifecycle_cost = evaluation.get('lifecycle_cost', {})
        annual_cost = lifecycle_cost.get('annual_energy_cost', 0)
        if annual_cost > 10000:
            considerations.append("Higher annual energy costs")
        
        return considerations

# Global instance for use across the application
pump_comparator = PumpComparator()