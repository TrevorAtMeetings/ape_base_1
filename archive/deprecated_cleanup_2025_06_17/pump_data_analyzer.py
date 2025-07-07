#!/usr/bin/env python3
"""
Pump Data Format Analyzer
Analyzes pump data files to identify any issues and provide feedback
"""

import json
import re
from typing import Dict, List, Any

def analyze_pump_data_file(file_path: str) -> Dict[str, Any]:
    """Analyze a pump data file and identify any issues"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse the JSON-like content
    try:
        # Clean up the content to make it valid JSON
        cleaned_content = content.strip()
        if cleaned_content.endswith(','):
            cleaned_content = cleaned_content[:-1]
        
        # Parse as JSON
        pump_data = json.loads(cleaned_content)
        
        analysis = {
            'file_path': file_path,
            'valid_json': True,
            'pump_code': pump_data.get('objPump.pPumpCode', 'Not found'),
            'test_speed': pump_data.get('objPump.pPumpTestSpeed', 'Not found'),
            'issues': [],
            'recommendations': [],
            'data_quality': 'Good'
        }
        
        # Check for required fields
        required_fields = [
            'objPump.pPumpCode',
            'objPump.pM_FLOW',
            'objPump.pM_HEAD',
            'objPump.pM_EFF'
        ]
        
        for field in required_fields:
            if field not in pump_data:
                analysis['issues'].append(f"Missing required field: {field}")
        
        # Analyze performance data
        flow_data = pump_data.get('objPump.pM_FLOW', '')
        head_data = pump_data.get('objPump.pM_HEAD', '')
        eff_data = pump_data.get('objPump.pM_EFF', '')
        npsh_data = pump_data.get('objPump.pM_NP', '')
        
        # Check for multiple curves (indicated by | separator)
        if '|' in flow_data:
            analysis['curve_type'] = 'Multiple curves'
            flow_curves = flow_data.split('|')
            head_curves = head_data.split('|')
            eff_curves = eff_data.split('|')
            
            analysis['num_curves'] = len(flow_curves)
            
            # Validate each curve
            for i, (flow_curve, head_curve, eff_curve) in enumerate(zip(flow_curves, head_curves, eff_curves)):
                flow_points = len(flow_curve.split(';'))
                head_points = len(head_curve.split(';'))
                eff_points = len(eff_curve.split(';'))
                
                if flow_points != head_points or flow_points != eff_points:
                    analysis['issues'].append(f"Curve {i+1}: Inconsistent data points (Flow: {flow_points}, Head: {head_points}, Eff: {eff_points})")
                
                analysis[f'curve_{i+1}_points'] = flow_points
        else:
            analysis['curve_type'] = 'Single curve'
            flow_points = len(flow_data.split(';')) if flow_data else 0
            head_points = len(head_data.split(';')) if head_data else 0
            eff_points = len(eff_data.split(';')) if eff_data else 0
            
            if flow_points != head_points or flow_points != eff_points:
                analysis['issues'].append(f"Inconsistent data points (Flow: {flow_points}, Head: {head_points}, Eff: {eff_points})")
            
            analysis['data_points'] = flow_points
        
        # Check units
        flow_unit = pump_data.get('objPump.pUnitFlow', '')
        head_unit = pump_data.get('objPump.pUnitHead', '')
        
        if flow_unit == 'US gpm' and head_unit == 'ft':
            analysis['units'] = 'Imperial (US gpm, ft)'
            analysis['recommendations'].append('Convert to metric units (m³/hr, m) for consistency with APE standards')
        elif flow_unit == 'm^3/hr' and head_unit == 'm':
            analysis['units'] = 'Metric (m³/hr, m)'
        else:
            analysis['units'] = f'Mixed or unknown ({flow_unit}, {head_unit})'
            analysis['issues'].append('Unit specification unclear or inconsistent')
        
        # Check for power data
        if 'objPump.pM_POW' not in pump_data or not pump_data.get('objPump.pM_POW'):
            analysis['recommendations'].append('Consider adding power consumption data for complete analysis')
        
        # Overall quality assessment
        if len(analysis['issues']) == 0:
            analysis['data_quality'] = 'Excellent'
        elif len(analysis['issues']) <= 2:
            analysis['data_quality'] = 'Good with minor issues'
        else:
            analysis['data_quality'] = 'Needs attention'
            
    except json.JSONDecodeError as e:
        analysis = {
            'file_path': file_path,
            'valid_json': False,
            'issues': [f"JSON parsing error: {str(e)}"],
            'data_quality': 'Invalid format'
        }
    
    return analysis

def generate_conversion_recommendations(analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate recommendations for converting the data format"""
    
    recommendations = {
        'format_changes_needed': [],
        'data_processing_steps': [],
        'upload_strategy': 'Ready for upload with minor adjustments'
    }
    
    # Check for common issues across all files
    imperial_units = sum(1 for result in analysis_results if 'Imperial' in result.get('units', ''))
    multiple_curves = sum(1 for result in analysis_results if result.get('curve_type') == 'Multiple curves')
    
    if imperial_units > 0:
        recommendations['format_changes_needed'].append(
            f"{imperial_units} pump(s) use imperial units - convert to metric before upload"
        )
    
    if multiple_curves > 0:
        recommendations['format_changes_needed'].append(
            f"{multiple_curves} pump(s) have multiple impeller curves - system will handle automatically"
        )
    
    # Data processing steps
    recommendations['data_processing_steps'] = [
        "1. Convert JSON format to CSV or use single pump entry",
        "2. Ensure consistent metric units (m³/hr, m)",
        "3. Validate data point consistency across curves",
        "4. Add manufacturer field if missing (default: APE PUMPS)"
    ]
    
    return recommendations

def main():
    """Analyze the three pump data files"""
    files = [
        'attached_assets/10_nhtb_1749843024452.txt',
        'attached_assets/10_wln_32a_1749843224124.txt',
        'attached_assets/10_wln_26a_1749843224125.txt'
    ]
    
    analysis_results = []
    
    print("=== APE Pumps Data Analysis Report ===\n")
    
    for file_path in files:
        try:
            analysis = analyze_pump_data_file(file_path)
            analysis_results.append(analysis)
            
            print(f"File: {analysis['pump_code']}")
            print(f"Format: {analysis.get('curve_type', 'Unknown')}")
            print(f"Units: {analysis.get('units', 'Unknown')}")
            print(f"Quality: {analysis['data_quality']}")
            
            if analysis.get('num_curves'):
                print(f"Curves: {analysis['num_curves']}")
                for i in range(analysis['num_curves']):
                    points = analysis.get(f'curve_{i+1}_points', 0)
                    print(f"  Curve {i+1}: {points} data points")
            elif analysis.get('data_points'):
                print(f"Data points: {analysis['data_points']}")
            
            if analysis['issues']:
                print("Issues:")
                for issue in analysis['issues']:
                    print(f"  ⚠️  {issue}")
            
            if analysis['recommendations']:
                print("Recommendations:")
                for rec in analysis['recommendations']:
                    print(f"  💡 {rec}")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    # Generate overall recommendations
    recommendations = generate_conversion_recommendations(analysis_results)
    
    print("\n=== Overall Upload Strategy ===")
    print(f"Status: {recommendations['upload_strategy']}")
    
    if recommendations['format_changes_needed']:
        print("\nRequired Changes:")
        for change in recommendations['format_changes_needed']:
            print(f"  🔧 {change}")
    
    print("\nProcessing Steps:")
    for step in recommendations['data_processing_steps']:
        print(f"  {step}")

if __name__ == "__main__":
    main()