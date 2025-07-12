"""
Centralized Pump Repository
Single source of truth for pump data loading and management.
Supports PostgreSQL database source.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
from datetime import datetime
from contextlib import contextmanager
import threading

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
    database_url: str = None  # Will be set dynamically
    
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
    
    def __init__(self, config: PumpRepositoryConfig = None):
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
                return self._load_from_postgresql_optimized()
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
    
    def _load_from_postgresql_optimized(self) -> bool:
        """
        Optimized PostgreSQL data loading using:
        - Single query with JOINs to eliminate N+1 problem
        - SQL aggregation for calculations
        - Connection pooling
        - Batch processing for large datasets
        """
        try:
            logger.info("Repository: Loading data from PostgreSQL database (optimized)")
            
            # Get DATABASE_URL dynamically when needed
            database_url = self.config.database_url or os.getenv('DATABASE_URL')
            if not database_url:
                logger.error("Repository: DATABASE_URL not configured")
                return False
            
            # Update config with the actual URL
            self.config.database_url = database_url
            
            # Parse DATABASE_URL for logging purposes
            parsed_url = urlparse(self.config.database_url)
            logger.info(f"Repository: Connecting to PostgreSQL at {parsed_url.hostname}:{parsed_url.port or 5432}")
            
            with self._get_connection() as conn:
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
                    
                    # OPTIMIZED: Single query to get all pump data with aggregated statistics
                    cursor.execute("""
                        WITH pump_stats AS (
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
                                ps.variable_diameter,
                                -- Aggregated statistics
                                COUNT(DISTINCT pc.id) as curve_count,
                                COUNT(ppp.id) as total_points,
                                COUNT(DISTINCT CASE WHEN ppp.npshr IS NOT NULL THEN pc.id END) as npsh_curves,
                                MIN(ppp.efficiency) as min_efficiency,
                                MAX(ppp.efficiency) as max_efficiency,
                                MIN(ppp.flow_rate) as min_flow,
                                MAX(ppp.flow_rate) as max_flow,
                                MIN(ppp.head) as min_head,
                                MAX(ppp.head) as max_head
                            FROM pumps p
                            LEFT JOIN pump_specifications ps ON p.id = ps.pump_id
                            LEFT JOIN pump_curves pc ON p.id = pc.pump_id
                            LEFT JOIN pump_performance_points ppp ON pc.id = ppp.curve_id
                            GROUP BY p.id, p.pump_code, p.manufacturer, p.pump_type, p.series,
                                     p.application_category, p.construction_standard, p.impeller_type,
                                     ps.test_speed_rpm, ps.max_flow_m3hr, ps.max_head_m, ps.max_power_kw,
                                     ps.bep_flow_m3hr, ps.bep_head_m, ps.npshr_at_bep, ps.min_impeller_diameter_mm,
                                     ps.max_impeller_diameter_mm, ps.min_speed_rpm, ps.max_speed_rpm,
                                     ps.variable_speed, ps.variable_diameter
                        )
                        SELECT * FROM pump_stats
                        ORDER BY pump_code
                    """)
                    
                    pump_stats_data = cursor.fetchall()
                    logger.info(f"Repository: Found {len(pump_stats_data)} pump records with aggregated statistics")
                    
                    # OPTIMIZED: Single query to get all curves with performance data
                    cursor.execute("""
                        SELECT 
                            p.pump_code,
                            pc.id as curve_id,
                            pc.impeller_diameter_mm,
                            pc.pump_id,
                            ppp.operating_point,
                            ppp.flow_rate as flow_m3hr,
                            ppp.head as head_m,
                            ppp.efficiency as efficiency_pct,
                            ppp.npshr as npshr_m
                        FROM pumps p
                        JOIN pump_curves pc ON p.id = pc.pump_id
                        LEFT JOIN pump_performance_points ppp ON pc.id = ppp.curve_id
                        ORDER BY p.pump_code, pc.impeller_diameter_mm, ppp.operating_point
                    """)
                    
                    all_curves_data = cursor.fetchall()
                    logger.info(f"Repository: Retrieved {len(all_curves_data)} performance points")
                    
                    # Process data efficiently using dictionaries for grouping
                    pump_models = []
                    curves_by_pump = {}
                    
                    # Group curves by pump
                    for row in all_curves_data:
                        pump_code = row['pump_code']
                        curve_id = row['curve_id']
                        
                        if pump_code not in curves_by_pump:
                            curves_by_pump[pump_code] = {}
                        
                        if curve_id not in curves_by_pump[pump_code]:
                            curves_by_pump[pump_code][curve_id] = {
                                'curve_id': curve_id,
                                'impeller_diameter_mm': row['impeller_diameter_mm'],
                                'pump_id': row['pump_id'],
                                'performance_points': []
                            }
                        
                        # Add performance point if it exists
                        if row['operating_point'] is not None:
                            curves_by_pump[pump_code][curve_id]['performance_points'].append({
                                'flow_m3hr': float(row['flow_m3hr']) if row['flow_m3hr'] is not None else 0.0,
                                'head_m': float(row['head_m']) if row['head_m'] is not None else 0.0,
                                'efficiency_pct': float(row['efficiency_pct']) if row['efficiency_pct'] is not None else 0.0,
                                'power_kw': None,  # Not available in current schema
                                'npshr_m': float(row['npshr_m']) if row['npshr_m'] is not None else None
                            })
                    
                    # Build pump models with optimized data processing
                    total_curves = 0
                    total_points = 0
                    npsh_curves = 0
                    
                    for pump_row in pump_stats_data:
                        pump_row_dict = dict(pump_row)
                        pump_code = pump_row_dict['pump_code']
                        
                        # Get curves for this pump
                        pump_curves = curves_by_pump.get(pump_code, {})
                        curves = []
                        
                        for curve_id, curve_data in pump_curves.items():
                            performance_points = curve_data['performance_points']
                            total_points += len(performance_points)
                            
                            # Check if curve has NPSH data
                            has_npsh_data = any(p.get('npshr_m') for p in performance_points)
                            if has_npsh_data:
                                npsh_curves += 1
                            
                            # Calculate ranges efficiently
                            if performance_points:
                                flows = [p['flow_m3hr'] for p in performance_points]
                                heads = [p['head_m'] for p in performance_points]
                                efficiencies = [p['efficiency_pct'] for p in performance_points]
                                npshrs = [p['npshr_m'] for p in performance_points if p.get('npshr_m')]
                                
                                curve = {
                                    'curve_id': f"{pump_code}_C{len(curves)+1}_{curve_data['impeller_diameter_mm']}mm",
                                    'curve_index': len(curves),
                                    'impeller_diameter_mm': float(curve_data['impeller_diameter_mm']),
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
                        
                        total_curves += len(curves)
                        
                        # Build pump model object using aggregated statistics
                        pump_model = {
                            'pump_code': pump_code,
                            'manufacturer': pump_row_dict.get('manufacturer', 'APE PUMPS'),
                            'pump_type': pump_row_dict.get('pump_type', 'END SUCTION'),
                            'model_series': pump_row_dict.get('model_series', ''),
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
                            # Use aggregated statistics from SQL
                            'curve_count': int(pump_row_dict.get('curve_count', 0)),
                            'total_points': int(pump_row_dict.get('total_points', 0)),
                            'npsh_curves': int(pump_row_dict.get('npsh_curves', 0)),
                            'power_curves': 0,  # Not available in current schema
                            # Add additional fields for compatibility
                            'description': f"{pump_code} - {pump_row_dict.get('model_series', '')}",
                            'max_flow_m3hr': float(pump_row_dict.get('max_flow_m3hr', 0)) if pump_row_dict.get('max_flow_m3hr') is not None else 0,
                            'max_head_m': float(pump_row_dict.get('max_head_m', 0)) if pump_row_dict.get('max_head_m') is not None else 0,
                            'max_power_kw': float(pump_row_dict.get('max_power_kw', 0)) if pump_row_dict.get('max_power_kw') is not None else 0,
                            'min_efficiency': float(pump_row_dict.get('min_efficiency', 0)) if pump_row_dict.get('min_efficiency') is not None else 0,
                            'max_efficiency': float(pump_row_dict.get('max_efficiency', 0)) if pump_row_dict.get('max_efficiency') is not None else 0,
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
    
    def _load_from_postgresql(self) -> bool:
        """
        Legacy PostgreSQL loading method (kept for backward compatibility)
        """
        return self._load_from_postgresql_optimized()
    
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
    

    
    def __del__(self):
        """Cleanup connection pool on deletion"""
        if self._connection_pool:
            self._connection_pool.closeall()

def insert_extracted_pump_data(data: dict, filename: str = None) -> int:
    """
    Insert extracted pump data (from Gemini) into the database.
    Returns the inserted pump ID.
    """
    from decimal import Decimal
    logger.info("[PumpRepo] ===== STARTING DATABASE INSERTION =====")
    logger.info(f"[PumpRepo] Inserting extracted pump data for file: {filename}")
    logger.info(f"[PumpRepo] Data structure: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    
    # Create a new repository instance for database operations
    config = PumpRepositoryConfig()
    config.database_url = os.getenv('DATABASE_URL')
    repo = PumpRepository(config)
    logger.info(f"[PumpRepo] New repository instance created for database operations")
    
    pool = repo._get_connection_pool()
    logger.info(f"[PumpRepo] Got connection pool")
    logger.info(f"[PumpRepo] Using DB URL: {repo.config.database_url}")
    
    def to_number_or_none(value):
        if value is None or value == '' or str(value).lower() == 'n/a':
            return None
        if isinstance(value, (int, float, Decimal)):
            return value
        if isinstance(value, str):
            import re
            numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
            if numeric_match:
                try:
                    return float(numeric_match.group(1))
                except (ValueError, TypeError):
                    return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    logger.info("[PumpRepo] Getting database connection...")
    with pool.getconn() as conn:
        try:
            logger.info("[PumpRepo] Database connection established")
            conn.autocommit = True
            logger.info("[PumpRepo] Set autocommit to True")
            
            with conn.cursor() as cur:
                logger.info("[PumpRepo] Database cursor created")
                
                # Verify database connection
                logger.info("[PumpRepo] Database connection established")
                
                # Check current schema
                cur.execute("SELECT current_schema()")
                schema = cur.fetchone()[0]
                logger.info(f"[PumpRepo] Current schema: {schema}")
                
                # Check if tables exist
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('pumps', 'pump_specifications', 'pump_curves', 'pump_performance_points')
                """)
                existing_tables = [row[0] for row in cur.fetchall()]
                logger.info(f"[PumpRepo] Existing tables: {existing_tables}")
                
                # Extract data sections
                pump_details = data.get('pumpDetails', {})
                tech_details = data.get('technicalDetails', {})
                specs = data.get('specifications', {})
                
                logger.info(f"[PumpRepo] Pump details: {pump_details}")
                logger.info(f"[PumpRepo] Technical details: {tech_details}")
                logger.info(f"[PumpRepo] Specifications: {specs}")
                
                # Prepare pump insertion data
                pump_code = pump_details.get('pumpModel')
                manufacturer = tech_details.get('manufacturer')
                pump_type = pump_details.get('pumpType')
                series = pump_details.get('pumpRange')
                application_category = pump_details.get('pumpApplication')
                impeller_type = tech_details.get('impellerType')
                
                logger.info(f"[PumpRepo] Inserting pump with code: {pump_code}")
                logger.info(f"[PumpRepo] Manufacturer: {manufacturer}")
                logger.info(f"[PumpRepo] Pump type: {pump_type}")
                
                # Insert into pumps table
                cur.execute(
                    """
                    INSERT INTO pumps (pump_code, manufacturer, pump_type, series, application_category, impeller_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (pump_code) DO UPDATE SET manufacturer = EXCLUDED.manufacturer
                    RETURNING id
                    """,
                    (pump_code, manufacturer, pump_type, series, application_category, impeller_type)
                )
                pump_id = cur.fetchone()[0]
                conn.commit()  # Explicit commit after pump insert
                logger.info(f"[PumpRepo] Pump inserted successfully, pump_id: {pump_id}")
                
                # Prepare specifications data
                test_speed = to_number_or_none(specs.get('testSpeed'))
                max_flow = to_number_or_none(specs.get('maxFlow'))
                max_head = to_number_or_none(specs.get('maxHead'))
                max_power = to_number_or_none(specs.get('maxPower'))
                bep_flow = to_number_or_none(specs.get('bepFlow'))
                bep_head = to_number_or_none(specs.get('bepHead'))
                npshr_at_bep = to_number_or_none(specs.get('npshrAtBep'))
                min_impeller = to_number_or_none(specs.get('minImpeller'))
                max_impeller = to_number_or_none(specs.get('maxImpeller'))
                
                logger.info(f"[PumpRepo] Inserting specifications:")
                logger.info(f"[PumpRepo]   Test speed: {test_speed}")
                logger.info(f"[PumpRepo]   Max flow: {max_flow}")
                logger.info(f"[PumpRepo]   Max head: {max_head}")
                logger.info(f"[PumpRepo]   Max power: {max_power}")
                logger.info(f"[PumpRepo]   BEP flow: {bep_flow}")
                logger.info(f"[PumpRepo]   BEP head: {bep_head}")
                logger.info(f"[PumpRepo]   NPSHR at BEP: {npshr_at_bep}")
                logger.info(f"[PumpRepo]   Min impeller: {min_impeller}")
                logger.info(f"[PumpRepo]   Max impeller: {max_impeller}")
                
                # Insert into pump_specifications
                cur.execute(
                    """
                    INSERT INTO pump_specifications (
                        pump_id, test_speed_rpm, max_flow_m3hr, max_head_m, max_power_kw, bep_flow_m3hr,
                        bep_head_m, npshr_at_bep, min_impeller_diameter_mm, max_impeller_diameter_mm
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (pump_id) DO NOTHING
                    """,
                    (pump_id, test_speed, max_flow, max_head, max_power, bep_flow, bep_head, npshr_at_bep, min_impeller, max_impeller)
                )
                conn.commit()  # Explicit commit after specifications insert
                logger.info(f"[PumpRepo] Specifications inserted successfully")
                
                # Insert curves and performance points
                curves_data = data.get('curves', [])
                logger.info(f"[PumpRepo] Processing {len(curves_data)} curves")
                
                if curves_data and isinstance(curves_data, list):
                    for i, curve in enumerate(curves_data):
                        logger.info(f"[PumpRepo] Processing curve {i+1}: {curve}")
                        
                        impeller_diameter = to_number_or_none(curve.get('impellerDiameter'))
                        logger.info(f"[PumpRepo] Curve {i+1} impeller diameter: {impeller_diameter}")
                        
                        if not impeller_diameter or impeller_diameter <= 0:
                            logger.warning(f"[PumpRepo] Skipping curve {i+1} - invalid impeller diameter: {impeller_diameter}")
                            continue
                        
                        # Insert curve
                        cur.execute(
                            "INSERT INTO pump_curves (pump_id, impeller_diameter_mm) VALUES (%s, %s) ON CONFLICT (pump_id, impeller_diameter_mm) DO NOTHING RETURNING id",
                            (pump_id, impeller_diameter)
                        )
                        res = cur.fetchone()
                        if res:
                            curve_id = res[0]
                            logger.info(f"[PumpRepo] New curve inserted, curve_id: {curve_id}")
                        else:
                            cur.execute("SELECT id FROM pump_curves WHERE pump_id = %s AND impeller_diameter_mm = %s", (pump_id, impeller_diameter))
                            curve_id = cur.fetchone()[0]
                            logger.info(f"[PumpRepo] Existing curve found, curve_id: {curve_id}")
                        
                        # Handle both old and new data structures
                        performance_points = curve.get('performancePoints', [])
                        
                        if performance_points and isinstance(performance_points, list):
                            # NEW STRUCTURE: performancePoints array
                            logger.info(f"[PumpRepo] Using NEW structure: performancePoints with {len(performance_points)} points")
                            
                            points_inserted = 0
                            for j, point in enumerate(performance_points):
                                flow_rate = to_number_or_none(point.get('flow'))
                                head = to_number_or_none(point.get('head'))
                                efficiency = to_number_or_none(point.get('efficiency'))
                                npshr = to_number_or_none(point.get('npshr'))
                                power = to_number_or_none(point.get('power'))
                                
                                logger.info(f"[PumpRepo] Point {j+1}: flow={flow_rate}, head={head}, eff={efficiency}, npshr={npshr}")
                                
                                if flow_rate is not None and head is not None:
                                    cur.execute(
                                        "INSERT INTO pump_performance_points (curve_id, operating_point, flow_rate, head, efficiency, npshr) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (curve_id, operating_point) DO NOTHING",
                                        (curve_id, j + 1, flow_rate, head, efficiency, npshr)
                                    )
                                    points_inserted += 1
                            
                            logger.info(f"[PumpRepo] Inserted {points_inserted} performance points for curve {i+1} (NEW structure)")
                            
                        else:
                            # OLD STRUCTURE: separate arrays
                            logger.info(f"[PumpRepo] Using OLD structure: separate arrays")
                            
                            flows = curve.get('flow', [])
                            heads = curve.get('head', [])
                            efficiencies = curve.get('efficiency', [])
                            npshrs = curve.get('npsh', [])
                            powers = curve.get('power', [])
                            
                            logger.info(f"[PumpRepo] Curve {i+1} data points:")
                            logger.info(f"[PumpRepo]   Flows: {len(flows)} points")
                            logger.info(f"[PumpRepo]   Heads: {len(heads)} points")
                            logger.info(f"[PumpRepo]   Efficiencies: {len(efficiencies)} points")
                            logger.info(f"[PumpRepo]   NPSHRs: {len(npshrs)} points")
                            logger.info(f"[PumpRepo]   Powers: {len(powers)} points")
                            
                            max_len = max(len(flows), len(heads), len(efficiencies), len(npshrs), len(powers))
                            logger.info(f"[PumpRepo] Processing {max_len} performance points for curve {i+1}")
                            
                            points_inserted = 0
                            for j in range(max_len):
                                flow_rate = flows[j] if j < len(flows) else None
                                head = heads[j] if j < len(heads) else None
                                efficiency = efficiencies[j] if j < len(efficiencies) else None
                                npshr = npshrs[j] if j < len(npshrs) else None
                                power = powers[j] if j < len(powers) else None
                                
                                if flow_rate is not None and head is not None:
                                    cur.execute(
                                        "INSERT INTO pump_performance_points (curve_id, operating_point, flow_rate, head, efficiency, npshr) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (curve_id, operating_point) DO NOTHING",
                                        (curve_id, j + 1, flow_rate, head, efficiency, npshr)
                                    )
                                    points_inserted += 1
                            
                            logger.info(f"[PumpRepo] Inserted {points_inserted} performance points for curve {i+1} (OLD structure)")
                        
                        conn.commit()  # Explicit commit after each curve
                else:
                    logger.warning("[PumpRepo] No curves data found or invalid format")
                
                # Log the file as processed
                if filename:
                    logger.info(f"[PumpRepo] Logging processed file: {filename}")
                    cur.execute("INSERT INTO processed_files (filename) VALUES (%s) ON CONFLICT (filename) DO NOTHING", (filename,))
                    conn.commit()  # Explicit commit after file logging
                    logger.info(f"[PumpRepo] File logged as processed")
                
                # Verify the insertion by querying the pumps table
                cur.execute("SELECT * FROM pumps WHERE id = %s", (pump_id,))
                row = cur.fetchone()
                logger.info(f"[PumpRepo] Verification query - pumps table row for pump_id {pump_id}: {row}")
                
                # Count related records
                cur.execute("SELECT COUNT(*) FROM pump_specifications WHERE pump_id = %s", (pump_id,))
                spec_count = cur.fetchone()[0]
                logger.info(f"[PumpRepo] Specifications count for pump_id {pump_id}: {spec_count}")
                
                cur.execute("SELECT COUNT(*) FROM pump_curves WHERE pump_id = %s", (pump_id,))
                curve_count = cur.fetchone()[0]
                logger.info(f"[PumpRepo] Curves count for pump_id {pump_id}: {curve_count}")
                
                cur.execute("SELECT COUNT(*) FROM pump_performance_points WHERE curve_id IN (SELECT id FROM pump_curves WHERE pump_id = %s)", (pump_id,))
                point_count = cur.fetchone()[0]
                logger.info(f"[PumpRepo] Performance points count for pump_id {pump_id}: {point_count}")
                
                logger.info(f"[PumpRepo] ===== DATABASE INSERTION COMPLETE =====")
                logger.info(f"[PumpRepo] Final pump_id: {pump_id}")
                return pump_id
                
        except Exception as e:
            logger.error(f"[PumpRepo] Insert failed: {str(e)}")
            logger.error(f"[PumpRepo] Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"[PumpRepo] Full traceback: {traceback.format_exc()}")
            raise
        finally:
            logger.info("[PumpRepo] Returning connection to pool")
            pool.putconn(conn)

def get_ai_prompt(name: str = 'default') -> Optional[Dict[str, Any]]:
    """
    Retrieve the AI extraction prompt by name from the database.
    Returns a dict with keys: id, name, prompt_text, last_updated.
    """
    config = PumpRepositoryConfig()
    config.database_url = os.getenv('DATABASE_URL')
    repo = PumpRepository(config)
    pool = repo._get_connection_pool()
    with pool.getconn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, prompt_text, last_updated
                FROM ai_prompts
                WHERE name = %s
                LIMIT 1
            """, (name,))
            row = cur.fetchone()
            return dict(row) if row else None


def upsert_ai_prompt(name: str, prompt_text: str) -> int:
    """
    Insert or update the AI extraction prompt in the database.
    Returns the prompt id.
    """
    config = PumpRepositoryConfig()
    config.database_url = os.getenv('DATABASE_URL')
    repo = PumpRepository(config)
    pool = repo._get_connection_pool()
    with pool.getconn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ai_prompts (name, prompt_text, last_updated)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO UPDATE SET
                    prompt_text = EXCLUDED.prompt_text,
                    last_updated = CURRENT_TIMESTAMP
                RETURNING id
            """, (name, prompt_text))
            prompt_id = cur.fetchone()[0]
            conn.commit()
            return prompt_id

def insert_ai_prompt(prompt_text: str, label: str = None) -> int:
    """
    Insert a new AI extraction prompt into the database. Returns the new prompt id.
    """
    config = PumpRepositoryConfig()
    config.database_url = os.getenv('DATABASE_URL')
    repo = PumpRepository(config)
    pool = repo._get_connection_pool()
    with pool.getconn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ai_prompts (name, prompt_text, last_updated, label)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
                RETURNING id
            """, ('default', prompt_text, label))
            prompt_id = cur.fetchone()[0]
            conn.commit()
            return prompt_id

def get_latest_ai_prompt() -> Optional[Dict[str, Any]]:
    """
    Get the most recent AI extraction prompt (by last_updated DESC).
    """
    config = PumpRepositoryConfig()
    config.database_url = os.getenv('DATABASE_URL')
    repo = PumpRepository(config)
    pool = repo._get_connection_pool()
    with pool.getconn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, prompt_text, last_updated, label
                FROM ai_prompts
                WHERE name = %s
                ORDER BY last_updated DESC
                LIMIT 1
            """, ('default',))
            row = cur.fetchone()
            return dict(row) if row else None

def get_prompt_history(limit: int = 5) -> list:
    """
    Get the last N prompts (by last_updated DESC).
    """
    config = PumpRepositoryConfig()
    config.database_url = os.getenv('DATABASE_URL')
    repo = PumpRepository(config)
    pool = repo._get_connection_pool()
    with pool.getconn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, prompt_text, last_updated, label
                FROM ai_prompts
                WHERE name = %s
                ORDER BY last_updated DESC
                LIMIT %s
            """, ('default', limit))
            rows = cur.fetchall()
            return [dict(row) for row in rows]

# Global repository instance
_repository = None

def get_pump_repository(config: PumpRepositoryConfig = None) -> PumpRepository:
    """Get global pump repository instance (singleton pattern)"""
    global _repository
    
    # Always check DATABASE_URL and force reload if different
    current_db_url = os.getenv('DATABASE_URL')
    
    if _repository is None:
        logger.info(f"Repository: Creating new instance with DATABASE_URL: {current_db_url}")
        _repository = PumpRepository(config)
    elif _repository.config.database_url != current_db_url:
        logger.info(f"Repository: DATABASE_URL changed from {_repository.config.database_url} to {current_db_url}")
        logger.info(f"Repository: Forcing recreation of repository instance")
        _repository = PumpRepository(config)
    
    return _repository




def reload_pump_repository() -> bool:
    """Force reload of the global repository"""
    global _repository
    if _repository:
        return _repository.reload()
    return False

def clear_pump_repository() -> None:
    """Clear the global repository cache to force recreation"""
    global _repository
    logger.info("Repository: Clearing global repository cache")
    _repository = None

def load_all_pump_data() -> List[Dict[str, Any]]:
    """Load and parse pump database into a list of pump data dictionaries."""
    try:
        # Use repository for data loading
        repository = get_pump_repository()
        catalog_data = repository.get_catalog_data()
        pump_models = catalog_data.get('pump_models', [])
        
        # Convert to simple dictionary format for compatibility
        pump_data_list = []
        for pump_model in pump_models:
            for curve in pump_model.get('curves', []):
                pump_data = {
                    'pump_code': pump_model['pump_code'],
                    'manufacturer': pump_model['manufacturer'],
                    'model': pump_model['pump_code'],
                    'series': pump_model['model_series'],
                    'pump_type': pump_model['pump_type'],
                    'test_speed_rpm': curve['test_speed_rpm'],
                    'max_flow_m3hr': pump_model['specifications'].get('max_flow_m3hr', 0),
                    'max_head_m': pump_model['specifications'].get('max_head_m', 0),
                    'impeller_diameter_mm': curve['impeller_diameter_mm'],
                    'performance_points': curve['performance_points']
                }
                pump_data_list.append(pump_data)

        logger.info(f"Repository: Loaded {len(pump_data_list)} pump curves for compatibility")
        return pump_data_list

    except Exception as e:
        logger.error(f"Repository: Error loading pump data: {e}")
        return []


 