"""
Quick Link Testing - Comprehensive but fast implementation
Tests all routes, forms, and critical user flows
"""

import pytest
from flask import url_for
from app import app

def assert_valid_response(response, expected_status_codes=[200]):
    """Assert response is valid"""
    assert response.status_code in expected_status_codes, \
        f"Expected status code in {expected_status_codes}, got {response.status_code}"

class TestAllRoutes:
    """Test all registered routes systematically"""
    
    def test_all_registered_routes(self, client):
        """Test all user-facing Flask routes (excludes API routes)"""
        routes = []
        for rule in app.url_map.iter_rules():
            if 'GET' in rule.methods and not rule.rule.startswith('/static'):
                # Exclude API routes and other non-user-facing routes
                if not rule.rule.startswith('/api/') and not rule.rule.startswith('/export-'):
                    routes.append(rule.rule)
        
        print(f"\nTesting {len(routes)} user-facing routes...")
        
        for route in routes:
            try:
                response = client.get(route)
                assert_valid_response(response, [200, 302, 401, 404])
                print(f"✅ {route}: {response.status_code}")
            except Exception as e:
                print(f"❌ {route}: ERROR - {str(e)}")
                raise

class TestMainFlow:
    """Test main user flows"""
    
    def test_index_page(self, client):
        """Test main index page"""
        response = client.get('/')
        assert_valid_response(response, [200, 302])
    
    def test_pump_selection_page(self, client):
        """Test pump selection page"""
        response = client.get('/pump_selection')
        assert_valid_response(response, [200])
    
    def test_pump_selection_form(self, client):
        """Test pump selection form submission"""
        data = {
            'flow_m3hr': '1000',
            'head_m': '50',
            'pump_type': 'General',
            'customer_name': 'Test Customer',
            'project_name': 'Test Project'
        }
        response = client.post('/pump_selection', data=data, follow_redirects=True)
        assert_valid_response(response, [200, 302])
    
    def test_pump_options_page(self, client):
        """Test pump options results page"""
        # First submit form to get results
        data = {'flow_m3hr': '1000', 'head_m': '50'}
        client.post('/pump_selection', data=data)
        
        response = client.get('/pump_options')
        assert_valid_response(response, [200])

class TestComparison:
    """Test comparison functionality"""
    
    def test_comparison_page(self, client):
        """Test comparison page"""
        response = client.get('/compare')
        assert_valid_response(response, [200])
    
    def test_comparison_form(self, client):
        """Test comparison form submission"""
        data = {
            'pump_codes': ['6-8-ALE', '6-K-6-VANE'],
            'flow_m3hr': '1000',
            'head_m': '50'
        }
        response = client.post('/compare', data=data, follow_redirects=True)
        assert_valid_response(response, [200, 302])

class TestReports:
    """Test report functionality"""
    
    def test_pump_report_page(self, client):
        """Test pump report page"""
        response = client.get('/pump_report')
        assert_valid_response(response, [200])
    
    def test_specific_pump_report(self, client):
        """Test specific pump report"""
        response = client.get('/pump_report/6-8-ALE')
        assert_valid_response(response, [200])
    
    def test_pdf_generation(self, client):
        """Test PDF generation"""
        response = client.get('/generate_pdf/6-8-ALE')
        assert_valid_response(response, [200])
    
    def test_professional_report(self, client):
        """Test professional report page"""
        response = client.get('/professional_pump_report/6-8-ALE')
        assert_valid_response(response, [200])

class TestAdmin:
    """Test admin functionality"""
    
    def test_admin_dashboard(self, client):
        """Test admin dashboard"""
        response = client.get('/admin')
        assert_valid_response(response, [200, 401, 302])

class TestAPI:
    """Test API endpoints"""
    
    def test_api_pumps(self, client):
        """Test API pumps endpoint"""
        response = client.get('/api/pumps')
        assert_valid_response(response, [200, 401])
    
    def test_api_pump_by_code(self, client):
        """Test API pump by code endpoint"""
        response = client.get('/api/pumps/6-8-ALE')
        assert_valid_response(response, [200, 404])

class TestForms:
    """Test form validation"""
    
    def test_invalid_pump_selection_form(self, client):
        """Test invalid form submission"""
        data = {'flow_m3hr': '-100', 'head_m': '50'}  # Invalid flow rate
        response = client.post('/pump_selection', data=data)
        assert response.status_code in [400, 200]  # Should handle gracefully
    
    def test_missing_required_fields(self, client):
        """Test missing required fields"""
        data = {'flow_m3hr': '1000'}  # Missing head_m
        response = client.post('/pump_selection', data=data)
        assert response.status_code in [400, 200]  # Should handle gracefully

class TestCriticalFlows:
    """Test critical user flows end-to-end"""
    
    def test_complete_pump_selection_flow(self, client):
        """Test complete pump selection flow"""
        # 1. Go to main page
        response = client.get('/')
        assert_valid_response(response, [200, 302])
        
        # 2. Go to pump selection
        response = client.get('/pump_selection')
        assert_valid_response(response, [200])
        
        # 3. Submit form
        data = {'flow_m3hr': '1000', 'head_m': '50'}
        response = client.post('/pump_selection', data=data, follow_redirects=True)
        assert_valid_response(response, [200, 302])
        
        # 4. View results
        response = client.get('/pump_options')
        assert_valid_response(response, [200])
        
        # 5. Generate report
        response = client.get('/pump_report/6-8-ALE')
        assert_valid_response(response, [200])
    
    def test_complete_comparison_flow(self, client):
        """Test complete comparison flow"""
        # 1. Go to comparison page
        response = client.get('/compare')
        assert_valid_response(response, [200])
        
        # 2. Submit comparison form
        data = {'pump_codes': ['6-8-ALE', '6-K-6-VANE']}
        response = client.post('/compare', data=data, follow_redirects=True)
        assert_valid_response(response, [200, 302])
        
        # 3. View comparison results
        response = client.get('/compare')
        assert_valid_response(response, [200])

def test_route_inventory():
    """Print all registered routes for manual review"""
    print("\n=== ALL REGISTERED ROUTES ===")
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/static'):
            methods = list(rule.methods)
            print(f"{rule.rule} -> {rule.endpoint} [{', '.join(methods)}]")
    print("=== END ROUTES ===\n") 