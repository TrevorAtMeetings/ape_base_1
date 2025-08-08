"""
Test Suite for PumpBrain System
================================
Comprehensive tests for the centralized Brain intelligence
"""

import unittest
import os
import sys
from unittest.mock import MagicMock, patch
import json

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pump_brain import PumpBrain, get_pump_brain, reset_brain, BrainMetrics
from app.brain.cache import BrainCache


class TestPumpBrain(unittest.TestCase):
    """Test the main PumpBrain class"""
    
    def setUp(self):
        """Set up test fixtures"""
        reset_brain()
        self.mock_repository = MagicMock()
        self.brain = PumpBrain(self.mock_repository)
        
        # Sample pump data
        self.sample_pump = {
            'pump_code': 'TEST-PUMP-1',
            'pump_name': 'Test Pump Model 1',
            'specifications': {
                'bep_flow_m3hr': 100,
                'bep_head_m': 50,
                'min_impeller_mm': 200,
                'max_impeller_mm': 250,
                'test_speed_rpm': 1450
            },
            'curves': [{
                'curve_id': 1,
                'impeller_diameter_mm': 250,
                'performance_points': [
                    {'flow_m3hr': 0, 'head_m': 65, 'efficiency_pct': 0},
                    {'flow_m3hr': 50, 'head_m': 60, 'efficiency_pct': 65},
                    {'flow_m3hr': 100, 'head_m': 50, 'efficiency_pct': 78},
                    {'flow_m3hr': 150, 'head_m': 35, 'efficiency_pct': 70},
                    {'flow_m3hr': 200, 'head_m': 15, 'efficiency_pct': 50}
                ]
            }]
        }
    
    def test_brain_initialization(self):
        """Test Brain initializes correctly"""
        self.assertIsNotNone(self.brain)
        self.assertIsNotNone(self.brain.selection)
        self.assertIsNotNone(self.brain.performance)
        self.assertIsNotNone(self.brain.charts)
        self.assertIsNotNone(self.brain.validator)
        self.assertEqual(self.brain.repository, self.mock_repository)
    
    def test_find_best_pump(self):
        """Test finding best pump for conditions"""
        # Mock repository response
        self.mock_repository.get_pump_models.return_value = [self.sample_pump]
        
        # Test pump selection
        results = self.brain.find_best_pump(90, 45)
        
        self.assertIsInstance(results, list)
        self.mock_repository.get_pump_models.assert_called_once()
    
    def test_evaluate_pump(self):
        """Test evaluating specific pump"""
        # Mock repository response
        self.mock_repository.get_pump_by_code.return_value = self.sample_pump
        
        # Test evaluation
        evaluation = self.brain.evaluate_pump('TEST-PUMP-1', 100, 50)
        
        self.assertIsInstance(evaluation, dict)
        self.assertIn('pump_code', evaluation)
        self.assertEqual(evaluation['pump_code'], 'TEST-PUMP-1')
    
    def test_calculate_performance(self):
        """Test performance calculation"""
        performance = self.brain.calculate_performance(
            self.sample_pump, 100, 45, impeller_trim=95
        )
        
        self.assertIsInstance(performance, dict)
        if performance:  # May be None if calculation fails
            self.assertIn('flow_m3hr', performance)
            self.assertIn('head_m', performance)
    
    def test_unit_conversion(self):
        """Test unit conversions"""
        # Flow conversion
        gpm_value = 100
        m3hr_value = self.brain.convert_units(gpm_value, 'gpm', 'm3hr')
        self.assertAlmostEqual(m3hr_value, 22.7124, places=2)
        
        # Head conversion
        ft_value = 100
        m_value = self.brain.convert_units(ft_value, 'ft', 'm')
        self.assertAlmostEqual(m_value, 30.48, places=2)
        
        # Power conversion
        hp_value = 10
        kw_value = self.brain.convert_units(hp_value, 'hp', 'kw')
        self.assertAlmostEqual(kw_value, 7.457, places=2)
    
    def test_validate_operating_point(self):
        """Test operating point validation"""
        # Valid point
        validation = self.brain.validator.validate_operating_point(100, 50)
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['errors']), 0)
        
        # Invalid point (negative flow)
        validation = self.brain.validator.validate_operating_point(-10, 50)
        self.assertFalse(validation['valid'])
        self.assertIn('Flow must be positive', validation['errors'])
    
    # Shadow mode test removed - Brain is now always active
    # Test archived as Brain operates in production mode only
    
    def test_cache_functionality(self):
        """Test caching system"""
        cache = BrainCache(max_size=10, default_ttl=60)
        
        # Test set and get
        cache.set('test_key', {'value': 123})
        cached_value = cache.get('test_key')
        self.assertEqual(cached_value, {'value': 123})
        
        # Test cache miss
        missing = cache.get('nonexistent')
        self.assertIsNone(missing)
        
        # Test stats
        stats = cache.get_stats()
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
    
    def test_brain_status(self):
        """Test Brain status reporting"""
        status = self.brain.get_status()
        
        self.assertIn('status', status)
        self.assertEqual(status['status'], 'operational')
        self.assertIn('mode', status)
        self.assertIn('uptime_seconds', status)
        self.assertIn('cache_stats', status)
    
    def test_axis_range_calculation(self):
        """Test chart axis range calculation"""
        curves = [self.sample_pump['curves'][0]]
        operating_point = (100, 50)
        
        ranges = self.brain.charts.calculate_axis_ranges(curves, operating_point)
        
        self.assertIn('flow', ranges)
        self.assertIn('head', ranges)
        self.assertIn('efficiency', ranges)
        self.assertGreater(ranges['flow']['max'], 100)
        self.assertGreater(ranges['head']['max'], 50)


class TestBrainPerformance(unittest.TestCase):
    """Test Brain performance and efficiency"""
    
    def setUp(self):
        """Set up for performance tests"""
        reset_brain()
        self.brain = get_pump_brain()
    
    def test_performance_metrics(self):
        """Test performance measurement"""
        import time
        
        # Perform operation
        start = time.time()
        self.brain.convert_units(100, 'gpm', 'm3hr')
        duration = time.time() - start
        
        # Should be very fast
        self.assertLess(duration, 0.1)  # Less than 100ms
        
        # Check metrics recorded
        metrics = BrainMetrics.get_metrics()
        self.assertIn('operations', metrics)
    
    def test_cache_performance(self):
        """Test cache improves performance"""
        import time
        
        # Mock expensive operation
        def expensive_calc():
            time.sleep(0.01)  # Simulate 10ms operation
            return {'result': 42}
        
        cache = BrainCache()
        
        # First call - no cache
        start = time.time()
        cache.set('test', expensive_calc())
        first_duration = time.time() - start
        
        # Second call - from cache
        start = time.time()
        result = cache.get('test')
        cached_duration = time.time() - start
        
        # Cache should be much faster
        self.assertLess(cached_duration, first_duration / 10)
        self.assertEqual(result, {'result': 42})


class TestBrainIntegration(unittest.TestCase):
    """Test Brain integration with existing system"""
    
    def setUp(self):
        """Set up integration tests"""
        reset_brain()
        self.brain = get_pump_brain()
    
    @patch('app.pump_repository.get_pump_repository')
    def test_repository_integration(self, mock_get_repo):
        """Test Brain works with repository"""
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        
        # Create Brain with repository
        brain = PumpBrain(mock_repo)
        
        # Verify repository is used
        mock_repo.get_pump_models.return_value = []
        results = brain.find_best_pump(100, 50)
        
        mock_repo.get_pump_models.assert_called()
        self.assertEqual(results, [])
    
    def test_affinity_laws_consistency(self):
        """Test affinity laws match existing implementation"""
        base_curve = {
            'performance_points': [
                {'flow_m3hr': 100, 'head_m': 50, 'efficiency_pct': 75, 'power_kw': 10}
            ]
        }
        
        # Test impeller scaling (90% trim)
        scaled = self.brain.performance.apply_affinity_laws(base_curve, diameter_ratio=0.9)
        
        # Verify affinity law calculations
        # Q₂ = Q₁ × (D₂/D₁) = 100 × 0.9 = 90
        # H₂ = H₁ × (D₂/D₁)² = 50 × 0.81 = 40.5
        # P₂ = P₁ × (D₂/D₁)³ = 10 × 0.729 = 7.29
        
        point = scaled['performance_points'][0]
        self.assertAlmostEqual(point['flow_m3hr'], 90, places=1)
        self.assertAlmostEqual(point['head_m'], 40.5, places=1)
        self.assertAlmostEqual(point['power_kw'], 7.29, places=1)
    
    def test_8K_pump_selection(self):
        """
        Test a known-good selection for the 8K pump that the Brain was failing.
        Duty point: 350 m³/hr @ 50m head.
        """
        # Get the 8K pump data directly from the repository
        from app.pump_repository import get_pump_repository
        repository = get_pump_repository()
        pump_data = repository.get_pump_by_code('8 K')
        self.assertIsNotNone(pump_data, "Could not find 8K pump in repository")
        
        # Log pump specifications for debugging
        specs = pump_data.get('specifications', {})
        print(f"\n=== 8K Pump Debug ===")
        print(f"Specs: min_impeller={specs.get('min_impeller_mm')}, max_impeller={specs.get('max_impeller_mm')}")
        
        # Get available curves
        curves = pump_data.get('curves', [])
        available_diameters = sorted([c.get('impeller_diameter_mm') for c in curves if c.get('impeller_diameter_mm')])
        print(f"Available impeller diameters: {available_diameters}")
        
        # Debug each curve's performance points
        for curve in curves:
            diam = curve.get('impeller_diameter_mm')
            points = curve.get('performance_points', [])
            if points:
                flows = [p['flow_m3hr'] for p in points[:3]]  # First 3 points
                heads = [p['head_m'] for p in points[:3]]
                print(f"  Curve {diam}mm: flows={flows}, heads={heads}")
        
        # Manually test the logic that Brain uses
        print(f"\n--- Testing Brain logic for 350 m³/hr @ 50m ---")
        
        # Step 1: Find suitable curves (Brain's _find_suitable_curves logic)
        suitable_curves = []
        for curve in curves:
            points = curve.get('performance_points', [])
            if points:
                flows = [p['flow_m3hr'] for p in points]
                if min(flows) <= 350 <= max(flows):
                    suitable_curves.append(curve)
                    print(f"  Curve {curve.get('impeller_diameter_mm')}mm is suitable (flow range: {min(flows)}-{max(flows)})")
        
        # Step 2: Test calculate_required_diameter for 406.4mm curve
        largest_curve = next((c for c in curves if c.get('impeller_diameter_mm') == 406.4), None)
        if largest_curve:
            points = largest_curve.get('performance_points', [])
            flows = [p['flow_m3hr'] for p in points]
            heads = [p['head_m'] for p in points]
            
            # Find head at 350 m³/hr using interpolation
            import numpy as np
            from scipy import interpolate
            interp_func = interpolate.interp1d(flows, heads, kind='linear', bounds_error=False)
            head_at_350 = float(interp_func(350))
            print(f"  406.4mm curve: head at 350 m³/hr = {head_at_350:.2f}m")
            
            # Calculate required diameter
            if head_at_350 > 50:
                diameter_ratio = np.sqrt(50 / head_at_350)
                required_diameter = 406.4 * diameter_ratio
                trim_percent = diameter_ratio * 100
                print(f"  Required trim: {trim_percent:.1f}% (diameter: {required_diameter:.1f}mm)")
                print(f"  Is trim >= 85%? {trim_percent >= 85}")
        
        # Use the Brain's performance module directly to debug
        performance_solution = self.brain.performance.calculate_at_point(
            pump_data, 
            flow=350.0, 
            head=50.0
        )
        
        # This is where the failure is. This should NOT be None.
        self.assertIsNotNone(performance_solution, "Brain's performance module failed to find a solution for 8K pump.")
        
        # Further assertions
        self.assertTrue(performance_solution.get('meets_requirements'), 
                       f"Solution doesn't meet requirements: {performance_solution}")
        self.assertAlmostEqual(performance_solution.get('head_m'), 50.0, delta=2.0,
                              msg=f"Head mismatch: expected ~50m, got {performance_solution.get('head_m')}m")
        
        # Log the solution for debugging
        print(f"\n8K pump solution: {performance_solution}")


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)