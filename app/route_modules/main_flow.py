"""Adding error handling to the index route to prevent crashes."""
"""
Main Flow Routes
Core user flow routes for pump selection and results
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from ..session_manager import safe_flash, safe_session_get, safe_session_set, safe_session_pop, safe_session_clear, get_form_data, store_form_data
from ..data_models import SiteRequirements
from ..pump_repository import get_pump_repository
from ..utils import validate_site_requirements

logger = logging.getLogger(__name__)

# Create blueprint
main_flow_bp = Blueprint('main_flow', __name__)

@main_flow_bp.route('/')
def index():
    """Main selection page."""
    try:
        logger.info("Index route accessed.")
        return render_template('input_form.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('500.html'), 500

@main_flow_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@main_flow_bp.route('/guide')
def guide():
    """Guide page."""
    logger.info("Guide page accessed.")
    return render_template('guide.html')

@main_flow_bp.route('/help')
def help():
    """Help page."""
    return render_template('help.html')

@main_flow_bp.route('/help-features')
def help_features_page():
    """Help features page."""
    return render_template('help_brochure.html')



@main_flow_bp.route('/pump_selection', methods=['POST', 'GET'])
def pump_selection():
    """Main pump selection endpoint."""
    if request.method == 'GET':
        return render_template('input_form.html')

    try:
        # Validate required fields
        flow_m3hr = request.form.get('flow_m3hr')
        head_m = request.form.get('head_m')

        if not flow_m3hr or not head_m:
            safe_flash('Flow rate and head are required fields.', 'error')
            return render_template('input_form.html'), 400

        try:
            flow_val = float(flow_m3hr)
            head_val = float(head_m)

            # Enhanced validation with realistic ranges
            if flow_val <= 0 or head_val <= 0:
                safe_flash('Flow rate and head must be positive values.', 'error')
                return render_template('input_form.html'), 400

            if flow_val > 10000:  # Reasonable upper limit
                safe_flash('Flow rate seems unusually high. Please verify your input.', 'warning')

            if head_val > 1000:  # Reasonable upper limit  
                safe_flash('Head seems unusually high. Please verify your input.', 'warning')

        except ValueError:
            safe_flash('Invalid numerical values for flow rate or head.', 'error')
            return render_template('input_form.html'), 400

        # Check for direct pump search
        direct_pump_search = request.form.get('direct_pump_search', '').strip()
        
        if direct_pump_search:
            logger.info(f"Direct pump search requested for: '{direct_pump_search}' with flow={flow_val}, head={head_val}")
            # Redirect directly to pump report with the searched pump
            return redirect(url_for('reports.pump_report',
                                   pump_code=direct_pump_search,
                                   flow=str(flow_val),
                                   head=str(head_val),
                                   direct_search='true'))
        
        # Get pump type from form
        selected_pump_type = request.form.get('pump_type', 'GENERAL')
        logger.info(f"Form submitted with pump type: '{selected_pump_type}'")
        
        # Process the selection - redirect to pump options
        return redirect(url_for('main_flow.pump_options', 
                               flow=str(flow_val), 
                               head=str(head_val),
                               application_type=request.form.get('application', 'water'),
                               pump_type=selected_pump_type))

    except Exception as e:
        logger.error(f"Error in pump selection: {str(e)}")
        safe_flash('An error occurred processing your request.', 'error')
        return render_template('input_form.html'), 500

@main_flow_bp.route('/select', methods=['GET'])
def select():
    """Select pump page."""
    return render_template('input_form.html')

@main_flow_bp.route('/pump_options')
def pump_options():
    """Show pump selection options page."""
    try:
        # Get form data with NaN protection
        flow_str = request.args.get('flow', '0')
        head_str = request.args.get('head', '0')

        # Reject NaN inputs
        if flow_str.lower() in ('nan', 'inf', '-inf'):
            flow = 0
        else:
            try:
                flow = float(flow_str)
                if not (flow == flow):  # NaN check (NaN != NaN)
                    flow = 0
            except (ValueError, TypeError):
                flow = 0

        if head_str.lower() in ('nan', 'inf', '-inf'):
            head = 0
        else:
            try:
                head = float(head_str)
                if not (head == head):  # NaN check (NaN != NaN)
                    head = 0
            except (ValueError, TypeError):
                head = 0

        if flow <= 0 or head <= 0:
            safe_flash('Please enter valid flow rate and head values.', 'error')
            return redirect(url_for('main_flow.index'))

        logger.info(f"Processing pump options for: flow={flow} m³/hr, head={head} m")

        # Get additional form parameters
        pump_type = request.args.get('pump_type', 'GENERAL')
        application_type = request.args.get('application_type', 'general')
        
        # Log pump type filtering for debugging
        logger.info(f"Pump type filter requested: '{pump_type}'")
        
        # Validate pump type against known types
        valid_pump_types = ['GENERAL', 'HSC', 'END SUCTION', 'MULTI-STAGE', 'VERTICAL TURBINE', 'AXIAL FLOW']
        if pump_type.upper() not in valid_pump_types:
            logger.warning(f"Invalid pump type '{pump_type}' requested, defaulting to 'GENERAL'")
            pump_type = 'GENERAL'

        # Create site requirements using pump_engine
        site_requirements = SiteRequirements(
            flow_m3hr=flow,
            head_m=head,
            pump_type=pump_type,
            application_type=application_type
        )

        # Use catalog engine for pump selection
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        logger.info(f"Loaded {len(catalog_engine.pumps)} pumps from catalog")

        # Evaluate pumps using catalog engine with pump type filtering and exclusion tracking
        pump_evaluations = []
        exclusion_data = None  # Initialize here
        try:
            # Get pump selections with exclusion data for transparency
            selection_data = catalog_engine.select_pumps(flow, head, max_results=10, pump_type=pump_type, return_exclusions=True)
            
            # Handle both old and new return formats
            if isinstance(selection_data, dict):
                pump_selections = selection_data['suitable_pumps']
                exclusion_data = {
                    'excluded_pumps': selection_data.get('excluded_pumps', []),
                    'exclusion_summary': selection_data.get('exclusion_summary', {}),
                    'total_evaluated': selection_data.get('total_evaluated', 0),
                    'feasible_count': selection_data.get('feasible_count', 0),
                    'excluded_count': selection_data.get('excluded_count', 0)
                }
            else:
                # Fallback for old format
                pump_selections = selection_data
                exclusion_data = None
            for selection in pump_selections[:3]:
                # Convert catalog engine format to template-compatible format
                pump = selection['pump']
                performance = selection['performance']

                standardized_eval = {
                    'pump_code': pump.pump_code,
                    'overall_score': selection.get('suitability_score', 0),
                    'selection_reason': f'Efficiency: {performance.get("efficiency_pct", 0):.1f}%, Head error: {selection.get("head_error_pct", 0):.1f}%',
                    'operating_point': performance,
                    'pump_info': {
                        'manufacturer': pump.manufacturer,
                        'model_series': pump.model_series,
                        'pump_type': pump.pump_type
                    },
                    'curve_index': 0,  # Will be determined from performance data
                    'suitable': selection.get('suitability_score', 0) > 50
                }
                pump_evaluations.append(standardized_eval)
        except Exception as e:
            import traceback
            logger.error(f"Error evaluating pumps with catalog engine: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            pump_evaluations = []

        if not pump_evaluations:
            safe_flash('No suitable pumps found for your requirements. Please adjust your specifications.', 'warning')
            return redirect(url_for('main_flow.index'))

        # Store results in session for detailed reports
        safe_session_set('pump_selections', pump_evaluations)
        safe_session_set('site_requirements', {
            'flow_m3hr': site_requirements.flow_m3hr,
            'head_m': site_requirements.head_m,
            'pump_type': site_requirements.pump_type,
            'customer_name': request.args.get('contact_name', 'Engineering Client'),
            'project_name': request.args.get('project_name', 'Pump Selection Project'),
            'application': request.args.get('application', 'Water Supply'),
            'fluid_type': request.args.get('liquid_type', 'Water')
        })
        
        # Store exclusion data for transparency
        if exclusion_data:
            safe_session_set('exclusion_data', exclusion_data)

        # Redirect to the best pump's report page with flow and head parameters
        best_pump = pump_evaluations[0]
        return redirect(url_for('reports.pump_report', 
                              pump_code=best_pump['pump_code'],
                              flow=site_requirements.flow_m3hr,
                              head=site_requirements.head_m,
                              pump_type=site_requirements.pump_type))

    except Exception as e:
        logger.error(f"Error in pump_options: {e}")
        safe_flash('An error occurred while processing your request. Please try again.', 'error')
        return redirect(url_for('main_flow.index'))