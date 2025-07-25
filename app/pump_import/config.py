"""
AI Configuration for Pump Data Extraction
Generic configuration file supporting multiple AI providers
"""

import os
from typing import Dict, Any

class AIConfig:
    """Generic configuration for AI model and extraction settings"""
    
    # Model Configuration - Generic and flexible
    MODEL_NAME = os.getenv('AI_MODEL_NAME', 'gpt-4o')
    API_KEY_ENV = os.getenv('AI_API_KEY_ENV', 'OPENAI_API_KEY')
    
    # Provider Configuration
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai').lower()
    
    # Extraction Settings
    MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '3500'))
    TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.1'))
    TIMEOUT_SECONDS = int(os.getenv('AI_TIMEOUT_SECONDS', '120'))
    
    # File Paths
    PROMPT_FILE_PATH = os.path.join(os.path.dirname(__file__), 'extraction_prompt.txt')
    
    # Validation Settings
    ENABLE_VALIDATION = os.getenv('AI_ENABLE_VALIDATION', 'true').lower() == 'true'
    ENABLE_FALLBACK = os.getenv('AI_ENABLE_FALLBACK', 'true').lower() == 'true'
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """Get model configuration dictionary"""
        return {
            'model_name': cls.MODEL_NAME,
            'api_key_env': cls.API_KEY_ENV,
            'provider': cls.AI_PROVIDER,
            'max_tokens': cls.MAX_TOKENS,
            'temperature': cls.TEMPERATURE,
            'timeout_seconds': cls.TIMEOUT_SECONDS
        }
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get API key from environment"""
        api_key = os.getenv(cls.API_KEY_ENV)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {cls.API_KEY_ENV}")
        return api_key
    
    @classmethod
    def get_provider_info(cls) -> Dict[str, str]:
        """Get provider information for client initialization"""
        return {
            'provider': cls.AI_PROVIDER,
            'model_name': cls.MODEL_NAME,
            'api_key_env': cls.API_KEY_ENV
        } 