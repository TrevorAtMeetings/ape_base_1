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

    if not selected_pump:
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
            
            # CRITICAL FIX: Ensure speed data is populated from database if missing
            if not selected_pump.get('test_speed_rpm') or not selected_pump.get('min_speed_rpm'):
                from ..catalog_engine import get_catalog_engine
                catalog_engine = get_catalog_engine()
                target_pump = catalog_engine.get_pump_by_code(pump_code)
                
                if target_pump:
                    # Add missing speed data from authentic database values
                    selected_pump['speed_rpm'] = target_pump.get_speed_rpm()
                    selected_pump['test_speed_rpm'] = target_pump.get_speed_rpm()
                    selected_pump['min_speed_rpm'] = target_pump.get_min_speed_rpm()
                    selected_pump['max_speed_rpm'] = target_pump.get_max_speed_rpm()
            
            break
    
    # If pump not in session but force selection is requested, load it directly
    if not selected_pump and force_selection:
        logger.info(f"Force selecting pump {pump_code} for engineering analysis")
        
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        
        # Get pump from catalog
        target_pump = catalog_engine.get_pump_by_code(pump_code)
        
        if target_pump:
            # Create minimal pump data for analysis - using AUTHENTIC database values
            selected_pump = {
                'pump_code': pump_code,
                'manufacturer': target_pump.manufacturer or 'APE PUMPS',
                'pump_type': target_pump.pump_type or 'Centrifugal',
                'model_series': target_pump.model_series,
                'stages': 1,  # Default
                'speed_rpm': target_pump.get_speed_rpm(),  # Authentic test speed from database
                'test_speed_rpm': target_pump.get_speed_rpm(),  # Explicit test speed field
                'min_speed_rpm': target_pump.get_min_speed_rpm(),  # Authentic min speed
                'max_speed_rpm': target_pump.get_max_speed_rpm(),  # Authentic max speed
                'bep_flow_m3hr': target_pump.bep_flow_m3hr if hasattr(target_pump, 'bep_flow_m3hr') else new_flow
            }
            
            # Calculate performance if flow and head are provided
            if new_flow and new_head:
                solution = target_pump.find_best_solution_for_duty(new_flow, new_head)
                if solution:
                    selected_pump.update({
                        'flow_m3hr': new_flow,
                        'head_m': new_head,
                        'efficiency_pct': solution.get('efficiency_pct', 0),
                        'power_kw': solution.get('power_kw', 0),
                        'npshr_m': solution.get('npshr_m', 0),
                        'trim_percent': solution.get('trim_percent', 100),
                        'impeller_diameter_mm': solution.get('impeller_diameter_mm', 0),
                        'qbep_percentage': solution.get('qbep_percentage', 100),
                        'suitability_score': 0  # Force selected, no score
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
    
    return render_template(
        'engineering_pump_report.html',
        selected_pump=selected_pump,
        alternative_pumps=alternatives[:5],
        site_requirements=site_requirements_data,
        pump_code=pump_code,
        current_date=current_date
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