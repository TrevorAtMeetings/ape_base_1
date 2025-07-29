"""
Reports Routes
Routes for pump reports and PDF generation
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, make_response, Response
from ..session_manager import safe_flash, safe_session_get, safe_session_set, safe_session_pop, safe_session_clear, get_form_data, store_form_data
from ..data_models import SiteRequirements
from ..pump_repository import load_all_pump_data
from ..utils import validate_site_requirements
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
    """Display comprehensive pump selection report (modern UI)."""
    try:
        from urllib.parse import unquote
        pump_code = unquote(pump_code)

        # Get stored results from session with validation
        pump_selections = session.get('pump_selections', [])
        site_requirements_data = session.get('site_requirements', {})

        # Validate session data integrity
        if pump_selections and not isinstance(pump_selections, list):
            logger.warning("Invalid pump_selections data in session, resetting")
            pump_selections = []
        if site_requirements_data and not isinstance(site_requirements_data, dict):
            logger.warning("Invalid site_requirements data in session, resetting")
            site_requirements_data = {}

        # If no session data, regenerate from URL parameters using catalog engine
        if not pump_selections:
            flow = request.args.get('flow', type=float)
            head = request.args.get('head', type=float)
            if not flow or not head:
                safe_flash('Flow and head parameters are required for pump analysis.', 'error')
                return redirect(url_for('main_flow.index'))
            from ..catalog_engine import get_catalog_engine
            catalog_engine = get_catalog_engine()
            try:
                site_requirements_data = {
                    'flow_m3hr': flow,
                    'head_m': head,
                    'pump_type': request.args.get('pump_type', 'General'),
                    'customer_name': request.args.get('customer', ''),
                    'project_name': request.args.get('project', ''),
                }
                target_pump = catalog_engine.get_pump_by_code(pump_code)
                if target_pump:
                    performance = target_pump.get_performance_at_duty(flow, head)
                    if performance:
                        # Calculate proper suitability score to match catalog engine scoring
                        efficiency_pct = performance.get('efficiency_pct', 0)
                        efficiency_score = min(efficiency_pct, 80)  # Max 80 points for efficiency
                        bep_score = 15  # Default BEP proximity score
                        head_margin_bonus = 20 if performance.get('head_m', 0) >= head else 0
                        raw_suitability_score = efficiency_score + bep_score + head_margin_bonus
                        # Normalize to 0-100% scale (115 is the maximum possible score)
                        suitability_score = min(100.0, (raw_suitability_score / 115.0) * 100.0)

                        pump_selections = [{
                            'pump_code': pump_code,
                            'overall_score': suitability_score,
                            'efficiency_at_duty': efficiency_pct,
                            'operating_point': performance,
                            'suitable': efficiency_pct > 40,
                            'manufacturer': target_pump.manufacturer,
                            'pump_type': target_pump.pump_type,
                            'test_speed_rpm': performance.get('test_speed_rpm', 1480),
                            'stages': '1'
                        }]
                    else:
                        pump_selections = []
                else:
                    pump_selections = []
            except Exception as e:
                logger.warning(f"Catalog pump evaluation failed: {e}")
                pump_selections = []

        # Find the selected pump in results
        selected_pump = None
        for selection in pump_selections:
            if selection.get('pump_code') == pump_code:
                selected_pump = selection
                break

        # If pump not found in session data, force regenerate with specific pump
        if not selected_pump:
            flow = request.args.get('flow', 1600.0, type=float)
            head = request.args.get('head', 10.3, type=float)
            pump_type = request.args.get('pump_type', 'AXIAL_FLOW')
            from ..catalog_engine import get_catalog_engine
            catalog_engine = get_catalog_engine()
            target_pump = catalog_engine.get_pump_by_code(pump_code)
            if target_pump:
                performance = target_pump.get_performance_at_duty(flow, head)
                if performance:
                    # Calculate proper suitability score to match catalog engine scoring
                    efficiency_pct = performance.get('efficiency_pct', 0)
                    efficiency_score = min(efficiency_pct, 80)  # Max 80 points for efficiency
                    bep_score = 15  # Default BEP proximity score
                    head_margin_bonus = 20 if performance.get('head_m', 0) >= head else 0
                    raw_suitability_score = efficiency_score + bep_score + head_margin_bonus
                    # Normalize to 0-100% scale (115 is the maximum possible score)
                    suitability_score = min(100.0, (raw_suitability_score / 115.0) * 100.0)

                    selected_pump = {
                        'pump_code': pump_code,
                        'overall_score': suitability_score,
                        'efficiency_at_duty': efficiency_pct,
                        'operating_point': performance,
                        'suitable': efficiency_pct > 40,
                        'manufacturer': target_pump.manufacturer,
                        'pump_type': target_pump.pump_type,
                        'test_speed_rpm': performance.get('test_speed_rpm', 1480),
                        'stages': '1'
                    }
                    site_requirements_data = {
                        'flow_m3hr': flow,
                        'head_m': head,
                        'pump_type': pump_type
                    }
                    pump_selections = [selected_pump]

        if not selected_pump:
            safe_flash('Selected pump not found or cannot meet requirements. Please start a new selection.', 'warning')
            return redirect(url_for('main_flow.index'))

        logger.info(f"Displaying report for pump: {pump_code}")

        # Get complete pump data with curves for data table
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        catalog_pump = catalog_engine.get_pump_by_code(pump_code)
        if catalog_pump:
            selected_pump['curves'] = catalog_pump.curves
            selected_pump['pump_type'] = catalog_pump.pump_type
            selected_pump['manufacturer'] = catalog_pump.manufacturer

        # Generate alternative pumps using catalog engine
        alternatives = []
        try:
            flow = site_requirements_data.get('flow_m3hr', 0)
            head = site_requirements_data.get('head_m', 0)
            pump_type = site_requirements_data.get('pump_type', 'General')
            direct_search = request.args.get('direct_search', 'false').lower() == 'true'

            if flow and head:
                from ..catalog_engine import get_catalog_engine
                catalog_engine = get_catalog_engine()

                # Handle direct pump search
                if direct_search:
                    # Find the specific pump by code (case-insensitive)
                    target_pump = None
                    search_code = pump_code.lower().strip()

                    for pump in catalog_engine.pumps:
                        pump_code_lower = pump.pump_code.lower().strip()
                        # Try exact match first, then partial match
                        if pump_code_lower == search_code or search_code in pump_code_lower:
                            target_pump = pump
                            break

                    # If still not found, try more flexible matching
                    if not target_pump:
                        for pump in catalog_engine.pumps:
                            pump_code_lower = pump.pump_code.lower().strip()
                            # Remove common separators and spaces for matching
                            normalized_search = search_code.replace('/', '').replace('-', '').replace(' ', '')
                            normalized_pump = pump_code_lower.replace('/', '').replace('-', '').replace(' ', '')
                            if normalized_search in normalized_pump or normalized_pump in normalized_search:
                                target_pump = pump
                                break

                    if not target_pump:
                        logger.warning(f"Direct search failed for pump code: '{pump_code}'. Available pumps: {[p.pump_code for p in catalog_engine.pumps[:10]]}")
                        safe_flash(f'Pump "{pump_code}" not found in database. Please check the model name and try again.', 'error')
                        return redirect(url_for('main_flow.index'))

                    # Calculate performance for the direct search pump
                    try:
                        performance_result = target_pump.get_performance_at_duty(flow, head)

                        if performance_result and not performance_result.get('error'):
                            operating_point = performance_result
                            suitable_pumps = [target_pump]
                            logger.info(f"Direct search successful for pump: {pump_code}")
                        else:
                            logger.error(f"Performance calculation failed for pump: {pump_code}")
                            safe_flash(f'Error calculating performance for pump "{pump_code}".', 'error')
                            return redirect(url_for('main_flow.index'))

                    except Exception as e:
                        logger.error(f"Error calculating performance for direct search pump {pump_code}: {str(e)}")
                        safe_flash(f'Error calculating performance for pump "{pump_code}".', 'error')
                        return redirect(url_for('main_flow.index'))
                else:
                    # Normal pump selection process
                    alternative_selections = catalog_engine.select_pumps(
                        flow_m3hr=flow,
                        head_m=head,
                        max_results=5,
                        pump_type=pump_type
                    )

                    # Filter out the selected pump and create alternative data
                    for alt_pump in alternative_selections:
                        if alt_pump.get('pump_code') != pump_code:
                            # Normalize alternative pump score to 0-100% scale
                            raw_alt_score = alt_pump.get('overall_score', 0)
                            normalized_alt_score = min(100.0, (raw_alt_score / 115.0) * 100.0)

                            alternatives.append({
                                'pump_code': alt_pump.get('pump_code'),
                                'overall_score': normalized_alt_score,
                                'efficiency_at_duty': alt_pump.get('efficiency_pct', 0),
                                'operating_point': alt_pump.get('operating_point', {}),
                                'suitable': alt_pump.get('efficiency_pct', 0) > 40,
                                'manufacturer': alt_pump.get('manufacturer', 'APE PUMPS'),
                                'pump_type': alt_pump.get('pump_type', 'Centrifugal'),
                                'test_speed_rpm': alt_pump.get('test_speed_rpm', 1480),
                                'stages': '1'
                            })

                            # Limit to 3 alternatives
                            if len(alternatives) >= 3:
                                break
        except Exception as e:
            logger.warning(f"Failed to generate alternatives: {e}")
            alternatives = []

        context_data = {
            'pump_selections': pump_selections,
            'selected_pump': selected_pump,
            'alternatives': alternatives,
            'site_requirements': {
                'flow_m3hr': site_requirements_data.get('flow_m3hr', 0),
                'head_m': site_requirements_data.get('head_m', 0),
                'pump_type': site_requirements_data.get('pump_type', 'General'),
                'customer_name': site_requirements_data.get('customer_name', 'Client Contact'),
                'project_name': site_requirements_data.get('project_name', 'Water Supply System Project'),
                'application': site_requirements_data.get('application', 'Water Supply'),
                'fluid_type': site_requirements_data.get('fluid_type', 'Water')
            },
            'selected_pump_code': pump_code,
            'current_date': __import__('datetime').datetime.now().strftime('%Y-%m-%d')
        }

        # Ensure selected_curve data is available for all pumps
        if selected_pump and isinstance(selected_pump, dict):
            op_point = selected_pump.get('operating_point', {})
            impeller_diameter = op_point.get('impeller_diameter_mm', op_point.get('impeller_size', 501.0))
            selected_pump['selected_curve'] = {
                'impeller_size': impeller_diameter,
                'impeller_diameter_mm': impeller_diameter,
                'is_selected': True,
                'curve_index': op_point.get('curve_index', 0)
            }
            if 'pump_info' not in selected_pump:
                selected_pump['pump_info'] = {
                    'pPumpCode': pump_code,
                    'pSuppName': 'APE PUMPS',
                    'pPumpTestSpeed': '1480',
                    'pFilter1': 'APE PUMPS',
                    'pStages': '1'
                }
            logger.info(f"Template data - selected_pump operating_point: {selected_pump.get('operating_point')}")
            logger.info(f"Template data - selected_pump selected_curve: {selected_pump.get('selected_curve')}")



        return render_template('professional_pump_report.html', **context_data)

    except Exception as e:
        logger.error(f"Error displaying pump report: {str(e)}", exc_info=True)
        safe_flash('Error loading pump report. Please try again.', 'error')
        return redirect(url_for('main_flow.index'))

@reports_bp.route('/professional_pump_report/<path:pump_code>')
def professional_pump_report(pump_code):
    """Generate professional pump report."""
    return pump_report(pump_code)

@reports_bp.route('/generate_pdf/<path:pump_code>')
def generate_pdf(pump_code):  # Renamed to match template usage
    """Generate PDF report using URL parameters instead of session data"""
    try:
        # URL decode the pump code to handle special characters
        from urllib.parse import unquote
        pump_code = unquote(pump_code)

        logger.info(f"PDF generation requested for pump: {pump_code}")

        # Get parameters from URL instead of session
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)

        if not flow or not head:
            logger.error(f"PDF generation - Missing flow or head parameters")
            safe_flash('Flow and head parameters are required for PDF generation.', 'error')
            return redirect(url_for('main_flow.index'))

        logger.info(f"PDF generation - Parameters: flow={flow}, head={head}")

        # Get catalog pump and calculate performance
        from ..catalog_engine import get_catalog_engine, convert_catalog_pump_to_legacy_format
        catalog_engine = get_catalog_engine()
        catalog_pump = catalog_engine.get_pump_by_code(pump_code)

        if not catalog_pump:
            logger.error(f"PDF generation - Catalog pump {pump_code} not found")
            safe_flash('Pump not found in catalog', 'error')
            return redirect(url_for('main_flow.index'))

        # Calculate performance at duty point
        performance = catalog_pump.get_performance_at_duty(flow, head)

        if not performance:
            logger.error(f"PDF generation - No performance data for {pump_code} at flow={flow}, head={head}")
            safe_flash(f'Pump {pump_code} cannot operate at flow={flow} m³/hr, head={head} m', 'error')
            return redirect(url_for('main_flow.index'))

        logger.info(f"PDF generation - Performance calculated: efficiency={performance.get('efficiency_pct')}%, power={performance.get('power_kw')}kW")

        # Create site requirements from URL parameters
        site_requirements = SiteRequirements(
            flow_m3hr=flow,
            head_m=head,
            customer_name=request.args.get('customer_name', 'Engineering Client'),
            project_name=request.args.get('project_name', 'Pump Selection Project'),
            application_type=request.args.get('application_type', 'general')
        )

        # Convert performance data to PDF template format
        operating_point = {
            'flow_m3hr': flow,
            'head_m': head,
            'achieved_head_m': performance.get('head_m', head),
            'efficiency_pct': performance.get('efficiency_pct', 0),
            'achieved_efficiency_pct': performance.get('efficiency_pct', 0),
            'power_kw': performance.get('power_kw', 0),
            'achieved_power_kw': performance.get('power_kw', 0),
            'npshr_m': performance.get('npshr_m', 0),
            'impeller_diameter_mm': performance.get('impeller_diameter_mm', 0),
            'impeller_size': performance.get('impeller_diameter_mm', 0),
            'test_speed_rpm': performance.get('test_speed_rpm', 1480)
        }

        # Create evaluation data for PDF
        evaluation = {
            'pump_code': pump_code,
            'overall_score': performance.get('efficiency_pct', 0),
            'selection_reason': f"Efficiency: {performance.get('efficiency_pct', 0):.1f}%, Operating at duty point",
            'operating_point': operating_point,
            'pump_info': {
                'manufacturer': catalog_pump.manufacturer,
                'model_series': catalog_pump.model_series,
                'pump_type': catalog_pump.pump_type
            },
            'curve_index': 0,
            'suitable': performance.get('efficiency_pct', 0) > 40
        }

        # Convert to legacy format for PDF compatibility
        legacy_pump = convert_catalog_pump_to_legacy_format(catalog_pump, performance)

        logger.info(f"PDF generation - Legacy pump converted, generating PDF")

        # Generate PDF using the calculated data
        from ..pdf_generator import generate_pdf_report as generate_pdf
        pdf_content = generate_pdf(
            selected_pump_evaluation=evaluation,
            parsed_pump=legacy_pump,
            site_requirements=site_requirements,
            alternatives=[]  # No alternatives in stateless mode
        )

        # Create response
        response = Response(pdf_content, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename="APE_Pump_Report_{pump_code.replace("/", "_").replace(" ", "_")}.pdf"'
        response.headers['Content-Length'] = len(pdf_content)

        return response

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        safe_flash('Error generating PDF report. Please try again.', 'error')
        return redirect(url_for('main_flow.index'))

@reports_bp.route('/generate_pdf', methods=['POST'])
def generate_pdf_post():  # Renamed to be more descriptive
    """API endpoint for PDF report generation."""
    try:
        data = request.get_json() if request.is_json else {}

        if not data:
            return jsonify({'error': 'No pump data provided'}), 400

        pump_code = data.get('pump_code')
        flow_rate = data.get('flow_rate')
        head = data.get('head')

        if not all([pump_code, flow_rate, head]):
            return jsonify({'error': 'Missing required parameters: pump_code, flow_rate, head'}), 400

        # Use catalog_engine directly instead of legacy pump_engine
        from ..catalog_engine import get_catalog_engine, convert_catalog_pump_to_legacy_format
        catalog_engine = get_catalog_engine()

        if not pump_code:
            return jsonify({'error': 'Pump code is required'}), 400

        catalog_pump = catalog_engine.get_pump_by_code(str(pump_code))

        if not catalog_pump:
            return jsonify({'error': f'Pump {pump_code} not found'}), 404

        # Validate and convert parameters with safe fallbacks
        try:
            flow_val = float(flow_rate) if flow_rate is not None else 100.0
            head_val = float(head) if head is not None else 20.0
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid flow_rate or head parameters'}), 400

        site_requirements = SiteRequirements(
            flow_m3hr=flow_val,
            head_m=head_val,
            application="API Request",
            fluid_type="clean_water",
            temperature=20.0,
            viscosity=1.0,
            density=1000.0,
            npsh_available=10.0,
            installation="standard"
        )

        # Get performance at duty point
        performance = catalog_pump.get_performance_at_duty(flow_val, head_val)

        if not performance:
            return jsonify({'error': f'Pump {pump_code} cannot operate at flow={flow_val} m³/hr, head={head_val} m'}), 400

        # Create evaluation data
        evaluation = {
            'pump_code': pump_code,
            'overall_score': performance.get('efficiency_pct', 0),
            'selection_reason': f"Efficiency: {performance.get('efficiency_pct', 0):.1f}%, Operating at duty point",
            'operating_point': performance,
            'pump_info': {
                'manufacturer': catalog_pump.manufacturer,
                'model_series': catalog_pump.model_series,
                'pump_type': catalog_pump.pump_type
            },
            'curve_index': 0,
            'suitable': performance.get('efficiency_pct', 0) > 40
        }

        # Convert to legacy format for PDF compatibility
        legacy_pump = convert_catalog_pump_to_legacy_format(catalog_pump, performance)

        from ..pdf_generator import generate_pdf_report
        pdf_content = generate_pdf_report(evaluation, legacy_pump, site_requirements)

        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        safe_pump_code = str(pump_code).replace("/", "_") if pump_code else "unknown"
        response.headers['Content-Disposition'] = f'attachment; filename="pump_report_{safe_pump_code}.pdf"'

        return response

    except Exception as e:
        logger.error(f"Error in PDF generation API: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500