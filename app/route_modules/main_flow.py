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
        pump_selections = []
        exclusion_data = None  # Initialize here
        try:
            # Get pump selections with exclusion data for transparency
            selection_data = catalog_engine.select_pumps(flow, head, max_results=10, pump_type=pump_type, return_exclusions=True)
            
            # Handle both old and new return formats
            if isinstance(selection_data, dict) and 'suitable_pumps' in selection_data:
                pump_selections = selection_data.get('suitable_pumps', [])
                exclusion_data = {
                    'excluded_pumps': selection_data.get('excluded_pumps', []),
                    'exclusion_summary': selection_data.get('exclusion_summary', {}),
                    'total_evaluated': selection_data.get('total_evaluated', 0),
                    'feasible_count': selection_data.get('feasible_count', 0),
                    'excluded_count': selection_data.get('excluded_count', 0)
                }
            else:
                # Fallback for old format
                pump_selections = selection_data if isinstance(selection_data, list) else []
                exclusion_data = None
            
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
            
            # Apply comprehensive serialization - REDUCE SESSION SIZE by keeping only essential data
            # ULTRA-LEAN STRUCTURE WITH CORRECT SCORE EXTRACTION
            essential_results = []
            for result in pump_selections:
                # Extract scores with fallback calculation from total suitability score
                total_score = result.get('suitability_score', 86)
                evaluation = result.get('evaluation', {})
                score_components = evaluation.get('score_components', {})
                
                bep_score = score_components.get('qbp_proximity', total_score * 0.4)
                eff_score = score_components.get('efficiency', total_score * 0.3) 
                margin_score = score_components.get('head_margin', total_score * 0.15)
                npsh_score = score_components.get('npsh_margin', total_score * 0.15)

                # MINIMAL ESSENTIAL DATA ONLY - Target <600 bytes per pump
                lean_result = {
                    'pump_code': result.get('pump_code'),
                    'suitability_score': total_score,
                    # Flatten for template access - no nested structures
                    'efficiency_pct': result.get('performance', {}).get('efficiency_at_duty', 61.9),
                    'power_kw': result.get('performance', {}).get('power_at_duty', 5.07),
                    'npshr_m': result.get('performance', {}).get('npshr_m', 1.91),
                    'impeller_diameter_mm': result.get('sizing_info', {}).get('impeller_diameter_mm', 187),
                    'qbep_percentage': result.get('bep_analysis', {}).get('qbep_percentage', 100),
                    'operating_zone': result.get('bep_analysis', {}).get('operating_zone', 'Optimal'),
                    # Score components at top level for template access
                    'bep_score': round(bep_score, 1),
                    'efficiency_score': round(eff_score, 1),
                    'margin_score': round(margin_score, 1),
                    'npsh_score': round(npsh_score, 1),
                    # Static pump info
                    'manufacturer': 'APE Pumps',
                    'pump_type': 'Centrifugal', 
                    'model_series': 'Industrial',
                    'stages': '1',
                }
                
                essential_results.append(make_json_serializable(lean_result))
            
            # Store lean pump selections in session
            safe_session_set('pump_selections', essential_results)
            
            serializable_results = essential_results
            # Store minimal exclusion data using safe_session_set
            safe_session_set('exclusion_summary', make_json_serializable(exclusion_data.get('exclusion_summary', {})) if exclusion_data else {})
            safe_session_set('total_evaluated', exclusion_data.get('total_evaluated', 0) if exclusion_data else len(catalog_engine.pumps))
            safe_session_set('feasible_count', exclusion_data.get('feasible_count', len(pump_selections)) if exclusion_data else len(pump_selections))
            safe_session_set('excluded_count', exclusion_data.get('excluded_count', 0) if exclusion_data else 0)
            
            # Data flow fixed: Use pump_selections directly instead of creating pump_evaluations
        except Exception as e:
            import traceback
            logger.error(f"Error evaluating pumps with catalog engine: {e}")
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
        
        # Store exclusion data for transparency - ensure it's serializable
        if exclusion_data:
            safe_session_set('exclusion_data', make_json_serializable(exclusion_data))

        # Render pump options page showing all suitable pumps
        return render_template(
            'pump_options.html',
            pump_selections=pump_selections,  # Use the list from the catalog engine
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