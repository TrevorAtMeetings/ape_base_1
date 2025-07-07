"""
Project Management Module
Advanced project tracking and multi-selection management for pump projects
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pump_engine import ParsedPumpData, SiteRequirements

logger = logging.getLogger(__name__)

@dataclass
class ProjectSelection:
    """Individual pump selection within a project"""
    selection_id: str
    pump_code: str
    application_name: str
    flow_m3hr: float
    head_m: float
    efficiency_pct: float
    power_kw: float
    selection_date: str
    notes: Optional[str] = None
    status: str = "active"

@dataclass
class PumpProject:
    """Complete pump project with multiple selections"""
    project_id: str
    project_name: str
    customer_name: str
    contact_email: str
    created_date: str
    last_modified: str
    selections: List[ProjectSelection]
    project_status: str = "active"
    total_flow_m3hr: Optional[float] = None
    total_power_kw: Optional[float] = None
    estimated_cost: Optional[float] = None
    notes: Optional[str] = None

class ProjectManager:
    """Advanced project management for pump selections"""
    
    def __init__(self):
        self.projects_cache = {}
        self.selection_history = []
    
    def create_new_project(self, project_data: Dict[str, Any]) -> PumpProject:
        """Create a new pump project"""
        try:
            project_id = str(uuid.uuid4())[:8]
            current_time = datetime.now().isoformat()
            
            project = PumpProject(
                project_id=project_id,
                project_name=project_data.get('project_name', f'Project {project_id}'),
                customer_name=project_data.get('customer_name', ''),
                contact_email=project_data.get('contact_email', ''),
                created_date=current_time,
                last_modified=current_time,
                selections=[],
                project_status='active',
                notes=project_data.get('notes', '')
            )
            
            self.projects_cache[project_id] = project
            logger.info(f"Created new project: {project.project_name} (ID: {project_id})")
            
            return project
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise
    
    def add_selection_to_project(self, project_id: str, 
                                pump_evaluation: Dict[str, Any],
                                site_requirements: SiteRequirements,
                                application_name: str = "Main Application") -> bool:
        """Add a pump selection to an existing project"""
        try:
            if project_id not in self.projects_cache:
                logger.error(f"Project {project_id} not found")
                return False
            
            project = self.projects_cache[project_id]
            
            # Extract pump details
            operating_point = pump_evaluation.get('operating_point', {})
            selection_id = str(uuid.uuid4())[:8]
            
            selection = ProjectSelection(
                selection_id=selection_id,
                pump_code=pump_evaluation.get('pump_code', 'Unknown'),
                application_name=application_name,
                flow_m3hr=operating_point.get('flow_m3hr', site_requirements.flow_m3hr),
                head_m=operating_point.get('achieved_head_m', site_requirements.head_m),
                efficiency_pct=operating_point.get('efficiency_pct', 0),
                power_kw=operating_point.get('power_kw', 0),
                selection_date=datetime.now().isoformat(),
                notes=pump_evaluation.get('selection_reason', '')
            )
            
            project.selections.append(selection)
            project.last_modified = datetime.now().isoformat()
            
            # Update project totals
            self._update_project_totals(project)
            
            logger.info(f"Added selection {selection.pump_code} to project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding selection to project: {str(e)}")
            return False
    
    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Generate comprehensive project summary"""
        try:
            if project_id not in self.projects_cache:
                return {'error': 'Project not found'}
            
            project = self.projects_cache[project_id]
            
            summary = {
                'project_info': {
                    'project_id': project.project_id,
                    'project_name': project.project_name,
                    'customer_name': project.customer_name,
                    'created_date': project.created_date,
                    'last_modified': project.last_modified,
                    'status': project.project_status
                },
                'selection_overview': {
                    'total_selections': len(project.selections),
                    'total_flow_m3hr': project.total_flow_m3hr or 0,
                    'total_power_kw': project.total_power_kw or 0,
                    'estimated_cost': project.estimated_cost or 0
                },
                'selections': [self._format_selection_summary(sel) for sel in project.selections],
                'project_analysis': self._analyze_project(project),
                'recommendations': self._generate_project_recommendations(project)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating project summary: {str(e)}")
            return {'error': str(e)}
    
    def compare_project_options(self, project_id: str) -> Dict[str, Any]:
        """Compare different pump options within a project"""
        try:
            if project_id not in self.projects_cache:
                return {'error': 'Project not found'}
            
            project = self.projects_cache[project_id]
            
            if len(project.selections) < 2:
                return {'comparison_available': False, 'reason': 'Need at least 2 selections for comparison'}
            
            comparison = {
                'comparison_available': True,
                'selection_count': len(project.selections),
                'efficiency_comparison': self._compare_efficiencies(project.selections),
                'power_comparison': self._compare_power_consumption(project.selections),
                'cost_analysis': self._analyze_project_costs(project.selections),
                'optimization_suggestions': self._suggest_optimizations(project.selections)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing project options: {str(e)}")
            return {'error': str(e)}
    
    def generate_project_report(self, project_id: str) -> Dict[str, Any]:
        """Generate comprehensive project report data"""
        try:
            if project_id not in self.projects_cache:
                return {'error': 'Project not found'}
            
            project = self.projects_cache[project_id]
            
            report_data = {
                'project_header': {
                    'project_name': project.project_name,
                    'customer_name': project.customer_name,
                    'report_date': datetime.now().strftime('%Y-%m-%d'),
                    'project_id': project.project_id,
                    'total_selections': len(project.selections)
                },
                'executive_summary': self._generate_executive_summary(project),
                'selection_details': [self._format_detailed_selection(sel) for sel in project.selections],
                'project_totals': {
                    'total_flow': project.total_flow_m3hr or 0,
                    'total_power': project.total_power_kw or 0,
                    'estimated_annual_energy': self._calculate_annual_energy(project),
                    'estimated_annual_cost': self._calculate_annual_cost(project)
                },
                'recommendations': self._generate_project_recommendations(project),
                'next_steps': self._generate_next_steps(project)
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating project report: {str(e)}")
            return {'error': str(e)}
    
    def _update_project_totals(self, project: PumpProject):
        """Update project-level totals"""
        project.total_flow_m3hr = sum(sel.flow_m3hr for sel in project.selections)
        project.total_power_kw = sum(sel.power_kw for sel in project.selections)
        project.estimated_cost = self._estimate_total_cost(project.selections)
    
    def _estimate_total_cost(self, selections: List[ProjectSelection]) -> float:
        """Estimate total project cost"""
        base_cost = 1000  # Base cost per pump
        total_cost = 0
        
        for selection in selections:
            # Simple cost estimation based on power
            pump_cost = base_cost * (1 + selection.power_kw / 10)
            total_cost += pump_cost
        
        return round(total_cost, 2)
    
    def _format_selection_summary(self, selection: ProjectSelection) -> Dict[str, Any]:
        """Format selection for summary display"""
        return {
            'selection_id': selection.selection_id,
            'pump_code': selection.pump_code,
            'application': selection.application_name,
            'flow_m3hr': selection.flow_m3hr,
            'head_m': selection.head_m,
            'efficiency_pct': selection.efficiency_pct,
            'power_kw': selection.power_kw,
            'selection_date': selection.selection_date,
            'status': selection.status
        }
    
    def _analyze_project(self, project: PumpProject) -> Dict[str, Any]:
        """Analyze project characteristics"""
        if not project.selections:
            return {'analysis_available': False}
        
        efficiencies = [sel.efficiency_pct for sel in project.selections]
        powers = [sel.power_kw for sel in project.selections]
        
        analysis = {
            'analysis_available': True,
            'efficiency_stats': {
                'average': round(sum(efficiencies) / len(efficiencies), 1),
                'range': f"{min(efficiencies):.1f}% - {max(efficiencies):.1f}%",
                'best_performer': max(project.selections, key=lambda x: x.efficiency_pct).pump_code
            },
            'power_distribution': {
                'total_power': round(sum(powers), 2),
                'average_power': round(sum(powers) / len(powers), 2),
                'power_range': f"{min(powers):.1f} - {max(powers):.1f} kW"
            },
            'diversity_analysis': {
                'unique_pumps': len(set(sel.pump_code for sel in project.selections)),
                'applications': len(set(sel.application_name for sel in project.selections))
            }
        }
        
        return analysis
    
    def _generate_project_recommendations(self, project: PumpProject) -> List[str]:
        """Generate project-specific recommendations"""
        recommendations = []
        
        if not project.selections:
            return ["Add pump selections to generate recommendations"]
        
        # Efficiency recommendations
        avg_efficiency = sum(sel.efficiency_pct for sel in project.selections) / len(project.selections)
        if avg_efficiency > 85:
            recommendations.append("Excellent overall efficiency selection - well optimized project")
        elif avg_efficiency > 80:
            recommendations.append("Good efficiency performance across selections")
        else:
            recommendations.append("Consider reviewing pump selections for better efficiency")
        
        # Power optimization
        total_power = sum(sel.power_kw for sel in project.selections)
        if total_power > 100:
            recommendations.append("Consider VFD installation for energy savings on larger pumps")
        
        # Diversity recommendations
        unique_pumps = len(set(sel.pump_code for sel in project.selections))
        if unique_pumps < len(project.selections) / 2:
            recommendations.append("Good standardization - fewer pump types simplify maintenance")
        else:
            recommendations.append("Consider standardizing on fewer pump models for operational efficiency")
        
        return recommendations
    
    def _compare_efficiencies(self, selections: List[ProjectSelection]) -> Dict[str, Any]:
        """Compare efficiencies across selections"""
        efficiencies = [sel.efficiency_pct for sel in selections]
        
        return {
            'highest': max(efficiencies),
            'lowest': min(efficiencies),
            'average': round(sum(efficiencies) / len(efficiencies), 1),
            'variation': round(max(efficiencies) - min(efficiencies), 1),
            'best_performer': max(selections, key=lambda x: x.efficiency_pct).pump_code
        }
    
    def _compare_power_consumption(self, selections: List[ProjectSelection]) -> Dict[str, Any]:
        """Compare power consumption across selections"""
        powers = [sel.power_kw for sel in selections]
        
        return {
            'total_power': round(sum(powers), 2),
            'average_power': round(sum(powers) / len(powers), 2),
            'highest_consumer': max(selections, key=lambda x: x.power_kw).pump_code,
            'power_distribution': [{'pump': sel.pump_code, 'power': sel.power_kw} for sel in selections]
        }
    
    def _analyze_project_costs(self, selections: List[ProjectSelection]) -> Dict[str, Any]:
        """Analyze project costs"""
        energy_cost_per_kwh = 0.15
        operating_hours = 8760
        
        annual_energy_costs = []
        for selection in selections:
            annual_cost = selection.power_kw * operating_hours * energy_cost_per_kwh
            annual_energy_costs.append(annual_cost)
        
        return {
            'total_annual_energy_cost': round(sum(annual_energy_costs), 0),
            'average_cost_per_pump': round(sum(annual_energy_costs) / len(annual_energy_costs), 0),
            'cost_breakdown': [
                {'pump': sel.pump_code, 'annual_cost': round(cost, 0)}
                for sel, cost in zip(selections, annual_energy_costs)
            ]
        }
    
    def _suggest_optimizations(self, selections: List[ProjectSelection]) -> List[str]:
        """Suggest project optimizations"""
        suggestions = []
        
        # Check for low efficiency pumps
        low_efficiency = [sel for sel in selections if sel.efficiency_pct < 75]
        if low_efficiency:
            suggestions.append(f"Consider upgrading {len(low_efficiency)} pump(s) with efficiency below 75%")
        
        # Check for power imbalance
        powers = [sel.power_kw for sel in selections]
        if max(powers) > min(powers) * 3:
            suggestions.append("Significant power variation - consider load balancing opportunities")
        
        # Standardization opportunities
        pump_types = set(sel.pump_code.split('-')[0] for sel in selections)
        if len(pump_types) > len(selections) / 2:
            suggestions.append("Multiple pump series used - consider standardization benefits")
        
        return suggestions
    
    def _generate_executive_summary(self, project: PumpProject) -> Dict[str, str]:
        """Generate executive summary for project"""
        total_selections = len(project.selections)
        avg_efficiency = sum(sel.efficiency_pct for sel in project.selections) / total_selections if total_selections > 0 else 0
        
        return {
            'overview': f"Project includes {total_selections} pump selections with {avg_efficiency:.1f}% average efficiency",
            'performance': "Excellent" if avg_efficiency > 85 else "Good" if avg_efficiency > 80 else "Acceptable",
            'total_capacity': f"{project.total_flow_m3hr:.0f} m³/hr total flow capacity",
            'energy_profile': f"{project.total_power_kw:.1f} kW total power requirement"
        }
    
    def _format_detailed_selection(self, selection: ProjectSelection) -> Dict[str, Any]:
        """Format detailed selection information"""
        return {
            'pump_code': selection.pump_code,
            'application': selection.application_name,
            'performance': {
                'flow_m3hr': selection.flow_m3hr,
                'head_m': selection.head_m,
                'efficiency_pct': selection.efficiency_pct,
                'power_kw': selection.power_kw
            },
            'selection_info': {
                'date': selection.selection_date,
                'notes': selection.notes or "No additional notes",
                'status': selection.status
            }
        }
    
    def _calculate_annual_energy(self, project: PumpProject) -> float:
        """Calculate total annual energy consumption"""
        operating_hours = 8760
        total_annual_kwh = sum(sel.power_kw * operating_hours for sel in project.selections)
        return round(total_annual_kwh, 0)
    
    def _calculate_annual_cost(self, project: PumpProject) -> float:
        """Calculate total annual energy cost"""
        energy_cost_per_kwh = 0.15
        annual_energy = self._calculate_annual_energy(project)
        return round(annual_energy * energy_cost_per_kwh, 0)
    
    def _generate_next_steps(self, project: PumpProject) -> List[str]:
        """Generate next steps for project"""
        next_steps = [
            "Review and approve final pump selections",
            "Obtain detailed quotations from APE Pumps",
            "Schedule installation planning meeting",
            "Prepare site preparation requirements"
        ]
        
        if project.total_power_kw and project.total_power_kw > 50:
            next_steps.insert(1, "Consider VFD evaluation for energy optimization")
        
        return next_steps

# Global instance for use across the application
project_manager = ProjectManager()