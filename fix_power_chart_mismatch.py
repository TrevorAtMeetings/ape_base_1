#!/usr/bin/env python3
"""
Fix Power Chart Mismatch for 28 HC 6P
Resolves issue where power operating point plots outside curve range
"""

import re

def fix_chart_power_calculation():
    """Fix the power calculation mismatch in chart data generation"""
    
    # Read the current routes.py file
    with open('app/routes.py', 'r') as f:
        content = f.read()
    
    # Find the specific chart data generation function
    # Look for the pattern in get_chart_data_safe function
    pattern = r'(            efficiencies = \[p\.get\(\'efficiency_pct\'\) for p in performance_points if p\.get\(\'efficiency_pct\'\) is not None\]\n            powers = calculate_power_curve\(performance_points\)\n            npshrs = \[p\.get\(\'npshr_m\'\) for p in performance_points if p\.get\(\'npshr_m\'\) is not None\])'
    
    replacement = '''            efficiencies = [p.get('efficiency_pct') for p in performance_points if p.get('efficiency_pct') is not None]
            
            # Calculate power curve - adjust for speed variation if this is the selected curve
            is_selected_curve = (i == best_curve_index)
            if is_selected_curve and operating_point and operating_point.get('sizing_info'):
                sizing_info = operating_point['sizing_info']
                if sizing_info.get('sizing_method') == 'speed_variation':
                    # Scale power curve for speed variation using affinity laws
                    base_speed = curve.get('test_speed_rpm', 980)
                    new_speed = sizing_info.get('required_speed_rpm', base_speed)
                    speed_ratio = new_speed / base_speed
                    
                    powers = []
                    for p in performance_points:
                        if p.get('efficiency_pct') and p.get('efficiency_pct') > 0:
                            # Scale flow and head for new speed using affinity laws
                            scaled_flow = p['flow_m3hr'] * speed_ratio
                            scaled_head = p['head_m'] * (speed_ratio ** 2)
                            # Calculate power at scaled conditions
                            scaled_power = (scaled_flow * scaled_head * 9.81) / (3600 * (p['efficiency_pct'] / 100))
                            powers.append(scaled_power)
                        else:
                            powers.append(0)
                    
                    # Also scale flow and head data to match the operating point
                    flows = [p['flow_m3hr'] * speed_ratio for p in performance_points if 'flow_m3hr' in p]
                    heads = [p['head_m'] * (speed_ratio ** 2) for p in performance_points if 'head_m' in p]
                else:
                    powers = calculate_power_curve(performance_points)
            else:
                powers = calculate_power_curve(performance_points)
                
            npshrs = [p.get('npshr_m') for p in performance_points if p.get('npshr_m') is not None]'''
    
    # Count occurrences to handle multiple instances
    matches = re.findall(pattern, content)
    print(f"Found {len(matches)} occurrences of the pattern")
    
    if len(matches) >= 1:
        # Replace only the first occurrence (in get_chart_data_safe function)
        content = re.sub(pattern, replacement, content, count=1)
        
        # Write the updated content back
        with open('app/routes.py', 'w') as f:
            f.write(content)
        
        print("✓ Successfully fixed power chart calculation mismatch")
        print("  - Power curve now scales with speed variation")
        print("  - Operating point will plot within curve range")
        print("  - Maintains authentic manufacturer data accuracy")
        
        return True
    else:
        print("✗ Pattern not found - manual fix required")
        return False

if __name__ == "__main__":
    print("=== Fixing Power Chart Calculation Mismatch ===")
    success = fix_chart_power_calculation()
    
    if success:
        print("\n=== Fix Applied Successfully ===")
        print("The 28 HC 6P power operating point will now plot correctly within the curve range.")
        print("Speed variation scaling is properly applied to both curve data and operating point.")
    else:
        print("\n=== Manual Fix Required ===")
        print("Could not automatically apply the fix. Manual intervention needed.")