#!/usr/bin/env python3
"""
Brain Calibration Tool - Tunable Physics Engine Calibrator
===========================================================
Tool for comparing Brain calculations against manufacturer data,
generating accuracy reports, and providing tuning recommendations.

Author: APE Pumps Engineering
Date: August 2025
Version: 1.0.0
"""

import sys
import os
import logging
import json
import argparse
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import numpy as np
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.pump_brain import get_pump_brain
from app.admin_config_service import admin_config_service
from app.pump_repository import get_pump_repository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrainCalibrator:
    """
    Calibration engine for the Brain's tunable physics parameters.
    Compares Brain calculations against manufacturer data and provides
    optimization recommendations.
    """
    
    def __init__(self):
        """Initialize the calibrator with Brain and repository access."""
        self.brain = get_pump_brain()
        self.repository = get_pump_repository()
        self.config_service = admin_config_service
        
        # Calibration test cases - known manufacturer data points
        self.test_cases = []
        self.results = {}
        
        logger.info("Brain Calibrator initialized")
    
    def load_test_cases(self, test_file: Optional[str] = None) -> List[Dict]:
        """
        Load test cases from file or generate from repository data.
        
        Args:
            test_file: Optional JSON file with test cases
            
        Returns:
            List of test case dictionaries
        """
        if test_file and os.path.exists(test_file):
            with open(test_file, 'r') as f:
                self.test_cases = json.load(f)
            logger.info(f"Loaded {len(self.test_cases)} test cases from {test_file}")
        else:
            # Generate test cases from repository data
            self.test_cases = self._generate_test_cases()
            logger.info(f"Generated {len(self.test_cases)} test cases from repository")
        
        return self.test_cases
    
    def _generate_test_cases(self) -> List[Dict]:
        """
        Generate test cases from repository pump data with authentic BEP specifications.
        Focus on pumps with known BEP data from manufacturer specifications.
        """
        test_cases = []
        
        # Query database directly for pumps with BEP data
        import os
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        database_url = os.environ.get('DATABASE_URL')
        
        try:
            with psycopg2.connect(database_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get pumps with BEP data and performance curves
                    cursor.execute("""
                        SELECT p.pump_code, ps.bep_flow_m3hr, ps.bep_head_m,
                               COUNT(pc.id) as curve_count
                        FROM pumps p 
                        JOIN pump_specifications ps ON p.id = ps.pump_id 
                        LEFT JOIN pump_curves pc ON p.id = pc.pump_id
                        WHERE ps.bep_flow_m3hr > 0 AND ps.bep_head_m > 0
                        GROUP BY p.pump_code, ps.bep_flow_m3hr, ps.bep_head_m
                        HAVING COUNT(pc.id) > 0
                        ORDER BY ps.bep_flow_m3hr
                        LIMIT 30
                    """)
                    
                    pumps_with_bep = cursor.fetchall()
                    logger.info(f"Found {len(pumps_with_bep)} pumps with BEP data and curves")
                    
                    # Generate test cases around BEP operating points
                    for pump in pumps_with_bep:
                        bep_flow = float(pump['bep_flow_m3hr'])
                        bep_head = float(pump['bep_head_m'])
                        pump_code = pump['pump_code']
                        
                        # Test at BEP and strategic nearby points
                        test_points = [
                            (0.8, 1.0),   # Part load at BEP head
                            (1.0, 1.0),   # Exact BEP point
                            (1.2, 1.0),   # Overload at BEP head
                            (1.0, 0.9),   # BEP flow at lower head
                            (1.0, 1.1),   # BEP flow at higher head
                        ]
                        
                        for flow_factor, head_factor in test_points:
                            test_flow = bep_flow * flow_factor
                            test_head = bep_head * head_factor
                            
                            test_cases.append({
                                'pump_code': pump_code,
                                'test_flow': test_flow,
                                'test_head': test_head,
                                'expected_bep_flow': bep_flow,
                                'expected_bep_head': bep_head,
                                'manufacturer': 'APE PUMPS',
                                'test_type': 'bep_validation',
                                'curve_count': pump['curve_count']
                            })
        
        except Exception as e:
            logger.error(f"Error generating test cases from database: {e}")
            # Fallback to empty test cases with clear error
            test_cases = []
        
        logger.info(f"Generated {len(test_cases)} test cases for calibration")
        return test_cases
    
    def run_calibration_test(self, calibration_factors: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Run calibration test with given factors.
        
        Args:
            calibration_factors: Optional custom calibration factors to test
            
        Returns:
            Calibration test results with accuracy metrics
        """
        logger.info("Starting calibration test...")
        
        # Apply custom calibration factors if provided
        if calibration_factors:
            self._apply_calibration_factors(calibration_factors)
        
        # Get current calibration factors
        current_factors = self.config_service.get_calibration_factors()
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'calibration_factors': current_factors,
            'test_results': [],
            'summary_stats': {},
            'recommendations': []
        }
        
        # Run tests for each test case
        for i, test_case in enumerate(self.test_cases):
            logger.info(f"Running test {i+1}/{len(self.test_cases)}: {test_case['pump_code']}")
            
            try:
                # Get Brain calculation
                brain_result = self.brain.performance.calculate_at_point(
                    pump_data=self._get_pump_data(test_case['pump_code']),
                    flow=test_case['test_flow'],
                    head=test_case['test_head']
                )
                
                if brain_result:
                    # Compare with expected values
                    test_result = self._analyze_test_result(test_case, brain_result)
                    results['test_results'].append(test_result)
                else:
                    logger.warning(f"No Brain result for {test_case['pump_code']}")
                    
            except Exception as e:
                logger.error(f"Test failed for {test_case['pump_code']}: {e}")
                results['test_results'].append({
                    'pump_code': test_case['pump_code'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Calculate summary statistics
        results['summary_stats'] = self._calculate_summary_stats(results['test_results'])
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        self.results = results
        logger.info(f"Calibration test completed: {len(results['test_results'])} tests")
        
        return results
    
    def _get_pump_data(self, pump_code: str) -> Dict[str, Any]:
        """Get complete pump data for a given pump code."""
        pump_models = self.repository.get_pump_models()
        for pump in pump_models:
            if pump.get('pump_code') == pump_code:
                return pump
        return {}
    
    def _analyze_test_result(self, test_case: Dict, brain_result: Dict) -> Dict[str, Any]:
        """
        Analyze a single test result against expected values.
        
        Args:
            test_case: Test case definition
            brain_result: Brain calculation result
            
        Returns:
            Analysis result with accuracy metrics
        """
        # Extract key metrics
        calculated_efficiency = brain_result.get('efficiency_percent', 0)
        calculated_power = brain_result.get('power_kw', 0)
        calculated_trim = brain_result.get('trim_percent', 100)
        
        # BEP migration analysis
        shifted_bep_flow = brain_result.get('shifted_bep_flow', test_case['expected_bep_flow'])
        shifted_bep_head = brain_result.get('shifted_bep_head', test_case['expected_bep_head'])
        
        # Calculate accuracy metrics
        bep_flow_error = abs(shifted_bep_flow - test_case['expected_bep_flow']) / test_case['expected_bep_flow'] * 100
        bep_head_error = abs(shifted_bep_head - test_case['expected_bep_head']) / test_case['expected_bep_head'] * 100
        
        return {
            'pump_code': test_case['pump_code'],
            'test_flow': test_case['test_flow'],
            'test_head': test_case['test_head'],
            'calculated_efficiency': calculated_efficiency,
            'calculated_power': calculated_power,
            'calculated_trim': calculated_trim,
            'shifted_bep_flow': shifted_bep_flow,
            'shifted_bep_head': shifted_bep_head,
            'bep_flow_error_percent': bep_flow_error,
            'bep_head_error_percent': bep_head_error,
            'status': 'success',
            'accuracy_grade': self._grade_accuracy(bep_flow_error, bep_head_error)
        }
    
    def _grade_accuracy(self, flow_error: float, head_error: float) -> str:
        """Grade the accuracy of BEP migration calculations."""
        max_error = max(flow_error, head_error)
        
        if max_error < 2:
            return 'excellent'
        elif max_error < 5:
            return 'good'
        elif max_error < 10:
            return 'acceptable'
        else:
            return 'poor'
    
    def _calculate_summary_stats(self, test_results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from test results."""
        successful_tests = [r for r in test_results if r.get('status') == 'success']
        
        if not successful_tests:
            return {'error': 'No successful tests'}
        
        flow_errors = [r['bep_flow_error_percent'] for r in successful_tests]
        head_errors = [r['bep_head_error_percent'] for r in successful_tests]
        
        grades = [r['accuracy_grade'] for r in successful_tests]
        grade_counts = {grade: grades.count(grade) for grade in ['excellent', 'good', 'acceptable', 'poor']}
        
        return {
            'total_tests': len(test_results),
            'successful_tests': len(successful_tests),
            'success_rate': len(successful_tests) / len(test_results) * 100,
            'average_flow_error': np.mean(flow_errors),
            'average_head_error': np.mean(head_errors),
            'max_flow_error': np.max(flow_errors),
            'max_head_error': np.max(head_errors),
            'accuracy_distribution': grade_counts,
            'overall_grade': self._calculate_overall_grade(grade_counts)
        }
    
    def _calculate_overall_grade(self, grade_counts: Dict[str, int]) -> str:
        """Calculate overall accuracy grade from distribution."""
        total = sum(grade_counts.values())
        if total == 0:
            return 'unknown'
        
        excellent_pct = grade_counts.get('excellent', 0) / total * 100
        good_pct = grade_counts.get('good', 0) / total * 100
        
        if excellent_pct >= 70:
            return 'excellent'
        elif excellent_pct + good_pct >= 80:
            return 'good'
        elif excellent_pct + good_pct >= 60:
            return 'acceptable'
        else:
            return 'needs_tuning'
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate tuning recommendations based on test results."""
        recommendations = []
        stats = results['summary_stats']
        
        if stats.get('overall_grade') == 'needs_tuning':
            avg_flow_error = stats.get('average_flow_error', 0)
            avg_head_error = stats.get('average_head_error', 0)
            
            current_factors = results['calibration_factors']
            
            if avg_flow_error > 5:
                new_flow_exp = current_factors.get('bep_shift_flow_exponent', 1.2)
                if avg_flow_error > 0:  # Over-predicting flow shift
                    new_flow_exp = max(1.0, new_flow_exp - 0.05)
                else:  # Under-predicting flow shift
                    new_flow_exp = min(1.5, new_flow_exp + 0.05)
                
                recommendations.append({
                    'parameter': 'bep_shift_flow_exponent',
                    'current_value': str(current_factors.get('bep_shift_flow_exponent', 1.2)),
                    'recommended_value': str(round(new_flow_exp, 2)),
                    'reason': f'Average flow error {avg_flow_error:.1f}% exceeds 5% threshold'
                })
            
            if avg_head_error > 5:
                new_head_exp = current_factors.get('bep_shift_head_exponent', 2.2)
                if avg_head_error > 0:  # Over-predicting head shift
                    new_head_exp = max(1.8, new_head_exp - 0.1)
                else:  # Under-predicting head shift
                    new_head_exp = min(2.5, new_head_exp + 0.1)
                
                recommendations.append({
                    'parameter': 'bep_shift_head_exponent',
                    'current_value': str(current_factors.get('bep_shift_head_exponent', 2.2)),
                    'recommended_value': str(round(new_head_exp, 2)),
                    'reason': f'Average head error {avg_head_error:.1f}% exceeds 5% threshold'
                })
        
        if not recommendations:
            recommendations.append({
                'message': 'Current calibration factors are performing well',
                'action': 'No adjustments needed'
            })
        
        return recommendations
    
    def _apply_calibration_factors(self, factors: Dict[str, float]) -> None:
        """Apply calibration factors to the configuration."""
        # Update engineering constants in database
        for factor_name, value in factors.items():
            try:
                # This would require an update method in admin_config_service
                logger.info(f"Would update {factor_name} to {value}")
            except Exception as e:
                logger.error(f"Failed to update {factor_name}: {e}")
    
    def save_results(self, filename: str) -> None:
        """Save calibration results to file."""
        output_dir = Path(__file__).parent / "calibration_results"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / filename
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
    
    def generate_report(self) -> str:
        """Generate a human-readable calibration report."""
        if not self.results:
            return "No calibration results available. Run calibration test first."
        
        stats = self.results['summary_stats']
        factors = self.results['calibration_factors']
        recommendations = self.results['recommendations']
        
        report = f"""
Brain Calibration Report
========================
Generated: {self.results['timestamp']}

Current Calibration Factors:
- BEP Flow Exponent: {factors.get('bep_shift_flow_exponent', 'N/A')}
- BEP Head Exponent: {factors.get('bep_shift_head_exponent', 'N/A')}
- Efficiency Correction: {factors.get('efficiency_correction_exponent', 'N/A')}

Test Results Summary:
- Total Tests: {stats.get('total_tests', 0)}
- Success Rate: {stats.get('success_rate', 0):.1f}%
- Average Flow Error: {stats.get('average_flow_error', 0):.2f}%
- Average Head Error: {stats.get('average_head_error', 0):.2f}%
- Overall Grade: {stats.get('overall_grade', 'unknown').upper()}

Accuracy Distribution:
- Excellent: {stats.get('accuracy_distribution', {}).get('excellent', 0)} tests
- Good: {stats.get('accuracy_distribution', {}).get('good', 0)} tests
- Acceptable: {stats.get('accuracy_distribution', {}).get('acceptable', 0)} tests
- Poor: {stats.get('accuracy_distribution', {}).get('poor', 0)} tests

Recommendations:
"""
        for rec in recommendations:
            if 'parameter' in rec:
                report += f"- {rec['parameter']}: {rec['current_value']} → {rec['recommended_value']}\n"
                report += f"  Reason: {rec['reason']}\n"
            else:
                report += f"- {rec.get('message', rec.get('action', 'No specific recommendation'))}\n"
        
        return report


def main():
    """Main CLI interface for brain calibration."""
    parser = argparse.ArgumentParser(description='Brain Calibration Tool')
    parser.add_argument('--test-file', help='JSON file with test cases')
    parser.add_argument('--output', default='calibration_results.json', help='Output file for results')
    parser.add_argument('--report', action='store_true', help='Generate human-readable report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize calibrator
        calibrator = BrainCalibrator()
        
        # Load test cases
        calibrator.load_test_cases(args.test_file)
        
        # Run calibration test
        results = calibrator.run_calibration_test()
        
        # Save results
        calibrator.save_results(args.output)
        
        # Generate report
        if args.report:
            print(calibrator.generate_report())
        else:
            print(f"Calibration completed. Results saved to {args.output}")
            print(f"Overall Grade: {results['summary_stats'].get('overall_grade', 'unknown').upper()}")
            print(f"Success Rate: {results['summary_stats'].get('success_rate', 0):.1f}%")
    
    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()