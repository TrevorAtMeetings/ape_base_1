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
        comparison_list = session.get('comparison_list', [])
        
        # Check if pump already in list
        existing_pump = next((p for p in comparison_list if p['pump_code'] == pump_code), None)
        if existing_pump:
            return jsonify({'success': False, 'message': f'{pump_code} already in comparison list'})
        
        # Store ONLY identifiers - Brain provides fresh data on demand when needed
        comparison_pump = {
            'pump_code': pump_code,
            'flow': float(flow),
            'head': float(head),
            'pump_type': pump_type,
            'added_timestamp': str(int(float(request.args.get('ts', '0'))))
        }
        
        comparison_list.append(comparison_pump)
        
        # Limit to 10 pumps max
        if len(comparison_list) > 10:
            comparison_list = comparison_list[-10:]
        
        # Save minimal data to session - Brain intelligence on demand
        session['comparison_list'] = comparison_list
        session.permanent = True  # Make session persistent
        
        # Also update site requirements for comparison page
        site_requirements = {
            'flow_m3hr': flow,
            'head_m': head,
            'pump_type': pump_type,
            'application': 'water'
        }
        session['site_requirements'] = site_requirements
        
        # Debug: Verify session save immediately
        saved_list = session.get('comparison_list', [])
        logger.info(f"Added {pump_code} to comparison list. Total: {len(comparison_list)}, Verified in session: {len(saved_list)}")
        
        return jsonify({
            'success': True, 
            'message': f'Added {pump_code} to comparison',
            'count': len(comparison_list),
            'debug_session_count': len(saved_list)
        })
        
    except Exception as e:
        logger.error(f"Error in add_to_comparison: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'})

@comparison_api_bp.route('/api/get_comparison_list', methods=['GET'])
def get_comparison_list():
    """Get current comparison list with fresh Brain evaluations."""
    try:
        # Get minimal identifiers from session
        comparison_identifiers = session.get('comparison_list', [])
        
        # Debug: Log session access
        logger.info(f"GET comparison_list - Found {len(comparison_identifiers)} items in session")
        
        if not comparison_identifiers:
            return jsonify({
                'success': True,
                'pumps': [],
                'count': 0,
                'debug_message': 'No items found in session'
            })
        
        # Get fresh Brain evaluations for each pump
        brain = get_pump_brain()
        if not brain:
            return jsonify({'success': False, 'message': 'Brain system unavailable'})
        
        fresh_pump_data = []
        for identifier in comparison_identifiers:
            try:
                pump_code = identifier['pump_code']
                flow = identifier['flow']
                head = identifier['head']
                
                # Get fresh evaluation from Brain - NO FALLBACKS
                evaluation = brain.evaluate_pump(pump_code, flow, head)
                
                if evaluation and not evaluation.get('excluded'):
                    # Combine identifier with fresh Brain intelligence
                    pump_data = {
                        **identifier,  # Original identifiers
                        'evaluation': evaluation,  # Fresh Brain data
                        'performance': evaluation  # Alias for template compatibility
                    }
                    fresh_pump_data.append(pump_data)
                else:
                    logger.warning(f"Pump {pump_code} no longer suitable, removing from comparison")
                    
            except Exception as e:
                logger.error(f"Error evaluating {identifier.get('pump_code', 'unknown')}: {str(e)}")
                continue
        
        # Update session with cleaned list (remove unsuitable pumps)
        if len(fresh_pump_data) != len(comparison_identifiers):
            cleaned_identifiers = [
                {'pump_code': p['pump_code'], 'flow': p['flow'], 'head': p['head'], 'pump_type': p.get('pump_type', 'GENERAL')}
                for p in fresh_pump_data
            ]
            session['comparison_list'] = cleaned_identifiers
        
        return jsonify({
            'success': True,
            'pumps': fresh_pump_data,
            'count': len(fresh_pump_data)
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