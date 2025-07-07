"""
Unified Pump File Processor
Handles both SCG and TXT files with identical processing logic
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
class UnifiedProcessingResult:
    """Result of unified processing operation"""
    success: bool
    pump_data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    processing_time: float = 0.0
    source_file: str = ""
    file_type: str = ""
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class ContentFormatDetector:
    """Detects the format of pump data content"""
    
    @staticmethod
    def detect_format(content: str) -> str:
        """Detect if content is JSON (TXT) or SCG format"""
        content = content.strip()
        
        if content.startswith('{') and content.endswith('}'):
            try:
                json.loads(content)
                return 'json'
            except json.JSONDecodeError:
                return 'unknown'
        elif 'pPumpCode' in content and 'pSuppName' in content:
            return 'scg'
        else:
            return 'unknown'

class EnhancedDataParser:
    """Enhanced parser for both SCG and TXT formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
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
            return [[] for _ in range(num_curves)]
    
    def parse_array_data(self, data_str: str) -> List[float]:
        """Parse array data from string format (for TXT files)"""
        if not data_str:
            return []
            
        try:
            # Handle string representation of arrays
            if isinstance(data_str, str):
                # Remove brackets and split by comma
                data_str = data_str.strip('[]')
                values = [self.to_float(x.strip()) for x in data_str.split(',') if x.strip()]
                return values
            elif isinstance(data_str, list):
                return [self.to_float(x) for x in data_str if x is not None]
            else:
                return []
        except (ValueError, TypeError):
            return []
    
    def parse_json_format(self, content: str) -> Dict[str, Any]:
        """Parse JSON format content (TXT files)"""
        try:
            raw_data = json.loads(content)
            
            # Extract pump metadata
            pump_info = {
                'pPumpCode': raw_data.get('objPump.pPumpCode') or raw_data.get('pPumpCode', ''),
                'pSuppName': raw_data.get('objPump.pSuppName') or raw_data.get('pSuppName', 'APE PUMPS'),
                'pUnitFlow': raw_data.get('objPump.pUnitFlow') or raw_data.get('pUnitFlow', 'm^3/hr'),
                'pUnitHead': raw_data.get('objPump.pUnitHead') or raw_data.get('pUnitHead', 'm'),
                'pPumpTestSpeed': raw_data.get('objPump.pPumpTestSpeed') or raw_data.get('pPumpTestSpeed', '1450'),
                'pBEPFlow': raw_data.get('objPump.pBEPFlow') or raw_data.get('pBEPFlow', ''),
                'pBEPHead': raw_data.get('objPump.pBEPHead') or raw_data.get('pBEPHead', ''),
                'pBEPEff': raw_data.get('objPump.pBEPEff') or raw_data.get('pBEPEff', ''),
            }
            
            # Extract performance curves data
            curves = []
            
            # Look for flow/head/efficiency arrays in various formats
            flow_keys = ['pTASGRX_Flow', 'objPump.pTASGRX_Flow', 'flow_data']
            head_keys = ['pTASGRX_Head', 'objPump.pTASGRX_Head', 'head_data'] 
            eff_keys = ['pTASGRX_Eff', 'objPump.pTASGRX_Eff', 'efficiency_data']
            power_keys = ['pTASGRX_Power', 'objPump.pTASGRX_Power', 'power_data']
            npsh_keys = ['pTASGRX_NPSH', 'objPump.pTASGRX_NPSH', 'npsh_data']
            
            # Find the actual data arrays
            flow_data = None
            head_data = None
            eff_data = None
            power_data = None
            npsh_data = None
            
            for key in flow_keys:
                if key in raw_data and raw_data[key]:
                    flow_data = self.parse_array_data(raw_data[key])
                    break
                    
            for key in head_keys:
                if key in raw_data and raw_data[key]:
                    head_data = self.parse_array_data(raw_data[key])
                    break
                    
            for key in eff_keys:
                if key in raw_data and raw_data[key]:
                    eff_data = self.parse_array_data(raw_data[key])
                    break
                    
            for key in power_keys:
                if key in raw_data and raw_data[key]:
                    power_data = self.parse_array_data(raw_data[key])
                    break
                    
            for key in npsh_keys:
                if key in raw_data and raw_data[key]:
                    npsh_data = self.parse_array_data(raw_data[key])
                    break
            
            # Create curve if we have minimum required data
            if flow_data and head_data:
                curve = {
                    'identifier': 'Main_Curve',
                    'flow_data': flow_data,
                    'head_data': head_data,
                    'efficiency_data': eff_data or [],
                    'power_data': power_data or [],
                    'npsh_data': npsh_data or []
                }
                curves.append(curve)
            
            return {
                'pump_info': pump_info,
                'curves': curves
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing JSON format: {e}")
            return {'pump_info': {}, 'curves': []}
    
    def parse_scg_format(self, content: str) -> Dict[str, Any]:
        """Parse SCG format content"""
        try:
            # Parse SCG content into key-value pairs
            raw_data = {}
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    raw_data[key.strip()] = value.strip()
            
            # Initialize structured data
            structured_data = {
                "pump_info": {},
                "curves": []
            }
            
            pi = structured_data["pump_info"]
            
            # Populate pump metadata
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
            
            # Determine number of curves
            num_curves = self.to_int(raw_data.get('pHeadCurvesNo', '0'))
            if num_curves == 0:
                self.logger.warning("No curves specified in SCG data")
                return structured_data
            
            # Parse curve identifiers
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
            
            # Parse curve data
            flow_series = self.get_curve_series_data(raw_data.get('pM_FLOW', ''), num_curves, "flow")
            head_series = self.get_curve_series_data(raw_data.get('pM_HEAD', ''), num_curves, "head")
            eff_series = self.get_curve_series_data(raw_data.get('pM_EFF', ''), num_curves, "efficiency")
            npsh_series = self.get_curve_series_data(raw_data.get('pM_NP', ''), num_curves, "NPSH")
            
            # Construct curve objects
            for i in range(num_curves):
                curve = {
                    'identifier': curve_identifiers[i],
                    'flow_data': flow_series[i] if i < len(flow_series) else [],
                    'head_data': head_series[i] if i < len(head_series) else [],
                    'efficiency_data': eff_series[i] if i < len(eff_series) else [],
                    'npsh_data': npsh_series[i] if i < len(npsh_series) else [],
                    'power_data': []  # Will be calculated
                }
                
                structured_data["curves"].append(curve)
            
            return structured_data
            
        except Exception as e:
            self.logger.error(f"Error parsing SCG format: {e}")
            return {'pump_info': {}, 'curves': []}

class UnifiedPowerCalculator:
    """Unified power calculation for both formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_power_curve(self, flow_data: List[float], head_data: List[float], 
                            eff_data: List[float], flow_unit: str = "m^3/hr", 
                            head_unit: str = "m") -> List[float]:
        """Calculate power using hydraulic formula with engineering precision"""
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
            
            # Hydraulic power formula: P = (Q * H * ρ * g) / η
            power_kw = (q_val * con_flow * h_val * con_head * 9.81) / (eff_val / 100.0)
            power_calculated.append(round(power_kw, 2))
        
        # Pad with zeros if original arrays were longer
        max_len = max(len(flow_data), len(head_data), len(eff_data))
        while len(power_calculated) < max_len:
            power_calculated.append(0.0)
        
        return power_calculated

class UnifiedPumpProcessor:
    """Main unified processor for both SCG and TXT files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.format_detector = ContentFormatDetector()
        self.parser = EnhancedDataParser()
        self.power_calculator = UnifiedPowerCalculator()
        
        self.processing_stats = {
            'files_processed': 0,
            'scg_files': 0,
            'txt_files': 0,
            'pumps_extracted': 0,
            'curves_processed': 0,
            'errors_encountered': 0
        }
    
    def read_file_content(self, file_path: str) -> str:
        """Read file content with proper encoding handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def process_file(self, file_path: str) -> UnifiedProcessingResult:
        """Process pump file regardless of format (SCG or TXT)"""
        start_time = datetime.now()
        
        try:
            # Read content
            content = self.read_file_content(file_path)
            
            # Detect format
            file_format = self.format_detector.detect_format(content)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            self.logger.info(f"Processing {file_ext} file as {file_format} format")
            
            # Parse based on detected format
            if file_format == 'json':
                structured_data = self.parser.parse_json_format(content)
                self.processing_stats['txt_files'] += 1
            elif file_format == 'scg':
                structured_data = self.parser.parse_scg_format(content)
                self.processing_stats['scg_files'] += 1
            else:
                return UnifiedProcessingResult(
                    success=False,
                    errors=[f"Unknown file format: {file_format}"],
                    source_file=file_path,
                    file_type=file_ext
                )
            
            # Calculate power for all curves
            for curve in structured_data.get('curves', []):
                if curve['flow_data'] and curve['head_data'] and curve['efficiency_data']:
                    flow_unit = structured_data['pump_info'].get('pUnitFlow', 'm^3/hr')
                    head_unit = structured_data['pump_info'].get('pUnitHead', 'm')
                    
                    curve['power_data'] = self.power_calculator.calculate_power_curve(
                        curve['flow_data'],
                        curve['head_data'],
                        curve['efficiency_data'],
                        flow_unit,
                        head_unit
                    )
            
            # Update statistics
            self.processing_stats['files_processed'] += 1
            self.processing_stats['pumps_extracted'] += 1
            self.processing_stats['curves_processed'] += len(structured_data.get('curves', []))
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return UnifiedProcessingResult(
                success=True,
                pump_data=structured_data,
                processing_time=processing_time,
                source_file=file_path,
                file_type=file_ext
            )
            
        except Exception as e:
            self.processing_stats['errors_encountered'] += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return UnifiedProcessingResult(
                success=False,
                errors=[str(e)],
                processing_time=processing_time,
                source_file=file_path,
                file_type=os.path.splitext(file_path)[1].lower()
            )
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return {
            **self.processing_stats,
            'success_rate': (self.processing_stats['pumps_extracted'] / 
                           max(1, self.processing_stats['files_processed'])) * 100,
            'average_curves_per_pump': (self.processing_stats['curves_processed'] / 
                                      max(1, self.processing_stats['pumps_extracted']))
        }

def test_unified_processing():
    """Test unified processing with both SCG and TXT formats"""
    processor = UnifiedPumpProcessor()
    
    # Test JSON format (TXT file content)
    json_content = {
        "objPump.pPumpCode": "TEST-TXT-001",
        "objPump.pSuppName": "APE PUMPS",
        "objPump.pUnitFlow": "m^3/hr",
        "objPump.pUnitHead": "m",
        "objPump.pTASGRX_Flow": "[100, 150, 200]",
        "objPump.pTASGRX_Head": "[30, 25, 18]",
        "objPump.pTASGRX_Eff": "[80, 85, 82]"
    }
    
    # Test SCG format content
    scg_content = """pPumpCode=TEST-SCG-001
pSuppName=APE PUMPS
pUnitFlow=m^3/hr
pUnitHead=m
pHeadCurvesNo=1
pM_IMP=MAIN001
pM_FLOW=100;150;200
pM_HEAD=30;25;18
pM_EFF=80;85;82"""
    
    print("Testing Unified Processing...")
    
    # Test format detection
    json_format = processor.format_detector.detect_format(json.dumps(json_content))
    scg_format = processor.format_detector.detect_format(scg_content)
    
    print(f"JSON content detected as: {json_format}")
    print(f"SCG content detected as: {scg_format}")
    
    # Test parsing
    json_result = processor.parser.parse_json_format(json.dumps(json_content))
    scg_result = processor.parser.parse_scg_format(scg_content)
    
    print(f"\nJSON parsing result: {len(json_result['curves'])} curves")
    print(f"SCG parsing result: {len(scg_result['curves'])} curves")
    
    # Test power calculations
    for i, result in enumerate([json_result, scg_result]):
        format_name = ["JSON/TXT", "SCG"][i]
        if result['curves']:
            curve = result['curves'][0]
            power_data = processor.power_calculator.calculate_power_curve(
                curve['flow_data'],
                curve['head_data'],
                curve['efficiency_data']
            )
            avg_power = sum(power_data) / len(power_data) if power_data else 0
            print(f"{format_name} average power: {avg_power:.2f} kW")

if __name__ == "__main__":
    test_unified_processing()