"""
AI Analyst Module for Brain System
===================================
Provides AI-powered insights for calibration analysis using OpenAI GPT-4o
"""

import logging
import json
import os
from typing import Dict, List, Any
from openai import OpenAI
from .config_manager import config

logger = logging.getLogger(__name__)

class AIAnalyst:
    """
    AI-powered analysis engine for pump calibration and performance insights
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = config.get('ai_analyst', 'openai_model_for_calibration_analysis')
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize OpenAI client with API key from environment"""
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.logger.info("AI Analyst initialized with OpenAI GPT-4o")
            else:
                self.logger.warning("OPENAI_API_KEY not found - AI insights will be limited")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            
    def generate_calibration_insights(self, comparison_data: Dict, metrics: Dict) -> List[str]:
        """
        Generate AI-powered insights about calibration results
        
        Args:
            comparison_data: Raw comparison points between manufacturer and Brain
            metrics: Statistical metrics from the comparison
            
        Returns:
            List of human-readable insights
        """
        if not self.client:
            # Fallback to rule-based insights if OpenAI is not available
            return self._generate_fallback_insights(metrics)
            
        try:
            # Prepare the prompt
            prompt = self._build_calibration_prompt(comparison_data, metrics)
            
            # Call OpenAI GPT-4o
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert pump engineer analyzing calibration data. 
                        Your role is to provide actionable insights about the Brain prediction system's accuracy.
                        Focus on:
                        1. Identifying patterns in the deviations
                        2. Suggesting specific calibration adjustments
                        3. Highlighting areas of excellence or concern
                        4. Providing recommendations for improving accuracy
                        
                        Keep insights concise, technical but accessible, and actionable.
                        Format your response as a JSON object with an 'insights' array containing strings."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=config.get('ai_analyst', 'lower_temperature_for_consistent_technical_analysis'),  # Lower temperature for more consistent technical analysis
                max_tokens=config.get('ai_analyst', 'maximum_tokens_for_calibration_insights')
            )
            
            # Parse the response
            content = response.choices[0].message.content
            if not content:
                self.logger.warning("Empty response from AI model")
                return self._generate_fallback_insights(metrics)
                
            result = json.loads(content)
            insights = result.get('insights', [])
            
            # Add calibration factor recommendations if significant deviations exist
            if metrics.get('efficiency', {}).get('mean_delta', 0) > 3:
                insights.append(self._suggest_calibration_factors(metrics))
                
            self.logger.info(f"Generated {len(insights)} AI insights for calibration analysis")
            return insights
            
        except Exception as e:
            self.logger.error(f"AI insight generation failed: {e}")
            return self._generate_fallback_insights(metrics)
            
    def _build_calibration_prompt(self, comparison_data: Dict, metrics: Dict) -> str:
        """Build a detailed prompt for GPT-4o analysis"""
        
        # Extract key information
        pump_code = comparison_data.get('pump_code', 'Unknown')
        points = comparison_data.get('comparison_points', [])
        
        prompt = f"""Analyze the following pump calibration data for {pump_code}:
        
        COMPARISON POINTS:
        """
        
        for point in points:
            prompt += f"""
        Flow: {point['flow']:.2f} m³/hr
        - Manufacturer Efficiency: {point['truth_efficiency']:.1f}%
        - Brain Efficiency: {point['brain_efficiency']:.1f}%
        - Delta: {point['delta_efficiency']:.1f}%
        - Manufacturer Power: {point['truth_power']:.2f} kW
        - Brain Power: {point['brain_power']:.2f} kW
        - Delta: {point['delta_power']:.1f}%
        """
        
        prompt += f"""
        
        STATISTICAL METRICS:
        - Overall Accuracy: {metrics.get('overall_accuracy', 0):.1f}%
        - Efficiency RMSE: {metrics.get('efficiency', {}).get('rmse', 0):.2f}%
        - Efficiency Mean Delta: {metrics.get('efficiency', {}).get('mean_delta', 0):.2f}%
        - Power RMSE: {metrics.get('power', {}).get('rmse', 0):.2f}%
        - Power Mean Delta: {metrics.get('power', {}).get('mean_delta', 0):.2f}%
        - Number of Points: {metrics.get('point_count', 0)}
        
        Please provide specific insights about:
        1. The pattern of deviations (systematic over/under prediction?)
        2. Flow-dependent accuracy variations
        3. Which physics parameters might need adjustment (be specific)
        4. Overall assessment of the Brain's predictive quality
        5. Specific calibration recommendations
        """
        
        return prompt
        
    def _suggest_calibration_factors(self, metrics: Dict) -> str:
        """Suggest specific calibration factor adjustments based on metrics"""
        
        eff_delta = metrics.get('efficiency', {}).get('mean_delta', 0)
        power_delta = metrics.get('power', {}).get('mean_delta', 0)
        
        suggestions = []
        
        if abs(eff_delta) > 3:
            direction = "increase" if eff_delta < 0 else "decrease"
            suggestions.append(f"Consider {direction} in efficiency_correction_exponent by ~{abs(eff_delta)/10:.3f}")
            
        if abs(power_delta) > 3:
            direction = "increase" if power_delta < 0 else "decrease"
            suggestions.append(f"Consider {direction} in power calculation factors")
            
        if suggestions:
            return f"Calibration Adjustment: {'; '.join(suggestions)}"
        else:
            return "Current calibration factors appear well-tuned"
            
    def _generate_fallback_insights(self, metrics: Dict) -> List[str]:
        """Generate rule-based insights when AI is not available"""
        insights = []
        
        # Overall accuracy assessment
        overall_acc = metrics.get('overall_accuracy', 0)
        if overall_acc >= 98:
            insights.append("Excellent accuracy: Brain predictions are highly reliable")
        elif overall_acc >= 95:
            insights.append("Good accuracy: Minor calibration may improve predictions")
        else:
            insights.append("Significant deviations detected: Calibration recommended")
            
        # Efficiency analysis
        eff_mean = metrics.get('efficiency', {}).get('mean_delta', 0)
        eff_rmse = metrics.get('efficiency', {}).get('rmse', 0)
        
        if abs(eff_mean) > 2:
            direction = "over-predicting" if eff_mean > 0 else "under-predicting"
            insights.append(f"Brain consistently {direction} efficiency by {abs(eff_mean):.1f}%")
            
        if eff_rmse > 5:
            insights.append(f"High efficiency variation (RMSE: {eff_rmse:.1f}%) suggests non-linear deviation")
            
        # Power analysis
        power_mean = metrics.get('power', {}).get('mean_delta', 0)
        power_rmse = metrics.get('power', {}).get('rmse', 0)
        
        if abs(power_mean) > 2:
            direction = "over-predicting" if power_mean > 0 else "under-predicting"
            insights.append(f"Brain consistently {direction} power by {abs(power_mean):.1f}%")
            
        if power_rmse > 5:
            insights.append(f"High power variation (RMSE: {power_rmse:.1f}%) may indicate model limitations")
            
        # Provide actionable recommendations
        if abs(eff_mean) > 5 or abs(power_mean) > 5:
            insights.append("Recommendation: Review physics model parameters for this pump type")
            
        return insights
        
    def analyze_pump_performance_trends(self, pump_code: str, historical_data: List[Dict]) -> Dict:
        """
        Analyze historical calibration trends for a specific pump
        
        Args:
            pump_code: Pump identifier
            historical_data: List of past calibration results
            
        Returns:
            Dict with trend analysis and recommendations
        """
        if not historical_data:
            return {"status": "No historical data available"}
            
        # Analyze accuracy trends over time
        accuracies = [d.get('overall_accuracy', 0) for d in historical_data]
        
        trend = {
            'improving': len([i for i in range(1, len(accuracies)) if accuracies[i] > accuracies[i-1]]),
            'declining': len([i for i in range(1, len(accuracies)) if accuracies[i] < accuracies[i-1]]),
            'average_accuracy': sum(accuracies) / len(accuracies) if accuracies else 0,
            'latest_accuracy': accuracies[-1] if accuracies else 0
        }
        
        if trend['improving'] > trend['declining']:
            trend['assessment'] = "Calibration quality is improving over time"
        elif trend['declining'] > trend['improving']:
            trend['assessment'] = "Calibration quality is declining - review recent changes"
        else:
            trend['assessment'] = "Calibration quality is stable"
            
        return trend
    
    def generate_pump_analysis(self, evaluation_result: Dict[str, Any], site_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-powered analysis for pump performance reports.
        
        Args:
            evaluation_result: Pump evaluation data
            site_data: Site requirements and conditions
            
        Returns:
            Dict containing analysis results and success status
        """
        try:
            if not self.client:
                self.logger.warning("OpenAI client not available - generating fallback analysis")
                return self._generate_fallback_pump_analysis(evaluation_result, site_data)
            
            # Build analysis prompt
            prompt = self._build_pump_analysis_prompt(evaluation_result, site_data)
            
            # Get AI analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert pump engineer providing technical analysis for pump selection reports. Provide clear, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.get('ai_analyst', 'maximum_tokens_for_calibration_insights'),
                temperature=config.get('ai_analyst', 'lower_temperature_for_consistent_technical_analysis')
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'analysis': analysis_text,
                'method': 'ai_generated'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI pump analysis: {e}")
            return self._generate_fallback_pump_analysis(evaluation_result, site_data)
    
    def _build_pump_analysis_prompt(self, evaluation_result: Dict[str, Any], site_data: Dict[str, Any]) -> str:
        """Build prompt for pump analysis AI request"""
        
        flow = site_data.get('flow_m3hr', 0)
        head = site_data.get('head_m', 0)
        efficiency = evaluation_result.get('efficiency_pct', 0)
        power = evaluation_result.get('power_kw', 0)
        qbp = evaluation_result.get('qbp_pct', 0)
        
        prompt = f"""Analyze this pump performance for a technical report:

Site Requirements:
- Flow Rate: {flow} m³/hr  
- Head: {head} m
- Application: Water pumping

Pump Performance:
- Efficiency: {efficiency}%
- Power Consumption: {power} kW
- QBP (Distance from BEP): {qbp}%

Please provide:
1. Performance Assessment (2-3 sentences)
2. Operating Characteristics (efficiency, power, BEP proximity)
3. Technical Recommendations for optimization

Keep response concise and engineering-focused."""

        return prompt
    
    def _generate_fallback_pump_analysis(self, evaluation_result: Dict[str, Any], site_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback analysis when AI is not available"""
        
        flow = site_data.get('flow_m3hr', 0)
        head = site_data.get('head_m', 0)  
        efficiency = evaluation_result.get('efficiency_pct', 0)
        qbp = evaluation_result.get('qbp_pct', 0)
        
        # Generate basic assessment
        if efficiency > 75:
            eff_assessment = "excellent efficiency"
        elif efficiency > 65:
            eff_assessment = "good efficiency"  
        elif efficiency > 55:
            eff_assessment = "acceptable efficiency"
        else:
            eff_assessment = "low efficiency"
            
        if qbp <= 110:
            bep_assessment = "operating close to Best Efficiency Point"
        elif qbp <= 130:
            bep_assessment = "operating reasonably close to BEP"
        else:
            bep_assessment = "operating away from optimal BEP"
            
        analysis = f"""Performance Assessment: This pump demonstrates {eff_assessment} ({efficiency}%) for the specified duty point of {flow} m³/hr at {head}m head.

Operating Characteristics: The pump is {bep_assessment} (QBP: {qbp}%), indicating {'optimal' if qbp <= 110 else 'acceptable' if qbp <= 130 else 'suboptimal'} hydraulic matching for this application.

Technical Recommendations: {'Continue with current selection - performance is well-suited for the application.' if efficiency > 65 and qbp <= 130 else 'Consider alternative pump sizes or impeller adjustments to improve efficiency and reduce operating costs.'}"""

        return {
            'success': True,
            'analysis': analysis,
            'method': 'fallback_generated'
        }