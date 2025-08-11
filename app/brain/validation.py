"""
Data Validation Module
======================
Data integrity validation and unit conversions
"""

import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data integrity and handles conversions"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        
        # Unit conversion factors
        self.conversions = {
            # Flow conversions to m³/hr
            'gpm_to_m3hr': 0.227124,
            'lps_to_m3hr': 3.6,
            'lpm_to_m3hr': 0.06,
            'mgd_to_m3hr': 157.725,
            
            # Head conversions to meters
            'ft_to_m': 0.3048,
            'psi_to_m': 0.703070,
            'bar_to_m': 10.1972,
            'kpa_to_m': 0.101972,
            
            # Power conversions to kW
            'hp_to_kw': 0.745699872,
            'w_to_kw': 0.001,
            
            # Diameter conversions to mm
            'in_to_mm': 25.4,
            'cm_to_mm': 10,
            'm_to_mm': 1000
        }
        
        # Validation rules
        self.validation_rules = {
            'flow_m3hr': {'min': 0.1, 'max': 50000},
            'head_m': {'min': 0.1, 'max': 5000},
            'efficiency_pct': {'min': 0, 'max': 100},
            'power_kw': {'min': 0, 'max': 10000},
            'npshr_m': {'min': 0, 'max': 100},
            'impeller_diameter_mm': {'min': 50, 'max': 5000},
            'speed_rpm': {'min': 100, 'max': 7200}
        }
    
    def validate_operating_point(self, flow: float, head: float) -> Dict[str, Any]:
        """
        Validate operating point parameters.
        
        Args:
            flow: Flow rate in m³/hr
            head: Head in meters
        
        Returns:
            Validation results
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check flow
            if flow <= 0:
                validation['valid'] = False
                validation['errors'].append('Flow must be positive')
            elif flow < self.validation_rules['flow_m3hr']['min']:
                validation['warnings'].append(f'Flow {flow} m³/hr is very low')
            elif flow > self.validation_rules['flow_m3hr']['max']:
                validation['warnings'].append(f'Flow {flow} m³/hr is unusually high')
            
            # Check head
            if head <= 0:
                validation['valid'] = False
                validation['errors'].append('Head must be positive')
            elif head < self.validation_rules['head_m']['min']:
                validation['warnings'].append(f'Head {head} m is very low')
            elif head > self.validation_rules['head_m']['max']:
                validation['warnings'].append(f'Head {head} m is unusually high')
            
            # Check for unrealistic combinations
            specific_speed = self._calculate_specific_speed(flow, head)
            if specific_speed < 10:
                validation['warnings'].append('Very low specific speed - unusual combination')
            elif specific_speed > 10000:
                validation['warnings'].append('Very high specific speed - unusual combination')
            
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f'Validation error: {str(e)}')
        
        return validation
    
    def validate_pump_data(self, pump_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate pump data completeness and integrity.
        
        Args:
            pump_data: Pump data dictionary
        
        Returns:
            Validation results with issues identified
        """
        validation = {
            'valid': True,
            'issues': [],
            'missing_fields': [],
            'data_quality_score': 100
        }
        
        try:
            # Check required fields
            required_fields = ['pump_code', 'curves']
            for field in required_fields:
                if field not in pump_data or not pump_data[field]:
                    validation['missing_fields'].append(field)
                    validation['data_quality_score'] -= 20
            
            # Check specifications
            specs = pump_data.get('specifications', {})
            if not specs:
                validation['issues'].append('No specifications available')
                validation['data_quality_score'] -= 10
            else:
                # Check BEP data
                if not specs.get('bep_flow_m3hr') or not specs.get('bep_head_m'):
                    validation['issues'].append('BEP data missing')
                    validation['data_quality_score'] -= 15
                
                # Check impeller data
                if not specs.get('min_impeller_mm') or not specs.get('max_impeller_mm'):
                    validation['issues'].append('Impeller diameter range missing')
                    validation['data_quality_score'] -= 10
            
            # Check curves
            curves = pump_data.get('curves', [])
            if not curves:
                validation['valid'] = False
                validation['issues'].append('No performance curves')
                validation['data_quality_score'] = 0
            else:
                # Check curve quality
                valid_curves = 0
                for curve in curves:
                    points = curve.get('performance_points', [])
                    if len(points) >= 3:  # Minimum for interpolation
                        valid_curves += 1
                
                if valid_curves == 0:
                    validation['valid'] = False
                    validation['issues'].append('No valid curves (need ≥3 points)')
                    validation['data_quality_score'] = 0
                elif valid_curves < len(curves) / 2:
                    validation['issues'].append(f'Only {valid_curves}/{len(curves)} curves valid')
                    validation['data_quality_score'] -= 20
            
            # Check for NPSH data
            has_npsh = False
            for curve in curves:
                points = curve.get('performance_points', [])
                if any(p.get('npshr_m') for p in points):
                    has_npsh = True
                    break
            
            if not has_npsh:
                validation['issues'].append('No NPSH data available')
                validation['data_quality_score'] -= 5
            
            # Set overall validity
            if validation['data_quality_score'] < 50:
                validation['valid'] = False
            
        except Exception as e:
            validation['valid'] = False
            validation['issues'].append(f'Validation error: {str(e)}')
            validation['data_quality_score'] = 0
        
        return validation
    
    def convert_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert between units.
        
        Args:
            value: Numeric value to convert
            from_unit: Source unit (e.g., 'gpm', 'ft')
            to_unit: Target unit (e.g., 'm3hr', 'm')
        
        Returns:
            Converted value
        """
        try:
            # Handle same unit
            if from_unit.lower() == to_unit.lower():
                return value
            
            # Normalize unit names
            from_unit = from_unit.lower().replace(' ', '').replace('/', '')
            to_unit = to_unit.lower().replace(' ', '').replace('/', '')
            
            # Direct conversion lookup
            conversion_key = f"{from_unit}_to_{to_unit}"
            if conversion_key in self.conversions:
                return value * self.conversions[conversion_key]
            
            # Reverse conversion
            reverse_key = f"{to_unit}_to_{from_unit}"
            if reverse_key in self.conversions:
                return value / self.conversions[reverse_key]
            
            # Complex conversions (through intermediate unit)
            # Flow: gpm -> m3hr
            if 'gpm' in from_unit and 'm3' in to_unit:
                return value * self.conversions['gpm_to_m3hr']
            elif 'm3' in from_unit and 'gpm' in to_unit:
                return value / self.conversions['gpm_to_m3hr']
            
            # Head: ft -> m
            if 'ft' in from_unit and 'm' in to_unit and 'mm' not in to_unit:
                return value * self.conversions['ft_to_m']
            elif 'm' in from_unit and 'ft' in to_unit and 'mm' not in from_unit:
                return value / self.conversions['ft_to_m']
            
            # Power: hp -> kw
            if 'hp' in from_unit and 'kw' in to_unit:
                return value * self.conversions['hp_to_kw']
            elif 'kw' in from_unit and 'hp' in to_unit:
                return value / self.conversions['hp_to_kw']
            
            # If no conversion found, log warning and return original
            logger.warning(f"No conversion found from {from_unit} to {to_unit}")
            return value
            
        except Exception as e:
            logger.error(f"Error converting units: {str(e)}")
            return value
    
    def handle_missing_data(self, pump: Dict[str, Any], 
                          strategy: str = "interpolate") -> Dict[str, Any]:
        """
        Handle missing data in pump specifications.
        
        Args:
            pump: Pump data with potential missing fields
            strategy: Strategy for handling ('interpolate', 'default', 'exclude')
        
        Returns:
            Pump data with missing fields handled
        """
        handled_pump = pump.copy()
        
        try:
            specs = handled_pump.get('specifications', {})
            
            if strategy == "interpolate":
                # Try to interpolate missing BEP from curves
                if not specs.get('bep_flow_m3hr') or not specs.get('bep_head_m'):
                    bep = self._find_bep_from_curves(handled_pump.get('curves', []))
                    if bep:
                        specs['bep_flow_m3hr'] = bep['flow']
                        specs['bep_head_m'] = bep['head']
                        logger.info(f"Interpolated BEP for pump {pump.get('pump_code')}")
                
                # Try to determine impeller range from curves
                if not specs.get('min_impeller_mm') or not specs.get('max_impeller_mm'):
                    imp_range = self._find_impeller_range(handled_pump.get('curves', []))
                    if imp_range:
                        specs['min_impeller_mm'] = imp_range['min']
                        specs['max_impeller_mm'] = imp_range['max']
                        logger.info(f"Determined impeller range for pump {pump.get('pump_code')}")
                
            elif strategy == "default":
                # REMOVED: No default values applied - reject incomplete pumps instead
                missing_fields = []
                if not specs.get('bep_flow_m3hr'):
                    missing_fields.append('bep_flow_m3hr')
                if not specs.get('bep_head_m'):
                    missing_fields.append('bep_head_m')
                if not specs.get('min_impeller_mm'):
                    missing_fields.append('min_impeller_mm')
                if not specs.get('max_impeller_mm'):
                    missing_fields.append('max_impeller_mm')
                
                if missing_fields:
                    logger.error(f"Pump {pump.get('pump_code')} missing critical data: {missing_fields} - NO FALLBACKS APPLIED")
                    handled_pump['data_incomplete'] = True
                    handled_pump['missing_critical_data'] = True
                    handled_pump['exclusion_reasons'] = [f'Missing manufacturer data: {", ".join(missing_fields)}']
                
            elif strategy == "exclude":
                # Mark pump as incomplete
                if not specs.get('bep_flow_m3hr') or not specs.get('bep_head_m'):
                    handled_pump['data_incomplete'] = True
                    handled_pump['missing_critical_data'] = True
                    logger.warning(f"Pump {pump.get('pump_code')} marked incomplete")
            
            handled_pump['specifications'] = specs
            
        except Exception as e:
            logger.error(f"Error handling missing data: {str(e)}")
        
        return handled_pump
    
    def _calculate_specific_speed(self, flow_m3hr: float, head_m: float, 
                                 speed_rpm: float = 1450) -> float:
        """
        Calculate specific speed (Ns).
        
        Args:
            flow_m3hr: Flow rate in m³/hr
            head_m: Head in meters
            speed_rpm: Speed in RPM (default 1450)
        
        Returns:
            Specific speed
        """
        # Convert to m³/s
        flow_m3s = flow_m3hr / 3600
        
        # Ns = N × √Q / H^(3/4)
        # Where N is rpm, Q is m³/s, H is meters
        if head_m > 0:
            ns = speed_rpm * (flow_m3s ** 0.5) / (head_m ** 0.75)
            return ns * 51.64  # Convert to dimensionless
        return 0
    
    def _find_bep_from_curves(self, curves: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """
        Find BEP from performance curves.
        
        Args:
            curves: List of performance curves
        
        Returns:
            BEP flow and head if found
        """
        best_efficiency = 0
        best_point = None
        
        for curve in curves:
            points = curve.get('performance_points', [])
            for point in points:
                eff = point.get('efficiency_pct', 0)
                if eff > best_efficiency:
                    best_efficiency = eff
                    best_point = {
                        'flow': point.get('flow_m3hr'),
                        'head': point.get('head_m'),
                        'efficiency': eff
                    }
        
        return best_point if best_point and best_efficiency > 0 else None
    
    def _find_impeller_range(self, curves: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """
        Find impeller diameter range from curves.
        
        Args:
            curves: List of performance curves
        
        Returns:
            Min and max impeller diameters if found
        """
        diameters = []
        
        for curve in curves:
            diameter = curve.get('impeller_diameter_mm')
            if diameter and diameter > 0:
                diameters.append(diameter)
        
        if diameters:
            return {
                'min': min(diameters),
                'max': max(diameters)
            }
        
        return None