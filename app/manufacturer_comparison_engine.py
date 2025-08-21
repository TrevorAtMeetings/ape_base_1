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
            
            # Create detailed prompt for Brain logic analysis
            prompt = f"""As a pump selection algorithm expert, analyze the Brain's calculation accuracy compared to manufacturer datasheet values.

PUMP MODEL: {analysis_data['pump_model']}
PUMP BEP: {analysis_data['bep_conditions']}

CALIBRATION DATA (Manufacturer Truth vs Brain Predictions):"""

            for i, point in enumerate(analysis_data['test_points'], 1):
                prompt += f"""
Point {i} @ {point['flow']:.0f} m³/hr, Impeller {point['diameter']:.0f}mm:
- Head: Truth {point['truth_head']:.1f}m vs Brain {point['brain_head']:.1f}m (Δ{point['head_error']:+.1f}%)
- Efficiency: Truth {point['truth_efficiency']:.1f}% vs Brain {point['brain_efficiency']:.1f}% (Δ{point['efficiency_error']:+.1f}%)
- Power: Truth {point['truth_power']:.1f}kW vs Brain {point['brain_power']:.1f}kW (Δ{point['power_error']:+.1f}%)"""

            prompt += """

Analyze the Brain's calculation logic and identify potential algorithm improvements:

1. **Calculation Accuracy**: Which Brain calculations (head, efficiency, power) show the largest deviations and why?
2. **Physics Model Analysis**: Could the affinity law exponents need adjustment? Is the efficiency penalty formula appropriate for this pump type?
3. **Trim Logic Review**: Is the Brain correctly applying impeller trim calculations? Are the trim penalties too aggressive or too conservative?
4. **Calibration Factors**: Which tunable parameters (efficiency_penalty_diffuser, efficiency_penalty_volute, trim limits, etc.) might need adjustment?
5. **Algorithm Recommendations**: Specific improvements to the Brain's calculation methods to better match manufacturer data.

Focus ONLY on the Brain's algorithmic logic - DO NOT mention physical pump conditions, wear, damage, or maintenance. This is purely about improving the Brain's mathematical models."""

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
        
        summary = f"**BRAIN ALGORITHM ANALYSIS: {analysis_data['pump_model']}**\n"
        summary += f"Pump BEP: {analysis_data['bep_conditions']}\n\n"
        
        # Check if this is a diffuser or volute pump
        pump_type = "diffuser" if any(x in analysis_data['pump_model'].upper() for x in ['HC', 'XHC', 'TURBINE']) else "volute"
        
        for i, point in enumerate(analysis_data['test_points'], 1):
            summary += f"**Point {i} @ {point['flow']:.0f} m³/hr (Impeller {point['diameter']:.0f}mm):**\n"
            
            # Head calculation analysis
            if abs(point['head_error']) < 1:
                summary += f"✅ Head Calculation: Perfect match ({point['head_error']:+.1f}%)\n"
            elif abs(point['head_error']) < 5:
                summary += f"⚠️ Head Calculation: Minor deviation ({point['head_error']:+.1f}%) - Affinity law exponents may need tuning\n"
            else:
                summary += f"❌ Head Calculation: Large error ({point['head_error']:+.1f}%) - Review head affinity law calculations\n"
            
            # Efficiency calculation analysis
            if abs(point['efficiency_error']) < 3:
                summary += f"✅ Efficiency Model: Excellent accuracy ({point['efficiency_error']:+.1f}%)\n"
            elif abs(point['efficiency_error']) < 10:
                summary += f"⚠️ Efficiency Model: Acceptable ({point['efficiency_error']:+.1f}%) - "
                if pump_type == "diffuser":
                    summary += f"Diffuser penalty factor (0.45) may need adjustment\n"
                else:
                    summary += f"Volute penalty factor (0.20) may need adjustment\n"
            else:
                summary += f"❌ Efficiency Model: Poor accuracy ({point['efficiency_error']:+.1f}%) - "
                summary += f"Review trim penalty calculations for {pump_type} pumps\n"
            
            # Power calculation analysis
            if abs(point['power_error']) < 5:
                summary += f"✅ Power Formula: Accurate ({point['power_error']:+.1f}%)\n"
            elif abs(point['power_error']) < 15:
                summary += f"⚠️ Power Formula: Moderate error ({point['power_error']:+.1f}%) - Check power affinity law exponent\n"
            else:
                summary += f"❌ Power Formula: Large error ({point['power_error']:+.1f}%) - Review power calculation method\n"
            
            summary += "\n"
        
        summary += "**🔍 BRAIN ALGORITHM TUNING RECOMMENDATIONS:**\n"
        
        # Analyze overall patterns
        avg_eff_error = sum(abs(p['efficiency_error']) for p in analysis_data['test_points']) / len(analysis_data['test_points'])
        avg_power_error = sum(abs(p['power_error']) for p in analysis_data['test_points']) / len(analysis_data['test_points'])
        
        if avg_eff_error > 5:
            if pump_type == "diffuser":
                summary += f"• Adjust efficiency_penalty_diffuser factor (currently 0.45) - try {0.45 - avg_eff_error/100:.2f}\n"
            else:
                summary += f"• Adjust efficiency_penalty_volute factor (currently 0.20) - try {0.20 - avg_eff_error/100:.2f}\n"
        
        if avg_power_error > 10:
            summary += "• Review power calculation: Ensure using actual operating head, not pump capability\n"
            summary += "• Verify power affinity law exponent (typically 3.0 for centrifugal pumps)\n"
        
        summary += "• Consider pump-specific physics model exponents for this pump type\n"
        summary += "• Review BEP migration calculations for trimmed impellers\n"
        summary += "• Validate interpolation methods used for curve data\n"
        
        return summary