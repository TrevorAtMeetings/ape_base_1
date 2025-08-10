#!/usr/bin/env python3

import sys
sys.path.append('.')

from app.pump_brain import PumpBrain

def debug_6wln():
    """Debug why 6 WLN 18A is being rejected"""
    print("=== Debugging 6 WLN 18A Rejection ===")
    
    brain = PumpBrain()
    
    # Test specific pump
    pump_code = "6 WLN 18A"
    flow = 350.0
    head = 50.0
    
    print(f"\nTesting: {pump_code}")
    print(f"Requirements: {flow} m³/hr @ {head}m")
    
    # Get pump data first
    pump_data = brain.repository.get_pump_by_code(pump_code)
    if not pump_data:
        print(f"ERROR: Pump {pump_code} not found in database!")
        return
        
    print(f"Found pump data: {pump_data.get('pump_name', 'Unknown')}")
    
    # Test performance calculation
    performance = brain.performance_intel.calculate_performance(pump_data, flow, head)
    
    if performance:
        print(f"Performance calculation SUCCESS:")
        print(f"  - Head: {performance.get('head', 'N/A')}m")
        print(f"  - Efficiency: {performance.get('efficiency_pct', 'N/A')}%")
        print(f"  - Power: {performance.get('power_kw', 'N/A')}kW")
        print(f"  - Trim: {performance.get('trim_percent', 'N/A')}%")
    else:
        print("Performance calculation FAILED - pump rejected")
        
    # Test selection scoring
    evaluation = brain.selection_intel.score_pump_selection(pump_data, flow, head, None, None)
    
    if evaluation.get('feasible', False):
        print(f"Selection scoring SUCCESS:")
        print(f"  - Score: {evaluation.get('total_score', 'N/A')}")
        print(f"  - Operating zone: {evaluation.get('operating_zone', 'N/A')}")
        print(f"  - QBP: {evaluation.get('qbp_percent', 'N/A')}%")
    else:
        print("Selection scoring FAILED:")
        print(f"  - Reasons: {evaluation.get('exclusion_reasons', [])}")
        
    # Check BEP data
    specs = pump_data.get('specifications', {})
    bep_flow = specs.get('bep_flow_m3hr', 0)
    bep_head = specs.get('bep_head_m', 0)
    print(f"\nBEP Data:")
    print(f"  - BEP Flow: {bep_flow} m³/hr")
    print(f"  - BEP Head: {bep_head}m")
    if bep_flow > 0:
        qbp = (flow / bep_flow) * 100
        print(f"  - QBP: {qbp:.1f}%")

if __name__ == "__main__":
    debug_6wln()