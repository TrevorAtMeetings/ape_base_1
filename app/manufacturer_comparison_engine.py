"""
Manufacturer Comparison Engine
Handles calibration analysis and comparison between ground truth data and Brain predictions
"""

import logging
from typing import Dict, List, Optional, Any
try:
    from .pump_brain import get_pump_brain
except ImportError:
    # Fallback for direct imports
    from pump_brain import get_pump_brain

logger = logging.getLogger(__name__)

class ManufacturerComparisonEngine:
    """Engine for comparing manufacturer ground truth data with Brain predictions"""
    
    def __init__(self):
        self.brain = get_pump_brain()
    
    def run_full_calibration(self, pump_data: Dict, ground_truth_points: List[Dict]) -> Dict:
        """
        Run complete calibration analysis for multiple performance points.
        
        Args:
            pump_data: Pump data dictionary from repository
            ground_truth_points: List of ground truth performance points
            
        Returns:
            Dictionary containing comparison results, chart data, and AI summary
        """
        logger.info(f"Running full calibration for {pump_data.get('pump_code', 'Unknown')} with {len(ground_truth_points)} points")
        
        comparison_points = []
        
        # Loop through each ground truth point
        for i, truth_point in enumerate(ground_truth_points):
            try:
                flow = truth_point['flow']
                truth_head = truth_point['head']
                truth_efficiency = truth_point['efficiency']
                truth_power = truth_point['power']
                diameter = truth_point.get('diameter')
                
                logger.debug(f"Processing point {i+1}: Flow={flow}, Head={truth_head}, Diameter={diameter}")
                
                # Get Brain's prediction at this exact flow
                brain_result = self._get_brain_prediction(pump_data, flow, diameter)
                
                # Calculate deltas
                row_data = {
                    'flow': flow,
                    'truth_head': truth_head,
                    'truth_efficiency': truth_efficiency,
                    'truth_power': truth_power,
                    'brain_head': brain_result.get('head'),
                    'brain_efficiency': brain_result.get('efficiency'),
                    'brain_power': brain_result.get('power'),
                    'diameter': diameter,
                    'errors': brain_result.get('errors', [])
                }
                
                # Calculate percentage deltas
                if brain_result.get('head'):
                    row_data['head_delta'] = ((brain_result['head'] - truth_head) / truth_head) * 100
                else:
                    row_data['head_delta'] = None
                    
                if brain_result.get('efficiency'):
                    row_data['efficiency_delta'] = ((brain_result['efficiency'] - truth_efficiency) / truth_efficiency) * 100
                else:
                    row_data['efficiency_delta'] = None
                    
                if brain_result.get('power'):
                    row_data['power_delta'] = ((brain_result['power'] - truth_power) / truth_power) * 100
                else:
                    row_data['power_delta'] = None
                
                comparison_points.append(row_data)
                
            except Exception as e:
                logger.error(f"Error processing ground truth point {i+1}: {e}")
                # Add error point to maintain indexing
                comparison_points.append({
                    'flow': truth_point.get('flow', 0),
                    'truth_head': truth_point.get('head', 0),
                    'truth_efficiency': truth_point.get('efficiency', 0),
                    'truth_power': truth_point.get('power', 0),
                    'brain_head': None,
                    'brain_efficiency': None,
                    'brain_power': None,
                    'head_delta': None,
                    'efficiency_delta': None,
                    'power_delta': None,
                    'errors': [f"Processing error: {str(e)}"]
                })
        
        # Generate chart data for Plotly
        chart_data = self._generate_chart_data(comparison_points)
        
        # Generate AI summary
        ai_summary = self._generate_ai_summary(comparison_points, pump_data)
        
        logger.info(f"Calibration complete: {len(comparison_points)} points processed")
        
        return {
            "comparison_points": comparison_points,
            "chart_data": chart_data,
            "ai_summary": ai_summary
        }
    
    def _get_brain_prediction(self, pump_data: Dict, flow: float, diameter: Optional[float] = None) -> Dict:
        """
        Get Brain prediction for a specific operating point
        
        Args:
            pump_data: Pump data dictionary
            flow: Flow rate in m³/hr
            diameter: Optional impeller diameter in mm
            
        Returns:
            Dictionary with Brain prediction results
        """
        try:
            pump_code = pump_data.get('pump_code', 'Unknown')
            
            # Use the Brain's performance engine to get prediction
            if diameter:
                # Force specific diameter constraint
                logger.debug(f"Getting Brain prediction for {pump_code} at {flow} m³/hr with forced diameter {diameter}mm")
                # Use the forced diameter approach in calculate_performance_at_flow
                result = self.brain.performance.calculate_performance_at_flow(
                    pump_data, flow, forced_diameter=diameter
                )
            else:
                # Let Brain choose optimal diameter using standard calculation
                logger.debug(f"Getting Brain prediction for {pump_code} at {flow} m³/hr (optimal diameter)")
                # Use the standard performance at flow calculation
                result = self.brain.performance.calculate_performance_at_flow(
                    pump_data, flow
                )
            
            if result:
                return {
                    'head': result.get('head_m'),
                    'efficiency': result.get('efficiency_pct'),
                    'power': result.get('power_kw'),
                    'diameter_used': result.get('diameter_mm'),
                    'errors': result.get('errors', [])
                }
            else:
                return {
                    'head': None,
                    'efficiency': None,
                    'power': None,
                    'diameter_used': None,
                    'errors': ['Brain calculation failed - no valid result']
                }
            
        except Exception as e:
            logger.error(f"Brain prediction failed: {e}")
            return {
                'head': None,
                'efficiency': None, 
                'power': None,
                'diameter_used': None,
                'errors': [f"Brain prediction error: {str(e)}"]
            }
    
    def _generate_chart_data(self, comparison_points: List[Dict]) -> Dict:
        """Generate data structure for Plotly chart overlay"""
        
        flows = []
        truth_heads = []
        brain_heads = []
        
        for point in comparison_points:
            if point.get('flow') and point.get('truth_head'):
                flows.append(point['flow'])
                truth_heads.append(point['truth_head'])
                brain_heads.append(point.get('brain_head') or 0)  # Use 0 for missing values
        
        return {
            'flows': flows,
            'truth_heads': truth_heads,
            'brain_heads': brain_heads
        }
    
    def _generate_ai_summary(self, comparison_points: List[Dict], pump_data: Dict) -> str:
        """Generate AI analysis summary of calibration results"""
        
        try:
            # Calculate summary statistics
            valid_points = [p for p in comparison_points if p.get('head_delta') is not None]
            
            if not valid_points:
                return "No valid comparison points available for analysis."
            
            head_deltas = [abs(p['head_delta']) for p in valid_points if p.get('head_delta') is not None]
            avg_head_error = sum(head_deltas) / len(head_deltas) if head_deltas else 0
            max_head_error = max(head_deltas) if head_deltas else 0
            
            # Count significant discrepancies
            major_discrepancies = len([d for d in head_deltas if d > 10])  # >10% difference
            minor_discrepancies = len([d for d in head_deltas if 5 < d <= 10])  # 5-10% difference
            
            # Generate summary text
            pump_code = pump_data.get('pump_code', 'Unknown')
            summary = f"""Calibration Analysis for {pump_code}

Performance Assessment:
• Analyzed {len(comparison_points)} performance points
• Average head prediction error: {avg_head_error:.1f}%
• Maximum head prediction error: {max_head_error:.1f}%

Discrepancy Breakdown:
• Major discrepancies (>10%): {major_discrepancies} points
• Minor discrepancies (5-10%): {minor_discrepancies} points
• Good matches (<5%): {len(valid_points) - major_discrepancies - minor_discrepancies} points

"""
            
            # Add recommendations
            if major_discrepancies > len(valid_points) * 0.5:
                summary += "\n⚠️  RECOMMENDATION: Significant systematic errors detected. Consider reviewing pump database accuracy or Brain calibration parameters."
            elif major_discrepancies > 0:
                summary += "\n📊 RECOMMENDATION: Some points show significant deviation. Review individual operating conditions and impeller diameters."
            else:
                summary += "\n✅ ASSESSMENT: Brain predictions show good correlation with ground truth data."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return f"Analysis summary unavailable due to processing error: {str(e)}"