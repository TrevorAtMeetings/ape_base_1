#!/usr/bin/env python3
"""
Test script for Ground Truth Calibration feature
Tests the Brain predictions against known values
"""

import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the application path
sys.path.insert(0, '/home/runner/workspace')

def test_calibration():
    """Test the Ground Truth Calibration functionality"""
    logger.info("="*60)
    logger.info("GROUND TRUTH CALIBRATION TEST")
    logger.info("="*60)
    
    from app.pump_brain import PumpBrain
    from app.pump_repository import PumpRepository
    
    # Initialize components
    logger.info("Initializing Brain and Repository...")
    brain = PumpBrain()
    pump_repo = PumpRepository()
    pump_repo.load_catalog()
    pump_models = pump_repo.get_pump_models()
    
    # Select a test pump (using a common pump)
    test_pump_code = "28 HC 6P"
    test_pump = None
    for pump in pump_models:
        if pump['pump_code'] == test_pump_code:
            test_pump = pump
            break
    
    if not test_pump:
        logger.error(f"Test pump {test_pump_code} not found!")
        return False
    
    # Define test duty point
    duty_flow = 1500  # m³/hr
    duty_head = 22    # m
    
    # Define "ground truth" values (simulated manufacturer data)
    # These would normally come from actual datasheets
    truth_diameter = 475    # mm
    truth_efficiency = 82.5  # %
    truth_power = 115.5     # kW
    
    logger.info(f"\nTest Pump: {test_pump_code}")
    logger.info(f"Duty Point: {duty_flow} m³/hr @ {duty_head}m")
    logger.info(f"\nGround Truth Values (Manufacturer):")
    logger.info(f"  Diameter: {truth_diameter} mm")
    logger.info(f"  Efficiency: {truth_efficiency}%")
    logger.info(f"  Power: {truth_power} kW")
    
    # Get Brain prediction
    logger.info("\nCalculating Brain predictions...")
    brain_result = brain.performance.calculate_at_point_industry_standard(
        test_pump, duty_flow, duty_head
    )
    
    if not brain_result:
        logger.error("Brain could not calculate performance!")
        return False
    
    # Extract Brain predictions
    brain_diameter = brain_result.get('diameter', 0)
    brain_efficiency = brain_result.get('efficiency', 0)
    brain_power = brain_result.get('power', 0)
    
    logger.info(f"\nBrain Predictions:")
    logger.info(f"  Diameter: {brain_diameter:.1f} mm")
    logger.info(f"  Efficiency: {brain_efficiency:.1f}%")
    logger.info(f"  Power: {brain_power:.1f} kW")
    
    # Calculate deltas
    def calculate_delta(truth, prediction):
        if truth == 0:
            return 0
        return ((prediction - truth) / truth) * 100
    
    delta_diameter = calculate_delta(truth_diameter, brain_diameter)
    delta_efficiency = calculate_delta(truth_efficiency, brain_efficiency)
    delta_power = calculate_delta(truth_power, brain_power)
    
    logger.info(f"\nCalibration Deltas:")
    logger.info(f"  Diameter Delta: {delta_diameter:+.2f}%")
    logger.info(f"  Efficiency Delta: {delta_efficiency:+.2f}%")
    logger.info(f"  Power Delta: {delta_power:+.2f}%")
    
    # Calculate average delta
    avg_delta = (abs(delta_diameter) + abs(delta_efficiency) + abs(delta_power)) / 3
    
    logger.info(f"\nAverage Delta: {avg_delta:.2f}%")
    
    # Evaluate accuracy
    if avg_delta < 2:
        logger.info("✅ EXCELLENT ACCURACY - Brain predictions are highly reliable")
        accuracy_level = "Excellent"
    elif avg_delta < 5:
        logger.info("⚠️ GOOD ACCURACY - Minor adjustments may improve predictions")
        accuracy_level = "Good"
    else:
        logger.info("❌ SIGNIFICANT DEVIATION - Physics model may need calibration")
        accuracy_level = "Needs Calibration"
    
    logger.info("\n" + "="*60)
    logger.info("CALIBRATION TEST COMPLETE")
    logger.info(f"Accuracy Level: {accuracy_level}")
    logger.info("="*60)
    
    # Test the polymorphic physics model effect
    logger.info("\nTesting Polymorphic Physics Model Effect...")
    if 'pump_type' in test_pump:
        pump_type = test_pump['pump_type']
        logger.info(f"Pump Type: {pump_type}")
        
        from app.brain.physics_models import PUMP_TYPE_EXPONENTS, normalize_pump_type
        normalized_type = normalize_pump_type(pump_type)
        
        if normalized_type in PUMP_TYPE_EXPONENTS:
            exponents = PUMP_TYPE_EXPONENTS[normalized_type]
            logger.info(f"Using {normalized_type} physics model:")
            logger.info(f"  Flow exponent: {exponents['flow']}")
            logger.info(f"  Head exponent: {exponents['head']}")
            logger.info(f"  Power exponent: {exponents['power']}")
        else:
            logger.info("Using standard affinity law exponents")
    
    return avg_delta < 5  # Return True if accuracy is acceptable

if __name__ == "__main__":
    success = test_calibration()
    sys.exit(0 if success else 1)