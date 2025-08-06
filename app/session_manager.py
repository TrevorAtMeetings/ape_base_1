"""
Session Management Module for Pump Selection Application
Provides centralized control over Flask session functionality.
"""

import os
from typing import Optional, Dict, Any
from flask import Flask, session, flash, request

# Global configuration
SESSION_ENABLED = True  # Enable session functionality when SECRET_KEY is available
SECRET_KEY_FALLBACK = "dev-secret-key-change-in-production"

class SessionManager:
    """Centralized session management for the Flask application."""

    def __init__(self, app: Flask):
        self.app = app
        self._configure_secret_key()

    def _configure_secret_key(self):
        """Configure the Flask secret key with fallback."""
        secret_key = os.environ.get("SESSION_SECRET", SECRET_KEY_FALLBACK)
        self.app.secret_key = secret_key

    def is_enabled(self) -> bool:
        """Check if sessions are enabled."""
        return SESSION_ENABLED and self.app.secret_key is not None

    def safe_flash(self, message: str, category: str = 'info') -> None:
        """Safely flash a message, handling disabled sessions."""
        if self.is_enabled():
            flash(message, category)
        else:
            # Log the message instead of flashing when sessions are disabled
            print(f"[{category.upper()}] {message}")

    def safe_session_get(self, key: str, default: Any = None) -> Any:
        """Safely get a session value."""
        if self.is_enabled():
            return session.get(key, default)
        return default

    def safe_session_set(self, key: str, value: Any) -> None:
        """Safely set a session value."""
        if self.is_enabled():
            session[key] = value

    def safe_session_pop(self, key: str, default: Any = None) -> Any:
        """Safely pop a session value."""
        if self.is_enabled():
            return session.pop(key, default)
        return default

    def safe_session_clear(self) -> None:
        """Safely clear all session data."""
        if self.is_enabled():
            session.clear()

    def get_form_data(self, key: str, default: Any = None) -> Any:
        """Get form data with fallback to session if sessions are enabled."""
        form_value = request.form.get(key)
        if form_value is not None:
            return form_value

        if self.is_enabled():
            return session.get(key, default)
        return default

    def store_form_data(self, data: Dict[str, Any]) -> None:
        """Store form data in session if sessions are enabled."""
        if self.is_enabled():
            for key, value in data.items():
                session[key] = value

# Global session manager instance
_session_manager: Optional[SessionManager] = None

def init_session_manager(app: Flask) -> SessionManager:
    """Initialize the global session manager."""
    global _session_manager
    _session_manager = SessionManager(app)
    return _session_manager

def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    if _session_manager is None:
        raise RuntimeError("Session manager not initialized. Call init_session_manager() first.")
    return _session_manager

def enable_sessions():
    """Enable session functionality."""
    global SESSION_ENABLED
    SESSION_ENABLED = True

def disable_sessions():
    """Disable session functionality."""
    global SESSION_ENABLED
    SESSION_ENABLED = False

def sessions_enabled() -> bool:
    """Check if sessions are currently enabled."""
    return SESSION_ENABLED

# Convenience functions for easy use in routes
def safe_flash(message: str, category: str = 'info') -> None:
    """Safely flash a message."""
    if _session_manager:
        _session_manager.safe_flash(message, category)
    else:
        print(f"[{category.upper()}] {message}")

def safe_session_get(key: str, default: Any = None) -> Any:
    """Safely get a session value."""
    if _session_manager:
        return _session_manager.safe_session_get(key, default)
    return default

def safe_session_set(key: str, value: Any) -> None:
    """Safely set a session value."""
    if _session_manager:
        _session_manager.safe_session_set(key, value)

def safe_session_pop(key: str, default: Any = None) -> Any:
    """Safely pop a session value."""
    if _session_manager:
        return _session_manager.safe_session_pop(key, default)
    return default

def safe_session_clear() -> None:
    """Safely clear all session data."""
    if _session_manager:
        _session_manager.safe_session_clear()

def get_form_data(key: str, default: Any = None) -> Any:
    """Get form data with session fallback."""
    if _session_manager:
        return _session_manager.get_form_data(key, default)
    return request.form.get(key, default)

def store_form_data(data: Dict[str, Any]) -> None:
    """Store form data in session."""
    if _session_manager:
        _session_manager.store_form_data(data)

def flatten_pump_data(pump_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten pump data structure to reduce session size and enable direct template access.
    Converts nested structure to flat dictionary for cookie size optimization.
    """
    if not pump_dict:
        return {}
    
    flattened = {}
    
    # Core pump identification
    flattened['pump_code'] = pump_dict.get('pump_code', 'N/A')
    flattened['suitability_score'] = pump_dict.get('suitability_score', 0)
    
    # Flatten performance data to top level
    performance = pump_dict.get('performance', {}) or pump_dict.get('operating_point', {})
    flattened['efficiency_pct'] = performance.get('efficiency_pct', 0)
    flattened['power_kw'] = performance.get('power_kw', 0)
    flattened['npshr_m'] = performance.get('npshr_m', 0)
    flattened['flow_m3hr'] = performance.get('flow_m3hr', 0)  
    flattened['head_m'] = performance.get('head_m', 0)
    
    # Flatten BEP analysis to top level
    bep_analysis = pump_dict.get('bep_analysis', {})
    flattened['qbep_percentage'] = bep_analysis.get('qbep_percentage', 100)
    flattened['operating_zone'] = bep_analysis.get('operating_zone', 'Unknown')
    
    # Flatten sizing info to top level
    sizing = pump_dict.get('sizing_info', {})
    flattened['impeller_diameter_mm'] = sizing.get('impeller_diameter_mm', 187)
    flattened['trim_percent'] = sizing.get('trim_percent', 100)
    
    # Flatten pump info to top level
    pump_info = pump_dict.get('pump', {})
    flattened['manufacturer'] = pump_info.get('manufacturer', 'APE Pumps')
    flattened['pump_type'] = pump_info.get('pump_type', 'Centrifugal')
    flattened['model_series'] = pump_info.get('model_series', 'Industrial')
    flattened['stages'] = pump_info.get('stages', '1')
    
    # Flatten individual scores to top level (v6.0 methodology)
    flattened['bep_score'] = pump_dict.get('bep_score', 0)
    flattened['efficiency_score'] = pump_dict.get('efficiency_score', 0)
    flattened['margin_score'] = pump_dict.get('margin_score', 0) 
    flattened['npsh_score'] = pump_dict.get('npsh_score', 0)
    
    return flattened

def store_pumps_optimized(suitable_pumps: list) -> None:
    """Store pumps in session using flattened structure to minimize session size."""
    if not _session_manager or not _session_manager.is_enabled():
        return
    
    # Flatten all pumps to reduce session size
    flattened_pumps = []
    for pump in suitable_pumps:
        flattened_pump = flatten_pump_data(pump)
        flattened_pumps.append(flattened_pump)
    
    # Store only essential data - limit to top 3 to stay under 4093 byte cookie limit
    session['suitable_pumps'] = flattened_pumps[:3]  # Cookie size optimization