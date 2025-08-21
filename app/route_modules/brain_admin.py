"""
Brain Admin Routes - Enterprise-grade data correction and configuration management
Implements the two-schema architecture with golden source protection
"""

import logging
import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
from ..brain_data_service import BrainDataService, BrainDataAccessor
from ..pump_repository import PumpRepository

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
        
    def process_calibration_data(self, pump_code, ground_truth_points):
        """
        Main processing flow for multi-point calibration
        
        Args:
            pump_code: Pump identifier
            ground_truth_points: List of dicts with flow, head, efficiency, power
            
        Returns:
            Dict with comparison results, metrics, and insights
        """
        from ..pump_brain import PumpBrain
        from ..pump_repository import PumpRepository
        import numpy as np
        
        # Get pump data
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
            
        # Initialize Brain
        brain = PumpBrain()
        
        # Process each ground truth point
        comparison_results = []
        for point in ground_truth_points:
            try:
                # Get Brain prediction
                brain_result = brain.performance.calculate_at_point_industry_standard(
                    pump_data, 
                    point['flow'], 
                    point['head']
                )
                
                if brain_result:
                    # Calculate deltas
                    comparison = {
                        'flow': point['flow'],
                        'truth_head': point['head'],
                        'truth_efficiency': point['efficiency'],
                        'truth_power': point['power'],
                        'brain_head': point['head'],  # Brain calculates for exact head
                        'brain_efficiency': brain_result.get('efficiency_pct', 0),
                        'brain_power': brain_result.get('power_kw', 0),
                        'brain_diameter': brain_result.get('impeller_diameter_mm', 0),
                        'delta_efficiency': self._calculate_delta(point['efficiency'], brain_result.get('efficiency_pct', 0)),
                        'delta_power': self._calculate_delta(point['power'], brain_result.get('power_kw', 0))
                    }
                    comparison_results.append(comparison)
                else:
                    self.logger.warning(f"No Brain result for {pump_code} at {point['flow']} m³/hr @ {point['head']}m")
                    
            except Exception as e:
                self.logger.error(f"Error processing point {point}: {e}")
                
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
            'metrics': metrics,
            'insights': insights
        }
        
    def _calculate_delta(self, truth, prediction):
        """Calculate percentage difference"""
        if truth == 0:
            return 0
        return ((prediction - truth) / truth) * 100
        
    def calculate_curve_deviation_metrics(self, comparison_results):
        """
        Calculate advanced statistical metrics for curve comparison
        """
        import numpy as np
        
        if not comparison_results:
            return {}
            
        # Extract deltas
        efficiency_deltas = [r['delta_efficiency'] for r in comparison_results]
        power_deltas = [r['delta_power'] for r in comparison_results]
        
        metrics = {
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
            'overall_accuracy': 100 - (abs(np.mean(efficiency_deltas + power_deltas)) if (efficiency_deltas + power_deltas) else 0),
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

@brain_admin_bp.route('/admin/pump-calibration/<pump_code>')
def pump_calibration_workbench(pump_code):
    """Display the calibration workbench for a specific pump"""
    try:
        # Build breadcrumbs
        breadcrumbs = [
            {'text': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'text': 'Brain Dashboard', 'url': url_for('brain_admin.brain_dashboard'), 'icon': 'psychology'},
            {'text': 'Pump Calibration', 'url': '', 'icon': 'tune'}
        ]
        
        # Get pump details
        pump_repo = PumpRepository()
        pump_repo.load_catalog()
        pump_models = pump_repo.get_pump_models()
        pump_data = None
        for pump in pump_models:
            if pump['pump_code'] == pump_code:
                pump_data = pump
                break
                
        if not pump_data:
            flash(f'Pump {pump_code} not found', 'error')
            return redirect(url_for('brain_admin.brain_dashboard'))
            
        return render_template('admin/pump_calibration.html',
                             pump_code=pump_code,
                             pump_data=pump_data,
                             breadcrumbs=breadcrumbs)
                             
    except Exception as e:
        logger.error(f"Error loading pump calibration workbench: {e}")
        flash(f'Error loading calibration workbench: {str(e)}', 'error')
        return redirect(url_for('brain_admin.brain_dashboard'))

@brain_admin_bp.route('/admin/pump-calibration/<pump_code>/analyze', methods=['POST'])
def analyze_pump_calibration(pump_code):
    """Process multiple ground truth points and return comparison data"""
    try:
        # Parse the performance data points
        data = request.get_json() if request.is_json else request.form
        
        # Extract performance points from form data
        ground_truth_points = []
        point_count = int(data.get('point_count', 0))
        
        for i in range(point_count):
            flow = data.get(f'flow_{i}')
            head = data.get(f'head_{i}')
            efficiency = data.get(f'efficiency_{i}')
            power = data.get(f'power_{i}')
            
            if flow and head and efficiency and power:
                ground_truth_points.append({
                    'flow': float(flow),
                    'head': float(head),
                    'efficiency': float(efficiency),
                    'power': float(power)
                })
                
        if not ground_truth_points:
            return jsonify({'error': 'No valid performance points provided'}), 400
            
        # Process calibration data
        engine = ManufacturerComparisonEngine()
        results = engine.process_calibration_data(pump_code, ground_truth_points)
        
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
                             pump_code=pump_code,
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

@brain_admin_bp.route('/api/pump-calibration/export/<pump_code>', methods=['GET'])
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