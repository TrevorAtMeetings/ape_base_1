#!/usr/bin/env python
"""
Script to find VFD-Only pumps from the catalog
"""

import os
import sys
sys.path.insert(0, '/home/runner/workspace')

from app.pump_repository import PumpRepository

# Initialize repository
repo = PumpRepository()

# Get all pumps
all_pumps = repo.get_all_pumps()

# Find VFD-Only pumps (variable_speed=True, variable_diameter=False)
vfd_only_pumps = []
for pump in all_pumps:
    if pump.get('variable_speed') and not pump.get('variable_diameter'):
        vfd_only_pumps.append({
            'pump_code': pump['pump_code'],
            'manufacturer': pump.get('manufacturer', ''),
            'pump_type': pump.get('pump_type', ''),
            'variable_speed': pump['variable_speed'],
            'variable_diameter': pump['variable_diameter'],
            'rated_speed_rpm': pump.get('rated_speed_rpm', 0)
        })

# Print results
print(f"Found {len(vfd_only_pumps)} VFD-Only pumps (variable_speed=True, variable_diameter=False)")
print("\nFirst 10 VFD-Only pumps:")
print("-" * 80)

for i, pump in enumerate(vfd_only_pumps[:10], 1):
    print(f"{i}. {pump['pump_code']:20} | Mfr: {pump['manufacturer']:10} | Type: {pump['pump_type']:15} | Speed: {pump['rated_speed_rpm']} rpm")

# Check for 8312 series
print("\n8312 Series VFD-Only pumps:")
print("-" * 80)
series_8312 = [p for p in vfd_only_pumps if '8312' in p['pump_code']]
if series_8312:
    for pump in series_8312[:5]:
        print(f"- {pump['pump_code']:20} | Speed: {pump['rated_speed_rpm']} rpm")
else:
    print("No 8312 series found in VFD-Only category")

# Find a good test candidate (with reasonable flow/head for testing)
print("\nRecommended test pump (first VFD-Only pump found):")
if vfd_only_pumps:
    test_pump = vfd_only_pumps[0]
    print(f"Pump Code: {test_pump['pump_code']}")
    print(f"Run test with flow around 450 m³/hr and head around 70m")