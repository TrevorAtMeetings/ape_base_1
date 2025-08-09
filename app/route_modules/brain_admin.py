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
        
        return render_template('admin/brain_dashboard_clean.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading brain dashboard: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin/brain_dashboard_clean.html', stats={})

@brain_admin_bp.route('/admin/brain/data-quality')
def data_quality_dashboard():
    """Data Quality Management Dashboard"""
    try:
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
                             total_issues=len(all_issues))
                             
    except Exception as e:
        logger.error(f"Error loading data quality dashboard: {e}")
        flash(f'Error loading data quality dashboard: {str(e)}', 'error')
        return render_template('admin/data_quality.html', 
                             issues_by_severity={}, pump_issues={}, total_issues=0)

@brain_admin_bp.route('/admin/brain/corrections')
def corrections_dashboard():
    """Data Corrections Management Dashboard"""
    try:
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
                             stats=correction_stats)
                             
    except Exception as e:
        logger.error(f"Error loading corrections dashboard: {e}")
        flash(f'Error loading corrections dashboard: {str(e)}', 'error')
        return render_template('admin/corrections.html', 
                             active_corrections=[], pending_corrections=[], stats={})

@brain_admin_bp.route('/admin/brain/workbench')
def brain_workbench():
    """Brain Logic Workbench - Test configurations and corrections"""
    try:
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
                             pump_codes=pump_codes)
                             
    except Exception as e:
        logger.error(f"Error loading brain workbench: {e}")
        flash(f'Error loading brain workbench: {str(e)}', 'error')
        return render_template('admin/brain_workbench.html',
                             production_config={}, pump_codes=[])

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
        
        # CATALOG ENGINE RETIRED - USING BRAIN SYSTEM
        # from ..catalog_engine import get_catalog_engine
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