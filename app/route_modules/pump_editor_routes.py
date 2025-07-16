"""
Pump Data Editor Routes
Handles human-in-the-loop editing of extracted pump data
"""
import logging
from flask import Blueprint, render_template, request, jsonify, session
import json
from datetime import datetime
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

# Create blueprint
pump_editor_bp = Blueprint('pump_editor', __name__)

# In-memory storage for edited data (in production, use database)
edited_pump_data = {}

@pump_editor_bp.route('/pump_editor')
def pump_editor():
    """
    Display the pump data editor interface
    """
    try:
        logger.info("[Pump Editor] Loading pump editor interface")
        
        # Get pump data from session or use default
        pump_data = session.get('extracted_pump_data', {})
        
        # If no data in session, check for latest extraction
        if not pump_data:
            pump_data = get_default_pump_data()
        
        return render_template('pump_data_editor.html', 
                             pump_data=pump_data,
                             title="Pump Data Editor")
        
    except Exception as e:
        logger.error(f"[Pump Editor] Error loading editor: {e}")
        return render_template('error.html', 
                             error_message=f"Error loading pump editor: {str(e)}")

@pump_editor_bp.route('/pump_editor/<extraction_id>')
def pump_editor_with_id(extraction_id):
    """
    Load specific extraction data for editing
    """
    try:
        logger.info(f"[Pump Editor] Loading extraction {extraction_id} for editing")
        
        # Load extraction data from storage
        pump_data = load_extraction_data(extraction_id)
        
        if not pump_data:
            # Provide helpful error message with recovery options
            error_message = f"""Extraction {extraction_id} not found. This may have occurred because:
            
• The extraction data was too large for session storage
• The browser rejected the session cookie
• The extraction data expired or was cleared

You can:
• Return to the AI extraction page to re-extract your PDF
• Check if you have any recent extractions available
• Contact support if this issue persists"""
            
            return render_template('error.html', 
                                 error_message=error_message,
                                 recovery_options=[
                                     {'text': 'New AI Extraction', 'url': '/ai-extract'},
                                     {'text': 'Return to Home', 'url': '/'}
                                 ])
        
        return render_template('pump_data_editor.html', 
                             pump_data=pump_data,
                             extraction_id=extraction_id,
                             title=f"Edit Extraction {extraction_id}")
        
    except Exception as e:
        logger.error(f"[Pump Editor] Error loading extraction {extraction_id}: {e}")
        return render_template('error.html', 
                             error_message=f"Error loading extraction: {str(e)}",
                             recovery_options=[
                                 {'text': 'New AI Extraction', 'url': '/ai-extract'},
                                 {'text': 'Return to Home', 'url': '/'}
                             ])

@pump_editor_bp.route('/api/save_pump_data', methods=['POST'])
def save_pump_data():
    """
    Save edited pump data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Validate data structure
        validation_result = validate_pump_data(data)
        if not validation_result['valid']:
            return jsonify({'success': False, 'error': validation_result['error']})
        
        # Generate unique ID for this save
        save_id = generate_save_id()
        
        # Add metadata
        enhanced_data = {
            'save_id': save_id,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'user_modifications': True
        }
        
        # Save to storage
        save_result = save_to_storage(enhanced_data)
        
        if save_result['success']:
            # Update session with latest data
            session['edited_pump_data'] = data
            session['last_save_id'] = save_id
            
            logger.info(f"[Pump Editor] Successfully saved pump data with ID: {save_id}")
            
            return jsonify({
                'success': True, 
                'save_id': save_id,
                'message': 'Data saved successfully'
            })
        else:
            return jsonify({'success': False, 'error': save_result['error']})
            
    except Exception as e:
        logger.error(f"[Pump Editor] Error saving pump data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@pump_editor_bp.route('/api/load_extraction_data/<extraction_id>')
def load_extraction_data_api(extraction_id):
    """
    Load extraction data for editing via API
    """
    try:
        data = load_extraction_data(extraction_id)
        
        if data:
            return jsonify({'success': True, 'data': data})
        else:
            return jsonify({'success': False, 'error': 'Extraction not found'})
            
    except Exception as e:
        logger.error(f"[Pump Editor] Error loading extraction {extraction_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@pump_editor_bp.route('/api/validate_pump_data', methods=['POST'])
def validate_pump_data_api():
    """
    Validate pump data structure via API
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'valid': False, 'error': 'No data provided'})
        
        result = validate_pump_data(data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"[Pump Editor] Error validating pump data: {e}")
        return jsonify({'valid': False, 'error': str(e)})

@pump_editor_bp.route('/api/generate_pdf_report', methods=['POST'])
def generate_pdf_report():
    """
    Generate PDF report from edited data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Validate data first
        validation_result = validate_pump_data(data)
        if not validation_result['valid']:
            return jsonify({'success': False, 'error': validation_result['error']})
        
        # Generate PDF report
        report_result = generate_pdf_from_edited_data(data)
        
        if report_result['success']:
            return jsonify({
                'success': True, 
                'pdf_url': report_result['pdf_url'],
                'filename': report_result['filename']
            })
        else:
            return jsonify({'success': False, 'error': report_result['error']})
            
    except Exception as e:
        logger.error(f"[Pump Editor] Error generating PDF report: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Helper functions

def get_default_pump_data():
    """
    Get default pump data structure
    """
    return {
        'model': '28 HC 6P',
        'speed': 980,
        'max_flow': 2500,
        'max_head': 35,
        'bep_flow': 1500,
        'bep_head': 25,
        'bep_efficiency': 84.8,
        'min_impeller': 451,
        'max_impeller': 501,
        'npsh_at_bep': 8
    }

def load_extraction_data(extraction_id: str) -> Dict[str, Any]:
    """
    Load extraction data from storage with multiple fallback sources
    """
    try:
        # Check in-memory storage first
        if extraction_id in edited_pump_data:
            logger.info(f"[Pump Editor] Found extraction {extraction_id} in memory")
            return edited_pump_data[extraction_id]
        
        # Check file storage in temp/extractions
        storage_path = f"app/static/temp/extractions/{extraction_id}.json"
        if os.path.exists(storage_path):
            logger.info(f"[Pump Editor] Found extraction {extraction_id} in file storage")
            with open(storage_path, 'r') as f:
                return json.load(f)
        
        # Check session storage as fallback
        from ..session_manager import safe_session_get
        session_key = f'extraction_{extraction_id}'
        session_data = safe_session_get(session_key)
        if session_data:
            logger.info(f"[Pump Editor] Found extraction {extraction_id} in session")
            return session_data
        
        # Check if this is the latest extraction
        latest_id = safe_session_get('last_extraction_id')
        if latest_id == extraction_id:
            # Try to find the latest extraction data
            latest_data = safe_session_get('extracted_pump_data')
            if latest_data:
                logger.info(f"[Pump Editor] Found extraction {extraction_id} as latest data")
                return latest_data
        
        logger.warning(f"[Pump Editor] Extraction {extraction_id} not found in any storage")
        return None
        
    except Exception as e:
        logger.error(f"[Pump Editor] Error loading extraction {extraction_id}: {e}")
        return None

def validate_pump_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate pump data structure
    """
    try:
        # Check required sections
        required_sections = ['specifications', 'performance_curves']
        for section in required_sections:
            if section not in data:
                return {'valid': False, 'error': f'Missing required section: {section}'}
        
        # Validate specifications
        specs = data['specifications']
        required_specs = ['model', 'speed', 'max_flow', 'max_head', 'bep_flow', 'bep_head', 'bep_efficiency']
        for spec in required_specs:
            if spec not in specs:
                return {'valid': False, 'error': f'Missing specification: {spec}'}
        
        # Validate performance curves
        curves = data['performance_curves']
        required_curves = ['impeller_501', 'impeller_451']
        for curve in required_curves:
            if curve not in curves:
                return {'valid': False, 'error': f'Missing curve data: {curve}'}
            
            # Validate curve data points
            curve_data = curves[curve]
            if not isinstance(curve_data, list) or len(curve_data) < 3:
                return {'valid': False, 'error': f'Invalid curve data for {curve}'}
            
            # Validate each data point
            for i, point in enumerate(curve_data):
                required_fields = ['flow', 'head', 'efficiency', 'npsh']
                for field in required_fields:
                    if field not in point:
                        return {'valid': False, 'error': f'Missing field {field} in {curve} point {i+1}'}
                    
                    # Check if value is numeric
                    if not isinstance(point[field], (int, float)):
                        return {'valid': False, 'error': f'Invalid {field} value in {curve} point {i+1}'}
        
        return {'valid': True}
        
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {str(e)}'}

def generate_save_id() -> str:
    """
    Generate unique save ID
    """
    import uuid
    return f"save_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

def save_to_storage(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save data to storage
    """
    try:
        save_id = data['save_id']
        
        # Save to in-memory storage
        edited_pump_data[save_id] = data
        
        # Save to file storage
        storage_dir = "app/static/temp/edited_data"
        os.makedirs(storage_dir, exist_ok=True)
        
        storage_path = f"{storage_dir}/{save_id}.json"
        with open(storage_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {'success': True, 'storage_path': storage_path}
        
    except Exception as e:
        logger.error(f"[Pump Editor] Error saving to storage: {e}")
        return {'success': False, 'error': str(e)}

def generate_pdf_from_edited_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate PDF report from edited data
    """
    try:
        # Convert edited data to pump selection format
        pump_selection_data = convert_to_pump_selection_format(data)
        
        # Use existing PDF generation system
        from ..pdf_generator import PDFGenerator
        
        pdf_generator = PDFGenerator()
        pdf_result = pdf_generator.generate_from_edited_data(pump_selection_data)
        
        return pdf_result
        
    except Exception as e:
        logger.error(f"[Pump Editor] Error generating PDF: {e}")
        return {'success': False, 'error': str(e)}

def convert_to_pump_selection_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert edited data to pump selection format for PDF generation
    """
    try:
        specs = data['specifications']
        curves = data['performance_curves']
        
        # Create pump selection compatible format
        pump_data = {
            'model': specs['model'],
            'speed': specs['speed'],
            'max_flow': specs['max_flow'],
            'max_head': specs['max_head'],
            'bep_flow': specs['bep_flow'],
            'bep_head': specs['bep_head'],
            'bep_efficiency': specs['bep_efficiency'],
            'min_impeller': specs['min_impeller'],
            'max_impeller': specs['max_impeller'],
            'performance_curves': curves,
            'user_edited': True,
            'edit_timestamp': datetime.now().isoformat()
        }
        
        return pump_data
        
    except Exception as e:
        logger.error(f"[Pump Editor] Error converting data format: {e}")
        return {}

logger.info("[Pump Editor] Routes module loaded successfully")