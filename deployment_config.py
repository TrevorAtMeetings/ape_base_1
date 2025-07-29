"""
Production Deployment Configuration
This module provides production-ready settings for the APE Pumps application.
"""
import os
import logging
from logging.handlers import RotatingFileHandler

class ProductionConfig:
    """Production configuration settings"""
    
    # Security Settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'fallback-secret-change-me')
    
    # Flask Settings
    DEBUG = False
    TESTING = False
    
    # Database Settings
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # API Settings
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = '/tmp/uploads'
    
    # Performance Settings
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
    
    @staticmethod
    def init_app(app):
        """Initialize production configuration"""
        
        # Setup production logging
        if not app.debug and not app.testing:
            if app.config.get('LOG_TO_STDOUT'):
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(logging.INFO)
                app.logger.addHandler(stream_handler)
            else:
                if not os.path.exists('logs'):
                    os.mkdir('logs')
                file_handler = RotatingFileHandler(
                    'logs/ape_pumps.log', 
                    maxBytes=10240, 
                    backupCount=10
                )
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                ))
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('APE Pumps startup')

class DevelopmentConfig:
    """Development configuration settings"""
    
    DEBUG = True
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    else:
        return DevelopmentConfig

# Security headers middleware
def add_security_headers(app):
    """Add security headers to all responses"""
    
    @app.after_request
    def security_headers(response):
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net "
            "https://cdnjs.cloudflare.com "
            "https://cdn.plot.ly; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net "
            "https://cdnjs.cloudflare.com "
            "https://fonts.googleapis.com; "
            "font-src 'self' "
            "https://fonts.gstatic.com "
            "https://cdnjs.cloudflare.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self';"
        )
        
        # Other security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    return app