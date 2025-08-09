"""
Brain-Only Comparison API - NO FALLBACKS EVER
============================================
API endpoints for pump comparison functionality using Brain system as single source of truth.
"""

import logging
from flask import Blueprint, request, jsonify, session
from app.pump_brain import get_pump_brain

logger = logging.getLogger(__name__)
comparison_api_bp = Blueprint('comparison_api', __name__)

@comparison_api_bp.route('/api/add_to_comparison', methods=['POST'])
def add_to_comparison():
    """Add a pump to the comparison list - stores ONLY identifiers, Brain evaluates on demand."""
    try:
        data = request.get_json()
        pump_code = data.get('pump_code')
        flow = data.get('flow')
        head = data.get('head')
        
        if not pump_code or not flow or not head:
            return jsonify({'success': False, 'message': 'Missing required parameters'})
        
        # Get current comparison list from session
        comparison_list = session.get('comparison_list', [])
        
        # Check if pump already in list (allow different pumps at same duty point)
        existing_pump = next((p for p in comparison_list 
                            if p['pump_code'] == pump_code), None)
        if existing_pump:
            return jsonify({'success': False, 'message': f'{pump_code} already in comparison list at this duty point'})
        
        # Store MINIMAL identifiers only - NO pump data, Brain evaluates fresh on demand
        comparison_identifier = {
            'pump_code': pump_code,
            'flow': float(flow),
            'head': float(head)
        }
        
        comparison_list.append(comparison_identifier)
        
        # Limit to 10 pumps max
        if len(comparison_list) > 10:
            comparison_list = comparison_list[:10]  # Keep first 10
        
        # Save minimal identifiers to session
        session['comparison_list'] = comparison_list
        session.modified = True  # Ensure session is marked as modified
        
        logger.info(f"Added {pump_code} to comparison (flow={flow}, head={head}). Total: {len(comparison_list)}")
        
        return jsonify({
            'success': True, 
            'message': f'Added {pump_code} to comparison',
            'count': len(comparison_list)
        })
        
    except Exception as e:
        logger.error(f"Error in add_to_comparison: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'})

@comparison_api_bp.route('/api/get_comparison_list', methods=['GET'])
def get_comparison_list():
    """Get comparison list identifiers - evaluation happens on the comparison page."""
    try:
        # Get minimal identifiers from session
        comparison_identifiers = session.get('comparison_list', [])
        
        logger.info(f"GET comparison_list - Found {len(comparison_identifiers)} items in session")
        
        return jsonify({
            'success': True,
            'identifiers': comparison_identifiers,
            'count': len(comparison_identifiers)
        })
        
    except Exception as e:
        logger.error(f"Error in get_comparison_list: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'})

@comparison_api_bp.route('/api/clear_comparison', methods=['POST'])
def clear_comparison():
    """Clear comparison list."""
    try:
        session['comparison_list'] = []
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
        
        comparison_list = session.get('comparison_list', [])
        comparison_list = [p for p in comparison_list if p['pump_code'] != pump_code]
        
        session['comparison_list'] = comparison_list
        
        return jsonify({
            'success': True,
            'message': f'Removed {pump_code} from comparison',
            'count': len(comparison_list)
        })
        
    except Exception as e:
        logger.error(f"Error in remove_from_comparison: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'})