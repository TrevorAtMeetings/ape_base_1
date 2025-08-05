"""
Service layer for admin configuration system
"""
import logging
from typing import Dict, List, Optional
from app.database import admin_db
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class AdminConfigService:
    """Service for managing admin configurations"""
    
    def __init__(self):
        self.db = admin_db
        self._config_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes
    
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
    
    def get_all_profiles(self) -> List[Dict]:
        """Get all configuration profiles"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, description, is_active, created_at, updated_at
                    FROM admin_config.application_profiles
                    ORDER BY name
                """)
                
                return cursor.fetchall()
    
    def get_engineering_constants(self) -> List[Dict]:
        """Get all locked engineering constants"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM admin_config.engineering_constants
                    ORDER BY category, name
                """)
                
                return cursor.fetchall()
    
    def update_profile(self, profile_id: int, updates: Dict, user: str, reason: str = None) -> bool:
        """Update a configuration profile with audit logging"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get current values for audit
                    cursor.execute("""
                        SELECT * FROM admin_config.application_profiles
                        WHERE id = %s
                    """, (profile_id,))
                    current = cursor.fetchone()
                    
                    if not current:
                        return False
                    
                    # Build update query
                    update_fields = []
                    update_values = []
                    audit_entries = []
                    
                    # Map update keys to database columns
                    field_mapping = {
                        'bep_weight': 'bep_weight',
                        'efficiency_weight': 'efficiency_weight',
                        'head_margin_weight': 'head_margin_weight',
                        'npsh_weight': 'npsh_weight',
                        'bep_optimal_min': 'bep_optimal_min',
                        'bep_optimal_max': 'bep_optimal_max',
                        'min_acceptable_efficiency': 'min_acceptable_efficiency',
                        'excellent_efficiency': 'excellent_efficiency',
                        'good_efficiency': 'good_efficiency',
                        'fair_efficiency': 'fair_efficiency',
                        'optimal_head_margin_max': 'optimal_head_margin_max',
                        'acceptable_head_margin_max': 'acceptable_head_margin_max',
                        'npsh_excellent_margin': 'npsh_excellent_margin',
                        'npsh_good_margin': 'npsh_good_margin',
                        'npsh_minimum_margin': 'npsh_minimum_margin',
                        'speed_variation_penalty_factor': 'speed_variation_penalty_factor',
                        'trimming_penalty_factor': 'trimming_penalty_factor',
                        'max_acceptable_trim_pct': 'max_acceptable_trim_pct',
                        'top_recommendation_threshold': 'top_recommendation_threshold',
                        'acceptable_option_threshold': 'acceptable_option_threshold',
                        'near_miss_count': 'near_miss_count'
                    }
                    
                    for key, value in updates.items():
                        if key in field_mapping:
                            db_field = field_mapping[key]
                            if current[db_field] != value:
                                update_fields.append(f"{db_field} = %s")
                                update_values.append(value)
                                audit_entries.append({
                                    'field': db_field,
                                    'old': current[db_field],
                                    'new': value
                                })
                    
                    if not update_fields:
                        return True  # No changes needed
                    
                    # Validate weights total 100 if any weight is updated
                    weight_fields = ['bep_weight', 'efficiency_weight', 'head_margin_weight', 'npsh_weight']
                    if any(f in updates for f in weight_fields):
                        # Get all weights (current + updates)
                        weights = {
                            'bep_weight': updates.get('bep_weight', current['bep_weight']),
                            'efficiency_weight': updates.get('efficiency_weight', current['efficiency_weight']),
                            'head_margin_weight': updates.get('head_margin_weight', current['head_margin_weight']),
                            'npsh_weight': updates.get('npsh_weight', current['npsh_weight'])
                        }
                        total = sum(weights.values())
                        if abs(total - 100.0) > 0.01:
                            raise ValueError(f"Weights must total 100, got {total}")
                    
                    # Update the profile
                    update_values.append(profile_id)
                    cursor.execute(f"""
                        UPDATE admin_config.application_profiles
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                    """, update_values)
                    
                    # Log audit entries
                    for entry in audit_entries:
                        cursor.execute("""
                            INSERT INTO admin_config.configuration_audits
                            (profile_id, changed_by, change_type, field_name, old_value, new_value, reason)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            profile_id,
                            user,
                            'update',
                            entry['field'],
                            str(entry['old']),
                            str(entry['new']),
                            reason
                        ))
                    
                    conn.commit()
                    
                    # Clear cache
                    self._config_cache.clear()
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return False
    
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
                    
                    profile_id = cursor.fetchone()[0]
                    
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
                
                return cursor.fetchall()
    
    def clear_cache(self):
        """Clear the configuration cache"""
        self._config_cache.clear()
        self._cache_timestamp = None
        logger.info("Configuration cache cleared")


# Create global instance
admin_config_service = AdminConfigService()