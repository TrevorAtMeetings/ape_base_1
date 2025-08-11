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
        # Home page doesn't need breadcrumbs - it's the starting point
        return render_template('input_form.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('500.html'), 500

@main_flow_bp.route('/about')
def about():
    """About page."""
    breadcrumbs = [
        {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
        {'label': 'About', 'url': '#', 'icon': 'info'}
    ]
    return render_template('about.html', breadcrumbs=breadcrumbs)

@main_flow_bp.route('/guide')
def guide():
    """Guide page."""
    logger.info("Guide page accessed.")
    breadcrumbs = [
        {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
        {'label': 'User Guide', 'url': '#', 'icon': 'help'}
    ]
    return render_template('guide.html', breadcrumbs=breadcrumbs)

@main_flow_bp.route('/help')
def help():
    """Help page."""
    breadcrumbs = [
        {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
        {'label': 'Help', 'url': '#', 'icon': 'help_outline'}
    ]
    return render_template('help.html', breadcrumbs=breadcrumbs)

@main_flow_bp.route('/help-features')
def help_features_page():
    """Help features page."""
    breadcrumbs = [
        {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
        {'label': 'Features', 'url': '#', 'icon': 'featured_play_list'}
    ]
    return render_template('help_brochure.html', breadcrumbs=breadcrumbs)



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

@main_flow_bp.route('/pump_options', methods=['GET', 'POST'])
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

        # BRAIN SYSTEM: Use Brain as core selection intelligence
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        logger.info("Using Brain system for pump selection - authentic validation only")

        # Prepare constraints for Brain system
        constraints = {
            'pump_type': pump_type,
            'max_results': 10,
            'application_type': application_type
        }

        # Evaluate pumps using Brain system with authentic exclusion tracking
        pump_selections = []
        exclusion_data = None
        try:
            # CRITICAL: Brain system validates with authentic exclusion reasons
            site_reqs = {'flow_m3hr': flow, 'head_m': head}
            brain_result = brain.find_best_pumps(site_reqs, constraints, include_exclusions=True)
            
            # Extract ranked pumps and authentic exclusion data
            pump_selections = brain_result.get('ranked_pumps', [])
            brain_exclusions = brain_result.get('exclusion_details')
            
            if brain_exclusions:
                # Use AUTHENTIC exclusion data from Brain - NO GUESSING
                exclusion_data = {
                    'excluded_pumps': brain_exclusions.get('excluded_pumps', []),
                    'exclusion_summary': brain_exclusions.get('exclusion_summary', {}),
                    'total_evaluated': brain_exclusions.get('total_evaluated', 0),
                    'feasible_count': brain_exclusions.get('feasible_count', len(pump_selections)),
                    'excluded_count': brain_exclusions.get('excluded_count', 0)
                }
                logger.info(f"Brain exclusions: {brain_exclusions.get('exclusion_summary', {})}")
            else:
                # Fallback only for structure, not data
                exclusion_data = {
                    'excluded_pumps': [],
                    'exclusion_summary': {},
                    'total_evaluated': 0,
                    'feasible_count': len(pump_selections),
                    'excluded_count': 0
                }
            
            # CRITICAL DATA FLOW FIX: Save the TRUE results from catalog engine to session
            # Convert ALL data to serializable formats
            def make_json_serializable(obj):
                """Convert any object to JSON serializable format."""
                import numpy as np
                from enum import Enum
                
                if obj is None or isinstance(obj, (str, int, float)):
                    return obj
                elif isinstance(obj, (bool, np.bool_)):
                    return bool(obj)  # Convert numpy bool to native Python bool
                elif isinstance(obj, (np.integer, np.floating)):
                    return obj.item()  # Convert numpy numbers
                elif hasattr(obj, 'item') and callable(getattr(obj, 'item')):  # Other numpy types
                    return obj.item()
                elif isinstance(obj, Enum):  # Handle all enum types explicitly
                    return obj.value  # Return the enum value instead of the enum object
                elif hasattr(obj, 'to_dict'):  # CatalogPump objects
                    return obj.to_dict()
                elif isinstance(obj, dict):
                    return {key: make_json_serializable(value) for key, value in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_json_serializable(item) for item in obj]
                else:
                    return str(obj)  # Convert everything else to string
            
            # NEW: Group results into ALL operating zones for tiered presentation
            preferred_pumps = [p for p in pump_selections if p.get('operating_zone') == 'preferred']
            allowable_pumps = [p for p in pump_selections if p.get('operating_zone') == 'allowable']
            acceptable_pumps = [p for p in pump_selections if p.get('operating_zone') == 'acceptable']
            marginal_pumps = [p for p in pump_selections if p.get('operating_zone') == 'marginal']
            
            logger.info(f"Tiered results: {len(preferred_pumps)} preferred, {len(allowable_pumps)} allowable, {len(acceptable_pumps)} acceptable, {len(marginal_pumps)} marginal pumps")
            
            # CRITICAL FIX: Use optimized session storage from session_manager
            from ..session_manager import store_pumps_optimized
            store_pumps_optimized(pump_selections)
            
            # Store ALL tiered results for enhanced UI
            safe_session_set('preferred_pumps', preferred_pumps)
            safe_session_set('allowable_pumps', allowable_pumps)
            safe_session_set('acceptable_pumps', acceptable_pumps)
            safe_session_set('marginal_pumps', marginal_pumps)
            
            # Store minimal exclusion data for transparency
            if exclusion_data:
                safe_session_set('exclusion_data', {
                    'total_evaluated': exclusion_data.get('total_evaluated', 0),
                    'feasible_count': exclusion_data.get('feasible_count', len(pump_selections)),
                    'excluded_count': exclusion_data.get('excluded_count', 0),
                    'suitable_pumps_count': len(pump_selections),
                    'preferred_count': len(preferred_pumps),
                    'allowable_count': len(allowable_pumps),
                    'acceptable_count': len(acceptable_pumps),
                    'marginal_count': len(marginal_pumps)
                })
            
            # Data flow fixed: Use pump_selections directly instead of creating pump_evaluations
        except Exception as e:
            import traceback
            logger.error(f"Error evaluating pumps with Brain system: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            pump_selections = []

        if not pump_selections:
            safe_flash('No suitable pumps found for your requirements. Please adjust your specifications.', 'warning')
            return redirect(url_for('main_flow.index'))

        # Store site requirements for reports (pump_selections already saved above with correct data)
        safe_session_set('site_requirements', {
            'flow_m3hr': flow,  # Use the 'flow' variable
            'head_m': head,     # Use the 'head' variable
            'pump_type': pump_type, # Use the 'pump_type' variable
            'customer_name': request.args.get('contact_name', 'Engineering Client'),
            'project_name': request.args.get('project_name', 'Pump Selection Project'),
            'application': application_type, # Use the 'application_type' variable
            'fluid_type': request.args.get('liquid_type', 'Water')
        })
        
        # Get ALL tiered results from session
        preferred_pumps = safe_session_get('preferred_pumps', [])
        allowable_pumps = safe_session_get('allowable_pumps', [])
        acceptable_pumps = safe_session_get('acceptable_pumps', [])
        marginal_pumps = safe_session_get('marginal_pumps', [])
        stored_pumps = safe_session_get('suitable_pumps', pump_selections)

        # Clean breadcrumbs for pump options page
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'Results', 'url': '#', 'icon': 'view_list'}
        ]
        
        # Render pump options page with ALL tiered results
        total_pumps = len(preferred_pumps) + len(allowable_pumps) + len(acceptable_pumps) + len(marginal_pumps)
        logger.info(f"Successfully found {total_pumps} total pumps: {len(preferred_pumps)} preferred, {len(allowable_pumps)} allowable, {len(acceptable_pumps)} acceptable, {len(marginal_pumps)} marginal")
        return render_template(
            'pump_options.html',
            breadcrumbs=breadcrumbs,
            pump_selections=stored_pumps,  # Legacy compatibility
            preferred_pumps=preferred_pumps,  # Tier 1 - Optimal range (80-110% BEP)
            allowable_pumps=allowable_pumps,  # Tier 2 - Good range (60-140% BEP)
            acceptable_pumps=acceptable_pumps,  # Tier 3 - Industrial range (50-200% BEP)
            marginal_pumps=marginal_pumps,  # Tier 4 - Outside typical ranges
            site_requirements={
                'flow_m3hr': flow,
                'head_m': head,
                'pump_type': pump_type,
                'customer_name': request.args.get('contact_name', 'Engineering Client'),
                'project_name': request.args.get('project_name', 'Pump Selection Project'),
                'application': application_type,
                'fluid_type': request.args.get('liquid_type', 'Water')
            },
            exclusion_data=safe_session_get('exclusion_data', {})
        )

    except Exception as e:
        import traceback
        logger.error(f"Error in pump_options: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        safe_flash('An error occurred while processing your request. Please try again.', 'error')
        return redirect(url_for('main_flow.index'))