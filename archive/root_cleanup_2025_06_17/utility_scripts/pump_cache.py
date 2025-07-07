#!/usr/bin/env python3
"""
Pump Data Cache System
Optimizes database loading and pump lookup performance
"""

import time
import threading
from typing import Dict, List, Optional
from pump_engine import ParsedPumpData

class PumpCache:
    """In-memory cache for pump data to improve performance"""
    
    def __init__(self):
        self._cache: Optional[List[ParsedPumpData]] = None
        self._pump_index: Dict[str, ParsedPumpData] = {}
        self._last_updated = 0
        self._cache_ttl = 300  # 5 minutes
        self._lock = threading.Lock()
    
    def get_all_pumps(self) -> List[ParsedPumpData]:
        """Get all pump data with caching"""
        with self._lock:
            current_time = time.time()
            
            # Check if cache is valid
            if (self._cache is None or 
                current_time - self._last_updated > self._cache_ttl):
                self._refresh_cache()
            
            return self._cache.copy()
    
    def get_pump_by_code(self, pump_code: str) -> Optional[ParsedPumpData]:
        """Get specific pump by code with fast lookup"""
        with self._lock:
            current_time = time.time()
            
            # Refresh cache if needed
            if (self._cache is None or 
                current_time - self._last_updated > self._cache_ttl):
                self._refresh_cache()
            
            return self._pump_index.get(pump_code)
    
    def _refresh_cache(self):
        """Refresh the cache from database"""
        from pump_engine import load_all_pump_data
        
        start_time = time.time()
        self._cache = load_all_pump_data()
        
        # Build index for fast lookup
        self._pump_index.clear()
        for pump in self._cache:
            self._pump_index[pump.pump_code] = pump
        
        self._last_updated = time.time()
        load_time = self._last_updated - start_time
        
        print(f"Cache refreshed: {len(self._cache)} pumps in {load_time:.3f}s")
    
    def invalidate(self):
        """Force cache refresh on next access"""
        with self._lock:
            self._last_updated = 0
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache performance statistics"""
        with self._lock:
            return {
                'cached_pumps': len(self._cache) if self._cache else 0,
                'indexed_pumps': len(self._pump_index),
                'last_updated': self._last_updated,
                'cache_age_seconds': time.time() - self._last_updated if self._last_updated > 0 else 0,
                'cache_valid': time.time() - self._last_updated < self._cache_ttl if self._last_updated > 0 else False
            }

# Global cache instance
pump_cache = PumpCache()