"""
Admin Routes
Routes for administrative functions including AI admin interface
"""
import logging
import os
from flask import render_template, Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

# Allowed file extensions for document upload
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'md'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/admin/ai')
def ai_admin():
    """AI Knowledge Base Admin page."""
    return render_template('ai_admin.html')

# Admin landing page with options
@admin_bp.route('/admin')
def admin_landing():
    return render_template('admin_landing.html')

@admin_bp.route('/admin/upload', methods=['POST'])
def upload_document():
    """Handle document upload for AI knowledge base"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Secure the filename
        filename = secure_filename(file.filename or 'unnamed')
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': file_size,
            'message': 'Document uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({'success': False, 'error': 'Upload failed'}), 500

@admin_bp.route('/api/chat/status', methods=['GET'])
def chat_status():
    """Get chat API status"""
    try:
        # Check if API keys are configured
        openai_configured = bool(os.environ.get('OPENAI_API_KEY'))
        google_configured = bool(os.environ.get('GOOGLE_API_KEY'))
        
        status = {
            'status': 'ready' if (openai_configured or google_configured) else 'not_configured',
            'providers': {
                'openai': 'configured' if openai_configured else 'not_configured',
                'google': 'configured' if google_configured else 'not_configured'
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error checking chat status: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@admin_bp.route('/admin/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents"""
    try:
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
        documents = []
        
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if allowed_file(filename):
                    filepath = os.path.join(upload_dir, filename)
                    file_stat = os.stat(filepath)
                    documents.append({
                        'filename': filename,
                        'size': file_stat.st_size,
                        'uploaded': file_stat.st_mtime,
                        'type': filename.split('.')[-1].lower()
                    })
        
        return jsonify({
            'success': True,
            'documents': documents,
            'count': len(documents)
        })
        
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve documents'}), 500


@admin_bp.route('/admin/test-query', methods=['POST'])
def test_query():
    """Test AI query functionality"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'No query provided'}), 400
        
        # For now, return a placeholder response indicating the feature is under development
        response = {
            'success': True,
            'query': query,
            'response': 'AI query functionality is under development. This feature will provide intelligent responses based on uploaded technical documents.',
            'confidence': 0.95,
            'sources': ['Feature coming soon'],
            'processing_time': 0.1
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing test query: {str(e)}")
        return jsonify({'success': False, 'error': 'Query processing failed'}), 500