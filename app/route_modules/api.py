"""
API Routes
Routes for API endpoints including chart data, AI analysis, and pump data
BRAIN SYSTEM MIGRATION COMPLETED - All object method calls converted to dictionary access
"""
import logging
import time
import base64
import re
import os
import json
import math
import markdown2
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, make_response
from ..session_manager import safe_flash
from ..data_models import SiteRequirements
from ..utils import validate_site_requirements
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
        # from ..catalog_engine import get_catalog_engine
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


def sanitize_json_data(data):
    """Recursively sanitize data to replace NaN, Infinity, and None with valid JSON values"""
    if isinstance(data, dict):
        return {k: sanitize_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_data(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return 0.0  # Replace NaN/Infinity with 0 for engineering safety
        return data
    elif data is None:
        return 0.0  # Replace None with 0 for numeric fields
    else:
        return data


def generate_brain_chart_data(pump_code, flow_rate, head):
    """Generate chart data using Brain system - simplified, lean implementation"""
    try:
        brain = get_pump_brain()
        
        # Get pump data and evaluate performance - Brain handles all logic
        target_pump = brain.repository.get_pump_by_code(pump_code)
        if not target_pump:
            return None
            
        curves = target_pump.get('curves', [])
        if not curves:
            return None
            
        # Brain evaluation provides complete analysis
        evaluation_result = brain.evaluate_pump(pump_code, flow_rate, head)
        if not evaluation_result:
            return None
        
        # Build lean chart data structure - Brain provides all intelligence
        chart_data = {
            'pump_code': pump_code,
            'pump_info': {
                'manufacturer': target_pump.get('manufacturer', 'APE PUMPS'),
                'series': target_pump.get('model_series', ''),
                'description': target_pump.get('pump_code', pump_code)
            },
            'curves': [],
            'operating_point': {
                'flow_m3hr': evaluation_result.get('flow_m3hr', flow_rate),
                'head_m': evaluation_result.get('head_m', head),
                'efficiency_pct': evaluation_result.get('efficiency_pct', 0),
                'power_kw': evaluation_result.get('power_kw', 0),
                'npshr_m': evaluation_result.get('npshr_m', 0),
                'impeller_size': evaluation_result.get('impeller_diameter_mm', 0),
                'extrapolated': evaluation_result.get('extrapolated', False),
                'sizing_info': evaluation_result.get('sizing_info', {})
            },
            'brain_config': {
                'context': 'web',
                'annotations': [],
                'axis_ranges': {'flow': {'min': 0, 'max': 600}, 'head': {'min': 0, 'max': 100}},
                'display_options': {'interactive': True, 'show_hover': True}
            },
            'metadata': {
                'flow_units': 'm³/hr', 'head_units': 'm', 'efficiency_units': '%',
                'power_units': 'kW', 'npshr_units': 'm', 'brain_generated': True
            }
        }
        
        # Add BEP annotation if available
        if evaluation_result.get('bep_flow_m3hr') and evaluation_result.get('bep_head_m'):
            chart_data['brain_config']['annotations'].append({
                'type': 'point', 'x': evaluation_result['bep_flow_m3hr'],
                'y': evaluation_result['bep_head_m'], 'text': 'BEP', 'style': 'star', 'color': 'gold'
            })
        
        # Add curves - Brain handles all transformations internally
        for i, curve in enumerate(curves):
            chart_data['curves'].append({
                'curve_index': i,
                'impeller_size': curve.get('impeller_size', f'Curve {i+1}'),
                'impeller_diameter_mm': curve.get('impeller_diameter_mm', 0),
                'display_label': f"Head {curve.get('impeller_diameter_mm', 0)}mm",
                'flow_data': curve.get('flow_data', []),
                'head_data': curve.get('head_data', []),
                'efficiency_data': curve.get('efficiency_data', []),
                'power_data': curve.get('power_data', []),
                'npshr_data': curve.get('npshr_data', []),
                'is_selected': i == 0
            })
            
        return chart_data
        
    except Exception as e:
        logger.error(f"Error generating Brain chart data: {str(e)}")
        return None


@api_bp.route('/chart_data/<path:pump_code>')
def get_chart_data(pump_code):
    """
    API endpoint to get chart data for interactive Plotly.js charts.
    Powered exclusively by the Brain system.
    """
    try:
        flow_rate = request.args.get('flow', type=float, default=100)
        head = request.args.get('head', type=float, default=50)

        if not BRAIN_AVAILABLE:
            logger.error("Chart API call failed: Brain system is not available.")
            return jsonify({'error': 'The intelligence engine is currently offline.'}), 503

        # Directly call the Brain's chart generation function. This is now the ONLY path.
        chart_data = generate_brain_chart_data(pump_code, flow_rate, head)

        if not chart_data:
            logger.warning(f"Brain could not generate chart data for pump {pump_code} at the given duty point.")
            return jsonify({'error': f'No valid performance data could be generated for pump {pump_code}.'}), 404

        # The Brain has provided the complete, correct data. Send it to the user.
        # Sanitize data to prevent JSON serialization errors with NaN values
        sanitized_data = sanitize_json_data(chart_data)
        response = make_response(json.dumps(sanitized_data))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minute cache
        return response

    except Exception as e:
        logger.error(f"An unhandled error occurred in get_chart_data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An internal server error occurred.'}), 500


