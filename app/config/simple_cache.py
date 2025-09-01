"""
Simple cache control - one setting controls everything.
"""

from flask import Flask

def setup_caching(app: Flask):
    """Simple cache setup based on DISABLE_ALL_CACHING environment variable."""
    
    import os
    
    # Single environment variable controls everything
    disable_caching = os.getenv('DISABLE_ALL_CACHING', 'false').lower() == 'true'
    
    if disable_caching:
        
        # Disable template caching
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.jinja_env.auto_reload = True
        app.jinja_env.cache = {}
        
        # Clear template cache before each request
        @app.before_request
        def clear_cache():
            app.jinja_env.cache.clear()
        
        # Disable HTTP caching
        @app.after_request
        def no_cache(response):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
            
    else:
        
        # Production-like caching
        app.config['TEMPLATES_AUTO_RELOAD'] = False
        
        @app.after_request
        def normal_cache(response):
            response.headers['Cache-Control'] = 'public, max-age=300'
            return response