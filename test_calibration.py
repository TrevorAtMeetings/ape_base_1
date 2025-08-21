import requests
import json

# Test data that caused the 58% error
test_data = {
    'pump_code': '10/12 BLE',
    'point_count': '1',
    'unit_system': 'metric',
    'flow_0': '828.7',
    'head_0': '27.8',
    'efficiency_0': '75',  # Estimated
    'power_0': '',  # Optional
    'diameter_0': '390',  # REQUIRED - the exact diameter
    'qbep_0': '',  # Optional
    'csrf_token': 'test_token'
}

# Build the URL
base_url = 'http://localhost:5000'
url = f"{base_url}/admin/pump-calibration/10%2F12%20BLE/analyze"

print(f"Testing calibration with:")
print(f"  Flow: {test_data['flow_0']} m³/hr")
print(f"  Head: {test_data['head_0']} m")
print(f"  Diameter: {test_data['diameter_0']} mm")
print(f"  URL: {url}")

# Note: This would normally require a session with CSRF token
# For testing, we'll just print what would be sent
print("\nForm data that would be submitted:")
for key, value in test_data.items():
    if value and key != 'csrf_token':
        print(f"  {key}: {value}")
