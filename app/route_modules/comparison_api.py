"""
API endpoints for pump comparison functionality.
"""

import logging
from flask import Blueprint, request, jsonify, session
from app.session_manager import safe_session_get, safe_session_set
from app.pump_repository import PumpRepository

logger = logging.getLogger(__name__)
comparison_api_bp = Blueprint('comparison_api', __name__)

@comparison_api_bp.route('/api/add_to_comparison', methods=['POST'])
def add_to_comparison():
    """Add a pump to the comparison list in session."""
    try:
        data = request.get_json()
        pump_code = data.get('pump_code')
        flow = data.get('flow')
        head = data.get('head')
        pump_type = data.get('pump_type', 'GENERAL')
        
        if not pump_code or not flow or not head:
            return jsonify({'success': False, 'message': 'Missing required parameters'})
        
        # Get current comparison list from session
        comparison_list = safe_session_get('comparison_list', [])
        
        # Check if pump already in list
        existing_pump = next((p for p in comparison_list if p['pump_code'] == pump_code), None)
        if existing_pump:
            return jsonify({'success': False, 'message': f'{pump_code} already in comparison list'})
        
        # Load pump data from repository
        try:
            repo = PumpRepository()
            pump_data = repo.get_pump_by_code(pump_code)
            
            if not pump_data:
                return jsonify({'success': False, 'message': 'Pump not found in database'})
            
            # Add pump to comparison list
            comparison_pump = {
                'pump_code': pump_code,
                'flow': flow,
                'head': head,
                'pump_type': pump_type,
                'pump_data': pump_data
            }
            
            comparison_list.append(comparison_pump)
            
            # Limit to 10 pumps max
            if len(comparison_list) > 10:
                comparison_list = comparison_list[-10:]
            
            # Save to session
            safe_session_set('comparison_list', comparison_list)
            
            # Also update site requirements for comparison page
            site_requirements = {
                'flow_m3hr': flow,
                'head_m': head,
                'pump_type': pump_type,
                'application': 'water'
            }
            safe_session_set('site_requirements', site_requirements)
            
            logger.info(f"Added {pump_code} to comparison list. Total: {len(comparison_list)}")
            
            return jsonify({
                'success': True, 
                'message': f'Added {pump_code} to comparison',
                'count': len(comparison_list)
            })
            
        except Exception as e:
            logger.error(f"Error loading pump data for {pump_code}: {str(e)}")
            return jsonify({'success': False, 'message': 'Error loading pump data'})
        
    except Exception as e:
        logger.error(f"Error in add_to_comparison: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'})

@comparison_api_bp.route('/api/get_comparison_list', methods=['GET'])
def get_comparison_list():
    """Get current comparison list from session."""
    try:
        comparison_list = safe_session_get('comparison_list', [])
        return jsonify({
            'success': True,
            'pumps': comparison_list,
            'count': len(comparison_list)
        })
    except Exception as e:
        logger.error(f"Error in get_comparison_list: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'})

@comparison_api_bp.route('/api/clear_comparison', methods=['POST'])
def clear_comparison():
    """Clear comparison list."""
    try:
        safe_session_set('comparison_list', [])
        return jsonify({'success': True, 'message': 'Comparison list cleared'})
    except Exception as e:
        logger.error(f"Error in clear_comparison: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'})

@comparison_api_bp.route('/api/remove_from_comparison', methods=['POST'])
def remove_from_comparison():
    """Remove a pump from comparison list."""
    try:
        data = request.get_json()
        pump_code = data.get('pump_code')
        
        if not pump_code:
            return jsonify({'success': False, 'message': 'Missing pump_code'})
        
        comparison_list = safe_session_get('comparison_list', [])
        comparison_list = [p for p in comparison_list if p['pump_code'] != pump_code]
        
        safe_session_set('comparison_list', comparison_list)
        
        return jsonify({
            'success': True,
            'message': f'Removed {pump_code} from comparison',
            'count': len(comparison_list)
        })
        
    except Exception as e:
        logger.error(f"Error in remove_from_comparison: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'})