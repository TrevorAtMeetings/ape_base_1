"""
SCG to Catalog Engine Adapter
Converts SCG-processed pump data to format compatible with existing catalog engine
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AdapterResult:
    """Result of SCG to catalog conversion"""
    success: bool
    catalog_data: Optional[Dict[str, Any]] = None
    pump_code: str = ""
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class SCGCatalogAdapter:
    """Adapter to convert SCG data format to catalog engine format"""
    
    def __init__(self):
        self.conversion_stats = {
            'pumps_converted': 0,
            'curves_converted': 0,
            'conversion_errors': 0
        }
    
    def map_scg_to_catalog(self, scg_pump_data: Dict[str, Any]) -> AdapterResult:
        """
        Convert SCG pump data to catalog engine format
        
        Args:
            scg_pump_data: Processed SCG data from SCGProcessor
            
        Returns:
            AdapterResult with catalog-compatible data
        """
        pump_info = scg_pump_data.get('pump_info', {})
        curves = scg_pump_data.get('curves', [])
        
        pump_code = pump_info.get('pPumpCode', '').strip()
        result = AdapterResult(success=False, pump_code=pump_code)
        
        if not pump_code:
            result.errors.append("Missing pump code in SCG data")
            return result
        
        try:
            # Create catalog-compatible pump structure
            catalog_pump = {
                'pump_code': pump_code,
                'manufacturer': pump_info.get('pSuppName', 'APE PUMPS'),
                'pump_type': self._determine_pump_type(pump_info),
                'series': self._extract_pump_series(pump_code),
                'test_speed_rpm': int(pump_info.get('pPumpTestSpeed', 1480)),
                'curves': [],
                'metadata': {
                    'source': 'scg_file',
                    'bep_flow_std': pump_info.get('pBEPFlowStd', 0),
                    'bep_head_std': pump_info.get('pBEPHeadStd', 0),
                    'max_flow': pump_info.get('pMaxQ', 0),
                    'max_head': pump_info.get('pMaxH', 0),
                    'min_impeller_diameter': pump_info.get('pMinImpD', 0),
                    'max_impeller_diameter': pump_info.get('pMaxImpD', 0),
                    'flow_units': pump_info.get('pUnitFlow', 'm^3/hr'),
                    'head_units': pump_info.get('pUnitHead', 'm'),
                    'filters': self._extract_filters(pump_info)
                }
            }
            
            # Convert curves to catalog format
            for curve_data in curves:
                catalog_curve = self._convert_curve_to_catalog_format(curve_data, pump_code)
                if catalog_curve:
                    catalog_pump['curves'].append(catalog_curve)
                    self.conversion_stats['curves_converted'] += 1
            
            if not catalog_pump['curves']:
                result.warnings.append("No valid curves found for pump")
            
            # Validate catalog compatibility
            validation_errors = self._validate_catalog_compatibility(catalog_pump)
            if validation_errors:
                result.errors.extend(validation_errors)
                return result
            
            result.success = True
            result.catalog_data = catalog_pump
            self.conversion_stats['pumps_converted'] += 1
            
            logger.info(f"Successfully converted SCG pump {pump_code} to catalog format")
            
        except Exception as e:
            result.errors.append(f"Conversion failed: {str(e)}")
            self.conversion_stats['conversion_errors'] += 1
            logger.error(f"Error converting SCG pump {pump_code}: {e}", exc_info=True)
        
        return result
    
    def _convert_curve_to_catalog_format(self, curve_data: Dict[str, Any], pump_code: str) -> Optional[Dict[str, Any]]:
        """Convert individual curve to catalog format"""
        try:
            # Extract impeller diameter from identifier
            impeller_diameter = self._extract_impeller_diameter(curve_data.get('identifier', ''))
            
            # Create performance points in catalog format
            performance_points = []
            flow_data = curve_data.get('flow_data', [])
            head_data = curve_data.get('head_data', [])
            efficiency_data = curve_data.get('efficiency_data', [])
            power_data = curve_data.get('power_data', [])
            npsh_data = curve_data.get('npsh_data', [])
            
            point_count = min(len(flow_data), len(head_data), len(efficiency_data))
            
            for i in range(point_count):
                performance_point = {
                    'flow_m3hr': flow_data[i],
                    'head_m': head_data[i],
                    'efficiency_pct': efficiency_data[i],
                    'power_kw': power_data[i] if i < len(power_data) else None,
                    'npshr_m': npsh_data[i] if i < len(npsh_data) and npsh_data[i] > 0 else None
                }
                performance_points.append(performance_point)
            
            # Create catalog curve structure
            catalog_curve = {
                'curve_id': curve_data.get('curve_id', f"{pump_code}_C{curve_data.get('curve_index', 0)}"),
                'curve_index': curve_data.get('curve_index', 0),
                'impeller_diameter_mm': impeller_diameter,
                'test_speed_rpm': 1480,  # Default, should be from pump_info
                'performance_points': performance_points,
                'point_count': len(performance_points),
                'flow_range_m3hr': f"{min(flow_data):.1f}-{max(flow_data):.1f}" if flow_data else "0.0-0.0",
                'head_range_m': f"{min(head_data):.1f}-{max(head_data):.1f}" if head_data else "0.0-0.0",
                'efficiency_range_pct': f"{min(efficiency_data):.1f}-{max(efficiency_data):.1f}" if efficiency_data else "0.0-0.0",
                'has_power_data': bool(power_data and any(p > 0 for p in power_data)),
                'has_npsh_data': bool(npsh_data and any(n > 0 for n in npsh_data)),
                'npsh_range_m': f"{min([n for n in npsh_data if n > 0]):.1f}-{max([n for n in npsh_data if n > 0]):.1f}" if npsh_data and any(n > 0 for n in npsh_data) else None
            }
            
            return catalog_curve
            
        except Exception as e:
            logger.error(f"Error converting curve {curve_data.get('curve_id', 'unknown')}: {e}")
            return None
    
    def _determine_pump_type(self, pump_info: Dict[str, Any]) -> str:
        """Determine pump type from pump info"""
        pump_code = pump_info.get('pPumpCode', '').upper()
        filters = [pump_info.get(f'pFilter{i}', '').upper() for i in range(1, 9)]
        
        # Check filters for pump type indicators
        filter_text = ' '.join(filters)
        
        if 'VERTICAL' in filter_text or 'VTP' in filter_text:
            return 'Vertical Turbine'
        elif 'HORIZONTAL' in filter_text or 'SPLIT CASE' in filter_text:
            return 'Horizontal Split Case'
        elif 'END SUCTION' in filter_text:
            return 'End Suction'
        elif 'INLINE' in filter_text or 'IN-LINE' in filter_text:
            return 'Inline'
        elif 'MULTISTAGE' in filter_text:
            return 'Multistage'
        else:
            return 'Centrifugal'  # Default
    
    def _extract_pump_series(self, pump_code: str) -> str:
        """Extract pump series from pump code"""
        # Common APE pump series patterns
        code = pump_code.strip().upper()
        
        if 'WLN' in code:
            return 'WLN Series'
        elif 'WO' in code:
            return 'WO Series'
        elif 'ALE' in code:
            return 'ALE Series'
        elif 'K' in code and 'VANE' in code:
            return 'K-VANE Series'
        elif code.startswith('BDM'):
            return 'BDM Series'
        else:
            # Extract first part as series
            parts = code.split()
            return f"{parts[0]} Series" if parts else "Standard Series"
    
    def _extract_impeller_diameter(self, identifier: str) -> float:
        """Extract impeller diameter from curve identifier"""
        try:
            # Look for numeric value in identifier (assuming it's diameter in mm)
            import re
            numbers = re.findall(r'\d+\.?\d*', identifier.strip())
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 0.0  # Default if no diameter found
    
    def _extract_filters(self, pump_info: Dict[str, Any]) -> Dict[str, str]:
        """Extract filter information as metadata"""
        filters = {}
        for i in range(1, 9):
            filter_value = pump_info.get(f'pFilter{i}', '').strip()
            if filter_value:
                filters[f'filter_{i}'] = filter_value
        return filters
    
    def _validate_catalog_compatibility(self, catalog_pump: Dict[str, Any]) -> List[str]:
        """Validate that converted data is compatible with catalog engine"""
        errors = []
        
        # Check required fields
        if not catalog_pump.get('pump_code'):
            errors.append("Missing pump_code")
        
        if not catalog_pump.get('manufacturer'):
            errors.append("Missing manufacturer")
        
        curves = catalog_pump.get('curves', [])
        if not curves:
            errors.append("No curves available")
        
        # Validate curves
        for i, curve in enumerate(curves):
            curve_errors = self._validate_catalog_curve(curve, i)
            errors.extend(curve_errors)
        
        return errors
    
    def _validate_catalog_curve(self, curve: Dict[str, Any], curve_index: int) -> List[str]:
        """Validate individual curve for catalog compatibility"""
        errors = []
        prefix = f"Curve {curve_index}: "
        
        if not curve.get('performance_points'):
            errors.append(f"{prefix}No performance points")
            return errors
        
        points = curve['performance_points']
        if len(points) < 3:
            errors.append(f"{prefix}Insufficient data points ({len(points)} < 3)")
        
        # Check for required data in points
        has_flow = any(p.get('flow_m3hr', 0) > 0 for p in points)
        has_head = any(p.get('head_m', 0) > 0 for p in points)
        has_efficiency = any(p.get('efficiency_pct', 0) > 0 for p in points)
        
        if not has_flow:
            errors.append(f"{prefix}No valid flow data")
        if not has_head:
            errors.append(f"{prefix}No valid head data")
        if not has_efficiency:
            errors.append(f"{prefix}No valid efficiency data")
        
        return errors
    
    def batch_convert_scg_data(self, scg_data_list: List[Dict[str, Any]]) -> List[AdapterResult]:
        """Convert multiple SCG pump data objects to catalog format"""
        results = []
        
        for scg_data in scg_data_list:
            result = self.map_scg_to_catalog(scg_data)
            results.append(result)
        
        return results
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        return self.conversion_stats.copy()
    
    def reset_stats(self):
        """Reset conversion statistics"""
        self.conversion_stats = {
            'pumps_converted': 0,
            'curves_converted': 0,
            'conversion_errors': 0
        }

# Integration with existing catalog engine
class CatalogEngineIntegrator:
    """Integrates SCG-converted data with existing catalog engine"""
    
    def __init__(self, catalog_engine_path: str = "data/ape_catalog_database.json"):
        self.catalog_path = catalog_engine_path
        self.integration_stats = {
            'pumps_added': 0,
            'pumps_updated': 0,
            'duplicates_found': 0,
            'integration_errors': 0
        }
    
    def integrate_pump_data(self, catalog_pump_data: Dict[str, Any], update_existing: bool = False) -> Dict[str, Any]:
        """
        Integrate converted pump data into existing catalog
        
        Args:
            catalog_pump_data: Pump data in catalog format
            update_existing: Whether to update existing pumps
            
        Returns:
            Integration result with status and details
        """
        import json
        import os
        
        result = {
            'success': False,
            'action': 'none',
            'pump_code': catalog_pump_data.get('pump_code', ''),
            'message': '',
            'errors': []
        }
        
        try:
            # Load existing catalog
            catalog_data = {}
            if os.path.exists(self.catalog_path):
                with open(self.catalog_path, 'r') as f:
                    catalog_data = json.load(f)
            
            pumps = catalog_data.get('pumps', {})
            pump_code = catalog_pump_data['pump_code']
            
            # Check if pump already exists
            if pump_code in pumps:
                if update_existing:
                    pumps[pump_code] = catalog_pump_data
                    result['action'] = 'updated'
                    result['message'] = f"Updated existing pump {pump_code}"
                    self.integration_stats['pumps_updated'] += 1
                else:
                    result['action'] = 'duplicate'
                    result['message'] = f"Pump {pump_code} already exists (not updated)"
                    self.integration_stats['duplicates_found'] += 1
                    result['success'] = True  # Not an error, just a duplicate
                    return result
            else:
                pumps[pump_code] = catalog_pump_data
                result['action'] = 'added'
                result['message'] = f"Added new pump {pump_code}"
                self.integration_stats['pumps_added'] += 1
            
            # Update catalog metadata
            catalog_data['pumps'] = pumps
            catalog_data['metadata'] = catalog_data.get('metadata', {})
            catalog_data['metadata']['pump_count'] = len(pumps)
            catalog_data['metadata']['last_updated'] = self._get_current_timestamp()
            
            # Save updated catalog
            os.makedirs(os.path.dirname(self.catalog_path), exist_ok=True)
            with open(self.catalog_path, 'w') as f:
                json.dump(catalog_data, f, indent=2)
            
            result['success'] = True
            logger.info(f"Successfully integrated pump {pump_code} into catalog")
            
        except Exception as e:
            result['errors'].append(f"Integration failed: {str(e)}")
            self.integration_stats['integration_errors'] += 1
            logger.error(f"Error integrating pump {pump_code}: {e}", exc_info=True)
        
        return result
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics"""
        return self.integration_stats.copy()

# Usage example
if __name__ == "__main__":
    # Test the adapter with sample data
    adapter = SCGCatalogAdapter()
    
    # Sample SCG data (would come from SCGProcessor)
    sample_scg_data = {
        'pump_info': {
            'pPumpCode': 'TEST-001',
            'pSuppName': 'APE PUMPS',
            'pPumpTestSpeed': 1480,
            'pUnitFlow': 'm^3/hr',
            'pUnitHead': 'm',
            'pFilter1': 'APE PUMPS',
            'pFilter2': 'CENTRIFUGAL'
        },
        'curves': [{
            'curve_id': 'TEST-001_C1',
            'curve_index': 0,
            'identifier': '200.00',
            'flow_data': [50, 75, 100, 125],
            'head_data': [35, 32, 30, 27],
            'efficiency_data': [60, 75, 80, 75],
            'power_data': [15.2, 20.1, 25.0, 30.5],
            'npsh_data': [3.0, 3.2, 3.5, 4.0]
        }]
    }
    
    result = adapter.map_scg_to_catalog(sample_scg_data)
    if result.success:
        print("Conversion successful!")
        print(f"Pump code: {result.catalog_data['pump_code']}")
        print(f"Curves: {len(result.catalog_data['curves'])}")
        print(f"Stats: {adapter.get_conversion_stats()}")
    else:
        print(f"Conversion failed: {result.errors}")