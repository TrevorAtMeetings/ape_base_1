"""
Feature Admin Routes
Admin interface for managing feature toggles
"""

import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.feature_toggle_service import get_feature_toggle_service
from functools import wraps

logger = logging.getLogger(__name__)

feature_admin_bp = Blueprint('feature_admin', __name__)

def admin_required(f):
    """Decorator to require admin access (placeholder - implement proper auth as needed)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement proper admin authentication
        return f(*args, **kwargs)
    return decorated_function

@feature_admin_bp.route('/admin/features')
@admin_required
def feature_management():
    """Feature toggle management dashboard"""
    service = get_feature_toggle_service()
    categorized_features = service.get_features_by_category()
    stats = service.get_feature_stats()
    
    return render_template('admin/feature_management.html', 
                         features=categorized_features, 
                         stats=stats)

@feature_admin_bp.route('/admin/features/toggle', methods=['POST'])
@admin_required
def toggle_feature():
    """Toggle a feature on or off"""
    try:
        data = request.get_json()
        feature_key = data.get('feature_key')
        enabled = data.get('enabled')
        
        if not feature_key:
            return jsonify({'success': False, 'error': 'Feature key required'}), 400
        
        service = get_feature_toggle_service()
        success = service.toggle_feature(feature_key, enabled, 'admin_user')
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Feature {feature_key} {"enabled" if enabled else "disabled"}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to toggle feature'}), 500
            
    except Exception as e:
        logger.error(f"Error toggling feature: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_admin_bp.route('/admin/features/add', methods=['POST'])
@admin_required
def add_feature():
    """Add a new feature toggle"""
    try:
        data = request.form if request.form else request.get_json()
        
        feature_key = data.get('feature_key', '').strip()
        feature_name = data.get('feature_name', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'general').strip()
        is_enabled = data.get('is_enabled', 'true').lower() == 'true'
        
        if not feature_key or not feature_name:
            flash('Feature key and name are required', 'error')
            return redirect(url_for('feature_admin.feature_management'))
        
        service = get_feature_toggle_service()
        success = service.add_feature(feature_key, feature_name, description, category, is_enabled)
        
        if success:
            flash(f'Feature "{feature_name}" added successfully', 'success')
        else:
            flash('Failed to add feature. Key may already exist.', 'error')
            
        return redirect(url_for('feature_admin.feature_management'))
        
    except Exception as e:
        logger.error(f"Error adding feature: {e}")
        flash(f'Error adding feature: {str(e)}', 'error')
        return redirect(url_for('feature_admin.feature_management'))

@feature_admin_bp.route('/admin/features/delete/<feature_key>', methods=['POST'])
@admin_required
def delete_feature(feature_key):
    """Delete a feature toggle"""
    try:
        service = get_feature_toggle_service()
        success = service.delete_feature(feature_key)
        
        if success:
            flash(f'Feature "{feature_key}" deleted successfully', 'success')
        else:
            flash('Failed to delete feature', 'error')
            
        return redirect(url_for('feature_admin.feature_management'))
        
    except Exception as e:
        logger.error(f"Error deleting feature: {e}")
        flash(f'Error deleting feature: {str(e)}', 'error')
        return redirect(url_for('feature_admin.feature_management'))

@feature_admin_bp.route('/api/features/status')
def get_feature_status():
    """API endpoint to get current feature status"""
    try:
        service = get_feature_toggle_service()
        features = service.get_all_features()
        
        # Convert to simple key-value mapping
        status = {f['feature_key']: f['is_enabled'] for f in features}
        
        return jsonify({
            'success': True,
            'features': status,
            'stats': service.get_feature_stats()
        })
        
    except Exception as e:
        logger.error(f"Error getting feature status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@feature_admin_bp.route('/api/features/<feature_key>')
def get_feature_details(feature_key):
    """Get details for a specific feature"""
    try:
        service = get_feature_toggle_service()
        feature = service.get_feature(feature_key)
        
        if feature:
            return jsonify({'success': True, 'feature': feature})
        else:
            return jsonify({'success': False, 'error': 'Feature not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting feature details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500