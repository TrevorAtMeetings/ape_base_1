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
            
            # Create detailed prompt for Brain configuration analysis
            pump_type = "diffuser" if any(x in analysis_data['pump_model'].upper() for x in ['HC', 'XHC', 'TURBINE']) else "volute"
            
            prompt = f"""As a pump physics model calibration expert, analyze the Brain's accuracy and provide SPECIFIC configuration parameter adjustments.

PUMP MODEL: {analysis_data['pump_model']} (Type: {pump_type.upper()})
PUMP BEP: {analysis_data['bep_conditions']}

CALIBRATION DATA (Manufacturer Truth vs Brain Predictions):"""

            for i, point in enumerate(analysis_data['test_points'], 1):
                trim_ratio = point['diameter'] / 362.0 if pump_type == 'diffuser' else point['diameter'] / 500.0  # Approximate
                prompt += f"""
Point {i} @ {point['flow']:.0f} m³/hr, Impeller {point['diameter']:.0f}mm (Trim: {trim_ratio:.1%}):
- Head: Truth {point['truth_head']:.1f}m vs Brain {point['brain_head']:.1f}m (Δ{point['head_error']:+.1f}%)
- Efficiency: Truth {point['truth_efficiency']:.1f}% vs Brain {point['brain_efficiency']:.1f}% (Δ{point['efficiency_error']:+.1f}%)
- Power: Truth {point['truth_power']:.1f}kW vs Brain {point['brain_power']:.1f}kW (Δ{point['power_error']:+.1f}%)"""

            prompt += f"""

Analyze the deltas and provide SPECIFIC Brain configuration adjustments:

1. **TUNABLE PHYSICS ENGINE PARAMETERS** (in engineering_constants table):
   - bep_shift_flow_exponent: 1.0 (controls Q scaling) → Recommend adjustment?
   - bep_shift_head_exponent: 2.0 (controls H scaling) → Recommend adjustment?
   - efficiency_correction_exponent: 0.1 → Recommend adjustment?

2. **EFFICIENCY PENALTY FACTORS** (Current for {pump_type}):
   - efficiency_penalty_{pump_type}: {0.45 if pump_type == 'diffuser' else 0.20} → Based on errors, recommend new value?
   - trim_dependent_small_exponent: 2.9 → For minor trims (<10%)
   - trim_dependent_large_exponent: 2.1 → For major trims (>10%)

3. **CONFIGURATION MANAGEMENT ACTIONS**:
   Provide exact SQL commands for the engineering_constants table:
   Example: UPDATE engineering_constants SET value = '0.38' WHERE name = 'efficiency_penalty_diffuser';

4. **BRAIN LOGIC WORKBENCH SETTINGS**:
   - Navigate to: Admin → Brain Logic Workbench
   - Identify which pump family needs specific tuning
   - Consider creating pump-type-specific overrides

5. **EXPECTED OUTCOMES**:
   For each adjustment, specify:
   - Current error: {avg_eff_error:.1f}% efficiency, {avg_power_error:.1f}% power
   - Target accuracy: ±3% efficiency, ±5% power
   - Estimated improvement after configuration change

Provide ACTIONABLE configuration updates with exact values and SQL commands.
DO NOT mention physical pump conditions, wear, or maintenance - focus ONLY on Brain algorithm configuration."""

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
        """Generate enhanced manual analysis as fallback with specific configuration recommendations"""
        
        summary = f"**BRAIN CONFIGURATION ANALYSIS: {analysis_data['pump_model']}**\n"
        summary += f"Pump BEP: {analysis_data['bep_conditions']}\n\n"
        
        # Check if this is a diffuser or volute pump
        pump_type = "diffuser" if any(x in analysis_data['pump_model'].upper() for x in ['HC', 'XHC', 'TURBINE']) else "volute"
        current_eff_penalty = 0.45 if pump_type == "diffuser" else 0.20
        
        # Calculate average errors across all points
        if analysis_data['test_points']:
            avg_head_error = sum(abs(p['head_error']) for p in analysis_data['test_points']) / len(analysis_data['test_points'])
            avg_eff_error = sum(abs(p['efficiency_error']) for p in analysis_data['test_points']) / len(analysis_data['test_points'])
            avg_power_error = sum(abs(p['power_error']) for p in analysis_data['test_points']) / len(analysis_data['test_points'])
            max_eff_error = max(abs(p['efficiency_error']) for p in analysis_data['test_points'])
        else:
            avg_head_error = avg_eff_error = avg_power_error = max_eff_error = 0
        
        summary += f"**CALIBRATION SUMMARY ({pump_type.upper()} pump):**\n"
        summary += f"• Average Head Error: {avg_head_error:+.1f}%\n"
        summary += f"• Average Efficiency Error: {avg_eff_error:+.1f}%\n"  
        summary += f"• Average Power Error: {avg_power_error:+.1f}%\n\n"
        
        summary += "**🔧 SPECIFIC CONFIGURATION ADJUSTMENTS REQUIRED:**\n\n"
        
        # 1. Efficiency Penalty Adjustments
        summary += "**1. EFFICIENCY PENALTY FACTORS:**\n"
        if avg_eff_error > 3:
            # Calculate recommended adjustment
            adjustment_factor = avg_eff_error / 100
            new_penalty = current_eff_penalty - (adjustment_factor * 0.5)  # Conservative adjustment
            new_penalty = max(0.1, min(0.6, new_penalty))  # Keep within reasonable bounds
            
            summary += f"• CURRENT: efficiency_penalty_{pump_type} = {current_eff_penalty:.2f}\n"
            summary += f"• RECOMMENDED: efficiency_penalty_{pump_type} = {new_penalty:.2f}\n"
            summary += f"• SQL UPDATE: UPDATE engineering_constants SET value = '{new_penalty:.2f}' WHERE name = 'efficiency_penalty_{pump_type}';\n"
            summary += f"• EXPECTED IMPACT: Reduce efficiency error from {avg_eff_error:.1f}% to <3%\n\n"
        else:
            summary += f"• efficiency_penalty_{pump_type} = {current_eff_penalty:.2f} ✅ (No adjustment needed)\n\n"
        
        # 2. Affinity Law Exponents
        summary += "**2. AFFINITY LAW EXPONENTS:**\n"
        if avg_head_error > 2:
            # Recommend head exponent adjustment
            head_adjustment = 2.0 + (avg_head_error / 50)  # Small adjustment
            summary += f"• CURRENT: bep_shift_head_exponent = 2.0\n"
            summary += f"• RECOMMENDED: bep_shift_head_exponent = {head_adjustment:.2f}\n"
            summary += f"• SQL UPDATE: UPDATE engineering_constants SET value = '{head_adjustment:.2f}' WHERE name = 'bep_shift_head_exponent';\n\n"
        else:
            summary += "• bep_shift_head_exponent = 2.0 ✅ (No adjustment needed)\n\n"
        
        # 3. Power Calculation Review
        if avg_power_error > 5:
            summary += "**3. POWER CALCULATION ADJUSTMENTS:**\n"
            summary += "• ISSUE: Power calculation shows significant error\n"
            summary += "• VERIFY: Brain must use actual operating head, not pump capability\n"
            summary += "• CHECK: Power formula = (Flow × Head × 9.81) / (3600 × Efficiency × 0.97)\n"
            summary += "• RECOMMENDATION: Review power_affinity_exponent (should be 3.0)\n\n"
        
        # 4. Trim-Specific Adjustments
        summary += "**4. TRIM-DEPENDENT PARAMETERS:**\n"
        for point in analysis_data['test_points']:
            trim_pct = (1 - point['diameter'] / 362.0) * 100 if pump_type == 'diffuser' else (1 - point['diameter'] / 500.0) * 100
            if trim_pct > 10:  # Heavy trim
                summary += f"• Point @ {point['flow']:.0f} m³/hr has {trim_pct:.1f}% trim\n"
                if abs(point['efficiency_error']) > 5:
                    summary += f"  → Adjust trim_dependent_large_exponent (current: 2.1)\n"
                    summary += f"  → Consider pump-specific trim factor for {pump_type} pumps\n"
        
        summary += "\n**5. CONFIGURATION MANAGEMENT ACTIONS:**\n"
        summary += "• Navigate to: Admin → Brain Logic Workbench\n"
        summary += "• Update parameters in engineering_constants table\n"
        summary += "• Re-run calibration after adjustments\n"
        summary += "• Target accuracy: Head ±2%, Efficiency ±3%, Power ±5%\n"
        
        return summary