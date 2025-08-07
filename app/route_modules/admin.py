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
            if not selection_results or not selection_results.get('suitable_pumps'):
                flash('No suitable pumps found for the given conditions', 'error')
                return render_template('admin_testing.html')
            
            # Extract pump objects from selection results
            test_pumps = []
            for result in selection_results['suitable_pumps'][:10]:
                if hasattr(result, 'pump'):
                    test_pumps.append(result['pump'])
                elif 'pump' in result:
                    test_pumps.append(result['pump'])
        
        # Run comparison tests
        test_results = []
        for pump in test_pumps:
            result = _compare_pump_performance(pump, flow_rate, head, pump_repo, catalog_engine)
            if result:
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
    """Get raw database performance using direct curve interpolation"""
    try:
        # Use the pump's direct interpolation method for raw database values
        raw_performance = pump.interpolate_performance_direct(flow_rate, head)
        
        return {
            'efficiency': raw_performance.get('efficiency_pct') if raw_performance else None,
            'power_kw': raw_performance.get('power_kw') if raw_performance else None,
            'npshr_m': raw_performance.get('npshr_m') if raw_performance else None
        }
        
    except Exception as e:
        logger.warning(f"Could not get database performance for {pump.pump_code}: {str(e)}")
        # Fallback to basic interpolation if direct method doesn't exist
        try:
            # Try alternative method - direct curve access
            best_curve = None
            best_score = float('inf')
            
            for curve in pump.curves:
                # Find curve with best head match at the flow rate
                flows = [p['flow_m3hr'] for p in curve['performance_points']]
                heads = [p['head_m'] for p in curve['performance_points']]
                
                if len(flows) >= 2 and min(flows) <= flow_rate <= max(flows):
                    # Interpolate head at this flow
                    try:
                        from scipy import interpolate
                        f_head = interpolate.interp1d(flows, heads, kind='linear', bounds_error=False, fill_value='extrapolate')
                        curve_head = float(f_head(flow_rate))
                        head_diff = abs(curve_head - head)
                        
                        if head_diff < best_score:
                            best_score = head_diff
                            best_curve = curve
                    except:
                        continue
            
            if best_curve:
                flows = [p['flow_m3hr'] for p in best_curve['performance_points']]
                efficiencies = [p['efficiency_pct'] for p in best_curve['performance_points']]
                
                if len(flows) >= 2:
                    f_eff = interpolate.interp1d(flows, efficiencies, kind='linear', bounds_error=False, fill_value='extrapolate')
                    efficiency = float(f_eff(flow_rate))
                    
                    # Try to get power if available
                    power = None
                    if pump.power_curves:
                        for power_curve in pump.power_curves:
                            if power_curve.get('impeller_diameter_mm') == best_curve.get('impeller_diameter_mm'):
                                power_flows = [p['flow_m3hr'] for p in power_curve['performance_points']]
                                powers = [p['power_kw'] for p in power_curve['performance_points']]
                                if len(power_flows) >= 2:
                                    f_power = interpolate.interp1d(power_flows, powers, kind='linear', bounds_error=False, fill_value='extrapolate')
                                    power = float(f_power(flow_rate))
                                break
                    
                    # Try to get NPSH if available  
                    npsh = None
                    if pump.npsh_curves:
                        for npsh_curve in pump.npsh_curves:
                            if npsh_curve.get('impeller_diameter_mm') == best_curve.get('impeller_diameter_mm'):
                                npsh_flows = [p['flow_m3hr'] for p in npsh_curve['performance_points']]
                                npshs = [p['npshr_m'] for p in npsh_curve['performance_points']]
                                if len(npsh_flows) >= 2:
                                    f_npsh = interpolate.interp1d(npsh_flows, npshs, kind='linear', bounds_error=False, fill_value='extrapolate')
                                    npsh = float(f_npsh(flow_rate))
                                break
                    
                    return {
                        'efficiency': efficiency,
                        'power_kw': power,
                        'npshr_m': npsh
                    }
            
        except Exception as e2:
            logger.warning(f"Fallback interpolation failed for {pump.pump_code}: {str(e2)}")
        
        return {'efficiency': None, 'power_kw': None, 'npshr_m': None}

def _get_ui_performance(pump, flow_rate, head, catalog_engine):
    """Get UI calculated performance using catalog engine's full methodology"""
    try:
        # Use catalog engine's unified evaluation method (includes all transformations, scaling, scoring)
        ui_solution = pump.find_best_solution_for_duty(flow_rate, head)
        
        if ui_solution:
            # Extract performance data from the solution
            performance = ui_solution.get('performance', {})
            return {
                'efficiency_pct': performance.get('efficiency_pct'),
                'power_kw': performance.get('power_kw'), 
                'npshr_m': performance.get('npshr_m'),
                'suitability_score': ui_solution.get('score'),
                'trim_percent': performance.get('trim_percent'),
                'method': ui_solution.get('method', 'unknown')
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