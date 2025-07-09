"""
Main Routes File
Imports and registers all route modules to maintain exact same functionality
"""
import logging
from flask import render_template, request, redirect, url_for, session
from ..session_manager import safe_flash
from .. import app

logger = logging.getLogger(__name__)

# Import all route modules to register their routes
# This approach maintains exact same route names and functionality MARK


# No templates need to be updated - all url_for() calls work unchanged

# Import main flow routes (core user flow)
from .main_flow import *

# Import data management routes (data handling, export, upload)
from .data_management import *

# Import report routes (pump reports, PDF generation)
from .reports import *

# Import API routes (chart data, AI analysis, pump data)
from .api import *

# Import admin routes (pump upload, recent pumps, SCG processing)
from .admin import *

# Import comparison routes (pump comparison, shortlist)
from .comparison import *

# Additional routes that don't fit into the main modules
@app.route('/help-features')
def help_features_page():
    """Help features page."""
    return render_template('help_brochure.html')

@app.route('/guide')
def guide_page():
    """Guide page."""
    return render_template('guide.html')

# Register all routes by importing the modules
# This maintains the exact same route names and functionality
# All templates continue to work without any changes
logger.info("All route modules imported and registered successfully")