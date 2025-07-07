#!/usr/bin/env python3
"""
Comprehensive NPSH Data Scanner
Scans all original pump data files to find actual NPSH data availability
"""

import os
import json
import re

def scan_source_files_for_npsh():
    """Scan all source pump files for NPSH data."""
    
    pump_data_dir = "data/pump_data"
    npsh_findings = []
    
    print("Scanning all source pump files for NPSH data...")
    print("="*60)
    
    # Get all .txt files in pump_data directory
    pump_files = [f for f in os.listdir(pump_data_dir) if f.endswith('.txt')]
    
    total_files = len(pump_files)
    files_with_npsh = 0
    
    for filename in sorted(pump_files):
        filepath = os.path.join(pump_data_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Fix malformed JSON (trailing comma)
            content_fixed = content.rstrip().rstrip(',') + '\n}'
            data = json.loads(content_fixed)
            pump_code = data.get('objPump.pPumpCode', filename.replace('.txt', ''))
            
            # Check NPSH-related fields
            npsh_eoc = data.get('objPump.pNPSHEOC', '0')
            npsh_curves_no = data.get('objPump.pNPSHCurvesNo', '0')
            npsh_data_raw = data.get('objPump.pM_NP', '')
            
            # Analyze NPSH data
            has_valid_npsh = False
            npsh_details = []
            
            if npsh_data_raw and npsh_data_raw != '':
                # Split by | for different curves
                npsh_curves = npsh_data_raw.split('|')
                
                for curve_idx, curve_data in enumerate(npsh_curves):
                    if curve_data.strip():
                        # Split by ; for individual points
                        npsh_points = [float(x) for x in curve_data.split(';') if x.strip()]
                        valid_points = [x for x in npsh_points if x > 0]
                        
                        if valid_points:
                            has_valid_npsh = True
                            npsh_details.append({
                                'curve_index': curve_idx,
                                'total_points': len(npsh_points),
                                'valid_points': len(valid_points),
                                'npsh_range': f"{min(valid_points):.1f} - {max(valid_points):.1f} m"
                            })
            
            if has_valid_npsh:
                files_with_npsh += 1
                npsh_findings.append({
                    'pump_code': pump_code,
                    'filename': filename,
                    'npsh_eoc': npsh_eoc,
                    'npsh_curves_declared': npsh_curves_no,
                    'npsh_details': npsh_details,
                    'total_valid_points': sum(d['valid_points'] for d in npsh_details)
                })
                
                print(f"✓ {pump_code}")
                for detail in npsh_details:
                    print(f"    Curve {detail['curve_index']}: {detail['valid_points']} points, range {detail['npsh_range']}")
        
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    print("\n" + "="*60)
    print("COMPREHENSIVE NPSH SCAN RESULTS")
    print("="*60)
    print(f"Total pump files scanned: {total_files}")
    print(f"Files with valid NPSH data: {files_with_npsh}")
    print(f"NPSH availability: {files_with_npsh/total_files*100:.1f}%")
    
    if npsh_findings:
        print(f"\nPUMPS WITH NPSH DATA ({len(npsh_findings)}):")
        print("-" * 40)
        
        total_npsh_points = 0
        for finding in npsh_findings:
            total_npsh_points += finding['total_valid_points']
            print(f"\n{finding['pump_code']} ({finding['filename']})")
            print(f"  NPSH EOC: {finding['npsh_eoc']} m")
            print(f"  Declared curves: {finding['npsh_curves_declared']}")
            print(f"  Valid NPSH points: {finding['total_valid_points']}")
            for detail in finding['npsh_details']:
                print(f"    Curve {detail['curve_index']}: {detail['valid_points']} points ({detail['npsh_range']})")
        
        print(f"\nTotal valid NPSH data points across all pumps: {total_npsh_points}")
    
    else:
        print("\nNo pumps found with valid NPSH data.")
    
    return npsh_findings

if __name__ == "__main__":
    findings = scan_source_files_for_npsh()