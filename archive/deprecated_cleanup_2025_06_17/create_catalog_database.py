#!/usr/bin/env python3
"""
Create APE Catalog Database Structure
Builds proper pump models with individual curves matching authentic APE catalog format
"""

import os
import json
import re
from typing import Dict, List, Any
from datetime import datetime

class CatalogDatabaseBuilder:
    """Builds database matching authentic APE catalog structure"""
    
    def __init__(self, source_dir: str = "data/pump_data"):
        self.source_dir = source_dir
        self.catalog = {
            'metadata': {
                'build_date': str(datetime.now()),
                'source': 'APE_CATALOG_DATA',
                'total_models': 0,
                'total_curves': 0,
                'total_points': 0,
                'npsh_curves': 0,
                'power_curves': 0
            },
            'pump_models': []
        }
        
    def extract_pump_data(self, filepath: str) -> Dict[str, Any]:
        """Extract pump data from source file"""
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Extract key fields using regex
        pump_code = self._extract_field(content, 'objPump.pPumpCode')
        manufacturer = self._extract_field(content, 'objPump.pSuppName', 'APE PUMPS')
        test_speed = int(self._extract_field(content, 'objPump.pPumpTestSpeed', '0'))
        
        # Performance data
        flow_data = self._extract_field(content, 'objPump.pM_FLOW', '')
        head_data = self._extract_field(content, 'objPump.pM_HEAD', '')
        eff_data = self._extract_field(content, 'objPump.pM_EFF', '')
        
        # Extract power data from pTASGRX_Power fields
        power_data = self._extract_power_data(content)
        
        npsh_data = self._extract_field(content, 'objPump.pM_NP', '')
        impeller_data = self._extract_field(content, 'objPump.pM_IMP', '')
        
        # Extract authentic pump type from source data
        pump_type_filter3 = self._extract_field(content, 'objPump.pFilter3', '')
        pump_type_filter4 = self._extract_field(content, 'objPump.pFilter4', '')
        
        # Specifications
        max_flow = float(self._extract_field(content, 'objPump.pMaxQ', '0'))
        max_head = float(self._extract_field(content, 'objPump.pMaxH', '0'))
        min_impeller = float(self._extract_field(content, 'objPump.pMinImpD', '0'))
        max_impeller = float(self._extract_field(content, 'objPump.pMaxImpD', '0'))
        min_speed = int(self._extract_field(content, 'objPump.pMinSpeed', '700'))
        max_speed = int(self._extract_field(content, 'objPump.pMaxSpeed', '1150'))
        
        return {
            'pump_code': pump_code,
            'manufacturer': manufacturer,
            'test_speed_rpm': test_speed,
            'flow_data': flow_data,
            'head_data': head_data,
            'efficiency_data': eff_data,
            'power_data': power_data,
            'npsh_data': npsh_data,
            'impeller_data': impeller_data,
            'pump_type_filter3': pump_type_filter3,
            'pump_type_filter4': pump_type_filter4,
            'specifications': {
                'max_flow_m3hr': max_flow,
                'max_head_m': max_head,
                'min_impeller_mm': min_impeller,
                'max_impeller_mm': max_impeller,
                'test_speed_rpm': test_speed,
                'min_speed_rpm': min_speed,
                'max_speed_rpm': max_speed
            }
        }
    
    def _extract_field(self, content: str, field: str, default: str = '') -> str:
        """Extract field value from JSON content using regex"""
        pattern = f'"{field}":"([^"]*)"'
        match = re.search(pattern, content)
        return match.group(1) if match else default
    
    def _extract_power_data(self, content: str) -> str:
        """Extract power data from pTASGRX_Power fields"""
        power_values = []
        
        # Extract power values for up to 4 curves (Power0, Power1, Power2, Power3)
        for i in range(4):
            power_field = f'objPump.pTASGRX_Power{i}'
            power_value = self._extract_field(content, power_field, '0')
            if power_value and power_value != '0':
                power_values.append(power_value)
        
        # Convert to the format expected by parse_performance_curves
        # If we have power data, format it as semicolon-separated values for each curve
        if power_values:
            # For now, assume all power values go to the first curve
            # More sophisticated parsing would correlate with flow/head curves
            return ';'.join(power_values)
        else:
            return ''
    
    def parse_performance_curves(self, pump_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse performance curves with correlated data points"""
        
        curves = []
        pump_code = pump_data['pump_code']
        
        # Split data by curves (|)
        flow_curves = pump_data['flow_data'].split('|') if pump_data['flow_data'] else []
        head_curves = pump_data['head_data'].split('|') if pump_data['head_data'] else []
        eff_curves = pump_data['efficiency_data'].split('|') if pump_data['efficiency_data'] else []
        power_curves = pump_data['power_data'].split('|') if pump_data['power_data'] else []
        npsh_curves = pump_data['npsh_data'].split('|') if pump_data['npsh_data'] else []
        
        # Parse impeller diameters
        impeller_diameters = []
        if pump_data['impeller_data']:
            try:
                impeller_diameters = [float(x.strip()) for x in pump_data['impeller_data'].split() if x.strip()]
            except:
                pass
        
        # Process each curve
        max_curves = max(len(flow_curves), len(head_curves), len(eff_curves))
        
        for curve_idx in range(max_curves):
            if curve_idx >= len(flow_curves) or curve_idx >= len(head_curves) or curve_idx >= len(eff_curves):
                continue
                
            try:
                # Parse data points for this curve
                flows = [float(x) for x in flow_curves[curve_idx].split(';') if x.strip()]
                heads = [float(x) for x in head_curves[curve_idx].split(';') if x.strip()]
                effs = [float(x) for x in eff_curves[curve_idx].split(';') if x.strip()]
                
                # Parse optional data
                powers = []
                if curve_idx < len(power_curves) and power_curves[curve_idx]:
                    try:
                        powers = [float(x) for x in power_curves[curve_idx].split(';') if x.strip()]
                    except:
                        pass
                
                npshs = []
                if curve_idx < len(npsh_curves) and npsh_curves[curve_idx]:
                    try:
                        npshs = [float(x) for x in npsh_curves[curve_idx].split(';') if x.strip() and float(x) > 0]
                    except:
                        pass
                
                # Get impeller diameter
                impeller_dia = impeller_diameters[curve_idx] if curve_idx < len(impeller_diameters) else 0
                
                # Create correlated performance points
                performance_points = []
                max_points = max(len(flows), len(heads), len(effs))
                
                for i in range(max_points):
                    if i < len(flows) and i < len(heads) and i < len(effs):
                        point = {
                            'flow_m3hr': flows[i],
                            'head_m': heads[i],
                            'efficiency_pct': effs[i],
                            'power_kw': powers[i] if i < len(powers) else None,
                            'npshr_m': npshs[i] if i < len(npshs) else None
                        }
                        performance_points.append(point)
                        self.catalog['metadata']['total_points'] += 1
                
                if performance_points:
                    # Create curve metadata
                    has_power = any(p['power_kw'] is not None for p in performance_points)
                    has_npsh = any(p['npshr_m'] is not None for p in performance_points)
                    
                    curve = {
                        'curve_id': f"{pump_code}_C{curve_idx+1}_{int(impeller_dia)}mm",
                        'curve_index': curve_idx,
                        'impeller_diameter_mm': impeller_dia,
                        'test_speed_rpm': pump_data['test_speed_rpm'],
                        'performance_points': performance_points,
                        'point_count': len(performance_points),
                        'flow_range_m3hr': f"{min(p['flow_m3hr'] for p in performance_points):.1f}-{max(p['flow_m3hr'] for p in performance_points):.1f}",
                        'head_range_m': f"{min(p['head_m'] for p in performance_points):.1f}-{max(p['head_m'] for p in performance_points):.1f}",
                        'efficiency_range_pct': f"{min(p['efficiency_pct'] for p in performance_points):.1f}-{max(p['efficiency_pct'] for p in performance_points):.1f}",
                        'has_power_data': has_power,
                        'has_npsh_data': has_npsh,
                        'npsh_range_m': f"{min(p['npshr_m'] for p in performance_points if p['npshr_m']):.1f}-{max(p['npshr_m'] for p in performance_points if p['npshr_m']):.1f}" if has_npsh else None
                    }
                    
                    curves.append(curve)
                    self.catalog['metadata']['total_curves'] += 1
                    
                    if has_npsh:
                        self.catalog['metadata']['npsh_curves'] += 1
                    if has_power:
                        self.catalog['metadata']['power_curves'] += 1
                        
            except Exception as e:
                print(f"Error parsing curve {curve_idx} for {pump_code}: {e}")
                continue
        
        return curves
    
    def determine_pump_type(self, pump_data: Dict[str, Any]) -> str:
        """Determine pump type using authentic source data"""
        
        # Use authentic pump type from source data filters
        filter3 = pump_data.get('pump_type_filter3', '').upper()
        filter4 = pump_data.get('pump_type_filter4', '').upper()
        
        # Map authentic pump type descriptions to standard categories
        if 'VERTICAL TURBINE' in filter3 or filter4 == 'VTP':
            return 'VTP'
        elif 'AXIAL' in filter3 or 'ALE' in filter4 or 'BLE' in filter4:
            return 'AXIAL_FLOW'
        elif 'MULTISTAGE' in filter3 or 'MULTISTAGE' in filter4:
            return 'MULTISTAGE'
        elif 'HIGH SPEED' in filter3 or 'HSC' in filter4:
            return 'HIGH_SPEED_CENTRIFUGAL'
        elif 'DOUBLE' in filter3 or 'DOUBLE' in filter4:
            return 'DOUBLE_SUCTION'
        elif 'END SUCTION' in filter3 or filter3 == 'CENTRIFUGAL':
            return 'END_SUCTION'
        else:
            # Fallback to code-based classification for legacy compatibility
            pump_code = pump_data.get('pump_code', '').upper()
            if 'ALE' in pump_code or 'BLE' in pump_code:
                return 'AXIAL_FLOW'
            elif 'HSC' in pump_code:
                return 'HIGH_SPEED_CENTRIFUGAL'
            elif any(x in pump_code for x in ['2P', '3P', '4P', '6P', '8P']):
                return 'MULTISTAGE'
            else:
                return 'END_SUCTION'
    
    def build_catalog(self) -> Dict[str, Any]:
        """Build complete catalog database"""
        
        print("Building APE Catalog Database...")
        print("=" * 50)
        
        # Process all pump files
        pump_files = [f for f in os.listdir(self.source_dir) if f.endswith('.txt')]
        
        for filename in sorted(pump_files):
            filepath = os.path.join(self.source_dir, filename)
            
            try:
                # Extract pump data
                pump_data = self.extract_pump_data(filepath)
                
                if not pump_data['pump_code']:
                    continue
                
                # Parse performance curves
                curves = self.parse_performance_curves(pump_data)
                
                if curves:
                    # Create pump model
                    pump_model = {
                        'pump_code': pump_data['pump_code'],
                        'manufacturer': pump_data['manufacturer'],
                        'pump_type': self.determine_pump_type(pump_data),
                        'model_series': pump_data['pump_code'].split()[0] if pump_data['pump_code'] else 'STANDARD',
                        'specifications': pump_data['specifications'],
                        'curves': curves,
                        'curve_count': len(curves),
                        'total_points': sum(c['point_count'] for c in curves),
                        'npsh_curves': sum(1 for c in curves if c['has_npsh_data']),
                        'power_curves': sum(1 for c in curves if c['has_power_data'])
                    }
                    
                    self.catalog['pump_models'].append(pump_model)
                    self.catalog['metadata']['total_models'] += 1
                    
                    print(f"✓ {pump_data['pump_code']}: {len(curves)} curves, {sum(c['point_count'] for c in curves)} points, {sum(1 for c in curves if c['has_npsh_data'])} NPSH curves")
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
        
        # Final summary
        print("\n" + "=" * 50)
        print("CATALOG BUILD SUMMARY")
        print("=" * 50)
        print(f"Total Pump Models: {self.catalog['metadata']['total_models']}")
        print(f"Total Performance Curves: {self.catalog['metadata']['total_curves']}")
        print(f"Total Performance Points: {self.catalog['metadata']['total_points']}")
        print(f"Curves with NPSH Data: {self.catalog['metadata']['npsh_curves']} ({self.catalog['metadata']['npsh_curves']/self.catalog['metadata']['total_curves']*100:.1f}%)")
        print(f"Curves with Power Data: {self.catalog['metadata']['power_curves']} ({self.catalog['metadata']['power_curves']/self.catalog['metadata']['total_curves']*100:.1f}%)")
        
        return self.catalog
    
    def save_catalog(self, output_file: str = "data/ape_catalog_database.json"):
        """Save catalog to JSON file"""
        
        with open(output_file, 'w') as f:
            json.dump(self.catalog, f, indent=2)
        
        print(f"\nCatalog database saved to {output_file}")
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"File size: {file_size:.1f} MB")

if __name__ == "__main__":
    builder = CatalogDatabaseBuilder()
    catalog = builder.build_catalog()
    builder.save_catalog()