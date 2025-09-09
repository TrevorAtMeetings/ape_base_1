"""
Pump Repository Loader Module
==============================
PostgreSQL data loading and transformation
"""

import os
import logging
from typing import Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import numpy as np
from psycopg2.extras import RealDictCursor
from .utils_impeller import compute_impeller_min_max_from_curves

logger = logging.getLogger(__name__)


class PostgreSQLLoader:
    """Handles PostgreSQL data loading and transformation for the pump repository"""
    
    def __init__(self, repository):
        """
        Initialize loader with reference to parent repository.
        
        Args:
            repository: Parent PumpRepository instance
        """
        self.repository = repository
        self.config = repository.config
    
    def load_from_postgresql_optimized(self) -> bool:
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

            with self.repository._get_connection() as conn:
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

                    # FIXED: Get all curves and their performance data (don't filter out curves without points)
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
                    
                    # Load available diameters from pump_diameters table  
                    cursor.execute("""
                        SELECT 
                            p.pump_code,
                            pd.diameter_value
                        FROM pumps p
                        JOIN pump_diameters pd ON p.id = pd.pump_id
                        WHERE pd.diameter_value > 0
                        ORDER BY p.pump_code, pd.diameter_value
                    """)
                    
                    diameter_data = cursor.fetchall()
                    
                    # Group diameters by pump code
                    diameters_by_pump = {}
                    for row in diameter_data:
                        pump_code = row['pump_code']
                        if pump_code not in diameters_by_pump:
                            diameters_by_pump[pump_code] = []
                        diameters_by_pump[pump_code].append(float(row['diameter_value']))

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

                        # Add performance point if it exists and has valid flow data
                        if (row['operating_point'] is not None and 
                            row['flow_m3hr'] is not None and 
                            float(row['flow_m3hr']) > 0):
                            curves_by_pump[pump_code][curve_id]['performance_points'].append({
                                'flow_m3hr': float(row['flow_m3hr']),
                                'head_m': float(row['head_m']) if row['head_m'] is not None else 0.0,
                                'efficiency_pct': float(row['efficiency_pct']) if row['efficiency_pct'] is not None else 0.0,
                                'power_kw': None,  # Will be populated by Brain performance analysis
                                'npshr_m': float(row['npshr_m']) if row['npshr_m'] is not None else None
                            })

                    # Build pump models with optimized data processing
                    total_curves = 0
                    total_points = 0
                    npsh_curves = 0

                    for pump_row in pump_stats_data:
                        pump_row_dict = dict(pump_row)
                        pump_code = pump_row_dict['pump_code']

                        # Get curves for this pump - ensure we process ALL pumps, not just those with performance data
                        pump_curves = curves_by_pump.get(pump_code, {})
                        curves = []
                        
                        # Get available diameters for this pump from pump_diameters table
                        available_diameters = diameters_by_pump.get(pump_code, [])
                        
                        # Log pump processing for debugging
                        logger.debug(f"Repository: Processing pump {pump_code} with {len(pump_curves)} curves")

                        # CRITICAL FIX: Sort curves by impeller diameter (largest first)
                        # This ensures the maximum impeller curve (containing design BEP) is processed first
                        sorted_curves = sorted(
                            pump_curves.items(), 
                            key=lambda x: float(x[1]['impeller_diameter_mm']), 
                            reverse=True
                        )

                        for curve_id, curve_data in sorted_curves:
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

                        # ENHANCED FIX: Use available diameters first, then curve derivation, then specifications
                        if available_diameters:
                            min_mm, max_mm = min(available_diameters), max(available_diameters)
                            logger.debug(f"Repository: Using available diameters for {pump_code}: {min_mm}-{max_mm}mm")
                        else:
                            # Fallback to curve derivation
                            min_mm, max_mm = compute_impeller_min_max_from_curves(curves)
                            
                            # Fallback to specification data if curve derivation fails
                            if not (min_mm and max_mm):
                                spec_min = pump_row_dict.get('min_impeller_diameter_mm')
                                spec_max = pump_row_dict.get('max_impeller_diameter_mm')
                                
                                if spec_min and spec_max:
                                    min_mm, max_mm = float(spec_min), float(spec_max)
                                    logger.debug(f"Repository: Using specification min/max impeller for {pump_code}: {min_mm}-{max_mm}mm")
                                else:
                                    logger.error(f"Repository: Could not derive min/max impeller for {pump_code} from curves or specifications.")
                                    # Ensure keys exist even for edge cases
                                    min_mm, max_mm = 0.0, 0.0

                        # Build pump model object using aggregated statistics

                        pump_model = {
                            'pump_code': pump_code,
                            'pump_id': pump_row_dict.get('id'),  # Include pump_id for BEP markers
                            'manufacturer': pump_row_dict.get('manufacturer', 'APE PUMPS'),
                            'pump_type': pump_row_dict.get('pump_type', 'END SUCTION'),
                            'model_series': pump_row_dict.get('model_series', ''),
                            'specifications': {
                                'max_flow_m3hr': float(pump_row_dict.get('max_flow_m3hr', 0)) if pump_row_dict.get('max_flow_m3hr') is not None else 0,
                                'max_head_m': float(pump_row_dict.get('max_head_m', 0)) if pump_row_dict.get('max_head_m') is not None else 0,
                                # CRITICAL FIX: Use curve-derived min/max instead of potentially stale database values
                                'min_impeller_diameter_mm': float(min_mm) if min_mm is not None else 0,
                                'max_impeller_diameter_mm': float(max_mm) if max_mm is not None else 0,
                                'test_speed_rpm': int(pump_row_dict.get('test_speed_rpm', 0)) if pump_row_dict.get('test_speed_rpm') is not None else 0,
                                'min_speed_rpm': int(pump_row_dict.get('min_speed_rpm', 0)) if pump_row_dict.get('min_speed_rpm') is not None else 0,
                                'max_speed_rpm': int(pump_row_dict.get('max_speed_rpm', 0)) if pump_row_dict.get('max_speed_rpm') is not None else 0,
                                # CRITICAL: Add BEP data from database specifications (authentic manufacturer data)
                                'bep_flow_m3hr': float(pump_row_dict.get('bep_flow_m3hr')) if pump_row_dict.get('bep_flow_m3hr') is not None else None,
                                'bep_head_m': float(pump_row_dict.get('bep_head_m')) if pump_row_dict.get('bep_head_m') is not None else None,
                                'npshr_at_bep': float(pump_row_dict.get('npshr_at_bep')) if pump_row_dict.get('npshr_at_bep') is not None else None,
                                # THREE-PATH SELECTION LOGIC FLAGS: Variable speed and diameter capabilities
                                'variable_speed': bool(pump_row_dict.get('variable_speed', False)),
                                'variable_diameter': bool(pump_row_dict.get('variable_diameter', True))
                            },
                            'curves': curves,
                            # Add available diameters from pump_diameters table
                            'available_diameters': available_diameters,
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
                    self.repository._catalog_data = {
                        'metadata': metadata,
                        'pump_models': pump_models
                    }

                    self.repository._metadata = metadata
                    self.repository._pump_models = pump_models
                    self.repository._is_loaded = True

                    logger.info(f"Repository: Successfully loaded {len(pump_models)} pump models from PostgreSQL")
                    logger.info(f"Repository: Total curves: {total_curves}")
                    logger.info(f"Repository: Total points: {total_points}")
                    logger.info(f"Repository: NPSH curves: {npsh_curves}")
                    logger.info(f"Repository: Tables used: {list(tables.keys())}")

                    return True

        except Exception as e:
            import traceback
            logger.error(f"Repository: Error loading from PostgreSQL: {e}")
            logger.error(f"Repository: Traceback: {traceback.format_exc()}")
            return False