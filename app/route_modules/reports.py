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