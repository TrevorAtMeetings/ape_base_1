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

# Pump Type Physics Models
# Each pump type has unique exponents for how performance scales with impeller diameter
PUMP_TYPE_EXPONENTS = {
    'AXIAL_FLOW': {
        'flow_exponent_x': 0.95,        # Flow scales slightly less than linear (0.90-1.00)
        'head_exponent_y': 1.65,        # Head scales less than quadratic (1.50-1.80)
        'power_exponent_z': 2.60,       # Power scales less than cubic (2.40-2.80)
        'npshr_exponent_alpha': 1.70,   # NPSH requirement scaling (1.6-1.8)
        'description': 'Axial flow pumps with propeller-type impellers'
    },
    
    'END_SUCTION': {
        'flow_exponent_x': 1.00,        # Flow scales linearly (0.98-1.02)
        'head_exponent_y': 1.95,        # Head scales nearly quadratic (1.90-2.00)
        'power_exponent_z': 2.93,       # Power scales nearly cubic (2.85-3.00)
        'npshr_exponent_alpha': 1.95,   # NPSH requirement scaling (1.9-2.0)
        'description': 'End suction radial flow centrifugal pumps'
    },
    
    'HORIZONTAL_SPLIT_CASE': {
        'flow_exponent_x': 1.00,        # Flow scales linearly
        'head_exponent_y': 2.01,        # Head scales quadratically (1.98-2.05)
        'power_exponent_z': 3.00,       # Power scales cubically (2.95-3.05)
        'npshr_exponent_alpha': 2.00,   # NPSH requirement scaling
        'description': 'Horizontal split case pumps (HSC)'
    },
    
    'MULTI_STAGE': {
        'flow_exponent_x': 1.00,        # Flow scales linearly
        'head_exponent_y': 1.97,        # Head scales nearly quadratic (1.95-2.00)
        'power_exponent_z': 2.95,       # Power scales nearly cubic (2.9-3.0)
        'npshr_exponent_alpha': 2.00,   # NPSH requirement scaling
        'description': 'Multi-stage radial flow pumps'
    },
    
    'VERTICAL_TURBINE': {
        'flow_exponent_x': 0.97,        # Flow scales slightly less than linear (0.95-1.00)
        'head_exponent_y': 1.85,        # Head scales less than quadratic (1.80-1.90)
        'power_exponent_z': 2.80,       # Power scales less than cubic (2.7-2.9)
        'npshr_exponent_alpha': 1.80,   # NPSH requirement scaling
        'description': 'Vertical turbine pumps with mixed-flow bowls'
    },
    
    # Default fallback for unknown pump types - standard affinity laws
    'DEFAULT': {
        'flow_exponent_x': 1.00,        # Standard linear flow scaling
        'head_exponent_y': 2.00,        # Standard quadratic head scaling
        'power_exponent_z': 3.00,       # Standard cubic power scaling
        'npshr_exponent_alpha': 2.00,   # Standard NPSH scaling
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