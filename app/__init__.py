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
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

app = Flask(__name__, 
           template_folder=template_dir,
           static_folder=static_dir)
logger.info("Flask app instance created.")

# 2. CONFIGURE THE APP
app.config['DEBUG'] = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
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
from . import routes
logger.info("Routes imported.")

# Import core functions from pump_engine.py (single source of truth)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.pump_engine import (
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
