"""
Polymorphic Physics Models for Pump Performance Calculations
==============================================================

This module contains pump-type-specific physics models that define the exponents
used in affinity law calculations. Different pump types exhibit different scaling
behaviors when their impellers are trimmed, and this module captures those
variations based on engineering research.

The Brain uses these models to achieve the highest level of engineering accuracy
in performance calculations. This is the single source of truth for all physics
formulas - logic lives in the code, not in the database.

Author: APE Pumps Brain System
Date: August 18, 2025
"""

from .config_manager import config

# Pump Type Physics Models
# Each pump type has unique exponents for how performance scales with impeller diameter
PUMP_TYPE_EXPONENTS = {
    'AXIAL_FLOW': {
        'flow_exponent_x': config.get('physics_models_constants', 'axial_flow_pump_flow_exponent_value'),
        'head_exponent_y': config.get('physics_models_constants', 'axial_flow_pump_head_exponent_value'),
        'power_exponent_z': config.get('physics_models_constants', 'axial_flow_pump_power_exponent_value'),
        'npshr_exponent_alpha': config.get('physics_models_constants', 'axial_flow_pump_npsh_exponent_value'),
        'description': 'Axial flow pumps with propeller-type impellers'
    },
    
    'END_SUCTION': {
        'flow_exponent_x': config.get('physics_models_constants', 'end_suction_pump_flow_exponent_value'),
        'head_exponent_y': config.get('physics_models_constants', 'end_suction_pump_head_exponent_value'),
        'power_exponent_z': config.get('physics_models_constants', 'end_suction_pump_power_exponent_value'),
        'npshr_exponent_alpha': config.get('physics_models_constants', 'end_suction_pump_npsh_exponent_value'),
        'description': 'End suction radial flow centrifugal pumps'
    },
    
    'HORIZONTAL_SPLIT_CASE': {
        'flow_exponent_x': config.get('physics_models_constants', 'horizontal_split_case_pump_flow_exponent_value'),
        'head_exponent_y': config.get('physics_models_constants', 'horizontal_split_case_pump_head_exponent_value'),
        'power_exponent_z': config.get('physics_models_constants', 'horizontal_split_case_pump_power_exponent_value'),
        'npshr_exponent_alpha': config.get('physics_models_constants', 'horizontal_split_case_pump_npsh_exponent_value'),
        'description': 'Horizontal split case pumps (HSC)'
    },
    
    'MULTI_STAGE': {
        'flow_exponent_x': config.get('physics_models_constants', 'multi_stage_pump_flow_exponent_value'),
        'head_exponent_y': config.get('physics_models_constants', 'multi_stage_pump_head_exponent_value'),
        'power_exponent_z': config.get('physics_models_constants', 'multi_stage_pump_power_exponent_value'),
        'npshr_exponent_alpha': config.get('physics_models_constants', 'multi_stage_pump_npsh_exponent_value'),
        'description': 'Multi-stage radial flow pumps'
    },
    
    'VERTICAL_TURBINE': {
        'flow_exponent_x': config.get('physics_models_constants', 'vertical_turbine_pump_flow_exponent_value'),
        'head_exponent_y': config.get('physics_models_constants', 'vertical_turbine_pump_head_exponent_value'),
        'power_exponent_z': config.get('physics_models_constants', 'vertical_turbine_pump_power_exponent_value'),
        'npshr_exponent_alpha': config.get('physics_models_constants', 'vertical_turbine_pump_npsh_exponent_value'),
        'description': 'Vertical turbine pumps with mixed-flow bowls'
    },
    
    # Default fallback for unknown pump types - standard affinity laws
    'DEFAULT': {
        'flow_exponent_x': config.get('physics_models_constants', 'default_pump_flow_exponent_value'),
        'head_exponent_y': config.get('physics_models_constants', 'default_pump_head_exponent_value'),
        'power_exponent_z': config.get('physics_models_constants', 'default_pump_power_exponent_value'),
        'npshr_exponent_alpha': config.get('physics_models_constants', 'default_pump_npsh_exponent_value'),
        'description': 'Standard affinity laws for general centrifugal pumps'
    }
}

# Pump type name mappings for normalization
# Maps various pump type descriptions to standard keys
PUMP_TYPE_MAPPINGS = {
    # Axial flow variations
    'AXIAL': 'AXIAL_FLOW',
    'AXIAL FLOW': 'AXIAL_FLOW',
    'PROPELLER': 'AXIAL_FLOW',
    
    # End suction variations
    'END SUCTION': 'END_SUCTION',
    'END-SUCTION': 'END_SUCTION',
    'RADIAL': 'END_SUCTION',
    'CENTRIFUGAL': 'END_SUCTION',
    
    # Horizontal split case variations
    'HSC': 'HORIZONTAL_SPLIT_CASE',
    'HORIZONTAL SPLIT': 'HORIZONTAL_SPLIT_CASE',
    'SPLIT CASE': 'HORIZONTAL_SPLIT_CASE',
    
    # Multi-stage variations
    'MULTISTAGE': 'MULTI_STAGE',
    'MULTI-STAGE': 'MULTI_STAGE',
    'MULTI STAGE': 'MULTI_STAGE',
    
    # Vertical turbine variations
    'VTP': 'VERTICAL_TURBINE',
    'VERTICAL': 'VERTICAL_TURBINE',
    'TURBINE': 'VERTICAL_TURBINE',
    'MIXED FLOW': 'VERTICAL_TURBINE',
    'MIXED-FLOW': 'VERTICAL_TURBINE'
}

def normalize_pump_type(pump_type: str) -> str:
    """
    Normalize pump type string to match our physics model keys.
    
    Args:
        pump_type: Raw pump type string from database
        
    Returns:
        Normalized pump type key for physics model lookup
    """
    if not pump_type:
        return 'DEFAULT'
    
    # Convert to uppercase and strip whitespace
    normalized = pump_type.upper().strip()
    
    # Check direct match first
    if normalized in PUMP_TYPE_EXPONENTS:
        return normalized
    
    # Check mappings
    if normalized in PUMP_TYPE_MAPPINGS:
        return PUMP_TYPE_MAPPINGS[normalized]
    
    # Default fallback
    return 'DEFAULT'

def get_exponents_for_pump_type(pump_type: str) -> dict:
    """
    Get the physics model exponents for a specific pump type.
    
    Args:
        pump_type: Pump type string
        
    Returns:
        Dictionary of exponents for affinity law calculations
    """
    normalized_type = normalize_pump_type(pump_type)
    return PUMP_TYPE_EXPONENTS[normalized_type].copy()