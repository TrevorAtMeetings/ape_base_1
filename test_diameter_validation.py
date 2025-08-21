#!/usr/bin/env python3
"""
Test script to verify diameter validation improvements in the calibration system.
"""

import requests
import json

def test_diameter_out_of_range():
    """
    Test that the system properly handles diameters outside the valid range.
    """
    print("Testing diameter validation for pump 100-200 2F...")
    print("Available curves: 184, 192, 200, 208, 217mm")
    print("Testing with diameter: 325mm (way outside range)")
    
    # Create test data with out-of-range diameter
    test_data = {
        'pump_code': '100-200 2F',
        'ground_truth_points': [
            {
                'flow': 400,
                'head': 45,
                'efficiency': 80,
                'power': 30,
                'diameter': 325  # This is way outside the valid range (184-217mm)
            }
        ]
    }
    
    print("\nTest data:")
    print(json.dumps(test_data, indent=2))
    
    # Test the processing
    from app.route_modules.brain_admin import ManufacturerComparisonEngine
    from app.pump_repository import get_pump_repository
    
    brain_admin = ManufacturerComparisonEngine()
    pump_repo = get_pump_repository()
    
    try:
        result = brain_admin.process_calibration_data(
            test_data['pump_code'],
            test_data['ground_truth_points'],
            pump_repo
        )
        
        print("\n✅ Processing completed successfully!")
        
        # Check for diameter warnings
        if result.get('diameter_warnings'):
            print("\n⚠️ Diameter warnings detected:")
            for warning in result['diameter_warnings']:
                print(f"  - Diameter {warning['diameter']}mm is outside valid range")
                print(f"    Valid range: {warning['min_valid']:.0f}-{warning['max_valid']:.0f}mm")
                print(f"    Available curves: {warning['available_curves']}")
        else:
            print("\n❌ No diameter warnings generated (unexpected)")
        
        # Check comparison points
        if result.get('comparison_points'):
            print(f"\n📊 Comparison points generated: {len(result['comparison_points'])}")
            for point in result['comparison_points']:
                if point.get('error_message'):
                    print(f"  - Flow {point['flow']}m³/hr: {point['error_message']}")
                elif point.get('brain_head') is None:
                    print(f"  - Flow {point['flow']}m³/hr: No Brain prediction available")
                else:
                    print(f"  - Flow {point['flow']}m³/hr: Brain predicted {point['brain_head']:.2f}m")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

def test_valid_diameter():
    """
    Test that the system works correctly with a valid diameter.
    """
    print("\n" + "="*60)
    print("Testing with valid diameter for pump 100-200 2F...")
    print("Testing with diameter: 200mm (valid, exists in curves)")
    
    # Create test data with valid diameter
    test_data = {
        'pump_code': '100-200 2F',
        'ground_truth_points': [
            {
                'flow': 400,
                'head': 45,
                'efficiency': 80,
                'power': 30,
                'diameter': 200  # This is a valid diameter
            }
        ]
    }
    
    from app.route_modules.brain_admin import ManufacturerComparisonEngine
    from app.pump_repository import get_pump_repository
    
    brain_admin = ManufacturerComparisonEngine()
    pump_repo = get_pump_repository()
    
    try:
        result = brain_admin.process_calibration_data(
            test_data['pump_code'],
            test_data['ground_truth_points'],
            pump_repo
        )
        
        print("\n✅ Processing completed successfully!")
        
        # Check for diameter warnings (should be none)
        if result.get('diameter_warnings'):
            print("\n⚠️ Unexpected diameter warnings:")
            for warning in result['diameter_warnings']:
                print(f"  - {warning}")
        else:
            print("\n✅ No diameter warnings (as expected)")
        
        # Check comparison points
        if result.get('comparison_points'):
            print(f"\n📊 Comparison points generated: {len(result['comparison_points'])}")
            valid_predictions = [p for p in result['comparison_points'] if p.get('brain_head') is not None]
            print(f"  - Valid Brain predictions: {len(valid_predictions)}")
            
            for point in result['comparison_points'][:3]:  # Show first 3 points
                if point.get('brain_head') is not None:
                    print(f"  - Flow {point['flow']:.1f}m³/hr: Brain={point['brain_head']:.2f}m, Truth={point['truth_head']:.2f}m")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Diameter Validation Test Suite")
    print("="*60)
    
    # Test 1: Out of range diameter
    test_diameter_out_of_range()
    
    # Test 2: Valid diameter
    test_valid_diameter()
    
    print("\n" + "="*60)
    print("Test suite completed!")