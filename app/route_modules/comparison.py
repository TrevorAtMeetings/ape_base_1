"""
Comparison Routes
Routes for pump comparison functionality
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from ..session_manager import safe_flash, safe_session_get, safe_session_set
from ..data_models import SiteRequirements
from ..pump_brain import get_pump_brain
from ..utils import validate_site_requirements
from .. import app
from flask import Response

logger = logging.getLogger(__name__)

# Create blueprint
comparison_bp = Blueprint('comparison', __name__)

@comparison_bp.route('/compare')
def pump_comparison():
    """Brain-only pump comparison - evaluates fresh on every page load."""
    try:
        # Get pump identifiers from session - minimal data only
        comparison_identifiers = session.get('comparison_list', [])
        
        logger.info(f"Comparison page - Found {len(comparison_identifiers)} pumps in session")
        
        # If no pumps to compare, redirect to home with message
        if not comparison_identifiers:
            safe_flash('Please add pumps to compare from the selection results page.', 'info')
            return redirect(url_for('main_flow.index'))
        
        # Get Brain for fresh evaluations
        brain = get_pump_brain()
        if not brain:
            safe_flash('Brain system unavailable for comparison.', 'error')
            return redirect(url_for('main_flow.index'))
        
        # Evaluate each pump fresh with Brain
        evaluated_pumps = []
        for identifier in comparison_identifiers:
            try:
                pump_code = identifier['pump_code']
                flow = identifier['flow']
                head = identifier['head']
                
                logger.info(f"Evaluating {pump_code} at {flow} m³/hr, {head} m")
                
                # Get fresh Brain evaluation
                evaluation = brain.evaluate_pump(pump_code, flow, head)
                
                if evaluation and not evaluation.get('excluded'):
                    # Direct Brain data - no mapping needed
                    evaluated_pumps.append(evaluation)
                else:
                    logger.warning(f"Pump {pump_code} excluded by Brain evaluation")
                    
            except Exception as e:
                logger.error(f"Error evaluating {identifier.get('pump_code', 'unknown')}: {str(e)}")
                continue
        
        # Clean session if some pumps failed
        if len(evaluated_pumps) < len(comparison_identifiers):
            valid_identifiers = [
                {'pump_code': p['pump_code'], 'flow': p['flow_m3hr'], 'head': p['head_m']}
                for p in evaluated_pumps
            ]
            session['comparison_list'] = valid_identifiers
            session.modified = True
        
        logger.info(f"Successfully evaluated {len(evaluated_pumps)} pumps for comparison")
        
        # Calculate lifecycle costs for each pump
        for pump in evaluated_pumps:
            power_kw = pump.get('power_kw', 0)
            flow = pump.get('flow_m3hr', 0)
            annual_hours = 8760
            electricity_rate = 2.50  # R/kWh
            annual_energy_cost = power_kw * annual_hours * electricity_rate
            
            pump['lifecycle_cost'] = {
                'initial_cost': 50000,
                'annual_energy_cost': annual_energy_cost,
                'total_10_year_cost': 50000 + (annual_energy_cost * 10),
                'cost_per_m3': annual_energy_cost / (flow * annual_hours) if flow > 0 else 0
            }
        
        # Prepare site requirements from first pump's duty point
        site_requirements = {}
        if evaluated_pumps:
            site_requirements = {
                'flow_m3hr': evaluated_pumps[0].get('flow_m3hr', 0),
                'head_m': evaluated_pumps[0].get('head_m', 0)
            }
        
        # Use legacy template structure for compatibility
        pump_comparisons = []
        for pump in evaluated_pumps:
            pump_comparison = {
                'pump_code': pump.get('pump_code'),
                'suitability_score': pump.get('total_score', 0),
                'overall_score': pump.get('total_score', 0),
                'selection_reason': f"Brain Score: {pump.get('total_score', 0):.1f}%",
                'pump_type': pump.get('pump_type', 'GENERAL'),
                'operating_point': {
                    'flow_m3hr': pump.get('flow_m3hr'),
                    'head_m': pump.get('head_m'),
                    'efficiency_pct': pump.get('efficiency_pct', 0),
                    'power_kw': pump.get('power_kw', 0),
                    'achieved_efficiency_pct': pump.get('efficiency_pct', 0),
                    'achieved_head_m': pump.get('head_m'),
                    'achieved_power_kw': pump.get('power_kw', 0),
                    'achieved_flow_m3hr': pump.get('flow_m3hr'),
                    'impeller_diameter_mm': pump.get('impeller_diameter_mm', 0),
                    'test_speed_rpm': pump.get('test_speed_rpm', 1450),
                    'npshr_m': pump.get('npshr_m', 0),
                    'trim_percent': pump.get('trim_percent', 100)
                },
                'pump_info': {
                    'manufacturer': 'APE PUMPS',
                    'model_series': pump.get('pump_code', '').split()[0] if pump.get('pump_code') else '',
                    'pump_type': pump.get('pump_type', 'GENERAL'),
                    'description': pump.get('description', '')
                },
                'suitable': pump.get('feasible', True),
                'lifecycle_cost': pump.get('lifecycle_cost'),
                'qbep_percentage': pump.get('qbp_percent', 100)
            }
            pump_comparisons.append(pump_comparison)
        
        return render_template('pump_comparison.html',
                             pump_comparisons=pump_comparisons,
                             site_requirements=site_requirements,
                             breadcrumbs=[])
    except Exception as e:
        logger.error(f"Error in pump_comparison: {str(e)}")
        safe_flash('Error loading comparison data.', 'error')
        return redirect(url_for('main_flow.index'))

@comparison_bp.route('/pump_comparison')
def pump_comparison_alias():
    """Alias for pump_comparison to maintain template compatibility."""
    return pump_comparison()

@comparison_bp.route('/pump_details/<path:pump_code>')
def pump_details(pump_code):
    """Get detailed pump information for modal display using Brain system - returns JSON"""
    try:
        # URL decode the pump code
        from urllib.parse import unquote
        original_pump_code = pump_code
        pump_code = unquote(pump_code)
        
        logger.info(f"Pump details request - Original: '{original_pump_code}', Decoded: '{pump_code}'")
        
        # Get duty point from parameters - require authentic values
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)
        
        logger.info(f"Duty point parameters - Flow: {flow}, Head: {head}")
        
        if not flow or not head:
            logger.error(f"Missing parameters - Flow: {flow}, Head: {head}")
            return jsonify({
                'error': 'Flow and head parameters are required',
                'message': 'Please provide valid flow and head values'
            }), 400
        
        # Use Brain system for evaluation - NO FALLBACKS
        brain = get_pump_brain()
        if not brain:
            return jsonify({'error': 'Brain system unavailable'}), 500
            
        evaluation = brain.evaluate_pump(pump_code, flow, head)
        
        if not evaluation or evaluation.get('excluded'):
            logger.error(f"No performance data for pump {pump_code} at flow={flow}, head={head}")
            return jsonify({
                'error': 'No performance data available for this duty point',
                'message': f'Pump {pump_code} cannot operate at flow={flow} m³/hr, head={head} m'
            }), 400
        
        logger.info(f"Brain evaluation completed successfully for {pump_code}")
        
        # Return Brain evaluation directly - contains all required data
        return jsonify(evaluation)
        
    except Exception as e:
        logger.error(f"Error fetching pump details for {pump_code}: {str(e)}")
        return jsonify({'error': 'Failed to load pump details'}), 50000

@comparison_bp.route('/shortlist_comparison')
def shortlist_comparison():
    """Brain-only side-by-side comparison of selected pumps"""
    try:
        pump_codes = request.args.getlist('pumps')
        if len(pump_codes) < 2 or len(pump_codes) > 10:
            safe_flash('Please select 2-10 pumps for shortlist comparison', 'error')
            return redirect(url_for('comparison.pump_comparison'))
            
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)
        
        if not flow or not head:
            safe_flash('Flow and head parameters are required for shortlist comparison', 'error')
            return redirect(url_for('comparison.pump_comparison'))
        
        # Brain-only evaluation - NO FALLBACKS
        brain = get_pump_brain()
        if not brain:
            safe_flash('Brain system unavailable for shortlist comparison', 'error')
            return redirect(url_for('comparison.pump_comparison'))
        
        shortlist_pumps = []
        for pump_code in pump_codes:
            evaluation = brain.evaluate_pump(pump_code, flow, head)
            if evaluation and not evaluation.get('excluded'):
                shortlist_pumps.append({
                    'pump_code': pump_code,
                    'evaluation': evaluation,
                    'performance': evaluation  # Alias for template compatibility
                })
        
        site_requirements = validate_site_requirements({
            'flow_m3hr': flow,
            'head_m': head,
            'application_type': request.args.get('application_type', 'water_supply'),
            'liquid_type': request.args.get('liquid_type', 'clean_water')
        })
        
        return render_template('shortlist_comparison.html',
                             shortlist_pumps=shortlist_pumps,
                             site_requirements=site_requirements.__dict__)
                             
    except Exception as e:
        logger.error(f"Error in shortlist comparison: {str(e)}")
        safe_flash('Error loading shortlist comparison', 'error')
        return redirect(url_for('comparison.pump_comparison'))

@comparison_bp.route('/generate_comparison_pdf')
def generate_comparison_pdf():
    """Generate PDF comparison report using URL parameters instead of session data."""
    try:
        # Get parameters from URL instead of session
        pump_codes = request.args.get('pumps', '').split(',')
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)
        
        if not pump_codes or not flow or not head:
            safe_flash('Pump codes, flow, and head parameters are required for PDF generation.', 'error')
            return redirect(url_for('comparison.pump_comparison'))
        
        logger.info(f"Comparison PDF generation - Pumps: {pump_codes}, Flow: {flow}, Head: {head}")
        
        # Brain-only evaluation for PDF generation
        brain = get_pump_brain()
        if not brain:
            safe_flash('Brain system unavailable for PDF generation.', 'error')
            return redirect(url_for('comparison.pump_comparison'))
        
        comparison_data = []
        for pump_code in pump_codes[:10]:  # Top 10 pumps
            if not pump_code.strip():
                continue
                
            evaluation = brain.evaluate_pump(pump_code.strip(), flow, head)
            
            if evaluation and not evaluation.get('excluded'):
                comparison_data.append({
                    'pump_code': pump_code.strip(),
                    'manufacturer': evaluation.get('manufacturer', 'APE PUMPS'),
                    'model_series': evaluation.get('model_series', ''),
                    'suitability_score': evaluation.get('suitability_score', 0),
                    'performance': evaluation,
                    'selection_reason': evaluation.get('selection_reason', 'Brain evaluation')
                })
        
        if not comparison_data:
            safe_flash('No valid pump data found for PDF generation.', 'error')
            return redirect(url_for('comparison.pump_comparison'))
        
        # Create site requirements from URL parameters
        site_requirements = SiteRequirements(
            flow_m3hr=flow,
            head_m=head,
            customer_name=request.args.get('customer_name', 'Engineering Client'),
            project_name=request.args.get('project_name', 'Pump Selection Project'),
            application_type=request.args.get('application_type', 'general')
        )
        
        # Generate PDF using pdf_generator
        from ..pdf_generator import generate_pdf_report as generate_pdf

        # Use the first pump evaluation for PDF template compatibility
        main_evaluation = comparison_data[0] if comparison_data else None

        if main_evaluation:
            # Create legacy object for PDF compatibility from Brain evaluation
            legacy_pump = type('LegacyPumpData', (), {
                'pPumpCode': main_evaluation.get('pump_code', ''),
                'pSuppName': main_evaluation.get('manufacturer', 'APE PUMPS'),
                'pBEPFlo': flow,
                'pBEPHed': head,
                'pBEPEff': main_evaluation['performance'].get('efficiency_pct', 80.0),
                'pKWMax': main_evaluation['performance'].get('power_kw', 50.0)
            })()
            
            pdf_content = generate_pdf(
                selected_pump_evaluation=main_evaluation,
                parsed_pump=legacy_pump,
                site_requirements=site_requirements,
                alternatives=comparison_data[1:] if len(comparison_data) > 1 else []
            )

            # Create response
            response = Response(pdf_content, mimetype='application/pdf')
            response.headers['Content-Disposition'] = f'attachment; filename="Pump_Comparison_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            
            return response
        else:
            safe_flash('Error generating comparison PDF', 'error')
            return redirect(url_for('comparison.pump_comparison'))
    
    except Exception as e:
        logger.error(f"Error generating comparison PDF: {str(e)}")
        safe_flash('Error generating comparison PDF.', 'error')
        return redirect(url_for('comparison.pump_comparison')) 