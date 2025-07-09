import logging
from flask import Blueprint, request, jsonify, render_template
import os
import tempfile
from ..pump_import.ai_extractor import extract_pump_data_from_pdf
from ..pump_repository import insert_extracted_pump_data
import json

logger = logging.getLogger(__name__)

ai_extract_bp = Blueprint('ai_extract', __name__)

@ai_extract_bp.route('/ai-extract', methods=['GET'])
def ai_extract_page():
    """AI extraction page."""
    return render_template('ai_extract.html')

@ai_extract_bp.route('/ai_extract/extract', methods=['POST'])
def ai_extract_extract():
    logger.info("[AI Extract Routes] ===== EXTRACT REQUEST RECEIVED =====")
    logger.info(f"[AI Extract Routes] Request method: {request.method}")
    logger.info(f"[AI Extract Routes] Request headers: {dict(request.headers)}")
    logger.info(f"[AI Extract Routes] Request files: {list(request.files.keys())}")
    
    if 'pdf_file' not in request.files:
        logger.warning("[AI Extract Routes] No file part in request")
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['pdf_file']
    logger.info(f"[AI Extract Routes] File received: {file.filename}")
    logger.info(f"[AI Extract Routes] File content type: {file.content_type}")
    
    if file.filename == '':
        logger.warning("[AI Extract Routes] No selected file")
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"[AI Extract Routes] File is not a PDF: {file.filename}")
        return jsonify({'success': False, 'message': 'Only PDF files are allowed'}), 400
    
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file.filename)
    logger.info(f"[AI Extract Routes] Saving file to: {file_path}")
    
    try:
        file.save(file_path)
        logger.info(f"[AI Extract Routes] File saved successfully to: {file_path}")
        
        # Verify file was saved
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            logger.info(f"[AI Extract Routes] Saved file size: {file_size} bytes")
        else:
            logger.error(f"[AI Extract Routes] File was not saved to: {file_path}")
            return jsonify({'success': False, 'message': 'Failed to save file'}), 500
        
        logger.info(f"[AI Extract Routes] Starting extraction for: {file.filename}")
        extracted_data = extract_pump_data_from_pdf(file_path)
        logger.info(f"[AI Extract Routes] Extraction successful for: {file.filename}")
        logger.info(f"[AI Extract Routes] Extracted data keys: {list(extracted_data.keys())}")
        
        # Log summary of extracted data
        if 'pumpDetails' in extracted_data:
            pump_model = extracted_data['pumpDetails'].get('pumpModel', 'N/A')
            logger.info(f"[AI Extract Routes] Extracted pump model: {pump_model}")
        
        if 'curves' in extracted_data:
            curve_count = len(extracted_data['curves'])
            logger.info(f"[AI Extract Routes] Extracted {curve_count} curves")
        
        logger.info("[AI Extract Routes] ===== EXTRACT REQUEST COMPLETE =====")
        return jsonify({'success': True, 'data': extracted_data, 'filename': file.filename})
        
    except Exception as e:
        logger.error(f"[AI Extract Routes] Extraction failed for {file.filename}: {str(e)}")
        logger.error(f"[AI Extract Routes] Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"[AI Extract Routes] Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_extract_bp.route('/ai_extract/insert', methods=['POST'])
def ai_extract_insert():
    logger.info("[AI Extract Routes] ===== INSERT REQUEST RECEIVED =====")
    logger.info(f"[AI Extract Routes] Request method: {request.method}")
    logger.info(f"[AI Extract Routes] Request content type: {request.content_type}")
    
    try:
        data = request.get_json()
        logger.info(f"[AI Extract Routes] Request data type: {type(data)}")
        logger.info(f"[AI Extract Routes] Request data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        filename = data.get('filename') if isinstance(data, dict) else None
        logger.info(f"[AI Extract Routes] Filename from request: {filename}")
        
        if filename:
            data = {k: v for k, v in data.items() if k != 'filename'}
            logger.info(f"[AI Extract Routes] Data keys after removing filename: {list(data.keys())}")
        
        logger.info(f"[AI Extract Routes] Inserting data for file: {filename}")
        logger.info(f"[AI Extract Routes] Data structure: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # Log key data points before insertion
        if isinstance(data, dict):
            if 'pumpDetails' in data:
                pump_model = data['pumpDetails'].get('pumpModel', 'N/A')
                logger.info(f"[AI Extract Routes] Pump model to insert: {pump_model}")
            
            if 'curves' in data:
                curve_count = len(data['curves'])
                logger.info(f"[AI Extract Routes] Curves to insert: {curve_count}")
                for i, curve in enumerate(data['curves']):
                    impeller_diameter = curve.get('impellerDiameter', 'N/A')
                    flow_points = len(curve.get('flow', []))
                    logger.info(f"[AI Extract Routes] Curve {i+1}: diameter {impeller_diameter}, flow points {flow_points}")
        
        pump_id = insert_extracted_pump_data(data, filename=filename)
        logger.info(f"[AI Extract Routes] Inserted pump data successfully, pump_id: {pump_id}")
        logger.info("[AI Extract Routes] ===== INSERT REQUEST COMPLETE =====")
        return jsonify({'success': True, 'pump_id': pump_id})
        
    except Exception as e:
        logger.error(f"[AI Extract Routes] Insert failed: {str(e)}")
        logger.error(f"[AI Extract Routes] Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"[AI Extract Routes] Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500 