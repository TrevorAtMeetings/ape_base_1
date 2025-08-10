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
    Generate AI-powered pump analysis content for report pages.
    Fast endpoint optimized for pump selection insights.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
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
        
        # Generate context-specific analysis prompt
        if topic == 'general':
            analysis_prompt = f"""
            Analyze the pump selection for {pump_code} at {flow} m³/hr and {head}m head:

            Performance Metrics:
            - Efficiency: {efficiency}%
            - Power Consumption: {power} kW
            - NPSHr: {npshr}m
            - Application: {application}

            Provide a brief technical analysis covering:
            1. Performance suitability for this duty point
            2. Energy efficiency assessment
            3. Key engineering considerations
            4. Operational recommendations

            Keep response under 300 words and use professional engineering language.
            """
        elif topic == 'efficiency':
            analysis_prompt = f"""
            Analyze the energy efficiency of pump {pump_code} at {flow} m³/hr @ {head}m:
            
            Current efficiency: {efficiency}%
            Power consumption: {power} kW
            
            Provide efficiency analysis including:
            1. Efficiency rating assessment
            2. Energy cost implications  
            3. Comparison to industry standards
            4. Optimization opportunities
            
            Keep response focused and under 200 words.
            """
        elif topic == 'application':
            analysis_prompt = f"""
            Evaluate pump {pump_code} for {application} application at {flow} m³/hr @ {head}m:
            
            Performance: {efficiency}% efficiency, {power} kW power, {npshr}m NPSHr
            
            Analyze:
            1. Application suitability
            2. Operating point assessment
            3. Reliability considerations
            4. Installation recommendations
            
            Keep response practical and under 250 words.
            """
        else:
            analysis_prompt = f"""
            Provide technical assessment of pump {pump_code} for {topic}:
            Operating conditions: {flow} m³/hr @ {head}m
            Performance: {efficiency}% efficiency, {power} kW power
            
            Focus on {topic} specific considerations and keep under 200 words.
            """

        # Import AI functionality
        try:
            from ..ai_model_router import AIModelRouter, ExtractionRequest, ModelProvider
            import os
            
            # Check if AI services are available
            openai_available = bool(os.getenv('OPENAI_API_KEY'))
            gemini_available = bool(os.getenv('GOOGLE_API_KEY'))
            
            if not (openai_available or gemini_available):
                return jsonify({
                    'response': f"**Analysis for {pump_code}**\n\nPerformance Summary:\n- Operating at {flow} m³/hr @ {head}m head\n- Efficiency: {efficiency}%\n- Power: {power} kW\n- NPSHr: {npshr}m\n\n*Note: AI analysis requires API key configuration.*"
                }), 200
            
            # Create extraction request
            request_obj = ExtractionRequest(
                content_type='text',
                user_preference=ModelProvider.AUTO,
                priority='speed',
                batch_size=1
            )
            
            router = AIModelRouter()
            selected_model, reason = router.select_model(request_obj)
            
            if selected_model == ModelProvider.OPENAI and openai_available:
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional pump engineer providing technical analysis. Use clear, concise language with engineering terminology."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                ai_response = response.choices[0].message.content
                
            elif selected_model == ModelProvider.GEMINI and gemini_available:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                response = model.generate_content(analysis_prompt)
                ai_response = response.text
                
            else:
                ai_response = f"**Analysis for {pump_code}**\n\nPerformance Summary:\n- Operating at {flow} m³/hr @ {head}m head\n- Efficiency: {efficiency}%\n- Power: {power} kW\n- NPSHr: {npshr}m\n\n*AI analysis temporarily unavailable.*"
                
        except ImportError:
            ai_response = f"**Technical Analysis - {pump_code}**\n\n**Operating Conditions:** {flow} m³/hr @ {head}m\n\n**Performance Metrics:**\n- Efficiency: {efficiency}%\n- Power: {power} kW\n- NPSHr: {npshr}m\n\n**Assessment:** This pump operates at the specified duty point with {efficiency}% efficiency. The power consumption of {power} kW indicates {'good' if efficiency > 75 else 'adequate' if efficiency > 65 else 'below optimal'} performance for this application.\n\n*Enhanced AI analysis available with API configuration.*"
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            ai_response = f"**Analysis for {pump_code}**\n\nTechnical Summary:\n- Flow: {flow} m³/hr\n- Head: {head}m\n- Efficiency: {efficiency}%\n- Power: {power} kW\n\nThis pump meets the basic requirements for the specified application."
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        logger.error(f"Error in AI analysis API: {str(e)}")
        return jsonify({'error': 'Analysis service temporarily unavailable'}), 500


@api_bp.route('/convert_markdown', methods=['POST'])
def convert_markdown():
    """
    Convert markdown text to HTML for display in reports.
    """
    try:
        data = request.get_json()
        if not data or 'markdown' not in data:
            return jsonify({'error': 'No markdown content provided'}), 400
        
        markdown_text = data['markdown']
        
        try:
            import markdown2
            html = markdown2.markdown(markdown_text)
        except ImportError:
            # Fallback: Simple markdown-like conversion
            html = markdown_text.replace('\n\n', '</p><p>')
            html = html.replace('\n', '<br>')
            html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
            html = html.replace('*', '<em>', 1).replace('*', '</em>', 1)
            html = f'<p>{html}</p>'
        
        return jsonify({'html': html})
        
    except Exception as e:
        logger.error(f"Error converting markdown: {str(e)}")
        return jsonify({'html': data.get('markdown', 'Content unavailable')})


    except Exception as e:
        logger.error(f"Error getting pump list: {str(e)}")
        return jsonify({'error': 'Failed to load pump list'}), 500