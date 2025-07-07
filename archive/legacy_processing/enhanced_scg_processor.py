"""
Enhanced SCG Processor with Advanced Data Processing Techniques
Incorporates robust error handling, type conversion, and engineering precision
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSCGProcessor:
    """Advanced SCG processor with sophisticated data handling capabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processing_stats = {
            'files_processed': 0,
            'pumps_extracted': 0,
            'curves_processed': 0,
            'errors_encountered': 0,
            'warnings_generated': 0
        }
        
    # Enhanced helper functions for robust data processing
    def to_float(self, value: Any, default: float = 0.0) -> float:
        """Convert value to float with safe fallback"""
        if value is None or str(value).strip() == '':
            return default
        try:
            return float(str(value).strip())
        except (ValueError, TypeError):
            return default
    
    def to_int(self, value: Any, default: int = 0) -> int:
        """Convert value to int with safe fallback"""
        if value is None or str(value).strip() == '':
            return default
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return default
    
    def to_bool(self, value: Any, default: bool = False) -> bool:
        """Convert value to bool with safe fallback"""
        if value is None or str(value).strip() == '':
            return default
        try:
            str_val = str(value).strip().lower()
            return str_val in ('true', '1', 'yes', 'on')
        except (ValueError, TypeError):
            return default
    
    def parse_space_separated_floats(self, value: str) -> List[float]:
        """Parse space-separated float values with zero filtering"""
        if not value or str(value).strip() == '':
            return []
        try:
            parts = str(value).strip().split()
            floats = []
            for part in parts:
                try:
                    val = self.to_float(part)
                    if val != 0.0:  # Filter out zeros for cleaner data
                        floats.append(val)
                except:
                    continue
            return floats
        except Exception:
            return []
    
    def get_curve_series_data(self, raw_data: str, num_curves: int, data_type: str = "unknown") -> List[List[float]]:
        """Enhanced curve data parsing with comprehensive mismatch handling"""
        if not raw_data or str(raw_data).strip() == '':
            self.logger.warning(f"Empty {data_type} curve data provided")
            return [[] for _ in range(num_curves)]
        
        try:
            segments = str(raw_data).split('|')
            
            # Handle segment count mismatch with detailed logging
            if len(segments) != num_curves:
                self.logger.warning(f"{data_type} data segments ({len(segments)}) != expected curves ({num_curves})")
                self.processing_stats['warnings_generated'] += 1
                
                # Pad with empty segments if too few
                while len(segments) < num_curves:
                    segments.append('')
                # Truncate if too many
                segments = segments[:num_curves]
            
            result = []
            for i, segment in enumerate(segments):
                if segment.strip():
                    try:
                        values = []
                        for val_str in segment.split(';'):
                            if val_str.strip():
                                values.append(self.to_float(val_str))
                        result.append(values)
                    except Exception as e:
                        self.logger.warning(f"Error parsing {data_type} curve {i+1} data: {e}")
                        result.append([])
                else:
                    result.append([])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing {data_type} curve series data: {e}")
            self.processing_stats['errors_encountered'] += 1
            return [[] for _ in range(num_curves)]
    
    def calculate_enhanced_power_curve(self, flow_data: List[float], head_data: List[float], 
                                     eff_data: List[float], flow_unit: str = "m^3/hr", 
                                     head_unit: str = "m") -> List[float]:
        """Enhanced power calculation with engineering precision"""
        if not all([flow_data, head_data, eff_data]):
            return []
        
        # Use minimum length to handle jagged arrays safely
        min_len = min(len(flow_data), len(head_data), len(eff_data))
        if min_len == 0:
            return []
        
        # Engineering conversion factors (standard precision)
        flow_conversions = {
            'm^3/hr': 1.0 / 3600.0,  # to m³/s
            'l/s': 1.0 / 1000.0,     # to m³/s
            'gpm': 0.00006309,       # US gallons/min to m³/s
            'l/min': 1.0 / 60000.0   # to m³/s
        }
        
        head_conversions = {
            'm': 1.0,                # no conversion
            'ft': 0.3048,           # feet to meters
            'kPa': 0.102,           # kPa to meters (standard factor)
            'psi': 0.704            # psi to meters
        }
        
        con_flow = flow_conversions.get(flow_unit, 1.0 / 3600.0)
        con_head = head_conversions.get(head_unit, 1.0)
        
        power_calculated = []
        
        for i in range(min_len):
            q_val = flow_data[i]
            h_val = head_data[i]
            eff_val = eff_data[i]
            
            # Skip calculation if any value is invalid
            if eff_val <= 0 or q_val < 0 or h_val < 0:
                power_calculated.append(0.0)
                continue
            
            # Hydraulic power formula: P = (Q * H * ρ * g) / (3600 * η)
            # Using standard gravity (9.81 m/s²) and water density (1000 kg/m³)
            power_kw = (q_val * con_flow * h_val * con_head * 9.81) / (eff_val / 100.0)
            power_calculated.append(round(power_kw, 2))
        
        # Pad with zeros if original arrays were longer
        max_len = max(len(flow_data), len(head_data), len(eff_data))
        while len(power_calculated) < max_len:
            power_calculated.append(0.0)
        
        return power_calculated
    
    def process_enhanced_scg_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process SCG data with enhanced robustness and validation"""
        try:
            # Initialize structured data with proper typing
            structured_data = {
                "pump_info": {},
                "curves": []
            }
            
            pi = structured_data["pump_info"]  # Alias for cleaner code
            
            # Populate pump metadata with enhanced type conversion
            pump_fields = {
                'pPumpCode': str,
                'pSuppName': str,
                'pUnitFlow': str,
                'pUnitHead': str,
                'pPumpTestSpeed': self.to_int,
                'pBEPFlow': self.to_float,
                'pBEPHead': self.to_float,
                'pBEPEff': self.to_float,
                'pKWMax': self.to_float,
                'pFilter1': str,
                'pFilter2': str,
                'pFilter3': str
            }
            
            for field, converter in pump_fields.items():
                if converter == str:
                    pi[field] = raw_data.get(field, '').strip()
                else:
                    pi[field] = converter(raw_data.get(field, ''))
            
            # Enhanced parsing for space-separated values
            if 'pM_Diam' in raw_data:
                pi['impeller_diameters'] = self.parse_space_separated_floats(raw_data['pM_Diam'])
            
            if 'pM_Speed' in raw_data:
                pi['test_speeds'] = self.parse_space_separated_floats(raw_data['pM_Speed'])
            
            if 'pM_EffIso' in raw_data:
                pi['efficiency_iso'] = self.parse_space_separated_floats(raw_data['pM_EffIso'])
            
            # Determine number of curves with validation
            num_curves = self.to_int(raw_data.get('pHeadCurvesNo', '0'))
            if num_curves == 0:
                self.logger.warning("No curves specified in SCG data")
                return structured_data
            
            # Parse curve identifiers with enhanced fallback
            imp_str_raw = raw_data.get('pM_IMP', '')
            curve_identifiers = []
            
            for i in range(num_curves):
                start_idx = i * 8
                end_idx = start_idx + 8
                
                if start_idx < len(imp_str_raw):
                    identifier = imp_str_raw[start_idx:end_idx].strip()
                    if identifier:
                        curve_identifiers.append(identifier)
                    else:
                        curve_identifiers.append(f"Unknown_ID_{i+1}")
                else:
                    curve_identifiers.append(f"Curve_{i+1}")
            
            # Parse curve data with enhanced error handling
            flow_series = self.get_curve_series_data(raw_data.get('pM_FLOW', ''), num_curves, "flow")
            head_series = self.get_curve_series_data(raw_data.get('pM_HEAD', ''), num_curves, "head")
            eff_series = self.get_curve_series_data(raw_data.get('pM_EFF', ''), num_curves, "efficiency")
            npsh_series = self.get_curve_series_data(raw_data.get('pM_NP', ''), num_curves, "NPSH")
            
            # Construct curve objects with enhanced power calculation
            for i in range(num_curves):
                curve = {
                    'identifier': curve_identifiers[i],
                    'flow_data': flow_series[i] if i < len(flow_series) else [],
                    'head_data': head_series[i] if i < len(head_series) else [],
                    'efficiency_data': eff_series[i] if i < len(eff_series) else [],
                    'npsh_data': npsh_series[i] if i < len(npsh_series) else [],
                    'power_data': []  # Will be calculated
                }
                
                # Calculate power with enhanced precision
                if curve['flow_data'] and curve['head_data'] and curve['efficiency_data']:
                    curve['power_data'] = self.calculate_enhanced_power_curve(
                        curve['flow_data'],
                        curve['head_data'],
                        curve['efficiency_data'],
                        pi.get('pUnitFlow', 'm^3/hr'),
                        pi.get('pUnitHead', 'm')
                    )
                    
                    # Log power calculation statistics
                    if curve['power_data']:
                        avg_power = sum(curve['power_data']) / len(curve['power_data'])
                        self.logger.info(f"Curve {i+1} ({curve['identifier']}): Average power {avg_power:.2f} kW")
                
                structured_data["curves"].append(curve)
            
            # Update processing statistics
            self.processing_stats['pumps_extracted'] += 1
            self.processing_stats['curves_processed'] += len(structured_data["curves"])
            
            return structured_data
            
        except Exception as e:
            self.logger.error(f"Error in enhanced SCG processing: {e}")
            self.processing_stats['errors_encountered'] += 1
            return {"pump_info": {}, "curves": []}
    
    def validate_processed_data(self, structured_data: Dict[str, Any]) -> List[str]:
        """Comprehensive validation of processed SCG data"""
        warnings = []
        
        if not structured_data.get('pump_info', {}).get('pPumpCode'):
            warnings.append("Missing pump code")
        
        curves = structured_data.get('curves', [])
        if not curves:
            warnings.append("No performance curves found")
            return warnings
        
        for i, curve in enumerate(curves):
            curve_id = curve.get('identifier', f'Curve_{i+1}')
            
            # Check data completeness
            if not curve.get('flow_data'):
                warnings.append(f"{curve_id}: Missing flow data")
            if not curve.get('head_data'):
                warnings.append(f"{curve_id}: Missing head data")
            if not curve.get('efficiency_data'):
                warnings.append(f"{curve_id}: Missing efficiency data")
            
            # Check data consistency
            flow_len = len(curve.get('flow_data', []))
            head_len = len(curve.get('head_data', []))
            eff_len = len(curve.get('efficiency_data', []))
            
            if flow_len != head_len or head_len != eff_len:
                warnings.append(f"{curve_id}: Inconsistent data point counts (F:{flow_len}, H:{head_len}, E:{eff_len})")
            
            # Validate power calculations
            power_data = curve.get('power_data', [])
            if power_data:
                avg_power = sum(power_data) / len(power_data)
                if avg_power > 1000:  # Unusually high power
                    warnings.append(f"{curve_id}: High average power ({avg_power:.1f} kW) - verify units")
                elif avg_power < 0.1:  # Unusually low power
                    warnings.append(f"{curve_id}: Low average power ({avg_power:.1f} kW) - check efficiency values")
        
        return warnings
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return {
            **self.processing_stats,
            'success_rate': (self.processing_stats['pumps_extracted'] / 
                           max(1, self.processing_stats['files_processed'])) * 100,
            'average_curves_per_pump': (self.processing_stats['curves_processed'] / 
                                      max(1, self.processing_stats['pumps_extracted']))
        }

def test_enhanced_processing():
    """Test the enhanced SCG processing capabilities"""
    processor = EnhancedSCGProcessor()
    
    # Test data simulating authentic SCG format
    test_scg_data = {
        'pPumpCode': '10-WLN-32A',
        'pSuppName': 'APE PUMPS',
        'pUnitFlow': 'm^3/hr',
        'pUnitHead': 'm',
        'pHeadCurvesNo': '2',
        'pM_IMP': 'IMP_001 IMP_002 ',
        'pM_FLOW': '50;75;100;125|60;90;120;150',
        'pM_HEAD': '35;32;30;27|40;37;35;32',
        'pM_EFF': '75;82;85;82|78;84;87;84',
        'pBEPFlow': '100',
        'pBEPHead': '30',
        'pBEPEff': '85'
    }
    
    print("Testing Enhanced SCG Processing...")
    result = processor.process_enhanced_scg_data(test_scg_data)
    
    print(f"Pump Code: {result['pump_info'].get('pPumpCode')}")
    print(f"Number of curves: {len(result['curves'])}")
    
    for i, curve in enumerate(result['curves']):
        print(f"\nCurve {i+1} ({curve['identifier']}):")
        print(f"  Flow points: {len(curve['flow_data'])}")
        print(f"  Head points: {len(curve['head_data'])}")
        print(f"  Efficiency points: {len(curve['efficiency_data'])}")
        if curve['power_data']:
            avg_power = sum(curve['power_data']) / len(curve['power_data'])
            print(f"  Average power: {avg_power:.2f} kW")
    
    # Validate processed data
    warnings = processor.validate_processed_data(result)
    if warnings:
        print(f"\nValidation warnings: {len(warnings)}")
        for warning in warnings[:3]:  # Show first 3 warnings
            print(f"  - {warning}")
    else:
        print("\n✓ Data validation passed")
    
    # Show statistics
    stats = processor.get_processing_statistics()
    print(f"\nProcessing Statistics:")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Average curves per pump: {stats['average_curves_per_pump']:.1f}")

if __name__ == "__main__":
    test_enhanced_processing()