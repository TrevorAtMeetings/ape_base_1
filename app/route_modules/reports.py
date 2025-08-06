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
    """Display comprehensive pump selection report using session data as single source of truth."""
    try:
        from urllib.parse import unquote
        pump_code = unquote(pump_code)
        
        # Get the required flow and head from the URL for context
        flow = request.args.get('flow')
        head = request.args.get('head')

        # DEBUG: Log entire session contents at function start
        from flask import session as flask_session
        logger.debug(f"=== SESSION DEBUG START ===")
        logger.debug(f"Full session keys: {list(flask_session.keys())}")
        logger.debug(f"Session size: {len(flask_session)}")
        
        # Get the TRUE results from the session
        pump_selections = safe_session_get('pump_selections', [])
        
        # DEBUG: Log pump selections data
        logger.debug(f"Retrieved pump_selections type: {type(pump_selections)}")
        logger.debug(f"Retrieved pump_selections length: {len(pump_selections) if isinstance(pump_selections, list) else 'NOT A LIST'}")
        logger.debug(f"Looking for pump_code: '{pump_code}'")

        selected_pump = None
        for i, pump in enumerate(pump_selections):
            pump_code_in_data = pump.get('pump_code') if isinstance(pump, dict) else 'NOT_DICT'
            logger.debug(f"Checking pump #{i}: '{pump_code_in_data}' == '{pump_code}' ? {pump_code_in_data == pump_code}")
            if pump.get('pump_code') == pump_code:
                selected_pump = pump
                logger.debug(f"MATCH FOUND at index {i}!")
                break
        
        logger.debug(f"Final result: selected_pump = {'FOUND' if selected_pump else 'NOT FOUND'}")
        logger.debug(f"=== SESSION DEBUG END ===")

        # NEW, SIMPLIFIED LOGIC
        if not selected_pump:
            # If the pump is not in the session, the session is invalid.
            # DO NOT recalculate. Redirect to the start.
            safe_flash("Your session has expired. Please run a new pump selection.", "warning")
            return redirect(url_for('main_flow.index', flow=flow, head=head))

        # The selected_pump object is now the SINGLE SOURCE OF TRUTH.
        # It contains the correct score and performance data calculated by the engine.
        
        # Get additional session data
        exclusion_summary = safe_session_get('exclusion_summary', {})
        site_requirements_data = safe_session_get('site_requirements', {})
        
        logger.info(f"Report display - Pump: {pump_code}, Score: {selected_pump.get('suitability_score', 'N/A')}")
        
        # Add current date for report generation
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Pass this correct object directly to the template.
        return render_template(
            'professional_pump_report.html',
            selected_pump=selected_pump,
            exclusion_summary=exclusion_summary,
            site_requirements=site_requirements_data,
            pump_code=pump_code,
            current_date=current_date
        )
    
    except Exception as e:
        logger.error(f"Error displaying pump report: {str(e)}", exc_info=True)
        safe_flash('Error loading pump report. Please try again.', 'error')
        return redirect(url_for('main_flow.index'))

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
        pump_selections = safe_session_get('pump_selections', [])
        selected_pump = None
        
        for pump in pump_selections:
            if pump.get('pump_code') == pump_code:
                selected_pump = pump
                break
                
        if not selected_pump:
            safe_flash('Pump data not found. Please run a new selection.', 'error')
            return redirect(url_for('main_flow.index'))
            
        # Use PDF generation logic with session data
        from ..pdf_generator import generate_pump_report_pdf
        return generate_pump_report_pdf(selected_pump, safe_session_get('site_requirements', {}))
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        safe_flash('Error generating PDF report.', 'error')
        return redirect(url_for('reports.pump_report', pump_code=pump_code))