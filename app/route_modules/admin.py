"""
Admin Routes
Routes for administrative functions including AI admin interface
"""
import logging
from flask import render_template, Blueprint

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/ai')
def ai_admin():
    """AI Knowledge Base Admin page."""
    return render_template('ai_admin.html')

# Optionally, make this the admin landing page as well:
@admin_bp.route('/admin')
def admin_landing():
    return render_template('ai_admin.html')

 