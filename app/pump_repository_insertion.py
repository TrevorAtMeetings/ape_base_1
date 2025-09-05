"""
Pump Repository Insertion Module
=================================
Data insertion logic for pump data extracted from Gemini
"""

import os
import logging
from decimal import Decimal
import psycopg2
from .pump_repository_core import PumpRepositoryConfig, PumpRepository

logger = logging.getLogger(__name__)


def insert_extracted_pump_data(data: dict, filename: str = None) -> int:
    """
    Insert extracted pump data (from Gemini) into the database.
    Returns the inserted pump ID.
    """
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
        """Convert value to number or return None if conversion fails"""
        if value is None or value == '' or value == 'None' or value == 'null':
            return None
        try:
            # Handle string representations
            if isinstance(value, str):
                value = value.strip()
                if value == '' or value.lower() in ['none', 'null', 'n/a', 'na']:
                    return None

            # Convert to float
            result = float(value)

            # Log problematic zero values for debugging
            if result == 0.0 and str(value) != '0' and str(value) != '0.0':
                logger.debug(f"[PumpRepo] Converting '{value}' to 0.0 - this might indicate a data issue")

            return result
        except (ValueError, TypeError) as e:
            logger.debug(f"[PumpRepo] Failed to convert '{value}' to number: {e}")
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

                # Store BEP markers if available
                if 'bepMarkers' in specs and specs['bepMarkers']:
                    logger.info(f"[PumpRepo] Storing {len(specs['bepMarkers'])} BEP markers for pump {pump_id}")
                    for marker in specs['bepMarkers']:
                        efficiency = marker.get('bepEfficiency', 0)
                        flow = marker.get('bepFlow', 0)
                        head = marker.get('bepHead', 0)

                        logger.info(f"[PumpRepo] BEP Marker: Efficiency={efficiency}%, Flow={flow}, Head={head}")

                        cur.execute("""
                            INSERT INTO pump_bep_markers (
                                pump_id, impeller_diameter, bep_flow, bep_head, 
                                bep_efficiency, marker_label, coordinate_x, coordinate_y
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            pump_id,
                            marker.get('impellerDiameter', 0),
                            flow,
                            head,
                            efficiency,
                            marker.get('markerLabel', ''),
                            marker.get('coordinates', {}).get('x', 0),
                            marker.get('coordinates', {}).get('y', 0)
                        ))

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
                            # NEW STRUCTURE: performance points array
                            logger.info(f"[PumpRepo] Using NEW structure: performancePoints array with {len(performance_points)} points")
                            points_inserted = 0
                            for j, point in enumerate(performance_points):
                                # Handle multiple possible field names for flow
                                flow_rate = to_number_or_none(point.get('flow') or point.get('flow_m3hr') or point.get('flowRate'))
                                # Handle multiple possible field names for head
                                head = to_number_or_none(point.get('head') or point.get('head_m') or point.get('headM'))
                                # Handle multiple possible field names for efficiency
                                efficiency = to_number_or_none(point.get('efficiency') or point.get('efficiency_pct') or point.get('eff'))
                                # Handle multiple possible field names for NPSH
                                npshr = to_number_or_none(point.get('npshr') or point.get('npshr_m') or point.get('npsh'))

                                logger.debug(f"[PumpRepo] Point {j+1}: Flow={flow_rate}, Head={head}, Eff={efficiency}, NPSH={npshr}")

                                if flow_rate is not None and head is not None:
                                    cur.execute(
                                        "INSERT INTO pump_performance_points (curve_id, operating_point, flow_rate, head, efficiency, npshr) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (curve_id, operating_point) DO NOTHING",
                                        (curve_id, j + 1, flow_rate, head, efficiency, npshr)
                                    )
                                    points_inserted += 1
                                else:
                                    logger.warning(f"[PumpRepo] Skipping point {j+1} - missing flow or head data")

                            logger.info(f"[PumpRepo] Inserted {points_inserted} performance points for curve {i+1} (NEW structure)")

                        else:
                            # OLD STRUCTURE: separate arrays
                            logger.info(f"[PumpRepo] Using OLD structure: separate arrays")

                            flows = curve.get('flow', [])
                            heads = curve.get('head', [])
                            efficiencies = curve.get('efficiency', [])
                            npshrs = curve.get('npsh', [])
                            powers = curve.get('power', [])

                            # Iterate through each set of values and insert
                            points_inserted = 0
                            for j in range(min(len(flows), len(heads))):  # Iterate only as far as the shortest list
                                flow_rate = to_number_or_none(flows[j])
                                head = to_number_or_none(heads[j])
                                efficiency = to_number_or_none(efficiencies[j] if len(efficiencies) > j else None)
                                npshr = to_number_or_none(npshrs[j] if len(npshrs) > j else None)

                                logger.debug(f"[PumpRepo] Point {j+1}: Flow={flow_rate}, Head={head}, Eff={efficiency}, NPSH={npshr}")

                                if flow_rate is not None and head is not None:
                                    cur.execute(
                                        "INSERT INTO pump_performance_points (curve_id, operating_point, flow_rate, head, efficiency, npshr) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (curve_id, operating_point) DO NOTHING",
                                        (curve_id, j + 1, flow_rate, head, efficiency, npshr)
                                    )
                                    points_inserted += 1
                                else:
                                    logger.warning(f"[PumpRepo] Skipping point {j+1} - missing flow or head data")

                            logger.info(f"[PumpRepo] Inserted {points_inserted} performance points for curve {i+1} (OLD structure)")
                        conn.commit()  # Commit after each curve is processed

                logger.info("[PumpRepo] Committing remaining changes to the database")
                conn.commit()

                logger.info("[PumpRepo] ===== DATABASE INSERTION COMPLETED =====")
                return pump_id

        except psycopg2.Error as e:
            logger.error(f"[PumpRepo] PostgreSQL error during insertion: {e}")
            conn.rollback()
            return None
        except Exception as e:
            logger.error(f"[PumpRepo] Generic error during insertion: {e}")
            conn.rollback()
            return None
        finally:
            if conn:
                conn.commit()
                cur.close()
                pool.putconn(conn)
                logger.info("[PumpRepo] Connection closed")