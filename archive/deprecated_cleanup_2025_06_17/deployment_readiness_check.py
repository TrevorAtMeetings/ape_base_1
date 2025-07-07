#!/usr/bin/env python3
"""
Comprehensive Deployment Readiness Assessment
Validates all critical systems before production deployment
"""

import os
import sys
import json
import time
import requests
from typing import Dict, List, Any
import sqlite3
import logging

class DeploymentReadinessChecker:
    """Comprehensive deployment readiness validation"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = {}
        self.critical_failures = []
        
    def check_core_functionality(self) -> Dict[str, Any]:
        """Test core pump selection functionality"""
        print("Testing core pump selection...")
        
        try:
            # Test main index page
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code != 200:
                self.critical_failures.append("Index page not accessible")
                return {"status": "FAIL", "error": f"Index returned {response.status_code}"}
            
            # Test pump selection with valid parameters
            selection_data = {
                "flow_rate": 1500,
                "head": 25,
                "application_type": "Water Supply"
            }
            
            response = requests.post(f"{self.base_url}/select_pump", 
                                   data=selection_data, timeout=15)
            
            if response.status_code == 200:
                if "pump_results" in response.text or "comparison" in response.text:
                    return {"status": "PASS", "message": "Core functionality working"}
                else:
                    return {"status": "WARN", "message": "Selection completed but results unclear"}
            else:
                self.critical_failures.append("Pump selection not working")
                return {"status": "FAIL", "error": f"Selection failed with {response.status_code}"}
                
        except Exception as e:
            self.critical_failures.append(f"Core functionality error: {str(e)}")
            return {"status": "FAIL", "error": str(e)}
    
    def check_comparison_page(self) -> Dict[str, Any]:
        """Test comparison page functionality"""
        print("Testing comparison page...")
        
        try:
            # Test comparison endpoint
            comparison_data = {
                "flow_rate": 1781,
                "head": 24,
                "application_type": "General"
            }
            
            response = requests.post(f"{self.base_url}/pump_comparison", 
                                   data=comparison_data, timeout=15)
            
            if response.status_code == 200:
                content = response.text.lower()
                if "comparison" in content and "pump" in content:
                    return {"status": "PASS", "message": "Comparison page working"}
                else:
                    return {"status": "WARN", "message": "Comparison page accessible but content unclear"}
            else:
                return {"status": "FAIL", "error": f"Comparison failed with {response.status_code}"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def check_chart_apis(self) -> Dict[str, Any]:
        """Test chart API endpoints"""
        print("Testing chart APIs...")
        
        try:
            # Test chart data endpoint
            pump_code = "28 HC 6P"
            encoded_pump = "MjggSEMgNlA"  # Base64 encoded
            
            response = requests.get(f"{self.base_url}/api/chart_data_safe/{encoded_pump}?flow=1781&head=24", 
                                  timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "curves" in data and "metadata" in data:
                        return {"status": "PASS", "message": "Chart APIs working"}
                    else:
                        return {"status": "WARN", "message": "Chart API responds but data structure unclear"}
                except:
                    return {"status": "WARN", "message": "Chart API responds but not JSON"}
            else:
                return {"status": "FAIL", "error": f"Chart API failed with {response.status_code}"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def check_pdf_generation(self) -> Dict[str, Any]:
        """Test PDF generation capability"""
        print("Testing PDF generation...")
        
        try:
            # Test PDF generation endpoint
            pdf_data = {
                "pump_code": "28 HC 6P",
                "flow_rate": 1781,
                "head": 24
            }
            
            response = requests.post(f"{self.base_url}/generate_pdf", 
                                   data=pdf_data, timeout=20)
            
            if response.status_code == 200:
                if response.headers.get('content-type') == 'application/pdf':
                    return {"status": "PASS", "message": "PDF generation working"}
                else:
                    return {"status": "WARN", "message": "PDF endpoint responds but not PDF content"}
            else:
                return {"status": "FAIL", "error": f"PDF generation failed with {response.status_code}"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def check_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and catalog availability"""
        print("Testing database and catalog...")
        
        try:
            # Check if catalog database exists
            catalog_path = "data/ape_catalog_database.json"
            if not os.path.exists(catalog_path):
                return {"status": "FAIL", "error": "APE catalog database not found"}
            
            # Try to load catalog
            with open(catalog_path, 'r') as f:
                catalog_data = json.load(f)
            
            if "pump_models" in catalog_data and len(catalog_data["pump_models"]) > 0:
                pump_count = len(catalog_data["pump_models"])
                return {"status": "PASS", "message": f"Catalog loaded with {pump_count} pumps"}
            else:
                return {"status": "FAIL", "error": "Catalog exists but contains no pump data"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def check_static_resources(self) -> Dict[str, Any]:
        """Test static resource accessibility"""
        print("Testing static resources...")
        
        try:
            # Test CSS
            response = requests.get(f"{self.base_url}/static/css/style.css", timeout=5)
            css_ok = response.status_code == 200
            
            # Test key endpoints for response
            response = requests.get(f"{self.base_url}/", timeout=5)
            html_ok = response.status_code == 200
            
            if css_ok and html_ok:
                return {"status": "PASS", "message": "Static resources accessible"}
            elif html_ok:
                return {"status": "WARN", "message": "HTML accessible but CSS may have issues"}
            else:
                return {"status": "FAIL", "error": "Static resource issues detected"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def check_performance(self) -> Dict[str, Any]:
        """Test basic performance metrics"""
        print("Testing performance...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if response_time < 2.0:
                    return {"status": "PASS", "message": f"Good response time: {response_time:.2f}s"}
                elif response_time < 5.0:
                    return {"status": "WARN", "message": f"Acceptable response time: {response_time:.2f}s"}
                else:
                    return {"status": "FAIL", "error": f"Slow response time: {response_time:.2f}s"}
            else:
                return {"status": "FAIL", "error": f"Performance test failed: {response.status_code}"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def run_full_assessment(self) -> Dict[str, Any]:
        """Run complete deployment readiness assessment"""
        print("🔍 Starting Comprehensive Deployment Readiness Assessment\n")
        
        tests = [
            ("Core Functionality", self.check_core_functionality),
            ("Comparison Page", self.check_comparison_page),
            ("Chart APIs", self.check_chart_apis),
            ("PDF Generation", self.check_pdf_generation),
            ("Database & Catalog", self.check_database_connectivity),
            ("Static Resources", self.check_static_resources),
            ("Performance", self.check_performance)
        ]
        
        results = {}
        passed = 0
        warnings = 0
        failures = 0
        
        for test_name, test_func in tests:
            print(f"Running {test_name}...")
            result = test_func()
            results[test_name] = result
            
            status = result["status"]
            if status == "PASS":
                passed += 1
                print(f"✅ {test_name}: PASSED")
            elif status == "WARN":
                warnings += 1
                print(f"⚠️  {test_name}: WARNING - {result.get('message', 'Unknown issue')}")
            else:
                failures += 1
                print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
            print()
        
        # Overall assessment
        total_tests = len(tests)
        print("="*60)
        print("DEPLOYMENT READINESS SUMMARY")
        print("="*60)
        print(f"✅ Passed: {passed}/{total_tests}")
        print(f"⚠️  Warnings: {warnings}/{total_tests}")
        print(f"❌ Failures: {failures}/{total_tests}")
        print()
        
        if failures == 0 and warnings <= 1:
            deployment_status = "READY"
            print("🚀 DEPLOYMENT STATUS: READY FOR PRODUCTION")
        elif failures == 0:
            deployment_status = "READY_WITH_WARNINGS"
            print("⚠️  DEPLOYMENT STATUS: READY WITH MINOR WARNINGS")
        elif failures <= 2:
            deployment_status = "NEEDS_FIXES"
            print("🔧 DEPLOYMENT STATUS: NEEDS FIXES BEFORE DEPLOYMENT")
        else:
            deployment_status = "NOT_READY"
            print("🛑 DEPLOYMENT STATUS: NOT READY - MAJOR ISSUES")
        
        print()
        
        if self.critical_failures:
            print("CRITICAL ISSUES TO ADDRESS:")
            for issue in self.critical_failures:
                print(f"• {issue}")
            print()
        
        return {
            "overall_status": deployment_status,
            "total_tests": total_tests,
            "passed": passed,
            "warnings": warnings,
            "failures": failures,
            "test_results": results,
            "critical_failures": self.critical_failures
        }

def main():
    """Run deployment readiness check"""
    checker = DeploymentReadinessChecker()
    results = checker.run_full_assessment()
    
    # Save results
    with open("deployment_readiness_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("📄 Full report saved to: deployment_readiness_report.json")
    
    # Exit with appropriate code
    if results["overall_status"] in ["READY", "READY_WITH_WARNINGS"]:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()