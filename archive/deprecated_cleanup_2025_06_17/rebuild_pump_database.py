#!/usr/bin/env python3
"""
Rebuild APE Pump Database with Proper Curve Structure
Restructures database to match authentic APE catalog format with individual curves
"""

import os
import json
import sys
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class PerformancePoint:
    """Single performance data point with all correlated parameters"""
    flow_m3hr: float
    head_m: float
    efficiency_pct: float
    power_kw: float = 0.0
    npshr_m: float = 0.0

@dataclass
class PumpCurve:
    """Individual pump curve with complete performance data"""
    curve_id: str  # Unique identifier
    pump_code: str
    impeller_diameter_mm: float
    test_speed_rpm: int
    manufacturer: str
    pump_type: str
    performance_points: List[PerformancePoint]
    curve_metadata: Dict[str, Any]

@dataclass
class PumpModel:
    """Pump model with multiple curves"""
    pump_code: str
    manufacturer: str
    model_series: str
    pump_type: str
    application: str
    curves: List[PumpCurve]
    specifications: Dict[str, Any]

class APEDatabaseRebuilder:
    """Rebuilds pump database with proper curve structure"""
    
    def __init__(self, source_dir: str = "data/pump_data"):
        self.source_dir = source_dir
        self.pump_models = []
        self.total_curves = 0
        self.total_points = 0
        
    def parse_source_file(self, filepath: str) -> PumpModel:
        """Parse source file and extract pump model with curves"""
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Fix malformed JSON (remove trailing comma before closing brace)
            lines = content.strip().split('\n')
            if lines[-1] == '}' and lines[-2].endswith(','):
                lines[-2] = lines[-2].rstrip(',')
            content_fixed = '\n'.join(lines)
            data = json.loads(content_fixed)
            
            # Extract pump metadata
            pump_code = data.get('objPump.pPumpCode', '')
            manufacturer = data.get('objPump.pSuppName', 'APE PUMPS')
            test_speed = int(data.get('objPump.pPumpTestSpeed', 0))
            
            # Determine pump type from filters
            pump_type = self._determine_pump_type(data)
            application = data.get('objPump.pFilter2', 'WATER SUPPLY')
            
            # Parse performance curves
            curves = self._parse_performance_curves(data, pump_code, manufacturer, pump_type, test_speed)
            
            # Extract specifications
            specifications = {
                'max_flow_m3hr': float(data.get('objPump.pMaxQ', 0)),
                'max_head_m': float(data.get('objPump.pMaxH', 0)),
                'min_impeller_mm': float(data.get('objPump.pMinImpD', 0)),
                'max_impeller_mm': float(data.get('objPump.pMaxImpD', 0)),
                'min_speed_rpm': int(data.get('objPump.pMinSpeed', 0)),
                'max_speed_rpm': int(data.get('objPump.pMaxSpeed', 0)),
                'bep_flow_std': float(data.get('objPump.pBEPFlowStd', 0)),
                'bep_head_std': float(data.get('objPump.pBEPHeadStd', 0)),
                'npsh_eoc': float(data.get('objPump.pNPSHEOC', 0)),
                'unit_flow': data.get('objPump.pUnitFlow', 'm^3/hr'),
                'unit_head': data.get('objPump.pUnitHead', 'm')
            }
            
            return PumpModel(
                pump_code=pump_code,
                manufacturer=manufacturer,
                model_series=self._extract_series(pump_code),
                pump_type=pump_type,
                application=application,
                curves=curves,
                specifications=specifications
            )
            
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return None
    
    def _determine_pump_type(self, data: Dict) -> str:
        """Determine pump type from filter data"""
        filter3 = data.get('objPump.pFilter3', '').upper()
        filter4 = data.get('objPump.pFilter4', '').upper()
        filter7 = data.get('objPump.pFilter7', '').upper()
        
        if 'ALE' in filter4:
            return 'AXIAL_FLOW'
        elif 'HSC' in filter3:
            return 'HIGH_SPEED_CENTRIFUGAL'
        elif any(x in filter4 for x in ['2P', '3P', '4P', '6P', '8P']):
            return 'MULTISTAGE'
        elif 'DOUBLE SUCTION' in filter7:
            return 'DOUBLE_SUCTION'
        else:
            return 'END_SUCTION'
    
    def _extract_series(self, pump_code: str) -> str:
        """Extract pump series from code"""
        # Simple series extraction logic
        parts = pump_code.split()
        if len(parts) > 0:
            return parts[0]
        return 'STANDARD'
    
    def _parse_performance_curves(self, data: Dict, pump_code: str, manufacturer: str, pump_type: str, test_speed: int) -> List[PumpCurve]:
        """Parse all performance curves from semicolon-delimited data"""
        curves = []
        
        # Get raw curve data
        flow_data = data.get('objPump.pM_FLOW', '')
        head_data = data.get('objPump.pM_HEAD', '')
        eff_data = data.get('objPump.pM_EFF', '')
        power_data = data.get('objPump.pM_POWER', '')  # May not exist
        npsh_data = data.get('objPump.pM_NP', '')
        impeller_data = data.get('objPump.pM_IMP', '')
        curve_names = data.get('objPump.pM_NAME', '')
        
        if not all([flow_data, head_data, eff_data]):
            return curves
        
        # Split by curves (|)
        flow_curves = flow_data.split('|')
        head_curves = head_data.split('|')
        eff_curves = eff_data.split('|')
        npsh_curves = npsh_data.split('|') if npsh_data else []
        power_curves = power_data.split('|') if power_data else []
        
        # Parse impeller diameters
        impeller_diameters = []
        if impeller_data:
            try:
                imp_values = [float(x.strip()) for x in impeller_data.split() if x.strip()]
                impeller_diameters = imp_values
            except:
                pass
        
        # Create curves
        for curve_idx, (flow_curve, head_curve, eff_curve) in enumerate(zip(flow_curves, head_curves, eff_curves)):
            try:
                # Parse data points
                flows = [float(x) for x in flow_curve.split(';') if x.strip()]
                heads = [float(x) for x in head_curve.split(';') if x.strip()]
                effs = [float(x) for x in eff_curve.split(';') if x.strip()]
                
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
                        npshs = [float(x) for x in npsh_curves[curve_idx].split(';') if x.strip()]
                    except:
                        pass
                
                # Get impeller diameter
                impeller_dia = impeller_diameters[curve_idx] if curve_idx < len(impeller_diameters) else 0
                
                # Create performance points with proper correlation
                performance_points = []
                max_points = max(len(flows), len(heads), len(effs))
                
                for i in range(max_points):
                    flow_val = flows[i] if i < len(flows) else None
                    head_val = heads[i] if i < len(heads) else None
                    eff_val = effs[i] if i < len(effs) else None
                    power_val = powers[i] if i < len(powers) else None
                    npsh_val = npshs[i] if i < len(npshs) and npshs[i] > 0 else None
                    
                    if flow_val is not None and head_val is not None and eff_val is not None:
                        point = PerformancePoint(
                            flow_m3hr=flow_val,
                            head_m=head_val,
                            efficiency_pct=eff_val,
                            power_kw=power_val if power_val is not None else 0.0,
                            npshr_m=npsh_val if npsh_val is not None else 0.0
                        )
                        performance_points.append(point)
                        self.total_points += 1
                
                if performance_points:
                    curve_id = f"{pump_code}_C{curve_idx+1}_{int(impeller_dia)}mm"
                    
                    curve_metadata = {
                        'curve_index': curve_idx,
                        'test_speed_rpm': test_speed,
                        'points_count': len(performance_points),
                        'flow_range': f"{min(p.flow_m3hr for p in performance_points):.1f}-{max(p.flow_m3hr for p in performance_points):.1f}",
                        'head_range': f"{min(p.head_m for p in performance_points):.1f}-{max(p.head_m for p in performance_points):.1f}",
                        'efficiency_range': f"{min(p.efficiency_pct for p in performance_points):.1f}-{max(p.efficiency_pct for p in performance_points):.1f}",
                        'has_power_data': any(p.power_kw is not None for p in performance_points),
                        'has_npsh_data': any(p.npshr_m is not None for p in performance_points)
                    }
                    
                    curve = PumpCurve(
                        curve_id=curve_id,
                        pump_code=pump_code,
                        impeller_diameter_mm=impeller_dia,
                        test_speed_rpm=test_speed,
                        manufacturer=manufacturer,
                        pump_type=pump_type,
                        performance_points=performance_points,
                        curve_metadata=curve_metadata
                    )
                    
                    curves.append(curve)
                    self.total_curves += 1
                    
            except Exception as e:
                print(f"Error parsing curve {curve_idx} for {pump_code}: {e}")
                continue
        
        return curves
    
    def rebuild_database(self):
        """Rebuild complete pump database with proper structure"""
        print("Rebuilding APE Pump Database with Proper Curve Structure...")
        print("="*60)
        
        # Get all pump files
        pump_files = [f for f in os.listdir(self.source_dir) if f.endswith('.txt')]
        
        print(f"Processing {len(pump_files)} pump files...")
        
        for filename in sorted(pump_files):
            filepath = os.path.join(self.source_dir, filename)
            pump_model = self.parse_source_file(filepath)
            
            if pump_model and pump_model.curves:
                self.pump_models.append(pump_model)
                print(f"✓ {pump_model.pump_code}: {len(pump_model.curves)} curves, {sum(len(c.performance_points) for c in pump_model.curves)} points")
        
        print("\n" + "="*60)
        print("REBUILD SUMMARY")
        print("="*60)
        print(f"Total Pump Models: {len(self.pump_models)}")
        print(f"Total Performance Curves: {self.total_curves}")
        print(f"Total Performance Points: {self.total_points}")
        
        # Analyze NPSH availability
        npsh_curves = sum(1 for model in self.pump_models for curve in model.curves 
                         if curve.curve_metadata['has_npsh_data'])
        npsh_points = sum(1 for model in self.pump_models for curve in model.curves 
                         for point in curve.performance_points if point.npshr_m is not None)
        
        print(f"Curves with NPSH Data: {npsh_curves} ({npsh_curves/self.total_curves*100:.1f}%)")
        print(f"Points with NPSH Data: {npsh_points} ({npsh_points/self.total_points*100:.1f}%)")
        
        return self.pump_models
    
    def save_structured_database(self, output_file: str = "data/pumps_database_structured.json"):
        """Save restructured database to JSON"""
        
        structured_data = {
            'metadata': {
                'total_pump_models': len(self.pump_models),
                'total_curves': self.total_curves,
                'total_performance_points': self.total_points,
                'rebuild_timestamp': str(datetime.now()),
                'data_structure': 'APE_CATALOG_FORMAT'
            },
            'pump_models': [asdict(model) for model in self.pump_models]
        }
        
        with open(output_file, 'w') as f:
            json.dump(structured_data, f, indent=2)
        
        print(f"Structured database saved to {output_file}")

if __name__ == "__main__":
    from datetime import datetime
    
    rebuilder = APEDatabaseRebuilder()
    pump_models = rebuilder.rebuild_database()
    rebuilder.save_structured_database()