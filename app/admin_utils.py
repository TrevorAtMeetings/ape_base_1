"""
Admin Utilities - Shared Functions
==================================
Shared utility functions for admin modules to prevent duplication.
"""

import logging
from functools import wraps
from flask import session, redirect, url_for, flash

logger = logging.getLogger(__name__)


def admin_required(f):
    """
    Decorator to require admin privileges for route access.
    Consolidated from multiple modules to prevent duplication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has admin privileges
        if not session.get('is_admin', False):
            flash('Admin access required', 'error')
            logger.warning(f"Unauthorized admin access attempt to {f.__name__}")
            return redirect(url_for('main_flow.index'))
        return f(*args, **kwargs)
    return decorated_function