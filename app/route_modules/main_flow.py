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
from ..process_logger import process_logger

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

@main_flow_bp.route('/bep_proximity_results')
def bep_proximity_results():
    """
    BEP Proximity Search Results - Fast selection based on BEP proximity.
    Finds pumps whose Best Efficiency Point is closest to the specified duty point.
    """
    try:
        # Get parameters from URL
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)
        pump_type = request.args.get('pump_type', default=None)
        
        # Validate inputs
        if not flow or not head or flow <= 0 or head <= 0:
            safe_flash('Invalid flow or head values. Please enter positive numbers.', 'error')
            return redirect(url_for('main_flow.index'))
        
        logger.info(f"BEP Proximity search: flow={flow} m³/hr, head={head}m, pump_type={pump_type}")
        
        # Get Brain instance and find pumps by BEP proximity
        from ..pump_brain import get_pump_brain
        brain = get_pump_brain()
        
        if not brain or not brain.selection:
            logger.error("Brain system not available for BEP proximity search")
            safe_flash('System temporarily unavailable. Please try again.', 'error')
            return redirect(url_for('main_flow.index'))
        
        # Find pumps by BEP proximity using normalized distance calculation
        proximity_results = brain.selection.find_pumps_by_bep_proximity(flow, head, pump_type)
        
        if not proximity_results:
            safe_flash('No pumps found with valid BEP data. Please try different parameters.', 'warning')
            return redirect(url_for('main_flow.index'))
        
        # Prepare breadcrumbs
        breadcrumbs = [
            {'label': 'Home', 'url': url_for('main_flow.index'), 'icon': 'home'},
            {'label': 'BEP Proximity Results', 'url': '#', 'icon': 'trending_up'}
        ]
        
        # Render results template
        return render_template(
            'bep_proximity_results.html',
            breadcrumbs=breadcrumbs,
            pumps=proximity_results,
            search_params={
                'flow': flow,
                'head': head,
                'pump_type': pump_type or 'All Types'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in BEP proximity search: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        safe_flash('An error occurred during BEP proximity search. Please try again.', 'error')
        return redirect(url_for('main_flow.index'))



@main_flow_bp.route('/pump_selection', methods=['POST', 'GET'])
def pump_selection():
    """Main pump selection endpoint."""
    if request.method == 'GET':
        return render_template('input_form.html')

    try:
        # Log start of selection process
        process_logger.log_section("PUMP SELECTION PROCESS START")
        process_logger.log_data("Form Data", dict(request.form))
        
        # Validate required fields - support both old and new field names
        flow_m3hr = request.form.get('flow_m3hr') or request.form.get('flow_rate')
        head_m = request.form.get('head_m') or request.form.get('total_head')
        
        process_logger.log(f"Raw Input: flow='{flow_m3hr}', head='{head_m}'")

        if not flow_m3hr or not head_m:
            process_logger.log("ERROR: Missing required fields", "ERROR")
            safe_flash('Flow rate and head are required fields.', 'error')
            return render_template('input_form.html'), 400

        try:
            flow_val = float(flow_m3hr)
            head_val = float(head_m)
            process_logger.log(f"Validated Input: flow={flow_val:.2f} m³/hr, head={head_val:.2f} m")

            # Enhanced validation with realistic ranges
            if flow_val <= 0 or head_val <= 0:
                process_logger.log("ERROR: Non-positive values", "ERROR")
                safe_flash('Flow rate and head must be positive values.', 'error')
                return render_template('input_form.html'), 400

            if flow_val > 10000:  # Reasonable upper limit
                process_logger.log(f"WARNING: High flow rate {flow_val} m³/hr", "WARNING")
                safe_flash('Flow rate seems unusually high. Please verify your input.', 'warning')

            if head_val > 1000:  # Reasonable upper limit  
                process_logger.log(f"WARNING: High head {head_val} m", "WARNING")
                safe_flash('Head seems unusually high. Please verify your input.', 'warning')

        except ValueError as e:
            process_logger.log(f"ERROR: Invalid numerical values - {str(e)}", "ERROR")
            safe_flash('Invalid numerical values for flow rate or head.', 'error')
            return render_template('input_form.html'), 400

        # Check for direct pump search
        direct_pump_search = request.form.get('direct_pump_search', '').strip()
        
        if direct_pump_search:
            process_logger.log(f"Direct pump search: '{direct_pump_search}'")
            logger.info(f"Direct pump search requested for: '{direct_pump_search}' with flow={flow_val}, head={head_val}")
            # Redirect directly to pump report with the searched pump
            return redirect(url_for('reports.pump_report',
                                   pump_code=direct_pump_search,
                                   flow=str(flow_val),
                                   head=str(head_val),
                                   direct_search='true'))
        
        # Get pump type from form
        selected_pump_type = request.form.get('pump_type', 'GENERAL')
        application_type = request.form.get('application', 'water')
        
        process_logger.log(f"Selection Parameters:")
        process_logger.log(f"  Flow: {flow_val:.2f} m³/hr")
        process_logger.log(f"  Head: {head_val:.2f} m")
        process_logger.log(f"  Pump Type: {selected_pump_type}")
        process_logger.log(f"  Application: {application_type}")
        
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
        process_logger.log_section("PUMP OPTIONS PROCESSING")
        process_logger.log_data("Request Args", dict(request.args))
        
        # Get form data with NaN protection
        flow_str = request.args.get('flow', '0')
        head_str = request.args.get('head', '0')
        
        process_logger.log(f"Input Strings: flow='{flow_str}', head='{head_str}'")

        # Reject NaN inputs
        if flow_str.lower() in ('nan', 'inf', '-inf'):
            process_logger.log(f"WARNING: Invalid flow string '{flow_str}', setting to 0", "WARNING")
            flow = 0
        else:
            try:
                flow = float(flow_str)
                if not (flow == flow):  # NaN check (NaN != NaN)
                    process_logger.log("WARNING: Flow is NaN, setting to 0", "WARNING")
                    flow = 0
            except (ValueError, TypeError):
                process_logger.log(f"ERROR: Cannot convert flow '{flow_str}' to float", "ERROR")
                flow = 0

        if head_str.lower() in ('nan', 'inf', '-inf'):
            process_logger.log(f"WARNING: Invalid head string '{head_str}', setting to 0", "WARNING")
            head = 0
        else:
            try:
                head = float(head_str)
                if not (head == head):  # NaN check (NaN != NaN)
                    process_logger.log("WARNING: Head is NaN, setting to 0", "WARNING")
                    head = 0
            except (ValueError, TypeError):
                process_logger.log(f"ERROR: Cannot convert head '{head_str}' to float", "ERROR")
                head = 0

        process_logger.log(f"Sanitized Values: flow={flow:.2f} m³/hr, head={head:.2f} m")

        if flow <= 0 or head <= 0:
            process_logger.log("ERROR: Invalid flow or head after sanitization", "ERROR")
            safe_flash('Please enter valid flow rate and head values.', 'error')
            return redirect(url_for('main_flow.index'))

        logger.info(f"Processing pump options for: flow={flow} m³/hr, head={head} m")

        # Get additional form parameters
        pump_type = request.args.get('pump_type', 'GENERAL')
        application_type = request.args.get('application_type', 'general')
        
        process_logger.log(f"Additional Parameters:")
        process_logger.log(f"  Pump Type: {pump_type}")
        process_logger.log(f"  Application: {application_type}")
        
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
        
        process_logger.log_separator()
        process_logger.log("BRAIN SYSTEM INITIALIZATION")

        # Prepare constraints for Brain system
        constraints = {
            'pump_type': pump_type,
            'max_results': 10,
            'application_type': application_type
        }
        
        process_logger.log_data("Constraints", constraints)

        # Evaluate pumps using Brain system with authentic exclusion tracking
        pump_selections = []
        exclusion_data = None
        try:
            # CRITICAL: Brain system validates with authentic exclusion reasons
            site_reqs = {'flow_m3hr': flow, 'head_m': head}
            
            process_logger.log("Calling Brain.find_best_pumps()...")
            brain_result = brain.find_best_pumps(site_reqs, constraints, include_exclusions=True)
            
            # Extract ranked pumps and authentic exclusion data
            pump_selections = brain_result.get('ranked_pumps', [])
            brain_exclusions = brain_result.get('exclusion_details')
            
            process_logger.log(f"Brain Results: {len(pump_selections)} feasible pumps found")
            
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

        # CRITICAL FIX: Create essential_results with proper nested structure for template
        def create_essential_result(pump_data):
            """Create properly structured data for template compatibility."""
            essential = {
                'pump_code': pump_data.get('pump_code', 'N/A'),
                'suitability_score': pump_data.get('total_score', pump_data.get('suitability_score', 0)),
                'total_score': pump_data.get('total_score', pump_data.get('suitability_score', 0)),
                'efficiency_pct': pump_data.get('efficiency_pct', pump_data.get('efficiency_at_duty', 0)),
                'power_kw': pump_data.get('power_kw', 0),
                'npshr_m': pump_data.get('npshr_m', 0),
                'qbp_percent': pump_data.get('qbp_percent', pump_data.get('qbep_percentage', 100)),
                'trim_percent': pump_data.get('trim_percent', 100),
                'operating_zone': pump_data.get('operating_zone', 'unknown'),
                'performance': {
                    'efficiency_pct': pump_data.get('efficiency_pct', pump_data.get('efficiency_at_duty', 0)),
                    'power_kw': pump_data.get('power_kw', 0),
                    'npshr_m': pump_data.get('npshr_m', 0),
                    'flow_m3hr': pump_data.get('flow_m3hr', 0),
                    'head_m': pump_data.get('head_m', 0),
                    'impeller_diameter_mm': pump_data.get('impeller_diameter_mm', 187)
                },
                # CRITICAL: Template expects nested pump structure
                'pump': {
                    'manufacturer': pump_data.get('manufacturer', 'APE PUMPS'),
                    'pump_type': pump_data.get('pump_type', 'END SUCTION'),
                    'model_series': pump_data.get('model_series', 'Industrial'),
                    'stages': pump_data.get('stages', '1')
                },
                # Direct access fields for template compatibility
                'manufacturer': pump_data.get('manufacturer', 'APE PUMPS'),
                'pump_type': pump_data.get('pump_type', 'END SUCTION'),
                'score_breakdown': {
                    'bep_score': pump_data.get('bep_score', 0),
                    'efficiency_score': pump_data.get('efficiency_score', 0),
                    'margin_score': pump_data.get('margin_score', 0),
                    'npsh_score': pump_data.get('npsh_score', 0)
                }
            }
            return essential

        # Create essential_results for template with proper nested structure
        essential_results = []
        all_pumps = preferred_pumps + allowable_pumps + acceptable_pumps + marginal_pumps
        for pump in all_pumps:
            essential_results.append(create_essential_result(pump))
        
        logger.info(f"Created {len(essential_results)} essential results with proper nested structure for template")

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
            pump_selections=essential_results,  # FIXED: Pass properly structured data
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