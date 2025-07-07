"""
Centralized Pump Repository
Single source of truth for pump data loading and management.
Supports both JSON file and PostgreSQL database sources.
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Enum for data source types"""
    JSON_FILE = "json_file"
    POSTGRESQL = "postgresql"

@dataclass
class PumpRepositoryConfig:
    """Configuration for pump repository"""
    # Data source configuration
    data_source: DataSource = DataSource.JSON_FILE
    
    # JSON file configuration
    catalog_path: str = "data/ape_catalog_database.json"
    
    # PostgreSQL configuration using DATABASE_URL format
    database_url: str = "postgresql://postgres:password@localhost:5432/pump_selection"
    
    # General configuration
    cache_enabled: bool = True
    reload_on_change: bool = False

class PumpRepository:
    """
    Centralized repository for pump data management.
    Supports both JSON file and PostgreSQL database sources.
    """
    
    def __init__(self, config: PumpRepositoryConfig = None):
        self.config = config or PumpRepositoryConfig()
        self._catalog_data = None
        self._pump_models = None
        self._metadata = None
        self._last_loaded = None
        self._is_loaded = False
        
    def load_catalog(self) -> bool:
        """Load catalog data from configured source"""
        try:
            if self.config.data_source == DataSource.JSON_FILE:
                return self._load_from_json()
            elif self.config.data_source == DataSource.POSTGRESQL:
                return self._load_from_postgresql()
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
    
    def _load_from_json(self) -> bool:
        """Load catalog data from JSON file"""
        try:
            if not os.path.exists(self.config.catalog_path):
                logger.error(f"Repository: Catalog file not found: {self.config.catalog_path}")
                return False
                
            with open(self.config.catalog_path, 'r', encoding='utf-8') as f:
                self._catalog_data = json.load(f)
            
            self._metadata = self._catalog_data.get('metadata', {})
            self._pump_models = self._catalog_data.get('pump_models', [])
            self._is_loaded = True
            
            logger.info(f"Repository: Loaded {len(self._pump_models)} pump models from JSON file")
            logger.info(f"Repository: Total curves: {self._metadata.get('total_curves', 0)}")
            logger.info(f"Repository: NPSH curves: {self._metadata.get('npsh_curves', 0)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Repository: Error loading from JSON: {e}")
            return False
    
    def _load_from_postgresql(self) -> bool:
        """
        Load catalog data from PostgreSQL database using DATABASE_URL.
        Currently a stub method - to be implemented when database is needed.
        """
        try:
            logger.info("Repository: PostgreSQL data source selected - stub method called")
            logger.warning("Repository: PostgreSQL functionality not yet implemented")
            logger.info(f"Repository: DATABASE_URL format: {self.config.database_url}")
            
            # TODO: Implement PostgreSQL loading logic using DATABASE_URL
            # This would include:
            # 1. Parsing DATABASE_URL to extract connection parameters
            # 2. Establishing database connection using psycopg2
            # 3. Querying pump data from tables
            # 4. Converting database rows to catalog format
            # 5. Handling connection pooling and error recovery
            
            # Example DATABASE_URL parsing:
            # from urllib.parse import urlparse
            # parsed = urlparse(self.config.database_url)
            # connection_params = {
            #     'host': parsed.hostname,
            #     'port': parsed.port,
            #     'database': parsed.path[1:],  # Remove leading '/'
            #     'user': parsed.username,
            #     'password': parsed.password
            # }
            
            # For now, return empty data structure
            self._catalog_data = {
                'metadata': {
                    'total_curves': 0,
                    'npsh_curves': 0,
                    'source': 'postgresql',
                    'status': 'not_implemented',
                    'database_url': self.config.database_url
                },
                'pump_models': []
            }
            self._metadata = self._catalog_data.get('metadata', {})
            self._pump_models = self._catalog_data.get('pump_models', [])
            self._is_loaded = True
            
            logger.info("Repository: PostgreSQL stub loaded (no data)")
            return True
            
        except Exception as e:
            logger.error(f"Repository: Error loading from PostgreSQL: {e}")
            return False
    
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
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get catalog metadata"""
        if not self._is_loaded:
            self.load_catalog()
        return self._metadata or {}
    
    def get_pump_by_code(self, pump_code: str) -> Optional[Dict[str, Any]]:
        """Get specific pump model by code"""
        pump_models = self.get_pump_models()
        for pump in pump_models:
            if pump.get('pump_code') == pump_code:
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
    
    def switch_data_source(self, new_source: DataSource) -> bool:
        """
        Switch data source and reload data.
        Useful for testing or runtime configuration changes.
        """
        logger.info(f"Repository: Switching data source from {self.config.data_source} to {new_source}")
        self.config.data_source = new_source
        return self.reload()

# Global repository instance
_repository = None

def get_pump_repository(config: PumpRepositoryConfig = None) -> PumpRepository:
    """Get global pump repository instance (singleton pattern)"""
    global _repository
    if _repository is None:
        _repository = PumpRepository(config)
        _repository.load_catalog()
    return _repository

def reload_pump_repository() -> bool:
    """Force reload of the global repository"""
    global _repository
    if _repository:
        return _repository.reload()
    return False

def switch_repository_data_source(new_source: DataSource) -> bool:
    """Switch the global repository's data source"""
    global _repository
    if _repository:
        return _repository.switch_data_source(new_source)
    return False 