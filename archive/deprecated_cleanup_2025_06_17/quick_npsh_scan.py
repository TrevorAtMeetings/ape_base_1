#!/usr/bin/env python3
"""
Quick scan to find all pumps with actual NPSH data in source files
"""

import os
import re

def quick_npsh_scan():
    """Scan source files for actual NPSH data using regex"""
    
    pump_data_dir = "data/pump_data"
    npsh_pumps = []
    
    print("Scanning for pumps with NPSH data...")
    
    for filename in sorted(os.listdir(pump_data_dir)):
        if filename.endswith('.txt'):
            filepath = os.path.join(pump_data_dir, filename)
            
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Extract pump code
                pump_code_match = re.search(r'"objPump\.pPumpCode":"([^"]+)"', content)
                pump_code = pump_code_match.group(1) if pump_code_match else filename.replace('.txt', '')
                
                # Extract NPSH data
                npsh_match = re.search(r'"objPump\.pM_NP":"([^"]+)"', content)
                
                if npsh_match:
                    npsh_data = npsh_match.group(1)
                    
                    # Check if any curve has non-zero NPSH values
                    curves = npsh_data.split('|')
                    has_real_npsh = False
                    
                    for curve_idx, curve in enumerate(curves):
                        npsh_values = [float(x) for x in curve.split(';') if x.strip()]
                        non_zero_npsh = [x for x in npsh_values if x > 0]
                        
                        if non_zero_npsh:
                            has_real_npsh = True
                            print(f"✓ {pump_code} (curve {curve_idx}): {len(non_zero_npsh)} NPSH points, range {min(non_zero_npsh):.1f}-{max(non_zero_npsh):.1f}m")
                            npsh_pumps.append({
                                'pump_code': pump_code,
                                'filename': filename,
                                'curve_index': curve_idx,
                                'npsh_points': len(non_zero_npsh),
                                'npsh_range': f"{min(non_zero_npsh):.1f}-{max(non_zero_npsh):.1f}"
                            })
                    
                    if not has_real_npsh:
                        print(f"- {pump_code}: No NPSH data (all zeros)")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    print(f"\nSummary: Found {len(npsh_pumps)} pump curves with actual NPSH data")
    return npsh_pumps

if __name__ == "__main__":
    npsh_pumps = quick_npsh_scan()