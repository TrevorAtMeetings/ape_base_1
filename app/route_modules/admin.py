"""
Admin Routes
Routes for administrative functions including pump upload, recent pumps, and SCG processing
"""
import os
import logging
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, send_file, jsonify, make_response
from ..session_manager import safe_flash
from werkzeug.utils import secure_filename
from .. import app

logger = logging.getLogger(__name__)

@app.route('/admin/pump_upload')
def pump_upload():
    """Admin pump upload interface."""
    return render_template('admin/pump_upload.html')

@app.route('/admin/recent_pumps')
def recent_pumps():
    """Show recently processed pumps."""
    try:
        # Get recent pump data from session or database
        recent_pumps_data = []
        
        # For now, return empty list - this would typically query a database
        return render_template('admin/recent_pumps.html', 
                             recent_pumps=recent_pumps_data,
                             total_count=len(recent_pumps_data))
    
    except Exception as e:
        logger.error(f"Error in recent_pumps: {str(e)}")
        safe_flash('Error loading recent pumps data.', 'error')
        return redirect(url_for('index'))

@app.route('/admin/download_template/<format_type>')
def download_template(format_type):
    """Download pump data template in specified format."""
    try:
        if format_type not in ['csv', 'json', 'txt']:
            safe_flash('Invalid format type.', 'error')
            return redirect(url_for('pump_upload'))
        
        # Create template data
        template_data = {
            'csv': create_csv_template(),
            'json': create_json_template(),
            'txt': create_txt_template()
        }
        
        content = template_data.get(format_type, '')
        filename = f'pump_data_template.{format_type}'
        
        response = make_response(content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
    
    except Exception as e:
        logger.error(f"Error downloading template: {str(e)}")
        safe_flash('Error generating template.', 'error')
        return redirect(url_for('pump_upload'))

def create_csv_template():
    """Create CSV template for pump data."""
    return """Pump Code,Manufacturer,Model,Test Speed (RPM),Impeller Size (mm),Flow (m³/hr),Head (m),Efficiency (%),Power (kW),NPSH (m)
10-WLN-32A,APE PUMPS,WLN Series,1480,312,100,15,75,5.5,2.5
10-WLN-32A,APE PUMPS,WLN Series,1480,312,200,14,82,9.5,3.0
10-WLN-32A,APE PUMPS,WLN Series,1480,312,300,12,78,12.5,3.5"""

def create_json_template():
    """Create JSON template for pump data."""
    return """{
  "pumps": [
    {
      "objPump": {
        "pPumpCode": "10-WLN-32A",
        "pSuppName": "APE PUMPS",
        "pPumpTestSpeed": "1480",
        "pFilter1": "APE PUMPS",
        "pStages": "1"
      },
      "performance_curves": [
        {
          "impeller_size": 312,
          "test_speed_rpm": 1480,
          "flow_vs_head": [[100, 15], [200, 14], [300, 12]],
          "flow_vs_efficiency": [[100, 75], [200, 82], [300, 78]],
          "flow_vs_power": [[100, 5.5], [200, 9.5], [300, 12.5]],
          "flow_vs_npshr": [[100, 2.5], [200, 3.0], [300, 3.5]]
        }
      ]
    }
  ]
}"""

def create_txt_template():
    """Create TXT template for pump data."""
    return """PUMP DATA TEMPLATE
===============

Format: objPump-pPumpCode-{PUMP_CODE}-objPump-pSuppName-{MANUFACTURER}-objPump-pPumpTestSpeed-{SPEED}-objPump-pFilter1-{MANUFACTURER}-objPump-pStages-1

Example:
objPump-pPumpCode-10-WLN-32A-objPump-pSuppName-APE PUMPS-objPump-pPumpTestSpeed-1480-objPump-pFilter1-APE PUMPS-objPump-pStages-1

Performance data should follow the pump definition with flow, head, efficiency, power, and NPSH values."""

@app.route('/admin/scg', methods=['GET', 'POST'])
def scg_admin():
    """SCG processing admin interface."""
    try:
        if request.method == 'POST':
            # Handle file upload
            if 'scg_file' not in request.files:
                safe_flash('No file selected.', 'error')
                return redirect(url_for('scg_admin'))
            
            file = request.files['scg_file']
            if file.filename == '':
                safe_flash('No file selected.', 'error')
                return redirect(url_for('scg_admin'))
            
            # Validate file type
            if not file.filename.lower().endswith('.txt'):
                safe_flash('Please upload a .txt file.', 'error')
                return redirect(url_for('scg_admin'))
            
            # Save file
            upload_dir = os.path.join(app.config.get('UPLOAD_FOLDER', 'app/static/temp'), 'scg_uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, safe_filename)
            file.save(file_path)
            
            # Process SCG file
            from ..scg_processor import process_scg_file
            result = process_scg_file(file_path)
            
            # Clean up
            os.remove(file_path)
            
            if result.get('success'):
                safe_flash(f'SCG file processed successfully. {result.get("pumps_processed", 0)} pumps extracted.', 'success')
            else:
                safe_flash(f'Error processing SCG file: {result.get("error", "Unknown error")}', 'error')
            
            return redirect(url_for('scg_admin'))
        
        # GET request - show admin interface
        return render_template('admin/scg_admin.html')
    
    except Exception as e:
        logger.error(f"Error in SCG admin: {str(e)}")
        safe_flash('Error processing SCG file.', 'error')
        return redirect(url_for('scg_admin'))

@app.route('/admin/scg/batch-status/<batch_id>')
def scg_batch_status(batch_id):
    """Get SCG batch processing status."""
    try:
        # This would typically query a database for batch status
        # For now, return a mock status
        status = {
            'batch_id': batch_id,
            'status': 'completed',
            'pumps_processed': 25,
            'errors': 0,
            'progress': 100,
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        return jsonify(status)
    
    except Exception as e:
        logger.error(f"Error getting SCG batch status: {str(e)}")
        return jsonify({'error': 'Failed to get batch status'}), 500

@app.route('/admin/scg/validate', methods=['POST'])
def scg_validate():
    """Validate SCG file format."""
    try:
        if 'scg_file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['scg_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read first few lines to validate format
        content = file.read().decode('utf-8', errors='ignore')
        lines = content.split('\n')[:10]  # Check first 10 lines
        
        # Basic SCG format validation
        valid_lines = 0
        total_lines = len(lines)
        
        for line in lines:
            if 'objPump-pPumpCode-' in line:
                valid_lines += 1
        
        validation_result = {
            'valid': valid_lines > 0,
            'valid_lines': valid_lines,
            'total_lines': total_lines,
            'format_score': (valid_lines / total_lines * 100) if total_lines > 0 else 0
        }
        
        return jsonify(validation_result)
    
    except Exception as e:
        logger.error(f"Error validating SCG file: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500

@app.route('/admin/scg/download-report')
def scg_download_report():
    """Download SCG processing report."""
    try:
        # Generate report content
        report_content = f"""SCG Processing Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
- Total files processed: 0
- Pumps extracted: 0
- Errors encountered: 0
- Processing time: 0 seconds

This is a placeholder report. Actual SCG processing reports would be generated based on real processing data.
"""
        
        response = make_response(report_content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename=scg_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating SCG report: {str(e)}")
        safe_flash('Error generating report.', 'error')
        return redirect(url_for('scg_admin'))

@app.route('/api/scg/stats')
def scg_stats():
    """Get SCG processing statistics."""
    try:
        # Mock statistics - would typically query database
        stats = {
            'total_files_processed': 0,
            'total_pumps_extracted': 0,
            'average_processing_time': 0,
            'success_rate': 100,
            'last_processed': None,
            'active_batches': 0
        }
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting SCG stats: {str(e)}")
        return jsonify({'error': 'Failed to get statistics'}), 500 