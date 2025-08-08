#!/usr/bin/env python
"""
Comprehensive Brain vs Legacy Discrepancy Analysis
===================================================
Tests a wide range of pumps and duty points to identify differences
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('brain_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force shadow mode for testing
os.environ['BRAIN_MODE'] = 'shadow'

from app.catalog_engine import get_catalog_engine
from app.pump_repository import get_pump_repository
from app.pump_brain import get_pump_brain, BrainMetrics


class DiscrepancyAnalyzer:
    """Analyze discrepancies between Brain and Legacy systems"""
    
    def __init__(self):
        self.repository = get_pump_repository()
        self.catalog = get_catalog_engine()
        self.brain = get_pump_brain(self.repository)
        self.discrepancies = []
        self.test_count = 0
        self.match_count = 0
        
    def analyze_pump_selection(self, flow: float, head: float, test_name: str = ""):
        """Compare pump selection between legacy and Brain"""
        
        self.test_count += 1
        logger.info(f"\nTest {self.test_count}: {test_name} - Flow={flow} m³/hr, Head={head} m")
        
        try:
            # Legacy selection
            legacy_results = self.catalog.select_pumps(
                flow_m3hr=flow,
                head_m=head,
                max_results=5
            )
            
            # Brain selection (called in shadow mode by catalog)
            brain_results = self.brain.selection.find_best_pumps(
                flow, head
            )[:5]  # Get top 5 results
            
            # Compare results
            if self._compare_selections(legacy_results, brain_results, flow, head):
                self.match_count += 1
                logger.info("  ✓ Results match")
            else:
                logger.warning("  ⚠ Discrepancy found")
                
        except Exception as e:
            logger.error(f"  ✗ Error in test: {str(e)}")
            
    def _compare_selections(self, legacy: List[Dict], brain: List[Dict], flow: float, head: float) -> bool:
        """Compare selection results and log discrepancies"""
        
        if not legacy and not brain:
            return True
            
        if len(legacy) != len(brain):
            self.discrepancies.append({
                'type': 'count_mismatch',
                'flow': flow,
                'head': head,
                'legacy_count': len(legacy),
                'brain_count': len(brain)
            })
            return False
            
        # Compare top pump
        if legacy and brain:
            legacy_top = legacy[0]
            brain_top = brain[0]
            
            if legacy_top['pump_code'] != brain_top['pump_code']:
                self.discrepancies.append({
                    'type': 'top_pump_mismatch',
                    'flow': flow,
                    'head': head,
                    'legacy_pump': legacy_top['pump_code'],
                    'brain_pump': brain_top['pump_code'],
                    'legacy_score': legacy_top.get('overall_score', 0),
                    'brain_score': brain_top.get('overall_score', 0)
                })
                return False
                
            # Compare scores
            score_diff = abs(legacy_top.get('overall_score', 0) - brain_top.get('overall_score', 0))
            if score_diff > 1.0:  # More than 1 point difference
                self.discrepancies.append({
                    'type': 'score_discrepancy',
                    'flow': flow,
                    'head': head,
                    'pump': legacy_top['pump_code'],
                    'legacy_score': legacy_top.get('overall_score', 0),
                    'brain_score': brain_top.get('overall_score', 0),
                    'difference': score_diff
                })
                return False
                
        return True
        
    def analyze_performance_calculation(self, pump_code: str, flow: float, head: float):
        """Compare performance calculations between legacy and Brain"""
        
        logger.info(f"\nPerformance Test: {pump_code} @ {flow} m³/hr, {head} m")
        
        try:
            # Get pump
            pump = self.repository.get_pump_by_code(pump_code)
            if not pump:
                logger.error(f"  Pump {pump_code} not found")
                return
                
            # Legacy catalog pump
            catalog_pump = self.catalog.get_pump_by_code(pump_code)
            if not catalog_pump:
                logger.error(f"  Catalog pump {pump_code} not found")
                return
                
            # Legacy performance
            legacy_perf = catalog_pump.find_best_solution_for_duty(flow, head)
            
            # Brain performance
            brain_perf = self.brain.performance.calculate_at_point(pump, flow, head)
            
            # Compare
            if self._compare_performance(legacy_perf, brain_perf, pump_code, flow, head):
                logger.info("  ✓ Performance calculations match")
            else:
                logger.warning("  ⚠ Performance discrepancy found")
                
        except Exception as e:
            logger.error(f"  ✗ Error in performance test: {str(e)}")
            
    def _compare_performance(self, legacy: Dict, brain: Dict, pump: str, flow: float, head: float) -> bool:
        """Compare performance results"""
        
        if not legacy and not brain:
            return True
            
        if bool(legacy) != bool(brain):
            self.discrepancies.append({
                'type': 'performance_availability',
                'pump': pump,
                'flow': flow,
                'head': head,
                'legacy_has_solution': bool(legacy),
                'brain_has_solution': bool(brain)
            })
            return False
            
        if legacy and brain:
            # Compare key metrics
            metrics = ['flow_m3hr', 'head_m', 'efficiency_pct', 'power_kw', 'impeller_diameter_mm']
            
            for metric in metrics:
                legacy_val = legacy.get(metric)
                brain_val = brain.get(metric)
                
                if legacy_val is not None and brain_val is not None:
                    diff_pct = abs(legacy_val - brain_val) / legacy_val * 100 if legacy_val else 0
                    
                    if diff_pct > 2.0:  # More than 2% difference
                        self.discrepancies.append({
                            'type': 'performance_metric',
                            'pump': pump,
                            'flow': flow,
                            'head': head,
                            'metric': metric,
                            'legacy_value': legacy_val,
                            'brain_value': brain_val,
                            'diff_percent': diff_pct
                        })
                        return False
                        
            # Compare sizing method
            legacy_sizing = legacy.get('sizing_info', {}).get('sizing_method')
            brain_sizing = brain.get('sizing_info', {}).get('sizing_method')
            
            if legacy_sizing != brain_sizing:
                self.discrepancies.append({
                    'type': 'sizing_method',
                    'pump': pump,
                    'flow': flow,
                    'head': head,
                    'legacy_method': legacy_sizing,
                    'brain_method': brain_sizing
                })
                return False
                
        return True
        
    def run_comprehensive_tests(self):
        """Run a comprehensive set of tests"""
        
        logger.info("="*70)
        logger.info("STARTING COMPREHENSIVE BRAIN VS LEGACY ANALYSIS")
        logger.info("="*70)
        
        # Test cases covering various scenarios
        test_cases = [
            # Low flow, low head
            {'flow': 10, 'head': 10, 'name': 'Low Flow/Head'},
            {'flow': 25, 'head': 15, 'name': 'Small Pump Range'},
            
            # Medium range - typical applications
            {'flow': 50, 'head': 30, 'name': 'Medium Low'},
            {'flow': 100, 'head': 50, 'name': 'Medium Standard'},
            {'flow': 150, 'head': 75, 'name': 'Medium High'},
            
            # High flow scenarios
            {'flow': 200, 'head': 40, 'name': 'High Flow Low Head'},
            {'flow': 300, 'head': 60, 'name': 'High Flow Medium Head'},
            {'flow': 400, 'head': 50, 'name': 'High Flow Standard'},
            {'flow': 500, 'head': 80, 'name': 'Very High Flow'},
            
            # High head scenarios
            {'flow': 50, 'head': 100, 'name': 'Low Flow High Head'},
            {'flow': 100, 'head': 150, 'name': 'Medium Flow Very High Head'},
            {'flow': 150, 'head': 200, 'name': 'High Head Application'},
            
            # Edge cases - likely to require trimming
            {'flow': 60, 'head': 40, 'name': 'Typical Trim Case'},
            {'flow': 80, 'head': 35, 'name': 'Moderate Trim'},
            {'flow': 120, 'head': 45, 'name': 'Light Trim'},
            
            # Specific pump tests (known issues)
            {'flow': 60, 'head': 40, 'name': '65-200 1F Test'},  # Known trimming case
            {'flow': 400, 'head': 50, 'name': '8K Pump Test'},   # Large pump
        ]
        
        # Run selection tests
        logger.info("\n" + "="*50)
        logger.info("PUMP SELECTION TESTS")
        logger.info("="*50)
        
        for test in test_cases:
            self.analyze_pump_selection(test['flow'], test['head'], test['name'])
            
        # Run performance calculation tests on specific pumps
        logger.info("\n" + "="*50)
        logger.info("PERFORMANCE CALCULATION TESTS")
        logger.info("="*50)
        
        performance_tests = [
            {'pump': '65-200 1F', 'flow': 60, 'head': 40},
            {'pump': '8 K', 'flow': 400, 'head': 50},
            {'pump': 'WXH-65-185 2P', 'flow': 100, 'head': 50},
            {'pump': '50-160 2F 2P', 'flow': 50, 'head': 30},
            {'pump': '4/5 ALE', 'flow': 150, 'head': 60},
        ]
        
        for test in performance_tests:
            self.analyze_performance_calculation(test['pump'], test['flow'], test['head'])
            
    def generate_report(self):
        """Generate analysis report"""
        
        logger.info("\n" + "="*70)
        logger.info("DISCREPANCY ANALYSIS REPORT")
        logger.info("="*70)
        
        logger.info(f"\nTotal Tests: {self.test_count}")
        logger.info(f"Matching Results: {self.match_count}")
        logger.info(f"Discrepancies Found: {len(self.discrepancies)}")
        
        if self.test_count > 0:
            match_rate = (self.match_count / self.test_count) * 100
            logger.info(f"Match Rate: {match_rate:.1f}%")
        
        if self.discrepancies:
            logger.info("\n" + "-"*50)
            logger.info("DISCREPANCY DETAILS")
            logger.info("-"*50)
            
            # Group discrepancies by type
            by_type = {}
            for disc in self.discrepancies:
                disc_type = disc['type']
                if disc_type not in by_type:
                    by_type[disc_type] = []
                by_type[disc_type].append(disc)
                
            for disc_type, items in by_type.items():
                logger.info(f"\n{disc_type.upper()} ({len(items)} occurrences):")
                
                for item in items[:3]:  # Show first 3 of each type
                    if disc_type == 'top_pump_mismatch':
                        logger.info(f"  Flow={item['flow']}, Head={item['head']}")
                        logger.info(f"    Legacy: {item['legacy_pump']} (score={item['legacy_score']:.1f})")
                        logger.info(f"    Brain:  {item['brain_pump']} (score={item['brain_score']:.1f})")
                    elif disc_type == 'performance_metric':
                        logger.info(f"  {item['pump']} @ {item['flow']}m³/hr, {item['head']}m")
                        logger.info(f"    {item['metric']}: Legacy={item['legacy_value']:.2f}, Brain={item['brain_value']:.2f} ({item['diff_percent']:.1f}% diff)")
                    elif disc_type == 'sizing_method':
                        logger.info(f"  {item['pump']} @ {item['flow']}m³/hr, {item['head']}m")
                        logger.info(f"    Legacy method: {item['legacy_method']}")
                        logger.info(f"    Brain method: {item['brain_method']}")
                        
            # Save detailed log
            with open('brain_discrepancies.json', 'w') as f:
                json.dump(self.discrepancies, f, indent=2)
            logger.info(f"\nDetailed discrepancies saved to brain_discrepancies.json")
            
        # Get Brain metrics
        metrics = BrainMetrics.get_metrics()
        if metrics.get('discrepancies'):
            logger.info(f"\nBrain Metrics recorded {len(metrics['discrepancies'])} discrepancies")
            
        logger.info("\n" + "="*70)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*70)
        
        return len(self.discrepancies) == 0


def main():
    """Run the analysis"""
    analyzer = DiscrepancyAnalyzer()
    analyzer.run_comprehensive_tests()
    success = analyzer.generate_report()
    
    if success:
        logger.info("\n✓ PERFECT PARITY ACHIEVED - Brain and Legacy are fully consistent!")
        return 0
    else:
        logger.info("\n⚠ Discrepancies found - review brain_discrepancies.json for details")
        logger.info("Next steps:")
        logger.info("  1. Review each discrepancy type")
        logger.info("  2. Determine if Brain is correct (improvement) or needs fixing")
        logger.info("  3. Update Brain logic in app/brain/*.py modules")
        logger.info("  4. Re-run this analysis until parity is achieved")
        return 1


if __name__ == "__main__":
    sys.exit(main())