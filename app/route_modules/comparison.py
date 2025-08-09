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
    """Brain-only pump comparison interface - NO FALLBACKS EVER."""
    try:
        # Clean breadcrumbs for navigation
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'Pump Comparison', 'url': '#', 'icon': 'compare_arrows'}
        ]
        
        # Get pump identifiers from session (simplified - only one source)
        comparison_list = safe_session_get('comparison_list', [])
        site_requirements = safe_session_get('site_requirements', {})
        
        logger.info(f"Comparison route - Session comparison_list: {len(comparison_list) if comparison_list else 0}")
        logger.info(f"Comparison route - Session site_requirements: {site_requirements}")

        # BRAIN-ONLY LOGIC: Convert pump identifiers to full evaluations
        pump_comparisons = []
        if comparison_list:
            brain = get_pump_brain()
            if not brain:
                safe_flash('Brain system unavailable for comparison.', 'error')
                return redirect(url_for('main_flow.index'))
            
            for identifier in comparison_list:
                try:
                    pump_code = identifier['pump_code']
                    flow = identifier['flow']
                    head = identifier['head']
                    
                    # Get fresh Brain evaluation - single source of truth
                    evaluation = brain.evaluate_pump(pump_code, flow, head)
                    
                    if evaluation and not evaluation.get('excluded'):
                        # Calculate lifecycle costs from Brain data
                        power_kw = evaluation.get('power_kw', 0)
                        annual_hours = 8760  
                        electricity_rate = 2.50  # R/kWh
                        annual_energy_cost = (power_kw * annual_hours * electricity_rate) / 1000
                        initial_cost = 50000  
                        total_10_year_cost = initial_cost + (annual_energy_cost * 10)
                        cost_per_m3 = (annual_energy_cost * 1000) / (flow * 8760) if flow > 0 else 0
                        
                        lifecycle_cost = {
                            'initial_cost': initial_cost,
                            'annual_energy_cost': annual_energy_cost * 1000,
                            'total_10_year_cost': total_10_year_cost,
                            'cost_per_m3': cost_per_m3
                        }
                        
                        # Format for template compatibility
                        pump_comparison = {
                            'pump_code': pump_code,
                            'suitability_score': evaluation.get('suitability_score', 0),
                            'overall_score': evaluation.get('overall_score', 0),
                            'selection_reason': evaluation.get('selection_reason', 'Brain evaluation'),
                            'pump_type': evaluation.get('pump_type', 'GENERAL'),
                            'operating_point': evaluation,  # Brain provides complete performance data
                            'pump_info': evaluation.get('pump_info', {}),
                            'suitable': not evaluation.get('excluded', False),
                            'lifecycle_cost': lifecycle_cost,
                            'qbep_percentage': evaluation.get('flow_ratio', 1.0) * 100
                        }
                        pump_comparisons.append(pump_comparison)
                    else:
                        logger.warning(f"Pump {pump_code} excluded from comparison: {evaluation.get('exclusion_reasons', ['Unknown'])}")
                        
                except Exception as e:
                    logger.error(f"Error evaluating {identifier.get('pump_code', 'unknown')}: {str(e)}")
                    continue

        if not pump_comparisons:
            # Get parameters from URL if no session data
            flow = request.args.get('flow', type=float)
            head = request.args.get('head', type=float)
            pump_type = request.args.get('pump_type', 'GENERAL')
            
            if flow and head:
                site_requirements = {'flow_m3hr': flow, 'head_m': head, 'pump_type': pump_type}
                safe_flash('Please add pumps to comparison first by clicking "Add to Compare" on pump report pages.', 'info')
            else:
                safe_flash('No pump selections available for comparison. Please run pump selection first.', 'info')
                return redirect(url_for('main_flow.index'))

        return render_template('pump_comparison.html',
                             pump_comparisons=pump_comparisons,
                             site_requirements=site_requirements,
                             breadcrumbs=breadcrumbs)
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
    """Get detailed pump information for modal display - returns JSON"""
    try:
        # URL decode the pump code
        from urllib.parse import unquote
        original_pump_code = pump_code
        pump_code = unquote(pump_code)
        
        logger.info(f"Pump details request - Original: '{original_pump_code}', Decoded: '{pump_code}'")
        
        # Get pump data from catalog engine
        # CATALOG ENGINE RETIRED - USING BRAIN SYSTEM
        # from ..catalog_engine import get_catalog_engine
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        pump = brain.repository.get_pump_by_code(pump_code)
        
        if not pump:
            logger.error(f"Pump not found: '{pump_code}'")
            return jsonify({'error': 'Pump not found'}), 404
        
        logger.info(f"Pump found: {pump.pump_code}")
        
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
        
        performance = pump.find_best_solution_for_duty(flow, head)
        
        if not performance:
            logger.error(f"No performance data for pump {pump_code} at flow={flow}, head={head}")
            return jsonify({
                'error': 'No performance data available for this duty point',
                'message': f'Pump {pump_code} cannot operate at flow={flow} m³/hr, head={head} m'
            }), 400
        
        logger.info(f"Performance calculated successfully for {pump_code}")
        
        # Format pump details for display
        pump_details_data = {
            'pump_code': pump.pump_code,
            'manufacturer': pump.manufacturer,
            'model_series': pump.model_series,
            'description': pump.description,
            'specifications': {
                'max_flow': pump.max_flow_m3hr,
                'max_head': pump.max_head_m,
                'max_power': pump.max_power_kw,
                'connection_size': getattr(pump, 'connection_size', 'Standard'),
                'materials': getattr(pump, 'materials', 'Cast Iron')
            },
            'performance': performance,
            'curves_count': len(pump.curves),
            'operating_ranges': {
                'flow_range': f"0 - {pump.max_flow_m3hr} m³/hr",
                'head_range': f"0 - {pump.max_head_m} m",
                'efficiency_range': f"{pump.min_efficiency} - {pump.max_efficiency}%"
            }
        }
        
        logger.info(f"Returning pump details for {pump_code}")
        return jsonify(pump_details_data)
        
    except Exception as e:
        logger.error(f"Error fetching pump details for {pump_code}: {str(e)}")
        return jsonify({'error': 'Failed to load pump details'}), 50000

@comparison_bp.route('/shortlist_comparison')
def shortlist_comparison():
    """Display side-by-side comparison of selected pumps"""
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
        
        # CATALOG ENGINE RETIRED - USING BRAIN SYSTEM
        # from ..catalog_engine import get_catalog_engine
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        
        shortlist_pumps = []
        for pump_code in pump_codes:
            pump = brain.repository.get_pump_by_code(pump_code)
            if pump:
                performance = pump.find_best_solution_for_duty(flow, head)
                shortlist_pumps.append({
                    'pump': pump,
                    'performance': performance,
                    'pump_code': pump_code
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
        
        # Get detailed information for pumps
        # CATALOG ENGINE RETIRED - USING BRAIN SYSTEM
        # from ..catalog_engine import get_catalog_engine
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        
        comparison_data = []
        for pump_code in pump_codes[:10]:  # Top 10 pumps
            if not pump_code.strip():
                continue
                
            catalog_pump = brain.repository.get_pump_by_code(pump_code.strip())
            
            if catalog_pump:
                performance = catalog_pump.get_performance_at_duty(flow, head)
                
                if performance:
                    comparison_data.append({
                        'pump_code': pump_code.strip(),
                        'manufacturer': catalog_pump.manufacturer,
                        'model_series': catalog_pump.model_series,
                        'suitability_score': performance.get('efficiency_pct', 0),
                        'performance': performance,
                        'selection_reason': f"Efficiency: {performance.get('efficiency_pct', 0):.1f}%"
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

        # Use the first pump as the main selection for PDF template compatibility
        main_evaluation = comparison_data[0] if comparison_data else None
        main_pump = brain.repository.get_pump_by_code(pump_codes[0]) if pump_codes else None

        if main_evaluation and main_pump:
            # Convert catalog pump to legacy format for PDF compatibility
            # CATALOG ENGINE RETIRED - Brain system uses dictionary format directly
            # from ..catalog_engine import convert_catalog_pump_to_legacy_format
            # Brain system uses dictionary format - create legacy object for PDF compatibility
            legacy_pump = type('LegacyPumpData', (), {
                'pPumpCode': main_pump.get('pump_code', ''),
                'pSuppName': main_pump.get('manufacturer', 'APE PUMPS'),
                'pBEPFlo': flow,
                'pBEPHed': head,
                'pBEPEff': main_evaluation.get('efficiency_pct', 80.0),
                'pKWMax': main_evaluation.get('power_kw', 50.0)
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