#!/usr/bin/env python
"""
Test Script for Three-Path Selection Logic
Tests the enhanced SelectionIntelligence module with variable_speed and variable_diameter flags
"""

import sys
import os
sys.path.insert(0, '.')

from app.pump_brain import PumpBrain
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_three_path_logic():
    """Test the Three-Path Selection Logic implementation"""
    
    # Initialize Brain
    brain = PumpBrain()
    
    # Test duty point
    test_flow = 500  # m³/hr
    test_head = 50   # m
    
    logger.info("=" * 80)
    logger.info("TESTING THREE-PATH SELECTION LOGIC")
    logger.info("=" * 80)
    logger.info(f"Test Duty Point: {test_flow} m³/hr @ {test_head} m")
    logger.info("")
    
    # Get pump selection results with exclusion details
    result = brain.selection.find_best_pumps(
        flow=test_flow,
        head=test_head,
        constraints={'max_results': 10},
        include_exclusions=True
    )
    
    # Analyze results by operation mode
    flexible_pumps = []
    trim_only_pumps = []
    vfd_only_pumps = []
    fixed_pumps = []
    
    # Check ranked pumps
    for pump in result.get('ranked_pumps', []):
        operation_mode = pump.get('operation_mode', 'UNKNOWN')
        if operation_mode == 'FLEXIBLE':
            flexible_pumps.append(pump)
        elif operation_mode == 'TRIM_ONLY':
            trim_only_pumps.append(pump)
        elif operation_mode == 'VFD_ONLY':
            vfd_only_pumps.append(pump)
        elif operation_mode == 'FIXED':
            fixed_pumps.append(pump)
    
    # Check excluded pumps for VFD-only
    exclusion_details = result.get('exclusion_details', {})
    excluded_pumps = exclusion_details.get('excluded_pumps', [])
    
    vfd_excluded = [p for p in excluded_pumps 
                    if 'VFD-only pump' in str(p.get('exclusion_reasons', []))]
    
    # Display results
    logger.info("RESULTS BY OPERATION MODE:")
    logger.info("-" * 40)
    
    logger.info(f"✓ FLEXIBLE PUMPS (Can use both methods): {len(flexible_pumps)}")
    for pump in flexible_pumps[:3]:
        logger.info(f"  - {pump['pump_code']}: Score {pump['total_score']:.1f}, Method: {pump.get('selection_method')}")
    
    logger.info(f"\n✓ TRIM-ONLY PUMPS (Fixed-speed): {len(trim_only_pumps)}")
    for pump in trim_only_pumps[:3]:
        logger.info(f"  - {pump['pump_code']}: Score {pump['total_score']:.1f}, Method: {pump.get('selection_method')}")
    
    logger.info(f"\n✓ VFD-ONLY PUMPS (In results): {len(vfd_only_pumps)}")
    for pump in vfd_only_pumps[:3]:
        logger.info(f"  - {pump['pump_code']}: Score {pump['total_score']:.1f}, Method: {pump.get('selection_method')}")
    
    logger.info(f"\n✓ VFD-ONLY PUMPS (Excluded): {len(vfd_excluded)}")
    for pump in vfd_excluded[:5]:
        logger.info(f"  - {pump['pump_code']}: {pump['exclusion_reasons']}")
    
    logger.info(f"\n✓ FIXED PUMPS (No adjustment): {len(fixed_pumps)}")
    for pump in fixed_pumps[:3]:
        logger.info(f"  - {pump['pump_code']}: Score {pump['total_score']:.1f}")
    
    # Summary statistics
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY STATISTICS:")
    logger.info("-" * 40)
    
    exclusion_summary = exclusion_details.get('exclusion_summary', {})
    total_evaluated = exclusion_details.get('total_evaluated', 0)
    feasible_count = exclusion_details.get('feasible_count', 0)
    excluded_count = exclusion_details.get('excluded_count', 0)
    
    logger.info(f"Total pumps evaluated: {total_evaluated}")
    logger.info(f"Feasible pumps: {feasible_count}")
    logger.info(f"Excluded pumps: {excluded_count}")
    
    logger.info(f"\nExclusion Reasons:")
    for reason, count in exclusion_summary.items():
        logger.info(f"  - {reason}: {count}")
    
    # Test specific pump examples if available
    logger.info("\n" + "=" * 80)
    logger.info("TESTING SPECIFIC PUMP EXAMPLES:")
    logger.info("-" * 40)
    
    # Get all pumps from repository to test specific ones
    all_pumps = brain.repository.get_pump_models()
    
    # Test a known FLEXIBLE pump (both = true)
    flexible_example = next((p for p in all_pumps if p['pump_code'] == '32 HC 6P'), None)
    if flexible_example:
        evaluation = brain.selection.evaluate_single_pump(flexible_example, test_flow, test_head)
        logger.info(f"\n32 HC 6P (Expected: FLEXIBLE)")
        logger.info(f"  Operation Mode: {evaluation.get('operation_mode')}")
        logger.info(f"  Selection Method: {evaluation.get('selection_method')}")
        logger.info(f"  Flexibility: {evaluation.get('pump_flexibility')}")
    
    # Test a known TRIM-ONLY pump
    trim_example = next((p for p in all_pumps if p['pump_code'] == '10 WLN 18A'), None)
    if trim_example:
        evaluation = brain.selection.evaluate_single_pump(trim_example, test_flow, test_head)
        logger.info(f"\n10 WLN 18A (Expected: TRIM-ONLY)")
        logger.info(f"  Operation Mode: {evaluation.get('operation_mode')}")
        logger.info(f"  Selection Method: {evaluation.get('selection_method')}")
        logger.info(f"  Flexibility: {evaluation.get('pump_flexibility')}")
    
    # Test a known VFD-ONLY pump
    vfd_example = next((p for p in all_pumps if p['pump_code'] == '8312-14'), None)
    if vfd_example:
        evaluation = brain.selection.evaluate_single_pump(vfd_example, test_flow, test_head)
        logger.info(f"\n8312-14 (Expected: VFD-ONLY)")
        logger.info(f"  Operation Mode: {evaluation.get('operation_mode')}")
        logger.info(f"  Selection Method: {evaluation.get('selection_method')}")
        logger.info(f"  Flexibility: {evaluation.get('pump_flexibility')}")
        logger.info(f"  VFD Required: {evaluation.get('vfd_required', False)}")
        logger.info(f"  Feasible: {evaluation.get('feasible')}")
        if not evaluation.get('feasible'):
            logger.info(f"  Exclusion Reason: {evaluation.get('exclusion_reasons')}")
    
    logger.info("\n" + "=" * 80)
    logger.info("THREE-PATH SELECTION LOGIC TEST COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    test_three_path_logic()