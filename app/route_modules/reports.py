import logging
from flask import (
    Blueprint, request, render_template, redirect, url_for, session, 
    send_file, jsonify, make_response
)
from urllib.parse import unquote
from ..session_manager import (
    safe_session_get, safe_session_set, safe_flash
)
from .. import app

logger = logging.getLogger(__name__)

def _get_bep_analysis_brain(pump_data, brain):
    """Get BEP analysis using Brain system - works with dictionary format"""
    try:
        # Extract BEP data from pump dictionary
        specifications = pump_data.get('specifications', {})
        bep_flow = specifications.get('bep_flow_m3hr', 0)
        bep_head = specifications.get('bep_head_m', 0)
        
        if bep_flow > 0 and bep_head > 0:
            return {
                'has_bep_data': True,
                'bep_flow_m3hr': bep_flow,
                'bep_head_m': bep_head
            }
        else:
            return {'has_bep_data': False}
    except Exception as e:
        logger.error(f"Error in BEP analysis for Brain system: {e}")
        return {'has_bep_data': False}

# Create blueprint
reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/pump_report', methods=['POST'])
def pump_report_post():
    """Handle POST requests for pump reports."""
    try:
        pump_code = request.form.get('pump_code')
        if not pump_code:
            safe_flash('Pump code is required.', 'error')
            return redirect(url_for('main_flow.index'))

        return redirect(url_for('reports.pump_report', pump_code=pump_code))

    except Exception as e:
        logger.error(f"Error in pump_report_post: {str(e)}")
        safe_flash('An error occurred processing your request.', 'error')
        return redirect(url_for('main_flow.index'))

@reports_bp.route('/pump_report/<path:pump_code>')
def pump_report(pump_code):
    """Render pump report - supports both presentation and engineering views."""
    from urllib.parse import unquote
    pump_code = unquote(pump_code)
    logger.info(f"--- Entering pump_report for pump_code: {pump_code} ---")
    
    # Get the required flow and head from the URL for context
    flow = request.args.get('flow')
    head = request.args.get('head')
    logger.debug(f"Request args: flow={flow}, head={head}")

    # --- DEBUGGING STEP 1: Inspect the entire session ---
    try:
        # Use json.dumps for pretty printing the session dictionary
        import json
        session_contents = json.dumps(safe_session_get('suitable_pumps', []), indent=2)
        logger.debug(f"Contents of session['suitable_pumps']:\n{session_contents}")
    except Exception as e:
        logger.error(f"Could not serialize session for debugging: {e}")
        logger.debug(f"Raw session content: {safe_session_get('suitable_pumps', [])}")

    pump_selections = safe_session_get('suitable_pumps', [])

    selected_pump = None
    if pump_selections:
        logger.debug(f"Searching for '{pump_code}' in {len(pump_selections)} pumps from session.")
        # --- DEBUGGING STEP 2: Inspect the search loop ---
        for pump in pump_selections:
            pump_code_in_session = pump.get('pump_code')
            logger.debug(f"Checking against pump in session: '{pump_code_in_session}'")
            if pump_code_in_session == pump_code:
                selected_pump = pump
                logger.info(f"SUCCESS: Found matching pump in session: '{pump_code}'")
                break
    else:
        logger.warning("Session 'suitable_pumps' is empty or not found.")

    # Check if this is a direct search request
    direct_search = request.args.get('direct_search', type=str) == 'true'
    
    if not selected_pump:
        if direct_search:
            logger.info(f"Direct search requested for pump '{pump_code}', bypassing session lookup.")
            # Try to find pump directly in catalog engine
            try:
                # CATALOG ENGINE RETIRED - USING BRAIN SYSTEM
                # from ..catalog_engine import get_catalog_engine
                from ..pump_brain import get_pump_brain
                brain = get_pump_brain()
                
                # Find the pump using Brain repository
                found_pump = brain.repository.get_pump_by_code(pump_code)
                
                if found_pump:
                    logger.info(f"Found pump '{pump_code}' in catalog for direct search.")
                    # Create a basic pump selection result for the found pump
                    selected_pump = {
                        'pump_code': found_pump.pump_code,
                        'pump_type': found_pump.pump_type,
                        'manufacturer': found_pump.manufacturer,
                        'model_series': found_pump.model_series,
                        'flow_m3hr': float(flow) if flow else 25.0,
                        'head_m': float(head) if head else 45.0,
                        'efficiency_pct': 75.0,  # Default, will be calculated
                        'power_kw': 50.0,  # Default, will be calculated
                        'npshr_m': 5.0,  # Default
                        'suitability_score': 85.0,  # Default for direct search
                        'qbep_percentage': 100.0,  # Default
                        'trim_percent': 100.0,  # Default, full impeller
                        'impeller_diameter_mm': 450.0,  # Default
                        'extrapolated': False
                    }
                    
                    # Try to get actual performance data for the operating point
                    try:
                        performance_result = found_pump.find_best_solution_for_duty(
                            float(flow) if flow else 25.0, 
                            float(head) if head else 45.0
                        )
                        
                        if performance_result:
                            selected_pump.update({
                                'efficiency_pct': performance_result.get('efficiency_pct', 75.0),
                                'power_kw': performance_result.get('power_kw', 50.0),
                                'npshr_m': performance_result.get('npshr_m', 5.0),
                                'qbep_percentage': performance_result.get('qbep_percentage', 100.0),
                                'trim_percent': performance_result.get('trim_percent', 100.0),
                                'impeller_diameter_mm': performance_result.get('impeller_diameter_mm', 450.0),
                                'extrapolated': performance_result.get('extrapolated', False)
                            })
                            logger.info(f"Updated pump performance data from analysis.")
                    except Exception as perf_error:
                        logger.warning(f"Could not analyze performance for direct search: {perf_error}")
                        # Keep default values
                        
                else:
                    logger.warning(f"Pump '{pump_code}' not found in catalog for direct search.")
                    safe_flash(f"Pump '{pump_code}' was not found in the database.", "error")
                    return redirect(url_for('main_flow.index', flow=flow, head=head))
                    
            except Exception as e:
                logger.error(f"Error during direct search: {e}")
                safe_flash("An error occurred while searching for the pump.", "error")
                return redirect(url_for('main_flow.index', flow=flow, head=head))
        else:
            logger.warning(f"Could not find pump '{pump_code}' in session. Redirecting to start.")
            safe_flash("Your session has expired or the pump was not found. Please run a new pump selection.", "warning")
            return redirect(url_for('main_flow.index', flow=flow, head=head))

    # If we get here, the pump was found successfully.
    logger.info(f"Proceeding to render report for '{selected_pump.get('pump_code')}'")
    
    # Get additional session data
    exclusion_summary = safe_session_get('exclusion_summary', {})
    site_requirements_data = safe_session_get('site_requirements', {})
    
    # DEBUG: Log what we're passing to template
    logger.info(f"DEBUG - site_requirements_data: {site_requirements_data}")
    logger.info(f"DEBUG - selected_pump keys: {list(selected_pump.keys()) if selected_pump else 'None'}")
    
    # CRITICAL: If site_requirements is empty, reconstruct from URL params for the report
    if not site_requirements_data or not site_requirements_data.get('flow_m3hr'):
        logger.warning("Site requirements missing from session, reconstructing from URL params")
        site_requirements_data = {
            'flow_m3hr': float(flow) if flow else 25.0,
            'head_m': float(head) if head else 45.0,
            'pump_type': request.args.get('pump_type', 'General'),
            'application': 'Water Supply',
            'customer_name': 'Engineering Client',
            'project_name': 'Pump Selection Project',
            'fluid_type': 'Water'
        }
        logger.info(f"DEBUG - Reconstructed site_requirements: {site_requirements_data}")
    
    # Add current date for report generation
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get alternative pumps (other pumps from session excluding selected one)
    alternatives = [p for p in pump_selections if p.get('pump_code') != pump_code][:2]  # Top 2 alternatives
    
    # Calculate BEP marker position for the visual indicator
    qbep_percentage = selected_pump.get('qbep_percentage', 100)
    if qbep_percentage <= 70:
        # Linear mapping from 0-70% to 0-20% position
        marker_position = (qbep_percentage / 70) * 20
    elif qbep_percentage <= 90:
        # Linear mapping from 70-90% to 20-30% position
        marker_position = 20 + ((qbep_percentage - 70) / 20) * 10
    elif qbep_percentage <= 110:
        # Linear mapping from 90-110% to 30-70% position
        marker_position = 30 + ((qbep_percentage - 90) / 20) * 40
    elif qbep_percentage <= 120:
        # Linear mapping from 110-120% to 70-80% position
        marker_position = 70 + ((qbep_percentage - 110) / 10) * 10
    else:
        # Linear mapping from 120-150% to 80-100% position
        marker_position = min(80 + ((qbep_percentage - 120) / 30) * 20, 100)
    
    # Add marker position to selected pump data
    selected_pump['marker_position'] = marker_position
    
    return render_template(
        'professional_pump_report.html',
        selected_pump=selected_pump,
        selected_pump_code=pump_code,  # Add this for template access
        alternatives=alternatives,  # Add alternatives for template
        exclusion_data=safe_session_get('exclusion_data', {}),  # Add exclusion data
        site_requirements=site_requirements_data,
        pump_code=pump_code,
        current_date=current_date
    )

@reports_bp.route('/professional_pump_report/<path:pump_code>')
def professional_pump_report(pump_code):
    """Generate professional pump report."""
    return pump_report(pump_code)

@reports_bp.route('/engineering_report/<path:pump_code>')
def engineering_report(pump_code):
    """Render engineering data sheet view of pump report."""
    from urllib.parse import unquote
    from datetime import datetime
    
    pump_code = unquote(pump_code)
    logger.info(f"Rendering engineering report for pump: {pump_code}")
    
    # Get flow and head from URL parameters (for recalculation)
    new_flow = request.args.get('flow', type=float)
    new_head = request.args.get('head', type=float)
    force_selection = request.args.get('force', type=str) == 'true'
    
    # Get data from session
    pump_selections = safe_session_get('suitable_pumps', [])
    selected_pump = None
    
    for pump in pump_selections:
        if pump.get('pump_code') == pump_code:
            selected_pump = pump.copy()  # Make a copy to avoid modifying session data
            
            # CRITICAL FIX: Ensure speed data and impeller specs are populated from database if missing
            if not selected_pump.get('test_speed_rpm') or not selected_pump.get('min_speed_rpm') or not selected_pump.get('min_impeller_mm'):
                # CATALOG ENGINE RETIRED - USING BRAIN SYSTEM
                # from ..catalog_engine import get_catalog_engine
                from ..pump_brain import get_pump_brain
                brain = get_pump_brain()
                target_pump = brain.repository.get_pump_by_code(pump_code)
                
                if target_pump:
                    # Add missing speed data from authentic database values - Brain repository returns dictionaries
                    specifications = target_pump.get('specifications', {})
                    selected_pump['speed_rpm'] = specifications.get('test_speed_rpm', 0)
                    selected_pump['test_speed_rpm'] = specifications.get('test_speed_rpm', 0)
                    selected_pump['min_speed_rpm'] = specifications.get('min_speed_rpm', 0)
                    selected_pump['max_speed_rpm'] = specifications.get('max_speed_rpm', 0)
                    # Add missing impeller specifications from authentic database values
                    selected_pump['min_impeller_mm'] = specifications.get('min_impeller_mm', 0)
                    selected_pump['max_impeller_mm'] = specifications.get('max_impeller_mm', 0)
                    
                    # Debug print for 8K
                    pump_code = target_pump.get('pump_code', '')
                    if pump_code.replace(' ', '').upper() in ('8K','8K-2F','8K150-400'):
                        logger.info("REPORT 8K → min=%.1f max=%.1f oper=%.1f",
                            specifications.get('min_impeller_mm', 0), 
                            specifications.get('max_impeller_mm', 0),
                            selected_pump.get('impeller_diameter_mm', 0)
                        )
            
            break
    
    # If pump not in session but force selection is requested, load it directly
    if not selected_pump and force_selection:
        logger.info(f"Force selecting pump {pump_code} for engineering analysis")
        
        # CATALOG ENGINE RETIRED - USING BRAIN SYSTEM
        # from ..catalog_engine import get_catalog_engine
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        
        # Get pump from catalog
        target_pump = brain.repository.get_pump_by_code(pump_code)
        
        if target_pump:
            # Create minimal pump data for analysis - using AUTHENTIC database values
            # Brain system returns dictionaries - access accordingly
            specifications = target_pump.get('specifications', {})
            selected_pump = {
                'pump_code': pump_code,
                'manufacturer': target_pump.get('manufacturer', 'APE PUMPS'),
                'pump_type': target_pump.get('pump_type', 'Centrifugal'),
                'model_series': target_pump.get('model_series', ''),
                'stages': 1,  # Default
                'speed_rpm': specifications.get('test_speed_rpm', 0),  # Authentic test speed from database
                'test_speed_rpm': specifications.get('test_speed_rpm', 0),  # Explicit test speed field
                'min_speed_rpm': specifications.get('min_speed_rpm', 0),  # Authentic min speed
                'max_speed_rpm': specifications.get('max_speed_rpm', 0),  # Authentic max speed
                'bep_flow_m3hr': target_pump.get('bep_flow_m3hr', new_flow or 0),
                # CRITICAL FIX: Add authentic min/max impeller specifications
                'min_impeller_mm': specifications.get('min_impeller_mm', 0),
                'max_impeller_mm': specifications.get('max_impeller_mm', 0),
            }
            
            # Calculate performance if flow and head are provided using Brain system
            if new_flow and new_head:
                # Use Brain system to evaluate pump performance at duty point
                pump_code = target_pump.get('pump_code', '')
                evaluation_result = brain.evaluate_pump(pump_code, new_flow, new_head)
                if evaluation_result:
                    # Extract performance data from Brain evaluation result
                    performance = evaluation_result.get('performance', evaluation_result)
                    selected_pump.update({
                        'flow_m3hr': new_flow,
                        'head_m': new_head,
                        'efficiency_pct': performance.get('efficiency_pct', 0),
                        'power_kw': performance.get('power_kw', 0),
                        'npshr_m': performance.get('npshr_m', 0),
                        'trim_percent': performance.get('trim_percent', 100),
                        'impeller_diameter_mm': performance.get('impeller_diameter_mm', 0),
                        'qbep_percentage': evaluation_result.get('qbep_percentage', 100),
                        'suitability_score': evaluation_result.get('score', 0)  # Use Brain evaluation score
                    })
        else:
            logger.warning(f"Pump {pump_code} not found in catalog")
    
    if not selected_pump:
        logger.warning(f"Pump {pump_code} not found in session or catalog")
        safe_flash("Pump data not found. Please run a new selection.", "warning")
        return redirect(url_for('main_flow.index'))
    
    # Get site requirements
    site_requirements_data = safe_session_get('site_requirements', {}).copy()
    
    # If new flow/head provided, recalculate performance
    if new_flow and new_head:
        logger.info(f"Recalculating for new conditions: Flow={new_flow}, Head={new_head}")
        
        # Update site requirements with new values
        site_requirements_data['flow_m3hr'] = new_flow
        site_requirements_data['head_m'] = new_head
        
        # Recalculate pump performance at new duty point
        from ..pump_repository import PumpRepository
        
        repository = PumpRepository()
        
        # Get pump data including curves for recalculation
        pump_data = repository.get_pump_by_code(pump_code)
        pump_curves = pump_data.get('curves', []) if pump_data else []
        if pump_curves:
            # Recalculate performance at new operating point
            from ..impeller_scaling import ImpellerScalingEngine
            
            scaler = ImpellerScalingEngine()
            result = scaler.find_optimal_sizing(
                pump_curves, 
                new_flow, 
                new_head
            )
            
            if result:
                # Update selected pump with new performance data
                selected_pump['flow_m3hr'] = new_flow
                selected_pump['head_m'] = new_head
                selected_pump['efficiency_pct'] = result.get('efficiency_pct', selected_pump.get('efficiency_pct', 0))
                selected_pump['power_kw'] = result.get('power_kw', selected_pump.get('power_kw', 0))
                selected_pump['npshr_m'] = result.get('npshr_m', selected_pump.get('npshr_m', 0))
                selected_pump['trim_percent'] = result.get('trim_percent', selected_pump.get('trim_percent', 100))
                selected_pump['impeller_diameter_mm'] = result.get('impeller_diameter_mm', selected_pump.get('impeller_diameter_mm', 0))
                
                # Recalculate QBEP percentage
                bep_flow = selected_pump.get('bep_flow_m3hr', new_flow)
                selected_pump['qbep_percentage'] = (new_flow / bep_flow * 100) if bep_flow > 0 else 100
                
                logger.info(f"Recalculated performance: Efficiency={selected_pump['efficiency_pct']:.1f}%, Power={selected_pump['power_kw']:.2f}kW")
    
    current_date = datetime.now().strftime("%d %B %Y")
    
    # Get alternative pumps
    alternatives = []
    for pump in pump_selections:
        if pump.get('pump_code') != pump_code:
            alternatives.append(pump)
    
    # Add breadcrumbs for navigation
    try:
        from flask import url_for
        site_reqs = site_requirements_data or {}
        flow_val = site_reqs.get('flow_m3hr', 0)
        head_val = site_reqs.get('head_m', 0)
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index')},
            {'label': 'Results', 'url': url_for('main_flow.pump_options', flow=flow_val, head=head_val)},
            {'label': f'{pump_code} - Engineering Report', 'url': '#'}
        ]
    except Exception as e:
        logger.warning(f"Could not generate breadcrumbs: {e}")
        breadcrumbs = []
    
    # Set up view switching functionality
    current_view = request.args.get('view', 'engineering')  # Default to engineering view
    show_view_toggle = True
    
    # Create URLs for view switching
    base_params = {
        'pump_code': pump_code,
        'flow': flow_val,
        'head': head_val
    }
    
    engineering_url = url_for('reports.engineering_report', **base_params, view='engineering')
    presentation_url = url_for('reports.pump_report', **base_params, view='presentation')
    
    return render_template(
        'engineering_pump_report.html',
        selected_pump=selected_pump,
        alternative_pumps=alternatives[:10],
        site_requirements=site_requirements_data,
        pump_code=pump_code,
        current_date=current_date,
        breadcrumbs=breadcrumbs,
        show_view_toggle=show_view_toggle,
        current_view=current_view,
        engineering_url=engineering_url,
        presentation_url=presentation_url,
        show_print=True
    )

@reports_bp.route('/generate_pdf/<path:pump_code>')
def generate_pdf(pump_code):
    """Generate PDF report using session data."""
    try:
        from urllib.parse import unquote
        pump_code = unquote(pump_code)
        
        # Get data from session as single source of truth
        pump_selections = safe_session_get('suitable_pumps', [])
        selected_pump = None
        
        for pump in pump_selections:
            if pump.get('pump_code') == pump_code:
                selected_pump = pump
                break
                
        if not selected_pump:
            safe_flash('Pump data not found. Please run a new selection.', 'error')
            return redirect(url_for('main_flow.index'))
            
        # PDF generation temporarily disabled - redirect to HTML report
        safe_flash('PDF generation is currently unavailable. Please use the HTML report.', 'info')
        return redirect(url_for('reports.pump_report', pump_code=pump_code))
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        safe_flash('Error generating PDF report.', 'error')
        return redirect(url_for('reports.pump_report', pump_code=pump_code))