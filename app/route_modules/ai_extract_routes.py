# Applying the provided changes to enhance error handling and response in the AI extraction routes.
import logging
from flask import Blueprint, request, jsonify, render_template, session
import os
import tempfile
import threading
import signal
import traceback
import time
from ..pump_import.ai_extractor import extract_pump_data_from_pdf
from ..pump_repository import insert_extracted_pump_data

def get_user_friendly_error_message(exception, model_choice):
    """
    Convert technical exceptions into user-friendly error messages
    """
    error_str = str(exception).lower()
    exception_type = type(exception).__name__

    # Timeout errors
    if exception_type == "TimeoutError" or "timeout" in error_str:
        return f"The {model_choice.upper()} AI model timed out while processing your PDF. This usually happens with complex technical diagrams. The system automatically tried an alternative approach, but both failed. Please try with a simpler PDF or contact support."

    # Rate limiting errors
    if "rate limit" in error_str or "429" in error_str:
        return f"The {model_choice.upper()} AI service is currently experiencing high demand. Please wait a moment and try again. The system attempted automatic fallback but both AI models are currently rate-limited."

    # JSON parsing errors (the main issue we're fixing)
    if "json" in error_str and "token" in error_str:
        return f"The {model_choice.upper()} AI model returned an invalid response format. This typically occurs when the AI service is experiencing issues or the PDF content is too complex. The system attempted to use an alternative AI model but both failed. Please try again in a few minutes."

    # Content policy errors
    if "content policy" in error_str or "safety" in error_str:
        return f"The {model_choice.upper()} AI model flagged this content for review. This sometimes happens with technical documents. The system tried an alternative AI model but was unable to process this PDF. Please ensure the PDF contains standard pump performance data."

    # API key or authentication errors
    if "api key" in error_str or "unauthorized" in error_str or "authentication" in error_str:
        return "AI service authentication failed. This is a system configuration issue. Please contact support."

    # File or processing errors
    if "file" in error_str or "pdf" in error_str:
        return "There was an issue processing your PDF file. Please ensure the file is a valid PDF containing pump performance curves and try again."

    # Generic AI extraction errors
    if "both models failed" in error_str:
        return "Both OpenAI and Google AI models were unable to process this PDF. This may be due to high API demand, complex diagram content, or temporary service issues. Please try again in a few minutes or contact support if the issue persists."

    # Default fallback
    return f"AI extraction encountered an unexpected error. The system tried multiple approaches but was unable to process this PDF. Error details: {str(exception)[:200]}... Please try again or contact support if the issue persists."


import json
import traceback
import time

logger = logging.getLogger(__name__)

# Import the new AI model router
from ..ai_model_router import get_ai_model_router, ModelProvider, ExtractionRequest

ai_extract_bp = Blueprint('ai_extract', __name__)

@ai_extract_bp.route('/ai-extract', methods=['GET'])
def ai_extract_page():
    """AI extraction page with model selection and previous data restoration."""
    router = get_ai_model_router()
    model_comparison = router.get_model_comparison()
    
    # Check if user is returning from editor (only restore data in this case)
    from_editor = request.args.get('from_editor', 'false').lower() == 'true'
    
    # Check for previous extraction data in session
    previous_data = None
    extraction_id = session.get('last_extraction_id')
    
    logger.info(f"[AI Extract] Page load - from_editor: {from_editor}")
    logger.info(f"[AI Extract] Page load - Session keys: {list(session.keys())}")
    logger.info(f"[AI Extract] Page load - last_extraction_id: {extraction_id}")
    
    # Only restore data if coming from editor
    if from_editor and extraction_id:
        try:
            # Try to load from file storage first
            import os
            import json
            extraction_file = f"app/static/temp/extractions/{extraction_id}.json"
            
            logger.info(f"[AI Extract] Looking for extraction file: {extraction_file}")
            
            if os.path.exists(extraction_file):
                with open(extraction_file, 'r') as f:
                    previous_data = json.load(f)
                logger.info(f"[AI Extract] Restored previous extraction data from file: {extraction_id}")
                logger.info(f"[AI Extract] Data keys: {list(previous_data.keys()) if isinstance(previous_data, dict) else 'Not a dict'}")
            else:
                logger.warning(f"[AI Extract] Extraction file not found: {extraction_file}")
                # Fallback to session storage
                session_key = f'extraction_{extraction_id}'
                if session_key in session:
                    previous_data = session[session_key]
                    logger.info(f"[AI Extract] Restored previous extraction data from session: {extraction_id}")
                else:
                    logger.warning(f"[AI Extract] Session key not found: {session_key}")
        except Exception as e:
            logger.warning(f"[AI Extract] Failed to restore previous extraction data: {e}")
            logger.warning(f"[AI Extract] Full traceback: {traceback.format_exc()}")
            # Clear invalid session data
            session.pop('last_extraction_id', None)
    else:
        if not from_editor:
            logger.info(f"[AI Extract] Not from editor - skipping session restoration")
        else:
            logger.info(f"[AI Extract] No previous extraction data found in session")
    
    logger.info(f"[AI Extract] Rendering template with data: {previous_data is not None}")
    if previous_data:
        logger.info(f"[AI Extract] Data keys: {list(previous_data.keys()) if isinstance(previous_data, dict) else 'Not a dict'}")
    return render_template('ai_extract.html', data=previous_data, model_comparison=model_comparison)

@ai_extract_bp.route('/ai_extract/extract', methods=['POST'])
def ai_extract_extract():
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400

        file = request.files['pdf_file']

        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'message': 'Only PDF files are allowed'}), 400

        # Check file size (limit to 10MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({'success': False, 'message': 'File too large. Maximum size is 10MB'}), 400

        # Get extraction parameters from form data
        user_model_choice = request.form.get('model_choice', 'auto')
        extraction_priority = request.form.get('priority', 'balanced')
        
        # Use AI model router for intelligent model selection
        try:
            router = get_ai_model_router()
        except Exception as router_error:
            logger.error(f"[AI Extract] Router initialization failed: {router_error}")
            return jsonify({
                'success': False,
                'message': 'AI model router initialization failed',
                'error_type': 'router_error',
                'retry_suggestion': 'Try again in a moment'
            }), 500
        
        # Map form values to router enums
        model_preference = ModelProvider.AUTO
        if user_model_choice == 'openai':
            model_preference = ModelProvider.OPENAI
        elif user_model_choice == 'gemini':
            model_preference = ModelProvider.GEMINI
        elif user_model_choice == 'anthropic':
            model_preference = ModelProvider.ANTHROPIC
        
        # Create extraction request context
        try:
            extraction_request = ExtractionRequest(
                file_size=file_size,
                file_type='pdf',
                user_preference=model_preference,
                priority=extraction_priority
            )
        except Exception as request_error:
            logger.error(f"[AI Extract] Request creation failed: {request_error}")
            return jsonify({
                'success': False,
                'message': 'Request creation failed',
                'error_type': 'request_error',
                'retry_suggestion': 'Try again in a moment'
            }), 500
        
        # Get model recommendation
        selected_model, selection_reason = router.select_model(extraction_request)
        model_choice = selected_model.value
        
        logger.info(f"[AI Extract] Model selection: {model_choice} - {selection_reason}")

        import os
        import tempfile
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, file.filename)
        
        # Initialize timing variables early to avoid scope issues  
        import time
        start_time = time.time()
        extraction_success = False
        accuracy_score = 0.0
        estimated_cost = 0.0

        try:
            file.save(file_path)

            # Verify file was saved
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
            else:
                return jsonify({'success': False, 'message': 'Failed to save file'}), 500

            # Add timeout handling to prevent hanging extraction
            import signal
            import threading
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Extraction timed out after 120 seconds")
            
            # Set up timeout for the extraction process - reduced to prevent Gunicorn worker timeout
            extraction_timeout = 60  # Increased to 60 seconds to allow more time for extraction
            logger.info(f"[AI Extract] Starting extraction with {extraction_timeout}s timeout using {model_choice}")
            
            try:
                # Use threading for better timeout control
                result = [None]
                exception = [None]
                
                def extraction_thread():
                    try:
                        result[0] = extract_pump_data_from_pdf(file_path, model_choice)
                    except Exception as e:
                        logger.error(f"[AI Extract] Exception in extraction thread: {e}")
                        logger.error(f"[AI Extract] Full traceback: {traceback.format_exc()}")
                        exception[0] = e
                
                thread = threading.Thread(target=extraction_thread)
                thread.daemon = True
                thread.start()
                thread.join(timeout=extraction_timeout)
                
                if thread.is_alive():
                    logger.error(f"[AI Extract] Extraction timed out after {extraction_timeout}s")
                    raise TimeoutError(f"Extraction process timed out after {extraction_timeout} seconds")
                
                if exception[0]:
                    raise exception[0]
                
                extracted_data = result[0]
                extraction_success = True
                
                # Calculate quality metrics for performance tracking
                if isinstance(extracted_data, dict):
                    accuracy_score = calculate_extraction_quality(extracted_data)
                    estimated_cost = estimate_extraction_cost(model_choice, file_size)
                
                processing_time = time.time() - start_time
                
                # Update router performance metrics
                router.update_performance_metrics(
                    selected_model,
                    extraction_success,
                    processing_time,
                    accuracy_score,
                    estimated_cost
                )
                
            except TimeoutError:
                # Update router with timeout failure
                processing_time = time.time() - start_time
                router.update_performance_metrics(
                    selected_model, False, processing_time, 0.0, 0.0
                )
                raise  # Re-raise timeout errors
        except Exception as e:
            # Update router with general failure
            try:
                processing_time = time.time() - start_time
                router.update_performance_metrics(
                    selected_model, False, processing_time, 0.0, 0.0
                )
            except Exception as perf_error:
                logger.warning(f"[AI Extract] Performance tracking failed: {perf_error}")
            logger.error(f"[AI Extract] Extraction failed: {e}")
            logger.error(f"[AI Extract] Full traceback: {traceback.format_exc()}")
            raise

        # Log summary of extracted data with safe access - CHECK FOR APE PROCESSOR OUTPUT
        pump_model = "Unknown"
        
        # Check if this is processed data from APE processor (new structure)
        if isinstance(extracted_data, dict) and 'pump_details' in extracted_data:
            pump_details = extracted_data.get('pump_details', {})
            pump_model = pump_details.get('pumpModel', 'Unknown')
        # Fallback to old structure
        elif isinstance(extracted_data, dict) and 'pumpDetails' in extracted_data:
            pump_model = extracted_data['pumpDetails'].get('pumpModel', 'Unknown')

        logger.info(f"[AI Extract] Successfully extracted pump: {pump_model}")

        # Enhanced logging for curve extraction quality - FIXED FOR APE PROCESSOR
        curves = []
        total_points = 0
        
        # Check for APE processor output structure first
        if isinstance(extracted_data, dict) and 'curves' in extracted_data:
            curves = extracted_data.get('curves', [])
            
            if curves:
                logger.info(f"[AI Extract] Processing {len(curves)} curves")
                for i, curve in enumerate(curves):
                    # APE processor uses 'performance_points' (underscore, not camelCase)
                    performance_points = curve.get('performance_points', [])
                    
                    points_count = len(performance_points)
                    total_points += points_count
                    impeller_dia = curve.get('impellerDiameter', 0)
                    logger.info(f"[AI Extract] Curve {i+1}: Impeller {impeller_dia}mm, {points_count} points")
                    
                    # Log sample points for debugging
                    if performance_points:
                        sample_point = performance_points[0]
                        logger.info(f"[AI Extract] Sample point: Flow={sample_point.get('flow', 0)}, Head={sample_point.get('head', 0)}, Eff={sample_point.get('efficiency', 0)}")
                
                logger.info(f"[AI Extract] Total: {len(curves)} curves with {total_points} data points")
            else:
                logger.warning("[AI Extract] No curves found in processed data")
        else:
            logger.warning("[AI Extract] No curves found in extracted data")

        # Enhanced BEP extraction logging - FIXED FOR APE PROCESSOR OUTPUT
        bep_markers = []
        main_bep_flow = 0
        main_bep_head = 0
        
        if isinstance(extracted_data, dict):
            # Check for APE processor output structure first
            if 'bep_data' in extracted_data:
                bep_data = extracted_data.get('bep_data', {})
                main_bep_flow = bep_data.get('bepFlow', 0)
                main_bep_head = bep_data.get('bepHead', 0)
                # APE processor might store BEP markers differently
                bep_markers = bep_data.get('bepMarkers', [])
            else:
                # Fallback to old structure
                specs = extracted_data.get('specifications', {})
                bep_markers = specs.get('bepMarkers', [])
                main_bep_flow = specs.get('bepFlow', 0)
                main_bep_head = specs.get('bepHead', 0)
            
        if bep_markers:
            logger.info(f"[AI Extract] Extracted {len(bep_markers)} BEP markers")
            for marker in bep_markers:
                logger.info(f"[AI Extract] BEP: {marker.get('impellerDiameter', 0)}mm - Flow={marker.get('bepFlow', 0)}, Head={marker.get('bepHead', 0)}, Eff={marker.get('bepEfficiency', 0)}%")
        
        if main_bep_flow > 0 or main_bep_head > 0:
            logger.info(f"[AI Extract] Main BEP: Flow={main_bep_flow}, Head={main_bep_head}")
        else:
            logger.warning("[AI Extract] Main BEP values are zero or missing")

        # Validate extraction quality before returning success
        if not extracted_data or not isinstance(extracted_data, dict):
            logger.error("[AI Extract] AI extraction returned invalid or empty data")
            return jsonify({
                'success': False,
                'message': 'AI extraction failed to return valid pump data. Please check the PDF quality and try again.',
                'error_type': 'invalid_extraction',
                'retry_suggestion': 'Ensure the PDF contains clear pump performance curves'
            }), 400

        # Check for minimal required data with more flexible validation - FIXED FOR APE PROCESSOR
        pump_details = {}
        curves = []
        specifications = {}
        
        # Handle APE processor output structure
        if isinstance(extracted_data, dict):
            if 'pump_details' in extracted_data:
                # APE processor output structure
                pump_details = extracted_data.get('pump_details', {})
                curves = extracted_data.get('curves', [])
                specifications = extracted_data.get('bep_data', {})
            else:
                # Fallback to old structure
                pump_details = extracted_data.get('pumpDetails', {})
                curves = extracted_data.get('curves', [])
                specifications = extracted_data.get('specifications', {})
        
        # Count total performance points across all curves - FIXED FOR APE PROCESSOR
        total_performance_points = 0
        for curve in curves:
            # APE processor uses 'performance_points' (underscore)
            points = curve.get('performance_points', [])
            if not points:
                # Fallback to old structure
                points = curve.get('performancePoints', [])
            total_performance_points += len(points)
        
        # More flexible validation - accept if we have either:
        # 1. Pump details with some specifications, OR
        # 2. At least one curve with performance points, OR
        # 3. BEP markers indicating successful extraction
        has_pump_info = bool(pump_details.get('pumpModel') or pump_details.get('manufacturer'))
        has_curve_data = total_performance_points > 0
        has_bep_data = bool(specifications.get('bepMarkers', []) or specifications.get('bepFlow', 0) > 0)
        
        if not (has_pump_info or has_curve_data or has_bep_data):
            logger.error(f"[AI Extract] Insufficient data extracted - PumpInfo: {has_pump_info}, CurveData: {has_curve_data} ({total_performance_points} points), BEP: {has_bep_data}")
            return jsonify({
                'success': False,
                'message': 'AI extraction completed but found insufficient pump data. The PDF may not contain clear pump performance information.',
                'error_type': 'insufficient_data',
                'retry_suggestion': 'Ensure the PDF contains clear pump performance curves and specifications, or try with a different AI model',
                'debug_info': {
                    'has_pump_info': has_pump_info,
                    'has_curve_data': has_curve_data,
                    'total_points': total_performance_points,
                    'has_bep_data': has_bep_data
                }
            }), 400
        
        logger.info(f"[AI Extract] Data validation passed - PumpInfo: {has_pump_info}, CurveData: {has_curve_data} ({total_performance_points} points), BEP: {has_bep_data}")

        # Always return success response for valid extraction
        # Store extraction data for editing (avoid session for large data)
        import time
        extraction_id = f"extract_{int(time.time())}"
        
        # Store in file system instead of session to avoid cookie size limits
        try:
            import os
            import json
            temp_dir = "app/static/temp/extractions"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Add filename to extracted data for preview
            extracted_data['filename'] = file.filename
            
            extraction_file = os.path.join(temp_dir, f"{extraction_id}.json")
            with open(extraction_file, 'w') as f:
                json.dump(extracted_data, f, indent=2)
                
            # Store only the extraction ID in session
            session['last_extraction_id'] = extraction_id
            logger.info(f"[AI Extract] Stored extraction data in file: {extraction_file}")
            logger.info(f"[AI Extract] Set session last_extraction_id: {extraction_id}")
            logger.info(f"[AI Extract] Session keys after setting: {list(session.keys())}")
            
        except Exception as storage_error:
            logger.error(f"[AI Extract] Failed to store extraction data: {storage_error}")
            # Fallback: store minimal data in session
            session[f'extraction_{extraction_id}'] = {
                'pump_details': extracted_data.get('pump_details', {}),
                'extraction_id': extraction_id
            }
        
        response_data = {
            'success': True, 
            'data': extracted_data, 
            'filename': file.filename,
            'extraction_id': extraction_id,
            'edit_url': f'/pump_editor/{extraction_id}',
            'preview_url': f'/ai_extract/preview/{extraction_id}'
        }
        return jsonify(response_data)

    except Exception as extraction_error:
        # Handle extraction-specific errors with enhanced error details
        logger.error(f"[AI Extract] Extraction failed with {model_choice}: {extraction_error}")
        logger.error(f"[AI Extract] Full traceback: {traceback.format_exc()}")

        # Try to categorize the error for better user feedback
        error_str = str(extraction_error).lower()

        if "specialist" in error_str:
            # Specialist processing failed, but we have fallback
            return jsonify({
                'success': False,
                'message': 'Advanced extraction failed, but automatic fallback succeeded. Some data may be incomplete.',
                'error_type': 'specialist_fallback',
                'retry_suggestion': 'Try again for full specialist processing or accept current results'
            }), 206  # Partial content
        else:
            # Handle generic extraction errors with JSON response
            return jsonify({
                'success': False,
                'message': get_user_friendly_error_message(extraction_error, model_choice),
                'error_type': 'extraction_error',
                'retry_suggestion': 'Try with a different AI model or check PDF quality',
                'fallback_model': 'gemini' if model_choice == 'openai' else 'openai'
            }), 500

    except TimeoutError as e:
        logger.error(f"[AI Extract] Timeout error: {e}")
        error_message = f"Extraction timed out: {str(e)}"
        return jsonify({
            'success': False, 
            'message': error_message,
            'error_type': 'timeout',
            'retry_suggestion': 'Try reducing the PDF size or try again in a few minutes',
            'fallback_model': 'gemini' if model_choice == 'openai' else 'openai'
        }), 408

    except ValueError as e:
        logger.error(f"[AI Extract] Value error: {e}")
        error_str = str(e).lower()

        if "rate_limit" in error_str or "429" in error_str or "quota" in error_str:
            # Check if it's Gemini quota exhaustion
            if "gemini" in error_str.lower() or "google" in error_str.lower():
                return jsonify({
                    'success': False,
                    'message': 'Gemini API daily quota (50 requests) exceeded. Automatic fallback to OpenAI failed.',
                    'error_type': 'quota_exhausted',
                    'retry_suggestion': 'Try again tomorrow when Gemini quota resets, or upgrade to Gemini Pro',
                    'fallback_model': 'openai',
                    'quota_info': 'Free Gemini tier: 50 requests/day limit reached'
                }), 429
            else:
                return jsonify({
                    'success': False,
                    'message': 'API rate limit exceeded. Please wait a moment and try again.',
                    'error_type': 'rate_limit',
                    'retry_suggestion': 'Wait 30-60 seconds before retrying',
                    'fallback_model': 'gemini' if model_choice == 'openai' else 'openai'
                }), 429
        elif "content_policy" in error_str or "safety" in error_str:
            return jsonify({
                'success': False,
                'message': 'Content policy restriction detected. Technical documents should be allowed.',
                'error_type': 'content_policy',
                'retry_suggestion': 'Try with a different AI model or contact support',
                'fallback_model': 'gemini' if model_choice == 'openai' else 'openai'
            }), 400
        elif "json" in error_str or "parsing" in error_str:
            return jsonify({
                'success': False,
                'message': 'AI response parsing failed. The model may have returned malformed data.',
                'error_type': 'parsing_error',
                'retry_suggestion': 'Try again with a different model or simpler PDF',
                'fallback_model': 'gemini' if model_choice == 'openai' else 'openai'
            }), 400
        else:
            logger.error(f"Extraction error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'message': f'Extraction error: {str(e)[:200]}...',
                'error_type': 'extraction_error',
                'retry_suggestion': 'Try with a different AI model or check PDF quality',
                'fallback_model': 'gemini' if model_choice == 'openai' else 'openai'
            }), 400

    except Exception as e:
        logger.error(f"[AI Extract] Unexpected error: {e}")
        logger.error(f"[AI Extract] Error type: {type(e).__name__}")
        return jsonify({
            'success': False,
            'message': f'Unexpected error during extraction: {str(e)[:200]}...',
            'error_type': 'unexpected_error',
            'retry_suggestion': 'Please try again or contact support if the issue persists',
            'fallback_model': 'gemini' if model_choice == 'openai' else 'openai'
        }), 500
    
    except Exception as e:
        logger.error(f"[AI Extract] Unexpected error: {e}")
        logger.error(f"[AI Extract] Error type: {type(e).__name__}")
        return jsonify({
            'success': False,
            'message': get_user_friendly_error_message(e, 'auto'),
            'error_type': 'unexpected_error',
            'retry_suggestion': 'Please try again or contact support if the issue persists'
        }), 500

@ai_extract_bp.route('/ai_extract/insert', methods=['POST'])
def ai_extract_insert():

    try:
        data = request.get_json()

        filename = data.get('filename') if isinstance(data, dict) else None

        if filename:
            data = {k: v for k, v in data.items() if k != 'filename'}

        # Log key data points before insertion
        if isinstance(data, dict):
            if 'pumpDetails' in data:
                pump_model = data['pumpDetails'].get('pumpModel', 'N/A')

            if 'curves' in data:
                curve_count = len(data['curves'])
                for i, curve in enumerate(data['curves']):
                    impeller_diameter = curve.get('impellerDiameter', 'N/A')
                    flow_points = len(curve.get('flow', []))

        pump_id = insert_extracted_pump_data(data, filename=filename)
        return jsonify({'success': True, 'pump_id': pump_id})

    except Exception as e:
        logger.error(f"[AI Extract Routes] Insert failed: {str(e)}")
        logger.error(f"[AI Extract Routes] Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"[AI Extract Routes] Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500 

@ai_extract_bp.route('/ai_extract/model_comparison', methods=['GET'])
def get_model_comparison():
    """API endpoint to get model performance comparison data."""
    try:
        from app.ai_model_router import get_ai_model_router
        router = get_ai_model_router()
        comparison_data = router.get_model_comparison()
        return jsonify({'success': True, 'data': comparison_data})
    except Exception as e:
        logger.error(f"[Model Comparison] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_extract_bp.route('/ai_extract/store_preview', methods=['POST'])
def store_pdf_preview():
    """Store PDF preview image for an extraction."""
    try:
        data = request.get_json()
        extraction_id = data.get('extraction_id')
        preview_data = data.get('preview_data')  # Base64 image data
        
        if not extraction_id or not preview_data:
            return jsonify({'success': False, 'message': 'Missing extraction_id or preview_data'}), 400
        
        # Store preview image
        import os
        import base64
        preview_dir = "static/temp/previews"
        os.makedirs(preview_dir, exist_ok=True)
        
        preview_file = os.path.join(preview_dir, f"{extraction_id}.png")
        
        # Remove data URL prefix if present
        if preview_data.startswith('data:image/'):
            preview_data = preview_data.split(',')[1]
        
        # Decode and save image
        with open(preview_file, 'wb') as f:
            f.write(base64.b64decode(preview_data))
        
        logger.info(f"[AI Extract] Stored PDF preview: {preview_file}")
        return jsonify({'success': True, 'preview_url': f'/ai_extract/preview/{extraction_id}'})
        
    except Exception as e:
        logger.error(f"[AI Extract] Failed to store preview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_extract_bp.route('/ai_extract/preview/<extraction_id>')
def get_pdf_preview(extraction_id):
    """Serve PDF preview image for an extraction."""
    try:
        import os
        from flask import send_file
        # Use absolute path to ensure correct file location
        preview_file = os.path.abspath(f"static/temp/previews/{extraction_id}.png")
        if os.path.exists(preview_file):
            return send_file(preview_file, mimetype='image/png')
        else:
            # Return a placeholder image or 404
            return jsonify({'error': 'Preview not found'}), 404
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[AI Extract] Failed to serve preview: {e}")
        return jsonify({'error': str(e)}), 500



def calculate_extraction_quality(extracted_data):
    """Calculate quality score for extracted data"""
    if not isinstance(extracted_data, dict):
        return 0.0
    
    score = 0.0
    total_checks = 0
    
    # Check pump details completeness
    if 'pumpDetails' in extracted_data:
        details = extracted_data['pumpDetails']
        checks = ['pumpModel', 'manufacturer', 'pumpType']
        for check in checks:
            total_checks += 1
            if check in details and details[check]:
                score += 1.0
    
    # Check curves completeness
    if 'curves' in extracted_data:
        curves = extracted_data['curves']
        if isinstance(curves, list) and len(curves) > 0:
            total_checks += 1
            score += 1.0
            
            # Check curve data quality
            for curve in curves:
                if 'performancePoints' in curve and len(curve['performancePoints']) > 5:
                    total_checks += 1
                    score += 1.0
    
    return score / total_checks if total_checks > 0 else 0.0

def estimate_extraction_cost(model_choice, file_size_bytes):
    """Estimate cost based on model and file size"""
    base_costs = {
        'openai': 0.15,  # Base cost for OpenAI
        'gemini': 0.08   # Base cost for Gemini
    }
    
    # Adjust for file size (larger files cost more)
    size_mb = file_size_bytes / (1024 * 1024)
    size_multiplier = 1.0 + (size_mb / 10.0)  # 10% increase per MB
    
    return base_costs.get(model_choice, 0.10) * size_multiplier