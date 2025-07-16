"""
APE Data Processor - Enhanced data structure handling for APE pump format
Handles pipe-separated values and multi-curve structures
"""

import logging
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class APEDataProcessor:
    """
    Enhanced processor for APE pump data with focus on accuracy and format matching
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Flexible key mappings for AI response variations
        self.PUMP_DETAILS_KEYS = {
            'pumpModel': ['pumpModel', 'model', 'pump_model', 'name'],
            'manufacturer': ['manufacturer', 'make', 'supplier'],
            'pumpType': ['pumpType', 'pump_type', 'type'],
            'testSpeed': ['testSpeed', 'test_speed', 'speed', 'rpm'],
            'maxFlow': ['maxFlow', 'max_flow', 'flowMax'],
            'maxHead': ['maxHead', 'max_head', 'headMax'],
            'minImpeller': ['minImpeller', 'min_impeller', 'impellerMin'],
            'maxImpeller': ['maxImpeller', 'max_impeller', 'impellerMax']
        }
        
        self.CURVE_KEYS = {
            'impellerDiameter': ['impellerDiameter', 'impeller_diameter', 'diameter'],
            'flowData': ['flowData', 'flow_data', 'flow', 'flows'],
            'headData': ['headData', 'head_data', 'head', 'heads'],
            'efficiencyData': ['efficiencyData', 'efficiency_data', 'efficiency', 'efficiencies'],
            'powerData': ['powerData', 'power_data', 'power', 'powers'],
            'npshData': ['npshData', 'npshr_data', 'npsh', 'npshr']
        }
    
    def _get_flexible_value(self, data_dict: Dict, key_options: List[str], default=None):
        """Get value using flexible key matching"""
        for key in key_options:
            if key in data_dict and data_dict[key] is not None:
                return data_dict[key]
        return default
        
    def process_extracted_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted data to match APE format structure
        
        Args:
            raw_data: Raw extracted data from AI
            
        Returns:
            Processed data in APE format
        """
        try:
            # Handle fallback data from rate limiting
            if raw_data.get('_extractionMetadata', {}).get('method') == 'fallback_rate_limited':
                self.logger.warning("[APE Processor] Processing fallback data from rate-limited extraction")
                return {
                    'success': True,
                    'extraction_method': 'rate_limited_fallback',
                    'pump_details': self._create_fallback_pump_details(),
                    'curves': [],
                    'specifications': {'variableDiameter': True},
                    'bep_data': {'bepFlowStd': 0, 'bepHeadStd': 0},
                    'data_quality': {'completeness_score': 0.0, 'accuracy_confidence': 0.0}
                }
            # Debug: Log the raw data structure comprehensively
            self.logger.info(f"[APE Processor] Raw data keys: {list(raw_data.keys())}")
            
            # Debug: Log top-level structure
            for key, value in raw_data.items():
                if isinstance(value, dict):
                    self.logger.info(f"[APE Processor] Key '{key}' is dict with keys: {list(value.keys())}")
                    # Log dict values for pump_details specifically
                    if key in ['pump_details', 'pumpDetails', 'pump_info', 'pumpInfo']:
                        for sub_key, sub_value in value.items():
                            self.logger.info(f"[APE Processor] {key}.{sub_key} = {sub_value}")
                elif isinstance(value, list):
                    self.logger.info(f"[APE Processor] Key '{key}' is list with {len(value)} items")
                    if value and isinstance(value[0], dict):
                        self.logger.info(f"[APE Processor] First item in '{key}' has keys: {list(value[0].keys())}")
                        # Log sample data from first curve
                        if key in ['curves', 'performanceCurves', 'curve_data']:
                            first_curve = value[0]
                            for curve_key, curve_value in first_curve.items():
                                if isinstance(curve_value, list):
                                    self.logger.info(f"[APE Processor] {key}[0].{curve_key} = list with {len(curve_value)} items: {curve_value[:3]}...")
                                else:
                                    self.logger.info(f"[APE Processor] {key}[0].{curve_key} = {curve_value}")
                else:
                    self.logger.info(f"[APE Processor] Key '{key}': {type(value).__name__} = {value}")
            
            # Debug: Log curves structure if present
            curves_key = None
            for key in ['curves', 'performanceCurves', 'curve_data', 'pumpCurves']:
                if key in raw_data:
                    curves_key = key
                    break
            
            if curves_key:
                curves = raw_data[curves_key]
                self.logger.info(f"[APE Processor] Found {len(curves)} curves under key '{curves_key}'")
                if curves:
                    for i, curve in enumerate(curves[:2]):  # Log first 2 curves
                        self.logger.info(f"[APE Processor] Curve {i+1} keys: {list(curve.keys())}")
                        # Log data array lengths
                        for curve_key, curve_value in curve.items():
                            if isinstance(curve_value, list):
                                self.logger.info(f"[APE Processor] Curve {i+1} '{curve_key}': {len(curve_value)} items")
            else:
                self.logger.warning("[APE Processor] No curves found under any expected key")
            
            processed_data = {
                'success': True,
                'extraction_method': 'enhanced_ape_processor',
                'pump_details': self._process_pump_details(raw_data),
                'curves': self._process_curves(raw_data),
                'specifications': self._process_specifications(raw_data),
                'bep_data': self._process_bep_data(raw_data),
                'data_quality': self._assess_data_quality(raw_data)
            }
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"[APE Processor] Processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'extraction_method': 'enhanced_ape_processor'
            }
    
    def _process_pump_details(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process pump details to match APE format"""
        # Try multiple possible locations for pump details
        pump_details = (raw_data.get('pump_details') or 
                       raw_data.get('pumpDetails') or 
                       raw_data.get('pump_info') or 
                       raw_data.get('pumpInfo') or 
                       raw_data.get('technicalDetails') or {})
        
        # Also check specifications section
        specifications = (raw_data.get('specifications') or 
                         raw_data.get('specs') or {})
        
        self.logger.info(f"[APE Processor] Pump details keys: {list(pump_details.keys()) if pump_details else 'None'}")
        self.logger.info(f"[APE Processor] Specifications keys: {list(specifications.keys()) if specifications else 'None'}")
        
        # Map to APE format using flexible key matching
        ape_details = {
            'pumpModel': (self._get_flexible_value(pump_details, self.PUMP_DETAILS_KEYS['pumpModel'], '') or 
                         self._get_flexible_value(raw_data, self.PUMP_DETAILS_KEYS['pumpModel'], '')),
            'manufacturer': (self._get_flexible_value(pump_details, self.PUMP_DETAILS_KEYS['manufacturer'], 'APE PUMPS') or 
                           self._get_flexible_value(raw_data, self.PUMP_DETAILS_KEYS['manufacturer'], 'APE PUMPS')),
            'pumpType': (self._get_flexible_value(pump_details, self.PUMP_DETAILS_KEYS['pumpType'], 'CENTRIFUGAL') or 
                        self._get_flexible_value(raw_data, self.PUMP_DETAILS_KEYS['pumpType'], 'CENTRIFUGAL')),
            'testSpeed': (self._get_flexible_value(specifications, self.PUMP_DETAILS_KEYS['testSpeed'], 0) or 
                         self._get_flexible_value(pump_details, self.PUMP_DETAILS_KEYS['testSpeed'], 0)),
            'maxFlow': (self._get_flexible_value(specifications, self.PUMP_DETAILS_KEYS['maxFlow'], 0) or 
                       self._get_flexible_value(pump_details, self.PUMP_DETAILS_KEYS['maxFlow'], 0)),
            'maxHead': (self._get_flexible_value(specifications, self.PUMP_DETAILS_KEYS['maxHead'], 0) or 
                       self._get_flexible_value(pump_details, self.PUMP_DETAILS_KEYS['maxHead'], 0)),
            'minImpeller': (self._get_flexible_value(specifications, self.PUMP_DETAILS_KEYS['minImpeller'], 0) or 
                           self._get_flexible_value(pump_details, self.PUMP_DETAILS_KEYS['minImpeller'], 0)),
            'maxImpeller': (self._get_flexible_value(specifications, self.PUMP_DETAILS_KEYS['maxImpeller'], 0) or 
                           self._get_flexible_value(pump_details, self.PUMP_DETAILS_KEYS['maxImpeller'], 0)),
            'unitFlow': 'm³/hr',
            'unitHead': 'm',
            'unitEfficiency': '%',
            'unitNPSH': 'm'
        }
        
        self.logger.info(f"[APE Processor] Processed pump model: '{ape_details['pumpModel']}'")
        return ape_details
    
    def _process_curves(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process curves to match APE multi-curve format"""
        curves_data = raw_data.get('curves', [])
        self.logger.info(f"[APE Processor] Processing {len(curves_data)} curves")
        
        if not curves_data:
            self.logger.warning("[APE Processor] No curves found in raw data")
            # Try alternative keys
            for alt_key in ['performanceCurves', 'curve_data', 'pumpCurves']:
                if alt_key in raw_data:
                    curves_data = raw_data[alt_key]
                    self.logger.info(f"[APE Processor] Found curves under alternative key '{alt_key}': {len(curves_data)} curves")
                    break
        
        processed_curves = []
        
        for i, curve in enumerate(curves_data):
            self.logger.info(f"[APE Processor] Curve {i+1} keys: {list(curve.keys())}")
            
            # Try multiple possible data extraction methods
            performance_points = curve.get('performancePoints', [])
            
            if performance_points:
                # Extract from performance points structure
                self.logger.info(f"[APE Processor] Curve {i+1}: Found performancePoints with {len(performance_points)} points")
                flow_data = [p.get('flow', 0) for p in performance_points]
                head_data = [p.get('head', 0) for p in performance_points]
                efficiency_data = [p.get('efficiency', 0) for p in performance_points]
                power_data = [p.get('power', 0) for p in performance_points]
                npsh_data = [p.get('npshr', p.get('npsh', 0)) for p in performance_points]
            else:
                # Extract from separate arrays using flexible keys
                flow_data = self._get_flexible_value(curve, self.CURVE_KEYS['flowData'], [])
                head_data = self._get_flexible_value(curve, self.CURVE_KEYS['headData'], [])
                efficiency_data = self._get_flexible_value(curve, self.CURVE_KEYS['efficiencyData'], [])
                power_data = self._get_flexible_value(curve, self.CURVE_KEYS['powerData'], [])
                npsh_data = self._get_flexible_value(curve, self.CURVE_KEYS['npshData'], [])
                
                self.logger.info(f"[APE Processor] Curve {i+1}: Extracted {len(flow_data)} flow, {len(head_data)} head, {len(efficiency_data)} efficiency points")
                
                # If still no data, try even more flexible extraction
                if not any([flow_data, head_data, efficiency_data, power_data, npsh_data]):
                    self.logger.warning(f"[APE Processor] Curve {i+1}: No data found with standard keys, trying flexible extraction")
                    self.logger.warning(f"[APE Processor] Curve {i+1}: Available keys: {list(curve.keys())}")
                    
                    # Try nested data structures
                    for key, value in curve.items():
                        if isinstance(value, dict):
                            # Check if data is nested in a sub-object
                            for sub_key, sub_value in value.items():
                                if isinstance(sub_value, list) and len(sub_value) > 0:
                                    if 'flow' in sub_key.lower() and not flow_data:
                                        flow_data = sub_value
                                        self.logger.info(f"[APE Processor] Curve {i+1}: Found flow data in nested key '{key}.{sub_key}': {len(flow_data)} points")
                                    elif 'head' in sub_key.lower() and not head_data:
                                        head_data = sub_value
                                        self.logger.info(f"[APE Processor] Curve {i+1}: Found head data in nested key '{key}.{sub_key}': {len(head_data)} points")
                                    elif 'efficiency' in sub_key.lower() and not efficiency_data:
                                        efficiency_data = sub_value
                                        self.logger.info(f"[APE Processor] Curve {i+1}: Found efficiency data in nested key '{key}.{sub_key}': {len(efficiency_data)} points")
                        elif isinstance(value, list) and len(value) > 0:
                            if 'flow' in key.lower() and not flow_data:
                                flow_data = value
                                self.logger.info(f"[APE Processor] Curve {i+1}: Found flow data in key '{key}': {len(flow_data)} points")
                            elif 'head' in key.lower() and not head_data:
                                head_data = value
                                self.logger.info(f"[APE Processor] Curve {i+1}: Found head data in key '{key}': {len(head_data)} points")
                            elif 'efficiency' in key.lower() and not efficiency_data:
                                efficiency_data = value
                                self.logger.info(f"[APE Processor] Curve {i+1}: Found efficiency data in key '{key}': {len(efficiency_data)} points")
                            elif 'power' in key.lower() and not power_data:
                                power_data = value
                                self.logger.info(f"[APE Processor] Curve {i+1}: Found power data in key '{key}': {len(power_data)} points")
                            elif 'npsh' in key.lower() and not npsh_data:
                                npsh_data = value
                                self.logger.info(f"[APE Processor] Curve {i+1}: Found NPSH data in key '{key}': {len(npsh_data)} points")
            
            # Get impeller diameter with flexible keys
            impeller_diameter = self._get_flexible_value(curve, self.CURVE_KEYS['impellerDiameter'], 0)
            
            # Ensure data consistency
            data_lengths = [len(flow_data), len(head_data), len(efficiency_data), len(power_data), len(npsh_data)]
            max_length = max(data_lengths) if any(data_lengths) else 0
            
            self.logger.info(f"[APE Processor] Curve {i+1}: Impeller {impeller_diameter}mm, max length {max_length}")
            
            if max_length == 0:
                self.logger.error(f"[APE Processor] Curve {i+1}: No data points found after all extraction attempts!")
                self.logger.error(f"[APE Processor] Curve {i+1}: Available keys: {list(curve.keys())}")
                continue
            
            # Pad arrays to same length
            flow_data = self._pad_array(flow_data, max_length)
            head_data = self._pad_array(head_data, max_length)
            efficiency_data = self._pad_array(efficiency_data, max_length)
            power_data = self._pad_array(power_data, max_length)
            npsh_data = self._pad_array(npsh_data, max_length)
            
            processed_curve = {
                'impellerDiameter': impeller_diameter,
                'speed': self._get_flexible_value(curve, ['speed', 'rpm'], 0),
                'curveName': self._get_flexible_value(curve, ['curveName', 'name'], ''),
                'curveType': self._get_flexible_value(curve, ['curveType', 'type'], 'variable_diameter'),
                'flow_data': flow_data,
                'head_data': head_data,
                'efficiency_data': efficiency_data,
                'power_data': power_data,
                'npsh_data': npsh_data,
                'performance_points': self._create_performance_points(
                    flow_data, head_data, efficiency_data, power_data, npsh_data
                ),
                # APE format strings
                'flow_string': ';'.join(map(str, flow_data)),
                'head_string': ';'.join(map(str, head_data)),
                'efficiency_string': ';'.join(map(str, efficiency_data)),
                'power_string': ';'.join(map(str, power_data)),
                'npsh_string': ';'.join(map(str, npsh_data))
            }
            
            processed_curves.append(processed_curve)
            self.logger.info(f"[APE Processor] Curve {i+1}: Successfully processed with {len(processed_curve['performance_points'])} points")
        
        self.logger.info(f"[APE Processor] Total processed curves: {len(processed_curves)}")
        return processed_curves
    
    def _process_specifications(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process specifications to match APE format"""
        specs = raw_data.get('specifications', {})
        
        return {
            'variableDiameter': specs.get('variableDiameter', True),
            'headCurvesNo': len(raw_data.get('curves', [])),
            'effCurvesNo': len(raw_data.get('curves', [])),
            'npshCurvesNo': 1,
            'polyOrder': 3,
            'bepMarkers': self._process_bep_markers(raw_data)
        }
    
    def _process_bep_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process BEP data to match APE format"""
        # Try multiple possible locations for BEP data
        bep_data = (raw_data.get('mainBEP') or 
                   raw_data.get('bep') or 
                   raw_data.get('bestEfficiencyPoint') or {})
        
        # Also check specifications section
        specifications = raw_data.get('specifications', {})
        
        self.logger.info(f"[APE Processor] BEP data keys: {list(bep_data.keys()) if bep_data else 'None'}")
        
        result = {
            'bepFlowStd': (bep_data.get('bepFlow') or bep_data.get('flow') or 
                          specifications.get('bepFlow') or 0),
            'bepHeadStd': (bep_data.get('bepHead') or bep_data.get('head') or 
                          specifications.get('bepHead') or 0),
            'bepEfficiency': (bep_data.get('bepEfficiency') or bep_data.get('efficiency') or 
                             specifications.get('bepEfficiency') or 0),
            'npshrAtBep': (bep_data.get('npshrAtBep') or bep_data.get('npsh') or 
                          specifications.get('npshrAtBep') or 0),
            'impellerDiameter': (bep_data.get('impellerDiameter') or bep_data.get('diameter') or 
                                specifications.get('impellerDiameter') or 0)
        }
        
        self.logger.info(f"[APE Processor] Processed BEP: Flow={result['bepFlowStd']}, Head={result['bepHeadStd']}")
        return result
    
    def _process_bep_markers(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process BEP markers for each curve"""
        bep_markers = raw_data.get('bepMarkers', [])
        processed_markers = []
        
        for marker in bep_markers:
            processed_marker = {
                'impellerDiameter': marker.get('impellerDiameter', 0),
                'bepFlow': marker.get('bepFlow', 0),
                'bepHead': marker.get('bepHead', 0),
                'bepEfficiency': marker.get('bepEfficiency', 0),
                'confidence': marker.get('confidence', 0.0)
            }
            processed_markers.append(processed_marker)
        
        return processed_markers
    
    def _create_performance_points(self, flow_data: List[float], head_data: List[float], 
                                 efficiency_data: List[float], power_data: List[float], 
                                 npsh_data: List[float]) -> List[Dict[str, Any]]:
        """Create performance points array with improved validation"""
        points = []
        
        # Ensure all inputs are lists
        flow_data = flow_data or []
        head_data = head_data or []
        efficiency_data = efficiency_data or []
        power_data = power_data or []
        npsh_data = npsh_data or []
        
        # Determine the number of points from the longest non-empty list
        data_lengths = [len(data) for data in [flow_data, head_data, efficiency_data, power_data, npsh_data] if data]
        num_points = max(data_lengths) if data_lengths else 0
        
        if num_points == 0:
            self.logger.warning("[APE Processor] No data points found for performance points creation")
            self.logger.warning(f"[APE Processor] Array lengths: flow={len(flow_data)}, head={len(head_data)}, eff={len(efficiency_data)}, power={len(power_data)}, npsh={len(npsh_data)}")
            return points
        
        # Validate that we have at least flow OR head data
        if not flow_data and not head_data:
            self.logger.error("[APE Processor] Critical: No flow or head data found - cannot create meaningful performance points")
            return points
        
        for i in range(num_points):
            # Only create point if we have essential data (flow or head)
            flow_val = flow_data[i] if i < len(flow_data) and flow_data[i] is not None else 0
            head_val = head_data[i] if i < len(head_data) and head_data[i] is not None else 0
            
            # Skip point if both flow and head are zero/missing
            if flow_val == 0 and head_val == 0:
                continue
                
            point = {
                'flow': flow_val,
                'head': head_val,
                'efficiency': efficiency_data[i] if i < len(efficiency_data) and efficiency_data[i] is not None else 0,
                'power': power_data[i] if i < len(power_data) and power_data[i] is not None else 0,
                'npsh': npsh_data[i] if i < len(npsh_data) and npsh_data[i] is not None else 0
            }
            points.append(point)
        
        self.logger.info(f"[APE Processor] Created {len(points)} valid performance points from {num_points} raw data points")
        return points
    
    def _pad_array(self, array: List[float], target_length: int) -> List[float]:
        """Pad array to target length with None for missing data"""
        if len(array) >= target_length:
            return array[:target_length]
        
        padded = array.copy()
        while len(padded) < target_length:
            padded.append(None)  # Use None instead of 0.0 to distinguish missing data
        
        return padded
    
    def _create_fallback_pump_details(self) -> Dict[str, Any]:
        """Create fallback pump details when extraction fails"""
        return {
            'pumpModel': 'EXTRACTION_FAILED',
            'manufacturer': 'UNKNOWN',
            'pumpType': 'CENTRIFUGAL',
            'testSpeed': 0,
            'maxFlow': 0,
            'maxHead': 0,
            'minImpeller': 0,
            'maxImpeller': 0,
            'unitFlow': 'm³/hr',
            'unitHead': 'm',
            'unitEfficiency': '%',
            'unitNPSH': 'm'
        }

    def _assess_data_quality(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of extracted data"""
        curves = raw_data.get('curves', [])
        
        quality_metrics = {
            'curves_count': len(curves),
            'total_data_points': sum(len(curve.get('flowData', [])) for curve in curves),
            'bep_markers_count': len(raw_data.get('bepMarkers', [])),
            'completeness_score': 0.0,
            'accuracy_confidence': 0.0
        }
        
        # Calculate completeness score
        if curves:
            points_per_curve = quality_metrics['total_data_points'] / len(curves)
            quality_metrics['completeness_score'] = min(points_per_curve / 9.0, 1.0)  # Target 9 points per curve
        
        # Calculate accuracy confidence
        bep_confidence = sum(marker.get('confidence', 0) for marker in raw_data.get('bepMarkers', []))
        if raw_data.get('bepMarkers'):
            quality_metrics['accuracy_confidence'] = bep_confidence / len(raw_data.get('bepMarkers', []))
        
        return quality_metrics


def get_ape_data_processor():
    """Get global APE data processor instance"""
    return APEDataProcessor()