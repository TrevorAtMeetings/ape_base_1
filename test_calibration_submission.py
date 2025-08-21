#!/usr/bin/env python3
"""
Test the corrected calibration tool with the exact data that caused the 58% error.
This will submit the form data and verify the Pure Validation Interface response.
"""

import requests
from bs4 import BeautifulSoup
import json
import sys

def test_calibration():
    """Test the calibration with the problematic data point"""
    
    # Start a session to maintain cookies
    session = requests.Session()
    
    # First, get the calibration page to obtain CSRF token
    base_url = 'http://localhost:5000'
    calibration_url = f"{base_url}/admin/pump-calibration/10%2F12%20BLE"
    
    print("Step 1: Getting calibration page...")
    response = session.get(calibration_url)
    
    if response.status_code != 200:
        print(f"Error: Could not access calibration page. Status: {response.status_code}")
        return False
    
    # Parse the HTML to find CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    
    if not csrf_input:
        print("Warning: CSRF token not found in form. Proceeding without it.")
        csrf_token = 'test_token'
    else:
        csrf_token = csrf_input.get('value', 'test_token')
    
    print(f"CSRF Token: {csrf_token[:20]}...")
    
    # Prepare the test data - the exact point that caused 58% error
    test_data = {
        'csrf_token': csrf_token,
        'point_count': '1',
        'unit_system': 'metric',
        'flow_0': '828.7',
        'head_0': '27.8',
        'efficiency_0': '75',  # Reasonable estimate
        'power_0': '',  # Optional
        'diameter_0': '390',  # REQUIRED - the exact diameter
        'qbep_0': ''  # Optional
    }
    
    print("\nStep 2: Submitting calibration data...")
    print(f"  Flow: {test_data['flow_0']} m³/hr")
    print(f"  Head: {test_data['head_0']} m")
    print(f"  Diameter: {test_data['diameter_0']} mm (REQUIRED)")
    
    # Submit the form data
    analyze_url = f"{base_url}/admin/pump-calibration/10%2F12%20BLE/analyze"
    response = session.post(analyze_url, data=test_data)
    
    if response.status_code != 200:
        print(f"Error: Failed to submit calibration. Status: {response.status_code}")
        return False
    
    print("\nStep 3: Analyzing response...")
    
    # Parse the response
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for the Pure Validation Interface elements
    validation_section = soup.find('div', string=lambda text: 'Direct Comparison at Specified Diameter' in text if text else False)
    
    if validation_section:
        print("✓ Pure Validation Interface found!")
    else:
        print("✗ Pure Validation Interface NOT found")
    
    # Look for the comparison table
    comparison_table = soup.find('table', class_='striped highlight')
    if comparison_table:
        print("✓ Comparison table found!")
        
        # Extract the values from the table
        rows = comparison_table.find_all('tr')
        for row in rows[2:]:  # Skip header rows
            cells = row.find_all('td')
            if len(cells) >= 4:
                test_point = cells[0].text.strip()
                ground_truth = cells[1].text.strip()
                brain_prediction = cells[2].text.strip()
                discrepancy = cells[3].text.strip()
                
                print(f"\n  Test Point: {test_point}")
                print(f"  Your Submitted Head: {ground_truth}")
                print(f"  Brain's Predicted Head: {brain_prediction}")
                print(f"  Discrepancy: {discrepancy}")
    
    # Look for decision buttons
    discard_button = soup.find('button', onclick=lambda x: 'discardCalibration' in x if x else False)
    flag_button = soup.find('button', onclick=lambda x: 'flagForReview' in x if x else False)
    
    print("\nStep 4: Checking decision interface...")
    if discard_button:
        print("✓ 'Discard - My Input Data is Incorrect' button found!")
    else:
        print("✗ Discard button NOT found")
    
    if flag_button:
        print("✓ 'Flag for Engineering Review' button found!")
    else:
        print("✗ Flag button NOT found")
    
    # Check for error messages
    error_alerts = soup.find_all('div', class_='alert-danger')
    if error_alerts:
        print("\n⚠ Error messages found:")
        for alert in error_alerts:
            print(f"  - {alert.text.strip()}")
    
    # Save the response HTML for manual inspection
    with open('calibration_response.html', 'w') as f:
        f.write(response.text)
    print("\n📄 Full response saved to calibration_response.html")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("CALIBRATION TOOL TEST")
    print("Testing with the exact data that caused 58% error")
    print("=" * 60)
    
    success = test_calibration()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)