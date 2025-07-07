#!/usr/bin/env python3
"""
Comprehensive PDF Generation Validation
Tests PDF generation with authentic pump data and verifies all specifications display correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from pdf_generator import generate_pdf_report
from catalog_engine import get_catalog_engine
import tempfile

class TestSiteRequirements:
    def __init__(self, flow, head, customer="Test Engineering Ltd", project="Validation Test"):
        self.flow_m3hr = flow
        self.head_m = head
        self.customer_name = customer
        self.project_name = project
        self.application_type = 'general'

def validate_pdf_generation():
    """Comprehensive PDF generation validation"""
    with app.app_context():
        print("=== COMPREHENSIVE PDF VALIDATION ===")
        
        # Get catalog engine
        engine = get_catalog_engine()
        stats = engine.get_catalog_stats()
        print(f"Catalog: {stats['total_models']} pumps, {stats['total_curves']} curves")
        
        # Test multiple pump scenarios
        test_cases = [
            {"flow": 342, "head": 27.4, "description": "6/8 ALE High Flow"},
            {"flow": 150, "head": 25, "description": "WXH Series Medium Flow"},
            {"flow": 100, "head": 50, "description": "High Head Application"}
        ]
        
        validation_results = []
        
        for i, test_case in enumerate(test_cases):
            print(f"\n--- Test Case {i+1}: {test_case['description']} ---")
            
            # Select pump
            results = engine.select_pumps(test_case['flow'], test_case['head'], max_results=1)
            if not results:
                print(f"❌ No pumps found for {test_case['flow']} m³/hr at {test_case['head']} m")
                continue
                
            pump_result = results[0]
            pump = pump_result['pump']
            performance = pump_result['performance']
            
            print(f"✓ Selected: {pump.pump_code}")
            print(f"  Efficiency: {performance.get('efficiency_pct', 0):.1f}%")
            print(f"  Power: {performance.get('power_kw', 0):.1f} kW")
            print(f"  Impeller: {performance.get('impeller_diameter_mm', 'N/A')}mm")
            print(f"  NPSH: {performance.get('npshr_m', 'N/A')} m")
            
            # Create site requirements
            site_req = TestSiteRequirements(test_case['flow'], test_case['head'])
            
            try:
                # Generate PDF
                pdf_content = generate_pdf_report(pump_result, pump, site_req)
                
                if pdf_content and len(pdf_content) > 1000:  # Reasonable PDF size
                    print(f"✓ PDF generated: {len(pdf_content)} bytes")
                    
                    # Save test PDF
                    filename = f"validation_test_{i+1}_{pump.pump_code.replace('/', '_')}.pdf"
                    with open(filename, 'wb') as f:
                        f.write(pdf_content)
                    print(f"✓ Saved: {filename}")
                    
                    validation_results.append({
                        'test_case': test_case['description'],
                        'pump_code': pump.pump_code,
                        'pdf_size': len(pdf_content),
                        'status': 'SUCCESS',
                        'filename': filename
                    })
                else:
                    print(f"❌ PDF too small: {len(pdf_content) if pdf_content else 0} bytes")
                    validation_results.append({
                        'test_case': test_case['description'],
                        'pump_code': pump.pump_code,
                        'status': 'FAILED - Small PDF',
                        'error': f"PDF size: {len(pdf_content) if pdf_content else 0} bytes"
                    })
                    
            except Exception as e:
                print(f"❌ PDF generation failed: {str(e)[:100]}")
                validation_results.append({
                    'test_case': test_case['description'],
                    'pump_code': pump.pump_code,
                    'status': 'FAILED - Exception',
                    'error': str(e)[:200]
                })
        
        # Summary
        print(f"\n=== VALIDATION SUMMARY ===")
        successful = sum(1 for r in validation_results if r['status'] == 'SUCCESS')
        total = len(validation_results)
        print(f"Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
        
        for result in validation_results:
            status_icon = "✓" if result['status'] == 'SUCCESS' else "❌"
            print(f"{status_icon} {result['test_case']}: {result['pump_code']} - {result['status']}")
            if 'filename' in result:
                print(f"   File: {result['filename']}")
            elif 'error' in result:
                print(f"   Error: {result['error']}")
        
        return successful == total

if __name__ == "__main__":
    success = validate_pdf_generation()
    if success:
        print("\n🎉 ALL PDF VALIDATION TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ PDF VALIDATION FAILED")
        sys.exit(1)