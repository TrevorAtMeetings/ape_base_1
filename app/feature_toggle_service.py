"""
Feature Toggle Service
Centralized management of application feature toggles for admin control
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class FeatureToggleService:
    """Service for managing feature toggles and admin controls"""
    
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self._feature_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def is_feature_enabled(self, feature_key: str) -> bool:
        """
        Check if a feature is enabled
        
        Args:
            feature_key: Unique key for the feature
            
        Returns:
            bool: True if feature is enabled, False otherwise
        """
        # Check cache first
        if (self._cache_timestamp and 
            (datetime.utcnow() - self._cache_timestamp).seconds < self._cache_ttl and
            feature_key in self._feature_cache):
            return self._feature_cache[feature_key].get('is_enabled', False)
        
        # Load from database
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT is_enabled FROM admin_features.feature_toggles
                        WHERE feature_key = %s
                    """, (feature_key,))
                    
                    result = cursor.fetchone()
                    if result:
                        enabled = result['is_enabled']
                        # Update cache
                        if not self._feature_cache:
                            self._refresh_cache()
                        return enabled
                    else:
                        logger.warning(f"Feature '{feature_key}' not found, defaulting to False")
                        return False
        except Exception as e:
            logger.error(f"Error checking feature '{feature_key}': {e}")
            return False
    
    def get_feature(self, feature_key: str) -> Optional[Dict]:
        """Get complete feature information"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM admin_features.feature_toggles
                        WHERE feature_key = %s
                    """, (feature_key,))
                    
                    result = cursor.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting feature '{feature_key}': {e}")
            return None
    
    def get_all_features(self) -> List[Dict]:
        """Get all features organized by category"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM admin_features.feature_toggles
                        ORDER BY category, feature_name
                    """)
                    
                    features = cursor.fetchall()
                    return [dict(feature) for feature in features]
        except Exception as e:
            logger.error(f"Error getting all features: {e}")
            return []
    
    def get_features_by_category(self) -> Dict[str, List[Dict]]:
        """Get features organized by category"""
        features = self.get_all_features()
        categorized = {}
        
        for feature in features:
            category = feature.get('category', 'general')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(feature)
        
        return categorized
    
    def toggle_feature(self, feature_key: str, enabled: bool, updated_by: str = 'admin') -> bool:
        """
        Toggle a feature on or off
        
        Args:
            feature_key: Unique key for the feature
            enabled: True to enable, False to disable
            updated_by: User who made the change
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE admin_features.feature_toggles
                        SET is_enabled = %s, 
                            updated_at = CURRENT_TIMESTAMP,
                            updated_by = %s
                        WHERE feature_key = %s
                    """, (enabled, updated_by, feature_key))
                    
                    if cursor.rowcount > 0:
                        conn.commit()
                        # Clear cache to force refresh
                        self._clear_cache()
                        logger.info(f"Feature '{feature_key}' {'enabled' if enabled else 'disabled'} by {updated_by}")
                        return True
                    else:
                        logger.warning(f"Feature '{feature_key}' not found for toggle")
                        return False
        except Exception as e:
            logger.error(f"Error toggling feature '{feature_key}': {e}")
            return False
    
    def update_feature_config(self, feature_key: str, config_data: Dict, updated_by: str = 'admin') -> bool:
        """Update feature configuration data"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE admin_features.feature_toggles
                        SET config_data = %s,
                            updated_at = CURRENT_TIMESTAMP,
                            updated_by = %s
                        WHERE feature_key = %s
                    """, (config_data, updated_by, feature_key))
                    
                    if cursor.rowcount > 0:
                        conn.commit()
                        self._clear_cache()
                        logger.info(f"Feature config updated for '{feature_key}' by {updated_by}")
                        return True
                    else:
                        return False
        except Exception as e:
            logger.error(f"Error updating feature config '{feature_key}': {e}")
            return False
    
    def add_feature(self, feature_key: str, feature_name: str, description: str = '', 
                   category: str = 'general', is_enabled: bool = True) -> bool:
        """Add a new feature toggle"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO admin_features.feature_toggles 
                        (feature_key, feature_name, description, category, is_enabled)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (feature_key, feature_name, description, category, is_enabled))
                    
                    conn.commit()
                    self._clear_cache()
                    logger.info(f"New feature '{feature_key}' added")
                    return True
        except Exception as e:
            logger.error(f"Error adding feature '{feature_key}': {e}")
            return False
    
    def delete_feature(self, feature_key: str) -> bool:
        """Delete a feature toggle"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM admin_features.feature_toggles
                        WHERE feature_key = %s
                    """, (feature_key,))
                    
                    if cursor.rowcount > 0:
                        conn.commit()
                        self._clear_cache()
                        logger.info(f"Feature '{feature_key}' deleted")
                        return True
                    else:
                        return False
        except Exception as e:
            logger.error(f"Error deleting feature '{feature_key}': {e}")
            return False
    
    def _refresh_cache(self):
        """Refresh the feature cache"""
        try:
            features = self.get_all_features()
            self._feature_cache = {f['feature_key']: f for f in features}
            self._cache_timestamp = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error refreshing feature cache: {e}")
    
    def _clear_cache(self):
        """Clear the feature cache"""
        self._feature_cache.clear()
        self._cache_timestamp = None
    
    def get_feature_stats(self) -> Dict:
        """Get statistics about features"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_features,
                            COUNT(CASE WHEN is_enabled THEN 1 END) as enabled_features,
                            COUNT(CASE WHEN NOT is_enabled THEN 1 END) as disabled_features,
                            COUNT(DISTINCT category) as categories
                        FROM admin_features.feature_toggles
                    """)
                    
                    result = cursor.fetchone()
                    return {
                        'total_features': result[0] or 0,
                        'enabled_features': result[1] or 0,
                        'disabled_features': result[2] or 0,
                        'categories': result[3] or 0
                    }
        except Exception as e:
            logger.error(f"Error getting feature stats: {e}")
            return {
                'total_features': 0,
                'enabled_features': 0, 
                'disabled_features': 0,
                'categories': 0
            }

# Singleton instance
_feature_toggle_service = None

def get_feature_toggle_service() -> FeatureToggleService:
    """Get the global feature toggle service instance"""
    global _feature_toggle_service
    if _feature_toggle_service is None:
        _feature_toggle_service = FeatureToggleService()
    return _feature_toggle_service

def is_feature_enabled(feature_key: str) -> bool:
    """Convenience function to check if a feature is enabled"""
    return get_feature_toggle_service().is_feature_enabled(feature_key)