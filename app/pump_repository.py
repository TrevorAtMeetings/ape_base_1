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
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Enum for data source types"""
    JSON_FILE = "json_file"
    POSTGRESQL = "postgresql"

@dataclass
class PumpRepositoryConfig:
    """Configuration for pump repository"""
    # Data source configuration
    data_source: DataSource = DataSource.POSTGRESQL # Change this to toggle between JSON and PostgreSQL
    
    # JSON file configuration
    catalog_path: str = "data/ape_catalog_database.json"
    
    # PostgreSQL configuration using DATABASE_URL format
    database_url: str = os.getenv('DATABASE_URL')
    
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
            
            # Ensure metadata has both old and new field names for compatibility
            if 'total_curves' in self._metadata and 'curve_count' not in self._metadata:
                self._metadata['curve_count'] = self._metadata['total_curves']
            elif 'curve_count' in self._metadata and 'total_curves' not in self._metadata:
                self._metadata['total_curves'] = self._metadata['curve_count']
            
            # Ensure each pump model has the expected fields
            for pump_model in self._pump_models:
                if 'curve_count' not in pump_model:
                    pump_model['curve_count'] = len(pump_model.get('curves', []))
                if 'total_points' not in pump_model:
                    pump_model['total_points'] = sum(len(curve.get('performance_points', [])) for curve in pump_model.get('curves', []))
                if 'npsh_curves' not in pump_model:
                    pump_model['npsh_curves'] = sum(1 for curve in pump_model.get('curves', []) if curve.get('has_npsh_data', False))
                if 'power_curves' not in pump_model:
                    pump_model['power_curves'] = sum(1 for curve in pump_model.get('curves', []) if curve.get('has_power_data', False))
                
                # Add additional fields for compatibility if not present
                if 'description' not in pump_model:
                    pump_model['description'] = f"{pump_model.get('pump_code', '')} - {pump_model.get('model_series', '')}"
                if 'max_flow_m3hr' not in pump_model:
                    specs = pump_model.get('specifications', {})
                    pump_model['max_flow_m3hr'] = specs.get('max_flow_m3hr', 0)
                if 'max_head_m' not in pump_model:
                    specs = pump_model.get('specifications', {})
                    pump_model['max_head_m'] = specs.get('max_head_m', 0)
                if 'max_power_kw' not in pump_model:
                    pump_model['max_power_kw'] = 0
                if 'min_efficiency' not in pump_model:
                    pump_model['min_efficiency'] = 0
                if 'max_efficiency' not in pump_model:
                    pump_model['max_efficiency'] = 0
                if 'connection_size' not in pump_model:
                    pump_model['connection_size'] = 'Standard'
                if 'materials' not in pump_model:
                    pump_model['materials'] = 'Cast Iron'
            
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
        Maps existing database tables to catalog format.
        """
        try:
            logger.info("Repository: Loading data from PostgreSQL database")
            
            # Parse DATABASE_URL
            parsed_url = urlparse(self.config.database_url)
            connection_params = {
                'host': parsed_url.hostname,
                'port': parsed_url.port or 5432,
                'database': parsed_url.path[1:],  # Remove leading '/'
                'user': parsed_url.username,
                'password': parsed_url.password
            }
            
            logger.info(f"Repository: Connecting to PostgreSQL at {connection_params['host']}:{connection_params['port']}")
            
            # Connect to database
            with psycopg2.connect(**connection_params) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    
                    # Get database schema information
                    cursor.execute("""
                        SELECT table_name, column_name, data_type
                        FROM information_schema.columns 
                        WHERE table_schema = 'public'
                        ORDER BY table_name, ordinal_position
                    """)
                    schema_info = cursor.fetchall()
                    
                    # Group columns by table
                    tables = {}
                    for row in schema_info:
                        table_name = row['table_name']
                        if table_name not in tables:
                            tables[table_name] = []
                        tables[table_name].append({
                            'column_name': row['column_name'],
                            'data_type': row['data_type']
                        })
                    
                    logger.info(f"Repository: Found tables: {list(tables.keys())}")
                    
                    # Load pump models and curves based on actual database structure
                    pump_models = []
                    total_curves = 0
                    total_points = 0
                    npsh_curves = 0
                    
                    # Query pumps with specifications
                    cursor.execute("""
                        SELECT 
                            p.id,
                            p.pump_code,
                            p.manufacturer,
                            p.pump_type,
                            p.series as model_series,
                            p.application_category,
                            p.construction_standard,
                            p.impeller_type,
                            ps.test_speed_rpm,
                            ps.max_flow_m3hr,
                            ps.max_head_m,
                            ps.max_power_kw,
                            ps.bep_flow_m3hr,
                            ps.bep_head_m,
                            ps.npshr_at_bep,
                            ps.min_impeller_diameter_mm,
                            ps.max_impeller_diameter_mm,
                            ps.min_speed_rpm,
                            ps.max_speed_rpm,
                            ps.variable_speed,
                            ps.variable_diameter
                        FROM pumps p
                        LEFT JOIN pump_specifications ps ON p.id = ps.pump_id
                        ORDER BY p.pump_code
                    """)
                    
                    pump_data = cursor.fetchall()
                    logger.info(f"Repository: Found {len(pump_data)} pump records")
                    
                    # Process each pump record
                    for pump_row in pump_data:
                        pump_row_dict = dict(pump_row)
                        
                        # Map to standard format
                        pump_code = pump_row_dict['pump_code']
                        manufacturer = pump_row_dict.get('manufacturer', 'APE PUMPS')
                        pump_type = pump_row_dict.get('pump_type', 'END SUCTION')
                        model_series = pump_row_dict.get('model_series', '')
                        pump_id = pump_row_dict['id']
                        
                        # Query curves for this pump
                        cursor.execute("""
                            SELECT 
                                id as curve_id,
                                impeller_diameter_mm,
                                pump_id
                            FROM pump_curves
                            WHERE pump_id = %s
                            ORDER BY impeller_diameter_mm
                        """, (pump_id,))
                        
                        curves_data = cursor.fetchall()
                        total_curves += len(curves_data)
                        
                        # Build curves with performance points
                        curves = []
                        for curve_row in curves_data:
                            curve_row_dict = dict(curve_row)
                            curve_id = curve_row_dict['curve_id']
                            
                            # Query performance points for this curve
                            cursor.execute("""
                                SELECT 
                                    operating_point,
                                    flow_rate as flow_m3hr,
                                    head as head_m,
                                    efficiency as efficiency_pct,
                                    npshr as npshr_m
                                FROM pump_performance_points
                                WHERE curve_id = %s
                                ORDER BY operating_point
                            """, (curve_id,))
                            
                            points_data = cursor.fetchall()
                            total_points += len(points_data)
                            
                            # Convert points to list of dicts
                            performance_points = []
                            for point in points_data:
                                point_dict = dict(point)
                                performance_points.append({
                                    'flow_m3hr': float(point_dict['flow_m3hr']) if point_dict['flow_m3hr'] is not None else 0.0,
                                    'head_m': float(point_dict['head_m']) if point_dict['head_m'] is not None else 0.0,
                                    'efficiency_pct': float(point_dict['efficiency_pct']) if point_dict['efficiency_pct'] is not None else 0.0,
                                    'power_kw': None,  # Not available in current schema
                                    'npshr_m': float(point_dict['npshr_m']) if point_dict['npshr_m'] is not None else None
                                })
                            
                            # Check if curve has NPSH data
                            has_npsh_data = any(p.get('npshr_m') for p in performance_points)
                            if has_npsh_data:
                                npsh_curves += 1
                            
                            # Calculate ranges
                            flows = [p['flow_m3hr'] for p in performance_points]
                            heads = [p['head_m'] for p in performance_points]
                            efficiencies = [p['efficiency_pct'] for p in performance_points]
                            npshrs = [p['npshr_m'] for p in performance_points if p.get('npshr_m')]
                            
                            # Build curve object
                            curve = {
                                'curve_id': f"{pump_code}_C{len(curves)+1}_{curve_row_dict['impeller_diameter_mm']}mm",
                                'curve_index': len(curves),
                                'impeller_diameter_mm': float(curve_row_dict['impeller_diameter_mm']),
                                'test_speed_rpm': int(pump_row_dict.get('test_speed_rpm', 0)) if pump_row_dict.get('test_speed_rpm') is not None else 0,
                                'performance_points': performance_points,
                                'point_count': len(performance_points),
                                'flow_range_m3hr': f"{min(flows)}-{max(flows)}" if flows else "0.0-0.0",
                                'head_range_m': f"{min(heads)}-{max(heads)}" if heads else "0.0-0.0",
                                'efficiency_range_pct': f"{min(efficiencies)}-{max(efficiencies)}" if efficiencies else "0.0-0.0",
                                'has_power_data': False,  # Not available in current schema
                                'has_npsh_data': has_npsh_data,
                                'npsh_range_m': f"{min(npshrs)}-{max(npshrs)}" if npshrs else "0.0-0.0"
                            }
                            curves.append(curve)
                        
                        # Build pump model object
                        pump_model = {
                            'pump_code': pump_code,
                            'manufacturer': manufacturer,
                            'pump_type': pump_type,
                            'model_series': model_series,
                            'specifications': {
                                'max_flow_m3hr': float(pump_row_dict.get('max_flow_m3hr', 0)) if pump_row_dict.get('max_flow_m3hr') is not None else 0,
                                'max_head_m': float(pump_row_dict.get('max_head_m', 0)) if pump_row_dict.get('max_head_m') is not None else 0,
                                'min_impeller_mm': float(pump_row_dict.get('min_impeller_diameter_mm', 0)) if pump_row_dict.get('min_impeller_diameter_mm') is not None else 0,
                                'max_impeller_mm': float(pump_row_dict.get('max_impeller_diameter_mm', 0)) if pump_row_dict.get('max_impeller_diameter_mm') is not None else 0,
                                'test_speed_rpm': int(pump_row_dict.get('test_speed_rpm', 0)) if pump_row_dict.get('test_speed_rpm') is not None else 0,
                                'min_speed_rpm': int(pump_row_dict.get('min_speed_rpm', 0)) if pump_row_dict.get('min_speed_rpm') is not None else 0,
                                'max_speed_rpm': int(pump_row_dict.get('max_speed_rpm', 0)) if pump_row_dict.get('max_speed_rpm') is not None else 0
                            },
                            'curves': curves,
                            # Add fields expected by catalog engine
                            'curve_count': len(curves),
                            'total_points': sum(len(curve['performance_points']) for curve in curves),
                            'npsh_curves': sum(1 for curve in curves if curve['has_npsh_data']),
                            'power_curves': sum(1 for curve in curves if curve['has_power_data']),
                            # Add additional fields for compatibility
                            'description': f"{pump_code} - {model_series}",
                            'max_flow_m3hr': float(pump_row_dict.get('max_flow_m3hr', 0)) if pump_row_dict.get('max_flow_m3hr') is not None else 0,
                            'max_head_m': float(pump_row_dict.get('max_head_m', 0)) if pump_row_dict.get('max_head_m') is not None else 0,
                            'max_power_kw': float(pump_row_dict.get('max_power_kw', 0)) if pump_row_dict.get('max_power_kw') is not None else 0,
                            'min_efficiency': min((p['efficiency_pct'] for curve in curves for p in curve['performance_points'] if p['efficiency_pct'] > 0), default=0),
                            'max_efficiency': max((p['efficiency_pct'] for curve in curves for p in curve['performance_points']), default=0),
                            'connection_size': 'Standard',
                            'materials': 'Cast Iron'
                        }
                        pump_models.append(pump_model)
                    
                    # Build metadata with both old and new field names for compatibility
                    metadata = {
                        'build_date': datetime.now().isoformat(),
                        'source': 'postgresql',
                        'total_models': len(pump_models),
                        'total_curves': total_curves,
                        'curve_count': total_curves,  # Add for backward compatibility
                        'total_points': total_points,
                        'npsh_curves': npsh_curves,
                        'power_curves': 0,  # Not available in current schema
                        'last_updated': datetime.now().isoformat(),
                        'database_url': self.config.database_url,
                        'status': 'loaded',
                        'tables_found': list(tables.keys())
                    }
                    
                    # Build catalog data structure
                    self._catalog_data = {
                        'metadata': metadata,
                        'pump_models': pump_models
                    }
                    
                    self._metadata = metadata
                    self._pump_models = pump_models
                    self._is_loaded = True
                    
                    logger.info(f"Repository: Successfully loaded {len(pump_models)} pump models from PostgreSQL")
                    logger.info(f"Repository: Total curves: {total_curves}")
                    logger.info(f"Repository: Total points: {total_points}")
                    logger.info(f"Repository: NPSH curves: {npsh_curves}")
                    logger.info(f"Repository: Tables used: {list(tables.keys())}")
                    
                    return True
                    
        except psycopg2.Error as e:
            logger.error(f"Repository: PostgreSQL error: {e}")
            return False
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