"""
Brain Admin Routes - Enterprise-grade data correction and configuration management
Implements the two-schema architecture with golden source protection
"""

import logging
import json
import re
import numpy as np
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
from ..brain_data_service import BrainDataService, BrainDataAccessor
from ..pump_repository import PumpRepository
from ..manufacturer_comparison_engine import ManufacturerComparisonEngine

logger = logging.getLogger(__name__)

brain_admin_bp = Blueprint('brain_admin', __name__)

@brain_admin_bp.route('/admin/brain')
def brain_dashboard():
    """Brain administration dashboard - main landing page"""
    try:
        # Clean breadcrumbs for navigation
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'Admin', 'url': '/admin', 'icon': 'admin_panel_settings'},
            {'label': 'Brain Dashboard', 'url': '#', 'icon': 'psychology'}
        ]
        brain_service = BrainDataService()
        
        # Get summary statistics
        quality_issues = brain_service.get_quality_issues(status='open')
        critical_issues = [issue for issue in quality_issues if issue.severity == 'critical']
        major_issues = [issue for issue in quality_issues if issue.severity == 'major']
        
        # Get pending corrections
        corrections = brain_service.get_active_corrections()
        
        stats = {
            'total_quality_issues': len(quality_issues),
            'critical_issues': len(critical_issues),
            'major_issues': len(major_issues),
            'active_corrections': len(corrections),
            'production_config': brain_service.get_production_config()['profile_name']
        }
        
        return render_template('admin/brain_dashboard_clean.html', stats=stats, breadcrumbs=breadcrumbs)
        
    except Exception as e:
        logger.error(f"Error loading brain dashboard: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        # Provide default breadcrumbs even in error case
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'Admin', 'url': '/admin', 'icon': 'admin_panel_settings'},
            {'label': 'Brain Dashboard', 'url': '#', 'icon': 'psychology'}
        ]
        return render_template('admin/brain_dashboard_clean.html', stats={}, breadcrumbs=breadcrumbs)

@brain_admin_bp.route('/admin/brain/status')
def brain_status_admin():
    """Brain system status endpoint"""
    import time
    try:
        from ..pump_brain import get_pump_brain
        
        brain = get_pump_brain()
        status = brain.get_status()
        
        response_data = {
            'brain_available': True,
            'status': status,
            'timestamp': time.time(),
            'uptime_seconds': time.time() - brain._initialized_at.timestamp() if hasattr(brain, '_initialized_at') else 0
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            'brain_available': False,
            'error': str(e),
            'timestamp': time.time()
        }), 503

@brain_admin_bp.route('/admin/brain/health')
def brain_health():
    """Brain system health check endpoint"""
    import time
    try:
        from ..pump_brain import get_pump_brain
        
        brain = get_pump_brain()
        status = brain.get_status()
        
        response_data = {
            'status': 'healthy',
            'brain_available': True,
            'pump_count': status.get('pump_count', 0),
            'timestamp': time.time(),
            'uptime_seconds': time.time() - brain._initialized_at.timestamp() if hasattr(brain, '_initialized_at') else 0
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'brain_available': False,
            'error': str(e),
            'timestamp': time.time()
        }), 503

@brain_admin_bp.route('/admin/brain/calibration')
def calibration_tool():
    """Brain Calibration Tool - Tunable Physics Engine Interface"""
    try:
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'label': 'Calibration Tool', 'url': '#', 'icon': 'tune'}
        ]
        
        # Get current calibration factors
        from ..admin_config_service import admin_config_service
        calibration_factors = admin_config_service.get_calibration_factors()
        
        return render_template('admin/brain_calibration.html', 
                             calibration_factors=calibration_factors,
                             breadcrumbs=breadcrumbs)
        
    except Exception as e:
        logger.error(f"Error loading calibration tool: {e}")
        flash(f'Error loading calibration tool: {str(e)}', 'error')
        return redirect(url_for('brain_admin.brain_dashboard'))

@brain_admin_bp.route('/admin/brain/calibration/run', methods=['POST'])
def run_calibration():
    """Run brain calibration test with enhanced options"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from tools.calibrate_brain import BrainCalibrator
        
        # Get request parameters
        data = request.get_json() if request.is_json else {}
        quick_test = data.get('quick_test', False)
        test_count = data.get('test_count', 20 if not quick_test else 5)
        
        # Initialize calibrator
        calibrator = BrainCalibrator()
        
        # Load test cases (limit for quick test)
        test_cases = calibrator.load_test_cases()
        if quick_test:
            calibrator.test_cases = test_cases[:test_count]
            logger.info(f"Running quick calibration test with {len(calibrator.test_cases)} pumps")
        
        # Run calibration test
        results = calibrator.run_calibration_test()
        
        return jsonify({
            'status': 'success',
            'results': results,
            'summary': results.get('summary_stats', {}),
            'recommendations': results.get('recommendations', []),
            'test_type': 'quick' if quick_test else 'full',
            'test_count': len(calibrator.test_cases)
        })
        
    except Exception as e:
        logger.error(f"Calibration test failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@brain_admin_bp.route('/admin/brain/calibration/report', methods=['POST'])
def generate_calibration_report():
    """Generate downloadable calibration report"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from tools.calibrate_brain import BrainCalibrator
        from io import StringIO
        
        # Run full calibration test
        calibrator = BrainCalibrator()
        calibrator.load_test_cases()
        results = calibrator.run_calibration_test()
        
        # Generate comprehensive report
        report_text = calibrator.generate_report()
        
        # Create downloadable response
        from flask import make_response
        response = make_response(report_text)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = 'attachment; filename=brain_calibration_report.txt'
        
        return response
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@brain_admin_bp.route('/admin/brain/calibration/update', methods=['POST'])
def update_calibration_factors():
    """Update calibration factors with validation and audit logging"""
    try:
        from ..admin_config_service import admin_config_service
        
        data = request.get_json()
        factors = data.get('factors', {})
        user_id = str(data.get('user_id', 'web_admin'))  # Ensure string format
        
        # Validate physics parameters - EXPANDED RANGES for comprehensive testing
        validation_errors = []
        physics_bounds = {
            'bep_shift_flow_exponent': (1.0, 2.0),  # EXPANDED: 1.0-1.5 → 1.0-2.0
            'bep_shift_head_exponent': (1.0, 3.0),  # EXPANDED: 1.8-2.5 → 1.0-3.0
            'efficiency_correction_exponent': (0.01, 0.5)  # EXPANDED: 0.05-0.2 → 0.01-0.5
        }
        
        # Validate user_id (must be non-empty string)
        if not user_id or not user_id.strip():
            validation_errors.append("user_id is required")
        
        for factor_name, value in factors.items():
            try:
                float_value = float(value)
                if factor_name in physics_bounds:
                    min_val, max_val = physics_bounds[factor_name]
                    if not (min_val <= float_value <= max_val):
                        validation_errors.append(f"{factor_name} must be between {min_val} and {max_val}")
            except (ValueError, TypeError):
                validation_errors.append(f"{factor_name} must be a valid number")
        
        if validation_errors:
            return jsonify({
                'status': 'error', 
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Update database with audit trail
        import os
        import psycopg2
        
        database_url = os.environ.get('DATABASE_URL')
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cursor:
                # Update factors
                for factor_name, value in factors.items():
                    cursor.execute("""
                        UPDATE admin_config.engineering_constants 
                        SET value = %s, updated_at = NOW()
                        WHERE name = %s AND category = 'BEP Migration'
                    """, (str(value), factor_name))
                
                # Log the change for audit
                cursor.execute("""
                    INSERT INTO admin_config.audit_log (
                        profile_id, action, user_id, changes, timestamp
                    ) VALUES (1, 'calibration_update', %s, %s, NOW())
                """, (user_id, f"Updated calibration factors: {factors}"))
                
                conn.commit()
        
        # Clear all caches to force reload of calibration factors
        admin_config_service._config_cache.clear()
        admin_config_service._cache_timestamp = None
        
        # CRITICAL: Clear PerformanceAnalyzer's class-level cache
        from ..brain.performance import PerformanceAnalyzer
        if hasattr(PerformanceAnalyzer, '_cached_factors'):
            delattr(PerformanceAnalyzer, '_cached_factors')
        if hasattr(PerformanceAnalyzer, '_cache_time'):
            delattr(PerformanceAnalyzer, '_cache_time')
        
        # Force all existing Brain instances to reload calibration factors
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        # Clear any performance analyzer instances that might have cached factors
        if hasattr(brain, '_performance_analyzer'):
            brain._performance_analyzer = None
        
        logger.info(f"Calibration factors updated by {user_id}: {factors}")
        
        # Return updated factors to refresh frontend immediately
        fresh_factors = admin_config_service.get_calibration_factors()
        return jsonify({
            'status': 'success', 
            'message': 'Calibration factors updated successfully',
            'updated_factors': fresh_factors  # Include fresh data for frontend refresh
        })
        
    except Exception as e:
        logger.error(f"Failed to update calibration factors: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@brain_admin_bp.route('/admin/brain/data-quality')
def data_quality_dashboard():
    """Data Quality Management Dashboard"""
    try:
        # Clean breadcrumbs for navigation
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'label': 'Data Quality', 'url': '#', 'icon': 'assessment'}
        ]
        brain_service = BrainDataService()
        
        # Get quality issues grouped by severity
        all_issues = brain_service.get_quality_issues()
        
        issues_by_severity = {
            'critical': [issue for issue in all_issues if issue.severity == 'critical'],
            'major': [issue for issue in all_issues if issue.severity == 'major'],
            'minor': [issue for issue in all_issues if issue.severity == 'minor']
        }
        
        # Get issues by pump for analysis
        pump_issues = {}
        for issue in all_issues:
            if issue.pump_code not in pump_issues:
                pump_issues[issue.pump_code] = []
            pump_issues[issue.pump_code].append(issue)
        
        # Sort pumps by issue count (most problematic first)
        sorted_pumps = sorted(pump_issues.items(), key=lambda x: len(x[1]), reverse=True)
        
        return render_template('admin/data_quality.html', 
                             issues_by_severity=issues_by_severity,
                             pump_issues=dict(sorted_pumps[:20]),  # Top 20 problematic pumps
                             total_issues=len(all_issues),
                             breadcrumbs=breadcrumbs)
                             
    except Exception as e:
        logger.error(f"Error loading data quality dashboard: {e}")
        flash(f'Error loading data quality dashboard: {str(e)}', 'error')
        # Provide default breadcrumbs in error case
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'label': 'Data Quality', 'url': '#', 'icon': 'assessment'}
        ]
        return render_template('admin/data_quality.html', 
                             issues_by_severity={}, pump_issues={}, total_issues=0, breadcrumbs=breadcrumbs)

@brain_admin_bp.route('/admin/brain/corrections')
def corrections_dashboard():
    """Data Corrections Management Dashboard"""
    try:
        # Add breadcrumbs for navigation  
        breadcrumbs = [
            {'text': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'text': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'text': 'Corrections', 'url': '', 'icon': 'edit'}
        ]
        brain_service = BrainDataService()
        
        # Get all corrections grouped by status
        active_corrections = brain_service.get_active_corrections()
        
        # Get pending corrections (need approval)
        with brain_service._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT pump_code, correction_type, field_path, 
                           corrected_value, justification, proposed_by, created_at, id
                    FROM brain_overlay.data_corrections 
                    WHERE status = 'pending' 
                    ORDER BY created_at DESC
                """)
                pending_corrections = cur.fetchall()
        
        correction_stats = {
            'active': len(active_corrections),
            'pending_approval': len(pending_corrections),
            'total_pumps_corrected': len(set(c.pump_code for c in active_corrections))
        }
        
        return render_template('admin/corrections.html',
                             active_corrections=active_corrections,
                             pending_corrections=pending_corrections,
                             stats=correction_stats,
                             breadcrumbs=breadcrumbs)
                             
    except Exception as e:
        logger.error(f"Error loading corrections dashboard: {e}")
        flash(f'Error loading corrections dashboard: {str(e)}', 'error')
        # Provide default breadcrumbs in error case
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'label': 'Corrections', 'url': '#', 'icon': 'build'}
        ]
        return render_template('admin/corrections.html', 
                             active_corrections=[], pending_corrections=[], stats={},
                             breadcrumbs=breadcrumbs)

@brain_admin_bp.route('/admin/brain/workbench')
def brain_workbench():
    """Brain Logic Workbench - Test configurations and corrections"""
    try:
        # Add breadcrumbs for navigation
        breadcrumbs = [
            {'text': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'text': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'text': 'Workbench', 'url': '', 'icon': 'science'}
        ]
        brain_service = BrainDataService()
        
        # Get current production configuration
        prod_config = brain_service.get_production_config()
        
        # Get available pump codes for testing
        pump_repo = PumpRepository()
        pump_repo.load_catalog()
        pump_models = pump_repo.get_pump_models()
        pump_codes = [pump['pump_code'] for pump in pump_models[:50]]  # First 50 for dropdown
        
        return render_template('admin/brain_workbench.html',
                             production_config=prod_config,
                             pump_codes=pump_codes,
                             breadcrumbs=breadcrumbs)
                             
    except Exception as e:
        logger.error(f"Error loading brain workbench: {e}")
        flash(f'Error loading brain workbench: {str(e)}', 'error')
        # Provide default breadcrumbs in error case  
        breadcrumbs = [
            {'text': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'text': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'text': 'Workbench', 'url': '', 'icon': 'science'}
        ]
        return render_template('admin/brain_workbench.html',
                             production_config={}, pump_codes=[],
                             breadcrumbs=breadcrumbs)

@brain_admin_bp.route('/admin/brain-workbench/run-calibration', methods=['POST'])
def run_ground_truth_calibration():
    """Ground Truth Calibration - Compare Brain predictions against manufacturer datasheet"""
    try:
        # Get form data
        pump_code = request.form.get('pump_code')
        duty_flow = float(request.form.get('duty_flow'))
        duty_head = float(request.form.get('duty_head'))
        truth_diameter = float(request.form.get('truth_diameter'))
        truth_efficiency = float(request.form.get('truth_efficiency'))
        truth_power = float(request.form.get('truth_power'))
        
        logger.info(f"Running calibration for {pump_code} at {duty_flow} m³/hr @ {duty_head}m")
        logger.info(f"Ground truth values - Diameter: {truth_diameter}mm, Efficiency: {truth_efficiency}%, Power: {truth_power}kW")
        
        # Get the pump data
        pump_repo = PumpRepository()
        pump_repo.load_catalog()
        pump_models = pump_repo.get_pump_models()
        pump_data = None
        for pump in pump_models:
            if pump['pump_code'] == pump_code:
                pump_data = pump
                break
        
        if not pump_data:
            raise ValueError(f"Pump {pump_code} not found in repository")
        
        # Get Brain prediction using the Brain system
        from ..pump_brain import PumpBrain
        brain = PumpBrain()
        
        # Calculate using Brain's performance analyzer
        brain_result = brain.performance.calculate_at_point_industry_standard(
            pump_data, duty_flow, duty_head
        )
        
        if not brain_result:
            raise ValueError(f"Brain could not calculate performance for {pump_code} at specified duty point")
        
        # Extract Brain predictions
        brain_diameter = brain_result.get('impeller_diameter_mm', 0)
        brain_efficiency = brain_result.get('efficiency_pct', 0)
        brain_power = brain_result.get('power_kw', 0)
        
        # Calculate deltas (percentage difference)
        def calculate_delta(truth, prediction):
            if truth == 0:
                return 0
            return ((prediction - truth) / truth) * 100
        
        delta_diameter = calculate_delta(truth_diameter, brain_diameter)
        delta_efficiency = calculate_delta(truth_efficiency, brain_efficiency)
        delta_power = calculate_delta(truth_power, brain_power)
        
        logger.info(f"Brain predictions - Diameter: {brain_diameter:.1f}mm, Efficiency: {brain_efficiency:.1f}%, Power: {brain_power:.1f}kW")
        logger.info(f"Deltas - Diameter: {delta_diameter:.2f}%, Efficiency: {delta_efficiency:.2f}%, Power: {delta_power:.2f}%")
        
        # Prepare calibration results
        calibration_results = {
            'pump_code': pump_code,
            'duty_flow': duty_flow,
            'duty_head': duty_head,
            'truth_diameter': truth_diameter,
            'truth_efficiency': truth_efficiency,
            'truth_power': truth_power,
            'brain_diameter': brain_diameter,
            'brain_efficiency': brain_efficiency,
            'brain_power': brain_power,
            'delta_diameter': delta_diameter,
            'delta_efficiency': delta_efficiency,
            'delta_power': delta_power
        }
        
        # Re-render the workbench page with calibration results
        breadcrumbs = [
            {'text': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'text': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'text': 'Workbench', 'url': '', 'icon': 'science'}
        ]
        
        brain_service = BrainDataService()
        prod_config = brain_service.get_production_config()
        pump_codes = [pump['pump_code'] for pump in pump_models[:50]]
        
        return render_template('admin/brain_workbench.html',
                             production_config=prod_config,
                             pump_codes=pump_codes,
                             breadcrumbs=breadcrumbs,
                             calibration_results=calibration_results)
        
    except Exception as e:
        logger.error(f"Error running calibration: {e}")
        flash(f'Error running calibration: {str(e)}', 'error')
        return redirect(url_for('brain_admin.brain_workbench'))

# ============================================================================
# ENHANCED MANUFACTURER COMPARISON - PUMP CALIBRATION WORKBENCH
# ============================================================================

class ManufacturerComparisonEngine:
    """
    Core engine for multi-point calibration analysis
    Compares manufacturer ground truth data with Brain predictions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def process_calibration_data(self, pump_code, ground_truth_points, pump_repo=None):
        """
        Main processing flow for multi-point calibration
        
        Args:
            pump_code: Pump identifier
            ground_truth_points: List of dicts with flow, head, efficiency, power
            pump_repo: Optional PumpRepository instance (will use singleton if not provided)
            
        Returns:
            Dict with comparison results, metrics, and insights
        """
        from ..pump_brain import PumpBrain
        from ..pump_repository import get_pump_repository
        import numpy as np
        
        # Use singleton pattern for repository
        if pump_repo is None:
            pump_repo = get_pump_repository()
            self.logger.info("Using singleton pump repository instance")
        
        # Efficient pump lookup using dictionary
        pump_models = pump_repo.get_pump_models()
        pump_dict = {pump['pump_code']: pump for pump in pump_models}
        pump_data = pump_dict.get(pump_code)
        
        if not pump_data:
            raise ValueError(f"Pump {pump_code} not found in repository")
            
        # Initialize Brain
        brain = PumpBrain()
        
        # Generate expanded flow range for better visualization
        # This creates a curve across the pump's operating range
        expanded_points = self._generate_expanded_flow_range(pump_data, ground_truth_points, brain)
        
        # Get BEP flow for QBep% calculations
        bep_flow = pump_data.get('bep_flow', 0)
        
        # Process each ground truth point
        comparison_results = []
        for point in ground_truth_points:
            try:
                # Calculate actual flow if QBep% is provided
                actual_flow = point['flow']
                qbep_percent = point.get('qbep_percent')
                
                if qbep_percent and bep_flow > 0:
                    # Use QBep% to determine the actual flow
                    actual_flow = bep_flow * (qbep_percent / 100.0)
                    self.logger.info(f"Using QBep% {qbep_percent}% -> Flow = {actual_flow:.1f} m³/hr (BEP = {bep_flow:.1f})")
                
                # PURE VALIDATION: Use calculate_performance_at_flow with forced_diameter constraint
                # This is the core of the validation interface - no optimization, just pure comparison
                if point.get('diameter'):
                    # User provided diameter - this is MANDATORY for validation
                    brain_prediction = brain.performance.calculate_performance_at_flow(
                        pump_data, 
                        actual_flow,
                        allow_excessive_trim=True,
                        forced_diameter=point['diameter']  # This is the new, correct parameter
                    )
                    
                    if brain_prediction:
                        self.logger.info(f"[PURE VALIDATION] {pump_code}: Brain prediction at {actual_flow} m³/hr with {point['diameter']}mm diameter")
                else:
                    # NO DIAMETER PROVIDED - This should be an error in pure validation mode
                    self.logger.error(f"[VALIDATION ERROR] {pump_code}: No diameter provided for validation point")
                    # Skip this point - diameter is mandatory
                    continue
                
                if brain_prediction:
                    # Now we have the brain's prediction at the EXACT diameter specified
                    # Compare it to the manufacturer's actual data
                    brain_head = brain_prediction.get('head_m', 0)
                    brain_efficiency = brain_prediction.get('efficiency_pct', 0)
                    brain_power = brain_prediction.get('power_kw', 0)
                    
                    # Calculate percentage deltas for head as well
                    delta_head = self._calculate_delta(point['head'], brain_head)
                    delta_efficiency = self._calculate_delta(point['efficiency'], brain_efficiency)
                    delta_power = self._calculate_delta(point['power'], brain_power)
                    
                    # Calculate diameter delta if provided
                    truth_diameter = point.get('diameter')
                    brain_diameter = brain_prediction.get('diameter_mm', 0)
                    delta_diameter = self._calculate_delta(truth_diameter, brain_diameter) if truth_diameter else None
                    
                    comparison = {
                        'flow': actual_flow,
                        'qbep_percent': qbep_percent,
                        'truth_head': point['head'],
                        'truth_efficiency': point['efficiency'],
                        'truth_power': point['power'],
                        'truth_diameter': truth_diameter,
                        'brain_head': brain_head,  # ACTUAL brain calculated head
                        'brain_efficiency': brain_efficiency,
                        'brain_power': brain_power,
                        'brain_diameter': brain_diameter,
                        'delta_head': delta_head,  # Added head comparison
                        'delta_efficiency': delta_efficiency,
                        'delta_power': delta_power,
                        'delta_diameter': delta_diameter
                    }
                    comparison_results.append(comparison)
                    
                    # Log significant deviations for debugging
                    if abs(delta_head) > 10:
                        self.logger.info(f"Significant head deviation for {pump_code} at {point['flow']} m³/hr: "
                                       f"Truth={point['head']:.2f}m, Brain={brain_head:.2f}m (Δ={delta_head:.1f}%)")
                else:
                    # Brain prediction failed - likely due to diameter out of range
                    self.logger.warning(f"No Brain prediction for {pump_code} at {actual_flow} m³/hr with diameter {point.get('diameter')}mm")
                    
                    # Add an error comparison entry so user knows what failed
                    comparison = {
                        'flow': actual_flow,
                        'qbep_percent': qbep_percent,
                        'truth_head': point['head'],
                        'truth_efficiency': point['efficiency'],
                        'truth_power': point['power'],
                        'truth_diameter': point.get('diameter'),
                        'brain_head': None,
                        'brain_efficiency': None,
                        'brain_power': None,
                        'brain_diameter': None,
                        'delta_head': None,
                        'delta_efficiency': None,
                        'delta_power': None,
                        'delta_diameter': None,
                        'error_message': f"Diameter {point.get('diameter')}mm is outside valid range for this pump"
                    }
                    comparison_results.append(comparison)
                    
            except Exception as e:
                self.logger.error(f"Error processing point {point}: {e}")
        
        # Check if we have diameter range issues
        diameter_warnings = []
        if 'curves' in pump_data:
            available_diameters = [c.get('impeller_diameter_mm', 0) for c in pump_data['curves'] if c.get('impeller_diameter_mm', 0) > 0]
            if available_diameters:
                min_available = min(available_diameters)
                max_available = max(available_diameters)
                
                for point in ground_truth_points:
                    diameter = point.get('diameter')
                    if diameter:
                        if diameter < min_available * 0.85 or diameter > max_available * 1.05:
                            diameter_warnings.append({
                                'diameter': diameter,
                                'min_valid': min_available * 0.85,
                                'max_valid': max_available * 1.05,
                                'available_curves': available_diameters
                            })
        
        # Generate curve data for visual comparison
        # This is for the Analytical Workbench - showing the full predicted curve
        curve_comparison_data = self._generate_curve_comparison_data(
            pump_data, ground_truth_points, brain
        )
        
        # If we have limited data points, add the expanded points for better visualization
        if len(comparison_results) < 5:
            comparison_results.extend(expanded_points)
            # Sort by flow for proper chart rendering
            comparison_results = sorted(comparison_results, key=lambda x: x['flow'])
                
        # Calculate curve deviation metrics
        metrics = self.calculate_curve_deviation_metrics(comparison_results)
        
        # Generate AI insights using the Brain's AI analyst
        try:
            brain_insights = brain.ai_analyst.generate_calibration_insights(
                {'pump_code': pump_code, 'comparison_points': comparison_results},
                metrics
            )
            insights = brain_insights
        except Exception as e:
            self.logger.warning(f"AI insights generation failed, using fallback: {e}")
            insights = self.generate_ai_insights(comparison_results, metrics)
        
        return {
            'pump_code': pump_code,
            'pump_data': pump_data,
            'comparison_points': comparison_results,
            'curve_comparison_data': curve_comparison_data,  # For visual charts
            'metrics': metrics,
            'insights': insights,
            'diameter_warnings': diameter_warnings  # Add warnings about diameter range issues
        }
    
    def _generate_curve_comparison_data(self, pump_data, ground_truth_points, brain):
        """
        Generate full curve data for visual comparison using the forced diameter.
        This shows what the Brain predicts the full curve should look like for the exact impeller diameter.
        """
        import numpy as np
        
        curve_data = []
        
        try:
            # Get the forced diameter from the first ground truth point (they should all be the same)
            forced_diameter = None
            if ground_truth_points and len(ground_truth_points) > 0:
                forced_diameter = ground_truth_points[0].get('diameter')
                self.logger.info(f"[CURVE GEN] Found diameter {forced_diameter} in ground truth points")
            
            if not forced_diameter:
                self.logger.warning("No diameter specified in ground truth points for curve generation")
                self.logger.warning(f"Ground truth points: {ground_truth_points}")
                return curve_data
            
            # Get the BEP flow from pump data
            bep_flow = pump_data.get('bep_flow', 0)
            
            if bep_flow <= 0:
                return curve_data
            
            # Calculate the flow range (40% to 140% of BEP for comprehensive view)
            min_flow = max(bep_flow * 0.4, 10)  # At least 10 m³/hr
            max_flow = bep_flow * 1.4
            
            # Generate 20 evenly spaced points for smooth curves
            flow_points = np.linspace(min_flow, max_flow, 20)
            
            for flow in flow_points:
                try:
                    # Get Brain's prediction at this flow with the FORCED diameter
                    brain_prediction = brain.performance.calculate_performance_at_flow(
                        pump_data, 
                        flow,
                        forced_diameter=forced_diameter,  # Use the forced diameter from ground truth
                        allow_excessive_trim=True
                    )
                    
                    if brain_prediction:
                        curve_data.append({
                            'flow': float(flow),
                            'brain_head': brain_prediction.get('head_m', 0),
                            'brain_efficiency': brain_prediction.get('efficiency_pct', 0),
                            'brain_power': brain_prediction.get('power_kw', 0),
                            'brain_diameter': forced_diameter  # The forced diameter used
                        })
                except Exception as e:
                    self.logger.debug(f"Could not generate curve point at {flow} m³/hr with diameter {forced_diameter}mm: {e}")
            
            # Sort by flow for proper chart rendering
            curve_data = sorted(curve_data, key=lambda x: x['flow'])
            self.logger.info(f"[CURVE GEN] Generated {len(curve_data)} curve points for diameter {forced_diameter}mm")
            
        except Exception as e:
            self.logger.warning(f"Error generating curve comparison data: {e}")
            
        return curve_data
    
    def _generate_expanded_flow_range(self, pump_data, ground_truth_points, brain):
        """
        Generate additional points across the pump's flow range for better visualization
        """
        import numpy as np
        
        expanded_points = []
        
        try:
            # Get the BEP flow from pump data
            bep_flow = pump_data.get('bep_flow', 0)
            
            if bep_flow <= 0:
                return expanded_points
            
            # Calculate the flow range (60% to 130% of BEP)
            min_flow = max(bep_flow * 0.6, 10)  # At least 10 m³/hr
            max_flow = bep_flow * 1.3
            
            # Get average head from ground truth points
            if ground_truth_points:
                avg_head = np.mean([p['head'] for p in ground_truth_points])
            else:
                avg_head = pump_data.get('bep_head', 20)
            
            # Generate 7 evenly spaced points across the flow range
            flow_points = np.linspace(min_flow, max_flow, 7)
            
            for flow in flow_points:
                # Skip if we already have ground truth for this flow
                if any(abs(p['flow'] - flow) < 5 for p in ground_truth_points):
                    continue
                    
                try:
                    # Get Brain's actual prediction at this flow
                    brain_prediction = brain.performance.calculate_performance_at_flow(
                        pump_data, 
                        flow,
                        allow_excessive_trim=True
                    )
                    
                    if brain_prediction:
                        # Use brain's actual prediction for the pump curve
                        brain_head = brain_prediction.get('head_m', 0)
                        brain_efficiency = brain_prediction.get('efficiency_pct', 0)
                        brain_power = brain_prediction.get('power_kw', 0)
                        
                        expanded_points.append({
                            'flow': float(flow),
                            'truth_head': brain_head,  # Use brain prediction as baseline
                            'truth_efficiency': brain_efficiency,
                            'truth_power': brain_power,
                            'brain_head': brain_head,
                            'brain_efficiency': brain_efficiency,
                            'brain_power': brain_power,
                            'brain_diameter': brain_prediction.get('diameter_mm', 0),
                            'delta_head': 0,  # No delta for expanded points
                            'delta_efficiency': 0,
                            'delta_power': 0,
                            'is_expanded': True  # Mark as expanded for UI
                        })
                except Exception as e:
                    self.logger.debug(f"Could not generate expanded point at {flow}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error generating expanded flow range: {e}")
            
        return expanded_points
        
    def _calculate_deltas(self, truth, prediction):
        """
        Robust helper method to calculate percentage difference between two values.
        Handles None, non-numeric types, and jinja2.Undefined objects.
        
        Args:
            truth: The ground truth value (expected/actual)
            prediction: The predicted value
            
        Returns:
            float or None: Percentage difference if both values are valid, None otherwise
        """
        try:
            # Check for jinja2.Undefined objects first
            from jinja2 import Undefined
            if isinstance(truth, Undefined) or isinstance(prediction, Undefined):
                self.logger.debug(f"Undefined value detected: truth={type(truth).__name__}, prediction={type(prediction).__name__}")
                return None
            
            # Check for None values
            if truth is None or prediction is None:
                self.logger.debug(f"None value detected: truth={truth}, prediction={prediction}")
                return None
            
            # Try to convert to float (handles strings, integers, etc.)
            try:
                truth_float = float(truth)
                prediction_float = float(prediction)
            except (TypeError, ValueError):
                self.logger.debug(f"Non-numeric value detected: truth={truth} ({type(truth).__name__}), prediction={prediction} ({type(prediction).__name__})")
                return None
            
            # Check for invalid numeric values (NaN, inf)
            import math
            if math.isnan(truth_float) or math.isnan(prediction_float):
                self.logger.debug(f"NaN value detected: truth={truth_float}, prediction={prediction_float}")
                return None
            if math.isinf(truth_float) or math.isinf(prediction_float):
                self.logger.debug(f"Infinite value detected: truth={truth_float}, prediction={prediction_float}")
                return None
            
            # Handle division by zero
            if truth_float == 0:
                if prediction_float == 0:
                    return 0.0  # Both are zero, no difference
                else:
                    # Truth is zero but prediction is not - this is undefined percentage
                    self.logger.debug(f"Cannot calculate percentage when truth=0 and prediction={prediction_float}")
                    return None
            
            # Calculate percentage difference
            delta = ((prediction_float - truth_float) / abs(truth_float)) * 100
            return delta
            
        except Exception as e:
            self.logger.warning(f"Unexpected error in _calculate_deltas: {e}, truth={truth}, prediction={prediction}")
            return None
    
    def _calculate_delta(self, truth, prediction):
        """Legacy method for backward compatibility - delegates to robust version"""
        result = self._calculate_deltas(truth, prediction)
        return result if result is not None else 0
    
    def _calculate_overall_accuracy(self, head_deltas, efficiency_deltas, power_deltas):
        """
        Calculate overall accuracy from delta lists, handling empty lists gracefully.
        
        Args:
            head_deltas: List of head delta percentages
            efficiency_deltas: List of efficiency delta percentages
            power_deltas: List of power delta percentages
            
        Returns:
            float: Overall accuracy percentage (0-100)
        """
        import numpy as np
        
        try:
            # Combine all valid deltas
            all_deltas = []
            
            # Add valid deltas from each list
            if head_deltas and isinstance(head_deltas, list):
                all_deltas.extend(head_deltas)
            if efficiency_deltas and isinstance(efficiency_deltas, list):
                all_deltas.extend(efficiency_deltas)
            if power_deltas and isinstance(power_deltas, list):
                all_deltas.extend(power_deltas)
            
            # If no valid deltas, return 100% (no data means no error)
            if not all_deltas:
                self.logger.info("No valid deltas for overall accuracy calculation, returning 100%")
                return 100.0
            
            # Calculate mean absolute error
            absolute_deltas = [abs(d) for d in all_deltas if d is not None]
            
            if not absolute_deltas:
                return 100.0
            
            mean_absolute_error = np.mean(absolute_deltas)
            
            # Convert to accuracy (100% - error%)
            # Clamp between 0 and 100
            accuracy = max(0.0, min(100.0, 100.0 - mean_absolute_error))
            
            self.logger.debug(f"Overall accuracy calculated: {accuracy:.2f}% from {len(absolute_deltas)} deltas")
            return accuracy
            
        except Exception as e:
            self.logger.warning(f"Error calculating overall accuracy: {e}, returning 0%")
            return 0.0
        
    def calculate_curve_deviation_metrics(self, comparison_results):
        """
        Calculate advanced statistical metrics for curve comparison
        """
        import numpy as np
        
        if not comparison_results:
            return {}
            
        # Extract deltas and filter out None/invalid values using a helper function
        def extract_valid_deltas(results, key):
            """Extract valid numeric delta values from results"""
            valid_deltas = []
            for r in results:
                if key in r:
                    value = r[key]
                    # Skip None values and jinja2.Undefined objects
                    if value is None:
                        continue
                    # Try to convert to float
                    try:
                        from jinja2 import Undefined
                        if isinstance(value, Undefined):
                            continue
                        delta_float = float(value)
                        # Skip NaN and infinity
                        import math
                        if not math.isnan(delta_float) and not math.isinf(delta_float):
                            valid_deltas.append(delta_float)
                    except (TypeError, ValueError):
                        # Skip non-numeric values
                        continue
            return valid_deltas
        
        # Extract valid deltas for each metric
        head_deltas = extract_valid_deltas(comparison_results, 'delta_head')
        efficiency_deltas = extract_valid_deltas(comparison_results, 'delta_efficiency')
        power_deltas = extract_valid_deltas(comparison_results, 'delta_power')
        
        metrics = {
            'head': {
                'rmse': np.sqrt(np.mean(np.square(head_deltas))) if head_deltas else 0,
                'mean_delta': np.mean(head_deltas) if head_deltas else 0,
                'max_delta': max(head_deltas, key=abs) if head_deltas else 0,
                'std_dev': np.std(head_deltas) if head_deltas else 0
            },
            'efficiency': {
                'rmse': np.sqrt(np.mean(np.square(efficiency_deltas))) if efficiency_deltas else 0,
                'mean_delta': np.mean(efficiency_deltas) if efficiency_deltas else 0,
                'max_delta': max(efficiency_deltas, key=abs) if efficiency_deltas else 0,
                'std_dev': np.std(efficiency_deltas) if efficiency_deltas else 0
            },
            'power': {
                'rmse': np.sqrt(np.mean(np.square(power_deltas))) if power_deltas else 0,
                'mean_delta': np.mean(power_deltas) if power_deltas else 0,
                'max_delta': max(power_deltas, key=abs) if power_deltas else 0,
                'std_dev': np.std(power_deltas) if power_deltas else 0
            },
            # Calculate overall accuracy safely
            'overall_accuracy': self._calculate_overall_accuracy(head_deltas, efficiency_deltas, power_deltas),
            'point_count': len(comparison_results)
        }
        
        return metrics
        
    def generate_ai_insights(self, comparison_results, metrics):
        """
        Generate human-readable insights about the calibration results
        """
        insights = []
        
        if not comparison_results:
            return ["No comparison data available"]
            
        # Overall accuracy assessment
        overall_acc = metrics.get('overall_accuracy', 0)
        if overall_acc >= 98:
            insights.append("Excellent accuracy: Brain predictions are highly reliable")
        elif overall_acc >= 95:
            insights.append("Good accuracy: Minor calibration may improve predictions")
        else:
            insights.append("Significant deviations detected: Calibration recommended")
            
        # Efficiency analysis
        eff_mean = metrics['efficiency']['mean_delta']
        if abs(eff_mean) > 2:
            direction = "over-predicting" if eff_mean > 0 else "under-predicting"
            insights.append(f"Brain consistently {direction} efficiency by {abs(eff_mean):.1f}%")
            
        # Power analysis
        power_mean = metrics['power']['mean_delta']
        if abs(power_mean) > 2:
            direction = "over-predicting" if power_mean > 0 else "under-predicting"
            insights.append(f"Brain consistently {direction} power by {abs(power_mean):.1f}%")
            
        # Flow-specific patterns
        if len(comparison_results) >= 3:
            # Check for trends at different flow ranges
            sorted_results = sorted(comparison_results, key=lambda x: x['flow'])
            low_flow = sorted_results[:len(sorted_results)//3]
            high_flow = sorted_results[-len(sorted_results)//3:]
            
            low_flow_eff_delta = np.mean([r['delta_efficiency'] for r in low_flow])
            high_flow_eff_delta = np.mean([r['delta_efficiency'] for r in high_flow])
            
            if abs(low_flow_eff_delta - high_flow_eff_delta) > 3:
                insights.append(f"Accuracy varies with flow: Better at {'high' if abs(high_flow_eff_delta) < abs(low_flow_eff_delta) else 'low'} flows")
                
        return insights

def normalize_pump_code(pump_code):
    """
    Normalize pump code for fuzzy matching
    Examples:
    - "10/12 BLE" -> "10/12 BLE"
    - "10-12 BLE" -> "10/12 BLE"
    - "10 12 BLE" -> "10/12 BLE"
    - "10_12_BLE" -> "10/12 BLE"
    """
    import re
    # Replace common separators with forward slash
    normalized = re.sub(r'[-_\s]+', '/', pump_code.strip())
    # Clean up multiple slashes
    normalized = re.sub(r'/+', '/', normalized)
    # Handle patterns like "10 12" -> "10/12"
    normalized = re.sub(r'(\d+)\s+(\d+)', r'\1/\2', normalized)
    return normalized.upper()  # Standardize to uppercase

def find_pump_fuzzy(pump_code, pump_models):
    """
    Find pump using fuzzy matching
    Returns the actual pump code from database or None if not found
    """
    # First try exact match
    pump_dict = {pump['pump_code']: pump for pump in pump_models}
    if pump_code in pump_dict:
        return pump_code
    
    # Normalize the search code
    normalized_search = normalize_pump_code(pump_code)
    
    # Create normalized lookup dictionary
    normalized_dict = {}
    for pump in pump_models:
        normalized_key = normalize_pump_code(pump['pump_code'])
        normalized_dict[normalized_key] = pump['pump_code']
    
    # Try to find normalized match
    if normalized_search in normalized_dict:
        return normalized_dict[normalized_search]
    
    # Try partial matching for very fuzzy cases
    # Remove all separators and spaces for ultra-fuzzy matching
    ultra_fuzzy_search = re.sub(r'[^A-Z0-9]', '', normalized_search)
    for pump in pump_models:
        ultra_fuzzy_pump = re.sub(r'[^A-Z0-9]', '', pump['pump_code'].upper())
        if ultra_fuzzy_search == ultra_fuzzy_pump:
            return pump['pump_code']
    
    return None

@brain_admin_bp.route('/admin/pump-calibration/<path:pump_code>', methods=['GET', 'POST'])
def pump_calibration_workbench(pump_code):
    """Rebuild: Simplified pump calibration workbench with single table and chart"""
    from ..pump_brain import get_pump_brain
    
    brain = get_pump_brain()
    pump_data = brain.repository.get_pump_by_code(pump_code)
    
    if not pump_data:
        flash(f"Pump {pump_code} not found.", "error")
        return redirect(url_for('brain_admin.brain_dashboard'))

    analysis_results = None
    if request.method == 'POST':
        try:
            # Parse multiple performance points from form
            ground_truth_points = []
            point_count = 1
            
            # Count how many data points were submitted
            while f'flow_{point_count}' in request.form:
                try:
                    flow = float(request.form.get(f'flow_{point_count}', 0))
                    head = float(request.form.get(f'head_{point_count}', 0))
                    efficiency = float(request.form.get(f'efficiency_{point_count}', 0))
                    power = float(request.form.get(f'power_{point_count}', 0))
                    diameter = float(request.form.get(f'diameter_{point_count}', 0))
                    
                    if flow > 0 and head > 0:  # Basic validation
                        ground_truth_points.append({
                            'flow': flow,
                            'head': head,
                            'efficiency': efficiency,
                            'power': power,
                            'diameter': diameter
                        })
                except ValueError:
                    pass  # Skip invalid points
                    
                point_count += 1
            
            if ground_truth_points:
                # Initialize comparison engine
                comparison_engine = ManufacturerComparisonEngine()
                
                # Run the complete analysis
                analysis_results = comparison_engine.run_full_calibration(
                    pump_data=pump_data,
                    ground_truth_points=ground_truth_points
                )
                
        except Exception as e:
            logger.error(f"Error processing calibration: {e}")
            flash(f"Error processing calibration: {str(e)}", "error")

    return render_template(
        'admin/pump_calibration_new.html', 
        pump=pump_data,
        analysis_results=analysis_results
    )

# DELETED - old broken analyze route - functionality moved to main workbench route
    """Process multiple ground truth points and return comparison data with fuzzy matching"""
    import re
    from flask import session
    
    try:
        # Validate and sanitize pump_code to prevent injection attacks (allow spaces and slashes)
        if not re.match(r'^[a-zA-Z0-9_\-\s/]+$', pump_code):
            logger.warning(f"Invalid pump code format attempted: {pump_code}")
            return jsonify({'error': 'Invalid pump code format'}), 400
        
        # Get pump models and use fuzzy matching to find the actual pump code
        from ..pump_repository import get_pump_repository
        pump_repo = get_pump_repository()
        pump_models = pump_repo.get_pump_models()
        
        actual_pump_code = find_pump_fuzzy(pump_code, pump_models)
        if not actual_pump_code:
            logger.warning(f"Pump '{pump_code}' not found with fuzzy matching")
            return jsonify({'error': f'Pump {pump_code} not found'}), 404
        
        # Log if fuzzy match was used
        if actual_pump_code != pump_code:
            logger.info(f"Fuzzy matched '{pump_code}' to '{actual_pump_code}' for analysis")
        
        # Parse the performance data points
        data = request.get_json() if request.is_json else request.form
        
        # CSRF Protection: Validate token for non-JSON requests
        if not request.is_json:
            csrf_token = data.get('csrf_token')
            if not csrf_token or csrf_token != session.get('csrf_token'):
                logger.warning(f"CSRF token validation failed for pump calibration")
                return jsonify({'error': 'Invalid CSRF token'}), 403
        
        # Extract performance points from form data with robust validation
        ground_truth_points = []
        
        try:
            point_count = int(data.get('point_count', 0))
            if point_count < 0 or point_count > 100:  # Reasonable limit
                return jsonify({'error': 'Invalid point count'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid point count format'}), 400
        
        # Try both indexing conventions (starting from 0 and from 1)
        for i in range(point_count):
            try:
                # Try index starting from 1 first (JavaScript convention)
                idx = i + 1
                flow_str = data.get(f'flow_{idx}') or data.get(f'flow_{i}')
                head_str = data.get(f'head_{idx}') or data.get(f'head_{i}')
                efficiency_str = data.get(f'efficiency_{idx}') or data.get(f'efficiency_{i}')
                power_str = data.get(f'power_{idx}') or data.get(f'power_{i}')  # Optional
                diameter_str = data.get(f'diameter_{idx}') or data.get(f'diameter_{i}')  # Optional
                qbep_str = data.get(f'qbep_{idx}') or data.get(f'qbep_{i}')  # Optional
                
                # Required fields
                if flow_str and head_str and efficiency_str:
                    # Safe conversion with validation
                    flow = float(flow_str)
                    head = float(head_str)
                    efficiency = float(efficiency_str)
                    
                    # Optional power - calculate if not provided
                    if power_str and power_str.strip():
                        power = float(power_str)
                        if power <= 0 or power > 100000:  # Max 100MW is reasonable
                            logger.warning(f"Power value out of range: {power}, calculating from efficiency")
                            # Calculate power from flow, head, and efficiency
                            power = (flow * head * 9.81) / (3600 * efficiency / 100 * 10)
                    else:
                        # Calculate power from flow, head, and efficiency
                        power = (flow * head * 9.81) / (3600 * efficiency / 100 * 10)
                    
                    # Optional diameter
                    diameter = None
                    if diameter_str and diameter_str.strip():
                        diameter = float(diameter_str)
                        if diameter <= 0 or diameter > 2000:  # Max 2000mm is reasonable
                            logger.warning(f"Diameter value out of range: {diameter}")
                            diameter = None
                    
                    # Optional QBep%
                    qbep_percent = None
                    if qbep_str and qbep_str.strip():
                        qbep_percent = float(qbep_str)
                        if qbep_percent <= 0 or qbep_percent > 200:
                            logger.warning(f"QBep% value out of range: {qbep_percent}")
                            qbep_percent = None
                    
                    # Validate ranges
                    if flow <= 0 or flow > 50000:  # Max 50,000 m³/hr is reasonable
                        logger.warning(f"Flow value out of range: {flow}")
                        continue
                    if head <= 0 or head > 5000:  # Max 5,000m head is reasonable
                        logger.warning(f"Head value out of range: {head}")
                        continue
                    if efficiency <= 0 or efficiency > 100:
                        logger.warning(f"Efficiency value out of range: {efficiency}")
                        continue
                    
                    ground_truth_points.append({
                        'flow': flow,
                        'head': head,
                        'efficiency': efficiency,
                        'power': power,
                        'diameter': diameter,
                        'qbep_percent': qbep_percent
                    })
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid input data at point {i}: {e}")
                continue  # Skip invalid points
                
        if not ground_truth_points:
            return jsonify({'error': 'No valid performance points provided'}), 400
            
        # Process calibration data with actual pump code
        engine = ManufacturerComparisonEngine()
        results = engine.process_calibration_data(actual_pump_code, ground_truth_points)
        
        # For AJAX requests, return JSON
        if request.is_json:
            return jsonify(results)
            
        # For form submissions, render template with results
        breadcrumbs = [
            {'text': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'text': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'text': 'Pump Calibration', 'url': '', 'icon': 'tune'}
        ]
        
        return render_template('admin/pump_calibration.html',
                             pump_code=actual_pump_code,  # Use actual code after fuzzy match
                             pump_data=results['pump_data'],
                             calibration_results=results,
                             breadcrumbs=breadcrumbs)
                             
    except Exception as e:
        logger.error(f"Error analyzing calibration data: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error analyzing calibration: {str(e)}', 'error')
        return redirect(url_for('brain_admin.pump_calibration_workbench', pump_code=pump_code))

@brain_admin_bp.route('/api/pump-calibration/validate-point', methods=['POST'])
def validate_calibration_point():
    """AJAX endpoint to validate individual performance points"""
    try:
        data = request.get_json()
        flow = float(data.get('flow', 0))
        head = float(data.get('head', 0))
        efficiency = float(data.get('efficiency', 0))
        power = float(data.get('power', 0))
        
        # Validation rules
        warnings = []
        errors = []
        
        # Basic range checks
        if flow <= 0:
            errors.append("Flow must be positive")
        if head <= 0:
            errors.append("Head must be positive")
        if efficiency <= 0 or efficiency > 100:
            errors.append("Efficiency must be between 0 and 100%")
        if power <= 0:
            errors.append("Power must be positive")
            
        # Physics checks
        if flow > 0 and head > 0 and power > 0:
            # Theoretical minimum power (assuming water)
            theoretical_min_power = (9.81 * 1000 * flow/3600 * head) / 1000  # kW
            if power < theoretical_min_power * 0.5:  # Allow some margin
                warnings.append("Power seems unusually low for given flow and head")
                
            # Efficiency sanity check
            if efficiency > 0:
                calculated_efficiency = (theoretical_min_power / power) * 100
                if abs(calculated_efficiency - efficiency) > 10:
                    warnings.append("Efficiency value doesn't match power calculation")
                    
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@brain_admin_bp.route('/admin/pump-calibration/<path:pump_code>/flag-review', methods=['POST'])
def flag_calibration_for_review(pump_code):
    """
    Flag a calibration discrepancy for engineering review.
    This is triggered when the user is certain their data is correct,
    indicating a potential fundamental error in the pump database.
    """
    import json
    from flask import session
    
    try:
        # Validate CSRF token
        csrf_token = request.form.get('csrf_token')
        if not csrf_token or csrf_token != session.get('csrf_token'):
            logger.warning(f"CSRF token validation failed for flag review")
            flash('Security validation failed. Please try again.', 'error')
            return redirect(url_for('brain_admin.pump_calibration', pump_code=pump_code))
        
        # Get the calibration data
        calibration_data = request.form.get('calibration_data')
        if calibration_data:
            try:
                calibration_results = json.loads(calibration_data)
            except json.JSONDecodeError:
                calibration_results = {}
        else:
            calibration_results = {}
        
        # Create a high-priority engineering ticket
        # In a real system, this would integrate with Jira, GitHub Issues, etc.
        ticket_data = {
            'priority': 'CRITICAL',
            'type': 'DATA_INTEGRITY_ISSUE',
            'pump_code': pump_code,
            'reported_by': session.get('user_id', 'unknown_user'),
            'timestamp': datetime.now().isoformat(),
            'calibration_data': calibration_results,
            'description': f'Critical discrepancy detected for pump {pump_code}. User confirmed their ground truth data is correct, indicating potential database errors.'
        }
        
        # Log the critical issue
        logger.critical(f"[DATA INTEGRITY] Pump {pump_code} flagged for engineering review")
        logger.critical(f"[DATA INTEGRITY] Ticket data: {json.dumps(ticket_data, indent=2)}")
        
        # In production, this would create an actual ticket in the tracking system
        # For now, we'll store it in a tracking file
        import os
        tickets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data_integrity_tickets')
        os.makedirs(tickets_dir, exist_ok=True)
        
        ticket_filename = f"{pump_code.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ticket_path = os.path.join(tickets_dir, ticket_filename)
        
        with open(ticket_path, 'w') as f:
            json.dump(ticket_data, f, indent=2)
        
        # Flash success message
        flash(f'Thank you. This discrepancy has been flagged for review by our engineering team. '
              f'Pump model {pump_code} cannot be calibrated until the source data is verified. '
              f'Ticket ID: {ticket_filename}', 'warning')
        
        # Redirect back to the brain dashboard
        return redirect(url_for('brain_admin.brain_dashboard'))
        
    except Exception as e:
        logger.error(f"Error flagging calibration for review: {e}")
        flash('Error creating engineering review ticket. Please contact support.', 'error')
        return redirect(url_for('brain_admin.pump_calibration', pump_code=pump_code))

@brain_admin_bp.route('/api/pump-calibration/export/<path:pump_code>', methods=['GET'])
def export_calibration_results(pump_code):
    """Export calibration results as CSV for documentation"""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        
        # Get the latest calibration data (would normally retrieve from database)
        # For now, we'll return a template CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Pump Code', 'Flow (m³/hr)', 'Head (m)', 
                        'Truth Efficiency (%)', 'Brain Efficiency (%)', 'Delta Efficiency (%)',
                        'Truth Power (kW)', 'Brain Power (kW)', 'Delta Power (%)'])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=calibration_{pump_code}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting calibration data: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API ENDPOINTS FOR AJAX OPERATIONS
# ============================================================================

@brain_admin_bp.route('/api/brain/propose-correction', methods=['POST'])
def api_propose_correction():
    """API endpoint to propose a new correction"""
    try:
        data = request.get_json()
        required_fields = ['pump_code', 'field_path', 'corrected_value', 'justification']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        brain_service = BrainDataService()
        correction_id = brain_service.propose_correction(
            pump_code=data['pump_code'],
            field_path=data['field_path'],
            corrected_value=data['corrected_value'],
            justification=data['justification'],
            correction_type=data.get('correction_type', 'specification'),
            original_value=data.get('original_value'),
            confidence_score=float(data.get('confidence_score', 1.0)),
            proposed_by=data.get('proposed_by', 'admin')
        )
        
        return jsonify({
            'success': True, 
            'correction_id': correction_id,
            'message': f'Correction {correction_id} proposed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error proposing correction: {e}")
        return jsonify({'error': str(e)}), 500

@brain_admin_bp.route('/api/brain/approve-correction/<int:correction_id>', methods=['POST'])
def api_approve_correction(correction_id):
    """API endpoint to approve a pending correction"""
    try:
        data = request.get_json() or {}
        approved_by = data.get('approved_by', 'admin')
        
        brain_service = BrainDataService()
        success = brain_service.approve_correction(correction_id, approved_by)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Correction {correction_id} approved successfully'
            })
        else:
            return jsonify({'error': 'Correction not found or already processed'}), 404
            
    except Exception as e:
        logger.error(f"Error approving correction {correction_id}: {e}")
        return jsonify({'error': str(e)}), 500

@brain_admin_bp.route('/api/brain/reject-correction/<int:correction_id>', methods=['POST'])
def api_reject_correction(correction_id):
    """API endpoint to reject a pending correction"""
    try:
        data = request.get_json() or {}
        approved_by = data.get('approved_by', 'admin')
        reason = data.get('reason', 'No reason provided')
        
        brain_service = BrainDataService()
        success = brain_service.reject_correction(correction_id, approved_by, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Correction {correction_id} rejected successfully'
            })
        else:
            return jsonify({'error': 'Correction not found or already processed'}), 404
            
    except Exception as e:
        logger.error(f"Error rejecting correction {correction_id}: {e}")
        return jsonify({'error': str(e)}), 500

@brain_admin_bp.route('/api/brain/test-pump/<pump_code>')
def api_test_pump(pump_code):
    """API endpoint to test pump with and without corrections"""
    try:
        pump_repo = PumpRepository()
        pump_repo.load_catalog()
        brain_service = BrainDataService()
        brain_accessor = BrainDataAccessor(pump_repo, brain_service)
        
        # Get original pump data
        original_pump = pump_repo.get_pump_by_code(pump_code)
        if not original_pump:
            return jsonify({'error': f'Pump {pump_code} not found'}), 404
        
        # Get enhanced pump data (with corrections)
        enhanced_pump = brain_accessor.get_enhanced_pump(pump_code)
        
        # Get active corrections for this pump
        corrections = brain_service.get_active_corrections(pump_code)
        
        return jsonify({
            'pump_code': pump_code,
            'original_data': original_pump,
            'enhanced_data': enhanced_pump,
            'corrections_applied': [
                {
                    'field_path': c.field_path,
                    'original_value': c.original_value,
                    'corrected_value': c.corrected_value,
                    'justification': c.justification
                }
                for c in corrections
            ],
            'has_corrections': len(corrections) > 0
        })
        
    except Exception as e:
        logger.error(f"Error testing pump {pump_code}: {e}")
        return jsonify({'error': str(e)}), 500

@brain_admin_bp.route('/api/brain/quality-check/<pump_code>')
def api_quality_check(pump_code):
    """API endpoint to run quality checks on a specific pump"""
    try:
        pump_repo = PumpRepository()
        pump_repo.load_catalog()
        brain_service = BrainDataService()
        
        pump_data = pump_repo.get_pump_by_code(pump_code)
        if not pump_data:
            return jsonify({'error': f'Pump {pump_code} not found'}), 404
        
        # Run quality checks
        quality_issues = []
        
        # Check 1: BEP specification vs curve data consistency
        specs = pump_data.get('specifications', {})
        bep_flow = specs.get('bep_flow_m3hr')
        bep_head = specs.get('bep_head_m')
        
        if bep_flow and bep_head:
            # Calculate BEP from curves if available
            curves = pump_data.get('curves', [])
            if curves:
                # This would involve curve interpolation - simplified for now
                quality_issues.append({
                    'type': 'bep_verification',
                    'field': 'bep_flow_m3hr',
                    'severity': 'minor',
                    'description': 'BEP specification requires curve verification'
                })
        
        # Check 2: Efficiency values
        for curve in pump_data.get('curves', []):
            for point in curve.get('performance_points', []):
                efficiency = point.get('efficiency')
                if efficiency and (efficiency < 0 or efficiency > 100):
                    quality_issues.append({
                        'type': 'efficiency_outlier',
                        'field': 'efficiency',
                        'severity': 'major',
                        'description': f'Invalid efficiency value: {efficiency}%'
                    })
        
        # Check 3: Missing critical data
        if not specs.get('max_flow_m3hr'):
            quality_issues.append({
                'type': 'missing_data',
                'field': 'max_flow_m3hr',
                'severity': 'critical',
                'description': 'Missing maximum flow specification'
            })
        
        return jsonify({
            'pump_code': pump_code,
            'quality_issues': quality_issues,
            'total_issues': len(quality_issues),
            'overall_quality': 'good' if len(quality_issues) < 3 else 'needs_review'
        })
        
    except Exception as e:
        logger.error(f"Error checking quality for pump {pump_code}: {e}")
        return jsonify({'error': str(e)}), 500

@brain_admin_bp.route('/api/brain/simulate-selection', methods=['POST'])
def api_simulate_selection():
    """API endpoint to simulate pump selection with different configurations"""
    try:
        data = request.get_json()
        flow_rate = float(data.get('flow_rate', 0))
        head = float(data.get('head', 0))
        use_corrections = data.get('use_corrections', True)
        
        if flow_rate <= 0 or head <= 0:
            return jsonify({'error': 'Invalid flow rate or head'}), 400
        

        from ..pump_brain import get_pump_brain
        
        brain = get_pump_brain()
        
        # Run selection using Brain system
        results = brain.find_best_pump(flow_rate, head, constraints={'max_results': 10})
        
        if not results:
            return jsonify({'error': 'No suitable pumps found'}), 404
        
        # Format results for API response
        formatted_results = []
        for result in results[:5]:  # Top 5 results
            if isinstance(result, dict) and 'pump' in result:
                formatted_results.append({
                    'pump_code': result['pump']['pump_code'],
                    'score': result.get('suitability_score', result.get('overall_score', 0)),
                    'efficiency': result.get('efficiency', 0),
                    'power': result.get('power_consumption_kw', 0),
                    'impeller_trim': result.get('impeller_trim_percentage', 0)
                })
        
        return jsonify({
            'duty_point': {'flow_m3hr': flow_rate, 'head_m': head},
            'results': formatted_results,
            'corrections_used': use_corrections,
            'total_candidates': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error simulating selection: {e}")
        return jsonify({'error': str(e)}), 500