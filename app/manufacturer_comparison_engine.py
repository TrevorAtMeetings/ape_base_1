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
                
                logger.info(f"[DATA DEBUG] Point {i+1}: Flow={flow}, Head={truth_head}, Eff={truth_efficiency}%, Power={truth_power}kW, Diameter={diameter}mm")
                logger.debug(f"Processing point {i+1}: Flow={flow}, Head={truth_head}, Diameter={diameter}")
                
                # Get Brain's prediction at this exact flow and head (datasheet validation)
                brain_result = self._get_brain_prediction(pump_data, flow, truth_head, diameter)
                
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
    
    def _get_brain_prediction(self, pump_data: Dict, flow: float, head: float, diameter: Optional[float] = None) -> Dict:
        """
        Get Brain prediction for a specific operating point
        
        Args:
            pump_data: Pump data dictionary
            flow: Flow rate in m³/hr
            head: Head in meters (manufacturer's datasheet value)
            diameter: Optional impeller diameter in mm (for reference only)
            
        Returns:
            Dictionary with Brain prediction results
        """
        try:
            pump_code = pump_data.get('pump_code', 'Unknown')
            
            # For datasheet validation, use the exact manufacturer's flow and head point
            # The Brain should calculate what efficiency and power it predicts at this exact operating point
            logger.debug(f"Getting Brain prediction for {pump_code} at exact datasheet point: {flow} m³/hr @ {head}m")
            
            # Use calculate_at_point_industry_standard which accepts flow AND head as inputs
            result = self.brain.performance.calculate_at_point_industry_standard(
                pump_data, flow, head
            )
            
            if result:
                # The head should match exactly what we input (datasheet validation principle)
                return {
                    'head': head,  # Use the exact manufacturer's head value
                    'efficiency': result.get('efficiency_pct'),
                    'power': result.get('power_kw'),
                    'diameter_used': result.get('impeller_diameter_mm', diameter),
                    'errors': result.get('errors', [])
                }
            else:
                return {
                    'head': head,  # Still return the manufacturer's head for comparison
                    'efficiency': None,
                    'power': None,
                    'diameter_used': diameter,
                    'errors': ['Brain calculation failed - pump may not be suitable for this operating point']
                }
            
        except Exception as e:
            logger.error(f"Brain prediction failed: {e}")
            return {
                'head': head,  # Still return the manufacturer's head for comparison
                'efficiency': None, 
                'power': None,
                'diameter_used': diameter,
                'errors': [f"Brain prediction error: {str(e)}"]
            }
    
    def _generate_chart_data(self, comparison_points: List[Dict]) -> Dict:
        """Generate comprehensive bar chart data for all performance metrics"""
        
        # Prepare data for grouped bar chart
        point_labels = []
        truth_heads = []
        brain_heads = []
        truth_efficiencies = []
        brain_efficiencies = []
        truth_powers = []
        brain_powers = []
        
        for i, point in enumerate(comparison_points):
            if point.get('flow'):
                point_labels.append(f"Point {i+1}<br>{point['flow']:.1f} m³/hr")
                truth_heads.append(point.get('truth_head', 0))
                brain_heads.append(point.get('brain_head', 0))
                truth_efficiencies.append(point.get('truth_efficiency', 0))
                brain_efficiencies.append(point.get('brain_efficiency', 0))
                truth_powers.append(point.get('truth_power', 0))
                brain_powers.append(point.get('brain_power', 0))
        
        return {
            'point_labels': point_labels,
            'truth_heads': truth_heads,
            'brain_heads': brain_heads,
            'truth_efficiencies': truth_efficiencies,
            'brain_efficiencies': brain_efficiencies,
            'truth_powers': truth_powers,
            'brain_powers': brain_powers
        }
    
    def _generate_ai_summary(self, comparison_points: List[Dict], pump_data: Dict) -> str:
        """Generate comprehensive engineering analysis using AI for troubleshooting guidance"""
        
        try:
            # Calculate detailed statistics for all metrics
            valid_points = [p for p in comparison_points if p.get('head_delta') is not None]
            
            if not valid_points:
                return "No valid comparison points available for analysis."
            
            # Prepare detailed analysis data for AI
            pump_code = pump_data.get('pump_code', 'Unknown')
            bep_flow = pump_data.get('bep_flow_m3hr', 0)
            bep_head = pump_data.get('bep_head_m', 0)
            
            analysis_data = {
                'pump_model': pump_code,
                'bep_conditions': f"{bep_flow:.0f} m³/hr @ {bep_head:.1f}m",
                'test_points': []
            }
            
            for point in comparison_points:
                test_point = {
                    'flow': point.get('flow', 0),
                    'truth_head': point.get('truth_head', 0),
                    'brain_head': point.get('brain_head', 0),
                    'truth_efficiency': point.get('truth_efficiency', 0),
                    'brain_efficiency': point.get('brain_efficiency', 0),
                    'truth_power': point.get('truth_power', 0),
                    'brain_power': point.get('brain_power', 0),
                    'head_error': point.get('head_delta', 0),
                    'efficiency_error': point.get('efficiency_delta', 0),
                    'power_error': point.get('power_delta', 0),
                    'diameter': point.get('diameter', 0)
                }
                analysis_data['test_points'].append(test_point)
            
            # Generate AI-powered engineering analysis
            return self._get_ai_engineering_analysis(analysis_data)
            
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            return f"Analysis generation error: {str(e)}"
    
    def _get_ai_engineering_analysis(self, analysis_data: Dict) -> str:
        """Generate AI-powered engineering analysis using OpenAI"""
        
        try:
            # Import OpenAI
            import openai
            import os
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Create detailed prompt for engineering analysis
            prompt = f"""As a senior pump engineer, analyze this calibration data and provide actionable troubleshooting guidance.

PUMP: {analysis_data['pump_model']}
BEP CONDITIONS: {analysis_data['bep_conditions']}

CALIBRATION DATA:"""

            for i, point in enumerate(analysis_data['test_points'], 1):
                prompt += f"""
Point {i} @ {point['flow']:.0f} m³/hr, Diameter {point['diameter']:.0f}mm:
- Head: Truth {point['truth_head']:.1f}m vs Brain {point['brain_head']:.1f}m (Δ{point['head_error']:+.1f}%)
- Efficiency: Truth {point['truth_efficiency']:.1f}% vs Brain {point['brain_efficiency']:.1f}% (Δ{point['efficiency_error']:+.1f}%)
- Power: Truth {point['truth_power']:.1f}kW vs Brain {point['brain_power']:.1f}kW (Δ{point['power_error']:+.1f}%)"""

            prompt += """

Provide a comprehensive engineering analysis including:
1. **Root Cause Analysis**: What physical factors might cause these deviations?
2. **Performance Assessment**: How do these errors impact pump operation?
3. **Manufacturing Tolerances**: Are deviations within expected ranges?
4. **Troubleshooting Actions**: Specific checks engineers should perform
5. **Operational Recommendations**: Adjustments or settings to optimize performance

Focus on actionable insights for pump engineers, not just statistics. Consider impeller wear, system conditions, calibration drift, and measurement accuracy."""

            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3  # Lower temperature for more focused technical analysis
            )
            
            # Handle potential None response from OpenAI
            ai_content = response.choices[0].message.content
            return ai_content if ai_content is not None else "AI analysis unavailable - empty response received"
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            # Fallback to enhanced manual analysis
            return self._generate_enhanced_manual_analysis(analysis_data)
    
    def _generate_enhanced_manual_analysis(self, analysis_data: Dict) -> str:
        """Generate enhanced manual analysis as fallback"""
        
        summary = f"🔧 **ENGINEERING ANALYSIS: {analysis_data['pump_model']}**\n"
        summary += f"BEP Design Point: {analysis_data['bep_conditions']}\n\n"
        
        for i, point in enumerate(analysis_data['test_points'], 1):
            summary += f"**Point {i} Analysis @ {point['flow']:.0f} m³/hr:**\n"
            
            # Head analysis
            if abs(point['head_error']) < 3:
                summary += f"✅ Head Prediction: Excellent match ({point['head_error']:+.1f}%)\n"
            elif abs(point['head_error']) < 8:
                summary += f"⚠️ Head Prediction: Acceptable deviation ({point['head_error']:+.1f}%)\n"
            else:
                summary += f"❌ Head Prediction: Significant deviation ({point['head_error']:+.1f}%) - Check impeller wear\n"
            
            # Efficiency analysis
            if abs(point['efficiency_error']) < 5:
                summary += f"✅ Efficiency Match: Good correlation ({point['efficiency_error']:+.1f}%)\n"
            elif abs(point['efficiency_error']) < 10:
                summary += f"⚠️ Efficiency: Moderate deviation ({point['efficiency_error']:+.1f}%) - Check clearances\n"
            else:
                summary += f"❌ Efficiency: Poor correlation ({point['efficiency_error']:+.1f}%) - Major wear suspected\n"
            
            # Power analysis
            if abs(point['power_error']) < 5:
                summary += f"✅ Power Calculation: Accurate prediction ({point['power_error']:+.1f}%)\n"
            else:
                summary += f"⚠️ Power Deviation: {point['power_error']:+.1f}% - Verify motor efficiency\n"
            
            summary += "\n"
        
        summary += "**🔍 RECOMMENDED ACTIONS:**\n"
        summary += "• Inspect impeller for wear patterns and damage\n"
        summary += "• Verify system operating conditions match design\n"
        summary += "• Check measurement instrument calibration\n"
        summary += "• Review pump installation and alignment\n"
        
        return summary