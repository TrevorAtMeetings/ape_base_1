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

        # Get the TRUE results from the session
        pump_selections = safe_session_get('pump_selections', [])

        selected_pump = None
        for pump in pump_selections:
            if pump.get('pump_code') == pump_code:
                selected_pump = pump
                break

        if not selected_pump:
            # DIRECT PUMP GENERATION: Generate the specific pump data for this report
            logger.warning(f"Session expired for pump {pump_code}. Generating fresh data.")
            
            if flow and head:
                # Use catalog engine directly to get this specific pump
                from app.catalog_engine import CatalogEngine
                catalog_engine = CatalogEngine()
                
                # Try to get the pump by its code first
                target_pump = catalog_engine.get_pump_by_code(pump_code)
                
                if target_pump:
                    try:
                        # Generate fresh evaluation for this specific pump
                        # Run the evaluation system to get proper performance data
                        results = catalog_engine.select_pumps(
                            flow_m3hr=float(flow),
                            head_m=float(head),
                            max_results=50,  # Get enough results to ensure we find this pump
                            pump_type=request.args.get('pump_type', 'GENERAL'),
                            return_exclusions=True
                        )
                        
                        # Find our specific pump in the results
                        for pump_result in results.get('suitable_pumps', []):
                            if pump_result.get('pump_code') == pump_code:
                                selected_pump = pump_result
                                logger.info(f"Successfully generated fresh data for pump {pump_code}")
                                break
                        
                        # If not found in suitable pumps, create a basic evaluation
                        if not selected_pump:
                            # Create a basic pump evaluation for display
                            performance = target_pump.get_any_performance_point(float(flow), float(head))
                            if performance:
                                selected_pump = {
                                    'pump_code': pump_code,
                                    'manufacturer': target_pump.manufacturer,
                                    'pump_type': target_pump.pump_type,
                                    'model_series': target_pump.model_series,
                                    'specifications': target_pump.specifications,
                                    'operating_point': {
                                        'flow_m3hr': performance['flow_m3hr'],
                                        'head_m': performance['head_m'],
                                        'efficiency_pct': performance['efficiency_pct'],
                                        'power_kw': performance['power_kw'],
                                        'npshr_m': performance.get('npshr_m'),
                                        'impeller_diameter_mm': performance['impeller_diameter_mm'],
                                        'test_speed_rpm': performance['test_speed_rpm']
                                    },
                                    'overall_score': 0,  # No scoring for direct lookup
                                    'suitable': True,
                                    'curves': target_pump.curves
                                }
                                logger.info(f"Created basic evaluation for pump {pump_code}")
                            else:
                                safe_flash('Unable to generate performance data for this pump.', 'error')
                                return redirect(url_for('main_flow.index'))
                            
                    except Exception as e:
                        logger.error(f"Error generating fresh pump data: {e}")
                        safe_flash('Error generating report. Please try again.', 'error')
                        return redirect(url_for('main_flow.index'))
                else:
                    safe_flash('Pump not found in catalog.', 'error')
                    return redirect(url_for('main_flow.index'))
            else:
                safe_flash('Missing parameters. Please run a new selection.', 'warning')
                return redirect(url_for('main_flow.index'))

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