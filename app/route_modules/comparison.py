"""
Comparison Routes
Routes for pump comparison functionality
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from ..session_manager import safe_flash, safe_session_get, safe_session_set
from ..pump_engine import load_all_pump_data, validate_site_requirements, SiteRequirements
from .. import app
from flask import Response

logger = logging.getLogger(__name__)

# Create blueprint
comparison_bp = Blueprint('comparison', __name__)

@comparison_bp.route('/compare')
def pump_comparison():
    """Pump comparison interface with fallback to URL parameters if session is empty."""
    try:
        # Try to get pump selections from session
        pump_selections = safe_session_get('pump_selections', [])
        site_requirements = safe_session_get('site_requirements', {})
        
        logger.info(f"Comparison route - Session pump_selections: {len(pump_selections) if pump_selections else 0}")
        logger.info(f"Comparison route - Session site_requirements: {site_requirements}")

        # Add lifecycle costs to existing pump selections if missing
        if pump_selections and not pump_selections[0].get('lifecycle_cost'):
            flow = site_requirements.get('flow_m3hr', 100)
            for selection in pump_selections:
                performance = selection.get('operating_point', {})
                power_kw = performance.get('power_kw', 0)
                efficiency_pct = performance.get('efficiency_pct', 0)
                
                # Map performance data to template expectations
                mapped_performance = {
                    'achieved_efficiency_pct': efficiency_pct,
                    'achieved_head_m': performance.get('head_m', 0),
                    'achieved_power_kw': power_kw,
                    'achieved_flow_m3hr': performance.get('flow_m3hr', 0),
                    'efficiency_pct': efficiency_pct,
                    'head_m': performance.get('head_m', 0),
                    'power_kw': power_kw,
                    'flow_m3hr': performance.get('flow_m3hr', 0),
                    'impeller_diameter_mm': performance.get('impeller_diameter_mm', 0),
                    'test_speed_rpm': performance.get('test_speed_rpm', 0)
                }
                
                # Basic lifecycle cost calculation
                annual_hours = 8760  # 24/7 operation
                electricity_rate = 2.50  # R/kWh (typical industrial rate)
                annual_energy_cost = (power_kw * annual_hours * electricity_rate) / 1000  # Convert to thousands
                initial_cost = 50000  # Estimated initial cost in R
                total_10_year_cost = initial_cost + (annual_energy_cost * 10)
                cost_per_m3 = (annual_energy_cost * 1000) / (flow * 8760) if flow > 0 else 0
                
                lifecycle_cost = {
                    'initial_cost': initial_cost,
                    'annual_energy_cost': annual_energy_cost * 1000,  # Convert back to R
                    'total_10_year_cost': total_10_year_cost,
                    'cost_per_m3': cost_per_m3
                }
                selection['operating_point'] = mapped_performance
                selection['lifecycle_cost'] = lifecycle_cost

        # If session is empty, reconstruct from URL parameters
        if not pump_selections:
            flow = request.args.get('flow', type=float)
            head = request.args.get('head', type=float)
            pump_type = request.args.get('pump_type', 'General')
            if flow and head:
                from ..catalog_engine import get_catalog_engine
                catalog_engine = get_catalog_engine()
                top_selections = catalog_engine.select_pumps(flow, head, max_results=10, pump_type=pump_type)
                pump_selections = []
                for selection in top_selections:
                    pump = selection['pump']
                    performance = selection['performance']
                    
                    # Calculate lifecycle costs
                    power_kw = performance.get('power_kw', 0)
                    efficiency_pct = performance.get('efficiency_pct', 0)
                    
                    # Map performance data to template expectations
                    mapped_performance = {
                        'achieved_efficiency_pct': efficiency_pct,
                        'achieved_head_m': performance.get('head_m', 0),
                        'achieved_power_kw': power_kw,
                        'achieved_flow_m3hr': performance.get('flow_m3hr', 0),
                        'efficiency_pct': efficiency_pct,
                        'head_m': performance.get('head_m', 0),
                        'power_kw': power_kw,
                        'flow_m3hr': performance.get('flow_m3hr', 0),
                        'impeller_diameter_mm': performance.get('impeller_diameter_mm', 0),
                        'test_speed_rpm': performance.get('test_speed_rpm', 0)
                    }
                    
                    # Basic lifecycle cost calculation
                    annual_hours = 8760  # 24/7 operation
                    electricity_rate = 2.50  # R/kWh (typical industrial rate)
                    annual_energy_cost = (power_kw * annual_hours * electricity_rate) / 1000  # Convert to thousands
                    initial_cost = 50000  # Estimated initial cost in R
                    total_10_year_cost = initial_cost + (annual_energy_cost * 10)
                    cost_per_m3 = (annual_energy_cost * 1000) / (flow * 8760) if flow > 0 else 0
                    
                    lifecycle_cost = {
                        'initial_cost': initial_cost,
                        'annual_energy_cost': annual_energy_cost * 1000,  # Convert back to R
                        'total_10_year_cost': total_10_year_cost,
                        'cost_per_m3': cost_per_m3
                    }
                    
                    evaluation = {
                        'pump_code': pump.pump_code,
                        'overall_score': selection.get('suitability_score', 0),
                        'selection_reason': f"Efficiency: {efficiency_pct:.1f}%, Head error: {selection.get('head_error_pct', 0):.1f}%",
                        'operating_point': mapped_performance,
                        'pump_info': {
                            'manufacturer': pump.manufacturer,
                            'model_series': pump.model_series,
                            'pump_type': pump.pump_type
                        },
                        'curve_index': 0,
                        'suitable': selection.get('suitability_score', 0) > 50,
                        'lifecycle_cost': lifecycle_cost
                    }
                    pump_selections.append(evaluation)
                site_requirements = {
                    'flow_m3hr': flow,
                    'head_m': head,
                    'pump_type': pump_type
                }

        if not pump_selections:
            safe_flash('No pump selections available for comparison. Please run pump selection first.', 'info')
            return redirect(url_for('main_flow.index'))

        return render_template('pump_comparison.html',
                             pump_comparisons=pump_selections,
                             site_requirements=site_requirements)
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
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        pump = catalog_engine.get_pump_by_code(pump_code)
        
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
        
        performance = pump.get_performance_at_duty(flow, head)
        
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
        return jsonify({'error': 'Failed to load pump details'}), 500

@comparison_bp.route('/shortlist_comparison')
def shortlist_comparison():
    """Display side-by-side comparison of selected pumps"""
    try:
        pump_codes = request.args.getlist('pumps')
        if len(pump_codes) < 2 or len(pump_codes) > 3:
            safe_flash('Please select 2-3 pumps for shortlist comparison', 'error')
            return redirect(url_for('comparison.pump_comparison'))
            
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)
        
        if not flow or not head:
            safe_flash('Flow and head parameters are required for shortlist comparison', 'error')
            return redirect(url_for('comparison.pump_comparison'))
        
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        
        shortlist_pumps = []
        for pump_code in pump_codes:
            pump = catalog_engine.get_pump_by_code(pump_code)
            if pump:
                performance = pump.get_performance_at_duty(flow, head)
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
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        
        comparison_data = []
        for pump_code in pump_codes[:5]:  # Top 5 pumps
            if not pump_code.strip():
                continue
                
            catalog_pump = catalog_engine.get_pump_by_code(pump_code.strip())
            
            if catalog_pump:
                performance = catalog_pump.get_performance_at_duty(flow, head)
                
                if performance:
                    comparison_data.append({
                        'pump_code': pump_code.strip(),
                        'manufacturer': catalog_pump.manufacturer,
                        'model_series': catalog_pump.model_series,
                        'overall_score': performance.get('efficiency_pct', 0),
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
        main_pump = catalog_engine.get_pump_by_code(pump_codes[0]) if pump_codes else None

        if main_evaluation and main_pump:
            # Convert catalog pump to legacy format for PDF compatibility
            from ..catalog_engine import convert_catalog_pump_to_legacy_format
            main_performance = main_pump.get_performance_at_duty(flow, head)
            if main_performance is not None:
                legacy_pump = convert_catalog_pump_to_legacy_format(main_pump, main_performance)
            else:
                # Create a minimal legacy pump object if performance is not available
                legacy_pump = type('LegacyPumpData', (), {
                    'pPumpCode': pump_codes[0],
                    'pSuppName': 'APE PUMPS',
                    'pBEPFlo': flow,
                    'pBEPHed': head,
                    'pBEPEff': 80.0,
                    'pKWMax': 50.0
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