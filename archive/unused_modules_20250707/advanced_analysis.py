"""
Advanced Pump Analysis Module
Provides sophisticated analysis capabilities for pump selection
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
class LifecycleCostAnalysis:
    """Lifecycle cost analysis results"""
    initial_cost: float
    annual_energy_cost: float
    maintenance_cost: float
    total_10_year_cost: float
    cost_per_m3: float
    payback_period: Optional[float]

@dataclass
class EnvironmentalImpact:
    """Environmental impact assessment"""
    annual_co2_kg: float
    annual_kwh: float
    efficiency_rating: str
    carbon_footprint_score: int

class AdvancedPumpAnalyzer:
    """Advanced analysis capabilities for pump selection"""
    
    def __init__(self):
        # Energy cost assumptions (can be configured)
        self.energy_cost_per_kwh = 2.485  # R2.49 per kWh
        self.co2_per_kwh = 0.233  # kg CO2 per kWh (UK grid average)
        self.operating_hours_per_year = 8760  # 24/7 operation
        
    def calculate_lifecycle_cost(self, 
                               parsed_pump: ParsedPumpData,
                               operating_point: Dict[str, Any],
                               site_requirements: SiteRequirements,
                               pump_cost_estimate: Optional[float] = None) -> LifecycleCostAnalysis:
        """Calculate comprehensive lifecycle cost analysis"""
        try:
            # Extract operating parameters
            power_kw = operating_point.get('power_kw', 0)
            flow_m3hr = operating_point.get('flow_m3hr', 0)
            efficiency = operating_point.get('efficiency_pct', 0)
            
            # Estimate pump cost if not provided (based on size and complexity)
            if pump_cost_estimate is None:
                pump_cost_estimate = self._estimate_pump_cost(parsed_pump, power_kw)
            
            # Calculate annual energy consumption and cost
            annual_kwh = power_kw * self.operating_hours_per_year
            annual_energy_cost = annual_kwh * self.energy_cost_per_kwh
            
            # Estimate maintenance costs (3-5% of initial cost annually)
            annual_maintenance_cost = pump_cost_estimate * 0.04
            
            # Calculate 10-year total cost
            total_10_year_cost = (pump_cost_estimate + 
                                (annual_energy_cost * 10) + 
                                (annual_maintenance_cost * 10))
            
            # Cost per cubic meter pumped
            annual_volume_m3 = flow_m3hr * self.operating_hours_per_year
            cost_per_m3 = total_10_year_cost / (annual_volume_m3 * 10) if annual_volume_m3 > 0 else 0
            
            return LifecycleCostAnalysis(
                initial_cost=pump_cost_estimate,
                annual_energy_cost=annual_energy_cost,
                maintenance_cost=annual_maintenance_cost,
                total_10_year_cost=total_10_year_cost,
                cost_per_m3=cost_per_m3,
                payback_period=None  # Would need comparison pump for payback
            )
            
        except Exception as e:
            logger.error(f"Error calculating lifecycle cost: {str(e)}")
            return LifecycleCostAnalysis(0, 0, 0, 0, 0, None)
    
    def calculate_environmental_impact(self,
                                     operating_point: Dict[str, Any]) -> EnvironmentalImpact:
        """Calculate environmental impact assessment"""
        try:
            power_kw = operating_point.get('power_kw', 0)
            efficiency = operating_point.get('efficiency_pct', 0)
            
            # Annual energy consumption
            annual_kwh = power_kw * self.operating_hours_per_year
            
            # CO2 emissions
            annual_co2_kg = annual_kwh * self.co2_per_kwh
            
            # Efficiency rating
            if efficiency >= 85:
                efficiency_rating = "Excellent"
            elif efficiency >= 80:
                efficiency_rating = "Very Good"
            elif efficiency >= 75:
                efficiency_rating = "Good"
            elif efficiency >= 70:
                efficiency_rating = "Fair"
            else:
                efficiency_rating = "Poor"
            
            # Carbon footprint score (1-100, higher is better)
            carbon_footprint_score = min(100, max(1, int(efficiency * 1.2)))
            
            return EnvironmentalImpact(
                annual_co2_kg=annual_co2_kg,
                annual_kwh=annual_kwh,
                efficiency_rating=efficiency_rating,
                carbon_footprint_score=carbon_footprint_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating environmental impact: {str(e)}")
            return EnvironmentalImpact(0, 0, "Unknown", 0)
    
    def analyze_variable_speed_potential(self,
                                       parsed_pump: ParsedPumpData,
                                       site_requirements: SiteRequirements) -> Dict[str, Any]:
        """Analyze potential benefits of variable frequency drive"""
        try:
            analysis = {
                'vfd_recommended': False,
                'potential_savings_pct': 0,
                'reasons': [],
                'operating_scenarios': []
            }
            
            # Check if flow varies significantly
            required_flow = site_requirements.flow_m3hr
            
            # Simulate different flow scenarios (70%, 85%, 100%, 115% of design)
            flow_scenarios = [0.7, 0.85, 1.0, 1.15]
            scenario_data = []
            
            for factor in flow_scenarios:
                scenario_flow = required_flow * factor
                scenario_head = site_requirements.head_m * (factor ** 2)  # Affinity laws
                
                scenario_data.append({
                    'flow_factor': factor,
                    'flow_m3hr': scenario_flow,
                    'head_m': scenario_head,
                    'description': f"{int(factor * 100)}% design flow"
                })
            
            analysis['operating_scenarios'] = scenario_data
            
            # Basic VFD recommendation logic
            if hasattr(site_requirements, 'variable_demand') and site_requirements.variable_demand:
                analysis['vfd_recommended'] = True
                analysis['potential_savings_pct'] = 25  # Conservative estimate
                analysis['reasons'].append("Variable demand profile indicates VFD benefits")
            
            if required_flow > 100:  # Larger pumps benefit more from VFD
                analysis['potential_savings_pct'] = max(analysis['potential_savings_pct'], 20)
                analysis['reasons'].append("Large pump size suitable for VFD energy savings")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing VFD potential: {str(e)}")
            return {'vfd_recommended': False, 'potential_savings_pct': 0, 'reasons': [], 'operating_scenarios': []}
    
    def compare_pump_alternatives(self,
                                pump_evaluations: List[Dict[str, Any]],
                                parsed_pumps: List[ParsedPumpData]) -> Dict[str, Any]:
        """Generate detailed comparison between pump alternatives"""
        try:
            if len(pump_evaluations) < 2:
                return {'comparison_available': False, 'reason': 'Insufficient alternatives for comparison'}
            
            comparison = {
                'comparison_available': True,
                'pump_comparisons': [],
                'key_differentiators': [],
                'recommendations': []
            }
            
            # Compare top 3 pumps
            for i, evaluation in enumerate(pump_evaluations[:3]):
                pump_code = evaluation.get('pump_code', 'Unknown')
                operating_point = evaluation.get('operating_point', {})
                
                pump_comparison = {
                    'rank': i + 1,
                    'pump_code': pump_code,
                    'efficiency': operating_point.get('efficiency_pct', 0),
                    'power_consumption': operating_point.get('power_kw', 0),
                    'overall_score': evaluation.get('overall_score', 0),
                    'key_advantages': [],
                    'considerations': []
                }
                
                # Identify key advantages
                if i == 0:  # Top choice
                    pump_comparison['key_advantages'].append("Highest overall suitability score")
                
                efficiency = operating_point.get('efficiency_pct', 0)
                if efficiency >= 85:
                    pump_comparison['key_advantages'].append("Excellent efficiency performance")
                elif efficiency >= 80:
                    pump_comparison['key_advantages'].append("Very good efficiency")
                
                comparison['pump_comparisons'].append(pump_comparison)
            
            # Generate key differentiators
            if len(pump_evaluations) >= 2:
                top_pump = pump_evaluations[0]
                second_pump = pump_evaluations[1]
                
                score_diff = top_pump.get('overall_score', 0) - second_pump.get('overall_score', 0)
                if score_diff < 10:
                    comparison['key_differentiators'].append("Close competition between top alternatives")
                
                efficiency_diff = (top_pump.get('operating_point', {}).get('efficiency_pct', 0) - 
                                 second_pump.get('operating_point', {}).get('efficiency_pct', 0))
                if abs(efficiency_diff) > 5:
                    comparison['key_differentiators'].append(f"Significant efficiency difference ({efficiency_diff:.1f}%)")
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing pump alternatives: {str(e)}")
            return {'comparison_available': False, 'reason': 'Error during comparison analysis'}
    
    def _estimate_pump_cost(self, parsed_pump: ParsedPumpData, power_kw: float) -> float:
        """Estimate pump cost based on size and type"""
        try:
            # Basic cost estimation (would be replaced with actual pricing data)
            base_cost = 1000  # Base cost in currency units
            
            # Size factor based on power
            size_factor = 1 + (power_kw / 10)  # Larger pumps cost more
            
            # Type factor based on pump series
            type_multiplier = 1.0
            pump_type = getattr(parsed_pump, 'pump_type', '').upper()
            
            if 'HSC' in pump_type:
                type_multiplier = 1.3  # Split case pumps are more expensive
            elif 'CPE' in pump_type:
                type_multiplier = 1.5  # Chemical pumps cost more
            elif 'VSC' in pump_type:
                type_multiplier = 1.4  # Vertical pumps cost more
            
            estimated_cost = base_cost * size_factor * type_multiplier
            return round(estimated_cost, 2)
            
        except Exception as e:
            logger.error(f"Error estimating pump cost: {str(e)}")
            return 1000.0  # Default estimate

# Global instance for use across the application
advanced_analyzer = AdvancedPumpAnalyzer()