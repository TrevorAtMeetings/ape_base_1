"""
Simplified AI Extractor for Pump Data Extraction
Uses a single configurable OpenAI model with a prompt from a text file
"""

import logging
import json
import base64
import os
import time
import traceback
from typing import Dict, Any, List, Optional
from openai import OpenAI
from PIL import Image
import io
import tempfile

from .config import AIConfig
from .pdf_to_image_converter import convert_pdf_to_images

logger = logging.getLogger(__name__)

class SimpleAIExtractor:
    """
    Simplified AI extractor using a single configurable OpenAI model
    """
    
    def __init__(self):
        self.config = AIConfig()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client with configuration"""
        try:
            api_key = self.config.get_api_key()
            self.client = OpenAI(api_key=api_key)
            logger.info(f"[Simple AI Extractor] Initialized with model: {self.config.MODEL_NAME}")
        except Exception as e:
            logger.error(f"[Simple AI Extractor] Failed to initialize client: {e}")
            raise
    
    def _load_prompt(self) -> str:
        """Load extraction prompt from text file"""
        try:
            with open(self.config.PROMPT_FILE_PATH, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
            logger.info(f"[Simple AI Extractor] Loaded prompt from {self.config.PROMPT_FILE_PATH}")
            return prompt
        except FileNotFoundError:
            logger.error(f"[Simple AI Extractor] Prompt file not found: {self.config.PROMPT_FILE_PATH}")
            raise
        except Exception as e:
            logger.error(f"[Simple AI Extractor] Failed to load prompt: {e}")
            raise
    
    def extract_pump_data(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract pump data from PDF using the configured AI model
        """
        start_time = time.time()
        
        try:
            logger.info(f"[Simple AI Extractor] Starting extraction for: {pdf_path}")
            
            # Convert PDF to images
            base64_images = convert_pdf_to_images(pdf_path)
            if not base64_images:
                raise ValueError("Failed to convert PDF to images")
            
            logger.info(f"[Simple AI Extractor] Converted PDF to {len(base64_images)} images")
            
            # Load extraction prompt
            prompt = self._load_prompt()
            logger.info(f"[Simple AI Extractor] Loaded prompt, length: {len(prompt)} characters")
            logger.info(f"[Simple AI Extractor] Prompt preview: {prompt[:200]}...")
            
            # Prepare content for API call
            content = [{"type": "text", "text": prompt}]
            
            # Add images to content
            for img_data in base64_images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_data}"
                    }
                })
            
            # Make API call
            logger.info(f"[Simple AI Extractor] Making API call to {self.config.MODEL_NAME}")
            logger.info(f"[Simple AI Extractor] Content length: {len(content)} items")
            logger.info(f"[Simple AI Extractor] Max tokens: {self.config.MAX_TOKENS}")
            logger.info(f"[Simple AI Extractor] Temperature: {self.config.TEMPERATURE}")
            
            response = self.client.chat.completions.create(
                model=self.config.MODEL_NAME,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.config.MAX_TOKENS,
                temperature=self.config.TEMPERATURE,
                timeout=self.config.TIMEOUT_SECONDS
            )
            
            # Extract response text
            response_text = response.choices[0].message.content.strip()
            logger.info(f"[Simple AI Extractor] API response received, length: {len(response_text)} characters")
            logger.info(f"[Simple AI Extractor] Response preview: {response_text[:200]}...")
            
            # Parse JSON response
            try:
                parsed_data = json.loads(response_text)
                processing_time = time.time() - start_time
                
                logger.info(f"[Simple AI Extractor] Extraction successful in {processing_time:.2f}s")
                
                # Validate and enhance data if enabled
                if self.config.ENABLE_VALIDATION:
                    parsed_data = self._validate_and_enhance_data(parsed_data)
                
                return parsed_data
                
            except json.JSONDecodeError as e:
                logger.error(f"[Simple AI Extractor] JSON parsing error: {e}")
                logger.error(f"[Simple AI Extractor] Raw response: {response_text[:500]}...")
                raise ValueError(f"AI returned invalid JSON: {e}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"[Simple AI Extractor] Extraction failed after {processing_time:.2f}s: {e}")
            logger.error(f"[Simple AI Extractor] Exception type: {type(e).__name__}")
            logger.error(f"[Simple AI Extractor] Full traceback: {traceback.format_exc()}")
            
            # Return fallback data if enabled
            if self.config.ENABLE_FALLBACK:
                logger.info("[Simple AI Extractor] Returning fallback data")
                return self._create_fallback_data()
            else:
                raise
    
    def _validate_and_enhance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance extracted data"""
        try:
            # Basic validation
            required_fields = ['pumpDetails', 'specifications', 'curves']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"[Simple AI Extractor] Missing required field: {field}")
                    data[field] = {}
            
            # Ensure curves is a list
            if not isinstance(data.get('curves', []), list):
                data['curves'] = []
            
            # Ensure specifications has required fields
            specs = data.get('specifications', {})
            if 'testSpeed' not in specs:
                specs['testSpeed'] = 0
            if 'maxFlow' not in specs:
                specs['maxFlow'] = 0
            if 'maxHead' not in specs:
                specs['maxHead'] = 0
            
            data['specifications'] = specs
            
            logger.info("[Simple AI Extractor] Data validation completed")
            return data
            
        except Exception as e:
            logger.error(f"[Simple AI Extractor] Data validation failed: {e}")
            return data
    
    def _create_fallback_data(self) -> Dict[str, Any]:
        """Create fallback data structure when extraction fails"""
        return {
            "pumpDetails": {
                "pumpModel": "Unknown",
                "manufacturer": "Unknown",
                "pumpType": "Unknown",
                "pumpRange": "Unknown",
                "application": "Unknown",
                "constructionStandard": "Unknown"
            },
            "technicalDetails": {
                "impellerType": "Unknown"
            },
            "specifications": {
                "testSpeed": 0,
                "maxFlow": 0,
                "maxHead": 0,
                "bepFlow": 0,
                "bepHead": 0,
                "npshrAtBep": 0,
                "minImpeller": 0,
                "maxImpeller": 0,
                "variableDiameter": False,
                "bepMarkers": []
            },
            "axisDefinitions": {
                "xAxis": {"min": 0, "max": 0, "unit": "m3/hr", "label": "Flow Rate"},
                "leftYAxis": {"min": 0, "max": 0, "unit": "m", "label": "Head"},
                "rightYAxis": {"min": 0, "max": 0, "unit": "%", "label": "Efficiency"},
                "secondaryRightYAxis": {"min": 0, "max": 0, "unit": "m", "label": "NPSH"}
            },
            "curves": [],
            "extractionStatus": "fallback",
            "errorMessage": "AI extraction failed, using fallback data"
        }

# Convenience function for backward compatibility
def extract_pump_data_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Main extraction function - simplified interface
    """
    extractor = SimpleAIExtractor()
    return extractor.extract_pump_data(pdf_path) 