"""
Test file for physics_models.py configuration
"""

from .config_manager import config

# Test the actual config calls we're using
def test_physics_config():
    print("Testing physics model config calls:")
    
    # Test all the calls used in physics_models.py
    test_calls = [
        ('axial_flow_pump_flow_exponent_value', 'Axial flow exponent'),
        ('axial_flow_pump_head_exponent_value', 'Axial head exponent'),
        ('axial_flow_pump_power_exponent_value', 'Axial power exponent'),
        ('axial_flow_pump_npsh_exponent_value', 'Axial NPSH exponent'),
        ('end_suction_pump_flow_exponent_value', 'End suction flow exponent'),
        ('end_suction_pump_head_exponent_value', 'End suction head exponent'),
        ('end_suction_pump_power_exponent_value', 'End suction power exponent'),
        ('end_suction_pump_npsh_exponent_value', 'End suction NPSH exponent'),
        ('default_pump_flow_exponent_value', 'Default flow exponent'),
        ('default_pump_head_exponent_value', 'Default head exponent'),
        ('default_pump_power_exponent_value', 'Default power exponent'),
        ('default_pump_npsh_exponent_value', 'Default NPSH exponent')
    ]
    
    for key, description in test_calls:
        try:
            value = config.get('physics_models_constants', key)
            print(f"SUCCESS: {description} = {value}")
        except Exception as e:
            print(f"ERROR: {description} - {e}")
            return False
    
    return True

if __name__ == "__main__":
    test_physics_config()