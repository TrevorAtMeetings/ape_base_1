"""
Performance Validation Module
=============================
Performance validation utilities and envelope checking
"""

import logging
from typing import Dict, Any
from .physics_models import get_exponents_for_pump_type

logger = logging.getLogger(__name__)


class PerformanceValidator:
    """Performance validation and utility methods"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain

    def get_exponents_for_pump(self, pump_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get the pump-type-specific physics model exponents.
        """
        pump_type = pump_data.get('pump_type', '')
        return get_exponents_for_pump_type(pump_type)

    def get_calibration_factor(self, factor_name: str, default_value: float = 1.0) -> float:
        """Get calibration factor with fallback to default."""
        # Try to get from brain's calibration factors
        if hasattr(self.brain, 'get_config_service'):
            try:
                config_service = self.brain.get_config_service()
                calibration_factors = config_service.get_calibration_factors()
                return calibration_factors.get(factor_name, default_value)
            except:
                pass
        return default_value

    def validate_envelope(self, pump: Dict[str, Any], flow: float, head: float) -> Dict[str, Any]:
        """
        Validate operating point within pump envelope.
        
        Args:
            pump: Pump data
            flow: Operating flow
            head: Operating head
        
        Returns:
            Validation results
        """
        validation = {
            'valid': True,
            'warnings': [],
            'recommendations': []
        }
        
        try:
            specs = pump.get('specifications', {})
            
            # Check BEP proximity
            bep_flow = specs.get('bep_flow_m3hr', 0)
            if bep_flow > 0:
                qbp = (flow / bep_flow) * 100
                
                if qbp < 60:
                    validation['warnings'].append(f'Operating at {qbp:.0f}% of BEP - risk of recirculation')
                    validation['recommendations'].append('Consider smaller pump or VFD')
                elif qbp > 130:
                    validation['warnings'].append(f'Operating at {qbp:.0f}% of BEP - risk of cavitation')
                    validation['recommendations'].append('Consider larger pump')
                elif 95 <= qbp <= 105:
                    validation['recommendations'].append('Excellent - operating near BEP')
            
            # Check head limits
            max_head = specs.get('max_head_m', 0)
            if max_head > 0 and head > max_head * 0.9:
                validation['warnings'].append('Operating near maximum head')
            
            # Check flow limits
            max_flow = specs.get('max_flow_m3hr', 0)
            if max_flow > 0 and flow > max_flow * 0.9:
                validation['warnings'].append('Operating near maximum flow')
            
            if validation['warnings']:
                validation['valid'] = False
            
        except Exception as e:
            logger.error(f"Error validating envelope: {str(e)}")
            validation['warnings'].append(f'Validation error: {str(e)}')
            validation['valid'] = False
        
        return validation