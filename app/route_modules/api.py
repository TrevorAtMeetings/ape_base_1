import logging
import json
import math
import numpy as np
from flask import Blueprint, request, jsonify, make_response
from ..pump_brain import get_pump_brain

logger = logging.getLogger(__name__)

# Create the API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Brain availability check
try:
    BRAIN_AVAILABLE = get_pump_brain() is not None
    logger.info("Brain system available for API integration")
except Exception:
    BRAIN_AVAILABLE = False
    logger.error("Brain system not available - API will have limited functionality")


def sanitize_json_data(data):
    """Recursively sanitize data to replace NaN, Infinity, and None with valid JSON values"""
    if isinstance(data, dict):
        return {k: sanitize_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_data(item) for item in data]
    # NEW: Add explicit boolean handling for native and NumPy booleans
    elif isinstance(data, (bool, np.bool_)):
        return bool(data)  # Convert to native Python bool (True -> true, False -> false)
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None  # Return null for invalid numbers, which Plotly can handle
        return data
    elif data is None:
        return None  # Keep None as None for JSON compatibility
    else:
        return data


@api_bp.route('/chart_data/<path:pump_code>')
def get_chart_data(pump_code):
    """
    BRAIN-ONLY API: Get chart data for interactive Plotly.js charts.
    API layer is "dumb" - just passes through Brain intelligence.
    """
    try:
        flow_rate = request.args.get('flow', type=float, default=100)
        head = request.args.get('head', type=float, default=50)

        if not BRAIN_AVAILABLE:
            logger.error("Chart API call failed: Brain system is not available.")
            return jsonify({'error': 'The intelligence engine is currently offline.'}), 503

        # SINGLE SOURCE OF TRUTH: Brain handles ALL logic
        brain = get_pump_brain()
        pump = brain.repository.get_pump_by_code(pump_code)
        evaluation = brain.evaluate_pump(pump_code, flow_rate, head)
        
        if not pump or not evaluation:
            logger.warning(f"Brain could not generate data for pump {pump_code} at {flow_rate}m³/hr @ {head}m")
            return jsonify({'error': f'No valid performance data for pump {pump_code}'}), 404

        # One call to the Brain's chart intelligence - this is the ONLY logic
        chart_payload = brain.charts.generate_chart_data_payload(pump, evaluation)
        
        if not chart_payload:
            return jsonify({'error': f'Brain could not generate chart payload for {pump_code}'}), 404
        
        # Sanitize and return - API is now truly "dumb"
        sanitized_data = sanitize_json_data(chart_payload)
        response = make_response(json.dumps(sanitized_data))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minute cache
        return response

    except Exception as e:
        logger.error(f"Error in Brain-only chart API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/pump_search')
def pump_search():
    """
    SUPERIOR pump search endpoint - replaces outdated get_pump_list.
    Brain-powered intelligent search with autocomplete support.
    """
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', type=int, default=20)
        
        if not BRAIN_AVAILABLE:
            return jsonify({'error': 'Search engine offline'}), 503
            
        brain = get_pump_brain()
        
        if not query:
            # Return recent/popular pumps when no query
            all_pumps = brain.repository.get_pump_models()
            pump_list = [{'pump_code': p.get('pump_code', ''), 'manufacturer': p.get('manufacturer', 'APE')} 
                        for p in all_pumps[:limit]]
        else:
            # Brain-powered intelligent search - fallback to full list and filter
            all_pumps = brain.repository.get_pump_models()
            search_results = [p for p in all_pumps if query.upper() in p.get('pump_code', '').upper()]
            pump_list = [{'pump_code': p.get('pump_code', ''), 'manufacturer': p.get('manufacturer', 'APE')} 
                        for p in search_results[:limit]]
        
        return jsonify({
            'success': True,
            'query': query,
            'results': pump_list,
            'count': len(pump_list)
        })
        
    except Exception as e:
        logger.error(f"Error in pump search: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500


@api_bp.route('/pump_list')
def get_pump_list():
    """API endpoint to get a list of all available pumps for UI controls."""
    try:
        if not BRAIN_AVAILABLE:
            return jsonify({'error': 'Pump list unavailable'}), 503
            
        brain = get_pump_brain()
        
        # ONE SIMPLE CALL TO THE BRAIN - proper architecture
        pump_list = brain.get_all_pump_codes()
        
        response = make_response(json.dumps({'pumps': pump_list, 'total': len(pump_list)}))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # Force fresh data
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        logger.error(f"Error in pump list: {str(e)}")
        return jsonify({'error': 'Pump list failed'}), 500

@api_bp.route('/pumps/search')
def search_pumps():
    """API endpoint for pump autocomplete search"""
    try:
        if not BRAIN_AVAILABLE:
            return jsonify({'error': 'Pump search unavailable'}), 503
            
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'pumps': [], 'total': 0})
        
        brain = get_pump_brain()
        all_pumps = brain.get_all_pump_codes()
        
        # Get all pump models with full data for proper autocomplete
        all_pump_models = brain.repository.get_pump_models()
        
        # Filter pumps that match the query and format for autocomplete
        filtered_pumps = []
        for pump_model in all_pump_models:
            pump_code = pump_model.get('pump_code', '')
            pump_type = pump_model.get('pump_type', 'General')
            
            if query.lower() in pump_code.lower():
                filtered_pumps.append({
                    'pump_code': pump_code,
                    'pump_type': pump_type
                })
        
        # Limit results for performance
        max_results = 20
        limited_pumps = filtered_pumps[:max_results]
        
        response = make_response(json.dumps({
            'pumps': limited_pumps, 
            'total': len(limited_pumps),
            'has_more': len(filtered_pumps) > max_results
        }))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Cache-Control'] = 'no-cache'
        return response
        
    except Exception as e:
        logger.error(f"Error in pump search: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@api_bp.route('/ai_analysis_fast', methods=['POST'])
def ai_analysis_fast():
    """
    BRAIN-ONLY API: Generate AI-powered pump analysis content for report pages.
    API is "dumb" - delegates all intelligence to Brain system.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if not BRAIN_AVAILABLE:
            logger.error("AI Analysis API call failed: Brain system is not available.")
            return jsonify({'error': 'AI analysis engine is currently offline.'}), 503

        # Extract pump parameters
        pump_code = data.get('pump_code', '')
        flow = float(data.get('flow', 0))
        head = float(data.get('head', 0))
        efficiency = float(data.get('efficiency', 0))
        power = float(data.get('power', 0))
        npshr = float(data.get('npshr', 0))
        application = data.get('application', 'water')
        topic = data.get('topic', 'general')

        if not pump_code or flow <= 0 or head <= 0:
            return jsonify({'error': 'Invalid pump parameters'}), 400

        # SINGLE SOURCE OF TRUTH: Brain handles ALL AI analysis logic
        brain = get_pump_brain()
        
        # Import and create analysis request
        from ..brain.ai_analysis import AnalysisRequest
        request_obj = AnalysisRequest(
            pump_code=pump_code,
            flow_m3hr=flow,
            head_m=head,
            efficiency_pct=efficiency,
            power_kw=power,
            npshr_m=npshr,
            application=application,
            topic=topic
        )

        # One call to Brain's AI analysis intelligence - this is the ONLY logic
        ai_response = brain.ai_analysis.generate_pump_analysis(request_obj)
        
        if not ai_response:
            return jsonify({'error': 'Brain could not generate analysis'}), 404

        return jsonify({'response': ai_response})
        
    except Exception as e:
        logger.error(f"Error in Brain-only AI analysis API: {str(e)}")
        return jsonify({'error': 'Analysis service temporarily unavailable'}), 500


@api_bp.route('/convert_markdown', methods=['POST'])
def convert_markdown():
    """
    BRAIN-ONLY API: Convert markdown text to HTML for display in reports.
    API is "dumb" - delegates markdown conversion to Brain system.
    """
    try:
        data = request.get_json()
        if not data or 'markdown' not in data:
            return jsonify({'error': 'No markdown content provided'}), 400

        if not BRAIN_AVAILABLE:
            logger.error("Markdown conversion API call failed: Brain system is not available.")
            return jsonify({'error': 'Markdown conversion engine is currently offline.'}), 503

        markdown_text = data['markdown']
        
        # SINGLE SOURCE OF TRUTH: Brain handles markdown conversion
        brain = get_pump_brain()
        html = brain.ai_analysis.convert_markdown_to_html(markdown_text)
        
        return jsonify({'html': html})
        
    except Exception as e:
        logger.error(f"Error in Brain-only markdown conversion: {str(e)}")
        return jsonify({'html': data.get('markdown', 'Content unavailable')})


    except Exception as e:
        logger.error(f"Error getting pump list: {str(e)}")
        return jsonify({'error': 'Failed to load pump list'}), 500