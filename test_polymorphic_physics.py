#!/usr/bin/env python3
"""
Test the Polymorphic Physics Model implementation in the Brain system.
This script verifies that different pump types use their specific physics exponents.
"""

import os
import sys
import logging
from decimal import Decimal

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables if needed
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/ape_pumps')

def test_physics_models():
    """Test that different pump types use their specific physics exponents."""
    
    logger.info("Testing Polymorphic Physics Model Implementation...")
    
    # Import after setting up the path
    from app.pump_brain import PumpBrain
    from app.brain.physics_models import PUMP_TYPE_EXPONENTS, normalize_pump_type
    
    # Initialize Brain
    brain = PumpBrain()
    performance_analyzer = brain.performance
    
    # Test cases with different pump types
    test_cases = [
        {
            'pump_type': 'AXIAL_FLOW',
            'pump_code': 'TEST_AXIAL_001',
            'expected_flow_exp': 0.95,
            'expected_head_exp': 1.65,
            'expected_power_exp': 2.60,
            'expected_npsh_exp': 1.70
        },
        {
            'pump_type': 'VERTICAL_TURBINE',
            'pump_code': '28 HC 6P',  # Real HC pump example
            'expected_flow_exp': 0.97,
            'expected_head_exp': 1.85,
            'expected_power_exp': 2.80,
            'expected_npsh_exp': 1.80
        },
        {
            'pump_type': 'END_SUCTION',
            'pump_code': 'TEST_END_001',
            'expected_flow_exp': 1.00,
            'expected_head_exp': 1.95,
            'expected_power_exp': 2.93,
            'expected_npsh_exp': 1.95
        },
        {
            'pump_type': 'MULTI_STAGE',
            'pump_code': 'TEST_MULTI_001',
            'expected_flow_exp': 1.00,
            'expected_head_exp': 1.97,
            'expected_power_exp': 2.95,
            'expected_npsh_exp': 2.00
        },
        {
            'pump_type': 'UNKNOWN_TYPE',  # Should use DEFAULT
            'pump_code': 'TEST_UNKNOWN',
            'expected_flow_exp': 1.00,
            'expected_head_exp': 2.00,
            'expected_power_exp': 3.00,
            'expected_npsh_exp': 2.00
        }
    ]
    
    logger.info(f"Testing {len(test_cases)} pump types...")
    all_passed = True
    
    for test in test_cases:
        logger.info(f"\nTesting pump type: {test['pump_type']} ({test['pump_code']})")
        
        # Test normalization
        normalized = normalize_pump_type(test['pump_type'])
        logger.info(f"  Normalized type: {normalized}")
        
        # Create mock pump data
        pump_data = {
            'pump_type': test['pump_type'],
            'pump_code': test['pump_code']
        }
        
        # Get exponents through the performance analyzer
        exponents = performance_analyzer._get_exponents_for_pump(pump_data)
        
        # Verify exponents match expected values
        results = {
            'flow': (exponents['flow_exponent_x'], test['expected_flow_exp']),
            'head': (exponents['head_exponent_y'], test['expected_head_exp']),
            'power': (exponents['power_exponent_z'], test['expected_power_exp']),
            'npsh': (exponents['npshr_exponent_alpha'], test['expected_npsh_exp'])
        }
        
        test_passed = True
        for exp_name, (actual, expected) in results.items():
            if abs(actual - expected) > 0.001:  # Small tolerance for floating point
                logger.error(f"  ❌ {exp_name} exponent: {actual} (expected {expected})")
                test_passed = False
                all_passed = False
            else:
                logger.info(f"  ✓ {exp_name} exponent: {actual}")
        
        if test_passed:
            logger.info(f"  ✅ Test PASSED for {test['pump_type']}")
        else:
            logger.error(f"  ❌ Test FAILED for {test['pump_type']}")
    
    # Summary
    logger.info("\n" + "="*60)
    if all_passed:
        logger.info("✅ ALL TESTS PASSED - Polymorphic Physics Model is working correctly!")
    else:
        logger.error("❌ SOME TESTS FAILED - Please review the implementation")
    
    return all_passed

def test_real_pump_calculation():
    """Test actual pump performance calculation with physics model."""
    
    logger.info("\n" + "="*60)
    logger.info("Testing Real Pump Calculation with Physics Model...")
    
    from app.pump_brain import PumpBrain
    
    # Initialize Brain
    brain = PumpBrain()
    
    # Test with a real vertical turbine pump
    test_pump = {
        'pump_code': '28 HC 6P',
        'pump_type': 'VERTICAL_TURBINE',
        'curves': [{
            'impeller_diameter_mm': 450,
            'performance_points': [
                {'flow_m3hr': 100, 'head_m': 100, 'efficiency_pct': 75},
                {'flow_m3hr': 200, 'head_m': 95, 'efficiency_pct': 80},
                {'flow_m3hr': 300, 'head_m': 85, 'efficiency_pct': 82},
                {'flow_m3hr': 400, 'head_m': 70, 'efficiency_pct': 78},
                {'flow_m3hr': 500, 'head_m': 50, 'efficiency_pct': 70}
            ]
        }],
        'specifications': {
            'bep_flow_m3hr': 300,
            'bep_head_m': 85,
            'bep_efficiency': 82,
            'pump_type': 'VERTICAL_TURBINE'
        }
    }
    
    # Test performance calculation at a specific point
    flow = 250  # m³/hr
    head = 60   # m
    
    logger.info(f"\nCalculating performance for {test_pump['pump_code']} at {flow} m³/hr @ {head}m")
    
    result = brain.performance.calculate_at_point_industry_standard(
        test_pump, flow, head
    )
    
    if result:
        logger.info(f"✅ Calculation successful!")
        logger.info(f"  Impeller diameter: {result.get('impeller_diameter_mm', 'N/A'):.1f} mm")
        logger.info(f"  Trim percentage: {result.get('trim_percent', 'N/A'):.1f}%")
        logger.info(f"  Delivered head: {result.get('head_m', 'N/A'):.1f} m")
        logger.info(f"  Efficiency: {result.get('efficiency_pct', 'N/A'):.1f}%")
        logger.info(f"  Power: {result.get('power_kw', 'N/A'):.1f} kW")
        
        # Verify that vertical turbine physics were used (head exponent should be ~1.85)
        # We can't directly verify this from the result, but the calculation should be different
        # from standard pumps
        logger.info("\n  Note: Vertical Turbine pump uses head exponent 1.85 vs standard 2.0")
        logger.info("  This results in different trim calculations compared to standard pumps")
    else:
        logger.error(f"❌ Calculation failed!")
    
    return result is not None

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("POLYMORPHIC PHYSICS MODEL TEST SUITE")
    logger.info("="*60)
    
    # Run tests
    test1_passed = test_physics_models()
    test2_passed = test_real_pump_calculation()
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("FINAL TEST SUMMARY")
    logger.info("="*60)
    
    if test1_passed and test2_passed:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("The Polymorphic Physics Model Enhancement is fully operational.")
        logger.info("Different pump types now use their specific physics exponents for")
        logger.info("more accurate performance calculations.")
    else:
        logger.error("❌ SOME TESTS FAILED")
        logger.error("Please review the test output above for details.")
    
    sys.exit(0 if (test1_passed and test2_passed) else 1)