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
# Standardized environment variable configuration
app.config['DEBUG'] = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
app.config['HOST'] = os.environ.get("FLASK_HOST", "0.0.0.0")
app.config['PORT'] = int(os.environ.get("FLASK_PORT", 5000))

# Define UPLOAD_FOLDER relative to the app's static folder
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'temp')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logger.info(f"App configured. Upload folder: {app.config['UPLOAD_FOLDER']}")

# Initialize session manager
from .session_manager import init_session_manager
session_manager = init_session_manager(app)
logger.info("Session manager initialized.")

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

# Register the Data Management blueprint
from .route_modules.data_management import data_management_bp
app.register_blueprint(data_management_bp)

# Register the Main Flow blueprint
from .route_modules.main_flow import main_flow_bp
app.register_blueprint(main_flow_bp)

# Register the Reports blueprint
from .route_modules.reports import reports_bp
app.register_blueprint(reports_bp)

# Register the Comparison blueprint
from .route_modules.comparison import comparison_bp
app.register_blueprint(comparison_bp)

# Register the Chat blueprint
from .route_modules.chat import chat_bp
app.register_blueprint(chat_bp)

# Register the API blueprint
from .route_modules.api import api_bp
app.register_blueprint(api_bp)

# Import core functions from pump_engine.py (single source of truth)
from .pump_engine import (
    load_all_pump_data,
    validate_site_requirements,
    SiteRequirements,
    ParsedPumpData,
    parse_pump_data
)
# selection_engine.py moved to archive - find_best_pumps is available in pump_engine.py

__all__ = [
    'app',  # Expose the Flask app instance
    'load_all_pump_data',
    'validate_site_requirements',
    'SiteRequirements',
    'ParsedPumpData',
    'parse_pump_data',
    # 'find_best_pumps',  # Available in pump_engine.py
]
