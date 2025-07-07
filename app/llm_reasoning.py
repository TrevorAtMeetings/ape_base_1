"""
LLM-Powered Reasoning Module for APE Pumps Selection Application
Generates intelligent, context-aware explanations for pump selection decisions
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logger = logging.getLogger(__name__)

class PumpSelectionReasoning:
    """Generate intelligent pump selection explanations using LLM"""
    
    def __init__(self):
        """Initialize OpenAI and Google Gemini clients with API keys from environment"""
        self.openai_client = None
        self.gemini_model = None
        self.fallback_mode = False
        
        # Initialize OpenAI
        try:
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
        
        # Initialize Google Gemini
        try:
            gemini_key = os.environ.get('GOOGLE_API_KEY')
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Google Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini client: {e}")
        
        # Set fallback mode if no LLM is available
        if not self.openai_client and not self.gemini_model:
            logger.warning("No LLM providers available, using fallback reasoning")
            self.fallback_mode = True
        else:
            logger.info("LLM reasoning module initialized successfully")
    
    def generate_selection_reasoning(self, 
                                   pump_evaluation: Dict[str, Any],
                                   parsed_pump: Any,
                                   site_requirements: Any,
                                   rank: int = 1) -> str:
        """
        Generate intelligent reasoning for pump selection
        
        Args:
            pump_evaluation: Detailed pump evaluation data
            parsed_pump: ParsedPumpData object
            site_requirements: SiteRequirements object
            rank: Ranking position (1=top choice, 2=alternative, etc.)
            
        Returns:
            Natural language explanation of pump selection reasoning
        """
        if self.fallback_mode:
            return self._generate_fallback_reasoning(pump_evaluation, parsed_pump, rank)
        
        pump_data = self._prepare_pump_data(pump_evaluation, parsed_pump, site_requirements)
        prompt = self._create_reasoning_prompt(pump_data, rank)
        system_prompt = self._get_system_prompt()
        
        # Try OpenAI first
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                result = response.choices[0].message.content
                if result:
                    logger.debug(f"Generated OpenAI reasoning for {parsed_pump.pump_code}")
                    return result.strip()
                    
            except Exception as e:
                logger.error(f"OpenAI API failed: {e}")
        
        # Fallback to Google Gemini
        if self.gemini_model:
            try:
                full_prompt = f"{system_prompt}\n\n{prompt}"
                response = self.gemini_model.generate_content(full_prompt)
                
                if response.text:
                    logger.debug(f"Generated Gemini reasoning for {parsed_pump.pump_code}")
                    return response.text.strip()
                    
            except Exception as e:
                logger.error(f"Google Gemini API failed: {e}")
        
        # Final fallback to template-based reasoning
        return self._generate_fallback_reasoning(pump_evaluation, parsed_pump, rank)
    
    def generate_technical_analysis(self,
                                  pump_evaluation: Dict[str, Any],
                                  parsed_pump: Any) -> Dict[str, str]:
        """
        Generate detailed technical analysis sections
        
        Returns:
            Dictionary with analysis sections: bep_explanation, npsh_explanation, power_explanation
        """
        if self.fallback_mode:
            return self._generate_fallback_analysis(pump_evaluation)
        
        operating_point = pump_evaluation.get('operating_point', {})
        bep_analysis = pump_evaluation.get('bep_analysis', {})
        npsh_analysis = pump_evaluation.get('npsh_analysis', {})
        power_analysis = pump_evaluation.get('power_analysis', {})
        
        analyses = {}
        system_prompt = self._get_technical_system_prompt()
        
        # BEP Analysis
        if operating_point and bep_analysis:
            bep_prompt = self._create_bep_analysis_prompt(operating_point, bep_analysis)
            bep_result = self._call_llm_api(system_prompt, bep_prompt, 200)
            if bep_result:
                analyses['bep_explanation'] = bep_result
            
        # NPSH Analysis
        if operating_point and npsh_analysis:
            npsh_prompt = self._create_npsh_analysis_prompt(operating_point, npsh_analysis)
            npsh_result = self._call_llm_api(system_prompt, npsh_prompt, 200)
            if npsh_result:
                analyses['npsh_explanation'] = npsh_result
        
        # Power Analysis
        if operating_point and power_analysis:
            power_prompt = self._create_power_analysis_prompt(operating_point, power_analysis)
            power_result = self._call_llm_api(system_prompt, power_prompt, 200)
            if power_result:
                analyses['power_explanation'] = power_result
        
        # Return analyses or fallback if none generated
        return analyses if analyses else self._generate_fallback_analysis(pump_evaluation)
    
    def _call_llm_api(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> Optional[str]:
        """
        Call LLM API with fallback between OpenAI and Google Gemini
        
        Args:
            system_prompt: System instruction
            user_prompt: User prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if all APIs fail
        """
        # Try OpenAI first
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.6
                )
                
                result = response.choices[0].message.content
                if result:
                    return result.strip()
                    
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}")
        
        # Fallback to Google Gemini
        if self.gemini_model:
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = self.gemini_model.generate_content(full_prompt)
                
                if response.text:
                    return response.text.strip()
                    
            except Exception as e:
                logger.error(f"Google Gemini API call failed: {e}")
        
        return None
    
    def _get_system_prompt(self) -> str:
        """System prompt for pump selection reasoning"""
        return """You are an expert pump engineer providing clear, professional explanations for pump selection decisions. 
        
        Your explanations should:
        - Be technically accurate but accessible to engineers
        - Focus on practical benefits and implications
        - Mention specific performance values when relevant
        - Explain why this pump is suitable for the application
        - Keep explanations concise (2-3 sentences maximum)
        - Use professional engineering language
        
        Avoid:
        - Overly technical jargon without explanation
        - Generic statements without specific reasoning
        - Repetitive phrases
        - Marketing language"""
    
    def _get_technical_system_prompt(self) -> str:
        """System prompt for detailed technical analysis"""
        return """You are an expert pump engineer explaining technical performance aspects to other engineers.
        
        Provide clear, technical explanations that:
        - Explain the engineering significance of the data
        - Relate performance to practical implications
        - Use specific values and percentages when available
        - Focus on what the data means for pump operation
        - Keep explanations focused and informative (1-2 sentences)"""
    
    def _prepare_pump_data(self, evaluation: Dict[str, Any], parsed_pump: Any, site_requirements: Any) -> Dict[str, Any]:
        """Prepare structured pump data for LLM input"""
        operating_point = evaluation.get('operating_point', {})
        
        # Safely handle None site_requirements
        if site_requirements is None:
            required_flow = operating_point.get('flow_m3hr', 0)
            required_head = operating_point.get('head_m', 0)
            application_type = 'General'
            liquid_type = 'Water'
        else:
            required_flow = getattr(site_requirements, 'flow_m3hr', 0)
            required_head = getattr(site_requirements, 'head_m', 0)
            application_type = getattr(site_requirements, 'application_type', 'General')
            liquid_type = getattr(site_requirements, 'liquid_type', 'Water')
        
        return {
            'pump_code': parsed_pump.pump_code if parsed_pump else 'Unknown',
            'pump_series': getattr(parsed_pump, 'series', 'Unknown') if parsed_pump else 'Unknown',
            'pump_description': getattr(parsed_pump, 'model', 'Unknown') if parsed_pump else 'Unknown',
            'required_flow': required_flow or 0,
            'required_head': required_head or 0,
            'achieved_flow': operating_point.get('flow_m3hr', 0) or 0,
            'achieved_head': operating_point.get('head_m', 0) or 0,
            'achieved_efficiency': operating_point.get('efficiency_pct', 0) or 0,
            'achieved_power': operating_point.get('power_kw', 0) or 0,
            'npsh_required': operating_point.get('npshr_m', 0) or 0,
            'overall_score': evaluation.get('overall_score', 0),
            'extrapolated': operating_point.get('extrapolated', False),
            'application_type': application_type,
            'liquid_type': liquid_type
        }
    
    def _create_reasoning_prompt(self, pump_data: Dict[str, Any], rank: int) -> str:
        """Create reasoning prompt for LLM"""
        ranking_context = {
            1: "This is the top recommended pump for the application.",
            2: "This is a strong alternative pump option.",
            3: "This is an additional pump option to consider."
        }
        
        context = ranking_context.get(rank, "This pump is suitable for the application.")
        
        return f"""Analyze and explain why the {pump_data['pump_code']} ({pump_data['pump_series']}) is recommended for this application. {context}

Application Requirements:
- Flow Rate: {pump_data['required_flow']} m³/hr
- Head: {pump_data['required_head']} m
- Application: {pump_data['application_type']}
- Liquid: {pump_data['liquid_type']}

Actual Pump Performance:
- Achieved Flow: {pump_data['achieved_flow']} m³/hr
- Achieved Head: {pump_data['achieved_head']} m
- Operating Efficiency: {pump_data['achieved_efficiency']}%
- Power Consumption: {pump_data['achieved_power']} kW
- NPSH Required: {pump_data['npsh_required']} m
- Selection Score: {pump_data['overall_score']}/100
- Extrapolated Point: {'Yes' if pump_data['extrapolated'] else 'No'}

Provide a professional engineering explanation focusing on:
1. How well the pump meets the duty requirements
2. Efficiency and energy considerations
3. Any operational advantages or considerations
4. Why this pump ranks as choice #{rank}

Keep response concise (2-3 sentences) and technically accurate."""
    
    def _create_bep_analysis_prompt(self, operating_point: Dict[str, Any], bep_analysis: Dict[str, Any]) -> str:
        """Create BEP analysis prompt"""
        return f"""Explain the Best Efficiency Point (BEP) performance analysis:

Operating Efficiency: {operating_point.get('efficiency_pct', 0):.1f}%
BEP Analysis: {bep_analysis}

Explain what this efficiency performance means for pump operation and energy consumption."""
    
    def _create_npsh_analysis_prompt(self, operating_point: Dict[str, Any], npsh_analysis: Dict[str, Any]) -> str:
        """Create NPSH analysis prompt"""
        return f"""Explain the NPSH (Net Positive Suction Head) analysis:

NPSH Required: {operating_point.get('npshr_m', 0):.1f} m
NPSH Analysis: {npsh_analysis}

Explain what this NPSH requirement means for pump installation and cavitation prevention."""
    
    def _create_power_analysis_prompt(self, operating_point: Dict[str, Any], power_analysis: Dict[str, Any]) -> str:
        """Create power analysis prompt"""
        return f"""Explain the power consumption analysis:

Power Required: {operating_point.get('power_kw', 0):.1f} kW
Efficiency: {operating_point.get('efficiency_pct', 0):.1f}%
Power Analysis: {power_analysis}

Explain what this power consumption means for operating costs and energy efficiency."""
    
    def _generate_fallback_reasoning(self, evaluation: Dict[str, Any], parsed_pump: Any, rank: int) -> str:
        """Generate fallback reasoning when LLM is unavailable"""
        operating_point = evaluation.get('operating_point', {})
        efficiency = operating_point.get('efficiency_pct', 0)
        score = evaluation.get('overall_score', 0)
        
        ranking_phrases = {
            1: "top choice",
            2: "strong alternative", 
            3: "viable option"
        }
        
        phrase = ranking_phrases.get(rank, "suitable option")
        
        if efficiency > 80:
            efficiency_desc = "high efficiency"
        elif efficiency > 70:
            efficiency_desc = "good efficiency"
        else:
            efficiency_desc = "acceptable efficiency"
            
        return f"The {parsed_pump.pump_code} is a {phrase} with {efficiency_desc} of {efficiency:.1f}% at the operating point. This pump achieves a suitability score of {score}/100 for your requirements."
    
    def _generate_fallback_analysis(self, evaluation: Dict[str, Any]) -> Dict[str, str]:
        """Generate fallback technical analysis"""
        operating_point = evaluation.get('operating_point', {})
        
        return {
            'bep_explanation': f"Operating at {operating_point.get('efficiency_pct', 0):.1f}% efficiency.",
            'npsh_explanation': f"NPSH requirement of {operating_point.get('npshr_m', 0):.1f} m.",
            'power_explanation': f"Power consumption of {operating_point.get('power_kw', 0):.1f} kW."
        }

# Global instance
llm_reasoning = PumpSelectionReasoning()