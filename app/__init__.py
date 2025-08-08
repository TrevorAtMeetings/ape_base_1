"""
APE Pumps Selection Application Package
This package initializes the Flask application and imports its components.
"""
import os
from dotenv import load_dotenv
from flask import Flask
import logging

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

__version__ = "1.0.0"
__author__ = "APE Pumps"

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. CREATE THE FLASK APPLICATION INSTANCE HERE
# Set template and static folders relative to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
logger.info("Flask app instance created.")

# 2. CONFIGURE THE APP
# Production-ready configuration
app.config['DEBUG'] = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
app.config['HOST'] = os.environ.get("FLASK_HOST", "0.0.0.0")
app.config['PORT'] = int(os.environ.get("FLASK_PORT", 5000))

# Security configuration
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'change-me-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000 if not app.config['DEBUG'] else 1

# Production logging
if not app.config['DEBUG']:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

# Define UPLOAD_FOLDER relative to the app's static folder
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'temp')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logger.info(f"App configured. Upload folder: {app.config['UPLOAD_FOLDER']}")

# Initialize session manager
from .session_manager import init_session_manager
session_manager = init_session_manager(app)
logger.info("Session manager initialized.")

# Clear repository cache to ensure correct DATABASE_URL is used
from .pump_repository import clear_pump_repository
clear_pump_repository()
logger.info("Repository cache cleared to ensure correct DATABASE_URL.")

# 3. IMPORT YOUR APPLICATION MODULES
# Import routes *after* the app is created and configured
from .route_modules import routes
logger.info("Routes imported.")

# Register admin blueprint for admin routes
from .route_modules.admin import admin_bp
app.register_blueprint(admin_bp)

# Register the AI Extract blueprint
from .route_modules.ai_extract_routes import ai_extract_bp
app.register_blueprint(ai_extract_bp)

# Import error handlers and health checks for production
try:
    import error_handlers
    import health_check
except ImportError:
    # Graceful fallback if modules don't exist
    pass

# Register the Data Management blueprint
from .route_modules.data_management import data_management_bp
app.register_blueprint(data_management_bp)

# Register the Main Flow blueprint
from .route_modules.main_flow import main_flow_bp
app.register_blueprint(main_flow_bp)

# Register the Reports blueprint
from .route_modules.reports import reports_bp
app.register_blueprint(reports_bp)

# Register the Comparison API blueprint
from .route_modules.comparison_api import comparison_api_bp
app.register_blueprint(comparison_api_bp)

# Register the Comparison blueprint
from .route_modules.comparison import comparison_bp
app.register_blueprint(comparison_bp)

# Register the Chat blueprint
from .route_modules.chat import chat_bp
app.register_blueprint(chat_bp)

# Register the API blueprint
from .route_modules.api import api_bp
app.register_blueprint(api_bp, url_prefix='/api')

# Register the Pump Editor blueprint
from .route_modules.pump_editor_routes import pump_editor_bp
app.register_blueprint(pump_editor_bp)

# Register the Admin Config blueprint
from .route_modules.admin_config import admin_config_bp
app.register_blueprint(admin_config_bp)

# Register the Brain Monitor blueprint (if available)
try:
    from .route_modules.brain_monitoring import brain_monitoring_bp
    app.register_blueprint(brain_monitoring_bp)
    logger.info("Brain monitoring routes registered")
except ImportError:
    logger.info("Brain monitoring not available - continuing without it")

# Import core functions from appropriate modules
from .data_models import SiteRequirements
from .pump_repository import get_pump_repository
from .utils import validate_site_requirements

__all__ = [
    'app',  # Expose the Flask app instance
    'get_pump_repository',
    'validate_site_requirements',
    'SiteRequirements'
]