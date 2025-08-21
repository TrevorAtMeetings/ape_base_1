#!/usr/bin/env python
"""
Test Script for VFD Calculation Logic
Tests the new calculate_performance_with_speed_variation method
"""

import sys
import os
sys.path.insert(0, '.')

from app.pump_brain import PumpBrain
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_vfd_calculation():
    """Test the VFD calculation method with various pumps"""
    
    # Initialize Brain
    brain = PumpBrain()
    
    logger.info("=" * 80)
    logger.info("TESTING VFD CALCULATION ENGINE")
    logger.info("=" * 80)
    
    # Test cases with different duty points
    test_cases = [
        {
            'name': 'Low Flow/Low Head',
            'flow': 100,  # m³/hr
            'head': 20,   # m
            'pump_codes': ['8312-14', '14 MC 6970 4P', '8 LC 4460']
        },
        {
            'name': 'Medium Flow/Medium Head',
            'flow': 500,  # m³/hr
            'head': 50,   # m
            'pump_codes': ['8312-14', '32 HC 6P', '12 MC 4320']
        },
        {
            'name': 'High Flow/High Head',
            'flow': 1000, # m³/hr
            'head': 80,   # m
            'pump_codes': ['32 HC 8P', '16 LC 6800']
        }
    ]
    
    # Get all pumps from repository
    all_pumps = brain.repository.get_pump_models()
    
    for test_case in test_cases:
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST CASE: {test_case['name']}")
        logger.info(f"Duty Point: {test_case['flow']} m³/hr @ {test_case['head']} m")
        logger.info("-" * 60)
        
        for pump_code in test_case['pump_codes']:
            # Find the pump in repository
            pump = next((p for p in all_pumps if p['pump_code'] == pump_code), None)
            
            if not pump:
                logger.warning(f"  {pump_code}: Not found in repository")
                continue
            
            # Check if it's a VFD-capable pump
            specs = pump.get('specifications', {})
            variable_speed = specs.get('variable_speed', False)
            variable_diameter = specs.get('variable_diameter', True)
            
            logger.info(f"\n  Testing: {pump_code}")
            logger.info(f"    Variable Speed: {variable_speed}, Variable Diameter: {variable_diameter}")
            
            # Test VFD calculation
            vfd_result = brain.performance.calculate_performance_with_speed_variation(
                pump, 
                test_case['flow'], 
                test_case['head']
            )
            
            if vfd_result:
                logger.info(f"    ✓ VFD Calculation Successful!")
                logger.info(f"    Required Speed: {vfd_result['required_speed_rpm']} RPM")
                logger.info(f"    Speed Ratio: {vfd_result['speed_ratio']}%")
                logger.info(f"    Efficiency: {vfd_result['efficiency_pct']:.1f}%")
                logger.info(f"    Power: {vfd_result['power_kw']:.1f} kW")
                logger.info(f"    Reference Point: Q={vfd_result['reference_point']['flow_m3hr']:.1f} m³/hr, H={vfd_result['reference_point']['head_m']:.1f}m")
                logger.info(f"    Operating Frequency: {vfd_result.get('operating_frequency_hz', 0):.1f} Hz")
            else:
                logger.info(f"    ✗ VFD not feasible (speed out of range or no solution)")
    
    # Test a specific VFD-Only pump in detail
    logger.info(f"\n{'='*80}")
    logger.info("DETAILED TEST: VFD-Only Pump (8312-14)")
    logger.info("-" * 80)
    
    vfd_only_pump = next((p for p in all_pumps if p['pump_code'] == '8312-14'), None)
    
    if vfd_only_pump:
        test_flow = 300  # m³/hr
        test_head = 35   # m
        
        logger.info(f"Pump: {vfd_only_pump['pump_code']}")
        logger.info(f"Type: {vfd_only_pump.get('pump_type', 'Unknown')}")
        specs = vfd_only_pump.get('specifications', {})
        logger.info(f"Speed Range: {specs.get('min_speed_rpm', 0)} - {specs.get('max_speed_rpm', 0)} RPM")
        logger.info(f"Test Speed: {specs.get('test_speed_rpm', 0)} RPM")
        logger.info(f"BEP: {specs.get('bep_flow_m3hr', 0):.1f} m³/hr @ {specs.get('bep_head_m', 0):.1f}m")
        
        logger.info(f"\nTesting at: {test_flow} m³/hr @ {test_head}m")
        
        result = brain.performance.calculate_performance_with_speed_variation(
            vfd_only_pump, 
            test_flow, 
            test_head
        )
        
        if result:
            logger.info("\n✓ VFD CALCULATION SUCCESSFUL")
            logger.info(f"  Sizing Method: {result['sizing_method']}")
            logger.info(f"  Required Speed: {result['required_speed_rpm']} RPM")
            logger.info(f"  Reference Speed: {result['reference_speed_rpm']} RPM")
            logger.info(f"  Speed Ratio: {result['speed_ratio']}%")
            logger.info(f"  Operating Frequency: {result.get('operating_frequency_hz', 0):.1f} Hz")
            logger.info(f"  Efficiency: {result['efficiency_pct']:.1f}%")
            logger.info(f"  Power: {result['power_kw']:.1f} kW")
            logger.info(f"  NPSH Required: {result.get('npshr_m', 'N/A')}")
            logger.info(f"  System Curve k: {result['system_curve_k']:.6f}")
            logger.info(f"  Static Head: {result['h_static']:.1f}m")
            logger.info(f"  Reference Point: Q={result['reference_point']['flow_m3hr']:.1f} m³/hr, H={result['reference_point']['head_m']:.1f}m")
        else:
            logger.info("\n✗ VFD CALCULATION FAILED")
            logger.info("  Likely reason: Required speed outside pump's operational range")
    else:
        logger.warning("8312-14 pump not found in repository")
    
    logger.info(f"\n{'='*80}")
    logger.info("VFD CALCULATION ENGINE TEST COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    test_vfd_calculation()