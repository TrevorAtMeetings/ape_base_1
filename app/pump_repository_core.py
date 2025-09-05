"""
Pump Repository Core Module
===========================
Core repository functionality and connection management
"""

import os
import logging
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager
from datetime import datetime
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Enum for data source types"""
    POSTGRESQL = "postgresql"

@dataclass
class PumpRepositoryConfig:
    """Configuration for pump repository"""
    # Data source configuration
    data_source: DataSource = DataSource.POSTGRESQL

    # PostgreSQL configuration using DATABASE_URL format
    database_url: Optional[str] = None  # Will be set dynamically

    # Connection pooling configuration
    pool_min_size: int = 1
    pool_max_size: int = 10

    # General configuration
    cache_enabled: bool = True
    reload_on_change: bool = False
    batch_size: int = 1000  # For large dataset processing


class PumpRepository:
    """
    Centralized repository for pump data management.
    Supports PostgreSQL database source.
    """

    def __init__(self, config: Optional[PumpRepositoryConfig] = None):
        self.config = config or PumpRepositoryConfig()
        self._catalog_data = None
        self._pump_models = None
        self._metadata = None
        self._last_loaded = None
        self._is_loaded = False
        self._connection_pool = None
        self._lock = threading.Lock()

    def _get_connection_pool(self):
        """Get or create connection pool"""
        if self._connection_pool is None:
            try:
                # Get DATABASE_URL dynamically if not set
                database_url = self.config.database_url or os.getenv('DATABASE_URL')
                if not database_url:
                    raise ValueError("DATABASE_URL not configured")

                self._connection_pool = SimpleConnectionPool(
                    self.config.pool_min_size,
                    self.config.pool_max_size,
                    database_url
                )
                logger.info(f"Repository: Created connection pool with {self.config.pool_min_size}-{self.config.pool_max_size} connections")
            except Exception as e:
                logger.error(f"Repository: Failed to create connection pool: {e}")
                raise
        return self._connection_pool

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        pool = self._get_connection_pool()
        conn = pool.getconn()
        try:
            yield conn
        finally:
            pool.putconn(conn)

    def load_catalog(self) -> bool:
        """Load catalog data from configured source"""
        try:
            if self.config.data_source == DataSource.POSTGRESQL:
                # Import and use the loader module
                from .pump_repository_loader import PostgreSQLLoader
                loader = PostgreSQLLoader(self)
                return loader.load_from_postgresql_optimized()
            else:
                logger.error(f"Repository: Unknown data source: {self.config.data_source}")
                return False

        except Exception as e:
            logger.error(f"Repository: Error loading catalog: {e}")
            self._catalog_data = None
            self._pump_models = []
            self._metadata = {}
            self._is_loaded = False
            return False

    def reload_catalog(self) -> bool:
        """Force reload catalog data clearing cache"""
        logger.info("Repository: Force reloading catalog data")
        self._catalog_data = None
        self._pump_models = None
        self._metadata = None
        self._is_loaded = False
        return self.load_catalog()

    def get_catalog_data(self) -> Dict[str, Any]:
        """Get raw catalog data"""
        if not self._is_loaded:
            self.load_catalog()
        return self._catalog_data or {}

    def get_pump_models(self) -> List[Dict[str, Any]]:
        """Get list of pump models"""
        if not self._is_loaded:
            self.load_catalog()
        return self._pump_models or []
    
    def get_all_pumps(self) -> List[Dict[str, Any]]:
        """Get all pumps - alias for get_pump_models for Brain system compatibility"""
        return self.get_pump_models()

    def get_metadata(self) -> Dict[str, Any]:
        """Get catalog metadata"""
        if not self._is_loaded:
            self.load_catalog()
        return self._metadata or {}

    def get_pump_by_code(self, pump_code: str) -> Optional[Dict[str, Any]]:
        """Get specific pump model by code (normalize whitespace/case)"""
        if not pump_code:
            return None
        key = ''.join(pump_code.split()).upper()  # strip spaces, uppercase
        pump_models = self.get_pump_models()
        for pump in pump_models:
            pump_code_normalized = ''.join((pump.get('pump_code') or '').split()).upper()
            if pump_code_normalized == key:
                return pump
        return None

    def get_pump_count(self) -> int:
        """Get total number of pump models"""
        return len(self.get_pump_models())

    def get_curve_count(self) -> int:
        """Get total number of curves"""
        metadata = self.get_metadata()
        return metadata.get('total_curves', 0)

    def reload(self) -> bool:
        """Force reload of catalog data"""
        self._is_loaded = False
        return self.load_catalog()

    def is_loaded(self) -> bool:
        """Check if repository is loaded"""
        return self._is_loaded

    def get_data_source(self) -> DataSource:
        """Get current data source"""
        return self.config.data_source

    def __del__(self):
        """Cleanup connection pool on deletion"""
        if self._connection_pool:
            self._connection_pool.closeall()


# Singleton pattern functions
_pump_repository = None

def get_pump_repository():
    """Get the singleton pump repository instance"""
    global _pump_repository
    if _pump_repository is None:
        config = PumpRepositoryConfig()
        config.database_url = os.getenv('DATABASE_URL')
        _pump_repository = PumpRepository(config)
    return _pump_repository


def clear_pump_repository():
    """Clear the singleton pump repository instance"""
    global _pump_repository
    _pump_repository = None


def load_all_pump_data():
    """Load all pump data from the repository"""
    try:
        repository = get_pump_repository()
        if not repository.is_loaded():
            success = repository.load_catalog()
            if not success:
                logger.error("Failed to load pump catalog")
                return []
        
        return repository.get_pump_models()
    except Exception as e:
        logger.error(f"Error loading pump data: {e}")
        return []