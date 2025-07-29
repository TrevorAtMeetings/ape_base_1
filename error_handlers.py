"""
Error handlers for production deployment
"""
import logging
from flask import render_template, jsonify, request
from app import app

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.is_json:
        return jsonify({'error': 'Not found', 'status': 404}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logging.error(f'Server Error: {error}', exc_info=True)
    if request.is_json:
        return jsonify({'error': 'Internal server error', 'status': 500}), 500
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    if request.is_json:
        return jsonify({'error': 'Forbidden', 'status': 403}), 403
    return render_template('errors/403.html'), 403

@app.errorhandler(413)
def file_too_large_error(error):
    """Handle file upload size errors"""
    if request.is_json:
        return jsonify({'error': 'File too large', 'status': 413}), 413
    return render_template('errors/413.html'), 413

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unexpected exceptions"""
    logging.error(f'Unhandled Exception: {e}', exc_info=True)
    
    # Don't expose internal errors in production
    if app.config.get('DEBUG'):
        # Re-raise in debug mode to see the full traceback
        raise e
    
    if request.is_json:
        return jsonify({'error': 'An unexpected error occurred', 'status': 500}), 500
    return render_template('errors/500.html'), 500