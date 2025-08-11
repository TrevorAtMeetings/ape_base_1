"""
Database configuration for admin config system
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class AdminConfigDB:
    """Database handler for admin configuration system"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not configured")
    
    @contextmanager
    def get_connection(self):
        """Get database connection"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_tables(self):
        """Initialize admin configuration tables in separate schema"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Create separate schema for admin configuration
                cursor.execute("""
                    CREATE SCHEMA IF NOT EXISTS admin_config;
                """)
                
                # Create application profiles table in admin_config schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_config.application_profiles (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        description TEXT,
                        
                        -- Scoring weights (must total 100)
                        bep_weight FLOAT NOT NULL DEFAULT 40.0,
                        efficiency_weight FLOAT NOT NULL DEFAULT 30.0,
                        head_margin_weight FLOAT NOT NULL DEFAULT 15.0,
                        npsh_weight FLOAT NOT NULL DEFAULT 15.0,
                        
                        -- Zone boundaries
                        bep_optimal_min FLOAT NOT NULL DEFAULT 0.95,
                        bep_optimal_max FLOAT NOT NULL DEFAULT 1.05,
                        
                        -- Efficiency thresholds
                        min_acceptable_efficiency FLOAT NOT NULL DEFAULT 40.0,
                        excellent_efficiency FLOAT NOT NULL DEFAULT 85.0,
                        good_efficiency FLOAT NOT NULL DEFAULT 75.0,
                        fair_efficiency FLOAT NOT NULL DEFAULT 65.0,
                        
                        -- Head margin preferences
                        optimal_head_margin_max FLOAT NOT NULL DEFAULT 5.0,
                        acceptable_head_margin_max FLOAT NOT NULL DEFAULT 10.0,
                        
                        -- NPSH safety factors
                        npsh_excellent_margin FLOAT NOT NULL DEFAULT 3.0,
                        npsh_good_margin FLOAT NOT NULL DEFAULT 1.5,
                        npsh_minimum_margin FLOAT NOT NULL DEFAULT 0.5,
                        
                        -- Modification preferences
                        speed_variation_penalty_factor FLOAT NOT NULL DEFAULT 15.0,
                        trimming_penalty_factor FLOAT NOT NULL DEFAULT 10.0,
                        max_acceptable_trim_pct FLOAT NOT NULL DEFAULT 75.0,
                        
                        -- Reporting preferences
                        top_recommendation_threshold FLOAT NOT NULL DEFAULT 70.0,
                        acceptable_option_threshold FLOAT NOT NULL DEFAULT 50.0,
                        near_miss_count INTEGER NOT NULL DEFAULT 5,
                        
                        -- Metadata
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by VARCHAR(100),
                        
                        -- Constraints
                        CONSTRAINT weights_total_100 CHECK (
                            ABS((bep_weight + efficiency_weight + head_margin_weight + npsh_weight) - 100.0) < 0.01
                        )
                    )
                """)
                
                # Create locked engineering constants table in admin_config schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_config.engineering_constants (
                        id SERIAL PRIMARY KEY,
                        category VARCHAR(50) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        value VARCHAR(200) NOT NULL,
                        unit VARCHAR(50),
                        description TEXT,
                        formula TEXT,
                        is_locked BOOLEAN DEFAULT TRUE NOT NULL,
                        
                        UNIQUE(category, name)
                    )
                """)
                
                # Create configuration audit table in admin_config schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_config.configuration_audits (
                        id SERIAL PRIMARY KEY,
                        profile_id INTEGER REFERENCES admin_config.application_profiles(id),
                        changed_by VARCHAR(100) NOT NULL,
                        change_type VARCHAR(50) NOT NULL,
                        field_name VARCHAR(100),
                        old_value VARCHAR(200),
                        new_value VARCHAR(200),
                        reason TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create trigger to update updated_at timestamp
                cursor.execute("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """)
                
                cursor.execute("""
                    DROP TRIGGER IF EXISTS update_application_profiles_updated_at ON admin_config.application_profiles;
                    CREATE TRIGGER update_application_profiles_updated_at 
                    BEFORE UPDATE ON admin_config.application_profiles 
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                """)
                
                conn.commit()
                logger.info("Admin configuration tables initialized successfully")
    
    def seed_engineering_constants(self):
        """Seed the locked engineering constants"""
        constants = [
            # Affinity Laws
            {
                'category': 'Affinity Laws',
                'name': 'Flow vs Speed',
                'value': 'Q2 = Q1 × (N2/N1)',
                'unit': None,
                'description': 'Flow rate varies directly with speed',
                'formula': 'Q2 = Q1 × (N2/N1)'
            },
            {
                'category': 'Affinity Laws',
                'name': 'Head vs Speed',
                'value': 'H2 = H1 × (N2/N1)²',
                'unit': None,
                'description': 'Head varies with the square of speed',
                'formula': 'H2 = H1 × (N2/N1)²'
            },
            {
                'category': 'Affinity Laws',
                'name': 'Power vs Speed',
                'value': 'P2 = P1 × (N2/N1)³',
                'unit': None,
                'description': 'Power varies with the cube of speed',
                'formula': 'P2 = P1 × (N2/N1)³'
            },
            
            # Impeller Trimming Laws
            {
                'category': 'Impeller Trimming',
                'name': 'Flow vs Diameter',
                'value': 'Q2 = Q1 × (D2/D1)',
                'unit': None,
                'description': 'Flow rate varies directly with impeller diameter',
                'formula': 'Q2 = Q1 × (D2/D1)'
            },
            {
                'category': 'Impeller Trimming',
                'name': 'Head vs Diameter',
                'value': 'H2 = H1 × (D2/D1)²',
                'unit': None,
                'description': 'Head varies with the square of impeller diameter',
                'formula': 'H2 = H1 × (D2/D1)²'
            },
            
            # BEP Migration (Research-Based Calibration Factors)
            {
                'category': 'BEP Migration',
                'name': 'bep_shift_flow_exponent',
                'value': '1.2',
                'unit': None,
                'description': 'Flow exponent for BEP migration calculations during impeller trimming',
                'formula': 'Q_shifted = Q_original × (D_trim/D_full)^exponent'
            },
            {
                'category': 'BEP Migration',
                'name': 'bep_shift_head_exponent',
                'value': '2.2',
                'unit': None,
                'description': 'Head exponent for BEP migration calculations during impeller trimming',
                'formula': 'H_shifted = H_original × (D_trim/D_full)^exponent'
            },
            {
                'category': 'BEP Migration',
                'name': 'efficiency_correction_exponent',
                'value': '0.1',
                'unit': None,
                'description': 'Efficiency correction factor for off-BEP operation penalties',
                'formula': 'η_penalty = (QBP - 110) × correction_exponent'
            },
            {
                'category': 'BEP Migration',
                'name': 'trim_dependent_small_exponent',
                'value': '2.9',
                'unit': None,
                'description': 'Enhanced affinity law exponent for small trims (<5%) - research-based',
                'formula': 'H2 = H1 × (D2/D1)^exponent for trims <5%'
            },
            {
                'category': 'BEP Migration',
                'name': 'trim_dependent_large_exponent',
                'value': '2.1',
                'unit': None,
                'description': 'Enhanced affinity law exponent for large trims (5-15%) - research-based',
                'formula': 'H2 = H1 × (D2/D1)^exponent for trims 5-15%'
            },
            {
                'category': 'BEP Migration',
                'name': 'efficiency_penalty_volute',
                'value': '0.20',
                'unit': None,
                'description': 'Efficiency penalty factor for volute pumps (research: 0.15-0.25)',
                'formula': 'Δη = factor × (1 - D_trim/D_full)'
            },
            {
                'category': 'BEP Migration',
                'name': 'efficiency_penalty_diffuser',
                'value': '0.45',
                'unit': None,
                'description': 'Efficiency penalty factor for diffuser pumps (research: 0.4-0.5)',
                'formula': 'Δη = factor × (1 - D_trim/D_full)'
            },
            {
                'category': 'BEP Migration',
                'name': 'npsh_degradation_threshold',
                'value': '10.0',
                'unit': '%',
                'description': 'Trim percentage above which NPSH degradation occurs (research: >10%)',
                'formula': 'NPSH penalty applies when trim > threshold'
            },
            {
                'category': 'BEP Migration',
                'name': 'npsh_degradation_factor',
                'value': '1.15',
                'unit': None,
                'description': 'NPSH multiplier for heavily trimmed impellers (research-based)',
                'formula': 'NPSH_required = NPSH_base × factor (for heavy trims)'
            },
            
            # Physical Limits
            {
                'category': 'Physical Limits',
                'name': 'Minimum Trim Percentage',
                'value': '75',
                'unit': '%',
                'description': 'Minimum allowable impeller trim percentage to maintain hydraulic efficiency',
                'formula': None
            },
            {
                'category': 'Physical Limits',
                'name': 'Maximum Trim Percentage',
                'value': '100',
                'unit': '%',
                'description': 'Maximum impeller size (full diameter)',
                'formula': None
            },
            {
                'category': 'Physical Limits',
                'name': 'Minimum Speed',
                'value': '600',
                'unit': 'RPM',
                'description': 'Minimum pump operating speed',
                'formula': None
            },
            {
                'category': 'Physical Limits',
                'name': 'Maximum Speed',
                'value': '3600',
                'unit': 'RPM',
                'description': 'Maximum pump operating speed',
                'formula': None
            },
            
            # NPSH Requirements
            {
                'category': 'NPSH',
                'name': 'Minimum Safety Margin',
                'value': '0.5',
                'unit': 'm',
                'description': 'Absolute minimum NPSH margin to prevent cavitation',
                'formula': 'NPSHa - NPSHr ≥ 0.5m'
            },
            
            # Interpolation
            {
                'category': 'Interpolation',
                'name': 'Method',
                'value': 'Quadratic/Cubic Spline',
                'unit': None,
                'description': 'Mathematical method for curve interpolation',
                'formula': None
            },
            {
                'category': 'Interpolation',
                'name': 'Maximum Extrapolation',
                'value': '15',
                'unit': '%',
                'description': 'Maximum allowable extrapolation beyond curve data points',
                'formula': None
            }
        ]
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for const in constants:
                    cursor.execute("""
                        INSERT INTO admin_config.engineering_constants 
                        (category, name, value, unit, description, formula, is_locked)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (category, name) DO NOTHING
                    """, (
                        const['category'],
                        const['name'],
                        const['value'],
                        const['unit'],
                        const['description'],
                        const['formula'],
                        True
                    ))
                conn.commit()
                logger.info("Engineering constants seeded successfully")
    
    def seed_default_profiles(self):
        """Seed default application profiles"""
        profiles = [
            {
                'name': 'General Purpose',
                'description': 'Balanced configuration for general pump applications',
                'bep_weight': 40.0,
                'efficiency_weight': 30.0,
                'head_margin_weight': 15.0,
                'npsh_weight': 15.0
            },
            {
                'name': 'Municipal Water Supply',
                'description': 'High reliability and efficiency for municipal water systems',
                'bep_weight': 35.0,
                'efficiency_weight': 35.0,
                'head_margin_weight': 15.0,
                'npsh_weight': 15.0,
                'npsh_excellent_margin': 3.5,
                'npsh_good_margin': 2.0
            },
            {
                'name': 'Industrial Process',
                'description': 'Tight tolerances and high efficiency for industrial processes',
                'bep_weight': 30.0,
                'efficiency_weight': 40.0,
                'head_margin_weight': 20.0,
                'npsh_weight': 10.0,
                'optimal_head_margin_max': 3.0,
                'acceptable_head_margin_max': 7.0
            },
            {
                'name': 'HVAC Systems',
                'description': 'Energy optimization for HVAC and cooling applications',
                'bep_weight': 30.0,
                'efficiency_weight': 45.0,
                'head_margin_weight': 15.0,
                'npsh_weight': 10.0,
                'excellent_efficiency': 80.0,
                'good_efficiency': 70.0
            },
            {
                'name': 'Fire Protection',
                'description': 'Maximum reliability with regulatory compliance',
                'bep_weight': 45.0,
                'efficiency_weight': 20.0,
                'head_margin_weight': 20.0,
                'npsh_weight': 15.0,
                'npsh_excellent_margin': 4.0,
                'speed_variation_penalty_factor': 20.0
            },
            {
                'name': 'Chemical Processing',
                'description': 'High safety margins for chemical applications',
                'bep_weight': 35.0,
                'efficiency_weight': 25.0,
                'head_margin_weight': 20.0,
                'npsh_weight': 20.0,
                'npsh_excellent_margin': 4.0,
                'npsh_good_margin': 2.5,
                'npsh_minimum_margin': 1.0
            }
        ]
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for profile in profiles:
                    # Build dynamic INSERT query based on provided fields
                    fields = list(profile.keys())
                    placeholders = ', '.join(['%s'] * len(fields))
                    field_names = ', '.join(fields)
                    
                    cursor.execute(f"""
                        INSERT INTO admin_config.application_profiles ({field_names})
                        VALUES ({placeholders})
                        ON CONFLICT (name) DO NOTHING
                    """, tuple(profile.values()))
                
                conn.commit()
                logger.info("Default application profiles seeded successfully")


# Initialize database on module load
admin_db = AdminConfigDB()