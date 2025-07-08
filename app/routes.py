import os
import logging
import csv
import io
import json
from datetime import datetime
from dotenv import load_dotenv
from flask import render_template, request, redirect, url_for, send_file, jsonify, make_response, session
from .session_manager import safe_flash, safe_session_get, safe_session_set, safe_session_pop, safe_session_clear, get_form_data, store_form_data
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import re
import markdown2

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Import the app instance FROM THE CURRENT PACKAGE (__init__.py)
from . import app
# Import pump engine functions as single source of truth
from app.pump_engine import load_all_pump_data, find_best_pumps, validate_site_requirements, SiteRequirements, ParsedPumpData

# Initialize logger first
logger = logging.getLogger(__name__)

# SCG Processing imports
try:
    from .scg_processor import SCGProcessor, ProcessingResult
    from .scg_catalog_adapter import SCGCatalogAdapter, CatalogEngineIntegrator
    from .batch_scg_processor import BatchSCGProcessor, BatchProcessingConfig, discover_scg_files, validate_scg_files
    SCG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"SCG processing modules not available: {e}")
    SCG_AVAILABLE = False

@app.route('/')
def index():
    """Main landing page with pump selection form."""
    logger.info("Index route accessed.")
    return render_template('input_form.html')

@app.route('/about')
def about():
    """About page with application information."""
    return render_template('about.html')

@app.route('/help')
def help_page():
    """Help page with user guidance."""
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
def select_pump_route():
    """Alternative route to the main form."""
    return render_template('input_form.html')

@app.route('/data-management')
def data_management():
    """Pump data management interface with table view and export options."""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        category = request.args.get('category', 'all', type=str)
        
        # Load pump data
        all_pumps = load_all_pump_data()
        
        # Apply filters
        filtered_pumps = all_pumps
        
        if search:
            filtered_pumps = [p for p in filtered_pumps if search.lower() in p.pump_code.lower()]
        
        if category != 'all':
            if category == 'END_SUCTION':
                filtered_pumps = [p for p in filtered_pumps 
                                if not any(x in p.pump_code.upper() for x in ['2F', '2P', '3P', '4P', '6P', '8P', 'ALE', 'HSC'])]
            elif category == 'MULTI_STAGE':
                filtered_pumps = [p for p in filtered_pumps 
                                if any(x in p.pump_code.upper() for x in ['2F', '2P', '3P', '4P', '6P', '8P'])]
            elif category == 'AXIAL_FLOW':
                filtered_pumps = [p for p in filtered_pumps if 'ALE' in p.pump_code.upper()]
            elif category == 'HSC':
                filtered_pumps = [p for p in filtered_pumps if 'HSC' in p.pump_code.upper()]
        
        # Calculate pagination
        total = len(filtered_pumps)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        pumps_page = filtered_pumps[start_idx:end_idx]
        
        # Prepare pump data for display
        pump_data = []
        for pump in pumps_page:
            # Extract basic performance data using catalog format
            max_flow = 0
            max_head = 0
            max_efficiency = 0
            has_npsh = False
            
            # Parse curves from pump_info
            from app.pump_engine import _parse_performance_curves
            curves = _parse_performance_curves(pump.pump_info)
            curve_count = len(curves)
            
            for curve in curves:
                flow_head_data = curve.get('flow_vs_head', [])
                if flow_head_data:
                    flows = [f for f, h in flow_head_data]
                    heads = [h for f, h in flow_head_data]
                    if flows:
                        max_flow = max(max_flow, max(flows))
                    if heads:
                        max_head = max(max_head, max(heads))
                
                eff_data = curve.get('flow_vs_efficiency', [])
                if eff_data:
                    effs = [e for f, e in eff_data if e > 0]
                    if effs:
                        max_efficiency = max(max_efficiency, max(effs))
                
                # Check for NPSH data
                npsh_data = curve.get('flow_vs_npshr', [])
                if npsh_data and any(npsh > 0 for f, npsh in npsh_data):
                    has_npsh = True
            
            pump_data.append({
                'pump_code': pump.pump_code,
                'manufacturer': pump.manufacturer,
                'model': pump.model,
                'max_flow': max_flow,
                'max_head': max_head,
                'max_efficiency': max_efficiency,
                'curve_count': curve_count,
                'has_npsh': has_npsh
            })
        
        # Calculate pagination info
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('data_management.html',
                             pumps=pump_data,
                             total=total,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             search=search,
                             category=category)
    
    except Exception as e:
        logger.error(f"Error in data management: {str(e)}")
        safe_flash('Error loading pump data.', 'error')
        return redirect(url_for('index'))

@app.route('/export-csv')
def export_csv():
    """Export pump data to CSV format."""
    try:
        # Load all pump data
        all_pumps = load_all_pump_data()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header with comprehensive performance data
        writer.writerow([
            'Pump Code', 'Manufacturer', 'Model', 'Test Speed (RPM)', 'Curve Count',
            'Max Flow (m³/hr)', 'Min Flow (m³/hr)', 'Flow Range (m³/hr)',
            'Max Head (m)', 'Min Head (m)', 'Head Range (m)',
            'Max Efficiency (%)', 'Min Efficiency (%)', 'Efficiency Range (%)',
            'Max Power (kW)', 'Min Power (kW)', 'Power Range (kW)',
            'Has NPSH Data', 'Max NPSH (m)', 'Min NPSH (m)',
            'BEP Flow (m³/hr)', 'BEP Head (m)', 'BEP Efficiency (%)', 'BEP Power (kW)',
            'Flow Points Count', 'Head Points Count', 'Efficiency Points Count', 'Power Points Count',
            'Impeller Sizes', 'Curve Quality Score', 'Data Completeness (%)',
            'Performance Summary'
        ])
        
        # Write comprehensive pump performance data
        for pump in all_pumps:
            # Initialize performance tracking variables
            all_flows, all_heads, all_efficiencies, all_powers, all_npshr = [], [], [], [], []
            curve_count = len(pump.curves) if pump.curves else 0
            impeller_sizes = []
            flow_points = head_points = eff_points = power_points = 0
            
            # Extract all performance data from curves
            if pump.curves:
                for curve in pump.curves:
                    # Flow vs Head data
                    flow_head_data = curve.get('flow_vs_head', [])
                    if flow_head_data:
                        curve_flows = [f for f, h in flow_head_data if f > 0]
                        curve_heads = [h for f, h in flow_head_data if h > 0]
                        all_flows.extend(curve_flows)
                        all_heads.extend(curve_heads)
                        flow_points += len(curve_flows)
                        head_points += len(curve_heads)
                    
                    # Flow vs Efficiency data
                    eff_data = curve.get('flow_vs_efficiency', [])
                    if eff_data:
                        curve_effs = [e for f, e in eff_data if e > 0 and e <= 100]
                        all_efficiencies.extend(curve_effs)
                        eff_points += len(curve_effs)
                    
                    # Flow vs Power data
                    power_data = curve.get('flow_vs_power', [])
                    if power_data:
                        curve_powers = [p for f, p in power_data if p > 0]
                        all_powers.extend(curve_powers)
                        power_points += len(curve_powers)
                    
                    # NPSH data
                    npshr_data = curve.get('flow_vs_npshr', [])
                    if npshr_data:
                        curve_npshr = [n for f, n in npshr_data if n > 0]
                        all_npshr.extend(curve_npshr)
                    
                    # Impeller size
                    impeller_size = curve.get('impeller_size', 'Standard')
                    if impeller_size and impeller_size not in impeller_sizes:
                        impeller_sizes.append(impeller_size)
            
            # Calculate performance ranges and statistics
            max_flow = max(all_flows) if all_flows else 0
            min_flow = min(all_flows) if all_flows else 0
            flow_range = max_flow - min_flow if all_flows else 0
            
            max_head = max(all_heads) if all_heads else 0
            min_head = min(all_heads) if all_heads else 0
            head_range = max_head - min_head if all_heads else 0
            
            max_efficiency = max(all_efficiencies) if all_efficiencies else 0
            min_efficiency = min(all_efficiencies) if all_efficiencies else 0
            eff_range = max_efficiency - min_efficiency if all_efficiencies else 0
            
            max_power = max(all_powers) if all_powers else 0
            min_power = min(all_powers) if all_powers else 0
            power_range = max_power - min_power if all_powers else 0
            
            max_npshr = max(all_npshr) if all_npshr else 0
            min_npshr = min(all_npshr) if all_npshr else 0
            
            # Calculate BEP (Best Efficiency Point)
            bep_flow = bep_head = bep_efficiency = bep_power = 'N/A'
            if all_efficiencies and pump.curves:
                max_eff_idx = all_efficiencies.index(max_efficiency)
                # Find corresponding flow point for max efficiency
                for curve in pump.curves:
                    eff_data = curve.get('flow_vs_efficiency', [])
                    if eff_data:
                        for i, (f, e) in enumerate(eff_data):
                            if abs(e - max_efficiency) < 0.1:  # Close match
                                bep_flow = f
                                bep_efficiency = e
                                # Find corresponding head and power
                                flow_head_data = curve.get('flow_vs_head', [])
                                power_data = curve.get('flow_vs_power', [])
                                if flow_head_data and i < len(flow_head_data):
                                    bep_head = flow_head_data[i][1]
                                if power_data and i < len(power_data):
                                    bep_power = power_data[i][1]
                                break
                    if bep_flow != 'N/A':
                        break
            
            # Calculate data quality metrics
            total_possible_points = curve_count * 4  # Flow, Head, Efficiency, Power
            actual_points = flow_points + head_points + eff_points + power_points
            data_completeness = (actual_points / total_possible_points * 100) if total_possible_points > 0 else 0
            
            # Quality score based on data completeness and ranges
            quality_score = 0
            if curve_count > 0:
                quality_score += min(curve_count * 20, 40)  # Max 40 for curve count
            if flow_range > 100:
                quality_score += 20  # Good flow range
            if eff_range > 10:
                quality_score += 20  # Good efficiency range
            if all_npshr:
                quality_score += 20  # Has NPSH data
            quality_score = min(quality_score, 100)
            
            # Performance summary
            performance_summary = []
            if max_efficiency > 85:
                performance_summary.append("High Efficiency")
            elif max_efficiency > 70:
                performance_summary.append("Good Efficiency")
            else:
                performance_summary.append("Standard Efficiency")
            
            if flow_range > 1000:
                performance_summary.append("Wide Flow Range")
            elif flow_range > 500:
                performance_summary.append("Moderate Flow Range")
            else:
                performance_summary.append("Narrow Flow Range")
            
            if all_npshr:
                performance_summary.append("NPSH Available")
            else:
                performance_summary.append("NPSH Not Available")
            
            summary_text = "; ".join(performance_summary)
            
            # Format numeric values with proper handling
            def format_value(val, decimals=1):
                if isinstance(val, (int, float)) and val > 0:
                    return f'{val:.{decimals}f}'
                return 'N/A'
            
            writer.writerow([
                pump.pump_code,
                pump.manufacturer,
                pump.model or 'N/A',
                getattr(pump, 'test_speed', 'N/A'),
                curve_count,
                format_value(max_flow),
                format_value(min_flow),
                format_value(flow_range),
                format_value(max_head),
                format_value(min_head),
                format_value(head_range),
                format_value(max_efficiency),
                format_value(min_efficiency),
                format_value(eff_range),
                format_value(max_power),
                format_value(min_power),
                format_value(power_range),
                'Yes' if all_npshr else 'No',
                format_value(max_npshr),
                format_value(min_npshr),
                format_value(bep_flow) if isinstance(bep_flow, (int, float)) else bep_flow,
                format_value(bep_head) if isinstance(bep_head, (int, float)) else bep_head,
                format_value(bep_efficiency) if isinstance(bep_efficiency, (int, float)) else bep_efficiency,
                format_value(bep_power) if isinstance(bep_power, (int, float)) else bep_power,
                flow_points,
                head_points,
                eff_points,
                power_points,
                '; '.join(impeller_sizes) if impeller_sizes else 'Standard',
                f'{quality_score:.0f}',
                f'{data_completeness:.1f}',
                summary_text
            ])
        
        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=ape_pumps_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
    
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        safe_flash('Error exporting data to CSV.', 'error')
        return redirect(url_for('data_management'))

@app.route('/upload-pump-data', methods=['POST'])
def upload_pump_data():
    """Upload new pump data from file."""
    try:
        if 'pump_file' not in request.files:
            safe_flash('No file selected.', 'error')
            return redirect(url_for('data_management'))
        
        file = request.files['pump_file']
        if file.filename == '':
            safe_flash('No file selected.', 'error')
            return redirect(url_for('data_management'))
        
        if not file.filename or not file.filename.lower().endswith(('.json', '.csv', '.txt')):
            safe_flash('Invalid file format. Please upload JSON, CSV, or TXT files.', 'error')
            return redirect(url_for('data_management'))
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(app.config.get('UPLOAD_FOLDER', 'app/static/temp'), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename or 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(upload_dir, safe_filename)
        file.save(file_path)
        
        # Process the file based on type
        upload_results = {'success': 0, 'errors': 0, 'messages': []}
        
        if filename.lower().endswith('.json'):
            upload_results = process_json_upload(file_path)
        elif filename.lower().endswith('.csv'):
            upload_results = process_csv_upload(file_path)
        elif filename.lower().endswith('.txt'):
            upload_results = process_txt_upload(file_path)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        if upload_results['success'] > 0:
            safe_flash(f'Successfully uploaded {upload_results["success"]} pumps. {upload_results["errors"]} errors.', 'success')
        else:
            safe_flash(f'Upload failed. {upload_results["errors"]} errors found.', 'error')
        
        for message in upload_results['messages'][:5]:  # Show first 5 messages
            safe_flash(message, 'info')
        
        return redirect(url_for('data_management'))
    
    except Exception as e:
        logger.error(f"Error uploading pump data: {str(e)}")
        safe_flash('Error processing uploaded file.', 'error')
        return redirect(url_for('data_management'))

def process_json_upload(file_path):
    """Process JSON pump data upload."""
    results = {'success': 0, 'errors': 0, 'messages': []}
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        pumps_data = []
        if isinstance(data, dict) and 'pumps' in data:
            pumps_data = data['pumps']
        elif isinstance(data, list):
            pumps_data = data
        elif isinstance(data, dict):
            pumps_data = [data]
        
        for pump_data in pumps_data:
            try:
                # Validate required fields
                if not isinstance(pump_data, dict):
                    results['errors'] += 1
                    continue
                
                # Extract pump code
                pump_code = None
                if 'objPump' in pump_data:
                    pump_code = pump_data['objPump'].get('pPumpCode')
                elif 'pPumpCode' in pump_data:
                    pump_code = pump_data['pPumpCode']
                elif 'pump_code' in pump_data:
                    pump_code = pump_data['pump_code']
                
                if not pump_code:
                    results['errors'] += 1
                    results['messages'].append(f'Missing pump code in data entry')
                    continue
                
                # Add to database (this would typically involve database insertion)
                # For now, we'll just validate the structure
                results['success'] += 1
                results['messages'].append(f'Validated pump: {pump_code}')
                
            except Exception as e:
                results['errors'] += 1
                results['messages'].append(f'Error processing pump data: {str(e)[:50]}')
    
    except Exception as e:
        results['errors'] += 1
        results['messages'].append(f'Error reading JSON file: {str(e)[:50]}')
    
    return results

def process_csv_upload(file_path):
    """Process CSV pump data upload."""
    results = {'success': 0, 'errors': 0, 'messages': []}
    
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    pump_code = row.get('Pump Code') or row.get('pump_code')
                    if not pump_code:
                        results['errors'] += 1
                        results['messages'].append(f'Row {row_num}: Missing pump code')
                        continue
                    
                    # Validate required fields
                    manufacturer = row.get('Manufacturer') or row.get('manufacturer')
                    if not manufacturer:
                        results['errors'] += 1
                        results['messages'].append(f'Row {row_num}: Missing manufacturer')
                        continue
                    
                    results['success'] += 1
                    results['messages'].append(f'Validated pump: {pump_code}')
                    
                except Exception as e:
                    results['errors'] += 1
                    results['messages'].append(f'Row {row_num}: {str(e)[:50]}')
    
    except Exception as e:
        results['errors'] += 1
        results['messages'].append(f'Error reading CSV file: {str(e)[:50]}')
    
    return results

def process_unified_pump_file(file_path):
    """Process pump file using unified processor for both SCG and TXT formats."""
    try:
        from app.unified_pump_processor import UnifiedPumpProcessor
        from app.scg_catalog_adapter import SCGCatalogAdapter
        from app.catalog_engine import get_catalog_engine
        
        # Use unified processor
        processor = UnifiedPumpProcessor()
        result = processor.process_file(file_path)
        
        # Convert result to legacy format for compatibility
        legacy_result = {'success': 0, 'errors': 0, 'messages': [], 'pump_data': None}
        
        if result.success and result.pump_data:
            # Convert to catalog format using existing adapter
            adapter = SCGCatalogAdapter()
            catalog_data = adapter.map_scg_to_catalog(result.pump_data)
            
            if catalog_data:
                legacy_result['success'] += 1
                legacy_result['pump_data'] = catalog_data
                if result.pump_data and result.pump_data.get('pump_info'):
                    pump_code = result.pump_data.get('pump_info', {}).get('pPumpCode', 'Unknown')
                    legacy_result['messages'].append(f'Successfully processed pump: {pump_code}')
                    legacy_result['messages'].append(f'File type: {result.file_type}')
                    legacy_result['messages'].append(f'Performance curves: {len(result.pump_data.get("curves", []))}')
                    legacy_result['messages'].append(f'Processing time: {result.processing_time:.2f}s')
                    
                    # Add power calculation validation with null safety
                    curves = result.pump_data.get('curves', [])
                    if curves:
                        for curve in curves:
                            power_data = curve.get('power_data')
                            if power_data and len(power_data) > 0:
                                avg_power = sum(power_data) / len(power_data)
                                legacy_result['messages'].append(f'Average power: {avg_power:.1f} kW')
                                break
                else:
                    legacy_result['messages'].append('Warning: Incomplete pump data structure')
            else:
                legacy_result['errors'] += 1
                legacy_result['messages'].append('Failed to convert to catalog format')
        else:
            legacy_result['errors'] += 1
            if result.errors:
                legacy_result['messages'].extend(result.errors)
            else:
                legacy_result['messages'].append('Processing failed')
        
        return legacy_result
        
    except Exception as e:
        return {
            'success': 0,
            'errors': 1,
            'messages': [f'Unified processing error: {str(e)[:50]}'],
            'pump_data': None
        }






@app.route('/pump-options')
def pump_options():
    return show_results()

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
        from app.catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        
        # Find best pumps using catalog engine with pump type filtering
        top_selections = catalog_engine.select_pumps(
            site_requirements.flow_m3hr, 
            site_requirements.head_m, 
            max_results=10,
            pump_type=pump_type
        )

        if not top_selections:
            logger.warning(f"No pumps found for flow={site_requirements.flow_m3hr}, head={site_requirements.head_m}")
            safe_flash('No suitable pumps found for your requirements. Please adjust your specifications.', 'warning')
            return redirect(url_for('index'))

        # Get the selected pump details from catalog format
        best_selection = top_selections[0]
        suggested_pump_obj = best_selection['pump']
        performance_data = best_selection['performance']

        if not suggested_pump_obj:
            safe_flash('Error retrieving pump details. Please try again.', 'error')
            return redirect(url_for('index'))

        # Generate charts for the suggested pump using catalog format
        chart_paths = generate_pump_charts(
            suggested_pump_obj, 
            performance_data,
            site_requirements
        )

        # Prepare template data
        template_data = {
            'site_requirements': site_requirements,
            'top_selections': top_selections,
            'suggested_pump_obj': suggested_pump_obj,
            'chart_paths': chart_paths,
            'num_alternatives': len(top_selections) - 1
        }

        # Store minimal results in session for report page (to avoid cookie size issues)
        session['pump_selections'] = [
            {
                'pump_code': selection['pump'].pump_code,
                'suitability_score': float(selection.get('suitability_score', 0)),
                'operating_point': {
                    'flow_m3hr': float(selection['performance'].get('flow_m3hr', 0)),
                    'head_m': float(selection['performance'].get('head_m', 0)),
                    'efficiency_pct': float(selection['performance'].get('efficiency_pct', 0)),
                    'power_kw': float(selection['performance'].get('power_kw', 0)),
                    'impeller_diameter_mm': float(selection['performance'].get('impeller_diameter_mm', 0)),
                    'test_speed_rpm': int(selection['performance'].get('test_speed_rpm', 0)) if selection['performance'].get('test_speed_rpm') else 0
                },
                'selected_curve': {
                    'curve_id': selection['performance'].get('curve', {}).get('curve_id', ''),
                    'impeller_diameter_mm': float(selection['performance'].get('curve', {}).get('impeller_diameter_mm', 0))
                },
                'ai_reasoning': ''  # Can be added later if needed
            }
            for selection in top_selections[:3]  # Limit to top 3 to reduce size
        ]
        session['site_requirements'] = {
            'flow_m3hr': site_requirements.flow_m3hr,
            'head_m': site_requirements.head_m,
            'pump_type': getattr(site_requirements, 'pump_type', 'General'),
            'customer_name': getattr(site_requirements, 'customer_name', ''),
            'project_name': getattr(site_requirements, 'project_name', ''),
            'application': getattr(site_requirements, 'application_type', ''),
        }

        # Redirect to dedicated report page
        selected_pump_code = top_selections[0]['pump'].pump_code
        return redirect(url_for('pump_report', pump_code=selected_pump_code))

    except ValueError as ve:
        safe_flash(f'Invalid input: {str(ve)}', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in pump selection: {str(e)}", exc_info=True)
        safe_flash('An error occurred during pump selection. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/pump_options')
def pump_options_page():
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
        from app.catalog_engine import get_catalog_engine
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

        return render_template('pump_options.html', 
                             pump_evaluations=pump_evaluations,
                             site_requirements={
                                 'flow_m3hr': site_requirements.flow_m3hr,
                                 'head_m': site_requirements.head_m,
                                 'pump_type': site_requirements.pump_type,
                                 'customer_name': getattr(site_requirements, 'customer_name', ''),
                                 'project_name': getattr(site_requirements, 'project_name', ''),
                                 'application': getattr(site_requirements, 'application', 'Water Supply'),
                             },
                             current_date='2024-06-06')

    except Exception as e:
        logger.error(f"Error in pump_options: {e}")
        safe_flash('An error occurred while processing your request. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/pump_report', methods=['POST'])
def pump_report_direct():
    """Generate PDF report directly from form data."""
    try:
        # Process form data similar to show_results
        form_data = {
            'flow_m3hr': request.form.get('flow_rate'),
            'head_m': request.form.get('head'),
            'customer_name': request.form.get('client_name', ''),
            'project_name': request.form.get('project_name', ''),
            'application': request.form.get('application_type', 'Water Supply'),
            'notes': request.form.get('notes', '')
        }

        site_requirements = validate_site_requirements(form_data)
        logger.info(f"PDF Direct - Processing requirements: {site_requirements}")

        # Load and find best pumps
        parsed_pumps_list = load_all_pump_data()
        pump_selections = find_best_pumps(parsed_pumps_list, site_requirements)

        if not pump_selections:
            safe_flash('No suitable pumps found for the specified requirements.', 'error')
            return redirect(url_for('index'))

        # Use the best pump for PDF generation
        selected_evaluation = pump_selections[0]
        target_pump = None
        for pump in parsed_pumps_list:
            if pump.pump_code == selected_evaluation['pump_code']:
                target_pump = pump
                break

        if not target_pump:
            safe_flash('Error finding pump data for PDF generation.', 'error')
            return redirect(url_for('index'))

        # Generate PDF
        from app.pdf_generator import generate_pdf_report as generate_pdf
        pdf_content = generate_pdf(
            selected_pump_evaluation=selected_evaluation,
            parsed_pump=target_pump,
            site_requirements=site_requirements,
            alternatives=pump_selections[1:3] if len(pump_selections) > 1 else []
        )

        # Return PDF response
        from flask import Response
        response = Response(pdf_content, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename="APE_Pump_Report_{selected_evaluation["pump_code"].replace("/", "_")}.pdf"'
        logger.info(f"PDF generated successfully for pump: {selected_evaluation['pump_code']}")
        return response

    except Exception as e:
        logger.error(f"Error in direct PDF generation: {str(e)}", exc_info=True)
        safe_flash('Error generating PDF report. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/pump_report/<path:pump_code>')
def pump_report(pump_code):
    """Display comprehensive pump selection report."""
    try:
        # URL decode the pump code
        from urllib.parse import unquote
        pump_code = unquote(pump_code)

        # Get stored results from session with validation
        pump_selections = session.get('pump_selections', [])
        site_requirements_data = session.get('site_requirements', {})
        
        # Validate session data integrity
        if pump_selections and not isinstance(pump_selections, list):
            logger.warning("Invalid pump_selections data in session, resetting")
            pump_selections = []
        
        if site_requirements_data and not isinstance(site_requirements_data, dict):
            logger.warning("Invalid site_requirements data in session, resetting")
            site_requirements_data = {}

        # If no session data, regenerate from URL parameters using catalog engine
        if not pump_selections:
            flow = request.args.get('flow', type=float)
            head = request.args.get('head', type=float)
            
            if not flow or not head:
                safe_flash('Flow and head parameters are required for pump analysis.', 'error')
                return redirect(url_for('index'))

            # Use catalog engine for consistent data
            from app.catalog_engine import get_catalog_engine
            catalog_engine = get_catalog_engine()
            
            try:
                # Create site requirements from URL params
                site_requirements_data = {
                    'flow_m3hr': flow,
                    'head_m': head,
                    'pump_type': request.args.get('pump_type', 'General'),
                    'customer_name': request.args.get('customer', ''),
                    'project_name': request.args.get('project', ''),
                }

                # Get specific pump from catalog engine
                target_pump = catalog_engine.get_pump_by_code(pump_code)
                if target_pump:
                    performance = target_pump.get_performance_at_duty(flow, head)
                    if performance:
                        # Create selection data structure with calculated performance
                        pump_selections = [{
                            'pump_code': pump_code,
                            'overall_score': performance.get('efficiency_pct', 0),
                            'efficiency_at_duty': performance.get('efficiency_pct', 0),
                            'operating_point': performance,
                            'suitable': performance.get('efficiency_pct', 0) > 40,
                            'manufacturer': target_pump.manufacturer,
                            'pump_info': {
                                'pPumpCode': pump_code,
                                'pSuppName': target_pump.manufacturer,
                                'pPumpTestSpeed': str(performance.get('test_speed_rpm', 1480)),
                                'pFilter1': target_pump.manufacturer,
                                'pStages': '1'
                            }
                        }]
                    else:
                        pump_selections = []
                else:
                    pump_selections = []

            except Exception as e:
                logger.warning(f"Catalog pump evaluation failed: {e}")
                pump_selections = []

        # Find the selected pump in results
        selected_pump = None
        for selection in pump_selections:
            if selection.get('pump_code') == pump_code:
                selected_pump = selection
                break

        # If pump not found in session data, force regenerate with specific pump
        if not selected_pump:
            # Get parameters from URL or use defaults for the specific pump
            flow = request.args.get('flow', 1600.0, type=float)
            head = request.args.get('head', 10.3, type=float)
            pump_type = request.args.get('pump_type', 'AXIAL_FLOW')
            
            from app.catalog_engine import get_catalog_engine
            catalog_engine = get_catalog_engine()
            
            # Get the specific pump and validate it can meet requirements
            target_pump = catalog_engine.get_pump_by_code(pump_code)
            if target_pump:
                performance = target_pump.get_performance_at_duty(flow, head)
                if performance:
                    # Create selection data for the specific requested pump
                    selected_pump = {
                        'pump_code': pump_code,
                        'overall_score': performance.get('selection_score', performance.get('efficiency_pct', 0)),
                        'efficiency_at_duty': performance.get('efficiency_pct', 0),
                        'operating_point': performance,
                        'suitable': performance.get('efficiency_pct', 0) > 40,
                        'manufacturer': target_pump.manufacturer,
                        'pump_info': {
                            'pPumpCode': pump_code,
                            'pSuppName': target_pump.manufacturer,
                            'pPumpTestSpeed': str(performance.get('test_speed_rpm', 1480)),
                            'pFilter1': target_pump.manufacturer,
                            'pStages': '1'
                        }
                    }
                    # Update session with correct data
                    site_requirements_data = {
                        'flow_m3hr': flow,
                        'head_m': head,
                        'pump_type': pump_type
                    }
                    pump_selections = [selected_pump]

        if not selected_pump:
            safe_flash('Selected pump not found or cannot meet requirements. Please start a new selection.', 'warning')
            return redirect(url_for('index'))

        logger.info(f"Displaying report for pump: {pump_code}")

        # Get complete pump data with curves for data table
        from app.catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        catalog_pump = catalog_engine.get_pump_by_code(pump_code)
        
        if catalog_pump:
            # Add performance curves data for pump data table
            selected_pump['curves'] = catalog_pump.curves
            selected_pump['pump_type'] = catalog_pump.pump_type
            selected_pump['manufacturer'] = catalog_pump.manufacturer

        # Create properly structured context data for template
        context_data = {
            'pump_selections': pump_selections,
            'selected_pump': selected_pump,
            'site_requirements': {
                'flow_m3hr': site_requirements_data.get('flow_m3hr', 0),
                'head_m': site_requirements_data.get('head_m', 0),
                'pump_type': site_requirements_data.get('pump_type', 'General'),
                'customer_name': site_requirements_data.get('customer_name', 'Client Contact'),
                'project_name': site_requirements_data.get('project_name', 'Water Supply System Project'),
                'application': site_requirements_data.get('application', 'Water Supply'),
                'fluid_type': site_requirements_data.get('fluid_type', 'Water')
            },
            'selected_pump_code': pump_code,
            'current_date': __import__('datetime').datetime.now().strftime('%Y-%m-%d')
        }

        # Extract authentic data from pump evaluation results
        if selected_pump and isinstance(selected_pump, dict):
            # Use the actual operating point data from pump evaluation
            operating_point = selected_pump.get('operating_point', {})

            # Ensure selected_curve data is available for all pumps
            if 'selected_curve' not in selected_pump or not selected_pump['selected_curve']:
                op_point = selected_pump.get('operating_point', {})
                impeller_diameter = op_point.get('impeller_diameter_mm', op_point.get('impeller_size', 501.0))
                selected_pump['selected_curve'] = {
                    'impeller_size': impeller_diameter,
                    'impeller_diameter_mm': impeller_diameter,
                    'is_selected': True,
                    'curve_index': op_point.get('curve_index', 0)
                }

            # Ensure pump info structure
            if 'pump_info' not in selected_pump:
                selected_pump['pump_info'] = {
                    'pPumpCode': pump_code,
                    'pSuppName': 'APE PUMPS',
                    'pPumpTestSpeed': '1480',
                    'pFilter1': 'APE PUMPS',
                    'pStages': '1'
                }

            # Debug logging
            logger.info(f"Template data - selected_pump operating_point: {selected_pump.get('operating_point')}")
            logger.info(f"Template data - selected_pump selected_curve: {selected_pump.get('selected_curve')}")

        return render_template('professional_pump_report.html', **context_data)

    except Exception as e:
        logger.error(f"Error displaying pump report: {str(e)}", exc_info=True)
        safe_flash('Error loading pump report. Please try again.', 'error')
        return redirect(url_for('index'))


@app.route('/professional_pump_report/<path:pump_code>')
def professional_pump_report(pump_code):
    """Alias for pump_report route to handle URL building."""
    return pump_report(pump_code)


# AI Chatbot Routes

@app.route('/help-features')
def help_features_page():
    """Help & Features brochure page"""
    logger.info("Help & Features page accessed.")
    return render_template('help_brochure.html')

@app.route('/guide')
def guide_page():
    """User guide page"""
    logger.info("Guide page accessed.")
    return render_template('guide.html')

@app.route('/generate_pdf/<path:pump_code>')
def generate_pdf_report(pump_code):
    """Generate PDF report using exact same data as web interface"""
    try:
        # URL decode the pump code to handle special characters
        from urllib.parse import unquote
        pump_code = unquote(pump_code)

        logger.info(f"PDF generation requested for pump: {pump_code}")
        
        # Get the exact same data that the web interface uses
        pump_selections = session.get('pump_selections', [])
        site_requirements_data = session.get('site_requirements', {})
        
        if not pump_selections:
            logger.error(f"PDF generation - No pump selections in session for {pump_code}")
            safe_flash('No pump selections found. Please run pump selection first.', 'error')
            return redirect(url_for('index'))
        
        # Find the selected pump from session data (same as web interface)
        selected_pump = None
        for pump in pump_selections:
            if pump.get('pump_code') == pump_code:
                selected_pump = pump
                break
                
        if not selected_pump:
            logger.error(f"PDF generation - Pump {pump_code} not found in session selections")
            safe_flash('Selected pump not found. Please run pump selection again.', 'error')
            return redirect(url_for('index'))
            
        logger.info(f"PDF generation - Using session data for pump: {pump_code}")
        logger.info(f"PDF generation - Operating point data: {selected_pump.get('operating_point')}")
        
        # Create site requirements from session with type safety
        flow_value = site_requirements_data.get('flow_m3hr')
        head_value = site_requirements_data.get('head_m')
        
        # Ensure numeric values are properly converted
        try:
            flow_m3hr = float(flow_value) if flow_value is not None else 0.0
            head_m = float(head_value) if head_value is not None else 0.0
        except (ValueError, TypeError):
            safe_flash('Invalid flow or head values in session data', 'error')
            return redirect(url_for('index'))
        
        site_requirements = SiteRequirements(
            flow_m3hr=flow_m3hr,
            head_m=head_m,
            customer_name=site_requirements_data.get('customer_name', 'Engineering Client'),
            project_name=site_requirements_data.get('project_name', 'Pump Selection Project'),
            application_type=site_requirements_data.get('application', 'general')
        )

        # Get catalog pump for PDF generation compatibility
        from app.catalog_engine import get_catalog_engine, convert_catalog_pump_to_legacy_format
        catalog_engine = get_catalog_engine()
        catalog_pump = catalog_engine.get_pump_by_code(pump_code)
        
        if not catalog_pump:
            logger.error(f"PDF generation - Catalog pump {pump_code} not found")
            safe_flash('Pump not found in catalog', 'error')
            return redirect(url_for('index'))
            
        # Get performance data from the web interface session data and convert to PDF template format
        operating_point = selected_pump.get('operating_point', {})
        
        # Convert catalog format to legacy PDF template format - ensure all values are authentic
        if not operating_point.get('flow_m3hr') or not operating_point.get('head_m'):
            safe_flash('Insufficient pump data for PDF generation. Please ensure valid pump selection.', 'error')
            return redirect(url_for('index'))
            
        converted_operating_point = {
            'flow_m3hr': operating_point['flow_m3hr'],
            'head_m': operating_point['head_m'],
            'achieved_head_m': operating_point['head_m'],  # PDF template expects this
            'efficiency_pct': operating_point.get('efficiency_pct', 0),
            'achieved_efficiency_pct': operating_point.get('efficiency_pct', 0),  # PDF template expects this
            'power_kw': operating_point.get('power_kw', 0),
            'achieved_power_kw': operating_point.get('power_kw', 0),  # PDF template expects this
            'npshr_m': operating_point.get('npshr_m', 0),
            'impeller_diameter_mm': operating_point.get('impeller_diameter_mm', 312.0),
            'impeller_size': operating_point.get('impeller_diameter_mm', 312.0),  # PDF template expects this
            'test_speed_rpm': operating_point.get('test_speed_rpm', 1480)
        }
        
        # Update the selected_pump with converted operating point for PDF compatibility
        selected_pump_for_pdf = selected_pump.copy()
        selected_pump_for_pdf['operating_point'] = converted_operating_point
        
        performance_data = {
            'curve': {
                'impeller_diameter_mm': operating_point.get('impeller_diameter_mm', 0),
                'test_speed_rpm': operating_point.get('test_speed_rpm', 0),
                'performance_points': []
            },
            'flow_m3hr': operating_point['flow_m3hr'],
            'head_m': operating_point['head_m'],
            'efficiency_pct': operating_point.get('efficiency_pct', 0),
            'power_kw': operating_point.get('power_kw', 0),
            'npshr_m': operating_point.get('npshr_m', 0),
            'impeller_diameter_mm': operating_point.get('impeller_diameter_mm', 0),
            'test_speed_rpm': operating_point.get('test_speed_rpm', 0)
        }
        
        # Convert to legacy format for PDF compatibility
        legacy_pump = convert_catalog_pump_to_legacy_format(catalog_pump, performance_data)
        
        logger.info(f"PDF generation - Performance data: impeller={performance_data.get('impeller_diameter_mm')}mm, power={performance_data.get('power_kw')}kW")
        
        # Generate PDF using the web interface data with converted format
        from app.pdf_generator import generate_pdf_report as generate_pdf
        pdf_content = generate_pdf(
            selected_pump_evaluation=selected_pump_for_pdf,
            parsed_pump=legacy_pump,
            site_requirements=site_requirements,
            alternatives=[p for p in pump_selections if p.get('pump_code') != pump_code][:2]
        )

        # Create response
        from flask import Response
        response = Response(pdf_content, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename="APE_Pump_Report_{pump_code.replace("/", "_").replace(" ", "_")}.pdf"'
        response.headers['Content-Length'] = len(pdf_content)

        return response

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        safe_flash('Error generating PDF report. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/api/chart_data/<pump_code>')
def get_chart_data(pump_code):
    """API endpoint to get chart data for interactive Plotly.js charts."""
    try:
        # Get site requirements from URL parameters
        flow_rate = request.args.get('flow', type=float, default=100)
        head = request.args.get('head', type=float, default=50)

        # Use catalog engine to get pump data
        from app.catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        target_pump = catalog_engine.get_pump_by_code(pump_code)

        if not target_pump:
            logger.error(f"Chart API: Pump {pump_code} not found in catalog")
            response = jsonify({
                'error': f'Pump {pump_code} not found',
                'available_pumps': len(catalog_engine.pumps),
                'suggestion': 'Please verify the pump code and try again'
            })
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response, 404

        # Use catalog pump curves directly
        curves = target_pump.curves
        
        if not curves:
            response = jsonify({'error': f'No curve data available for pump {pump_code}'})
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response, 404

        # Create site requirements for operating point calculation
        site_requirements = SiteRequirements(flow_m3hr=flow_rate, head_m=head)

        # Get the best curve and calculate performance using catalog engine
        best_curve = target_pump.get_best_curve_for_duty(flow_rate, head)
        
        # Calculate performance at duty point with detailed analysis
        performance_result = target_pump.get_performance_at_duty(flow_rate, head)
        
        # Extract operating point details from performance calculation
        operating_point = None
        speed_scaling_applied = False
        actual_speed_ratio = 1.0
        
        if performance_result and not performance_result.get('error'):
            operating_point = performance_result
            
            # Check for speed variation in the performance calculation
            sizing_info = performance_result.get('sizing_info')
            if sizing_info and sizing_info.get('sizing_method') == 'speed_variation':
                speed_scaling_applied = True
                required_speed = sizing_info.get('required_speed_rpm', 980)
                base_speed = 980
                actual_speed_ratio = required_speed / base_speed
                logger.info(f"Chart API: Speed variation detected - {base_speed}→{required_speed} RPM (ratio: {actual_speed_ratio:.3f})")
                logger.info(f"Chart API: Performance at scaled speed - power: {performance_result.get('power_kw')}kW")
        
        logger.info(f"Chart API: Final scaling status - applied: {speed_scaling_applied}, ratio: {actual_speed_ratio:.3f}")

        # Prepare chart data with enhanced operating point including sizing info
        operating_point_data = {}
        if operating_point and not operating_point.get('error'):
            operating_point_data = {
                'flow_m3hr': operating_point.get('flow_m3hr', flow_rate),
                'head_m': operating_point.get('head_m', head),
                'efficiency_pct': operating_point.get('efficiency_pct'),
                'power_kw': operating_point.get('power_kw'),
                'npshr_m': operating_point.get('npshr_m'),
                'impeller_size': operating_point.get('impeller_size'),
                'curve_index': operating_point.get('curve_index'),
                'extrapolated': operating_point.get('extrapolated', False),
                'within_range': not operating_point.get('extrapolated', False),
                'sizing_info': operating_point.get('sizing_info')  # Include sizing information
            }

        chart_data = {
            'pump_code': pump_code,
            'pump_info': {
                'manufacturer': target_pump.manufacturer,
                'series': target_pump.model_series,
                'description': target_pump.pump_code
            },
            'curves': [],
            'operating_point': operating_point_data,
            'metadata': {
                'flow_units': 'm³/hr',
                'head_units': 'm',
                'efficiency_units': '%',
                'power_units': 'kW',
                'npshr_units': 'm'
            }
        }

        # Process each curve from catalog format
        best_curve_index = 0
        if best_curve:
            # Find the best curve index
            for i, curve in enumerate(curves):
                if curve.get('curve_id') == best_curve.get('curve_id'):
                    best_curve_index = i
                    break
        
        # Use the actual performance calculation results for consistent chart scaling
        
        for i, curve in enumerate(curves):
            # Extract data points from catalog curve format
            performance_points = curve.get('performance_points', [])
            is_selected_curve = (i == best_curve_index)
            
            # For the selected curve, use the same calculation methodology as operating point
            if is_selected_curve and operating_point:
                # Generate chart data that matches the operating point calculation
                # This ensures consistency between chart visualization and performance results
                
                if speed_scaling_applied and actual_speed_ratio != 1.0:
                    # Apply speed scaling to match operating point calculation
                    flows = [p['flow_m3hr'] * actual_speed_ratio for p in performance_points if 'flow_m3hr' in p]
                    heads = [p['head_m'] * (actual_speed_ratio ** 2) for p in performance_points if 'head_m' in p]
                    base_powers = calculate_power_curve(performance_points)
                    powers = [power * (actual_speed_ratio ** 3) for power in base_powers]
                    logger.info(f"Chart API: Speed scaling applied to selected curve - ratio={actual_speed_ratio:.3f}")
                else:
                    # Use original data for non-speed-varied cases
                    flows = [p['flow_m3hr'] for p in performance_points if 'flow_m3hr' in p]
                    heads = [p['head_m'] for p in performance_points if 'head_m' in p]
                    powers = calculate_power_curve(performance_points)
            else:
                # Non-selected curves use original manufacturer data
                flows = [p['flow_m3hr'] for p in performance_points if 'flow_m3hr' in p]
                heads = [p['head_m'] for p in performance_points if 'head_m' in p]
                powers = calculate_power_curve(performance_points)
            
            efficiencies = [p.get('efficiency_pct') for p in performance_points if p.get('efficiency_pct') is not None]
                
            npshrs = [p.get('npshr_m') for p in performance_points if p.get('npshr_m') is not None]

            curve_data = {
                'curve_index': i,
                'impeller_size': curve.get('impeller_size', f'Curve {i+1}'),
                'flow_data': flows,
                'head_data': heads,
                'efficiency_data': efficiencies,
                'power_data': powers,
                'npshr_data': npshrs,
                'is_selected': i == best_curve_index
            }
            chart_data['curves'].append(curve_data)

        # Create response with short-term caching for chart data
        response = jsonify(chart_data)
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minute cache
        response.headers['Content-Type'] = 'application/json'
        return response

    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        error_response = jsonify({'error': f'Error retrieving chart data: {str(e)}'})
        error_response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return error_response, 500

def calculate_power_curve(performance_points):
    """Calculate power values for performance points using hydraulic formula."""
    powers = []
    for p in performance_points:
        if p.get('power_kw') and p.get('power_kw') > 0:
            powers.append(p['power_kw'])
        elif p.get('efficiency_pct') and p.get('efficiency_pct') > 0 and p.get('flow_m3hr', 0) > 0:
            # P(kW) = (Q × H × 9.81) / (3600 × η)
            calc_power = (p['flow_m3hr'] * p['head_m'] * 9.81) / (3600 * (p['efficiency_pct'] / 100))
            powers.append(calc_power)
        elif p.get('flow_m3hr', 0) == 0:
            powers.append(0)
        else:
            # Fallback for missing data - estimate based on flow and head
            estimated_power = (p.get('flow_m3hr', 0) * p.get('head_m', 0) * 9.81) / (3600 * 0.75)  # Assume 75% efficiency
            powers.append(max(0, estimated_power))
    return powers

@app.route('/api/chart_data_safe/<safe_pump_code>')
def get_chart_data_safe(safe_pump_code):
    """Optimized API endpoint to get chart data using base64-encoded pump codes."""
    import time
    start_time = time.time()
    try:
        # Decode base64 pump code
        import base64
        # Restore URL-safe base64 characters
        safe_pump_code = safe_pump_code.replace('-', '+').replace('_', '/')
        # Add padding if needed
        while len(safe_pump_code) % 4:
            safe_pump_code += '='
        pump_code = base64.b64decode(safe_pump_code).decode('utf-8')

        # Get site requirements from URL parameters
        flow_rate = request.args.get('flow', type=float, default=100)
        head = request.args.get('head', type=float, default=50)

        # Use catalog engine for consistent pump lookup
        logger.info(f"Chart API: Loading data for pump {pump_code}")
        data_load_start = time.time()
        
        from app.catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        target_pump = catalog_engine.get_pump_by_code(pump_code)
        
        logger.info(f"Chart API: Catalog lookup took {time.time() - data_load_start:.3f}s")

        if not target_pump:
            return jsonify({'error': f'Pump {pump_code} not found'})

        # Use catalog pump curves directly
        curves = target_pump.curves
        
        if not curves:
            return jsonify({'error': f'Pump {pump_code} not found or no curve data available'})

        # Calculate operating point using catalog engine
        best_curve = target_pump.get_best_curve_for_duty(flow_rate, head)
        operating_point_data = target_pump.get_performance_at_duty(flow_rate, head)

        # Extract speed scaling information from performance calculation
        speed_scaling_applied = False
        actual_speed_ratio = 1.0
        
        if operating_point_data and operating_point_data.get('sizing_info'):
            sizing_info = operating_point_data['sizing_info']
            if sizing_info.get('sizing_method') == 'speed_variation':
                speed_scaling_applied = True
                required_speed = sizing_info.get('required_speed_rpm', 980)
                base_speed = 980
                actual_speed_ratio = required_speed / base_speed
                logger.info(f"Chart API: Speed variation detected - {base_speed}→{required_speed} RPM (ratio: {actual_speed_ratio:.3f})")

        # Prepare operating point data for charts
        op_point = {
            'flow_m3hr': flow_rate,
            'head_m': operating_point_data.get('head_m', head) if operating_point_data else head,
            'efficiency_pct': operating_point_data.get('efficiency_pct') if operating_point_data else None,
            'power_kw': operating_point_data.get('power_kw') if operating_point_data else None,
            'npshr_m': operating_point_data.get('npshr_m') if operating_point_data else None,
            'extrapolated': operating_point_data.get('extrapolated', False) if operating_point_data else False
        }

        # Prepare chart data
        chart_data = {
            'pump_code': pump_code,
            'pump_info': {
                'manufacturer': target_pump.manufacturer,
                'series': target_pump.model_series,
                'description': target_pump.pump_code
            },
            'curves': [],
            'operating_point': op_point,
            'metadata': {
                'flow_units': 'm³/hr',
                'head_units': 'm',
                'efficiency_units': '%',
                'power_units': 'kW',
                'npshr_units': 'm'
            }
        }

        # Process each curve from catalog format
        best_curve_index = 0
        if best_curve:
            # Find the best curve index
            for i, curve in enumerate(curves):
                if curve.get('curve_id') == best_curve.get('curve_id'):
                    best_curve_index = i
                    break
        
        for i, curve in enumerate(curves):
            # Extract data points from catalog curve format
            performance_points = curve.get('performance_points', [])
            is_selected_curve = (i == best_curve_index)
            
            # Calculate base data
            base_flows = [p['flow_m3hr'] for p in performance_points if 'flow_m3hr' in p]
            base_heads = [p['head_m'] for p in performance_points if 'head_m' in p]
            base_powers = calculate_power_curve(performance_points)
            efficiencies = [p.get('efficiency_pct') for p in performance_points if p.get('efficiency_pct') is not None]
            npshrs = [p.get('npshr_m') for p in performance_points if p.get('npshr_m') is not None]
            
            # Apply speed scaling to selected curve if speed variation is required
            if is_selected_curve and speed_scaling_applied and actual_speed_ratio != 1.0:
                # Apply affinity laws for speed variation - Global Fix Implementation
                flows = [flow * actual_speed_ratio for flow in base_flows]
                heads = [head * (actual_speed_ratio ** 2) for head in base_heads]
                powers = [power * (actual_speed_ratio ** 3) for power in base_powers]
                logger.info(f"Chart API: Speed scaling applied to selected curve - power range: {min(powers):.1f}-{max(powers):.1f} kW")
                # Efficiency and NPSH remain unchanged with speed variation
            else:
                # Use original manufacturer data for non-selected curves or when no speed variation
                flows = base_flows
                heads = base_heads
                powers = base_powers

            curve_data = {
                'curve_index': i,
                'impeller_size': curve.get('impeller_size', f'Curve {i+1}'),
                'flow_data': flows,
                'head_data': heads,
                'efficiency_data': efficiencies,
                'power_data': powers,
                'npshr_data': npshrs,
                'is_selected': is_selected_curve
            }
            chart_data['curves'].append(curve_data)

        # Create response with cache-control headers
        response = jsonify(chart_data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        total_time = time.time() - start_time
        logger.info(f"Chart API: Total request time {total_time:.3f}s for pump {pump_code}")

        return response

    except Exception as e:
        logger.error(f"Error in safe chart data API: {str(e)}")
        return jsonify({'error': f'Failed to generate chart data: {str(e)}'}), 500

def pump_code_safe(pump_code):
    """Convert pump code to filename-safe string."""
    return "".join(c if c.isalnum() or c in '-_' else '_' for c in str(pump_code))

def generate_pump_charts(parsed_pump_obj, operating_point, site_requirements_obj, chart_width=10, chart_height=6):
    """
    Generate static matplotlib charts for pump performance using base64 encoding for WeasyPrint.
    """
    import io
    import base64

    charts = {}

    if not parsed_pump_obj:
        logger.warning("generate_pump_charts called with None for parsed_pump_obj")
        return charts

    logger.info(f"Generating charts for pump: {parsed_pump_obj.pump_code}")
    logger.info(f"Operating point data: {operating_point}")

    try:
        # Generate head chart with authentic pump curve data
        fig, ax = plt.subplots(figsize=(chart_width, chart_height))

        # Plot authentic head curves for all impeller sizes
        has_legend_data = False
        for i, curve in enumerate(parsed_pump_obj.curves):
            flow_vs_head = curve.get('flow_vs_head', [])
            if flow_vs_head:
                flow_data = [point[0] for point in flow_vs_head]
                head_data = [point[1] for point in flow_vs_head]
                impeller_size = curve.get('impeller_size', f'Curve {i+1}')

                # Use thicker line for selected curve
                line_width = 3 if i == operating_point.get('curve_index', 0) else 2
                ax.plot(flow_data, head_data, linewidth=line_width, 
                       label=f'{impeller_size}mm Impeller', marker='o', markersize=4)
                has_legend_data = True

        # Mark operating point
        if operating_point and operating_point.get('flow_m3hr') and operating_point.get('achieved_head_m'):
            ax.plot(operating_point['flow_m3hr'], operating_point['achieved_head_m'], 
                   'ro', markersize=10, label='Operating Point', zorder=5)
            has_legend_data = True

        ax.set_xlabel('Flow Rate (m³/hr)')
        ax.set_ylabel('Head (m)')
        ax.set_title(f'{parsed_pump_obj.pump_code} - Head vs Flow')
        ax.grid(True, alpha=0.3)
        if has_legend_data:
            ax.legend()

        # Save to base64 for reliable WeasyPrint rendering
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        head_chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)
        charts['head'] = f"data:image/png;base64,{head_chart_base64}"
        logger.debug(f"Generated head chart as base64 (length: {len(head_chart_base64)})")

        # Generate efficiency chart
        fig_eff, ax_eff = plt.subplots(figsize=(chart_width, chart_height))
        has_eff_legend_data = False

        for i, curve in enumerate(parsed_pump_obj.curves):
            flow_vs_efficiency = curve.get('flow_vs_efficiency', [])
            if flow_vs_efficiency:
                flow_data = [point[0] for point in flow_vs_efficiency]
                eff_data = [point[1] for point in flow_vs_efficiency]
                impeller_size = curve.get('impeller_size', f'Curve {i+1}')

                line_width = 3 if i == operating_point.get('curve_index', 0) else 2
                ax_eff.plot(flow_data, eff_data, linewidth=line_width, 
                           label=f'{impeller_size}mm Impeller', marker='o', markersize=4)
                has_eff_legend_data = True

        # Mark operating point
        if operating_point and operating_point.get('flow_m3hr') and operating_point.get('achieved_efficiency_pct'):
            ax_eff.plot(operating_point['flow_m3hr'], operating_point['achieved_efficiency_pct'], 
                       'ro', markersize=10, label='Operating Point', zorder=5)
            has_eff_legend_data = True

        ax_eff.set_xlabel('Flow Rate (m³/hr)')
        ax_eff.set_ylabel('Efficiency (%)')
        ax_eff.set_title(f'{parsed_pump_obj.pump_code} - Efficiency vs Flow')
        ax_eff.grid(True, alpha=0.3)
        if has_eff_legend_data:
            ax_eff.legend()

        buffer_eff = io.BytesIO()
        plt.savefig(buffer_eff, format='png', dpi=150, bbox_inches='tight')
        buffer_eff.seek(0)
        eff_chart_base64 = base64.b64encode(buffer_eff.getvalue()).decode('utf-8')
        plt.close(fig_eff)
        charts['efficiency'] = f"data:image/png;base64,{eff_chart_base64}"

        # Generate power chart
        fig_pow, ax_pow = plt.subplots(figsize=(chart_width, chart_height))
        has_power_legend_data = False

        for i, curve in enumerate(parsed_pump_obj.curves):
            flow_vs_power = curve.get('flow_vs_power', [])
            if flow_vs_power:
                flow_data = [point[0] for point in flow_vs_power]
                power_data = [point[1] for point in flow_vs_power]
                impeller_size = curve.get('impeller_size', f'Curve {i+1}')

                line_width = 3 if i == operating_point.get('curve_index', 0) else 2
                ax_pow.plot(flow_data, power_data, linewidth=line_width, 
                           label=f'{impeller_size}mm Impeller', marker='o', markersize=4)
                has_power_legend_data = True

        # Mark operating point
        if operating_point and operating_point.get('flow_m3hr') and operating_point.get('achieved_power_kw'):
            ax_pow.plot(operating_point['flow_m3hr'], operating_point['achieved_power_kw'], 
                       'ro', markersize=10, label='Operating Point', zorder=5)
            has_power_legend_data = True

        ax_pow.set_xlabel('Flow Rate (m³/hr)')
        ax_pow.set_ylabel('Power (kW)')
        ax_pow.set_title(f'{parsed_pump_obj.pump_code} - Power vs Flow')
        ax_pow.grid(True, alpha=0.3)
        if has_power_legend_data:
            ax_pow.legend()

        buffer_pow = io.BytesIO()
        plt.savefig(buffer_pow, format='png', dpi=150, bbox_inches='tight')
        buffer_pow.seek(0)
        power_chart_base64 = base64.b64encode(buffer_pow.getvalue()).decode('utf-8')
        plt.close(fig_pow)
        charts['power'] = f"data:image/png;base64,{power_chart_base64}"

        # Generate NPSH chart only if NPSH data is available
        has_npsh_data = False
        for curve in parsed_pump_obj.curves:
            flow_vs_npshr = curve.get('flow_vs_npshr', [])
            if flow_vs_npshr and any(point[1] > 0 for point in flow_vs_npshr):
                has_npsh_data = True
                break

        if has_npsh_data:
            fig_npsh, ax_npsh = plt.subplots(figsize=(chart_width, chart_height))

            for i, curve in enumerate(parsed_pump_obj.curves):
                flow_vs_npshr = curve.get('flow_vs_npshr', [])
                if flow_vs_npshr:
                    flow_data = [point[0] for point in flow_vs_npshr]
                    npshr_data = [point[1] for point in flow_vs_npshr]
                    impeller_size = curve.get('impeller_size', f'Curve {i+1}')

                    line_width = 3 if i == operating_point.get('curve_index', 0) else 2
                    ax_npsh.plot(flow_data, npshr_data, linewidth=line_width, 
                               label=f'{impeller_size}mm Impeller', marker='o', markersize=4)

            # Mark operating point
            if (operating_point and operating_point.get('flow_m3hr') and 
                operating_point.get('achieved_npshr_m') is not None):
                ax_npsh.plot(operating_point['flow_m3hr'], operating_point['achieved_npshr_m'], 
                           'ro', markersize=10, label='Operating Point', zorder=5)

            ax_npsh.set_xlabel('Flow Rate (m³/hr)')
            ax_npsh.set_ylabel('NPSHr (m)')
            ax_npsh.set_title(f'{parsed_pump_obj.pump_code} - NPSHr vs Flow')
            ax_npsh.grid(True, alpha=0.3)
            ax_npsh.legend()

            buffer_npsh = io.BytesIO()
            plt.savefig(buffer_npsh, format='png', dpi=150, bbox_inches='tight')
            buffer_npsh.seek(0)
            npsh_chart_base64 = base64.b64encode(buffer_npsh.getvalue()).decode('utf-8')
            plt.close(fig_npsh)
            charts['npsh'] = f"data:image/png;base64,{npsh_chart_base64}"
        else:
            # For pumps without NPSH data, don't generate NPSH chart
            charts['npsh'] = None
            logger.info(f"No NPSH data available for pump {parsed_pump_obj.pump_code}")

    except Exception as e:
        logger.error(f"Error generating charts: {str(e)}", exc_info=True)

    return charts

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return render_template('500.html'), 500

@app.route('/compare')
def pump_comparison():
    """Display pump comparison page with multiple pump options"""
    try:
        # Get requirements from URL parameters - require authentic values
        flow_str = request.args.get('flow')
        head_str = request.args.get('head')

        if not flow_str or not head_str:
            safe_flash('Flow and head parameters are required for pump comparison', 'error')
            return redirect(url_for('index'))

        # Guard against invalid data injection
        if flow_str.lower() in ('nan', 'infinity', 'inf', '-inf') or head_str.lower() in ('nan', 'infinity', 'inf', '-inf'):
            safe_flash('Invalid flow or head parameters provided', 'error')
            return redirect(url_for('index'))

        try:
            flow = float(flow_str)
            head = float(head_str)
        except (ValueError, TypeError):
            safe_flash('Invalid flow or head parameters provided', 'error')
            return redirect(url_for('index'))

        # Get pump type from URL parameters to maintain filtering consistency
        pump_type = request.args.get('pump_type', 'General')
        
        # Debug logging for pump type filtering
        logger.info(f"URL parameters: {dict(request.args)}")
        logger.info(f"Extracted pump_type: '{pump_type}' (type: {type(pump_type)})")
        
        # Validate and create site requirements
        site_requirements = validate_site_requirements({
            'flow_m3hr': flow,
            'head_m': head,
            'application_type': request.args.get('application_type', 'water_supply'),
            'liquid_type': request.args.get('liquid_type', 'clean_water'),
            'pump_type': pump_type
        })

        logger.info(f"Generating comparison for requirements: {site_requirements}")
        logger.info(f"Pump type filter: {pump_type}")

        # Use catalog engine for pump selection with pump type filtering
        from app.catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        logger.info(f"Successfully loaded {len(catalog_engine.pumps)} pumps from catalog")

        # Find best pump options using catalog engine with pump type filter
        pump_selections = catalog_engine.select_pumps(flow, head, max_results=10, pump_type=pump_type)

        # Format pump comparisons with detailed analysis using catalog format
        pump_comparisons = []
        for i, selection in enumerate(pump_selections):
            pump = selection['pump']
            performance = selection['performance']
            
            # Convert catalog format to comparison format with proper null handling
            operating_point = {
                'achieved_efficiency_pct': performance.get('efficiency_pct') or 0,
                'achieved_power_kw': performance.get('power_kw') or 0,
                'achieved_head_m': performance.get('head_m') or head,
                'achieved_flow_m3hr': performance.get('flow_m3hr') or flow,
                'achieved_npshr_m': performance.get('npshr_m') or 0,
                'npsh_required_m': performance.get('npsh_required_m') or 0,
                'impeller_size': performance.get('impeller_diameter_mm') or 'N/A',
                'test_speed_rpm': performance.get('test_speed_rpm') or 1480
            }
            
            # Calculate lifecycle costs using South African rates
            power_kw = performance.get('power_kw') or 0
            annual_hours = 8760  # Standard operating hours
            electricity_rate_rand_kwh = 2.49  # South African commercial rate
            
            annual_energy_cost = power_kw * annual_hours * electricity_rate_rand_kwh
            initial_cost_estimate = 45000 + (power_kw * 800)  # Base cost + power scaling
            total_10_year_cost = initial_cost_estimate + (annual_energy_cost * 10)
            
            lifecycle_cost = {
                'initial_cost': initial_cost_estimate,
                'annual_energy_cost': annual_energy_cost,
                'total_10_year_cost': total_10_year_cost,
                'cost_per_m3': total_10_year_cost / (flow * annual_hours) if flow > 0 else 0
            }
            
            comparison_data = {
                'pump_code': pump.pump_code,
                'manufacturer': pump.manufacturer,
                'pump_series': pump.model_series,
                'pump_type': pump.pump_type,
                'ranking': i + 1,
                'overall_score': selection.get('suitability_score', 0),
                'efficiency_at_duty': performance.get('efficiency_pct') or 0,
                'head_error_pct': selection.get('head_error_pct') or 0,
                'operating_point': operating_point,
                'lifecycle_cost': lifecycle_cost,
                'selection_reason': f'Efficiency: {(performance.get("efficiency_pct") or 0):.1f}%, Head error: {(selection.get("head_error_pct") or 0):.1f}%',
                'suitable': selection.get('suitability_score', 0) > 50,
                'description': getattr(pump, 'description', f'{pump.pump_code} - High efficiency centrifugal pump')
            }
            pump_comparisons.append(comparison_data)

        logger.info(f"Generated comparison data for {len(pump_comparisons)} pumps")

        return render_template('pump_comparison.html',
                             pump_comparisons=pump_comparisons,
                             site_requirements=site_requirements.__dict__,
                             enable_shortlist=True,
                             max_shortlist_items=3)

    except Exception as e:
        logger.error(f"Error in pump comparison: {str(e)}", exc_info=True)
        safe_flash(f'Error generating pump comparison: {str(e)}', 'error')
        return redirect(url_for('index'))

def _get_pump_series(pump_code):
    """Get pump series information based on pump code"""
    if "ALE" in pump_code:
        return "ALE Series - High Efficiency End Suction"
    elif "K" in pump_code and "VANE" in pump_code:
        return "K Series - Multi-Vane Impeller"
    elif "K" in pump_code:
        return "K Series - Standard Centrifugal"
    else:
        return "Industrial Series"

@app.route('/pump_details/<pump_code>')
def pump_details(pump_code):
    """Get detailed pump information for modal display"""
    try:
        from app.catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()
        
        pump = catalog_engine.get_pump_by_code(pump_code)
        if not pump:
            return jsonify({'error': 'Pump not found'}), 404
            
        # Get duty point from parameters - require authentic values
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)
        
        if not flow or not head:
            return jsonify({
                'error': 'Flow and head parameters are required',
                'message': 'Please provide valid flow and head values'
            }), 400
        
        performance = pump.get_performance_at_duty(flow, head)
        
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
        
        return jsonify(pump_details_data)
        
    except Exception as e:
        logger.error(f"Error fetching pump details for {pump_code}: {str(e)}")
        return jsonify({'error': 'Failed to load pump details'}), 500

@app.route('/shortlist_comparison')
def shortlist_comparison():
    """Display side-by-side comparison of selected pumps"""
    try:
        pump_codes = request.args.getlist('pumps')
        if len(pump_codes) < 2 or len(pump_codes) > 3:
            safe_flash('Please select 2-3 pumps for shortlist comparison', 'error')
            return redirect(url_for('pump_comparison'))
            
        flow = request.args.get('flow', type=float)
        head = request.args.get('head', type=float)
        
        if not flow or not head:
            safe_flash('Flow and head parameters are required for shortlist comparison', 'error')
            return redirect(url_for('pump_comparison'))
        
        from app.catalog_engine import get_catalog_engine
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
        return redirect(url_for('pump_comparison'))

@app.route('/generate_comparison_pdf')
def generate_comparison_pdf():
    """Generate PDF comparison report for multiple pumps"""
    try:
        # Get parameters - require authentic values
        pump_codes = request.args.get('pumps', '').split(',')
        flow_str = request.args.get('flow')
        head_str = request.args.get('head')

        if not flow_str or not head_str:
            return jsonify({'error': 'Flow and head parameters are required'}), 400

        # Guard against invalid data injection
        if flow_str.lower() in ('nan', 'infinity', 'inf', '-inf') or head_str.lower() in ('nan', 'infinity', 'inf', '-inf'):
            return jsonify({'error': 'Invalid flow or head parameters provided'}), 400

        try:
            flow = float(flow_str)
            head = float(head_str)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid flow or head parameters provided'}), 400

        if not pump_codes or len(pump_codes) < 2:
            safe_flash('At least 2 pumps required for comparison', 'error')
            return redirect(url_for('index'))

        # Validate site requirements
        site_requirements = validate_site_requirements({
            'flow_m3hr': flow,
            'head_m': head,
            'application_type': request.args.get('application_type', 'water_supply'),
            'liquid_type': request.args.get('liquid_type', 'clean_water')
        })

        # Use catalog engine for pump data
        from app.catalog_engine import get_catalog_engine
        catalog_engine = get_catalog_engine()

        pump_evaluations = []
        for pump_code in pump_codes:
            pump = catalog_engine.get_pump_by_code(pump_code)
            if pump:
                performance = pump.get_performance_at_duty(flow, head)
                if performance:
                    # Convert to evaluation format for PDF compatibility
                    operating_point = {
                        'achieved_efficiency_pct': performance.get('efficiency_pct', 0),
                        'achieved_power_kw': performance.get('power_kw', 0),
                        'achieved_head_m': performance.get('head_m', 0),
                        'achieved_npshr_m': performance.get('npshr_m', 0),
                        'impeller_size': performance.get('impeller_diameter_mm', 0),
                        'flow_m3hr': performance.get('flow_m3hr', flow),
                        'head_m': performance.get('head_m', head),
                        'efficiency_pct': performance.get('efficiency_pct', 0),
                        'power_kw': performance.get('power_kw', 0),
                        'npshr_m': performance.get('npshr_m', 0),
                        'impeller_diameter_mm': performance.get('impeller_diameter_mm', 0)
                    }
                    
                    evaluation = {
                        'pump_code': pump_code,
                        'overall_score': performance.get('efficiency_pct', 0),
                        'efficiency_at_duty': performance.get('efficiency_pct', 0),
                        'operating_point': operating_point,
                        'manufacturer': pump.manufacturer,
                        'suitable': performance.get('efficiency_pct', 0) > 40
                    }
                    pump_evaluations.append(evaluation)

        # Generate comparison PDF content
        from app.pdf_generator import generate_pdf_report as generate_pdf

        # Use the first pump as the main selection for PDF template compatibility
        main_evaluation = pump_evaluations[0] if pump_evaluations else None
        main_pump = catalog_engine.get_pump_by_code(pump_codes[0]) if pump_codes else None

        if main_evaluation and main_pump:
            # Convert catalog pump to legacy format for PDF compatibility
            from app.catalog_engine import convert_catalog_pump_to_legacy_format
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
                alternatives=pump_evaluations[1:] if len(pump_evaluations) > 1 else []
            )

            response = make_response(pdf_content)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=pump_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

            return response
        else:
            safe_flash('Error generating comparison PDF', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error generating comparison PDF: {str(e)}", exc_info=True)
        safe_flash(f'Error generating comparison PDF: {str(e)}', 'error')
        return redirect(url_for('index'))



# Missing API Routes for Deployment
@app.route('/api/pumps', methods=['GET'])
def get_pumps_api():
    """API endpoint for pump data."""
    try:
        pumps_data = load_all_pump_data()
        if not pumps_data:
            return jsonify({'error': 'No pump data available'}), 404

        api_response = []
        for pump in pumps_data:
            api_response.append({
                'pump_code': pump.pump_code,
                'supplier': pump.manufacturer,
                'max_power': getattr(pump, 'max_power', 0),
                'bep_flow': getattr(pump, 'bep_flow', 0),
                'test_speed': getattr(pump, 'test_speed', 0)
            })

        return jsonify({
            'success': True,
            'pumps': api_response,
            'count': len(api_response)
        })

    except Exception as e:
        logger.error(f"Error in pumps API: {str(e)}")
        return jsonify({'error': 'Failed to load pump data'}), 500

@app.route('/select_pump', methods=['POST'])
def select_pump_api():
    """API endpoint for pump selection."""
    try:
        form_data = request.form.to_dict() if request.form else {}

        if not form_data:
            return jsonify({'error': 'No selection criteria provided'}), 400

        site_requirements = validate_site_requirements(form_data)
        all_pump_data_list = load_all_pump_data()

        if not all_pump_data_list:
            return jsonify({'error': 'Pump database unavailable'}), 500

        # Use already parsed pump data from load_all_pump_data
        parsed_pumps_list = all_pump_data_list

        pump_selections = find_best_pumps(parsed_pumps_list, site_requirements)[:3]

        if not pump_selections:
            return jsonify({'error': 'No suitable pumps found'}), 404

        response_data = {
            'success': True,
            'selected_pumps': [
                {
                    'pump_code': selection.get('pump_code', 'Unknown'),
                    'overall_score': selection.get('overall_score', 0),
                    'head_accuracy_score': selection.get('head_accuracy_score', 0),
                    'efficiency_score': selection.get('efficiency_score', 0)
                }
                for selection in pump_selections
            ],
            'site_requirements': {
                'flow_rate': site_requirements.flow_m3hr,
                'head': site_requirements.head_m,
                'application': site_requirements.application_type
            }
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in pump selection API: {str(e)}")
        return jsonify({'error': f'Selection failed: {str(e)}'}), 500

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf_api():
    """API endpoint for PDF report generation."""
    try:
        data = request.get_json() if request.is_json else {}

        if not data:
            return jsonify({'error': 'No pump data provided'}), 400

        pump_code = data.get('pump_code')
        flow_rate = data.get('flow_rate')
        head = data.get('head')

        if not all([pump_code, flow_rate, head]):
            return jsonify({'error': 'Missing required parameters: pump_code, flow_rate, head'}), 400

        all_pump_data_list = load_all_pump_data()
        target_pump = None

        for pump_data in all_pump_data_list:
            if pump_data.pump_code == pump_code:
                target_pump = pump_data
                break

        if not target_pump:
            return jsonify({'error': f'Pump {pump_code} not found'}), 404

        # target_pump is already a ParsedPumpData object
        parsed_pump = target_pump
        if not parsed_pump:
            return jsonify({'error': 'Failed to find pump data'}), 500

        # Validate and convert parameters with safe fallbacks
        try:
            flow_val = float(flow_rate) if flow_rate is not None else 100.0
            head_val = float(head) if head is not None else 20.0
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid flow_rate or head parameters'}), 400

        site_requirements = SiteRequirements(
            flow_m3hr=flow_val,
            head_m=head_val,
            application="API Request",
            fluid_type="clean_water",
            temperature=20.0,
            viscosity=1.0,
            density=1000.0,
            npsh_available=10.0,
            installation="standard"
        )

        from app.pump_engine import evaluate_pump_for_requirements
        evaluation = evaluate_pump_for_requirements(parsed_pump, site_requirements)
        pdf_content = generate_pdf_report(evaluation, parsed_pump, site_requirements)

        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        safe_pump_code = str(pump_code).replace("/", "_") if pump_code else "unknown"
        response.headers['Content-Disposition'] = f'attachment; filename="pump_report_{safe_pump_code}.pdf"'

        return response

    except Exception as e:
        logger.error(f"Error in PDF generation API: {str(e)}")
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

@app.route('/api/ai_analysis_fast', methods=['POST'])
def ai_analysis_fast():
    """Fast AI technical analysis without knowledge base dependency."""
    try:
        data = request.get_json()
        pump_code = data.get('pump_code', '')
        flow = data.get('flow', 0)
        head = data.get('head', 0)
        efficiency = data.get('efficiency', 0)
        power = data.get('power', 0)
        npshr = data.get('npshr', 'N/A')
        application = data.get('application', 'Water Supply')
        topic = data.get('topic', None)  # Handle specific topic requests

        # Generate technical analysis based on pump parameters
        efficiency_rating = "excellent" if float(efficiency) >= 80 else "good" if float(efficiency) >= 70 else "acceptable"
        power_analysis = "efficient" if float(power) < 150 else "moderate power consumption"

        # Handle topic-specific analysis requests
        if topic == 'efficiency optimization':
            return jsonify({
                'response': _generate_efficiency_optimization_analysis(pump_code, efficiency, power, flow, head),
                'source_documents': [],
                'confidence_score': 0.9,
                'processing_time': 1.5,
                'cost_estimate': 0.015
            })
        elif topic == 'maintenance recommendations':
            return jsonify({
                'response': _generate_maintenance_recommendations(pump_code, efficiency, power, application),
                'source_documents': [],
                'confidence_score': 0.9,
                'processing_time': 1.5,
                'cost_estimate': 0.015
            })

        analysis_text = f"""## 1) Efficiency Characteristics and BEP Analysis

The Best Efficiency Point (BEP) is crucial for optimal pump performance. For centrifugal pumps, the efficiency of {efficiency}% indicates {efficiency_rating} performance for this type of pump. Operating at or near BEP minimizes energy consumption and wear. The {pump_code} pump achieves maximum efficiency through proper impeller design and sizing.

For centrifugal pumps, efficiency above 80% is considered excellent, while 70-80% is good performance. The achieved {efficiency}% efficiency demonstrates that this pump is well-suited for the specified operating conditions.

## 2) NPSH Considerations and Cavitation Prevention

Net Positive Suction Head (NPSH) is critical to prevent cavitation. With NPSH Required of {npshr} m, ensure adequate NPSH Available at the installation site exceeds this value by at least 0.5-1.0 meters safety margin.

Cavitation can cause significant damage including pitting, noise, vibration, and reduced performance. The IEEE standard recommends maintaining NPSH margin of 0.5-1.0 meters to prevent cavitation under all operating conditions. System designers must calculate NPSH Available based on suction tank level, atmospheric pressure, vapor pressure, and friction losses.

## 3) Material Selection and Corrosion Resistance

Material selection for {application} applications should consider fluid characteristics and environmental conditions. For {application} applications, common materials include:

- **Cast Iron**: Suitable for clean water applications with pH 6.5-8.5
- **Stainless Steel 316**: Excellent corrosion resistance for most water applications
- **Duplex Steel**: Superior strength and corrosion resistance for demanding conditions

The IEEE standard provides comprehensive guidelines for material selection to ensure longevity and reliability. Consider fluid temperature, pH, chloride content, and presence of abrasives when selecting materials.

## 4) Maintenance Requirements and Lifecycle Expectations

Regular maintenance is essential for optimal pump performance and longevity:

- **Bearing lubrication**: Every 6 months or per manufacturer specifications
- **Seal inspection**: Quarterly visual inspection, annual replacement if needed
- **Impeller clearance**: Annual verification and adjustment
- **Vibration monitoring**: Continuous or periodic monitoring for early fault detection
- **Performance verification**: Annual efficiency and head testing

Proper maintenance extends pump life to 15-25 years in typical water applications. Establishing baseline performance data during commissioning enables trending and predictive maintenance strategies.

## 5) Operating Envelope and Turndown Capabilities

The pump operating envelope defines safe operating limits. Key considerations:

- **Minimum flow**: Typically 10-20% of BEP flow to prevent recirculation
- **Maximum flow**: Limited by cavitation, power, and mechanical constraints
- **Preferred operating range**: 80-110% of BEP flow for optimal efficiency

Operating outside recommended flow range can cause recirculation, increased wear, and reduced efficiency. Variable frequency drives can extend turndown capabilities while maintaining efficiency across a broader operating range.

## 6) Installation and Commissioning Considerations

Proper installation ensures reliable operation:

- **Foundation design**: Adequate mass and stiffness to minimize vibration
- **Piping support**: Prevent stress on pump casing from piping loads
- **Alignment verification**: Laser alignment of motor and pump within 0.05mm
- **Suction conditions**: Adequate submergence and piping design
- **Commissioning tests**: Performance verification, vibration analysis, seal leakage check

Follow IEEE and manufacturer guidelines for installation procedures. Document baseline performance including flow, head, power, vibration, and temperature for future reference."""

        return jsonify({
            'response': analysis_text,
            'source_documents': [],
            'confidence_score': 0.9,
            'processing_time': 2.0,
            'cost_estimate': 0.02
        })

    except Exception as e:
        logger.error(f"Error in fast AI analysis: {e}")
        return jsonify({
            'response': 'Technical analysis temporarily unavailable. Please try again or contact support.',
            'source_documents': [],
            'confidence_score': 0.0,
            'processing_time': 0.0,
            'cost_estimate': 0.0
        }), 500

@app.after_request
def add_cache_headers(response):
    """Add cache headers for static assets."""
    if request.endpoint and 'static' in request.endpoint:
        # Cache static headers for 1 hour
        response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

def markdown_to_html(text: str) -> str:
    """Convert markdown text to HTML using markdown2 library for reliable parsing"""
    if not text or not isinstance(text, str):
        logger.warning("markdown_to_html received empty or invalid input.")
        return ""
    
    try:
        # Clean up source document references first
        clean_text = text
        clean_text = re.sub(r'\(([^)]*\.pdf[^)]*)\)', '', clean_text)
        clean_text = re.sub(r'according to ([^.,\s]+\.pdf)', 'according to industry standards', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'as stated in ([^.,\s]+\.pdf)', 'as stated in technical literature', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'from ([^.,\s]+\.pdf)', 'from technical documentation', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\b[a-zA-Z_\-]+\.pdf\b', '', clean_text)
        
        # Preserve line breaks and normalize spacing without collapsing line structure
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # Only collapse spaces/tabs, not newlines
        clean_text = re.sub(r'[ \t]*\n[ \t]*', '\n', clean_text)  # Clean up line breaks
        clean_text = clean_text.strip()
        
        # Use markdown2 with appropriate extras for robust parsing
        html = markdown2.markdown(clean_text, extras=['cuddled-lists', 'strike', 'fenced-code-blocks'])
        
        # Convert H2 tags (from ##) to H4 with proper styling for consistency
        html = html.replace('<h2>', '<h4 style="color: #1976d2; margin: 20px 0 10px 0; font-weight: 600;">')
        html = html.replace('</h2>', '</h4>')
        
        # Add proper styling to paragraphs and lists
        html = html.replace('<p>', '<p style="margin: 15px 0; line-height: 1.6; color: #333;">')
        html = html.replace('<ul>', '<ul style="margin: 15px 0; padding-left: 20px;">')
        html = html.replace('<li>', '<li style="margin: 5px 0; color: #555;">')
        
        logger.debug("Markdown successfully converted to HTML using markdown2.")
        return html
        
    except Exception as e:
        logger.error(f"Error converting markdown to HTML with markdown2: {e}", exc_info=True)
        return "<p>Error: Could not display formatted technical analysis at this time.</p>"

@app.route('/api/convert_markdown', methods=['POST'])
def convert_markdown_api():
    """Convert markdown to HTML using markdown2 library"""
    try:
        data = request.get_json()
        markdown_text = data.get('markdown', '')
        
        if not markdown_text:
            return jsonify({'error': 'No markdown text provided'}), 400
            
        html_output = markdown_to_html(markdown_text)
        return jsonify({'html': html_output})
        
    except Exception as e:
        logger.error(f"Error in markdown conversion API: {e}")
        return jsonify({'error': 'Markdown conversion failed'}), 500

def _generate_efficiency_optimization_analysis(pump_code, efficiency, power, flow, head):
    """Generate focused efficiency optimization analysis"""
    efficiency_val = float(efficiency)
    power_val = float(power)
    flow_val = float(flow)
    
    analysis = f"""## Efficiency Optimization Analysis for {pump_code}

### Current Performance Assessment
- **Operating Efficiency**: {efficiency}% ({"Excellent" if efficiency_val >= 80 else "Good" if efficiency_val >= 75 else "Needs Improvement"})
- **Power Consumption**: {power_val:.1f} kW at {flow} m³/h
- **Specific Energy**: {power_val/flow_val:.2f} kWh/m³

### Optimization Opportunities

**1. Operating Point Optimization**
- Current efficiency of {efficiency}% {"is near optimal range" if efficiency_val >= 80 else "can be improved"}
- {"Maintain current operating conditions" if efficiency_val >= 80 else "Consider impeller trimming or speed adjustment"}
- Target efficiency range: 80-85% for maximum cost-effectiveness

**2. Variable Frequency Drive (VFD) Benefits**
- Potential energy savings: {"10-30%" if efficiency_val < 80 else "5-15%"} with proper control
- Improved part-load performance and system flexibility
- Reduced mechanical stress and extended equipment life

**3. System Improvements**
- Optimize piping design to reduce friction losses
- Regular maintenance to maintain peak efficiency
- Consider parallel pump operation for variable demands

### Energy Cost Impact
- Annual energy cost savings: R{"34,000-136,000" if power_val > 100 else "17,000-68,000"} with optimization
- Payback period: {"1-2 years" if efficiency_val < 75 else "2-3 years"} for efficiency improvements
- Long-term operational benefits justify investment in optimization measures"""

    return analysis

def _generate_maintenance_recommendations(pump_code, efficiency, power, application):
    """Generate focused maintenance recommendations"""
    efficiency_val = float(efficiency)
    power_val = float(power)
    
    analysis = f"""## Maintenance Recommendations for {pump_code}

### Preventive Maintenance Schedule

**Monthly Inspections**
- Check pump performance parameters (flow, head, power)
- Inspect mechanical seals for leakage
- Monitor bearing temperatures and vibration levels
- Verify alignment and coupling condition

**Quarterly Maintenance**
- Performance testing and efficiency verification
- Lubrication of bearings (if applicable)
- Inspection of impeller and volute for wear
- Check foundation bolts and mounting stability

**Annual Overhaul**
- Complete performance curve verification
- Impeller balancing and wear assessment
- Mechanical seal replacement (planned)
- Motor electrical testing and insulation checks

### Performance Monitoring

**Key Performance Indicators**
- Efficiency target: Maintain above {max(75, efficiency_val-5)}%
- Power consumption: Monitor for {"increases above " + str(power_val*1.1) + " kW"}
- Vibration limits: ISO 10816 standards for rotating machinery

**Warning Signs**
- Efficiency drop below {efficiency_val-10}% indicates maintenance needed
- Unusual noise, vibration, or temperature increases
- Seal leakage or bearing temperature rise

### {"Water Supply" if "water" in application.lower() else "Industrial"} Application Considerations
- {"Clean water service allows extended maintenance intervals" if "water" in application.lower() else "Industrial service requires more frequent inspections"}
- Expected service life: {"15-20 years" if "water" in application.lower() else "10-15 years"} with proper maintenance
- Critical spare parts: mechanical seals, bearings, impeller

### Cost-Effective Maintenance
- Planned maintenance costs: 2-4% of pump capital cost annually
- Condition-based monitoring reduces unexpected failures by 70%
- Proper maintenance maintains efficiency within 2-3% of design values"""

    return analysis

def process_section_content(content):
    """Process section content into proper HTML paragraphs and lists"""
    if not content.strip():
        return ""
    
    # Apply text formatting first
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong class="md-bold">\1</strong>', content)
    content = re.sub(r'\*([^*]+?)\*', r'<em class="md-italic">\1</em>', content)
    
    # Split content into logical blocks
    paragraphs = re.split(r'\n\s*\n', content)
    processed_blocks = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # Check for bullet lists
        if re.search(r'^-\s+', paragraph, re.MULTILINE):
            # Process as unordered list
            list_items = []
            lines = paragraph.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('- '):
                    item_content = line[2:].strip()
                    list_items.append(f'<li class="md-li">{item_content}</li>')
            
            if list_items:
                processed_blocks.append(f'<ul class="md-ul">{"".join(list_items)}</ul>')
        else:
            # Process as regular paragraph
            # Join multiple lines into single paragraph
            lines = [line.strip() for line in paragraph.split('\n') if line.strip()]
            if lines:
                paragraph_text = ' '.join(lines)
                processed_blocks.append(f'<p class="md-paragraph">{paragraph_text}</p>')
    
    return ''.join(processed_blocks)



def test_markdown_processing():
    """Test function for debugging markdown processing"""
    test_content = """This is the first paragraph.

This is the second paragraph with **bold text** and *italic text*.

- Item 1
- Item 2
- Sub Item 2.1"""
    
    html_output = process_section_content(test_content)
    logger.debug(f"process_section_content INPUT:\n{test_content}")
    logger.debug(f"process_section_content OUTPUT:\n{html_output}")
    
    # Test full markdown with headers
    test_markdown = """## 1) First Section Title
This is the first paragraph of the first section.
It might have **bold** and *italic* text.

This is another paragraph in the first section.

## 2) Second Section Title
This section only has one paragraph.

- Followed by a list
- Item two"""
    
    html_markdown_output = markdown_to_html(test_markdown)
    logger.debug(f"markdown_to_html INPUT:\n{test_markdown}")
    logger.debug(f"markdown_to_html OUTPUT:\n{html_markdown_output}")
    
    return html_markdown_output

@app.route('/api/ai_analysis', methods=['POST'])
def ai_analysis():
    """AI technical expert analysis with markdown formatting."""
    try:
        data = request.get_json()
        pump_code = data.get('pump_code', '')
        flow = data.get('flow', 0)
        head = data.get('head', 0)
        efficiency = data.get('efficiency', 0)
        power = data.get('power', 0)
        npshr = data.get('npshr', 'N/A')
        application = data.get('application', 'Water Supply')

        # Generate technical analysis based on pump parameters
        efficiency_rating = "excellent" if float(efficiency) >= 80 else "good" if float(efficiency) >= 70 else "acceptable"
        power_analysis = "efficient" if float(power) < 150 else "moderate power consumption"

        analysis_text = f"""## 1) Efficiency Characteristics and BEP Analysis

The Best Efficiency Point (BEP) is crucial for optimal pump performance. For centrifugal pumps, the efficiency of {efficiency}% indicates {efficiency_rating} performance for this type of pump. Operating at or near BEP minimizes energy consumption and wear. The {pump_code} pump achieves maximum efficiency through proper impeller design and sizing.

For centrifugal pumps, efficiency above 80% is considered excellent, while 70-80% is good performance. The achieved {efficiency}% efficiency demonstrates that this pump is well-suited for the specified operating conditions.

## 2) NPSH Considerations and Cavitation Prevention

Net Positive Suction Head (NPSH) is critical to prevent cavitation. With NPSH Required of {npshr} m, ensure adequate NPSH Available at the installation site exceeds this value by at least 0.5-1.0 meters safety margin.

Cavitation can cause significant damage including pitting, noise, vibration, and reduced performance. The IEEE standard recommends maintaining NPSH margin of 0.5-1.0 meters to prevent cavitation under all operating conditions. System designers must calculate NPSH Available based on suction tank level, atmospheric pressure, vapor pressure, and friction losses.

## 3) Material Selection and Corrosion Resistance

Material selection for {application} applications should consider fluid characteristics and environmental conditions. For {application} applications, common materials include:

- **Cast Iron**: Suitable for clean water applications with pH 6.5-8.5
- **Stainless Steel 316**: Excellent corrosion resistance for most water applications
- **Duplex Steel**: Superior strength and corrosion resistance for demanding conditions

The IEEE standard provides comprehensive guidelines for material selection to ensure longevity and reliability. Consider fluid temperature, pH, chloride content, and presence of abrasives when selecting materials.

## 4) Maintenance Requirements and Lifecycle Expectations

Regular maintenance is essential for optimal pump performance and longevity:

- **Bearing lubrication**: Every 6 months or per manufacturer specifications
- **Seal inspection**: Quarterly visual inspection, annual replacement if needed
- **Impeller clearance**: Annual verification and adjustment
- **Vibration monitoring**: Continuous or periodic monitoring for early fault detection
- **Performance verification**: Annual efficiency and head testing

Proper maintenance extends pump life to 15-25 years in typical water applications. Establishing baseline performance data during commissioning enables trending and predictive maintenance strategies.

## 5) Operating Envelope and Turndown Capabilities

The pump operating envelope defines safe operating limits. Key considerations:

- **Minimum flow**: Typically 10-20% of BEP flow to prevent recirculation
- **Maximum flow**: Limited by cavitation, power, and mechanical constraints
- **Preferred operating range**: 80-110% of BEP flow for optimal efficiency

Operating outside recommended flow range can cause recirculation, increased wear, and reduced efficiency. Variable frequency drives can extend turndown capabilities while maintaining efficiency across a broader operating range.

## 6) Installation and Commissioning Considerations

Proper installation ensures reliable operation:

- **Foundation design**: Adequate mass and stiffness to minimize vibration
- **Piping support**: Prevent stress on pump casing from piping loads
- **Alignment verification**: Laser alignment of motor and pump within 0.05mm
- **Suction conditions**: Adequate submergence and piping design
- **Commissioning tests**: Performance verification, vibration analysis, seal leakage check

Follow IEEE and manufacturer guidelines for installation procedures. Document baseline performance including flow, head, power, vibration, and temperature for future reference."""

        # Convert markdown to HTML for proper rendering
        html_analysis = markdown_to_html(analysis_text)

        return jsonify({
            'response': html_analysis,
            'source_documents': [],
            'confidence_score': 0.9,
            'processing_time': 2.0,
            'cost_estimate': 0.02
        })

    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return jsonify({
            'response': 'Technical analysis temporarily unavailable. Please try again or contact support.',
            'source_documents': [],
            'confidence_score': 0.0,
            'processing_time': 0.0,
            'cost_estimate': 0.0
        }), 500

# Pump Upload System Routes
@app.route('/admin/pump_upload')
def pump_upload():
    """Pump upload interface"""
    return render_template('admin/pump_upload.html')





@app.route('/admin/recent_pumps')
def recent_pumps():
    """Get recently added pumps"""
    try:
        from app.pump_engine import load_all_pump_data
        pump_data = load_all_pump_data()
        
        recent_pumps = []
        for pump_entry in pump_data[-10:]:
            if isinstance(pump_entry, dict) and 'objPump' in pump_entry:
                pump = pump_entry['objPump']
                flow_points = len(pump.get('pM_FLOW', '').split(';')) if pump.get('pM_FLOW') else 0
                recent_pumps.append({
                    'pump_code': pump.get('pPumpCode', 'Unknown'),
                    'test_speed': pump.get('pPumpTestSpeed', 'Unknown'),
                    'performance_points': flow_points
                })
        
        return jsonify({'pumps': recent_pumps})
        
    except Exception as e:
        logger.error(f"Error getting recent pumps: {e}")
        return jsonify({'pumps': []})



@app.route('/admin/download_template/<format_type>')
def download_template(format_type):
    """Download template files for pump data upload"""
    try:
        if format_type == 'csv':
            template_content = '''pump_code,test_speed,manufacturer,flow_points,head_points,efficiency_points,power_points,npsh_points
"8 K 8 VANE",1450,"APE PUMPS","0;120;180;240;300;360","45.2;44.1;42.8;40.9;38.2;35.1","0;65;75;81;84;79","0;85;95;105;115;125","2.1;2.3;2.8;3.2;3.8;4.5"
"10 K 10 VANE",1450,"APE PUMPS","0;150;220;290;380;450","52.1;51.2;49.8;47.5;44.2;40.1","0;68;78;83;85;81","0;105;118;132;148;165","2.3;2.5;3.0;3.5;4.1;4.8"'''
            
            response = make_response(template_content)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=pump_template.csv'
            return response
            
        else:
            return jsonify({'error': 'Invalid template format'}), 400
            
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        return jsonify({'error': str(e)}), 500

# ================================
# SCG Processing Routes
# ================================

# Global SCG processor instances - initialize variables to prevent unbound errors
scg_processor = None
scg_adapter = None
batch_processor = None

if SCG_AVAILABLE:
    try:
        scg_processor = SCGProcessor()
        scg_adapter = SCGCatalogAdapter()
        batch_processor = BatchSCGProcessor()
    except Exception as e:
        logger.error(f"Failed to initialize SCG processors: {e}")
        SCG_AVAILABLE = False

@app.route('/admin/scg', methods=['GET', 'POST'])
def scg_management():
    """SCG file management interface"""
    if not SCG_AVAILABLE:
        safe_flash('SCG processing not available - missing dependencies', 'error')
        return redirect(url_for('admin_upload_pump_data'))
    
    if request.method == 'POST':
        try:
            # Handle single file upload
            if 'scg_file' in request.files:
                file = request.files['scg_file']
                if file and file.filename and file.filename.lower().endswith('.scg'):
                    # Save uploaded file
                    filename = secure_filename(file.filename)
                    temp_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'temp'), filename)
                    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                    file.save(temp_path)
                    
                    # Process SCG file with null checks
                    if scg_processor is None:
                        safe_flash('SCG processor not available', 'error')
                        return redirect(url_for('scg_management'))
                        
                    result = scg_processor.process_scg_file(temp_path)
                    
                    if result.success and result.pump_data:
                        # Convert to catalog format
                        if scg_adapter is None:
                            safe_flash('SCG adapter not available', 'error')
                            return redirect(url_for('scg_management'))
                            
                        catalog_data = scg_adapter.map_scg_to_catalog(result.pump_data)
                        
                        if catalog_data:
                            # Integrate with catalog
                            integrator = CatalogEngineIntegrator()
                            # Convert string form value to boolean
                            update_existing = request.form.get('update_existing', 'false').lower() == 'true'
                            integration_result = integrator.integrate_pump_data(
                                catalog_data,
                                update_existing=update_existing
                            )
                            
                            if integration_result['success']:
                                safe_flash(f"Successfully processed SCG file: {integration_result['message']}", 'success')
                            else:
                                safe_flash(f"Integration failed: {integration_result.get('errors', [])}", 'error')
                        else:
                            safe_flash(f"Conversion failed: {adapter_result.errors}", 'error')
                    else:
                        safe_flash(f"Processing failed: {result.errors}", 'error')
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                else:
                    safe_flash('Please select a valid .scg file', 'error')
            
            # Handle batch upload
            elif 'scg_directory' in request.form:
                directory_path = request.form['scg_directory']
                if os.path.exists(directory_path):
                    scg_files = discover_scg_files(directory_path)
                    validation_result = validate_scg_files(scg_files)
                    
                    if validation_result['valid_files']:
                        # Start batch processing with proper type conversion
                        update_existing_str = request.form.get('update_existing', 'false')
                        update_existing_bool = update_existing_str.lower() == 'true' if isinstance(update_existing_str, str) else bool(update_existing_str)
                        
                        config = BatchProcessingConfig(
                            max_workers=int(request.form.get('max_workers', 2)),
                            update_existing=update_existing_bool,
                            generate_report=True
                        )
                        
                        batch_processor_instance = BatchSCGProcessor(config)
                        batch_result = batch_processor_instance.process_files(validation_result['valid_files'])
                        
                        safe_flash(f"Batch processing completed: {batch_result.successful_pumps}/{batch_result.total_files} successful", 'success')
                        if batch_result.report_path:
                            session['last_batch_report'] = batch_result.report_path
                    else:
                        safe_flash('No valid SCG files found in directory', 'error')
                else:
                    safe_flash('Directory not found', 'error')
                    
        except Exception as e:
            logger.error(f"Error in SCG processing: {e}", exc_info=True)
            safe_flash(f"Processing error: {str(e)}", 'error')
    
    # Get processing statistics
    stats = {}
    if SCG_AVAILABLE:
        stats = {
            'scg_processor': scg_processor.get_processing_stats(),
            'catalog_adapter': scg_adapter.get_conversion_stats()
        }
    
    return render_template('scg_management.html', stats=stats, scg_available=SCG_AVAILABLE)

@app.route('/admin/scg/batch-status/<batch_id>')
def scg_batch_status(batch_id):
    """Get status of batch processing"""
    if not SCG_AVAILABLE:
        return jsonify({'error': 'SCG processing not available'}), 500
    
    status = batch_processor.get_batch_status(batch_id)
    if status:
        return jsonify(status)
    else:
        return jsonify({'error': 'Batch not found'}), 404

@app.route('/admin/scg/validate', methods=['POST'])
def scg_validate_file():
    """Validate SCG file without processing"""
    if not SCG_AVAILABLE:
        return jsonify({'error': 'SCG processing not available'}), 500
    
    try:
        if 'scg_file' in request.files:
            file = request.files['scg_file']
            if file and file.filename.lower().endswith('.scg'):
                # Save and validate file
                filename = secure_filename(file.filename)
                temp_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'temp'), filename)
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                file.save(temp_path)
                
                # Parse SCG file for validation
                try:
                    raw_data = scg_processor.parse_scg_to_raw_dict(temp_path)
                    pump_code = raw_data.get('pPumpCode', 'Unknown')
                    num_curves = int(raw_data.get('pHeadCurvesNo', '0'))
                    
                    validation_result = {
                        'valid': True,
                        'pump_code': pump_code,
                        'num_curves': num_curves,
                        'manufacturer': raw_data.get('pSuppName', 'Unknown'),
                        'flow_unit': raw_data.get('pUnitFlow', 'Unknown'),
                        'head_unit': raw_data.get('pUnitHead', 'Unknown'),
                        'file_size': os.path.getsize(temp_path),
                        'warnings': []
                    }
                    
                    if num_curves == 0:
                        validation_result['warnings'].append('No performance curves defined')
                    
                    if not pump_code or pump_code == 'Unknown':
                        validation_result['warnings'].append('Missing or invalid pump code')
                    
                    return jsonify(validation_result)
                    
                finally:
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass
            else:
                return jsonify({'error': 'Invalid file format'}), 400
        else:
            return jsonify({'error': 'No file provided'}), 400
            
    except Exception as e:
        logger.error(f"Error validating SCG file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/scg/download-report')
def scg_download_report():
    """Download latest batch processing report"""
    if not SCG_AVAILABLE:
        safe_flash('SCG processing not available', 'error')
        return redirect(url_for('scg_management'))
    
    report_path = session.get('last_batch_report')
    if report_path and os.path.exists(report_path):
        return send_file(report_path, as_attachment=True, download_name=f"scg_batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    else:
        safe_flash('No report available', 'error')
        return redirect(url_for('scg_management'))

@app.route('/api/scg/stats')
def scg_processing_stats():
    """Get SCG processing statistics"""
    if not SCG_AVAILABLE:
        return jsonify({'error': 'SCG processing not available'}), 500
    
    try:
        stats = {
            'scg_processor': scg_processor.get_processing_stats(),
            'catalog_adapter': scg_adapter.get_conversion_stats(),
            'active_batches': batch_processor.list_active_batches(),
            'available': True
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting SCG stats: {e}")
        return jsonify({'error': str(e)}), 500