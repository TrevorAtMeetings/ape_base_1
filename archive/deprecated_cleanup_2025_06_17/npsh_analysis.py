#!/usr/bin/env python3
"""
NPSH Data Analysis for APE Pumps Database
Comprehensive analysis of NPSH data availability and quality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pump_engine import load_all_pump_data
import json

def analyze_npsh_data():
    """Analyze NPSH data availability across all pumps."""
    
    print("Loading pump database...")
    all_pumps = load_all_pump_data()
    
    if not all_pumps:
        print("ERROR: Could not load pump data")
        return
    
    print(f"Analyzing NPSH data for {len(all_pumps)} pumps...\n")
    
    # NPSH analysis counters
    pumps_with_npsh = 0
    pumps_without_npsh = 0
    total_npsh_points = 0
    npsh_by_category = {
        'END_SUCTION': {'with_npsh': 0, 'without_npsh': 0, 'total_points': 0},
        'MULTI_STAGE': {'with_npsh': 0, 'without_npsh': 0, 'total_points': 0},
        'AXIAL_FLOW': {'with_npsh': 0, 'without_npsh': 0, 'total_points': 0},
        'HSC': {'with_npsh': 0, 'without_npsh': 0, 'total_points': 0}
    }
    
    # Detailed analysis
    npsh_examples = []
    missing_examples = []
    
    for pump in all_pumps:
        has_npsh = False
        pump_npsh_points = 0
        
        # Categorize pump type
        pump_code_upper = pump.pump_code.upper()
        category = 'END_SUCTION'  # Default
        if any(x in pump_code_upper for x in ['2F', '2P', '3P', '4P', '6P', '8P']):
            category = 'MULTI_STAGE'
        elif 'ALE' in pump_code_upper:
            category = 'AXIAL_FLOW'
        elif 'HSC' in pump_code_upper:
            category = 'HSC'
        
        if pump.curves:
            for curve_idx, curve in enumerate(pump.curves):
                # Check multiple possible NPSH field names
                npsh_fields = ['flow_vs_npshr', 'flow_vs_npsh', 'npshr_data', 'npsh_data']
                curve_has_npsh = False
                
                for field in npsh_fields:
                    npsh_data = curve.get(field, [])
                    if npsh_data and len(npsh_data) > 0:
                        # Validate NPSH data points
                        valid_npsh_points = []
                        for point in npsh_data:
                            if isinstance(point, (list, tuple)) and len(point) >= 2:
                                flow, npsh_val = point[0], point[1]
                                if npsh_val is not None and npsh_val > 0:
                                    valid_npsh_points.append(point)
                            elif isinstance(point, (int, float)) and point > 0:
                                # Handle direct numeric NPSH values
                                valid_npsh_points.append(point)
                        
                        if valid_npsh_points:
                            curve_has_npsh = True
                            pump_npsh_points += len(valid_npsh_points)
                            total_npsh_points += len(valid_npsh_points)
                            
                            if len(npsh_examples) < 5:  # Collect examples
                                npsh_examples.append({
                                    'pump_code': pump.pump_code,
                                    'curve_index': curve_idx,
                                    'field_name': field,
                                    'npsh_points': len(valid_npsh_points),
                                    'sample_data': valid_npsh_points[:3]
                                })
                
                if curve_has_npsh:
                    has_npsh = True
        
        # Update counters
        if has_npsh:
            pumps_with_npsh += 1
            npsh_by_category[category]['with_npsh'] += 1
            npsh_by_category[category]['total_points'] += pump_npsh_points
        else:
            pumps_without_npsh += 1
            npsh_by_category[category]['without_npsh'] += 1
            
            if len(missing_examples) < 10:  # Collect missing examples
                missing_examples.append({
                    'pump_code': pump.pump_code,
                    'category': category,
                    'curve_count': len(pump.curves) if pump.curves else 0
                })
    
    # Print comprehensive analysis
    print("="*60)
    print("NPSH DATA AVAILABILITY ANALYSIS")
    print("="*60)
    
    print(f"Total Pumps Analyzed: {len(all_pumps)}")
    print(f"Pumps WITH NPSH Data: {pumps_with_npsh} ({pumps_with_npsh/len(all_pumps)*100:.1f}%)")
    print(f"Pumps WITHOUT NPSH Data: {pumps_without_npsh} ({pumps_without_npsh/len(all_pumps)*100:.1f}%)")
    print(f"Total NPSH Data Points: {total_npsh_points}")
    
    print("\n" + "="*40)
    print("NPSH DATA BY PUMP CATEGORY")
    print("="*40)
    
    for category, data in npsh_by_category.items():
        total_cat = data['with_npsh'] + data['without_npsh']
        if total_cat > 0:
            with_pct = data['with_npsh'] / total_cat * 100
            print(f"\n{category}:")
            print(f"  Total Pumps: {total_cat}")
            print(f"  With NPSH: {data['with_npsh']} ({with_pct:.1f}%)")
            print(f"  Without NPSH: {data['without_npsh']} ({100-with_pct:.1f}%)")
            print(f"  NPSH Points: {data['total_points']}")
    
    if npsh_examples:
        print("\n" + "="*40)
        print("EXAMPLES WITH NPSH DATA")
        print("="*40)
        for example in npsh_examples:
            print(f"\nPump: {example['pump_code']}")
            print(f"  Field: {example['field_name']}")
            print(f"  Points: {example['npsh_points']}")
            print(f"  Sample: {example['sample_data']}")
    
    if missing_examples:
        print("\n" + "="*40)
        print("EXAMPLES WITHOUT NPSH DATA")
        print("="*40)
        for example in missing_examples[:5]:
            print(f"  {example['pump_code']} ({example['category']}, {example['curve_count']} curves)")
    
    # Check data structure for a few pumps
    print("\n" + "="*40)
    print("CURVE STRUCTURE ANALYSIS")
    print("="*40)
    
    sample_pumps = all_pumps[:3]
    for pump in sample_pumps:
        print(f"\nPump: {pump.pump_code}")
        if pump.curves:
            for i, curve in enumerate(pump.curves):
                print(f"  Curve {i} keys: {list(curve.keys())}")
                # Check for any NPSH-related keys
                npsh_keys = [k for k in curve.keys() if 'npsh' in k.lower()]
                if npsh_keys:
                    print(f"  NPSH-related keys: {npsh_keys}")
                    for key in npsh_keys:
                        data = curve[key]
                        print(f"    {key}: {type(data)} with {len(data) if hasattr(data, '__len__') else 'N/A'} items")

if __name__ == "__main__":
    analyze_npsh_data()