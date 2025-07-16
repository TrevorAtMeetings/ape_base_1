"""
AI Model Router
Smart routing system for OpenAI and Gemini model selection
"""

import os
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    AUTO = "auto"

@dataclass
class ModelPerformance:
    """Track model performance metrics"""
    success_rate: float
    average_processing_time: float
    average_accuracy_score: float
    cost_per_extraction: float
    total_extractions: int
    last_updated: float

@dataclass
class ExtractionRequest:
    """Request context for model selection"""
    file_size: int
    file_type: str
    user_preference: ModelProvider
    priority: str  # 'speed', 'accuracy', 'cost'
    batch_size: int = 1

class AIModelRouter:
    """
    Intelligent router for selecting between OpenAI and Gemini models
    """
    
    def __init__(self):
        self.performance_metrics = {
            ModelProvider.OPENAI: ModelPerformance(
                success_rate=0.95,
                average_processing_time=115.0,
                average_accuracy_score=0.92,
                cost_per_extraction=0.15,
                total_extractions=0,
                last_updated=time.time()
            ),
            ModelProvider.GEMINI: ModelPerformance(
                success_rate=0.88,
                average_processing_time=35.0,
                average_accuracy_score=0.85,
                cost_per_extraction=0.08,
                total_extractions=0,
                last_updated=time.time()
            ),
            ModelProvider.ANTHROPIC: ModelPerformance(
                success_rate=0.92,
                average_processing_time=45.0,
                average_accuracy_score=0.90,
                cost_per_extraction=0.12,
                total_extractions=0,
                last_updated=time.time()
            )
        }
        
        # Model availability status
        self.model_availability = {
            ModelProvider.OPENAI: self._check_openai_availability(),
            ModelProvider.GEMINI: self._check_gemini_availability(),
            ModelProvider.ANTHROPIC: self._check_anthropic_availability()
        }
        
        # Cost limits and quotas
        self.daily_cost_limit = float(os.getenv('AI_DAILY_COST_LIMIT', '50.0'))
        self.current_daily_cost = 0.0
        
    def select_model(self, request: ExtractionRequest) -> Tuple[ModelProvider, str]:
        """
        Select the best model based on request context and performance metrics
        """
        logger.info(f"[Model Router] Selecting model for request: {request}")
        
        # Handle explicit user preference
        if request.user_preference != ModelProvider.AUTO:
            if self.model_availability[request.user_preference]:
                return request.user_preference, f"User selected {request.user_preference.value}"
            else:
                logger.warning(f"[Model Router] {request.user_preference.value} not available, falling back to auto selection")
        
        # Smart routing based on priority
        if request.priority == 'speed':
            return self._select_for_speed(request)
        elif request.priority == 'accuracy':
            return self._select_for_accuracy(request)
        elif request.priority == 'cost':
            return self._select_for_cost(request)
        else:
            return self._select_balanced(request)
    
    def _select_for_speed(self, request: ExtractionRequest) -> Tuple[ModelProvider, str]:
        """Select model optimized for speed"""
        if not self.model_availability[ModelProvider.GEMINI]:
            return ModelProvider.OPENAI, "Gemini unavailable, using OpenAI"
        
        gemini_perf = self.performance_metrics[ModelProvider.GEMINI]
        openai_perf = self.performance_metrics[ModelProvider.OPENAI]
        
        if gemini_perf.average_processing_time < openai_perf.average_processing_time:
            return ModelProvider.GEMINI, f"Gemini is faster ({gemini_perf.average_processing_time:.1f}s vs {openai_perf.average_processing_time:.1f}s)"
        else:
            return ModelProvider.OPENAI, f"OpenAI is faster ({openai_perf.average_processing_time:.1f}s vs {gemini_perf.average_processing_time:.1f}s)"
    
    def _select_for_accuracy(self, request: ExtractionRequest) -> Tuple[ModelProvider, str]:
        """Select model optimized for accuracy"""
        if not self.model_availability[ModelProvider.OPENAI]:
            return ModelProvider.GEMINI, "OpenAI unavailable, using Gemini"
        
        gemini_perf = self.performance_metrics[ModelProvider.GEMINI]
        openai_perf = self.performance_metrics[ModelProvider.OPENAI]
        
        if openai_perf.average_accuracy_score > gemini_perf.average_accuracy_score:
            return ModelProvider.OPENAI, f"OpenAI is more accurate ({openai_perf.average_accuracy_score:.2f} vs {gemini_perf.average_accuracy_score:.2f})"
        else:
            return ModelProvider.GEMINI, f"Gemini is more accurate ({gemini_perf.average_accuracy_score:.2f} vs {openai_perf.average_accuracy_score:.2f})"
    
    def _select_for_cost(self, request: ExtractionRequest) -> Tuple[ModelProvider, str]:
        """Select model optimized for cost"""
        if not self.model_availability[ModelProvider.GEMINI]:
            return ModelProvider.OPENAI, "Gemini unavailable, using OpenAI"
        
        gemini_perf = self.performance_metrics[ModelProvider.GEMINI]
        openai_perf = self.performance_metrics[ModelProvider.OPENAI]
        
        if gemini_perf.cost_per_extraction < openai_perf.cost_per_extraction:
            return ModelProvider.GEMINI, f"Gemini is cheaper (${gemini_perf.cost_per_extraction:.3f} vs ${openai_perf.cost_per_extraction:.3f})"
        else:
            return ModelProvider.OPENAI, f"OpenAI is cheaper (${openai_perf.cost_per_extraction:.3f} vs ${gemini_perf.cost_per_extraction:.3f})"
    
    def _select_balanced(self, request: ExtractionRequest) -> Tuple[ModelProvider, str]:
        """Select model with balanced performance"""
        # Calculate composite score for each model
        scores = {}
        
        for provider in [ModelProvider.OPENAI, ModelProvider.GEMINI, ModelProvider.ANTHROPIC]:
            if not self.model_availability[provider]:
                continue
                
            perf = self.performance_metrics[provider]
            
            # Normalize metrics (0-1 scale)
            speed_score = 1.0 - (perf.average_processing_time / 200.0)  # Assume 200s max
            accuracy_score = perf.average_accuracy_score
            cost_score = 1.0 - (perf.cost_per_extraction / 0.30)  # Assume $0.30 max
            reliability_score = perf.success_rate
            
            # Weighted composite score
            composite_score = (
                speed_score * 0.25 +
                accuracy_score * 0.35 +
                cost_score * 0.20 +
                reliability_score * 0.20
            )
            
            scores[provider] = composite_score
        
        if not scores:
            return ModelProvider.OPENAI, "No models available, defaulting to OpenAI"
        
        best_provider = max(scores, key=scores.get)
        best_score = scores[best_provider]
        
        return best_provider, f"Best balanced performance (score: {best_score:.3f})"
    
    def _check_openai_availability(self) -> bool:
        """Check if OpenAI API is available"""
        try:
            import openai
            return bool(os.getenv('OPENAI_API_KEY'))
        except ImportError:
            return False
    
    def _check_gemini_availability(self) -> bool:
        """Check if Gemini API is available with multiple key support"""
        try:
            import google.generativeai as genai
            # Check for multiple Google API keys
            primary_key = os.getenv('GOOGLE_API_KEY')
            secondary_key = os.getenv('GOOGLE_API_KEY_2') 
            gemini_key = os.getenv('GEMINI_API_KEY')
            
            return bool(primary_key or secondary_key or gemini_key)
        except ImportError:
            return False
    
    def _check_anthropic_availability(self) -> bool:
        """Check if Anthropic API is available"""
        try:
            import anthropic
            return bool(os.getenv('ANTHROPIC_API_KEY'))
        except ImportError:
            return False
    
    def update_performance_metrics(self, provider: ModelProvider, success: bool, 
                                 processing_time: float, accuracy_score: float, 
                                 cost: float):
        """Update performance metrics based on extraction results"""
        perf = self.performance_metrics[provider]
        
        # Update success rate (moving average)
        perf.total_extractions += 1
        perf.success_rate = (perf.success_rate * (perf.total_extractions - 1) + 
                           (1.0 if success else 0.0)) / perf.total_extractions
        
        # Update processing time (moving average)
        perf.average_processing_time = (perf.average_processing_time * (perf.total_extractions - 1) + 
                                      processing_time) / perf.total_extractions
        
        # Update accuracy score (moving average)
        perf.average_accuracy_score = (perf.average_accuracy_score * (perf.total_extractions - 1) + 
                                     accuracy_score) / perf.total_extractions
        
        # Update cost (moving average)
        perf.cost_per_extraction = (perf.cost_per_extraction * (perf.total_extractions - 1) + 
                                  cost) / perf.total_extractions
        
        perf.last_updated = time.time()
        
        # Update daily cost tracking
        self.current_daily_cost += cost
        
        logger.info(f"[Model Router] Updated {provider.value} metrics: "
                   f"Success={perf.success_rate:.3f}, "
                   f"Time={perf.average_processing_time:.1f}s, "
                   f"Accuracy={perf.average_accuracy_score:.3f}, "
                   f"Cost=${perf.cost_per_extraction:.3f}")
    
    def get_model_comparison(self) -> Dict:
        """Get current model performance comparison"""
        return {
            "models": {
                provider.value: {
                    "available": self.model_availability[provider],
                    "success_rate": perf.success_rate,
                    "avg_time": perf.average_processing_time,
                    "accuracy": perf.average_accuracy_score,
                    "cost": perf.cost_per_extraction,
                    "total_runs": perf.total_extractions
                }
                for provider, perf in self.performance_metrics.items()
            },
            "daily_cost": self.current_daily_cost,
            "cost_limit": self.daily_cost_limit
        }
    
    def get_recommendation(self, request: ExtractionRequest) -> Dict:
        """Get model recommendation with detailed reasoning"""
        selected_model, reason = self.select_model(request)
        comparison = self.get_model_comparison()
        
        return {
            "recommended_model": selected_model.value,
            "reason": reason,
            "alternatives": [
                {
                    "model": provider.value,
                    "available": self.model_availability[provider],
                    "estimated_time": perf.average_processing_time,
                    "estimated_cost": perf.cost_per_extraction,
                    "accuracy_score": perf.average_accuracy_score
                }
                for provider, perf in self.performance_metrics.items()
                if provider != selected_model and self.model_availability[provider]
            ],
            "performance_comparison": comparison
        }

# Global router instance
_router_instance = None

def get_ai_model_router() -> AIModelRouter:
    """Get global AI model router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = AIModelRouter()
    return _router_instance