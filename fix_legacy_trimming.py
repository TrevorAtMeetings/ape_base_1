#!/usr/bin/env python3
"""Script to analyze and fix Legacy trimming logic."""

import os
os.environ['BRAIN_MODE'] = 'shadow'

from app.catalog_engine import CatalogEngine
from app.pump_repository import get_pump_repository
from app.impeller_scaling import ImpellerScalingEngine

def analyze_trimming_issue():
    """Analyze why Legacy isn't finding the optimal trim solution."""
    
    repo = get_pump_repository()
    catalog = CatalogEngine()
    scaling_engine = ImpellerScalingEngine()
    
    # Get the pump
    pump = None
    for p in catalog.pumps:
        if p.pump_code == '100-400 2F':
            pump = p
            break
    
    if not pump:
        print("100-400 2F pump not found!")
        return
    
    print("=" * 70)
    print("ANALYZING TRIMMING ISSUE FOR 100-400 2F at 200 m³/hr @ 40m")
    print("=" * 70)
    
    # Test parameters
    flow = 200.0
    head = 40.0
    
    # Get pump curves
    curves = pump.curves
    
    print(f"\nAvailable curves:")
    for curve in curves:
        imp_d = curve.get('impeller_diameter_mm', 0)
        points = curve.get('performance_points', [])
        print(f"  Ø {imp_d}mm: {len(points)} points")
    
    # Call Legacy's find_optimal_sizing
    optimal = scaling_engine.find_optimal_sizing(curves, flow, head)
    
    if optimal:
        print(f"\nLegacy find_optimal_sizing result:")
        print(f"  Base Ø: {optimal['sizing']['base_diameter_mm']:.1f}mm")
        print(f"  Required Ø: {optimal['sizing']['required_diameter_mm']:.1f}mm")
        print(f"  Trim %: {optimal['sizing']['trim_percent']:.1f}%")
        print(f"  Delivered head: {optimal['performance']['head_m']:.1f}m")
        print(f"  Head error: {optimal['performance']['head_m'] - head:.1f}m")
        
        # Check if this meets the 2% tolerance
        if optimal['performance']['head_m'] >= head * 0.98:
            print(f"  ✓ Meets 2% tolerance")
        else:
            print(f"  ✗ Fails 2% tolerance")
    
    # Now manually calculate what the best trim should be
    print("\n" + "=" * 70)
    print("MANUAL CALCULATION OF OPTIMAL TRIM:")
    print("=" * 70)
    
    best_solution = None
    min_head_error = float('inf')
    
    for curve in curves:
        imp_d = curve.get('impeller_diameter_mm', 0)
        if not imp_d:
            continue
        
        # Interpolate performance at 200 m³/hr for this curve
        points = curve.get('performance_points', [])
        flows = [p['flow_m3hr'] for p in points]
        heads = [p['head_m'] for p in points]
        effs = [p['efficiency_pct'] for p in points]
        
        # Find interpolated head at 200 m³/hr
        if min(flows) <= flow <= max(flows):
            # Simple linear interpolation for test
            import numpy as np
            from scipy.interpolate import interp1d
            
            f_head = interp1d(flows, heads, kind='linear', fill_value='extrapolate')
            f_eff = interp1d(flows, effs, kind='linear', fill_value='extrapolate')
            
            base_head = float(f_head(flow))
            base_eff = float(f_eff(flow))
            
            # Calculate required diameter using affinity laws
            if base_head > head:  # Can trim down
                required_d = imp_d * (head / base_head) ** 0.5
                trim_pct = (required_d / imp_d) * 100
                
                if 85 <= trim_pct <= 100:
                    # Calculate trimmed efficiency (efficiency reduces with trim)
                    eff_reduction = (1 - (100 - trim_pct) / 100 * 0.02)  # 2% loss per 10% trim
                    trimmed_eff = base_eff * eff_reduction
                    
                    head_error = abs(head - head)  # Should be 0 after trim
                    
                    print(f"\n  Base Ø {imp_d}mm:")
                    print(f"    Interpolated @ {flow} m³/hr: {base_head:.1f}m, {base_eff:.1f}%")
                    print(f"    Required Ø for {head}m: {required_d:.1f}mm")
                    print(f"    Trim %: {trim_pct:.1f}%")
                    print(f"    Trimmed efficiency: {trimmed_eff:.1f}%")
                    
                    if head_error < min_head_error:
                        min_head_error = head_error
                        best_solution = {
                            'base_diameter': imp_d,
                            'required_diameter': required_d,
                            'trim_percent': trim_pct,
                            'base_head': base_head,
                            'delivered_head': head,
                            'efficiency': trimmed_eff
                        }
    
    if best_solution:
        print("\n" + "=" * 70)
        print("BEST MANUAL SOLUTION:")
        print("=" * 70)
        print(f"  Base Ø: {best_solution['base_diameter']:.1f}mm")
        print(f"  Required Ø: {best_solution['required_diameter']:.1f}mm")
        print(f"  Trim %: {best_solution['trim_percent']:.1f}%")
        print(f"  Delivered head: {best_solution['delivered_head']:.1f}m")
        print(f"  Efficiency: {best_solution['efficiency']:.1f}%")

analyze_trimming_issue()