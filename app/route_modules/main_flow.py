"""
Main Flow Routes
Core user flow routes for pump selection and results
"""
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, session, jsonify
from ..session_manager import safe_flash, safe_session_get, safe_session_set, safe_session_pop, safe_session_clear, get_form_data, store_form_data
from ..pump_engine import load_all_pump_data, find_best_pumps, validate_site_requirements, SiteRequirements, ParsedPumpData
from .. import app

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Main landing page with pump selection form."""
    logger.info("Index route accessed.")
    return render_template('input_form.html')

@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@app.route('/help')
def help():
    """Help page."""
    return render_template('help.html')

@app.route('/pump_selection', methods=['POST', 'GET'])
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
        
        # Process the selection
        return redirect(url_for('show_results', 
                               flow=str(flow_val), 
                               head=str(head_val),
                               application_type=request.form.get('application_type', 'water_supply'),
                               pump_type=request.form.get('pump_type', 'General')))
    
    except Exception as e:
        logger.error(f"Error in pump selection: {str(e)}")
        safe_flash('An error occurred processing your request.', 'error')
        return render_template('input_form.html'), 500

@app.route('/select', methods=['GET'])
def select():
    """Select pump page."""
    return render_template('input_form.html')

@app.route('/pump_options')
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
            return redirect(url_for('index'))

        logger.info(f"Processing pump options for: flow={flow} m³/hr, head={head} m")

        # Get additional form parameters
        pump_type = request.args.get('pump_type', 'General')
        application_type = request.args.get('application_type', 'general')
        
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

        # Evaluate pumps using catalog engine with pump type filtering
        pump_evaluations = []
        try:
            pump_selections = catalog_engine.select_pumps(flow, head, max_results=10, pump_type=pump_type)
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
            logger.error(f"Error evaluating pumps with catalog engine: {e}")
            pump_evaluations = []

        if not pump_evaluations:
            safe_flash('No suitable pumps found for your requirements. Please adjust your specifications.', 'warning')
            return redirect(url_for('index'))

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

        # Redirect to the best pump's report page with flow and head parameters
        best_pump = pump_evaluations[0]
        return redirect(url_for('pump_report', 
                              pump_code=best_pump['pump_code'],
                              flow=site_requirements.flow_m3hr,
                              head=site_requirements.head_m,
                              pump_type=site_requirements.pump_type))

    except Exception as e:
        logger.error(f"Error in pump_options: {e}")
        safe_flash('An error occurred while processing your request. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/show_results', methods=['POST', 'GET'])
def show_results():
    """Process pump selection and show results."""
    try:
        # Handle GET requests (back button) vs POST requests (form submission)
        if request.method == 'GET':
            # Try to get parameters from URL for GET requests
            flow = request.args.get('flow', type=float)
            head = request.args.get('head', type=float)

            if flow and head:
                form_data = {
                    'flow_m3hr': str(flow),
                    'head_m': str(head),
                    'pump_type': request.args.get('pump_type', 'General'),
                    'customer_name': request.args.get('customer', ''),
                    'project_name': request.args.get('project', ''),
                    'application': request.args.get('application', 'Water Supply')
                }
            else:
                # No valid parameters, redirect to pump options
                safe_flash('Please enter your pump requirements.', 'info')
                return redirect(url_for('index'))
        else:
            # POST request - get data from form
            form_data = request.form.to_dict()

        logger.debug(f"Received form data: {form_data}")

        # Convert form data to site requirements
        site_requirements = validate_site_requirements(form_data)
        logger.info(f"Processing requirements: {site_requirements}")

        # Extract pump type from form data
        pump_type = form_data.get('pump_type', 'General')
        logger.info(f"Pump type filter: {pump_type}")

        # Use catalog engine for pump selection
        from ..catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        
        # Find best pumps using catalog engine with pump type filtering
        top_selections = catalog_engine.select_pumps(
            site_requirements.flow_m3hr, 
            site_requirements.head_m, 
            max_results=10,
            pump_type=pump_type
        )

        if not top_selections:
            safe_flash('No suitable pumps found for your requirements. Please adjust your specifications.', 'warning')
            return redirect(url_for('index'))

        # Convert catalog engine format to template-compatible format
        pump_evaluations = []
        for selection in top_selections:
            pump = selection['pump']
            performance = selection['performance']
            
            # Create standardized evaluation format
            evaluation = {
                'pump_code': pump.pump_code,
                'overall_score': selection.get('suitability_score', 0),
                'selection_reason': f'Efficiency: {performance.get("efficiency_pct", 0):.1f}%, Head error: {selection.get("head_error_pct", 0):.1f}%',
                'operating_point': performance,
                'pump_info': {
                    'manufacturer': pump.manufacturer,
                    'model_series': pump.model_series,
                    'pump_type': pump.pump_type
                },
                'curve_index': 0,
                'suitable': selection.get('suitability_score', 0) > 50
            }
            pump_evaluations.append(evaluation)

        # Store results in session for detailed reports
        safe_session_set('pump_selections', pump_evaluations)
        safe_session_set('site_requirements', {
            'flow_m3hr': site_requirements.flow_m3hr,
            'head_m': site_requirements.head_m,
            'pump_type': site_requirements.pump_type,
            'customer_name': form_data.get('customer_name', 'Engineering Client'),
            'project_name': form_data.get('project_name', 'Pump Selection Project'),
            'application': form_data.get('application', 'Water Supply'),
            'fluid_type': form_data.get('fluid_type', 'Water')
        })

        return render_template('results.html',
                             pump_evaluations=pump_evaluations,
                             site_requirements={
                                 'flow_m3hr': site_requirements.flow_m3hr,
                                 'head_m': site_requirements.head_m,
                                 'pump_type': site_requirements.pump_type,
                                 'customer_name': form_data.get('customer_name', 'Engineering Client'),
                                 'project_name': form_data.get('project_name', 'Pump Selection Project'),
                                 'application': form_data.get('application', 'Water Supply'),
                                 'fluid_type': form_data.get('fluid_type', 'Water')
                             },
                             current_date=datetime.now().strftime('%Y-%m-%d'))

    except Exception as e:
        logger.error(f"Error in show_results: {str(e)}")
        safe_flash('An error occurred while processing your request. Please try again.', 'error')
        return redirect(url_for('index')) 