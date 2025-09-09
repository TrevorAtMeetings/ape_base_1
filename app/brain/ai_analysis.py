"""
APE Pumps Brain System - AI Analysis Intelligence Module
========================================================
Handles AI-powered pump analysis, technical insights, and engineering recommendations.
Integrates with Brain system architecture for centralized intelligence.

Author: APE Pumps Engineering
Date: August 2025
Version: 1.0.0
"""

import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .config_manager import config

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Custom analysis error for when AI analysis cannot be generated"""
    pass


@dataclass
class AnalysisRequest:
    """Data structure for AI analysis requests"""
    pump_code: str
    flow_m3hr: float
    head_m: float
    efficiency_pct: float
    power_kw: float
    npshr_m: float
    application: str
    topic: str = 'general'


class AIAnalysisIntelligence:
    """AI-powered analysis intelligence for pump performance and selection insights"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        logger.info("Entering ai_analysis.py file")
        self.brain = brain
        
        # Check AI service availability
        self.openai_available = bool(os.getenv('OPENAI_API_KEY'))
        self.gemini_available = bool(os.getenv('GOOGLE_API_KEY'))
        self.ai_available = self.openai_available or self.gemini_available
        
        logger.info(f"AI Analysis Intelligence initialized - OpenAI: {'✓' if self.openai_available else '✗'}, Gemini: {'✓' if self.gemini_available else '✗'}")
    
    def generate_pump_analysis(self, request: AnalysisRequest) -> str:
        """
        Generate AI-powered pump analysis based on performance data and operating conditions.
        
        Args:
            request: Analysis request with pump parameters
            
        Returns:
            AI-generated analysis text
        """
        try:
            logger.debug(f"[AI Analysis] Generating {request.topic} analysis for {request.pump_code}")
            
            # Validate request - no fallbacks for invalid data
            if not request.pump_code or request.flow_m3hr <= config.get('ai_analysis', 'minimum_flow_threshold') or request.head_m <= config.get('ai_analysis', 'minimum_head_threshold'):
                raise AnalysisError(f"Invalid analysis parameters: pump_code={request.pump_code}, flow={request.flow_m3hr}, head={request.head_m}")
            
            # Generate analysis prompt based on topic
            prompt = self._create_analysis_prompt(request)
            
            if not self.ai_available:
                logger.error("AI services not available - analysis cannot be generated without proper API keys")
                raise AnalysisError("AI Analysis requires OpenAI or Google Gemini API key - no fallbacks available")
            
            # Use AI service for analysis
            ai_response = self._call_ai_service(prompt)
            
            if ai_response:
                logger.debug(f"[AI Analysis] Successfully generated {len(ai_response)} character analysis")
                return ai_response
            else:
                logger.error("AI service call failed and returned no response")
                raise AnalysisError("AI service failed to generate analysis - no fallbacks available")
                
        except AnalysisError:
            # Re-raise AnalysisError to maintain explicit error handling
            raise
        except Exception as e:
            logger.error(f"[AI Analysis] Error generating analysis: {str(e)}")
            raise AnalysisError(f"AI Analysis failed due to unexpected error: {str(e)}")
    
    def _create_analysis_prompt(self, request: AnalysisRequest) -> str:
        """Create context-specific analysis prompt"""
        
        base_context = f"""
        Pump: {request.pump_code}
        Operating Point: {request.flow_m3hr} m3/h @ {request.head_m}m
        Performance: {request.efficiency_pct}% efficiency, {request.power_kw} kW power
        NPSHr: {request.npshr_m}m
        Application: {request.application}
        """
        
        if request.topic == 'general':
            word_limit = config.get('ai_analysis', 'word_limit_for_general_analysis_responses')
            return f"""
            As a professional pump engineer, provide a comprehensive technical analysis for the following pump selection:
            
            {base_context}
            
            Analyze:
            1. Performance suitability for this duty point
            2. Energy efficiency assessment (compare to industry standards)
            3. Key engineering considerations and potential issues
            4. Operational recommendations and optimization opportunities
            
            Use professional engineering language, be concise (under {word_limit} words), and focus on actionable insights.
            """
            
        elif request.topic == 'efficiency':
            word_limit = config.get('ai_analysis', 'word_limit_for_efficiency_analysis_responses')
            return f"""
            As a pump efficiency expert, analyze the energy performance:
            
            {base_context}
            
            Focus on:
            1. Efficiency rating assessment against industry benchmarks
            2. Annual energy cost implications and ROI considerations
            3. Comparison to optimal efficiency ranges for this pump type
            4. Energy optimization recommendations
            
            Keep response focused and under {word_limit} words.
            """
            
        elif request.topic == 'application':
            word_limit = config.get('ai_analysis', 'word_limit_for_application_analysis_responses')
            return f"""
            As an application engineer, evaluate pump suitability:
            
            {base_context}
            
            Address:
            1. Application-specific suitability and compatibility
            2. Operating point assessment relative to pump BEP
            3. Reliability and maintenance considerations
            4. Installation and system integration recommendations
            
            Provide practical guidance in under {word_limit} words.
            """
            
        else:
            word_limit = config.get('ai_analysis', 'word_limit_for_other_topic_analysis_responses')
            return f"""
            Provide technical assessment for {request.topic} aspects of this pump selection:
            
            {base_context}
            
            Focus specifically on {request.topic} considerations and provide actionable engineering insights.
            Keep response under {word_limit} words.
            """
    
    def _call_ai_service(self, prompt: str) -> Optional[str]:
        """Call available AI service for analysis"""
        try:
            if self.openai_available:
                return self._call_openai(prompt)
            elif self.gemini_available:
                return self._call_gemini(prompt)
            else:
                return None
                
        except Exception as e:
            logger.error(f"[AI Analysis] AI service call failed: {str(e)}")
            return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI GPT for analysis"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model=config.get('ai_analysis', 'openai_model_for_ai_analysis'),
                messages=[
                    {"role": "system", "content": "You are a professional pump engineer with extensive experience in centrifugal pump selection and analysis. Provide clear, concise technical analysis using industry-standard terminology."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.get('ai_analysis', 'maximum_tokens_for_ai_response'),
                temperature=config.get('ai_analysis', 'temperature_setting_for_ai_model_consistency')
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"[AI Analysis] OpenAI call failed: {str(e)}")
            return None
    
    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Google Gemini for analysis"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            model = genai.GenerativeModel(config.get('ai_analysis', 'google_gemini_model_for_analysis'))
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"[AI Analysis] Gemini call failed: {str(e)}")
            return None
    
    def _generate_engineering_analysis(self, request: AnalysisRequest) -> str:
        """Generate engineering-based analysis when AI is unavailable"""
        
        # Efficiency assessment
        if request.efficiency_pct >= config.get('ai_analysis', 'excellent_efficiency_threshold'):
            efficiency_rating = "excellent"
            efficiency_note = "Operating at premium efficiency levels"
        elif request.efficiency_pct >= config.get('ai_analysis', 'good_efficiency_threshold'):
            efficiency_rating = "good"
            efficiency_note = "Above-average efficiency for this application"
        elif request.efficiency_pct >= config.get('ai_analysis', 'adequate_efficiency_threshold'):
            efficiency_rating = "adequate"
            efficiency_note = "Meets minimum efficiency requirements"
        else:
            efficiency_rating = "below optimal"
            efficiency_note = "Consider efficiency improvement opportunities"
        
        # Power assessment
        power_density = request.power_kw / request.flow_m3hr if request.flow_m3hr > config.get('ai_analysis', 'minimum_flow_threshold') else config.get('ai_analysis', 'default_power_density')
        
        # Power rating assessment
        acceptable_threshold = config.get('ai_analysis', 'power_density_threshold_for_acceptable_ranges_kw_per_m3hr')
        moderate_threshold = config.get('ai_analysis', 'power_density_threshold_for_moderate_ranges_kw_per_m3hr')
        power_rating = "within acceptable ranges" if power_density < acceptable_threshold else "moderate" if power_density < moderate_threshold else "high"
        
        # Application recommendations
        energy_threshold = config.get('ai_analysis', 'efficiency_threshold_for_energy_conscious_applications')
        standard_threshold = config.get('ai_analysis', 'efficiency_threshold_for_standard_applications')
        maintenance_threshold = config.get('ai_analysis', 'efficiency_threshold_for_maintenance_recommendations')
        
        app_recommendation = "Excellent choice for energy-conscious applications" if request.efficiency_pct >= energy_threshold else "Suitable for standard applications" if request.efficiency_pct >= standard_threshold else "Consider alternatives if efficiency is critical"
        maintenance_recommendation = "Regular maintenance recommended for optimal performance" if request.efficiency_pct < maintenance_threshold else "Standard maintenance schedule appropriate"
        
        power_density_str = f"{power_density:.2f}"
        analysis = f"""**Engineering Analysis - {request.pump_code}**

**Operating Conditions:** {request.flow_m3hr} m3/h @ {request.head_m}m

**Performance Assessment:**
- Efficiency: {request.efficiency_pct}% ({efficiency_rating})
- Power: {request.power_kw} kW
- NPSHr: {request.npshr_m}m
- {efficiency_note}

**Technical Evaluation:**
This pump demonstrates {efficiency_rating} performance characteristics for the specified duty point. The power density of {power_density_str} kW per cubic meter per hour is {power_rating} for this application type.

**Engineering Recommendations:**
- {app_recommendation}
- Monitor NPSH available vs required ({request.npshr_m}m) to prevent cavitation
- {maintenance_recommendation}

*Professional AI analysis available with API key configuration.*"""
        
        return analysis
    
    def _generate_fallback_analysis(self, request: AnalysisRequest, error_msg: str) -> str:
        """Generate basic fallback analysis when other methods fail"""
        return f"""**Analysis for {request.pump_code}**

**Operating Point:** {request.flow_m3hr} m3/h @ {request.head_m}m

**Performance Summary:**
- Efficiency: {request.efficiency_pct}%
- Power: {request.power_kw} kW
- NPSHr: {request.npshr_m}m

This pump meets the basic requirements for the specified {request.application} application.

*Note: {error_msg}*"""

    def convert_markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown text to HTML for display"""
        try:
            import markdown2
            return markdown2.markdown(markdown_text)
        except ImportError:
            # Fallback: Simple markdown-like conversion
            html = markdown_text.replace('\n\n', '</p><p>')
            html = html.replace('\n', '<br>')
            html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
            html = html.replace('*', '<em>', 1).replace('*', '</em>', 1)
            return f'<p>{html}</p>'