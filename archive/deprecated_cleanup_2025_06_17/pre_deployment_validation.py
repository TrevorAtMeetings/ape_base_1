"""
Pre-Deployment Validation for APE Pumps Selection Application
Comprehensive testing and issue identification before production deployment
"""

import requests
import json
import logging
from typing import Dict, List, Any
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PreDeploymentValidator:
    """Comprehensive pre-deployment validation suite."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.issues = []
        self.passed_tests = []
        
    def log_issue(self, severity: str, component: str, description: str):
        """Log an identified issue."""
        self.issues.append({
            'severity': severity,
            'component': component,
            'description': description,
            'timestamp': time.time()
        })
        logger.error(f"{severity} - {component}: {description}")
        
    def log_pass(self, test_name: str):
        """Log a passed test."""
        self.passed_tests.append(test_name)
        logger.info(f"✓ {test_name}")
    
    def test_core_routes(self) -> Dict[str, Any]:
        """Test essential application routes."""
        routes_to_test = [
            ('/', 'Home page'),
            ('/admin', 'Admin panel'),
            ('/chat', 'AI Expert console'),
            ('/api/pumps', 'Pump data API')
        ]
        
        results = {}
        for route, description in routes_to_test:
            try:
                response = requests.get(f"{self.base_url}{route}", timeout=10)
                if response.status_code == 200:
                    self.log_pass(f"{description} accessible")
                    results[route] = 'PASS'
                else:
                    self.log_issue('CRITICAL', 'Routing', f"{description} returned {response.status_code}")
                    results[route] = 'FAIL'
            except Exception as e:
                self.log_issue('CRITICAL', 'Routing', f"{description} failed: {str(e)}")
                results[route] = 'ERROR'
                
        return results
    
    def test_pump_selection_flow(self) -> Dict[str, Any]:
        """Test the complete pump selection workflow."""
        try:
            # Test pump selection with valid parameters
            test_data = {
                'flow_rate': 342,
                'head': 27.4,
                'application': 'water_supply',
                'fluid_type': 'clean_water'
            }
            
            response = requests.post(
                f"{self.base_url}/select_pump",
                data=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.log_pass("Pump selection workflow")
                return {'pump_selection': 'PASS'}
            else:
                self.log_issue('HIGH', 'Pump Selection', f"Selection failed with status {response.status_code}")
                return {'pump_selection': 'FAIL'}
                
        except Exception as e:
            self.log_issue('HIGH', 'Pump Selection', f"Selection workflow error: {str(e)}")
            return {'pump_selection': 'ERROR'}
    
    def test_chart_generation(self) -> Dict[str, Any]:
        """Test performance chart generation."""
        try:
            # Test chart API with known pump
            response = requests.get(
                f"{self.base_url}/api/chart_data_safe/Ni84IEFMRQ?flow=342&head=27.4",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'curves' in data and len(data['curves']) > 0:
                    self.log_pass("Chart data generation")
                    return {'chart_generation': 'PASS'}
                else:
                    self.log_issue('MEDIUM', 'Charts', "Chart data missing or empty")
                    return {'chart_generation': 'FAIL'}
            else:
                self.log_issue('MEDIUM', 'Charts', f"Chart API returned {response.status_code}")
                return {'chart_generation': 'FAIL'}
                
        except Exception as e:
            self.log_issue('MEDIUM', 'Charts', f"Chart generation error: {str(e)}")
            return {'chart_generation': 'ERROR'}
    
    def test_pdf_generation(self) -> Dict[str, Any]:
        """Test PDF report generation."""
        try:
            # Test PDF generation endpoint
            test_data = {
                'pump_code': '6/8 ALE',
                'flow_rate': 342,
                'head': 27.4
            }
            
            response = requests.post(
                f"{self.base_url}/generate_pdf",
                json=test_data,
                timeout=45
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type:
                    self.log_pass("PDF report generation")
                    return {'pdf_generation': 'PASS'}
                else:
                    self.log_issue('HIGH', 'PDF Generation', "PDF response not properly formatted")
                    return {'pdf_generation': 'FAIL'}
            else:
                self.log_issue('HIGH', 'PDF Generation', f"PDF generation failed with status {response.status_code}")
                return {'pdf_generation': 'FAIL'}
                
        except Exception as e:
            self.log_issue('HIGH', 'PDF Generation', f"PDF generation error: {str(e)}")
            return {'pdf_generation': 'ERROR'}
    
    def test_ai_systems(self) -> Dict[str, Any]:
        """Test AI/LLM integration systems."""
        try:
            # Test AI query endpoint
            test_query = {
                'query': 'What is the efficiency of the 6/8 ALE pump at 342 m³/hr?'
            }
            
            response = requests.post(
                f"{self.base_url}/admin/test-query",
                json=test_query,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('response'):
                    self.log_pass("AI query system")
                    return {'ai_systems': 'PASS'}
                else:
                    self.log_issue('MEDIUM', 'AI Systems', "AI query returned empty or invalid response")
                    return {'ai_systems': 'FAIL'}
            else:
                self.log_issue('MEDIUM', 'AI Systems', f"AI query failed with status {response.status_code}")
                return {'ai_systems': 'FAIL'}
                
        except Exception as e:
            self.log_issue('MEDIUM', 'AI Systems', f"AI system error: {str(e)}")
            return {'ai_systems': 'ERROR'}
    
    def test_navigation_and_ui(self) -> Dict[str, Any]:
        """Test navigation and UI components."""
        try:
            # Test main page for navigation elements
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for essential navigation elements
                nav_elements = ['Selection', 'Admin', 'About']
                missing_elements = []
                
                for element in nav_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    self.log_pass("Navigation structure")
                    return {'navigation': 'PASS'}
                else:
                    self.log_issue('LOW', 'Navigation', f"Missing navigation elements: {missing_elements}")
                    return {'navigation': 'FAIL'}
            else:
                self.log_issue('MEDIUM', 'Navigation', f"Main page inaccessible: {response.status_code}")
                return {'navigation': 'FAIL'}
                
        except Exception as e:
            self.log_issue('MEDIUM', 'Navigation', f"Navigation test error: {str(e)}")
            return {'navigation': 'ERROR'}
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete pre-deployment validation suite."""
        logger.info("Starting pre-deployment validation...")
        
        validation_results = {
            'timestamp': time.time(),
            'tests': {},
            'summary': {}
        }
        
        # Run all validation tests
        test_methods = [
            ('Core Routes', self.test_core_routes),
            ('Pump Selection', self.test_pump_selection_flow),
            ('Chart Generation', self.test_chart_generation),
            ('PDF Generation', self.test_pdf_generation),
            ('AI Systems', self.test_ai_systems),
            ('Navigation & UI', self.test_navigation_and_ui)
        ]
        
        for test_name, test_method in test_methods:
            logger.info(f"Running {test_name} tests...")
            try:
                result = test_method()
                validation_results['tests'][test_name] = result
            except Exception as e:
                self.log_issue('CRITICAL', test_name, f"Test suite failed: {str(e)}")
                validation_results['tests'][test_name] = {'error': str(e)}
        
        # Generate summary
        total_issues = len(self.issues)
        critical_issues = len([i for i in self.issues if i['severity'] == 'CRITICAL'])
        high_issues = len([i for i in self.issues if i['severity'] == 'HIGH'])
        
        validation_results['summary'] = {
            'total_tests': len(self.passed_tests),
            'passed_tests': len(self.passed_tests),
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'high_priority_issues': high_issues,
            'deployment_ready': critical_issues == 0 and high_issues <= 2,
            'issues': self.issues
        }
        
        return validation_results
    
    def generate_report(self) -> str:
        """Generate human-readable validation report."""
        results = self.run_full_validation()
        
        report = """
# APE Pumps Application - Pre-Deployment Validation Report

## Executive Summary
"""
        
        summary = results['summary']
        if summary['deployment_ready']:
            report += "✅ **DEPLOYMENT READY** - Application meets production standards\n\n"
        else:
            report += "❌ **DEPLOYMENT BLOCKED** - Critical issues must be resolved\n\n"
        
        report += f"""
## Test Results
- **Total Tests Run**: {summary['total_tests']}
- **Tests Passed**: {summary['passed_tests']}
- **Critical Issues**: {summary['critical_issues']}
- **High Priority Issues**: {summary['high_priority_issues']}
- **Total Issues**: {summary['total_issues']}

## Detailed Test Results
"""
        
        for test_category, test_results in results['tests'].items():
            report += f"\n### {test_category}\n"
            for test_name, result in test_results.items():
                status_icon = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️"
                report += f"- {status_icon} {test_name}: {result}\n"
        
        if self.issues:
            report += "\n## Issues Found\n"
            for issue in self.issues:
                severity_icon = "🔴" if issue['severity'] == 'CRITICAL' else "🟡" if issue['severity'] == 'HIGH' else "🔵"
                report += f"- {severity_icon} **{issue['severity']}** ({issue['component']}): {issue['description']}\n"
        
        report += f"\n## Recommendation\n"
        if summary['deployment_ready']:
            report += "The application is ready for production deployment. All critical systems are operational."
        else:
            report += "Resolve critical and high-priority issues before deployment. The application has functional components but requires fixes for production readiness."
        
        return report

def main():
    """Run pre-deployment validation."""
    validator = PreDeploymentValidator()
    report = validator.generate_report()
    
    # Save report to file
    with open('pre_deployment_validation_report.md', 'w') as f:
        f.write(report)
    
    print(report)
    
    return validator.run_full_validation()

if __name__ == "__main__":
    main()