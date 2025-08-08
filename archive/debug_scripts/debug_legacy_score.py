#!/usr/bin/env python3
"""Debug script to analyze Legacy scoring breakdown for 100-400 2F."""

import os
os.environ['BRAIN_MODE'] = 'shadow'

from app.catalog_engine import CatalogEngine
from app.pump_repository import get_pump_repository

def debug_legacy_score():
    """Debug Legacy scoring for 100-400 2F pump."""
    
    repo = get_pump_repository()
    catalog = CatalogEngine()
    
    # Get the specific pump
    pump_100_400 = None
    for pump in catalog.pumps:
        if pump.pump_code == '100-400 2F':
            pump_100_400 = pump
            break
    
    if not pump_100_400:
        print("100-400 2F pump not found!")
        return
    
    print("=" * 70)
    print("DEBUGGING LEGACY SCORE FOR 100-400 2F at 200 m³/hr @ 40m")
    print("=" * 70)
    
    # Test the pump at the operating point
    flow = 200.0
    head = 40.0
    
    # Get the best solution for this pump
    best_solution = pump_100_400.find_best_solution_for_duty(flow, head)
    
    if best_solution:
        print(f"\nBest Solution Found:")
        print(f"  Method: {best_solution['method']}")
        print(f"  Score: {best_solution['score']:.1f}")
        print(f"  Flow: {best_solution['flow_m3hr']:.1f} m³/hr")
        print(f"  Head: {best_solution['head_m']:.1f} m")
        print(f"  Efficiency: {best_solution['efficiency_pct']:.1f}%")
        
        breakdown = best_solution.get('score_breakdown', {})
        if breakdown:
            print(f"\nScore Breakdown:")
            for component, details in breakdown.items():
                if isinstance(details, dict):
                    score = details.get('score', 0)
                    print(f"  {component:15} : {score:6.1f} pts")
                    for key, val in details.items():
                        if key != 'score':
                            print(f"    {key}: {val}")
        else:
            print("  No score breakdown available")
        
        # Also check BEP calculations
        bep_analysis = pump_100_400.calculate_bep_distance(flow, head)
        print(f"\nBEP Analysis:")
        print(f"  BEP Flow: {bep_analysis.get('bep_flow', 0):.1f} m³/hr")
        print(f"  BEP Head: {bep_analysis.get('bep_head', 0):.1f} m")
        print(f"  Flow Ratio: {bep_analysis.get('flow_ratio', 0)*100:.1f}%")
        print(f"  BEP Available: {bep_analysis.get('bep_available', False)}")
        
        # Check specifications
        specs = pump_100_400.specifications
        print(f"\nPump Specifications:")
        print(f"  BEP Flow (spec): {specs.get('bep_flow_m3hr', 0):.1f} m³/hr")
        print(f"  BEP Head (spec): {specs.get('bep_head_m', 0):.1f} m")
        print(f"  BEP Efficiency (spec): {specs.get('bep_efficiency_pct', 0):.1f}%")
        
    else:
        print("No solution found for this pump!")
    
    # Now run the full selection to see how it's scored in context
    print("\n" + "=" * 70)
    print("FULL SELECTION RESULTS:")
    print("=" * 70)
    
    results = catalog.select_pumps(flow_m3hr=flow, head_m=head, max_results=10)
    
    for i, pump in enumerate(results, 1):
        if pump['pump_code'] == '100-400 2F':
            print(f"\n100-400 2F found at position #{i}:")
            print(f"  Overall Score: {pump.get('overall_score', 0):.1f}")
            breakdown = pump.get('score_breakdown', {})
            if breakdown:
                print(f"  Score Breakdown:")
                for comp, details in breakdown.items():
                    if isinstance(details, dict):
                        print(f"    {comp}: {details.get('score', 0):.1f} pts")
            else:
                print("  No score breakdown in selection results")
            break

debug_legacy_score()