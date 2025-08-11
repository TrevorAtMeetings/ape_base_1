"""
APE Pumps Brain System - Core Intelligence Module
==================================================
Centralized intelligence system for pump selection, performance analysis,
and visualization decisions. Single source of truth for all calculations.

Author: APE Pumps Engineering
Date: August 2025
Version: 1.0.0
"""

import os
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from functools import wraps
from datetime import datetime
import json

# Import sub-modules
from .brain.selection import SelectionIntelligence
from .brain.performance import PerformanceAnalyzer
from .brain.charts import ChartIntelligence
from .brain.validation import DataValidator
from .brain.cache import BrainCache
from .brain.ai_analysis import AIAnalysisIntelligence

# Configure logging
logger = logging.getLogger(__name__)

# Brain is now always active in production
BRAIN_MODE = 'active'  # Fixed to active mode


def measure_performance(func):
    """Decorator to measure and log performance of Brain operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            
            # Log if operation takes longer than threshold
            if elapsed > 100:
                logger.warning(f"Brain.{func.__name__} took {elapsed:.2f}ms")
            else:
                logger.debug(f"Brain.{func.__name__} completed in {elapsed:.2f}ms")
            
            # Store metrics for monitoring
            BrainMetrics.record_operation(func.__name__, elapsed)
            
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"Brain.{func.__name__} failed after {elapsed:.2f}ms: {str(e)}")
            BrainMetrics.record_error(func.__name__, str(e))
            raise
    return wrapper


class BrainMetrics:
    """Collect and store Brain performance metrics"""
    _metrics = {
        'operations': {},
        'errors': [],
        'discrepancies': []
    }
    
    @classmethod
    def record_operation(cls, operation: str, duration_ms: float):
        """Record operation performance"""
        if operation not in cls._metrics['operations']:
            cls._metrics['operations'][operation] = []
        cls._metrics['operations'][operation].append({
            'timestamp': datetime.now().isoformat(),
            'duration_ms': duration_ms
        })
        # Keep only last 1000 entries per operation
        if len(cls._metrics['operations'][operation]) > 1000:
            cls._metrics['operations'][operation] = cls._metrics['operations'][operation][-1000:]
    
    @classmethod
    def record_error(cls, operation: str, error: str):
        """Record operation errors"""
        cls._metrics['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'error': error
        })
        # Keep only last 100 errors
        if len(cls._metrics['errors']) > 100:
            cls._metrics['errors'] = cls._metrics['errors'][-100:]
    
    @classmethod
    def record_discrepancy(cls, operation: str, legacy_result: Any, brain_result: Any):
        """Record discrepancies between legacy and Brain calculations"""
        cls._metrics['discrepancies'].append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'legacy': str(legacy_result)[:200],  # Truncate for storage
            'brain': str(brain_result)[:200]
        })
        # Keep only last 50 discrepancies
        if len(cls._metrics['discrepancies']) > 50:
            cls._metrics['discrepancies'] = cls._metrics['discrepancies'][-50:]
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return cls._metrics.copy()
    
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Get metrics summary for dashboard"""
        return cls._metrics.copy()
    
    @classmethod
    def record_feedback(cls, feedback: Dict[str, Any]):
        """Record user feedback about Brain selections"""
        if 'feedback' not in cls._metrics:
            cls._metrics['feedback'] = []
        cls._metrics['feedback'].append({
            'timestamp': datetime.now().isoformat(),
            'details': feedback
        })
        # Keep only last 100 feedback entries
        if len(cls._metrics['feedback']) > 100:
            cls._metrics['feedback'] = cls._metrics['feedback'][-100:]


class PumpBrain:
    """
    Central intelligence system for pump operations.
    Consolidates all pump-related calculations and decision-making.
    """
    
    def __init__(self, repository=None, config_service=None):
        """
        Initialize the Brain with all intelligence modules.
        
        Args:
            repository: PumpRepository instance for data access
            config_service: AdminConfigService for configuration management
        """
        # CRITICAL FIX: Always ensure repository is available
        if repository is None:
            from .pump_repository import get_pump_repository
            repository = get_pump_repository()
            logger.info("PumpBrain: Auto-loaded repository during initialization")
        
        # Initialize config service for tunable physics parameters
        if config_service is None:
            from .admin_config_service import admin_config_service
            config_service = admin_config_service
            logger.debug("PumpBrain: Auto-loaded admin config service")
        
        # Store dependencies
        self.repository = repository
        self.config_service = config_service
        
        # Initialize intelligence modules
        self.selection = SelectionIntelligence(self)
        self.performance = PerformanceAnalyzer(self)
        self.charts = ChartIntelligence(self)
        self.validator = DataValidator(self)
        self.ai_analysis = AIAnalysisIntelligence(self)
        
        # Initialize cache
        self._cache = BrainCache()
        
        # Log initialization
        logger.info(f"PumpBrain initialized in {BRAIN_MODE} mode")
        
        # Track initialization time for uptime monitoring
        self._initialized_at = datetime.now()
    
    def get_config_service(self):
        """
        Get the configuration service for accessing tunable parameters.
        
        Returns:
            AdminConfigService instance for physics parameter management
        """
        return self.config_service
    
    # ==================== SELECTION OPERATIONS ====================
    
    @measure_performance
    def find_best_pump(self, flow: float, head: float, 
                      constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Find the best pump(s) for given operating conditions.
        
        Args:
            flow: Required flow rate in m³/hr
            head: Required head in meters
            constraints: Optional constraints (npsh_available, max_power_kw, etc.)
        
        Returns:
            List of pump recommendations with scores and details
        """
        # Check cache first - use robust cache key generation
        cache_key = self._cache.make_key("best_pump", flow, head, constraints)
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        # Validate inputs
        validation = self.validator.validate_operating_point(flow, head)
        if not validation['valid']:
            raise ValueError(f"Invalid operating point: {validation['errors']}")
        
        # Use selection intelligence to find best pumps  
        brain_result = self.selection.find_best_pumps(flow, head, constraints, include_exclusions=False)
        
        # Extract just the ranked pumps for legacy compatibility
        results = brain_result.get('ranked_pumps', [])
        
        # Cache results
        self._cache.set(cache_key, results, ttl=300)  # 5 minute TTL
        
        return results
    
    @measure_performance
    def get_all_pump_codes(self) -> List[Dict[str, str]]:
        """
        Returns a minimal list of all pumps for UI elements like autocomplete.
        Single source of truth for pump list data.
        """
        cache_key = "all_pump_codes_list"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        pump_models = self.repository.get_pump_models()
        pump_list = [
            {
                'pump_code': pump.get('pump_code', 'Unknown'),
                'manufacturer': pump.get('manufacturer', 'APE PUMPS'),
                'pump_type': pump.get('pump_type', 'Centrifugal'),
                'description': f"{pump.get('pump_type', '')} - {pump.get('model_series', '')}"
            }
            for pump in pump_models
        ]
        
        # Sort by pump code for consistency
        pump_list.sort(key=lambda x: x['pump_code'])
        
        self._cache.set(cache_key, pump_list, ttl=3600)  # Cache for 1 hour
        logger.info(f"Brain: Generated pump list with {len(pump_list)} pumps")
        return pump_list
    
    @measure_performance
    def evaluate_pump(self, pump_id: str, flow: float, head: float) -> Dict[str, Any]:
        """
        Evaluate a specific pump at given operating conditions.
        
        Args:
            pump_id: Pump identifier (code or ID)
            flow: Operating flow rate in m³/hr
            head: Operating head in meters
        
        Returns:
            Detailed evaluation including performance, efficiency, and suitability
        """
        # Get pump data from repository
        if not self.repository:
            raise RuntimeError("Brain requires repository for pump evaluation")
        
        pump_data = self.repository.get_pump_by_code(pump_id)
        if not pump_data:
            raise ValueError(f"Pump {pump_id} not found")
        
        # Perform evaluation
        evaluation = self.selection.evaluate_single_pump(pump_data, flow, head)
        
        return evaluation
    
    @measure_performance
    def rank_pumps(self, pump_list: List[str], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank a list of pumps based on specified criteria.
        
        Args:
            pump_list: List of pump codes/IDs to rank
            criteria: Ranking criteria (flow, head, weights, etc.)
        
        Returns:
            Ranked list with scores and analysis
        """
        return self.selection.rank_pumps(pump_list, criteria)
    
    @measure_performance
    def find_best_pumps(self, site_requirements: Dict[str, Any], 
                       constraints: Optional[Dict[str, Any]] = None,
                       include_exclusions: bool = False) -> Dict[str, Any]:
        """
        Find best pumps with optional detailed exclusion analysis.
        
        DEBUG: Main Brain entry point for pump selection.
        """
        # CRITICAL DEBUG: Log main Brain entry point
        flow = site_requirements.get('flow_m3hr', 0)
        head = site_requirements.get('head_m', 0)
        logger.error(f"🎯 [MAIN BRAIN] find_best_pumps called: flow={flow}, head={head}")
        logger.error(f"🎯 [MAIN BRAIN] Constraints: {constraints}")
        logger.error(f"🎯 [MAIN BRAIN] Include exclusions: {include_exclusions}")
        
        # Validate inputs
        validation = self.validator.validate_operating_point(flow, head)
        if not validation['valid']:
            raise ValueError(f"Invalid operating point: {validation['errors']}")
        
        # Use selection intelligence with exclusion tracking
        return self.selection.find_best_pumps(flow, head, constraints, include_exclusions)
    
    # ==================== PERFORMANCE ANALYSIS ====================
    
    @measure_performance
    def calculate_performance(self, pump: Dict[str, Any], flow: float, 
                            head: float, impeller_trim: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate pump performance at specified conditions.
        
        Args:
            pump: Pump data dictionary
            flow: Operating flow rate in m³/hr
            head: Operating head in meters
            impeller_trim: Optional impeller trim percentage (85-100)
        
        Returns:
            Performance data including efficiency, power, NPSH
        """
        result = self.performance.calculate_at_point(pump, flow, head, impeller_trim)
        return result if result is not None else {}
    
    @measure_performance
    def apply_affinity_laws(self, base_curve: Dict[str, Any], 
                           diameter_ratio: float = 1.0,
                           speed_ratio: float = 1.0) -> Dict[str, Any]:
        """
        Apply affinity laws to scale pump performance.
        
        Args:
            base_curve: Base performance curve data
            diameter_ratio: Impeller diameter ratio (new/original)
            speed_ratio: Speed ratio (new/original)
        
        Returns:
            Scaled performance curve
        """
        return self.performance.apply_affinity_laws(base_curve, diameter_ratio, speed_ratio)
    
    @measure_performance
    def validate_operating_envelope(self, pump: Dict[str, Any], 
                                   flow: float, head: float) -> Dict[str, Any]:
        """
        Validate if operating point is within pump's safe envelope.
        
        Args:
            pump: Pump data
            flow: Operating flow rate
            head: Operating head
        
        Returns:
            Validation results with warnings/recommendations
        """
        return self.performance.validate_envelope(pump, flow, head)
    
    # ==================== CHART INTELLIGENCE ====================
    
    @measure_performance
    def get_optimal_chart_config(self, pump: Dict[str, Any], 
                                context: str = "web") -> Dict[str, Any]:
        """
        Get optimal chart configuration for pump visualization.
        
        Args:
            pump: Pump data to visualize
            context: Display context (web/pdf/report)
        
        Returns:
            Chart configuration with ranges, annotations, etc.
        """
        return self.charts.get_optimal_config(pump, context)
    
    @measure_performance
    def generate_chart_annotations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate intelligent chart annotations based on analysis.
        
        Args:
            analysis: Pump analysis results
        
        Returns:
            List of annotations with positions and text
        """
        return self.charts.generate_annotations(analysis)
    
    @measure_performance
    def determine_axis_ranges(self, curves: List[Dict[str, Any]], 
                            operating_point: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Determine optimal axis ranges for chart display.
        
        Args:
            curves: List of performance curves
            operating_point: Optional (flow, head) tuple
        
        Returns:
            Axis ranges for x and y axes
        """
        return self.charts.calculate_axis_ranges(curves, operating_point)
    
    # ==================== VALIDATION & CONVERSION ====================
    
    @measure_performance
    def convert_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert between different units.
        
        Args:
            value: Numeric value to convert
            from_unit: Source unit
            to_unit: Target unit
        
        Returns:
            Converted value
        """
        return self.validator.convert_units(value, from_unit, to_unit)
    
    @measure_performance
    def validate_data_integrity(self, pump_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate pump data integrity and completeness.
        
        Args:
            pump_data: Pump data to validate
        
        Returns:
            Validation results with issues identified
        """
        return self.validator.validate_pump_data(pump_data)
    
    @measure_performance
    def handle_missing_data(self, pump: Dict[str, Any], 
                          strategy: str = "interpolate") -> Dict[str, Any]:
        """
        Handle missing data in pump specifications.
        
        Args:
            pump: Pump data with potential missing fields
            strategy: Strategy for handling missing data
        
        Returns:
            Pump data with missing fields handled
        """
        return self.validator.handle_missing_data(pump, strategy)
    
    # ==================== SHADOW MODE OPERATIONS ====================
    
    # Shadow compare method removed - Brain is now always active
    # Archived to archive/shadow_mode/shadow_compare_method.py
    
    def _results_differ(self, result1: Any, result2: Any, tolerance: float = 0.01) -> bool:
        """
        Compare two results for significant differences.
        
        Args:
            result1: First result
            result2: Second result
            tolerance: Numerical tolerance for float comparisons
        
        Returns:
            True if results differ significantly
        """
        # Handle None cases
        if result1 is None or result2 is None:
            return result1 != result2
        
        # Handle numeric comparisons
        if isinstance(result1, (int, float)) and isinstance(result2, (int, float)):
            return abs(result1 - result2) > tolerance
        
        # Handle dictionary comparisons
        if isinstance(result1, dict) and isinstance(result2, dict):
            # Check if same keys
            if set(result1.keys()) != set(result2.keys()):
                return True
            # Check values recursively
            for key in result1:
                if self._results_differ(result1[key], result2[key], tolerance):
                    return True
            return False
        
        # Handle list comparisons
        if isinstance(result1, list) and isinstance(result2, list):
            if len(result1) != len(result2):
                return True
            for item1, item2 in zip(result1, result2):
                if self._results_differ(item1, item2, tolerance):
                    return True
            return False
        
        # Default comparison
        return result1 != result2
    
    # ==================== UTILITY METHODS ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get Brain system status and metrics."""
        uptime = (datetime.now() - self._initialized_at).total_seconds()
        
        return {
            'status': 'operational',
            'mode': BRAIN_MODE,
            'uptime_seconds': uptime,
            'cache_stats': self._cache.get_stats(),
            'metrics': BrainMetrics.get_metrics(),
            'initialized_at': self._initialized_at.isoformat()
        }
    
    def clear_cache(self):
        """Clear Brain cache."""
        self._cache.clear()
        logger.info("Brain cache cleared")


# ==================== GLOBAL BRAIN INSTANCE ====================

# Create singleton Brain instance
_brain_instance = None


def get_pump_brain(repository=None) -> PumpBrain:
    """
    Get or create the global Brain instance.
    
    Args:
        repository: Optional repository instance
    
    Returns:
        PumpBrain singleton instance
    """
    global _brain_instance
    
    if _brain_instance is None:
        # CRITICAL FIX: Always ensure repository is available
        if repository is None:
            from .pump_repository import get_pump_repository
            repository = get_pump_repository()
            logger.info("Brain system: Auto-loaded repository for initialization")
        _brain_instance = PumpBrain(repository)
    elif repository and _brain_instance.repository is None:
        # Update repository if provided and not set
        _brain_instance.repository = repository
    elif _brain_instance.repository is None:
        # CRITICAL FIX: If Brain exists but has no repository, fix it
        from .pump_repository import get_pump_repository
        _brain_instance.repository = get_pump_repository()
        logger.info("Brain system: Repository connection restored")
    
    return _brain_instance


def reset_brain():
    """Reset the global Brain instance (mainly for testing)."""
    global _brain_instance
    _brain_instance = None
    logger.info("Brain instance reset")