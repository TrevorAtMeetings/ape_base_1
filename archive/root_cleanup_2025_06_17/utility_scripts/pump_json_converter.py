#!/usr/bin/env python3
"""
APE Pumps JSON Data Converter
Converts the specific JSON format from your pump data files to the upload system format
"""

import json
import os
from typing import Dict, List, Any

def convert_imperial_to_metric(flow_gpm: float, head_ft: float) -> tuple:
    """Convert imperial units to metric"""
    # 1 US gpm = 0.227124 m³/hr
    # 1 ft = 0.3048 m
    flow_m3hr = flow_gpm * 0.227124
    head_m = head_ft * 0.3048
    return flow_m3hr, head_m

def parse_multi_curve_data(flow_str: str, head_str: str, eff_str: str, npsh_str: str = "") -> List[Dict[str, Any]]:
    """Parse multi-curve data separated by | symbols"""
    curves = []
    
    flow_curves = flow_str.split('|')
    head_curves = head_str.split('|')
    eff_curves = eff_str.split('|')
    npsh_curves = npsh_str.split('|') if npsh_str else [''] * len(flow_curves)
    
    for i, (flow_curve, head_curve, eff_curve, npsh_curve) in enumerate(zip(flow_curves, head_curves, eff_curves, npsh_curves)):
        curve_data = {
            'curve_index': i + 1,
            'flow_data': flow_curve.strip(),
            'head_data': head_curve.strip(),
            'efficiency_data': eff_curve.strip(),
            'npsh_data': npsh_curve.strip() if npsh_curve else ''
        }
        curves.append(curve_data)
    
    return curves

def convert_json_pump_data(file_path: str) -> List[Dict[str, Any]]:
    """Convert JSON pump data file to upload format"""
    
    with open(file_path, 'r') as f:
        content = f.read().strip()
        # Remove trailing comma and closing brace if present
        if content.endswith(',\n}') or content.endswith(',}'):
            content = content.rsplit(',', 1)[0] + '\n}'
        elif content.endswith(','):
            content = content[:-1]
        
        pump_data = json.loads(content)
    
    pump_code = pump_data.get('objPump.pPumpCode', 'Unknown')
    test_speed = pump_data.get('objPump.pPumpTestSpeed', '1450')
    manufacturer = pump_data.get('objPump.pSuppName', 'APE PUMPS')
    
    # Get performance data
    flow_data = pump_data.get('objPump.pM_FLOW', '')
    head_data = pump_data.get('objPump.pM_HEAD', '')
    eff_data = pump_data.get('objPump.pM_EFF', '')
    npsh_data = pump_data.get('objPump.pM_NP', '')
    
    # Check if imperial units need conversion
    flow_unit = pump_data.get('objPump.pUnitFlow', '')
    head_unit = pump_data.get('objPump.pUnitHead', '')
    is_imperial = flow_unit == 'US gpm' and head_unit == 'ft'
    
    converted_pumps = []
    
    # Handle multi-curve data
    if '|' in flow_data:
        curves = parse_multi_curve_data(flow_data, head_data, eff_data, npsh_data)
        
        for curve in curves:
            # Convert units if necessary
            if is_imperial:
                flow_points = [float(x) for x in curve['flow_data'].split(';')]
                head_points = [float(x) for x in curve['head_data'].split(';')]
                
                converted_flow = []
                converted_head = []
                
                for flow_gpm, head_ft in zip(flow_points, head_points):
                    flow_m3hr, head_m = convert_imperial_to_metric(flow_gpm, head_ft)
                    converted_flow.append(f"{flow_m3hr:.1f}")
                    converted_head.append(f"{head_m:.1f}")
                
                curve['flow_data'] = ';'.join(converted_flow)
                curve['head_data'] = ';'.join(converted_head)
            
            # Create pump object for each curve
            pump_obj = {
                "objPump": {
                    "pPumpCode": f"{pump_code}_C{curve['curve_index']}",
                    "pPumpTestSpeed": test_speed,
                    "pFilter1": manufacturer,
                    "pSuppName": manufacturer,
                    "pM_FLOW": curve['flow_data'],
                    "pM_HEAD": curve['head_data'],
                    "pM_EFF": curve['efficiency_data'],
                    "pM_POW": "",  # Not provided in source data
                    "pM_NPSH": curve['npsh_data'],
                    "pVarD": "True",
                    "pVarN": "True",
                    "nPolyOrder": "3",
                    "pHeadCurvesNo": "1"
                }
            }
            converted_pumps.append(pump_obj)
    
    else:
        # Single curve data
        if is_imperial:
            flow_points = [float(x) for x in flow_data.split(';')]
            head_points = [float(x) for x in head_data.split(';')]
            
            converted_flow = []
            converted_head = []
            
            for flow_gpm, head_ft in zip(flow_points, head_points):
                flow_m3hr, head_m = convert_imperial_to_metric(flow_gpm, head_ft)
                converted_flow.append(f"{flow_m3hr:.1f}")
                converted_head.append(f"{head_m:.1f}")
            
            flow_data = ';'.join(converted_flow)
            head_data = ';'.join(converted_head)
        
        pump_obj = {
            "objPump": {
                "pPumpCode": pump_code,
                "pPumpTestSpeed": test_speed,
                "pFilter1": manufacturer,
                "pSuppName": manufacturer,
                "pM_FLOW": flow_data,
                "pM_HEAD": head_data,
                "pM_EFF": eff_data,
                "pM_POW": "",  # Not provided in source data
                "pM_NPSH": npsh_data,
                "pVarD": "True",
                "pVarN": "True",
                "nPolyOrder": "3",
                "pHeadCurvesNo": "1"
            }
        }
        converted_pumps.append(pump_obj)
    
    return converted_pumps

def convert_and_upload_files(file_paths: List[str]) -> None:
    """Convert JSON files and add them to the database"""
    from pump_upload_system import PumpUploadSystem
    
    upload_system = PumpUploadSystem()
    all_converted_pumps = []
    
    print("Converting pump data files...")
    
    for file_path in file_paths:
        try:
            converted_pumps = convert_json_pump_data(file_path)
            all_converted_pumps.extend(converted_pumps)
            print(f"✓ Converted {file_path}: {len(converted_pumps)} pump curves")
            
            for pump in converted_pumps:
                pump_code = pump['objPump']['pPumpCode']
                flow_points = len(pump['objPump']['pM_FLOW'].split(';'))
                print(f"  - {pump_code}: {flow_points} data points")
                
        except Exception as e:
            print(f"✗ Error converting {file_path}: {e}")
    
    # Upload to database
    if all_converted_pumps:
        print(f"\nUploading {len(all_converted_pumps)} pump curves to database...")
        pumps_added = upload_system.add_pumps_to_database(all_converted_pumps)
        print(f"✓ Successfully added {pumps_added} new pumps to database")
        
        # Validate database
        validation = upload_system.validate_database()
        print(f"✓ Database validation: {'PASSED' if validation['valid'] else 'FAILED'}")
        print(f"✓ Total pumps in database: {validation['pump_count']}")
    else:
        print("No pumps to upload.")

def main():
    """Main function to convert the three provided files"""
    files = [
        'attached_assets/10_nhtb_1749843024452.txt',
        'attached_assets/10_wln_32a_1749843224124.txt',
        'attached_assets/10_wln_26a_1749843224125.txt'
    ]
    
    # Check if files exist
    existing_files = [f for f in files if os.path.exists(f)]
    
    if not existing_files:
        print("No pump data files found. Please ensure the files are in the correct location.")
        return
    
    print("=== APE Pumps JSON Data Converter ===")
    print(f"Found {len(existing_files)} pump data files")
    
    convert_and_upload_files(existing_files)

if __name__ == "__main__":
    main()