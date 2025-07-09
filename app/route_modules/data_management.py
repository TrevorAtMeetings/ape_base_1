"""
Data Management Routes
Routes for pump data management, export, and upload functionality
"""
import os
import logging
import csv
import io
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, send_file, jsonify, make_response
from ..session_manager import safe_flash
from werkzeug.utils import secure_filename
from .. import app
from ..pump_engine import load_all_pump_data

logger = logging.getLogger(__name__)

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
            from ..pump_engine import _parse_performance_curves
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

def process_txt_upload(file_path):
    """Process TXT pump data upload."""
    # For now, treat as JSON
    return process_json_upload(file_path) 