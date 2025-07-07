"""
System Curve Analysis Module
Advanced system curve modeling and optimization for pump selection
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import math
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pump_engine import ParsedPumpData, SiteRequirements

logger = logging.getLogger(__name__)

@dataclass
class SystemCurvePoint:
    """Single point on system curve"""
    flow_m3hr: float
    head_m: float
    power_kw: Optional[float] = None

@dataclass
class OperatingScenario:
    """Operating scenario with varying demands"""
    name: str
    flow_factor: float  # Multiplier of design flow
    hours_per_year: float
    description: str

class SystemCurveAnalyzer:
    """Advanced system curve analysis and optimization"""
    
    def __init__(self):
        # Standard operating scenarios
        self.standard_scenarios = [
            OperatingScenario("Peak Demand", 1.0, 2000, "Maximum design flow requirement"),
            OperatingScenario("Normal Operation", 0.85, 4000, "Typical daily operation"),
            OperatingScenario("Reduced Demand", 0.70, 2000, "Low demand periods"),
            OperatingScenario("Minimum Flow", 0.60, 760, "Minimum system requirements")
        ]
    
    def analyze_system_curve(self, site_requirements: SiteRequirements) -> Dict[str, Any]:
        """Generate comprehensive system curve analysis"""
        try:
            design_flow = site_requirements.flow_m3hr
            design_head = site_requirements.head_m
            
            # Generate system curve points
            system_curve = self._generate_system_curve(design_flow, design_head)
            
            # Analyze operating scenarios
            scenarios_analysis = self._analyze_operating_scenarios(design_flow, design_head)
            
            # Calculate system characteristics
            system_characteristics = self._calculate_system_characteristics(design_flow, design_head)
            
            analysis = {
                'system_curve_points': system_curve,
                'operating_scenarios': scenarios_analysis,
                'system_characteristics': system_characteristics,
                'optimization_opportunities': self._identify_optimization_opportunities(scenarios_analysis),
                'control_strategy_recommendations': self._recommend_control_strategies(scenarios_analysis)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in system curve analysis: {str(e)}")
            return {'error': str(e)}
    
    def optimize_pump_selection_for_scenarios(self, 
                                            parsed_pumps: List[ParsedPumpData],
                                            site_requirements: SiteRequirements) -> Dict[str, Any]:
        """Optimize pump selection considering multiple operating scenarios"""
        try:
            design_flow = site_requirements.flow_m3hr
            design_head = site_requirements.head_m
            
            optimization_results = {
                'scenario_analysis': {},
                'weighted_efficiency': {},
                'energy_analysis': {},
                'recommendations': []
            }
            
            # Analyze each pump across all scenarios
            for pump in parsed_pumps[:5]:  # Analyze top 5 pumps
                pump_analysis = self._analyze_pump_across_scenarios(pump, design_flow, design_head)
                optimization_results['scenario_analysis'][pump.pump_code] = pump_analysis
            
            # Calculate weighted efficiency for each pump
            optimization_results['weighted_efficiency'] = self._calculate_weighted_efficiency(
                optimization_results['scenario_analysis']
            )
            
            # Generate energy analysis
            optimization_results['energy_analysis'] = self._generate_energy_analysis(
                optimization_results['scenario_analysis']
            )
            
            # Generate recommendations
            optimization_results['recommendations'] = self._generate_scenario_recommendations(
                optimization_results
            )
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error in pump optimization: {str(e)}")
            return {'error': str(e)}
    
    def _generate_system_curve(self, design_flow: float, design_head: float) -> List[Dict[str, float]]:
        """Generate system curve points using quadratic relationship"""
        curve_points = []
        
        # Estimate static head (typically 60-80% of design head)
        static_head = design_head * 0.7
        dynamic_head = design_head - static_head
        
        # System curve: H = H_static + K * Q^2
        # Where K = dynamic_head / design_flow^2
        if design_flow > 0:
            k_factor = dynamic_head / (design_flow ** 2)
        else:
            k_factor = 0
        
        # Generate points from 0 to 120% of design flow
        flow_range = np.linspace(0, design_flow * 1.2, 13)
        
        for flow in flow_range:
            head = static_head + k_factor * (flow ** 2)
            curve_points.append({
                'flow_m3hr': round(flow, 1),
                'head_m': round(head, 2)
            })
        
        return curve_points
    
    def _analyze_operating_scenarios(self, design_flow: float, design_head: float) -> List[Dict[str, Any]]:
        """Analyze different operating scenarios"""
        scenarios = []
        
        for scenario in self.standard_scenarios:
            scenario_flow = design_flow * scenario.flow_factor
            # System curve relationship: head varies with square of flow
            scenario_head = design_head * (scenario.flow_factor ** 2) * 0.3 + design_head * 0.7
            
            scenario_data = {
                'name': scenario.name,
                'flow_m3hr': round(scenario_flow, 1),
                'head_m': round(scenario_head, 2),
                'flow_factor': scenario.flow_factor,
                'hours_per_year': scenario.hours_per_year,
                'description': scenario.description,
                'energy_percentage': round((scenario.hours_per_year / 8760) * 100, 1)
            }
            
            scenarios.append(scenario_data)
        
        return scenarios
    
    def _calculate_system_characteristics(self, design_flow: float, design_head: float) -> Dict[str, Any]:
        """Calculate key system characteristics"""
        # Estimate static and dynamic head components
        static_head = design_head * 0.7
        dynamic_head = design_head * 0.3
        
        characteristics = {
            'estimated_static_head': round(static_head, 2),
            'estimated_dynamic_head': round(dynamic_head, 2),
            'static_head_percentage': round((static_head / design_head) * 100, 1),
            'system_type': self._classify_system_type(static_head / design_head),
            'control_suitability': self._assess_control_suitability(static_head / design_head),
            'variable_demand_potential': self._assess_variable_demand_potential(design_flow)
        }
        
        return characteristics
    
    def _classify_system_type(self, static_ratio: float) -> str:
        """Classify system type based on static head ratio"""
        if static_ratio > 0.8:
            return "High static head system"
        elif static_ratio > 0.5:
            return "Mixed static/dynamic system"
        else:
            return "Dynamic head dominated system"
    
    def _assess_control_suitability(self, static_ratio: float) -> Dict[str, Any]:
        """Assess suitability for different control methods"""
        suitability = {
            'vfd_effectiveness': 'High' if static_ratio < 0.6 else 'Medium' if static_ratio < 0.8 else 'Low',
            'throttle_valve_efficiency': 'Low' if static_ratio < 0.3 else 'Medium',
            'bypass_control_feasibility': 'High' if static_ratio > 0.7 else 'Medium',
            'recommended_control': 'VFD' if static_ratio < 0.6 else 'Throttle valve with VFD'
        }
        
        return suitability
    
    def _assess_variable_demand_potential(self, design_flow: float) -> Dict[str, Any]:
        """Assess potential for variable demand optimization"""
        potential = {
            'energy_savings_potential': 'High' if design_flow > 100 else 'Medium' if design_flow > 50 else 'Low',
            'vfd_payback_estimate': '1-2 years' if design_flow > 200 else '2-3 years' if design_flow > 100 else '3-5 years',
            'recommended_analysis': 'Detailed VFD study recommended' if design_flow > 100 else 'Basic VFD analysis sufficient'
        }
        
        return potential
    
    def _analyze_pump_across_scenarios(self, pump: ParsedPumpData, 
                                     design_flow: float, design_head: float) -> Dict[str, Any]:
        """Analyze pump performance across all operating scenarios"""
        scenario_results = []
        
        for scenario in self.standard_scenarios:
            scenario_flow = design_flow * scenario.flow_factor
            scenario_head = design_head * (scenario.flow_factor ** 2) * 0.3 + design_head * 0.7
            
            # Find best operating point for this scenario
            best_curve_idx = 0
            best_efficiency = 0
            operating_point = None
            
            for curve_idx, curve in enumerate(pump.performance_curves):
                # Interpolate at scenario flow
                if self._flow_in_range(scenario_flow, curve['flow_points']):
                    try:
                        head = np.interp(scenario_flow, curve['flow_points'], curve['head_points'])
                        efficiency = np.interp(scenario_flow, curve['flow_points'], curve['efficiency_points'])
                        
                        if efficiency > best_efficiency and abs(head - scenario_head) / scenario_head < 0.2:
                            best_efficiency = efficiency
                            best_curve_idx = curve_idx
                            operating_point = {
                                'efficiency': efficiency,
                                'head': head,
                                'power': self._calculate_power(scenario_flow, head, efficiency, pump.sg)
                            }
                    except:
                        continue
            
            scenario_result = {
                'scenario_name': scenario.name,
                'flow_m3hr': scenario_flow,
                'required_head_m': scenario_head,
                'hours_per_year': scenario.hours_per_year,
                'operating_point': operating_point,
                'curve_used': best_curve_idx,
                'performance_rating': self._rate_scenario_performance(operating_point, scenario_head)
            }
            
            scenario_results.append(scenario_result)
        
        return {
            'scenarios': scenario_results,
            'overall_rating': self._calculate_overall_rating(scenario_results)
        }
    
    def _flow_in_range(self, flow: float, flow_points: List[float]) -> bool:
        """Check if flow is within pump curve range"""
        return min(flow_points) <= flow <= max(flow_points)
    
    def _calculate_power(self, flow: float, head: float, efficiency: float, sg: float = 1.0) -> float:
        """Calculate power consumption"""
        if efficiency <= 0:
            return 0
        
        # Power = (Flow * Head * SG * 9.81) / (3600 * Efficiency/100)
        power_kw = (flow * head * sg * 9.81) / (3600 * (efficiency / 100))
        return round(power_kw, 2)
    
    def _rate_scenario_performance(self, operating_point: Optional[Dict], required_head: float) -> str:
        """Rate pump performance for a specific scenario"""
        if not operating_point:
            return "Unsuitable"
        
        efficiency = operating_point.get('efficiency', 0)
        head_delivered = operating_point.get('head', 0)
        head_margin = (head_delivered - required_head) / required_head
        
        if efficiency > 80 and 0 <= head_margin <= 0.2:
            return "Excellent"
        elif efficiency > 75 and 0 <= head_margin <= 0.3:
            return "Good"
        elif efficiency > 70 and -0.1 <= head_margin <= 0.4:
            return "Acceptable"
        else:
            return "Poor"
    
    def _calculate_overall_rating(self, scenario_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall rating across all scenarios"""
        total_weighted_efficiency = 0
        total_hours = 0
        performance_scores = {'Excellent': 4, 'Good': 3, 'Acceptable': 2, 'Poor': 1, 'Unsuitable': 0}
        total_score = 0
        
        for result in scenario_results:
            hours = result['hours_per_year']
            total_hours += hours
            
            if result['operating_point']:
                efficiency = result['operating_point']['efficiency']
                total_weighted_efficiency += efficiency * hours
                
                performance = result['performance_rating']
                total_score += performance_scores.get(performance, 0) * hours
        
        weighted_efficiency = total_weighted_efficiency / total_hours if total_hours > 0 else 0
        weighted_performance_score = total_score / total_hours if total_hours > 0 else 0
        
        return {
            'weighted_efficiency': round(weighted_efficiency, 1),
            'weighted_performance_score': round(weighted_performance_score, 2),
            'overall_suitability': self._score_to_suitability(weighted_performance_score)
        }
    
    def _score_to_suitability(self, score: float) -> str:
        """Convert numeric score to suitability rating"""
        if score >= 3.5:
            return "Excellent across all scenarios"
        elif score >= 2.5:
            return "Good overall performance"
        elif score >= 1.5:
            return "Acceptable with limitations"
        else:
            return "Not recommended for variable operation"
    
    def _calculate_weighted_efficiency(self, scenario_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate weighted efficiency for each pump"""
        weighted_efficiencies = {}
        
        for pump_code, analysis in scenario_analysis.items():
            overall_rating = analysis.get('overall_rating', {})
            weighted_efficiency = overall_rating.get('weighted_efficiency', 0)
            weighted_efficiencies[pump_code] = weighted_efficiency
        
        return weighted_efficiencies
    
    def _generate_energy_analysis(self, scenario_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive energy analysis"""
        energy_analysis = {
            'annual_energy_comparison': {},
            'cost_comparison': {},
            'best_energy_performer': None
        }
        
        energy_cost_per_kwh = 2.485  # R2.49 per kWh
        best_energy_consumption = float('inf')
        best_pump = None
        
        for pump_code, analysis in scenario_analysis.items():
            annual_energy = 0
            
            for scenario in analysis.get('scenarios', []):
                if scenario['operating_point']:
                    power = scenario['operating_point']['power']
                    hours = scenario['hours_per_year']
                    annual_energy += power * hours
            
            annual_cost = annual_energy * energy_cost_per_kwh
            
            energy_analysis['annual_energy_comparison'][pump_code] = {
                'annual_kwh': round(annual_energy, 0),
                'annual_cost_zar': round(annual_cost, 0)
            }
            
            if annual_energy < best_energy_consumption:
                best_energy_consumption = annual_energy
                best_pump = pump_code
        
        energy_analysis['best_energy_performer'] = best_pump
        return energy_analysis
    
    def _generate_scenario_recommendations(self, optimization_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on scenario analysis"""
        recommendations = []
        
        # Find best overall performer
        weighted_efficiencies = optimization_results.get('weighted_efficiency', {})
        if weighted_efficiencies:
            best_pump = max(weighted_efficiencies, key=weighted_efficiencies.get)
            best_efficiency = weighted_efficiencies[best_pump]
            recommendations.append(f"Recommend {best_pump} for best overall efficiency ({best_efficiency}%)")
        
        # Energy recommendations
        energy_analysis = optimization_results.get('energy_analysis', {})
        best_energy_pump = energy_analysis.get('best_energy_performer')
        if best_energy_pump:
            recommendations.append(f"Consider {best_energy_pump} for lowest energy consumption")
        
        # Control recommendations
        if any(eff > 80 for eff in weighted_efficiencies.values()):
            recommendations.append("VFD control recommended for energy optimization")
        
        recommendations.append("Consider multiple pump installation for very variable demands")
        
        return recommendations
    
    def _identify_optimization_opportunities(self, scenarios_analysis: List[Dict[str, Any]]) -> List[str]:
        """Identify optimization opportunities from scenario analysis"""
        opportunities = []
        
        # Check for significant flow variation
        flows = [scenario['flow_m3hr'] for scenario in scenarios_analysis]
        flow_variation = (max(flows) - min(flows)) / max(flows)
        
        if flow_variation > 0.4:
            opportunities.append("High flow variation indicates strong VFD benefits")
        
        # Check operating hours distribution
        peak_hours = next((s['hours_per_year'] for s in scenarios_analysis if s['name'] == 'Peak Demand'), 0)
        if peak_hours < 3000:
            opportunities.append("Limited peak operation supports pump downsizing consideration")
        
        opportunities.append("Multiple speed pump option should be evaluated")
        opportunities.append("Parallel pump configuration may offer better part-load efficiency")
        
        return opportunities
    
    def _recommend_control_strategies(self, scenarios_analysis: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Recommend control strategies based on operating patterns"""
        strategies = []
        
        # VFD strategy
        strategies.append({
            'strategy': 'Variable Frequency Drive (VFD)',
            'benefits': 'Excellent energy savings for variable flow applications',
            'suitability': 'High for dynamic head systems',
            'estimated_savings': '20-40% energy reduction'
        })
        
        # Throttle valve strategy
        strategies.append({
            'strategy': 'Throttle Valve Control',
            'benefits': 'Simple and reliable control method',
            'suitability': 'Suitable for systems with high static head',
            'estimated_savings': '5-15% compared to bypass control'
        })
        
        # Multiple pump strategy
        strategies.append({
            'strategy': 'Multiple Pump Configuration',
            'benefits': 'Excellent part-load efficiency and redundancy',
            'suitability': 'Ideal for highly variable demand profiles',
            'estimated_savings': '15-30% energy savings at part load'
        })
        
        return strategies

# Global instance for use across the application
system_curve_analyzer = SystemCurveAnalyzer()