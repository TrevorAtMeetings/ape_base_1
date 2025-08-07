"""
Admin Routes
Routes for administrative functions including AI admin interface
"""
import logging
import os
from flask import render_template, Blueprint, request, jsonify, current_app, flash
from werkzeug.utils import secure_filename
from ..catalog_engine import get_catalog_engine
from ..pump_repository import PumpRepository
from ..utils import SiteRequirements

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

@admin_bp.route('/admin/testing')
def testing_interface():
    """Performance Testing & Validation Interface"""
    return render_template('admin_testing.html')

@admin_bp.route('/admin/testing', methods=['POST'])
def run_performance_test():
    """Run performance comparison test between database and UI calculations"""
    try:
        # Get form data
        flow_rate = float(request.form.get('flow_rate', 0))
        head = float(request.form.get('head', 0))
        pump_code = request.form.get('pump_code', '').strip()
        
        if flow_rate <= 0 or head <= 0:
            flash('Please enter valid flow rate and head values', 'error')
            return render_template('admin_testing.html')
        
        logger.info(f"Running performance test: Flow={flow_rate} m³/hr, Head={head} m, Pump={pump_code or 'ALL'}")
        
        # Initialize engines
        catalog_engine = get_catalog_engine()
        pump_repo = PumpRepository()
        
        # Create site requirements
        site_requirements = SiteRequirements(flow_rate, head)
        
        # Get test pumps - either specific pump or all suitable pumps
        if pump_code:
            # Test specific pump
            catalog_pump = catalog_engine.get_pump_by_code(pump_code)
            if not catalog_pump:
                flash(f'Pump code "{pump_code}" not found in database', 'error')
                return render_template('admin_testing.html')
            test_pumps = [catalog_pump]
        else:
            # Get suitable pumps from catalog engine (limit to top 10 for testing)
            selection_results = catalog_engine.select_pumps(
                flow_rate, head, pump_type='GENERAL', max_results=10
            )
            if not selection_results:
                flash('No suitable pumps found for the given conditions', 'error')
                return render_template('admin_testing.html')
            
            # Extract pump objects from selection results
            test_pumps = []
            limited_results = selection_results[:10] if len(selection_results) > 10 else selection_results
            for result in limited_results:
                # selection_results is a list of dicts, each with a 'pump' key
                if isinstance(result, dict) and 'pump' in result:
                    test_pumps.append(result['pump'])
                elif hasattr(result, 'pump'):
                    test_pumps.append(result.pump)
                    
            if not test_pumps:
                flash('Unable to extract pump objects from selection results', 'error')
                return render_template('admin_testing.html')
        
        # Run comparison tests
        test_results = []
        for pump in test_pumps:
            result = _compare_pump_performance(pump, flow_rate, head, pump_repo, catalog_engine)
            if result:
                # Add BEP analysis to each pump result
                bep_data = _get_bep_analysis(pump, pump_repo, catalog_engine)
                result['bep_analysis'] = bep_data
                test_results.append(result)
        
        logger.info(f"Performance test completed: {len(test_results)} pumps tested")
        
        return render_template('admin_testing.html', 
                             test_results=test_results,
                             test_conditions={
                                 'flow_m3hr': flow_rate,
                                 'head_m': head,
                                 'pump_code': pump_code if pump_code else None
                             })
        
    except ValueError as e:
        flash(f'Invalid input: {str(e)}', 'error')
        return render_template('admin_testing.html')
    except Exception as e:
        logger.error(f"Error in performance test: {str(e)}")
        flash('An error occurred during testing. Please check the logs.', 'error')
        return render_template('admin_testing.html')

def _compare_pump_performance(pump, flow_rate, head, pump_repo, catalog_engine):
    """Compare database raw values vs UI calculated values for a single pump"""
    try:
        # Get raw database performance (direct curve interpolation)
        db_performance = _get_database_performance(pump, flow_rate, head)
        
        # Get UI calculated performance (catalog engine with all transformations)
        ui_performance = _get_ui_performance(pump, flow_rate, head, catalog_engine)
        
        # Calculate deltas
        efficiency_delta = None
        power_delta = None  
        npsh_delta = None
        
        if db_performance.get('efficiency') is not None and ui_performance.get('efficiency_pct') is not None:
            efficiency_delta = ui_performance['efficiency_pct'] - db_performance['efficiency']
            
        if db_performance.get('power_kw') is not None and ui_performance.get('power_kw') is not None:
            power_delta = ui_performance['power_kw'] - db_performance['power_kw']
            
        if db_performance.get('npshr_m') is not None and ui_performance.get('npshr_m') is not None:
            npsh_delta = ui_performance['npshr_m'] - db_performance['npshr_m']
        
        # Determine status based on deltas
        status = _determine_status(efficiency_delta, power_delta, npsh_delta)
        
        return {
            'pump_code': pump.pump_code,
            'pump_type': pump.pump_type,
            'db_efficiency': db_performance.get('efficiency'),
            'ui_efficiency': ui_performance.get('efficiency_pct'),
            'efficiency_delta': efficiency_delta,
            'db_power': db_performance.get('power_kw'),
            'ui_power': ui_performance.get('power_kw'),
            'power_delta': power_delta,
            'db_npsh': db_performance.get('npshr_m'),
            'ui_npsh': ui_performance.get('npshr_m'),
            'npsh_delta': npsh_delta,
            'ui_score': ui_performance.get('suitability_score'),
            'status': status
        }
        
    except Exception as e:
        logger.error(f"Error comparing performance for {pump.pump_code}: {str(e)}")
        return None

def _get_database_performance(pump, flow_rate, head):
    """Get raw database performance using direct curve interpolation (no transformations)"""
    try:
        # Use the existing _get_performance_interpolated method which gives raw curve data
        raw_performance = pump._get_performance_interpolated(flow_rate, head)
        
        logger.debug(f"Database performance for {pump.pump_code} at {flow_rate}/{head}: {raw_performance}")
        
        if raw_performance:
            return {
                'efficiency': raw_performance.get('efficiency_pct'),
                'power_kw': raw_performance.get('power_kw'),
                'npshr_m': raw_performance.get('npshr_m')
            }
        
        # Enhanced debug info when no data found
        logger.warning(f"No database performance data for {pump.pump_code} at {flow_rate} m³/hr, {head} m")
        logger.debug(f"Available curves for {pump.pump_code}: {len(pump.curves) if pump.curves else 0}")
        
        if pump.curves:
            for i, curve in enumerate(pump.curves):
                points = curve.get('performance_points', [])
                if points:
                    flow_range = f"{min(p.get('flow_m3hr', 0) for p in points):.0f}-{max(p.get('flow_m3hr', 0) for p in points):.0f}"
                    head_range = f"{min(p.get('head_m', 0) for p in points):.1f}-{max(p.get('head_m', 0) for p in points):.1f}"
                    logger.debug(f"Curve {i} flow range: {flow_range} m³/hr, head range: {head_range} m")
        
        return {'efficiency': None, 'power_kw': None, 'npshr_m': None}
        
    except Exception as e:
        logger.warning(f"Database performance calculation failed for {pump.pump_code}: {str(e)}")
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        return {'efficiency': None, 'power_kw': None, 'npshr_m': None}

def _get_ui_performance(pump, flow_rate, head, catalog_engine):
    """Get UI calculated performance using catalog engine's full methodology"""
    try:
        # Use catalog engine's unified evaluation method (includes all transformations, scaling, scoring)
        ui_solution = pump.find_best_solution_for_duty(flow_rate, head)
        
        logger.info(f"UI solution for {pump.pump_code}: {ui_solution}")
        
        if ui_solution and ui_solution.get('performance'):
            # Extract performance data from the solution
            performance = ui_solution.get('performance', {})
            logger.info(f"UI performance data for {pump.pump_code}: {performance}")
            
            return {
                'efficiency_pct': performance.get('efficiency_pct'),
                'power_kw': performance.get('power_kw'), 
                'npshr_m': performance.get('npshr_m'),
                'suitability_score': ui_solution.get('score'),
                'trim_percent': performance.get('trim_percent'),
                'method': ui_solution.get('method', 'unknown')
            }
        else:
            logger.warning(f"No UI solution found for {pump.pump_code} at {flow_rate} m³/hr, {head} m")
            # Fallback: try direct performance calculation if find_best_solution_for_duty fails
            fallback_performance = pump._get_performance_interpolated(flow_rate, head)
            if fallback_performance:
                logger.info(f"Using fallback performance for UI calculation: {fallback_performance}")
                return {
                    'efficiency_pct': fallback_performance.get('efficiency_pct'),
                    'power_kw': fallback_performance.get('power_kw'), 
                    'npshr_m': fallback_performance.get('npshr_m'),
                    'suitability_score': 0,  # No score available
                    'trim_percent': 100,  # Assume no trim
                    'method': 'fallback_interpolation'
                }
            else:
                return {
                    'efficiency_pct': None,
                    'power_kw': None,
                    'npshr_m': None,
                    'suitability_score': None,
                    'trim_percent': None,
                    'method': 'no_solution'
                }
        
    except Exception as e:
        logger.warning(f"Could not get UI performance for {pump.pump_code}: {str(e)}")
        return {
            'efficiency_pct': None,
            'power_kw': None, 
            'npshr_m': None,
            'suitability_score': None,
            'trim_percent': None,
            'method': 'error'
        }

def _get_bep_analysis(pump, pump_repo, catalog_engine):
    """Get BEP analysis for the pump including BEP coordinates and performance"""
    try:
        # Get BEP from pump specifications
        bep_flow = pump.specifications.get('q_bep', 0)
        bep_head = pump.specifications.get('h_bep', 0)
        bep_efficiency = pump.specifications.get('eff_bep', 0)
        
        logger.info(f"BEP specifications for {pump.pump_code}: Flow={bep_flow}, Head={bep_head}, Efficiency={bep_efficiency}")
        
        # If no BEP specs, try to estimate from curve data
        if not bep_flow or not bep_head:
            bep_estimate = _estimate_bep_from_curves(pump)
            if bep_estimate:
                bep_flow = bep_estimate.get('flow_m3hr', 0)
                bep_head = bep_estimate.get('head_m', 0)
                bep_efficiency = bep_estimate.get('efficiency_pct', 0)
                logger.info(f"Estimated BEP for {pump.pump_code}: Flow={bep_flow}, Head={bep_head}, Efficiency={bep_efficiency}")
        
        if bep_flow and bep_head:
            # Calculate performance at BEP using both methods
            bep_db_performance = _get_database_performance(pump, bep_flow, bep_head)
            bep_ui_performance = _get_ui_performance(pump, bep_flow, bep_head, catalog_engine)
            
            return {
                'bep_flow_m3hr': bep_flow,
                'bep_head_m': bep_head,
                'bep_efficiency_pct': bep_efficiency,
                'db_performance': bep_db_performance,
                'ui_performance': bep_ui_performance,
                'has_bep_data': True
            }
        else:
            logger.warning(f"No BEP data available for {pump.pump_code}")
            return {'has_bep_data': False}
            
    except Exception as e:
        logger.error(f"Error getting BEP analysis for {pump.pump_code}: {str(e)}")
        return {'has_bep_data': False}

def _estimate_bep_from_curves(pump):
    """Estimate BEP from curve data by finding peak efficiency point"""
    try:
        best_efficiency = 0
        bep_point = None
        
        for curve in pump.curves:
            points = curve.get('performance_points', [])
            for point in points:
                efficiency = point.get('efficiency_pct', 0)
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    bep_point = {
                        'flow_m3hr': point.get('flow_m3hr'),
                        'head_m': point.get('head_m'),
                        'efficiency_pct': efficiency
                    }
        
        return bep_point
        
    except Exception as e:
        logger.warning(f"Error estimating BEP from curves for {pump.pump_code}: {str(e)}")
        return None

def _determine_status(efficiency_delta, power_delta, npsh_delta):
    """Determine test status based on deltas between database and UI values"""
    
    # Check for major differences (indicating potential issues)
    major_diff = False
    minor_diff = False
    
    if efficiency_delta is not None and abs(efficiency_delta) > 5:  # >5% efficiency difference
        major_diff = True
    elif efficiency_delta is not None and abs(efficiency_delta) > 2:  # >2% efficiency difference
        minor_diff = True
        
    if power_delta is not None and abs(power_delta) > 2:  # >2kW power difference
        major_diff = True  
    elif power_delta is not None and abs(power_delta) > 0.5:  # >0.5kW power difference
        minor_diff = True
        
    if npsh_delta is not None and abs(npsh_delta) > 1:  # >1m NPSH difference
        major_diff = True
    elif npsh_delta is not None and abs(npsh_delta) > 0.3:  # >0.3m NPSH difference
        minor_diff = True
    
    if major_diff:
        return 'major_diff'
    elif minor_diff:
        return 'minor_diff'
    else:
        return 'match'

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