#!/usr/bin/env python3
"""
APE Pump Data Structure Analysis
Demonstrates how semicolon-delimited data correlates across performance parameters
"""

def analyze_pump_data_structure():
    """Analyze the 10 WLN 32A pump data structure to show parameter correlation."""
    
    # Data from the 10 WLN 32A pump file
    pump_code = "10 WLN 32A"
    impeller_diameters = [685.00, 720.00, 755.00]  # mm
    
    # Raw semicolon-delimited data from the file
    flow_data = "0;410.4;800;929.9;1195;1392;1444;1507|0;426;836.4;950.6;1086;1226;1366;1486;1538;1590|0;451.9;888.3;971.4;1091;1294;1460;1564;1631;1678"
    head_data = "76.7;75.3;71.2;68.5;62.3;56.2;53.4;50.7|85.6;84.2;79.5;77.4;74;70.5;66.4;61.6;58.9;56.2|95.2;93.2;87.7;85.6;83.6;78.1;72.6;67.8;64.4;61.6"
    eff_data = "0;55;74;76;78.2;76;74;72|0;55;74;76;78;78.55;78;76;74;72|0;55;74;76;78;79;78;76;74;72"
    npsh_data = "0;0;0;0;0;0;0;0|0;0;0;0;0;0;0;0;0;0|3;3;3.2;3.3;3.5;4.2;5.1;6;6.8;7.8"
    
    print("="*80)
    print(f"APE PUMP DATA STRUCTURE ANALYSIS: {pump_code}")
    print("="*80)
    
    # Parse curves (separated by |)
    flow_curves = flow_data.split('|')
    head_curves = head_data.split('|')
    eff_curves = eff_data.split('|')
    npsh_curves = npsh_data.split('|')
    
    print(f"Number of performance curves: {len(flow_curves)}")
    print(f"Impeller diameters: {impeller_diameters} mm")
    print()
    
    # Analyze each curve
    for i, (flow_curve, head_curve, eff_curve, npsh_curve) in enumerate(zip(flow_curves, head_curves, eff_curves, npsh_curves)):
        impeller_dia = impeller_diameters[i]
        
        # Parse data points (separated by ;)
        flows = [float(x) for x in flow_curve.split(';')]
        heads = [float(x) for x in head_curve.split(';')]
        effs = [float(x) for x in eff_curve.split(';')]
        npshs = [float(x) for x in npsh_curve.split(';')]
        
        print(f"CURVE {i+1}: Impeller Diameter {impeller_dia} mm")
        print("-" * 60)
        print(f"{'Point':<5} {'Flow':<8} {'Head':<8} {'Eff':<8} {'NPSH':<8}")
        print(f"{'#':<5} {'(m³/hr)':<8} {'(m)':<8} {'(%)':<8} {'(m)':<8}")
        print("-" * 60)
        
        # Show correlated data points
        max_points = max(len(flows), len(heads), len(effs), len(npshs))
        for j in range(max_points):
            flow_val = flows[j] if j < len(flows) else 'N/A'
            head_val = heads[j] if j < len(heads) else 'N/A'
            eff_val = effs[j] if j < len(effs) else 'N/A'
            npsh_val = npshs[j] if j < len(npshs) else 'N/A'
            
            # Format values
            flow_str = f"{flow_val:.1f}" if isinstance(flow_val, float) else str(flow_val)
            head_str = f"{head_val:.1f}" if isinstance(head_val, float) else str(head_val)
            eff_str = f"{eff_val:.1f}" if isinstance(eff_val, float) else str(eff_val)
            npsh_str = f"{npsh_val:.1f}" if isinstance(npsh_val, float) else str(npsh_val)
            
            print(f"{j+1:<5} {flow_str:<8} {head_str:<8} {eff_str:<8} {npsh_str:<8}")
        
        print()
        
        # Analyze NPSH data availability for this curve
        valid_npsh = [x for x in npshs if x > 0]
        if valid_npsh:
            print(f"   ✓ NPSH data available: {len(valid_npsh)} points (range: {min(valid_npsh):.1f} - {max(valid_npsh):.1f} m)")
        else:
            print(f"   ✗ No NPSH data available (all zeros)")
        
        # Find best efficiency point for this curve
        if effs:
            max_eff = max(effs)
            max_eff_idx = effs.index(max_eff)
            bep_flow = flows[max_eff_idx] if max_eff_idx < len(flows) else 'N/A'
            bep_head = heads[max_eff_idx] if max_eff_idx < len(heads) else 'N/A'
            print(f"   BEP: {bep_flow:.1f} m³/hr @ {bep_head:.1f} m, {max_eff:.1f}% efficiency")
        
        print()
    
    print("="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    print("1. Each semicolon (;) separates performance values at the same operating point")
    print("2. Each pipe (|) separates different impeller diameter curves")
    print("3. Position correspondence: Flow[0];Head[0];Eff[0];NPSH[0] = same operating point")
    print("4. This pump HAS NPSH data for the largest impeller (755mm) only")
    print("5. Smaller impellers (685mm, 720mm) show zeros for NPSH values")
    print()
    print("DATA QUALITY FINDINGS:")
    print(f"- Flow data points per curve: {[len(curve.split(';')) for curve in flow_curves]}")
    print(f"- Head data points per curve: {[len(curve.split(';')) for curve in head_curves]}")
    print(f"- Efficiency data points per curve: {[len(curve.split(';')) for curve in eff_curves]}")
    print(f"- NPSH data points per curve: {[len([x for x in curve.split(';') if float(x) > 0]) for curve in npsh_curves]}")

if __name__ == "__main__":
    analyze_pump_data_structure()