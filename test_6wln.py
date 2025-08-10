#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

# Set up minimal Flask context
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', '')
os.environ['SESSION_SECRET'] = os.environ.get('SESSION_SECRET', 'test')

from app.pump_repository import PumpRepository

def test_6wln():
    print("=== Testing 6 WLN 18A Data ===")
    
    repo = PumpRepository()
    repo.initialize()
    
    # Find 6 WLN 18A
    pump = repo.get_pump_by_code("6 WLN 18A")
    
    if not pump:
        print("ERROR: 6 WLN 18A not found!")
        return
    
    print(f"Found: {pump.get('pump_name', 'Unknown')}")
    
    # Check BEP data
    specs = pump.get('specifications', {})
    print(f"BEP Flow: {specs.get('bep_flow_m3hr', 'Missing')} m³/hr")
    print(f"BEP Head: {specs.get('bep_head_m', 'Missing')} m")
    
    # Calculate QBP for 350 m³/hr
    bep_flow = specs.get('bep_flow_m3hr', 0)
    if bep_flow > 0:
        qbp = (350.0 / bep_flow) * 100
        print(f"QBP for 350 m³/hr: {qbp:.1f}%")
        
        if 60 <= qbp <= 130:
            print("✓ QBP within 60-130% range")
        else:
            print(f"✗ QBP {qbp:.1f}% outside 60-130% range - THIS IS THE ISSUE")
    
    # Check impeller diameters
    diameters = pump.get('diameters', [])
    print(f"Available diameters: {diameters}")
    
    if diameters:
        max_dia = max(diameters)
        target_dia = 397.6  # From manufacturer
        trim_pct = (target_dia / max_dia) * 100
        print(f"Required diameter: {target_dia}mm from {max_dia}mm = {trim_pct:.1f}%")
        
        if trim_pct >= 85.0:
            print("✓ Trim within 15% limit")
        else:
            print(f"✗ Trim {trim_pct:.1f}% exceeds 15% limit - THIS IS THE ISSUE")

if __name__ == "__main__":
    test_6wln()