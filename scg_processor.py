"""
SCG Pump Data Processor for APE Pumps Selection Application
Processes authentic SCG pump data files into structured format compatible with catalog engine.
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

@dataclass
class ProcessingResult:
    """Result of SCG processing operation"""
    success: bool
    pump_data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    processing_time: float = 0.0
    source_file: str = ""
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class SCGValidationRules:
    """Validation rules for SCG pump data"""
    
    @staticmethod
    def validate_flow_head_relationship(flow_data: List[float], head_data: List[float]) -> List[str]:
        """Validate physical relationship between flow and head"""
        errors = []
        
        if not flow_data or not head_data:
            errors.append("Missing flow or head data")
            return errors
            
        if len(flow_data) != len(head_data):
            errors.append(f"Flow data points ({len(flow_data)}) != head data points ({len(head_data)})")
            
        # Check for generally decreasing head with increasing flow
        for i in range(1, min(len(flow_data), len(head_data))):
            if flow_data[i] < flow_data[i-1]:
                errors.append(f"Non-monotonic flow data at index {i}")
                break
                
        return errors
    
    @staticmethod
    def validate_efficiency_range(efficiency_data: List[float]) -> List[str]:
        """Validate efficiency values are within reasonable ranges"""
        errors = []
        
        for i, eff in enumerate(efficiency_data):
            if eff < 0 or eff > 100:
                errors.append(f"Invalid efficiency {eff}% at index {i} (must be 0-100%)")
            elif eff > 95:
                errors.append(f"Unusually high efficiency {eff}% at index {i}")
                
        return errors
    
    @staticmethod
    def validate_power_calculation(flow: float, head: float, efficiency: float, power: float) -> List[str]:
        """Validate calculated power against hydraulic formula"""
        errors = []
        
        if efficiency <= 0:
            return errors  # Skip validation for zero efficiency
            
        # Calculate expected power using hydraulic formula: P = (Q * H * ρ * g) / (3600 * η)
        # Assuming water: ρ = 1000 kg/m³, g = 9.81 m/s²
        expected_power = (flow * head * 1000 * 9.81) / (3600 * (efficiency / 100))
        
        if abs(power - expected_power) / expected_power > 0.05:  # 5% tolerance
            errors.append(f"Power calculation mismatch: calculated={power:.2f}kW, expected={expected_power:.2f}kW")
            
        return errors

class SCGProcessor:
    """Main SCG file processor with validation and catalog engine compatibility"""
    
    def __init__(self):
        self.validation_rules = SCGValidationRules()
        self.processing_stats = {
            'files_processed': 0,
            'pumps_processed': 0,
            'curves_processed': 0,
            'errors_encountered': 0
        }
    
    def parse_scg_to_raw_dict(self, file_path: str) -> Dict[str, str]:
        """
        Parse SCG file into raw dictionary format
        
        Args:
            file_path: Path to SCG file
            
        Returns:
            Dictionary with string values from SCG file
        """
        raw_data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    if '=' in line:
                        key, value = line.split('=', 1)
                        raw_data[key.strip()] = value.strip()
                    else:
                        logger.warning(f"Skipping malformed line {line_num} in {file_path}: {line}")
                        
        except Exception as e:
            logger.error(f"Error parsing SCG file {file_path}: {e}")
            raise
            
        return raw_data
    
    def process_pump_data_legacy(self, raw_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Process raw SCG data into structured format with validation
        Enhanced version of the provided function with additional safety checks
        
        Args:
            raw_data: Raw dictionary from SCG file
            
        Returns:
            Structured pump data dictionary
        """
        if not raw_data:
            raise ValueError("No raw_data provided to process_pump_data")

        structured_data = {
            "pump_info": {},
            "curves": [],
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "data_source": "scg_file",
                "validation_status": "pending"
            }
        }

        # Helper functions for safe type conversion
        def to_float(value, default=0.0):
            try:
                if isinstance(value, str) and value.strip() == '':
                    return default
                return float(str(value).strip())
            except (ValueError, TypeError):
                return default

        def to_int(value, default=0):
            try:
                return int(float(str(value).strip()))
            except (ValueError, TypeError):
                return default

        def to_bool(value, default=False):
            if isinstance(value, str):
                return value.strip().lower() in ('true', '1', 'yes')
            return bool(value) if value is not None else default

        # Populate pump_info (scalar data)
        pi = structured_data["pump_info"]
        
        # Basic pump identification
        pi['pPumpCode'] = raw_data.get('pPumpCode', '').strip()
        pi['pSuppName'] = raw_data.get('pSuppName', 'APE PUMPS').strip()
        pi['pKWMax'] = to_float(raw_data.get('pKWMax'))
        pi['pBEPFlowStd'] = to_float(raw_data.get('pBEPFlowStd'))
        pi['pBEPHeadStd'] = to_float(raw_data.get('pBEPHeadStd'))
        pi['pNPSHEOC'] = to_float(raw_data.get('pNPSHEOC'))

        # Filter fields (pump categories/specifications)
        for i in range(1, 9):
            pi[f'pFilter{i}'] = raw_data.get(f'pFilter{i}', '').strip()

        # Boolean flags
        pi['pVarN'] = to_bool(raw_data.get('pVarN'))
        pi['pVarD'] = to_bool(raw_data.get('pVarD'))
        pi['pImpImperial'] = to_bool(raw_data.get('pImpImperial'))
        pi['pMotorImperial'] = to_bool(raw_data.get('pMotorImperial'))

        # Units and ranges
        pi['pUnitFlow'] = raw_data.get('pUnitFlow', 'm^3/hr').strip()
        pi['pUnitHead'] = raw_data.get('pUnitHead', 'm').strip()
        pi['pMaxQ'] = to_float(raw_data.get('pMaxQ'))
        pi['pMaxH'] = to_float(raw_data.get('pMaxH'))
        pi['pMinImpD'] = to_float(raw_data.get('pMinImpD'))
        pi['pMaxImpD'] = to_float(raw_data.get('pMaxImpD'))
        pi['pMinSpeed'] = to_float(raw_data.get('pMinSpeed'))
        pi['pMaxSpeed'] = to_float(raw_data.get('pMaxSpeed'))
        pi['pPumpTestSpeed'] = to_float(raw_data.get('pPumpTestSpeed'))
        pi['pPumpImpDiam'] = to_float(raw_data.get('pPumpImpDiam'))
        pi['nPolyOrder'] = to_int(raw_data.get('nPolyOrder'))
        pi['pM_NAME'] = raw_data.get('pM_NAME', '').strip()

        # TASGRX performance data
        for param in ["Flow", "Head", "Eff", "Power", "NPSH"]:
            for i in range(4):
                pi[f'pTASGRX_{param}{i}'] = to_float(raw_data.get(f'pTASGRX_{param}{i}'))

        # Parse space-separated arrays
        def parse_space_separated_floats(key_name):
            val_str = raw_data.get(key_name, '')
            if not val_str.strip():
                return []
            return [to_float(v) for v in val_str.split() if v.strip() and to_float(v, -1.0) >= 0.0]

        pi['diameters_available'] = parse_space_separated_floats('pM_Diam')
        pi['speeds_available'] = parse_space_separated_floats('pM_Speed')
        pi['iso_efficiency_lines'] = parse_space_separated_floats('pM_EffIso')

        # Determine number of curves
        num_curves = to_int(raw_data.get('pHeadCurvesNo', '0'))
        if num_curves == 0:
            logger.warning(f"No curves specified for pump {pi.get('pPumpCode')}")
            return structured_data

        # Parse curve identifiers
        curve_identifiers = []
        imp_str_raw = raw_data.get('pM_IMP', '')
        for i in range(num_curves):
            start_index = i * 8
            end_index = start_index + 8
            if end_index <= len(imp_str_raw):
                identifier = imp_str_raw[start_index:end_index].strip()
                curve_identifiers.append(identifier)
            else:
                curve_identifiers.append(f"Curve_{i+1}")

        # Parse curve data arrays
        def get_curve_series_data(key_name, num_expected_curves):
            data_str_raw = raw_data.get(key_name, '')
            if not data_str_raw:
                return [''] * num_expected_curves
                
            series_str_list = data_str_raw.split('|')
            
            if len(series_str_list) != num_expected_curves:
                logger.warning(f"Curve count mismatch in {key_name}: expected {num_expected_curves}, found {len(series_str_list)}")
                # Pad or truncate to match expected count
                series_str_list.extend([''] * (num_expected_curves - len(series_str_list)))
                series_str_list = series_str_list[:num_expected_curves]
                
            return series_str_list

        all_curves_flow_str = get_curve_series_data('pM_FLOW', num_curves)
        all_curves_head_str = get_curve_series_data('pM_HEAD', num_curves)
        all_curves_eff_str = get_curve_series_data('pM_EFF', num_curves)
        all_curves_npsh_str = get_curve_series_data('pM_NP', num_curves)

        # Unit conversion factors matching current catalog engine
        unit_flow = pi.get('pUnitFlow', 'm^3/hr')
        unit_head = pi.get('pUnitHead', 'm')

        con_flow = 1.0 / 3600.0  # m^3/hr to m^3/s
        if unit_flow == "l/sec":
            con_flow = 1.0 / 1000.0
        elif unit_flow == "US gpm":
            con_flow = 1.0 / 15850.32

        con_head = 1.0  # m
        if unit_head == "bar":
            con_head = 10.19716
        elif unit_head == "kPa":
            con_head = 0.1019716  # Standard conversion
        elif unit_head == "ft":
            con_head = 0.3048

        # Process each curve
        for i in range(num_curves):
            curve_data = {
                "curve_id": f"{pi['pPumpCode']}_{curve_identifiers[i]}".replace(' ', '_'),
                "identifier": curve_identifiers[i],
                "curve_index": i,
                "flow_data": [],
                "head_data": [],
                "efficiency_data": [],
                "npsh_data": [],
                "power_data": [],
                "validation_errors": [],
                "validation_warnings": []
            }

            # Parse data points
            flow_points = [to_float(p.strip()) for p in all_curves_flow_str[i].split(';') if p.strip()]
            head_points = [to_float(p.strip()) for p in all_curves_head_str[i].split(';') if p.strip()]
            eff_points = [to_float(p.strip()) for p in all_curves_eff_str[i].split(';') if p.strip()]
            npsh_points = [to_float(p.strip()) for p in all_curves_npsh_str[i].split(';') if p.strip()]

            # Validate data consistency
            min_len = min(len(flow_points), len(head_points), len(eff_points))
            if min_len == 0:
                logger.warning(f"No valid data points for curve {i} of pump {pi['pPumpCode']}")
                continue

            # Truncate to consistent length
            flow_points = flow_points[:min_len]
            head_points = head_points[:min_len]
            eff_points = eff_points[:min_len]
            npsh_points = npsh_points[:min_len] if len(npsh_points) >= min_len else npsh_points + [0.0] * (min_len - len(npsh_points))

            # Calculate power for each point
            power_points = []
            for j in range(min_len):
                q_val = flow_points[j]
                h_val = head_points[j]
                eff_val = eff_points[j]

                if eff_val > 0:
                    # Match production standard exactly - pump_engine.py formula
                    flow_m3hr = q_val  # Already in m³/hr from SCG file
                    head_m = h_val * con_head  # Convert head to meters if needed
                    efficiency_decimal = eff_val / 100.0  # Convert percentage to decimal
                    sg = 1.0  # Specific gravity for water
                    
                    # Production formula: P = (Flow * Head * SG * 9.81) / (Efficiency_decimal * 3600)
                    power_kw = (flow_m3hr * head_m * sg * 9.81) / (efficiency_decimal * 3600)
                    power_points.append(round(power_kw, 3))  # Match production 3 decimal places
                else:
                    power_points.append(0.0)

            # Store processed data
            curve_data.update({
                "flow_data": flow_points,
                "head_data": head_points,
                "efficiency_data": eff_points,
                "npsh_data": npsh_points,
                "power_data": power_points,
                "point_count": min_len
            })

            # Validate curve data
            curve_data["validation_errors"].extend(
                self.validation_rules.validate_flow_head_relationship(flow_points, head_points)
            )
            curve_data["validation_errors"].extend(
                self.validation_rules.validate_efficiency_range(eff_points)
            )

            # Validate power calculations for sample points
            for j in range(0, min_len, max(1, min_len // 3)):  # Check every ~3rd point
                validation_errors = self.validation_rules.validate_power_calculation(
                    flow_points[j], head_points[j], eff_points[j], power_points[j]
                )
                curve_data["validation_errors"].extend(validation_errors)

            structured_data["curves"].append(curve_data)

        # Set overall validation status
        total_errors = sum(len(curve.get("validation_errors", [])) for curve in structured_data["curves"])
        structured_data["metadata"]["validation_status"] = "valid" if total_errors == 0 else "warnings" if total_errors < 5 else "errors"
        structured_data["metadata"]["total_validation_errors"] = total_errors

        return structured_data

    def process_scg_file(self, file_path: str) -> ProcessingResult:
        """
        Process complete SCG file with error handling and validation
        
        Args:
            file_path: Path to SCG file
            
        Returns:
            ProcessingResult with success status and data
        """
        start_time = datetime.now()
        result = ProcessingResult(success=False, source_file=file_path)
        
        try:
            # Parse SCG file
            raw_data = self.parse_scg_to_raw_dict(file_path)
            if not raw_data:
                result.errors.append("No data found in SCG file")
                return result
            
            # Process pump data
            pump_data = self.process_pump_data(raw_data)
            
            # Update statistics
            self.processing_stats['files_processed'] += 1
            self.processing_stats['pumps_processed'] += 1
            self.processing_stats['curves_processed'] += len(pump_data.get('curves', []))
            
            # Check for validation errors
            total_errors = sum(len(curve.get("validation_errors", [])) for curve in pump_data.get('curves', []))
            if total_errors > 0:
                result.warnings.append(f"Found {total_errors} validation warnings in pump data")
                self.processing_stats['errors_encountered'] += total_errors
            
            result.success = True
            result.pump_data = pump_data
            
            logger.info(f"Successfully processed SCG file: {file_path}")
            
        except Exception as e:
            result.errors.append(f"Processing failed: {str(e)}")
            logger.error(f"Error processing SCG file {file_path}: {e}", exc_info=True)
        
        finally:
            result.processing_time = (datetime.now() - start_time).total_seconds()
        
        return result

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.processing_stats.copy()

    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {
            'files_processed': 0,
            'pumps_processed': 0,
            'curves_processed': 0,
            'errors_encountered': 0
        }

# Usage example and testing
if __name__ == "__main__":
    processor = SCGProcessor()
    
    # Example with test data (would normally come from actual SCG file)
    test_raw_data = {
        "pPumpCode": "TEST-PUMP-001",
        "pSuppName": "APE PUMPS",
        "pKWMax": "50.0",
        "pBEPFlowStd": "100.0",
        "pBEPHeadStd": "30.0",
        "pFilter1": "APE PUMPS",
        "pFilter2": "CENTRIFUGAL",
        "pUnitFlow": "m^3/hr",
        "pUnitHead": "m",
        "pHeadCurvesNo": "1",
        "pM_FLOW": "50;75;100;125;150",
        "pM_HEAD": "35;32;30;27;23",
        "pM_EFF": "60;75;80;75;65",
        "pM_NP": "3.0;3.2;3.5;4.0;5.0",
        "pM_IMP": "200.00  "
    }
    
    try:
        processed_data = processor.process_pump_data(test_raw_data)
        print("Test processing successful!")
        print(f"Pump: {processed_data['pump_info']['pPumpCode']}")
        print(f"Curves: {len(processed_data['curves'])}")
        print(f"Validation status: {processed_data['metadata']['validation_status']}")
        
        if processed_data['curves']:
            first_curve = processed_data['curves'][0]
            print(f"First curve power data: {first_curve['power_data']}")
            
    except Exception as e:
        print(f"Test failed: {e}")