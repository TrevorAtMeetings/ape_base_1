"""
Unit tests for PumpBrain performance calculation
"""
import unittest
import sys
import os
import logging

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.pump_brain import PumpBrain

# Set up detailed logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TestPumpBrainPerformance(unittest.TestCase):
    """Test pump brain performance calculations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.brain = PumpBrain()
        # Ensure the repository is loaded
        self.brain.repository.load_catalog()
    
    def test_calculate_at_point_specific_pump(self):
        """Test calculate_at_point for WXH-40-135 2P at 18 m³/hr @ 15m"""
        print("\n=== FOCUSED UNIT TEST: WXH-40-135 2P ===")
        
        # Find the specific pump
        pump_models = self.brain.repository.get_pump_models()
        target_pump = None
        
        for pump in pump_models:
            if pump.get('pump_code') == 'WXH-40-135 2P':
                target_pump = pump
                break
        
        self.assertIsNotNone(target_pump, "WXH-40-135 2P pump not found in repository")
        
        print(f"Found pump: {target_pump.get('pump_code')}")
        print(f"Pump has {len(target_pump.get('curves', []))} curves")
        
        # Test specific duty point
        flow = 18.0  # m³/hr
        head = 15.0  # m
        
        print(f"Testing duty point: {flow} m³/hr @ {head}m")
        
        # Call the method under test
        result = self.brain.performance.calculate_at_point(target_pump, flow, head)
        
        # Assert that result is not None
        self.assertIsNotNone(result, 
            f"calculate_at_point returned None for {target_pump.get('pump_code')} at {flow} m³/hr @ {head}m")
        
        print(f"SUCCESS: calculate_at_point returned: {result}")
        
        # Additional assertions if result is not None
        if result:
            self.assertIn('efficiency_pct', result, "Result missing efficiency_pct")
            self.assertIn('head_m', result, "Result missing head_m") 
            self.assertIn('power_kw', result, "Result missing power_kw")


if __name__ == '__main__':
    unittest.main()