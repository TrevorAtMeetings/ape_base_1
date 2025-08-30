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
        # Check if we have URL parameters (new direct access method)
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)
        pump_type = request.args.get('pump_type', default='GENERAL')
        
        # Get pump identifiers from session - minimal data only
        comparison_identifiers = session.get('comparison_list', [])
        
        logger.info(f"Comparison page - Found {len(comparison_identifiers)} pumps in session, URL params: flow={flow}, head={head}, pump_type={pump_type}")
        
        # If we have URL parameters but no session pumps, auto-select pumps for comparison
        if not comparison_identifiers and flow and head:
            logger.info("No pumps in session but have URL params - auto-selecting pumps for comparison")
            
            # Get Brain for pump selection
            brain = get_pump_brain()
            if not brain:
                safe_flash('Brain system unavailable for comparison.', 'error')
                return redirect(url_for('main_flow.index'))
            
            # Use Brain to find best pumps
            site_requirements = {
                'flow_m3hr': flow,
                'head_m': head,
                'pump_type': pump_type
            }
            
            pump_result = brain.find_best_pumps(
                site_requirements=site_requirements
            )
            
            # Extract pumps from the result - returns {'ranked_pumps': [...], 'exclusion_details': ...}
            pump_selections = []
            if pump_result and isinstance(pump_result, dict):
                # The method returns a dict with 'ranked_pumps' key
                if 'ranked_pumps' in pump_result:
                    pump_selections = pump_result['ranked_pumps'][:5]  # Take top 5
                    logger.info(f"Found {len(pump_selections)} pumps from ranked_pumps")
                    if pump_selections:
                        first_pump = pump_selections[0]
                        if isinstance(first_pump, dict):
                            logger.info(f"First pump structure (dict): keys = {list(first_pump.keys())[:10]}")
                        else:
                            logger.info(f"First pump structure (object): type = {type(first_pump)}, attrs = {dir(first_pump)[:10]}")
                else:
                    logger.warning(f"No 'ranked_pumps' key found. Keys available: {list(pump_result.keys())}")
            
            if not pump_selections:
                safe_flash('No pumps found matching the requirements.', 'info')
                return redirect(url_for('main_flow.index'))
            
            # Convert to comparison identifiers format
            comparison_identifiers = []
            for pump in pump_selections:
                # Handle different possible pump object structures
                if isinstance(pump, dict):
                    pump_code = pump.get('pump_code') or pump.get('pump', {}).get('pump_code') or pump.get('id')
                elif hasattr(pump, 'pump_code'):
                    pump_code = pump.pump_code
                elif hasattr(pump, 'pump') and hasattr(pump.pump, 'pump_code'):
                    pump_code = pump.pump.pump_code
                else:
                    logger.warning(f"Unable to extract pump_code from: {pump}")
                    continue
                    
                comparison_identifiers.append({
                    'pump_code': pump_code,
                    'flow_m3hr': flow,
                    'head_m': head,
                    'pump_type': pump_type
                })
            
            # Store in session for future use
            session['comparison_list'] = comparison_identifiers
            
            logger.info(f"Auto-selected {len(comparison_identifiers)} pumps for comparison")
            
            # Important: Continue with the comparison rather than redirect
            # This preserves the flow/head parameters in the URL
        
        # If still no pumps to compare, redirect to home with message
        elif not comparison_identifiers:
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
                # Handle both old format (flow/head) and new format (flow_m3hr/head_m)
                flow = identifier.get('flow_m3hr') or identifier.get('flow', 0)
                head = identifier.get('head_m') or identifier.get('head', 0)
                
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
            power_kw = pump.get('power_kw') or 0
            flow = pump.get('flow_m3hr') or 0
            annual_hours = 8760
            electricity_rate = 2.50  # R/kWh
            annual_energy_cost = float(power_kw) * annual_hours * electricity_rate if power_kw else 0
            
            pump['lifecycle_cost'] = {
                'initial_cost': 50000,
                'annual_energy_cost': annual_energy_cost,
                'total_10_year_cost': 50000 + (annual_energy_cost * 10),
                'cost_per_m3': annual_energy_cost / (float(flow) * annual_hours) if flow and flow > 0 else 0
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
            # Ensure all numeric values are not None
            total_score = pump.get('total_score') or 0
            flow_m3hr = pump.get('flow_m3hr') or 0
            head_m = pump.get('head_m') or 0
            efficiency_pct = pump.get('efficiency_pct') or 0
            power_kw = pump.get('power_kw') or 0
            impeller_diameter_mm = pump.get('impeller_diameter_mm') or 0
            test_speed_rpm = pump.get('test_speed_rpm') or 1450
            npshr_m = pump.get('npshr_m') or 0
            trim_percent = pump.get('trim_percent') or 100
            qbp_percent = pump.get('qbp_percent') or 100
            
            pump_comparison = {
                'pump_code': pump.get('pump_code', ''),
                'suitability_score': float(total_score),
                'overall_score': float(total_score),
                'selection_reason': f"Brain Score: {float(total_score):.1f}%",
                'pump_type': pump.get('pump_type', 'GENERAL'),
                'operating_point': {
                    'flow_m3hr': float(flow_m3hr),
                    'head_m': float(head_m),
                    'efficiency_pct': float(efficiency_pct),
                    'power_kw': float(power_kw),
                    'achieved_efficiency_pct': float(efficiency_pct),
                    'achieved_head_m': float(head_m),
                    'achieved_power_kw': float(power_kw),
                    'achieved_flow_m3hr': float(flow_m3hr),
                    'impeller_diameter_mm': float(impeller_diameter_mm),
                    'test_speed_rpm': float(test_speed_rpm),
                    'npshr_m': float(npshr_m),
                    'trim_percent': float(trim_percent)
                },
                'pump_info': {
                    'manufacturer': 'APE PUMPS',
                    'model_series': pump.get('pump_code', '').split()[0] if pump.get('pump_code') else '',
                    'pump_type': pump.get('pump_type', 'GENERAL'),
                    'description': pump.get('description', '')
                },
                'suitable': pump.get('feasible', True),
                'lifecycle_cost': pump.get('lifecycle_cost', {}),
                'qbep_percentage': float(qbp_percent)
            }
            pump_comparisons.append(pump_comparison)
        
        # Convert dictionaries to objects with attribute access for template compatibility
        class PumpComparison:
            def __init__(self, data):
                self.__dict__.update(data)
            
            def get(self, key, default=None):
                """Support dictionary-like get method for template compatibility"""
                return getattr(self, key, default)
        
        pump_comparison_objects = [PumpComparison(pump) for pump in pump_comparisons]
        
        return render_template('pump_comparison.html',
                             pump_comparisons=pump_comparison_objects,
                             site_requirements=site_requirements,
                             breadcrumbs=[])
    except Exception as e:
        import traceback
        logger.error(f"Error in pump_comparison: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        safe_flash(f'Error loading comparison data: {str(e)}', 'error')
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
        
        # Create object class for template compatibility
        class ShortlistPump:
            def __init__(self, pump_code, evaluation):
                self.pump_code = pump_code
                self.evaluation = evaluation
                self.performance = evaluation  # Alias for template compatibility
                # Add any nested attributes the template expects
                self.pump = type('obj', (object,), {
                    'pump_code': pump_code,
                    'max_flow_m3hr': evaluation.get('max_flow_m3hr', 0),
                    'max_head_m': evaluation.get('max_head_m', 0)
                })()
            
            def get(self, key, default=None):
                """Support dictionary-like get method"""
                return getattr(self, key, default)
        
        shortlist_pumps = []
        for pump_code in pump_codes:
            evaluation = brain.evaluate_pump(pump_code, flow, head)
            if evaluation and not evaluation.get('excluded'):
                shortlist_pumps.append(ShortlistPump(pump_code, evaluation))
        
        # Create simple site requirements object
        site_requirements = {
            'flow_m3hr': flow,
            'head_m': head,
            'application_type': request.args.get('application_type', 'water_supply'),
            'liquid_type': request.args.get('liquid_type', 'clean_water')
        }
        
        return render_template('shortlist_comparison.html',
                             shortlist_pumps=shortlist_pumps,
                             site_requirements=site_requirements)
                             
    except Exception as e:
        import traceback
        logger.error(f"Error in shortlist comparison: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        safe_flash(f'Error loading shortlist comparison: {str(e)}', 'error')
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


@comparison_bp.route('/api/comparison/add', methods=['POST'])
def add_to_comparison():
    """API endpoint to add a pump to the comparison session."""
    try:
        data = request.get_json()
        
        if not data or 'pump_code' not in data:
            return jsonify({
                'success': False,
                'error': 'Pump code is required'
            }), 400
        
        # Get current comparison list from session
        comparison_list = session.get('comparison_list', [])
        
        # Create pump identifier object
        pump_identifier = {
            'pump_code': data['pump_code'],
            'flow_m3hr': data.get('flow_m3hr', 0),
            'head_m': data.get('head_m', 0),
            'pump_type': data.get('pump_type', 'GENERAL')
        }
        
        # Check if pump is already in comparison list
        existing_codes = [p['pump_code'] for p in comparison_list]
        if pump_identifier['pump_code'] in existing_codes:
            return jsonify({
                'success': False,
                'error': f'Pump {pump_identifier["pump_code"]} is already in comparison list'
            }), 400
        
        # Add pump to comparison list
        comparison_list.append(pump_identifier)
        
        # Limit comparison list to 5 pumps max
        if len(comparison_list) > 5:
            comparison_list = comparison_list[-5:]
        
        # Update session
        session['comparison_list'] = comparison_list
        
        logger.info(f"Added pump {pump_identifier['pump_code']} to comparison. Total: {len(comparison_list)} pumps")
        
        return jsonify({
            'success': True,
            'message': f'Pump {pump_identifier["pump_code"]} added to comparison',
            'count': len(comparison_list),
            'pumps': [p['pump_code'] for p in comparison_list]
        })
        
    except Exception as e:
        logger.error(f"Error adding pump to comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while adding pump to comparison'
        }), 500


@comparison_bp.route('/api/comparison/remove', methods=['POST'])
def remove_from_comparison():
    """API endpoint to remove a pump from the comparison session."""
    try:
        data = request.get_json()
        
        if not data or 'pump_code' not in data:
            return jsonify({
                'success': False,
                'error': 'Pump code is required'
            }), 400
        
        # Get current comparison list from session
        comparison_list = session.get('comparison_list', [])
        
        # Remove pump from comparison list
        pump_code = data['pump_code']
        comparison_list = [p for p in comparison_list if p['pump_code'] != pump_code]
        
        # Update session
        session['comparison_list'] = comparison_list
        
        logger.info(f"Removed pump {pump_code} from comparison. Remaining: {len(comparison_list)} pumps")
        
        return jsonify({
            'success': True,
            'message': f'Pump {pump_code} removed from comparison',
            'count': len(comparison_list),
            'pumps': [p['pump_code'] for p in comparison_list]
        })
        
    except Exception as e:
        logger.error(f"Error removing pump from comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while removing pump from comparison'
        }), 500


@comparison_bp.route('/api/comparison/clear', methods=['POST'])
def clear_comparison():
    """API endpoint to clear all pumps from the comparison session."""
    try:
        session['comparison_list'] = []
        
        logger.info("Cleared comparison list")
        
        return jsonify({
            'success': True,
            'message': 'Comparison list cleared',
            'count': 0,
            'pumps': []
        })
        
    except Exception as e:
        logger.error(f"Error clearing comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while clearing comparison'
        }), 500


@comparison_bp.route('/api/comparison/status')
def comparison_status():
    """API endpoint to get current comparison status."""
    try:
        comparison_list = session.get('comparison_list', [])
        
        return jsonify({
            'success': True,
            'count': len(comparison_list),
            'pumps': [p['pump_code'] for p in comparison_list],
            'full_list': comparison_list
        })
        
    except Exception as e:
        logger.error(f"Error getting comparison status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while getting comparison status'
        }), 500 