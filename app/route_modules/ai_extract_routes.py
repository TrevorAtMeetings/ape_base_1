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
    
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        file.save(file_path)
        
        # Verify file was saved
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
        else:
            return jsonify({'success': False, 'message': 'Failed to save file'}), 500
        
        extracted_data = extract_pump_data_from_pdf(file_path)
        
        # Log summary of extracted data
        if 'pumpDetails' in extracted_data:
            pump_model = extracted_data['pumpDetails'].get('pumpModel', 'N/A')
        
        if 'curves' in extracted_data:
            curve_count = len(extracted_data['curves'])
        
        return jsonify({'success': True, 'data': extracted_data, 'filename': file.filename})
        
    except Exception as e:
        logger.error(f"[AI Extract Routes] Extraction failed for {file.filename}: {str(e)}")
        logger.error(f"[AI Extract Routes] Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"[AI Extract Routes] Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"[AI Extract Routes] Cleaned up temporary file: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"[AI Extract Routes] Failed to clean up temporary file: {cleanup_error}")

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