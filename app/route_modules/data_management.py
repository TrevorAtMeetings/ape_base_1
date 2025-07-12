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
from flask import Blueprint, render_template, request, redirect, url_for, send_file, jsonify, make_response
from ..session_manager import safe_flash
from werkzeug.utils import secure_filename
from ..pump_repository import load_all_pump_data

logger = logging.getLogger(__name__)

# Create blueprint
data_management_bp = Blueprint('data_management', __name__)

@data_management_bp.route('/data-management')
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
            filtered_pumps = [p for p in filtered_pumps if search.lower() in p.get('pump_code', '').lower()]
        
        if category != 'all':
            if category == 'END_SUCTION':
                filtered_pumps = [p for p in filtered_pumps 
                                if not any(x in p.get('pump_code', '').upper() for x in ['2F', '2P', '3P', '4P', '6P', '8P', 'ALE', 'HSC'])]
            elif category == 'MULTI_STAGE':
                filtered_pumps = [p for p in filtered_pumps 
                                if any(x in p.get('pump_code', '').upper() for x in ['2F', '2P', '3P', '4P', '6P', '8P'])]
            elif category == 'AXIAL_FLOW':
                filtered_pumps = [p for p in filtered_pumps if 'ALE' in p.get('pump_code', '').upper()]
            elif category == 'HSC':
                filtered_pumps = [p for p in filtered_pumps if 'HSC' in p.get('pump_code', '').upper()]
        
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
            
            # Parse curves from pump data (now a dictionary)
            from ..utils import _parse_performance_curves
            # Convert pump data to legacy format for compatibility
            pump_info = {
                'pM_FLOW': ';'.join(str(p['flow_m3hr']) for p in pump.get('performance_points', [])),
                'pM_HEAD': ';'.join(str(p['head_m']) for p in pump.get('performance_points', [])),
                'pM_EFF': ';'.join(str(p['efficiency_pct']) for p in pump.get('performance_points', [])),
                'pM_NP': ';'.join(str(p.get('npshr_m', 0)) for p in pump.get('performance_points', [])),
                'pM_IMP': str(pump.get('impeller_diameter_mm', 0))
            }
            curves = _parse_performance_curves(pump_info)
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
                'pump_code': pump.get('pump_code', ''),
                'manufacturer': pump.get('manufacturer', ''),
                'model': pump.get('model', ''),
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
        return redirect(url_for('main_flow.index'))

@data_management_bp.route('/export-csv')
def export_csv():
    """Export pump data to CSV format."""
    try:
        # Load all pump data
        all_pumps = load_all_pump_data()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write simplified header for new data format
        writer.writerow([
            'Pump Code', 'Manufacturer', 'Model', 'Test Speed (RPM)',
            'Max Flow (m³/hr)', 'Min Flow (m³/hr)', 'Flow Range (m³/hr)',
            'Max Head (m)', 'Min Head (m)', 'Head Range (m)',
            'Max Efficiency (%)', 'Min Efficiency (%)', 'Efficiency Range (%)',
            'Has NPSH Data', 'Max NPSH (m)', 'Min NPSH (m)',
            'Impeller Diameter (mm)', 'Performance Points Count'
        ])
        
        # Write pump data in new format
        for pump in all_pumps:
            # Extract basic data
            pump_code = pump.get('pump_code', '')
            manufacturer = pump.get('manufacturer', '')
            model = pump.get('model', '')
            test_speed = pump.get('test_speed_rpm', 'N/A')
            impeller_diameter = pump.get('impeller_diameter_mm', 'N/A')
            
            # Extract performance points
            performance_points = pump.get('performance_points', [])
            
            # Calculate statistics
            flows = [p['flow_m3hr'] for p in performance_points if p.get('flow_m3hr', 0) > 0]
            heads = [p['head_m'] for p in performance_points if p.get('head_m', 0) > 0]
            efficiencies = [p['efficiency_pct'] for p in performance_points if p.get('efficiency_pct', 0) > 0]
            npshrs = [p.get('npshr_m', 0) for p in performance_points if p.get('npshr_m', 0) > 0]
            
            # Calculate ranges
            max_flow = max(flows) if flows else 0
            min_flow = min(flows) if flows else 0
            flow_range = max_flow - min_flow if flows else 0
            
            max_head = max(heads) if heads else 0
            min_head = min(heads) if heads else 0
            head_range = max_head - min_head if heads else 0
            
            max_efficiency = max(efficiencies) if efficiencies else 0
            min_efficiency = min(efficiencies) if efficiencies else 0
            eff_range = max_efficiency - min_efficiency if efficiencies else 0
            
            max_npshr = max(npshrs) if npshrs else 0
            min_npshr = min(npshrs) if npshrs else 0
            
            # Write row
            writer.writerow([
                pump_code,
                manufacturer,
                model,
                test_speed,
                max_flow, min_flow, flow_range,
                max_head, min_head, head_range,
                max_efficiency, min_efficiency, eff_range,
                'Yes' if npshrs else 'No',
                max_npshr, min_npshr,
                impeller_diameter,
                len(performance_points)
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

@data_management_bp.route('/upload-pump-data', methods=['POST'])
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
        upload_dir = os.path.join('app/static/temp', 'uploads')
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