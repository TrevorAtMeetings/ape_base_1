"""
Service layer for admin configuration system
"""
import logging
from typing import Dict, List, Optional, Tuple
from app.database import admin_db
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import psycopg2

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""
    pass


class ConfigurationError(Exception):
    """Custom configuration error"""
    pass


class AdminConfigService:
    """Service for managing admin configurations"""
    
    def __init__(self):
        self.db = admin_db
        self._config_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes

    def initialize_database(self) -> tuple[bool, str]:
        """Create admin schema/tables and seed constants and default profiles."""
        try:
            # Create schema and tables
            self.db.init_tables()
            # Seed locked engineering constants
            self.db.seed_engineering_constants()
            # Seed default configuration profiles
            self.db.seed_default_profiles()
            # Clear any stale cache
            self._config_cache.clear()
            self._cache_timestamp = None
            logger.info("Admin configuration database initialized and seeded successfully")
            return True, "Database initialized and seeded successfully"
        except Exception as e:
            logger.error(f"Failed to initialize admin configuration database: {e}", exc_info=True)
            return False, str(e)
    
    def get_active_profile(self, profile_name: str = 'General Purpose') -> Dict:
        """Get active configuration profile with caching"""
        cache_key = f"profile_{profile_name}"
        
        # Check cache
        if (self._cache_timestamp and 
            (datetime.utcnow() - self._cache_timestamp).seconds < self._cache_ttl and
            cache_key in self._config_cache):
            return self._config_cache[cache_key]
        
        # Load from database
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM admin_config.application_profiles
                    WHERE name = %s AND is_active = TRUE
                    LIMIT 1
                """, (profile_name,))
                
                profile = cursor.fetchone()
                
                if not profile:
                    # Return default configuration if profile not found
                    logger.warning(f"Profile '{profile_name}' not found, using defaults")
                    return self._get_default_config()
                
                # Convert to dictionary format
                config = {
                    'id': profile['id'],
                    'name': profile['name'],
                    'description': profile['description'],
                    'scoring_weights': {
                        'bep': profile['bep_weight'],
                        'efficiency': profile['efficiency_weight'],
                        'head_margin': profile['head_margin_weight'],
                        'npsh': profile['npsh_weight']
                    },
                    'zones': {
                        'bep_optimal': (profile['bep_optimal_min'], profile['bep_optimal_max']),
                        'efficiency_thresholds': {
                            'minimum': profile['min_acceptable_efficiency'],
                            'fair': profile['fair_efficiency'],
                            'good': profile['good_efficiency'],
                            'excellent': profile['excellent_efficiency']
                        },
                        'head_margin': {
                            'optimal_max': profile['optimal_head_margin_max'],
                            'acceptable_max': profile['acceptable_head_margin_max']
                        },
                        'npsh_margins': {
                            'excellent': profile['npsh_excellent_margin'],
                            'good': profile['npsh_good_margin'],
                            'minimum': profile['npsh_minimum_margin']
                        }
                    },
                    'modifications': {
                        'speed_penalty': profile['speed_variation_penalty_factor'],
                        'trim_penalty': profile['trimming_penalty_factor'],
                        'max_trim_pct': profile['max_acceptable_trim_pct']
                    },
                    'reporting': {
                        'top_threshold': profile['top_recommendation_threshold'],
                        'acceptable_threshold': profile['acceptable_option_threshold'],
                        'near_miss_count': profile['near_miss_count']
                    }
                }
                
                # Update cache
                self._config_cache[cache_key] = config
                self._cache_timestamp = datetime.utcnow()
                
                return config
    
    def _get_default_config(self) -> Dict:
        """Get default configuration values"""
        return {
            'id': 0,
            'name': 'Default',
            'description': 'Default configuration',
            'scoring_weights': {
                'bep': 40.0,
                'efficiency': 30.0,
                'head_margin': 15.0,
                'npsh': 15.0
            },
            'zones': {
                'bep_optimal': (0.95, 1.05),
                'efficiency_thresholds': {
                    'minimum': 40.0,
                    'fair': 65.0,
                    'good': 75.0,
                    'excellent': 85.0
                },
                'head_margin': {
                    'optimal_max': 5.0,
                    'acceptable_max': 10.0
                },
                'npsh_margins': {
                    'excellent': 3.0,
                    'good': 1.5,
                    'minimum': 0.5
                }
            },
            'modifications': {
                'speed_penalty': 15.0,
                'trim_penalty': 10.0,
                'max_trim_pct': 75.0
            },
            'reporting': {
                'top_threshold': 70.0,
                'acceptable_threshold': 50.0,
                'near_miss_count': 5
            }
        }
    
    def validate_profile_data(self, profile_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate profile configuration data
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Validate scoring weights
            weights = profile_data.get('scoring_weights', {})
            total_weight = sum([
                float(weights.get('bep', 0)),
                float(weights.get('efficiency', 0)),
                float(weights.get('head_margin', 0)),
                float(weights.get('npsh', 0))
            ])
            
            if abs(total_weight - 100.0) > 0.1:
                errors.append(f"Scoring weights must total 100.0, got {total_weight}")
            
            # Validate individual weight ranges
            for weight_name, weight_value in weights.items():
                weight_val = float(weight_value)
                if not (0 <= weight_val <= 100):
                    errors.append(f"{weight_name} weight must be between 0-100, got {weight_val}")
            
            # Validate efficiency thresholds
            efficiency = profile_data.get('zones', {}).get('efficiency_thresholds', {})
            thresholds = [
                ('minimum', efficiency.get('minimum', 0)),
                ('fair', efficiency.get('fair', 0)),
                ('good', efficiency.get('good', 0)),
                ('excellent', efficiency.get('excellent', 0))
            ]
            
            prev_val = 0
            for name, val in thresholds:
                if not (0 <= float(val) <= 100):
                    errors.append(f"Efficiency {name} must be 0-100%, got {val}")
                if float(val) <= prev_val:
                    errors.append(f"Efficiency {name} ({val}%) must be > previous threshold ({prev_val}%)")
                prev_val = float(val)
            
            # Validate BEP range
            bep_range = profile_data.get('zones', {}).get('bep_optimal', (0.95, 1.05))
            if len(bep_range) != 2 or bep_range[0] >= bep_range[1]:
                errors.append("BEP optimal range must have min < max")
            
            # Validate NPSH margins
            npsh = profile_data.get('zones', {}).get('npsh_margins', {})
            npsh_vals = [
                ('minimum', npsh.get('minimum', 0.5)),
                ('good', npsh.get('good', 1.5)),
                ('excellent', npsh.get('excellent', 3.0))
            ]
            
            prev_val = 0
            for name, val in npsh_vals:
                if float(val) <= prev_val:
                    errors.append(f"NPSH {name} margin ({val}m) must be > previous ({prev_val}m)")
                prev_val = float(val)
            
        except (ValueError, TypeError, KeyError) as e:
            errors.append(f"Data validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def update_profile(self, profile_id: int, profile_data: Dict, user_id: str = "system") -> Tuple[bool, str]:
        """
        Update profile with validation and audit logging
        Returns: (success, message)
        """
        # Validate input data
        is_valid, errors = self.validate_profile_data(profile_data)
        if not is_valid:
            return False, f"Validation failed: {'; '.join(errors)}"
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Start transaction
                    cursor.execute("BEGIN")
                    
                    # Get current profile for audit
                    cursor.execute("""
                        SELECT name, bep_weight, efficiency_weight, head_margin_weight, npsh_weight 
                        FROM admin_config.application_profiles 
                        WHERE id = %s
                    """, (profile_id,))
                    
                    old_profile = cursor.fetchone()
                    if not old_profile:
                        cursor.execute("ROLLBACK")
                        return False, "Profile not found"
                    
                    # Update profile
                    weights = profile_data.get('scoring_weights', {})
                    zones = profile_data.get('zones', {})
                    efficiency = zones.get('efficiency_thresholds', {})
                    head_margin = zones.get('head_margin', {})
                    npsh_margins = zones.get('npsh_margins', {})
                    modifications = profile_data.get('modifications', {})
                    reporting = profile_data.get('reporting', {})
                    bep_optimal = zones.get('bep_optimal', (0.95, 1.05))
                    
                    cursor.execute("""
                        UPDATE admin_config.application_profiles SET
                            bep_weight = %s,
                            efficiency_weight = %s,
                            head_margin_weight = %s,
                            npsh_weight = %s,
                            bep_optimal_min = %s,
                            bep_optimal_max = %s,
                            min_acceptable_efficiency = %s,
                            fair_efficiency = %s,
                            good_efficiency = %s,
                            excellent_efficiency = %s,
                            optimal_head_margin_max = %s,
                            acceptable_head_margin_max = %s,
                            npsh_minimum_margin = %s,
                            npsh_good_margin = %s,
                            npsh_excellent_margin = %s,
                            speed_variation_penalty_factor = %s,
                            trimming_penalty_factor = %s,
                            max_acceptable_trim_pct = %s,
                            top_recommendation_threshold = %s,
                            acceptable_option_threshold = %s,
                            near_miss_count = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (
                        weights.get('bep', 40.0),
                        weights.get('efficiency', 30.0),
                        weights.get('head_margin', 15.0),
                        weights.get('npsh', 15.0),
                        bep_optimal[0],
                        bep_optimal[1],
                        efficiency.get('minimum', 40.0),
                        efficiency.get('fair', 65.0),
                        efficiency.get('good', 75.0),
                        efficiency.get('excellent', 85.0),
                        head_margin.get('optimal_max', 5.0),
                        head_margin.get('acceptable_max', 10.0),
                        npsh_margins.get('minimum', 0.5),
                        npsh_margins.get('good', 1.5),
                        npsh_margins.get('excellent', 3.0),
                        modifications.get('speed_penalty', 15.0),
                        modifications.get('trim_penalty', 10.0),
                        modifications.get('max_trim_pct', 75.0),
                        reporting.get('top_threshold', 70.0),
                        reporting.get('acceptable_threshold', 50.0),
                        reporting.get('near_miss_count', 5),
                        profile_id
                    ))
                    
                    # Add audit log
                    changes = []
                    if weights.get('bep') != old_profile['bep_weight']:
                        changes.append(f"BEP weight: {old_profile['bep_weight']} → {weights.get('bep')}")
                    if weights.get('efficiency') != old_profile['efficiency_weight']:
                        changes.append(f"Efficiency weight: {old_profile['efficiency_weight']} → {weights.get('efficiency')}")
                    
                    if changes:
                        cursor.execute("""
                            INSERT INTO admin_config.audit_log (
                                profile_id, action, user_id, changes, timestamp
                            ) VALUES (%s, %s, %s, %s, NOW())
                        """, (profile_id, 'update', user_id, '; '.join(changes)))
                    
                    cursor.execute("COMMIT")
                    
                    # Clear cache
                    self._config_cache.clear()
                    self._cache_timestamp = None
                    
                    logger.info(f"Profile {profile_id} updated by {user_id}: {len(changes)} changes")
                    return True, "Profile updated successfully"
                    
        except psycopg2.Error as e:
            logger.error(f"Database error updating profile {profile_id}: {e}")
            return False, f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error updating profile {profile_id}: {e}")
            return False, f"Unexpected error: {str(e)}"
    
    def get_all_profiles(self) -> List[Dict]:
        """Get all configuration profiles"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, description, is_active, created_at, updated_at
                    FROM admin_config.application_profiles
                    ORDER BY name
                """)
                
                return [dict(row) for row in cursor.fetchall()]
    
    def get_profile_by_id(self, profile_id: int) -> Optional[Dict]:
        """Get specific profile by ID"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM admin_config.application_profiles
                    WHERE id = %s
                """, (profile_id,))
                
                profile = cursor.fetchone()
                if not profile:
                    return None
                
                # Convert to expected format
                return {
                    'id': profile['id'],
                    'name': profile['name'],
                    'description': profile['description'],
                    'is_active': profile['is_active'],
                    'scoring_weights': {
                        'bep': profile['bep_weight'],
                        'efficiency': profile['efficiency_weight'],
                        'head_margin': profile['head_margin_weight'],
                        'npsh': profile['npsh_weight']
                    },
                    'zones': {
                        'bep_optimal': (profile['bep_optimal_min'], profile['bep_optimal_max']),
                        'efficiency_thresholds': {
                            'minimum': profile['min_acceptable_efficiency'],
                            'fair': profile['fair_efficiency'],
                            'good': profile['good_efficiency'],
                            'excellent': profile['excellent_efficiency']
                        },
                        'npsh_margins': {
                            'excellent': profile['npsh_excellent_margin'],
                            'good': profile['npsh_good_margin'],
                            'minimum': profile['npsh_minimum_margin']
                        }
                    }
                }
    
    def get_engineering_constants(self) -> List[Dict]:
        """Get all locked engineering constants"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM admin_config.engineering_constants
                    ORDER BY name
                """)
                
                return [dict(row) for row in cursor.fetchall()]
    
    def get_calibration_factors(self) -> Dict[str, float]:
        """
        Get BEP migration calibration factors from engineering constants.
        These factors control the physics model for impeller trimming effects.
        
        Returns:
            Dict with calibration factors for BEP migration calculations
        """
        cache_key = "calibration_factors"
        
        # Check cache first
        if (self._cache_timestamp and 
            (datetime.utcnow() - self._cache_timestamp).seconds < self._cache_ttl and
            cache_key in self._config_cache):
            return self._config_cache[cache_key]
        
        # Load from database
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT name, value FROM admin_config.engineering_constants
                    WHERE category = 'BEP Migration' 
                    ORDER BY name
                """)
                
                constants = cursor.fetchall()
                
                # Convert to calibration factors dictionary
                calibration_factors = {}
                for constant in constants:
                    try:
                        calibration_factors[constant['name']] = float(constant['value'])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid calibration factor value for {constant['name']}: {constant['value']}")
                        # Use safe defaults if database value is invalid
                        if constant['name'] == 'bep_shift_flow_exponent':
                            calibration_factors[constant['name']] = 1.2
                        elif constant['name'] == 'bep_shift_head_exponent':
                            calibration_factors[constant['name']] = 2.2
                        elif constant['name'] == 'efficiency_correction_exponent':
                            calibration_factors[constant['name']] = 0.1
                
                # Ensure all required factors are present with safe defaults
                defaults = {
                    'bep_shift_flow_exponent': 1.2,
                    'bep_shift_head_exponent': 2.2,
                    'efficiency_correction_exponent': 0.1,
                    'trim_dependent_small_exponent': 2.9,
                    'trim_dependent_large_exponent': 2.1,
                    'efficiency_penalty_volute': 0.20,
                    'efficiency_penalty_diffuser': 0.45,
                    'npsh_degradation_threshold': 10.0,
                    'npsh_degradation_factor': 1.15
                }
                
                for key, default_value in defaults.items():
                    if key not in calibration_factors:
                        logger.warning(f"Missing calibration factor {key}, using default {default_value}")
                        calibration_factors[key] = default_value
                
                # Cache the result
                self._config_cache[cache_key] = calibration_factors
                self._cache_timestamp = datetime.utcnow()
                
                logger.debug(f"Loaded calibration factors: {calibration_factors}")
                return calibration_factors
    

    
    def create_profile(self, profile_data: Dict, user: str) -> Optional[int]:
        """Create a new configuration profile"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert the new profile
                    cursor.execute("""
                        INSERT INTO admin_config.application_profiles
                        (name, description, bep_weight, efficiency_weight, head_margin_weight, 
                         npsh_weight, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        profile_data['name'],
                        profile_data.get('description', ''),
                        profile_data.get('bep_weight', 40.0),
                        profile_data.get('efficiency_weight', 30.0),
                        profile_data.get('head_margin_weight', 15.0),
                        profile_data.get('npsh_weight', 15.0),
                        user
                    ))
                    
                    result = cursor.fetchone()
                    if not result:
                        logger.error("Failed to create profile: No ID returned")
                        return None
                    profile_id = result[0]
                    
                    # Log creation
                    cursor.execute("""
                        INSERT INTO admin_config.configuration_audits
                        (profile_id, changed_by, change_type, reason)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        profile_id,
                        user,
                        'create',
                        'Profile created'
                    ))
                    
                    conn.commit()
                    return profile_id
                    
        except Exception as e:
            logger.error(f"Failed to create profile: {e}")
            return None
    
    def get_audit_log(self, profile_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get audit log entries"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if profile_id:
                    cursor.execute("""
                        SELECT a.*, p.name as profile_name
                        FROM admin_config.configuration_audits a
                        JOIN admin_config.application_profiles p ON a.profile_id = p.id
                        WHERE a.profile_id = %s
                        ORDER BY a.timestamp DESC
                        LIMIT %s
                    """, (profile_id, limit))
                else:
                    cursor.execute("""
                        SELECT a.*, p.name as profile_name
                        FROM admin_config.configuration_audits a
                        JOIN admin_config.application_profiles p ON a.profile_id = p.id
                        ORDER BY a.timestamp DESC
                        LIMIT %s
                    """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
    
    def clear_cache(self):
        """Clear the configuration cache"""
        self._config_cache.clear()
        self._cache_timestamp = None
        logger.info("Configuration cache cleared")


# Create global instance
admin_config_service = AdminConfigService()