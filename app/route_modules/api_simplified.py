"""
API Routes
Routes for API endpoints including chart data, AI analysis, and pump data
"""
import logging
import time
import json
from flask import Blueprint, request, jsonify, make_response
from ..data_models import SiteRequirements
from .. import app

logger = logging.getLogger(__name__)

# Try to import Brain system for Phase 2 integration
try:
    from ..pump_brain import get_pump_brain, BrainMetrics
    BRAIN_AVAILABLE = True
    logger.info("Brain system available for API integration")
except ImportError:
    BRAIN_AVAILABLE = False
    logger.info("Brain system not available - using legacy methods only")

# Create blueprint
api_bp = Blueprint('api', __name__)


@api_bp.route('/pump_list')
def get_pump_list():
    """API endpoint to get list of all available pumps for selection. CACHED for performance."""
    try:
        # PERFORMANCE FIX: Add caching headers and optimize response
        response = make_response()
        
        # Check if catalog is already loaded to avoid redundant loading
        # CATALOG ENGINE RETIRED - USING BRAIN SYSTEM
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        
        # PERFORMANCE FIX: Create minimal pump list (reduce payload size)
        pump_list = []
        pump_models = brain.repository.get_pump_models()
        for pump in pump_models[:100]:  # Limit to 100 pumps for autocomplete
            pump_list.append({
                'pump_code': pump.get('pump_code', 'Unknown'),
                'manufacturer': pump.get('manufacturer', 'APE PUMPS'),
                'pump_type': pump.get('pump_type', 'Centrifugal')
            })
        
        # Sort by pump code
        pump_list.sort(key=lambda x: x['pump_code'])
        
        response.data = json.dumps({'pumps': pump_list, 'total': len(pump_models)})
        response.headers['Content-Type'] = 'application/json'
        # PERFORMANCE FIX: Add aggressive caching (5 minutes)
        response.headers['Cache-Control'] = 'public, max-age=300'
        response.headers['ETag'] = f'pump-list-v1-{len(pump_models)}'
        
        return response
    except Exception as e:
        logger.error(f"Error getting pump list: {str(e)}")
        return jsonify({'error': 'Failed to load pump list'}), 500


def generate_brain_chart_data(pump_code, flow_rate, head):
    """Generate chart data using Brain system"""
    try:
        brain = get_pump_brain()
        
        # Get pump data from Brain system
        target_pump = brain.repository.get_pump_by_code(pump_code)
        if not target_pump:
            return None
            
        # Get curves
        curves = target_pump.get('curves', [])
        if not curves:
            return None
            
        # Evaluate pump performance
        evaluation_result = brain.evaluate_pump(pump_code, flow_rate, head)
        
        # Build chart data structure
        chart_data = {
            'pump_code': pump_code,
            'pump_info': {
                'manufacturer': target_pump.get('manufacturer', 'APE PUMPS'),
                'series': target_pump.get('model_series', ''),
                'description': target_pump.get('pump_code', pump_code)
            },
            'curves': [],
            'operating_point': None,
            'brain_config': {
                'context': 'web',
                'margin': 0.1,
                'annotations': [],
                'axis_ranges': {
                    'flow': {'min': 0, 'max': 600},
                    'head': {'min': 0, 'max': 100},
                    'efficiency': {'min': 0, 'max': 100}
                },
                'display_options': {
                    'interactive': True,
                    'show_hover': True,
                    'show_toolbar': True,
                    'responsive': True
                }
            },
            'metadata': {
                'flow_units': 'm³/hr',
                'head_units': 'm',
                'efficiency_units': '%',
                'power_units': 'kW',
                'npshr_units': 'm',
                'brain_generated': True
            }
        }
        
        # Add curves data
        for i, curve in enumerate(curves):
            curve_data = {
                'curve_index': i,
                'impeller_size': curve.get('impeller_size', f'Curve {i+1}'),
                'impeller_diameter_mm': curve.get('impeller_diameter_mm', 0),
                'display_label': f"Head {curve.get('impeller_diameter_mm', 0)}mm",
                'transformation_applied': None,
                'flow_data': curve.get('flow_data', []),
                'head_data': curve.get('head_data', []),
                'efficiency_data': curve.get('efficiency_data', []),
                'power_data': curve.get('power_data', []),
                'npshr_data': curve.get('npshr_data', []),
                'is_selected': i == 0
            }
            chart_data['curves'].append(curve_data)
            
        # Add operating point from evaluation
        if evaluation_result:
            chart_data['operating_point'] = {
                'flow_m3hr': evaluation_result.get('flow_m3hr', flow_rate),
                'head_m': evaluation_result.get('head_m', head),
                'efficiency_pct': evaluation_result.get('efficiency_pct', 0),
                'power_kw': evaluation_result.get('power_kw', 0),
                'npshr_m': evaluation_result.get('npshr_m', 0),
                'impeller_size': evaluation_result.get('impeller_diameter_mm', 0),
                'sizing_info': {}
            }
            
        return chart_data
        
    except Exception as e:
        logger.error(f"Error generating Brain chart data: {str(e)}")
        return None


@api_bp.route('/chart_data/<path:pump_code>')
def get_chart_data(pump_code):
    """API endpoint to get chart data for interactive Plotly.js charts."""
    try:
        # Get site requirements from URL parameters
        flow_rate = request.args.get('flow', type=float, default=100)
        head = request.args.get('head', type=float, default=50)

        # Brain is now always active
        brain_mode = 'active'
        use_brain = BRAIN_AVAILABLE
        
        # Use Brain system to get pump data
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        target_pump = brain.repository.get_pump_by_code(pump_code)

        if not target_pump:
            logger.error(f"Chart API: Pump {pump_code} not found in catalog")
            response = jsonify({
                'error': f'Pump {pump_code} not found',
                'available_pumps': len(brain.repository.get_pump_models()),
                'suggestion': 'Please verify the pump code and try again'
            })
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response, 404

        # Use Brain system pump curves directly (dictionary format)
        curves = target_pump.get('curves', [])

        if not curves:
            response = jsonify({
                'error': f'No curve data available for pump {pump_code}'
            })
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response, 404

        # BRAIN SYSTEM ACTIVE MODE - Return Brain results directly
        if use_brain:
            try:
                # Generate chart data using Brain
                brain_chart_data = generate_brain_chart_data(pump_code, flow_rate, head)
                
                if brain_chart_data and brain_mode == 'active':
                    # Active mode - return Brain results directly
                    logger.info(f"Brain Active: Returning optimized chart data for {pump_code}")
                    response = make_response(json.dumps(brain_chart_data))
                    response.headers['Content-Type'] = 'application/json'
                    response.headers['Cache-Control'] = 'public, max-age=300'
                    return response
            except Exception as e:
                logger.error(f"Brain chart generation failed: {str(e)}")
                # Fall back to basic response
                
        # Basic fallback response
        return jsonify({'error': 'Chart data generation failed'}), 500

    except Exception as e:
        logger.error(f"Error in chart data API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500