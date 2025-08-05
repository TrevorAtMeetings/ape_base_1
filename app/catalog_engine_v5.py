"""
Enhanced Catalog Engine with v5 Pump Selection Methodology
==========================================================
This module integrates the v5 pump selection methodology directly into
the catalog engine, providing improved scoring and transparency.
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
from scipy import interpolate

from .catalog_engine import CatalogEngine
from .pump_selection_v5 import SelectionMethodology

logger = logging.getLogger(__name__)


class CatalogEngineV5(CatalogEngine):
    """Enhanced catalog engine with v5 selection methodology."""
    
    def __init__(self, repository):
        super().__init__(repository)
        self.selection_methodology = SelectionMethodology()
        
    def select_pumps_v5(self,
                       flow_m3hr: float,
                       head_m: float,
                       pump_type: Optional[str] = None,
                       npsha_m: Optional[float] = None,
                       specific_gravity: float = 1.0,
                       return_detailed_report: bool = True) -> Dict[str, Any]:
        """
        Select pumps using v5 methodology with enhanced scoring and transparency.
        
        Returns:
            Dictionary containing:
            - summary: Selection statistics
            - pump_comparisons: Top recommended pumps with scores
            - near_miss_pumps: Pumps that almost met criteria
            - exclusion_analysis: Breakdown of exclusion reasons
        """
        evaluations = []
        
        # Filter by pump type if specified
        pumps_to_evaluate = self.pumps
        if pump_type and pump_type != 'all':
            pumps_to_evaluate = [p for p in self.pumps if p.pump_type == pump_type]
            
        logger.info(f"V5 Selection: Evaluating {len(pumps_to_evaluate)} pumps for "
                   f"flow={flow_m3hr} m³/hr, head={head_m} m")
        
        # Pre-sort by BEP proximity for efficiency
        pumps_to_evaluate = self._sort_by_bep_proximity(pumps_to_evaluate, flow_m3hr)
        
        # Evaluate each pump
        for pump in pumps_to_evaluate:
            pump_data = {
                'pump_code': pump.pump_code,
                'performance_curves': pump.curves,
                'specifications': pump.specifications
            }
            
            evaluation = self.selection_methodology.evaluate_pump(
                pump_data, flow_m3hr, head_m, npsha_m
            )
            
            # Add pump metadata
            evaluation['pump_type'] = pump.pump_type
            evaluation['manufacturer'] = pump.manufacturer
            evaluation['series'] = pump.series
            
            evaluations.append(evaluation)
            
        # Generate comprehensive report
        report = self.selection_methodology.generate_selection_report(evaluations)
        
        # Convert to expected format for compatibility
        pump_comparisons = []
        for pump_eval in report['top_recommendations']:
            if pump_eval['performance']:
                pump_comparison = {
                    'pump_code': pump_eval['pump_code'],
                    'pump_type': pump_eval.get('pump_type', ''),
                    'overall_score': pump_eval['score'],
                    'score_breakdown': pump_eval['score_breakdown'],
                    'efficiency_at_duty': pump_eval['performance']['efficiency_pct'],
                    'power_kw': pump_eval['performance']['power_kw'],
                    'npshr_m': pump_eval['performance'].get('npshr_m', 0),
                    'head_at_duty': pump_eval['performance']['head_m'],
                    'sizing_method': pump_eval.get('solution_method', 'direct'),
                    'modification_details': pump_eval.get('modification_details', {})
                }
                
                # Add BEP analysis
                pump_comparison['bep_analysis'] = self._get_bep_analysis(
                    pump_eval, flow_m3hr
                )
                
                pump_comparisons.append(pump_comparison)
                
        result = {
            'pump_comparisons': pump_comparisons,
            'selection_summary': report['summary'],
            'near_miss_pumps': report.get('near_miss_pumps', []),
            'exclusion_analysis': report.get('exclusion_analysis', {}),
            'site_requirements': {
                'flow_m3hr': flow_m3hr,
                'head_m': head_m,
                'npsha_m': npsha_m,
                'specific_gravity': specific_gravity
            }
        }
        
        if return_detailed_report:
            result['detailed_evaluations'] = evaluations
            
        return result
        
    def _sort_by_bep_proximity(self, pumps: List, flow_m3hr: float) -> List:
        """Sort pumps by BEP proximity to target flow."""
        def get_bep_flow(pump):
            # Try to get BEP from specifications
            bep_flow = pump.specifications.get('q_bep', 0)
            
            if bep_flow <= 0 and pump.curves:
                # Estimate BEP from curves
                for curve in pump.curves:
                    points = curve.get('performance_points', [])
                    if points:
                        # Find point with highest efficiency
                        bep_point = max(points, key=lambda p: p.get('efficiency_pct', 0))
                        bep_flow = bep_point.get('flow_m3hr', 0)
                        if bep_flow > 0:
                            break
                            
            return abs(bep_flow - flow_m3hr) if bep_flow > 0 else float('inf')
            
        return sorted(pumps, key=get_bep_flow)
        
    def _get_bep_analysis(self, evaluation: Dict, flow_m3hr: float) -> Dict:
        """Get BEP analysis for pump comparison display."""
        score_breakdown = evaluation.get('score_breakdown', {})
        bep_score = score_breakdown.get('bep_score', 0)
        
        # Determine operating zone based on BEP score
        if bep_score >= 35:
            operating_zone = "Optimal Zone"
        elif bep_score >= 20:
            operating_zone = "Acceptable Zone"
        elif bep_score >= 10:
            operating_zone = "Marginal Zone"
        else:
            operating_zone = "Poor Zone"
            
        return {
            'bep_score': bep_score,
            'operating_zone': operating_zone,
            'bep_available': True,
            'on_right_side': True  # Simplified for now
        }
        
    def get_performance_at_duty_v5(self, pump: 'CatalogPump', 
                                  flow_m3hr: float, head_m: float) -> Optional[Dict]:
        """
        Get pump performance at duty point using v5 methodology.
        
        This method evaluates all possible solutions and returns the best one.
        """
        pump_data = {
            'pump_code': pump.pump_code,
            'performance_curves': pump.curves,
            'specifications': pump.specifications
        }
        
        evaluation = self.selection_methodology.evaluate_pump(
            pump_data, flow_m3hr, head_m
        )
        
        if evaluation['feasible'] and evaluation['performance']:
            return {
                'flow_m3hr': flow_m3hr,
                'head_m': evaluation['performance']['head_m'],
                'efficiency_pct': evaluation['performance']['efficiency_pct'],
                'power_kw': evaluation['performance']['power_kw'],
                'npshr_m': evaluation['performance'].get('npshr_m', 0),
                'sizing_method': evaluation.get('solution_method', 'direct'),
                'sizing_info': evaluation.get('modification_details', {}),
                'score': evaluation['score'],
                'score_breakdown': evaluation['score_breakdown']
            }
            
        return None