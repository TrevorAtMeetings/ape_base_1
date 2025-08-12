import logging
from flask import (
    Blueprint, request, render_template, redirect, url_for, session, 
    send_file, jsonify, make_response
)
from urllib.parse import unquote
from datetime import datetime
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
            safe_flash("Pump code is required.", "error")
            return redirect(url_for('main_flow.index'))
        return redirect(url_for('reports.pump_report', pump_code=pump_code))
    except Exception as e:
        logger.error(f"Error in pump_report_post: {str(e)}")
        safe_flash('An error occurred while processing your request.', 'error')
        return redirect(url_for('main_flow.index'))

@reports_bp.route('/pump_report/<path:pump_code>')
def pump_report(pump_code):
    """Render pump report with presentation view."""
    pump_code = unquote(pump_code)
    
    # Get definitive duty point
    site_reqs = safe_session_get('site_requirements', {})
    flow = request.args.get('flow', type=float) or site_reqs.get('flow_m3hr')
    head = request.args.get('head', type=float) or site_reqs.get('head_m')
    
    # Clean breadcrumbs for navigation
    breadcrumbs = [
        {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
        {'label': 'Results', 'url': url_for('main_flow.pump_options', flow=flow, head=head) if flow and head else '#'},
        {'label': pump_code, 'url': '#', 'icon': 'description'}
    ]

    if not (flow and head):
        safe_flash("Flow and head are required to view a report.", "error")
        return redirect(url_for('main_flow.index'))

    # THE BRAIN IS THE SINGLE SOURCE OF TRUTH
    from ..pump_brain import get_pump_brain
    brain = get_pump_brain()
    
    # Make one definitive call to the Brain to get all necessary data
    evaluation_result = brain.evaluate_pump(pump_code, flow, head)
    
    if not evaluation_result or not evaluation_result.get('feasible'):
        safe_flash(f"Pump {pump_code} is not suitable for the duty point {flow}m³/hr @ {head}m.", "warning")
        return redirect(url_for('main_flow.index'))
        
    # The 'evaluation_result' is now the complete and final data object
    selected_pump = evaluation_result.copy()
    
    # Get alternatives from the session if they exist
    pump_selections = safe_session_get('suitable_pumps', [])
    alternatives = [p for p in pump_selections if p.get('pump_code') != pump_code][:2]
    
    # FIX: For direct searches, alternatives list is empty because main selection was skipped
    # Generate alternatives using Brain system when none exist
    if not alternatives and flow and head:
        logger.info(f"No alternatives found in session - generating via Brain for direct search")
        try:
            best_pumps_result = brain.find_best_pumps({'flow_m3hr': flow, 'head_m': head})
            if best_pumps_result and 'ranked_pumps' in best_pumps_result:
                # Get top 3 alternatives (excluding the current pump)
                brain_alternatives = []
                for pump in best_pumps_result['ranked_pumps'][:5]:  # Check top 5
                    if pump.get('pump_code') != pump_code:
                        brain_alternatives.append(pump)
                        if len(brain_alternatives) >= 2:  # Limit to 2 alternatives
                            break
                alternatives = brain_alternatives
                logger.info(f"Generated {len(alternatives)} alternatives via Brain system")
        except Exception as e:
            logger.warning(f"Could not generate alternatives via Brain: {e}")
            alternatives = []
    
    # Get comparison list from session for comparison features
    comparison_list = safe_session_get('comparison_list', [])
    
    # Template data structure
    template_data = {
        'selected_pump': selected_pump,
        'site_requirements': {'flow_m3hr': flow, 'head_m': head, 'pump_type': request.args.get('pump_type', 'GENERAL')},
        'alternatives': alternatives,
        'alternative_pumps': alternatives,  # Both names for template compatibility
        'comparison_list': comparison_list,
        'current_date': datetime.now().strftime("%d %B %Y"),
        'current_view': 'presentation',
        'show_view_toggle': True
    }
    
    return render_template('professional_pump_report.html', breadcrumbs=breadcrumbs, **template_data)

# REMOVED: Redundant route - professional_pump_report was identical to pump_report
# Users should use /pump_report directly for consistency

@reports_bp.route('/bep_proximity_report/<path:pump_code>')
def bep_proximity_report(pump_code):
    """
    Dedicated report for BEP proximity selection.
    Shows pump capabilities at BEP without strict selection constraints.
    """
    pump_code = unquote(pump_code)
    logger.info(f"BEP Proximity Report for pump: {pump_code}")
    
    # Get duty point from request
    flow = request.args.get('flow', type=float)
    head = request.args.get('head', type=float)
    
    if not (flow and head):
        safe_flash("Flow and head are required to view a report.", "error")
        return redirect(url_for('main_flow.index'))
    
    from ..pump_brain import get_pump_brain
    brain = get_pump_brain()
    
    # Get pump data without strict evaluation
    pump_data = None
    if brain.repository:
        all_pumps = brain.repository.get_pump_models()
        for pump in all_pumps:
            if pump.get('pump_code') == pump_code:
                pump_data = pump
                break
    
    if not pump_data:
        safe_flash(f"Pump {pump_code} not found.", "error")
        return redirect(url_for('main_flow.index'))
    
    # Get BEP data and performance capabilities
    specs = pump_data.get('specifications', {})
    bep_flow = specs.get('bep_flow_m3hr', 0)
    bep_head = specs.get('bep_head_m', 0)
    bep_efficiency = specs.get('bep_efficiency_pct', 0)
    
    # Calculate what the pump CAN deliver at the requested flow
    performance_at_flow = brain.performance.calculate_performance_at_flow(
        pump_data, flow, allow_excessive_trim=True  # Allow showing performance even with excessive trim
    )
    
    # If performance calculation fails, show BEP data
    if not performance_at_flow:
        performance_at_flow = {
            'flow_m3hr': bep_flow,
            'head_m': bep_head,
            'efficiency_pct': bep_efficiency,
            'power_kw': specs.get('power_kw', 0),
            'npsh_r': specs.get('npsh_r', 0),
            'note': 'Showing pump BEP performance'
        }
    
    # Prepare pump data for display
    selected_pump = {
        'pump_code': pump_code,
        'pump_name': pump_data.get('pump_name', pump_code),
        'manufacturer': pump_data.get('manufacturer', 'APE'),
        'pump_type': pump_data.get('pump_type', 'Centrifugal'),
        'flow_m3hr': flow,
        'required_head_m': head,
        'delivered_head_m': performance_at_flow.get('head_m', bep_head),
        'efficiency_pct': performance_at_flow.get('efficiency_pct', bep_efficiency),
        'power_kw': performance_at_flow.get('power_kw', 0),
        'npsh_r': performance_at_flow.get('npsh_r', 0),
        'bep_flow_m3hr': bep_flow,
        'bep_head_m': bep_head,
        'bep_efficiency_pct': bep_efficiency,
        'trim_percent': performance_at_flow.get('trim_percent', 0),
        'specifications': specs,
        'curves': pump_data.get('curves', []),
        'note': performance_at_flow.get('note', '')
    }
    
    # Generate chart data using the charts intelligence module
    chart_data = brain.charts.generate_chart_data_payload(pump_data, performance_at_flow)
    
    breadcrumbs = [
        {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
        {'label': 'BEP Proximity', 'url': url_for('main_flow.bep_proximity_results', flow=flow, head=head)},
        {'label': pump_code, 'url': '#', 'icon': 'description'}
    ]
    
    from datetime import datetime
    
    return render_template('engineering_pump_report.html',
                         selected_pump=selected_pump,
                         chart_data=chart_data,
                         site_requirements={'flow_m3hr': flow, 'head_m': head},
                         alternatives=[],  # No alternatives for BEP proximity
                         breadcrumbs=breadcrumbs,
                         is_bep_proximity=True,  # Flag to show this is BEP proximity selection
                         current_date=datetime.now().strftime('%B %d, %Y'))

@reports_bp.route('/engineering_report/<path:pump_code>')
def engineering_report(pump_code):
    """BRAIN-ONLY Engineering Report - Single Source of Truth"""
    pump_code = unquote(pump_code)
    logger.info(f"Rendering engineering report for pump: {pump_code}")
    
    # Get definitive duty point from URL parameters or session
    site_reqs = safe_session_get('site_requirements', {})
    flow = request.args.get('flow', type=float) or site_reqs.get('flow_m3hr')
    head = request.args.get('head', type=float) or site_reqs.get('head_m')
    
    # Clean breadcrumbs for engineering report
    breadcrumbs = [
        {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
        {'label': 'Results', 'url': url_for('main_flow.pump_options', flow=flow, head=head) if flow and head else '#'},
        {'label': pump_code, 'url': '#', 'icon': 'engineering'}
    ]

    if not (flow and head):
        safe_flash("Flow and head are required to view a report.", "error")
        return redirect(url_for('main_flow.index'))

    # THE BRAIN IS THE SINGLE SOURCE OF TRUTH - NO FALLBACKS, NO LEGACY PATHS
    from ..pump_brain import get_pump_brain
    brain = get_pump_brain()
    
    # Clean pump code (remove any URL encoding artifacts)
    import urllib.parse
    clean_pump_code = urllib.parse.unquote(pump_code)
    # Remove any query parameters that got mixed in
    if '?' in clean_pump_code:
        clean_pump_code = clean_pump_code.split('?')[0]
    
    # Make one definitive call to the Brain to get all necessary data
    evaluation_result = brain.evaluate_pump(clean_pump_code, flow, head)
    
    if not evaluation_result or not evaluation_result.get('feasible'):
        safe_flash(f"Pump {pump_code} is not suitable for the duty point {flow}m³/hr @ {head}m.", "warning")
        return redirect(url_for('main_flow.index'))
        
    # The 'evaluation_result' is now the complete and final data object for the template
    # NO other recalculations are needed - Brain provides everything
    selected_pump = evaluation_result.copy()
    
    # CRITICAL FIX: Map Brain's total_score to template's expected suitability_score
    if 'total_score' in selected_pump:
        selected_pump['suitability_score'] = selected_pump['total_score']
    
    # Add pump specifications for template fields that need min/max impeller, test speed, etc.
    pump_models = brain.repository.get_pump_models()
    pump_model = next((p for p in pump_models if p.get('pump_code') == pump_code), None)
    if pump_model and 'specifications' in pump_model:
        selected_pump['specifications'] = pump_model['specifications']
    
    # Get alternatives from the session if they exist
    pump_selections = safe_session_get('suitable_pumps', [])
    alternatives = [p for p in pump_selections if p.get('pump_code') != pump_code][:2]
    
    # FIX: For direct searches, alternatives list is empty because main selection was skipped
    # Generate alternatives using Brain system when none exist
    if not alternatives and flow and head:
        logger.info(f"No alternatives found in session - generating via Brain for direct search")
        try:
            best_pumps_result = brain.find_best_pumps({'flow_m3hr': flow, 'head_m': head})
            if best_pumps_result and 'ranked_pumps' in best_pumps_result:
                # Get top 3 alternatives (excluding the current pump)
                brain_alternatives = []
                for pump in best_pumps_result['ranked_pumps'][:5]:  # Check top 5
                    if pump.get('pump_code') != pump_code:
                        brain_alternatives.append(pump)
                        if len(brain_alternatives) >= 2:  # Limit to 2 alternatives
                            break
                alternatives = brain_alternatives
                logger.info(f"Generated {len(alternatives)} alternatives via Brain system")
        except Exception as e:
            logger.warning(f"Could not generate alternatives via Brain: {e}")
            alternatives = []
    
    # Create breadcrumbs for navigation
    try:
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index')},
            {'label': 'Results', 'url': url_for('main_flow.pump_options', flow=flow, head=head)},
            {'label': f'{pump_code} - Engineering Report', 'url': '#'}
        ]
    except Exception as e:
        logger.warning(f"Could not generate breadcrumbs: {e}")
        breadcrumbs = []
    
    # Template data structure - SINGLE SOURCE FROM BRAIN
    template_data = {
        'selected_pump': selected_pump,  # Complete Brain evaluation result
        'site_requirements': {'flow_m3hr': flow, 'head_m': head},
        'alternatives': alternatives,
        'current_date': datetime.now().strftime("%d %B %Y"),
        'current_view': 'engineering',
        'show_view_toggle': True,
        'breadcrumbs': breadcrumbs
    }
    
    return render_template('engineering_pump_report.html', **template_data)

@reports_bp.route('/pdf_report/<path:pump_code>')
def pdf_report(pump_code):
    """Generate PDF report using Brain system exclusively."""
    pump_code = unquote(pump_code)
    
    # Get duty point
    site_reqs = safe_session_get('site_requirements', {})
    flow = request.args.get('flow', type=float) or site_reqs.get('flow_m3hr')
    head = request.args.get('head', type=float) or site_reqs.get('head_m')

    if not (flow and head):
        safe_flash("Flow and head are required to generate a PDF report.", "error")
        return redirect(url_for('main_flow.index'))

    # THE BRAIN IS THE SINGLE SOURCE OF TRUTH
    from ..pump_brain import get_pump_brain
    brain = get_pump_brain()
    
    evaluation_result = brain.evaluate_pump(pump_code, flow, head)
    
    if not evaluation_result:
        safe_flash(f"Cannot generate PDF for pump {pump_code}.", "error")
        return redirect(url_for('main_flow.index'))
    
    try:
        # TODO: Implement PDF generation - currently disabled
        # from ..pdf_generator import generate_pump_pdf
        
        # Generate PDF with Brain data - currently disabled
        # pdf_buffer = generate_pump_pdf(
        #     pump_data=evaluation_result,
        #     site_requirements={'flow_m3hr': flow, 'head_m': head}
        # )
        raise NotImplementedError("PDF generation temporarily disabled")
        
        # Create response
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{pump_code}_report.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        safe_flash("Error generating PDF report.", "error")
        return redirect(url_for('reports.engineering_report', pump_code=pump_code, flow=flow, head=head))

@reports_bp.route('/api/pump_report_data/<path:pump_code>')
def pump_report_data_api(pump_code):
    """API endpoint for pump report data using Brain system."""
    pump_code = unquote(pump_code)
    
    # Get duty point
    flow = request.args.get('flow', type=float)
    head = request.args.get('head', type=float)

    if not (flow and head):
        return jsonify({'error': 'Flow and head parameters are required'}), 400

    try:
        # THE BRAIN IS THE SINGLE SOURCE OF TRUTH
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        
        evaluation_result = brain.evaluate_pump(pump_code, flow, head)
        
        if not evaluation_result:
            return jsonify({'error': f'Pump {pump_code} not found or not suitable'}), 404
        
        # CRITICAL FIX: Map Brain's total_score to template's expected suitability_score
        if 'total_score' in evaluation_result:
            evaluation_result['suitability_score'] = evaluation_result['total_score']
            
        return jsonify({
            'success': True,
            'pump_data': evaluation_result,
            'site_requirements': {'flow_m3hr': flow, 'head_m': head}
        })
        
    except Exception as e:
        logger.error(f"Error in pump report data API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500