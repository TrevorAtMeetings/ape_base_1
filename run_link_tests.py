#!/usr/bin/env python3
"""
Quick Link Test Runner
Run comprehensive link tests and generate report
"""

import subprocess
import sys
import os
from datetime import datetime

def run_tests():
    """Run the link tests"""
    print("🔍 Starting Quick Link Testing...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Run pytest with verbose output
    result = subprocess.run([
        'python', '-m', 'pytest', 
        'tests/test_quick_links.py', 
        '-v',
        '--tb=short',
        '--capture=no'  # Show print statements
    ], capture_output=True, text=True)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    if result.returncode == 0:
        print("✅ All link tests PASSED!")
        print("🎉 No broken links detected!")
    else:
        print("❌ Some link tests FAILED!")
        print("🔧 Check the output above for broken links")
        print("\nFailed tests:")
        print(result.stdout)
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return result.returncode

def run_route_inventory():
    """Run route inventory to see all routes"""
    print("\n🗺️  ROUTE INVENTORY")
    print("=" * 30)
    
    result = subprocess.run([
        'python', '-m', 'pytest', 
        'tests/test_quick_links.py::test_route_inventory',
        '-v',
        '-s'  # Show print statements
    ], capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)

if __name__ == "__main__":
    print("🚀 Quick Link Testing Suite")
    print("=" * 30)
    
    # First show route inventory
    run_route_inventory()
    
    # Then run tests
    exit_code = run_tests()
    
    sys.exit(exit_code) 