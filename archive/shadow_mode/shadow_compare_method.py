"""
ARCHIVED: Shadow Compare Method from PumpBrain
Date Archived: August 8, 2025
Reason: Brain system is now active in production, shadow mode no longer needed

This method was used to run Brain operations in parallel with legacy code
and compare results during the transition period.
"""

def shadow_compare(self, operation: str, legacy_result: Any, *args, **kwargs) -> Any:
    """
    Run Brain operation in shadow mode and compare with legacy result.
    
    Args:
        operation: Brain operation name
        legacy_result: Result from legacy calculation
        *args, **kwargs: Arguments for Brain operation
    
    Returns:
        Legacy result (in shadow mode) or Brain result (in active mode)
    """
    if BRAIN_MODE == 'disabled':
        return legacy_result
    
    try:
        # Get the Brain method
        brain_method = getattr(self, operation)
        if not brain_method:
            logger.error(f"Brain operation '{operation}' not found")
            return legacy_result
        
        # Calculate with Brain
        brain_result = brain_method(*args, **kwargs)
        
        # Compare results
        if self._results_differ(legacy_result, brain_result):
            logger.warning(f"Discrepancy in {operation}: Legacy vs Brain differ")
            BrainMetrics.record_discrepancy(operation, legacy_result, brain_result)
        
        # Return based on mode
        if BRAIN_MODE == 'active':
            logger.debug(f"Using Brain result for {operation}")
            return brain_result
        else:  # shadow mode
            logger.debug(f"Shadow mode: returning legacy result for {operation}")
            return legacy_result
            
    except Exception as e:
        logger.error(f"Brain shadow operation failed: {str(e)}")
        return legacy_result

def _results_differ(self, result1: Any, result2: Any, tolerance: float = 0.01) -> bool:
    """
    Check if two results differ significantly.
    
    Args:
        result1: First result to compare
        result2: Second result to compare
        tolerance: Tolerance for numerical comparison (default 1%)
    
    Returns:
        True if results differ significantly
    """
    # Implementation details omitted for brevity
    pass