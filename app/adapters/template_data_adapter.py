"""
Template Data Adapter for V2 Enhanced Reports
=============================================
Transforms data structures for V2 template compatibility without
affecting existing functionality.

Author: APE Pumps Engineering  
Date: August 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TemplateDataAdapter:
    """
    Adapts data structures for V2 template compatibility.
    Provides both backward compatibility and enhanced features.
    """
    
    @staticmethod
    def adapt_for_v2_template(base_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform existing flat data structure to V2 nested structure.
        
        This method takes the current flat data structure and creates
        the nested objects that V2 template expects, while preserving
        all original data for backward compatibility.
        
        Args:
            base_data: Original flat data structure from Brain
            
        Returns:
            Enhanced data structure with V2 nested objects
        """
        if not base_data:
            return base_data
            
        logger.debug(f"Adapting data for V2 template: {base_data.get('pump_code', 'Unknown')}")
        
        # Preserve all original data
        enhanced_data = dict(base_data)
        
        # Add nested operating_point structure if not already present
        if 'operating_point' not in enhanced_data:
            enhanced_data['operating_point'] = {
                'efficiency_pct': base_data.get('efficiency_pct'),
                'power_kw': base_data.get('power_kw'),
                'flow_m3hr': base_data.get('flow_m3hr'),
                'head_m': base_data.get('head_m'),
                'npshr_m': base_data.get('npshr_m'),
                'impeller_diameter_mm': base_data.get('impeller_diameter_mm'),
                'test_speed_rpm': base_data.get('test_speed_rpm'),
                'extrapolated': base_data.get('extrapolated', False),
                'qbp_percent': base_data.get('qbp_percent'),
                'trim_percent': base_data.get('trim_percent', 0)
            }
        
        # Add nested selected_curve structure if not already present
        if 'selected_curve' not in enhanced_data:
            enhanced_data['selected_curve'] = {
                'impeller_diameter_mm': base_data.get('impeller_diameter_mm'),
                'test_speed_rpm': base_data.get('test_speed_rpm'),
                'curve_data': base_data.get('curve_data', {}),
                'max_impeller_mm': base_data.get('max_impeller_mm'),
                'min_impeller_mm': base_data.get('min_impeller_mm')
            }
            
        return enhanced_data
    
    @staticmethod
    def is_enhanced_data(data: Dict[str, Any]) -> bool:
        """
        Check if data already has V2 enhanced structure.
        
        Args:
            data: Data dictionary to check
            
        Returns:
            True if data has V2 nested structures
        """
        return ('operating_point' in data and 
                'selected_curve' in data and
                isinstance(data['operating_point'], dict) and
                isinstance(data['selected_curve'], dict))
    
    @staticmethod
    def adapt_alternatives_list(alternatives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Adapt a list of alternative pumps for V2 template.
        
        Args:
            alternatives: List of alternative pump data
            
        Returns:
            List of adapted alternative pump data
        """
        if not alternatives:
            return alternatives
            
        adapted_alternatives = []
        for alt in alternatives:
            adapted_alt = TemplateDataAdapter.adapt_for_v2_template(alt)
            adapted_alternatives.append(adapted_alt)
            
        logger.debug(f"Adapted {len(adapted_alternatives)} alternatives for V2")
        return adapted_alternatives
    
    @staticmethod
    def ensure_v2_compatibility(template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all template data is V2 compatible.
        
        This is the main entry point for adapting complete template data
        structures for V2 templates.
        
        Args:
            template_data: Complete template data dictionary
            
        Returns:
            V2-compatible template data dictionary
        """
        logger.debug("Ensuring V2 compatibility for template data")
        
        # Adapt main pump data
        if 'selected_pump' in template_data:
            template_data['selected_pump'] = TemplateDataAdapter.adapt_for_v2_template(
                template_data['selected_pump']
            )
        
        # Adapt alternatives
        if 'alternatives' in template_data:
            template_data['alternatives'] = TemplateDataAdapter.adapt_alternatives_list(
                template_data['alternatives']
            )
            
        # Ensure alternative_pumps compatibility (legacy field)
        if 'alternative_pumps' in template_data:
            template_data['alternative_pumps'] = TemplateDataAdapter.adapt_alternatives_list(
                template_data['alternative_pumps']
            )
            
        logger.debug("V2 compatibility ensured for template data")
        return template_data