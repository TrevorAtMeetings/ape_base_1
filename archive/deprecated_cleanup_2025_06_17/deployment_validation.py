"""
Production Deployment Validation for APE Pumps Selection Application
Comprehensive testing and validation before deployment
"""

import os
import sys
import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentValidator:
    """Validate application readiness for production deployment."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.test_results = []
        
    def validate_core_functionality(self) -> Dict[str, Any]:
        """Test core pump selection functionality."""
        logger.info("Validating core pump selection functionality...")
        
        test_cases = [
            {"flow": 150, "head": 45, "pump_type": "HSC", "expected_result": "HSC150-200"},
            {"flow": 100, "head": 30, "pump_type": "VSC", "expected_result": "VSC100-150"},
            {"flow": 250, "head": 60, "pump_type": "BB1", "expected_result": "BB1-200-300"}
        ]
        
        results = {
            "test_name": "Core Functionality",
            "status": "PASS",
            "details": [],
            "errors": []
        }
        
        for i, test_case in enumerate(test_cases):
            try:
                # Test form submission
                form_data = {
                    'flow_rate': test_case['flow'],
                    'head': test_case['head'],
                    'pump_type': test_case['pump_type'],
                    'application': 'Water Transfer',
                    'fluid_type': 'Clean Water',
                    'temperature': 20,
                    'viscosity': 1.0,
                    'specific_gravity': 1.0,
                    'npsha': 8.0,
                    'elevation': 0,
                    'suction_conditions': 'Flooded Suction',
                    'discharge_conditions': 'Atmospheric',
                    'power_supply': '3-Phase 400V',
                    'installation_type': 'Horizontal',
                    'maintenance_access': 'Good',
                    'budget_range': 'Standard',
                    'delivery_timeline': 'Standard'
                }
                
                response = requests.post(f"{self.base_url}/results", data=form_data, timeout=30)
                
                if response.status_code == 200:
                    results["details"].append(f"Test case {i+1}: Form submission successful")
                else:
                    results["status"] = "FAIL"
                    results["errors"].append(f"Test case {i+1}: HTTP {response.status_code}")
                    
            except Exception as e:
                results["status"] = "FAIL"
                results["errors"].append(f"Test case {i+1}: {str(e)}")
        
        return results
    
    def validate_chart_api(self) -> Dict[str, Any]:
        """Test interactive chart API endpoints."""
        logger.info("Validating chart API functionality...")
        
        results = {
            "test_name": "Chart API",
            "status": "PASS",
            "details": [],
            "errors": []
        }
        
        try:
            # Test chart data endpoint
            response = requests.get(
                f"{self.base_url}/api/chart_data/HSC150-200?flow=150&head=45",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    results["status"] = "PARTIAL"
                    results["errors"].append(f"Chart API returns error: {data['error']}")
                else:
                    results["details"].append("Chart API returns valid data structure")
                    
                    # Validate data structure
                    required_fields = ['pump_code', 'curves', 'metadata']
                    for field in required_fields:
                        if field in data:
                            results["details"].append(f"Required field '{field}' present")
                        else:
                            results["status"] = "FAIL"
                            results["errors"].append(f"Missing required field: {field}")
            else:
                results["status"] = "FAIL"
                results["errors"].append(f"Chart API HTTP {response.status_code}")
                
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Chart API error: {str(e)}")
        
        return results
    
    def validate_pdf_generation(self) -> Dict[str, Any]:
        """Test PDF report generation."""
        logger.info("Validating PDF generation functionality...")
        
        results = {
            "test_name": "PDF Generation",
            "status": "PASS",
            "details": [],
            "errors": []
        }
        
        try:
            # Test PDF generation endpoint
            response = requests.get(
                f"{self.base_url}/pdf_report/HSC150-200",
                timeout=30
            )
            
            if response.status_code == 200:
                if response.headers.get('Content-Type') == 'application/pdf':
                    results["details"].append("PDF generation successful with correct content type")
                    
                    # Check PDF content length
                    content_length = len(response.content)
                    if content_length > 1000:  # Reasonable PDF size
                        results["details"].append(f"PDF size: {content_length} bytes (reasonable)")
                    else:
                        results["status"] = "PARTIAL"
                        results["errors"].append(f"PDF size suspicious: {content_length} bytes")
                else:
                    results["status"] = "FAIL"
                    results["errors"].append("Invalid content type for PDF response")
            else:
                results["status"] = "FAIL"
                results["errors"].append(f"PDF generation HTTP {response.status_code}")
                
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"PDF generation error: {str(e)}")
        
        return results
    
    def validate_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and performance."""
        logger.info("Validating database connectivity...")
        
        results = {
            "test_name": "Database Connectivity",
            "status": "PASS",
            "details": [],
            "errors": []
        }
        
        try:
            from pump_engine import load_all_pump_data
            
            start_time = datetime.now()
            pump_data = load_all_pump_data()
            load_time = (datetime.now() - start_time).total_seconds()
            
            if pump_data and len(pump_data) > 0:
                results["details"].append(f"Database loaded {len(pump_data)} pumps in {load_time:.2f}s")
                
                if load_time < 2.0:  # Performance check
                    results["details"].append("Database performance: Excellent")
                elif load_time < 5.0:
                    results["details"].append("Database performance: Acceptable")
                else:
                    results["status"] = "PARTIAL"
                    results["errors"].append(f"Database performance slow: {load_time:.2f}s")
            else:
                results["status"] = "FAIL"
                results["errors"].append("Database returned no data")
                
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Database connectivity error: {str(e)}")
        
        return results
    
    def validate_responsive_design(self) -> Dict[str, Any]:
        """Test responsive design compatibility."""
        logger.info("Validating responsive design...")
        
        results = {
            "test_name": "Responsive Design",
            "status": "PASS",
            "details": [],
            "errors": []
        }
        
        try:
            # Test main page load
            response = requests.get(self.base_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for responsive design elements
                responsive_indicators = [
                    'viewport',
                    'materialize',
                    'responsive-img',
                    'grid-template-columns',
                    'media query'
                ]
                
                found_indicators = []
                for indicator in responsive_indicators:
                    if indicator.lower() in content.lower():
                        found_indicators.append(indicator)
                
                if len(found_indicators) >= 3:
                    results["details"].append(f"Responsive design elements found: {', '.join(found_indicators)}")
                else:
                    results["status"] = "PARTIAL"
                    results["errors"].append("Limited responsive design elements detected")
                    
                # Check for mobile-friendly form elements
                if 'input-field' in content and 'col s12' in content:
                    results["details"].append("Mobile-friendly form structure detected")
                else:
                    results["status"] = "PARTIAL"
                    results["errors"].append("Form may not be optimized for mobile")
                    
            else:
                results["status"] = "FAIL"
                results["errors"].append(f"Main page HTTP {response.status_code}")
                
        except Exception as e:
            results["status"] = "FAIL"
            results["errors"].append(f"Responsive design validation error: {str(e)}")
        
        return results
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete deployment validation suite."""
        logger.info("Starting comprehensive deployment validation...")
        
        validation_suite = [
            self.validate_core_functionality,
            self.validate_chart_api,
            self.validate_pdf_generation,
            self.validate_database_connectivity,
            self.validate_responsive_design
        ]
        
        self.test_results = []
        overall_status = "PASS"
        
        for validation_test in validation_suite:
            try:
                result = validation_test()
                self.test_results.append(result)
                
                if result["status"] == "FAIL":
                    overall_status = "FAIL"
                elif result["status"] == "PARTIAL" and overall_status == "PASS":
                    overall_status = "PARTIAL"
                    
            except Exception as e:
                error_result = {
                    "test_name": "Unknown Test",
                    "status": "FAIL",
                    "details": [],
                    "errors": [f"Test execution error: {str(e)}"]
                }
                self.test_results.append(error_result)
                overall_status = "FAIL"
        
        summary = {
            "overall_status": overall_status,
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r["status"] == "PASS"]),
            "failed_tests": len([r for r in self.test_results if r["status"] == "FAIL"]),
            "partial_tests": len([r for r in self.test_results if r["status"] == "PARTIAL"]),
            "validation_timestamp": datetime.now().isoformat(),
            "test_results": self.test_results
        }
        
        return summary
    
    def generate_validation_report(self) -> str:
        """Generate human-readable validation report."""
        if not self.test_results:
            return "No validation results available. Run validation first."
        
        summary = self.run_full_validation()
        
        report = []
        report.append("=" * 60)
        report.append("APE PUMPS DEPLOYMENT VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Validation Time: {summary['validation_timestamp']}")
        report.append(f"Overall Status: {summary['overall_status']}")
        report.append(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
        report.append("")
        
        for result in summary['test_results']:
            report.append(f"Test: {result['test_name']}")
            report.append(f"Status: {result['status']}")
            
            if result['details']:
                report.append("Details:")
                for detail in result['details']:
                    report.append(f"  ✓ {detail}")
            
            if result['errors']:
                report.append("Issues:")
                for error in result['errors']:
                    report.append(f"  ✗ {error}")
            
            report.append("-" * 40)
        
        # Deployment recommendations
        report.append("DEPLOYMENT RECOMMENDATIONS:")
        
        if summary['overall_status'] == "PASS":
            report.append("✓ Application is ready for production deployment")
            report.append("✓ All critical systems validated successfully")
        elif summary['overall_status'] == "PARTIAL":
            report.append("⚠ Application has minor issues but can be deployed")
            report.append("⚠ Monitor the identified issues post-deployment")
        else:
            report.append("✗ Application requires fixes before deployment")
            report.append("✗ Address critical issues before proceeding")
        
        return "\n".join(report)

if __name__ == "__main__":
    validator = DeploymentValidator()
    report = validator.generate_validation_report()
    print(report)