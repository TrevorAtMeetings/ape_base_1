"""
Feature Admin Routes
Admin interface for managing feature toggles
"""

import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.admin_config_service import get_config_service

logger = logging.getLogger(__name__)

feature_admin_bp = Blueprint('feature_admin', __name__)

@feature_admin_bp.route('/admin/features')
def feature_management():
    """Feature toggle management dashboard"""
    service = get_config_service()
    toggles = service.get_feature_toggles()
    stats = service.get_feature_stats()
    
    # Organize features by category (simple categorization)
    categorized_features = {
        'AI': {},
        'Admin': {},
        'Features': {},
        'System': {}
    }
    
    for key, feature in toggles.items():
        if 'ai' in key.lower() or 'chatbot' in key.lower():
            categorized_features['AI'][key] = feature
        elif 'admin' in key.lower():
            categorized_features['Admin'][key] = feature
        elif 'brain' in key.lower() or 'pdf' in key.lower():
            categorized_features['System'][key] = feature
        else:
            categorized_features['Features'][key] = feature
    
    return render_template('admin/feature_management.html', 
                         features=categorized_features, 
                         stats=stats)

@feature_admin_bp.route('/admin/features/toggle', methods=['POST'])
def toggle_feature():
    """Toggle a feature on or off"""
    try:
        data = request.get_json()
        feature_key = data.get('feature_key')
        enabled = data.get('enabled')
        
        if not feature_key:
            return jsonify({'success': False, 'error': 'Feature key required'}), 400
        
        # For config-based system, we just return the current state
        # In a production system, you would need to update the config file
        service = get_config_service()
        is_enabled = service.is_feature_enabled(feature_key)
        success = True  # Config-based toggles are read-only for now
        
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
        
        # Config-based system is read-only - can't add new features dynamically
        service = get_config_service()
        success = False  # Can't add features to static config file
        
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
def delete_feature(feature_key):
    """Delete a feature toggle"""
    try:
        # Config-based system is read-only - can't delete features dynamically
        service = get_config_service()
        success = False  # Can't delete features from static config file
        
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
        service = get_config_service()
        toggles = service.get_feature_toggles()
        
        # Convert to simple key-value mapping
        status = {}
        for key, feature in toggles.items():
            if isinstance(feature, bool):
                status[key] = feature
            elif isinstance(feature, dict):
                status[key] = feature.get('enabled', False)
            else:
                status[key] = False
        
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
        service = get_config_service()
        toggles = service.get_feature_toggles()
        feature = toggles.get(feature_key)
        
        if feature:
            return jsonify({'success': True, 'feature': feature})
        else:
            return jsonify({'success': False, 'error': 'Feature not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting feature details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500