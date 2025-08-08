#!/usr/bin/env python3
"""Debug script to analyze count mismatches between Legacy and Brain systems."""

import os
import json
os.environ['BRAIN_MODE'] = 'shadow'

from app.catalog_engine import CatalogEngine
from app.pump_brain import get_pump_brain
from app.pump_repository import get_pump_repository

def analyze_count_mismatch():
    """Find and analyze cases where count differs."""
    
    repo = get_pump_repository()
    catalog = CatalogEngine()
    brain = get_pump_brain(repo)
    
    # Load discrepancies
    with open('brain_discrepancies.json', 'r') as f:
        discrepancies = json.load(f)
    
    count_mismatches = [d for d in discrepancies if d['type'] == 'count_mismatch']
    
    if count_mismatches:
        case = count_mismatches[0]
        flow = case['flow']
        head = case['head']
        
        print(f"=" * 70)
        print(f"COUNT MISMATCH ANALYSIS: Flow={flow} m³/hr, Head={head} m")
        print(f"Legacy count: {case['legacy_count']}, Brain count: {case['brain_count']}")
        print(f"=" * 70)
        
        # Get full results from both systems
        legacy_results = catalog.select_pumps(flow_m3hr=flow, head_m=head, max_results=10)
        brain_results = brain.selection.find_best_pumps(flow, head)
        
        # Find pumps that Legacy includes but Brain excludes
        legacy_codes = {p['pump_code'] for p in legacy_results}
        brain_codes = {p['pump_code'] for p in brain_results}
        
        only_in_legacy = legacy_codes - brain_codes
        only_in_brain = brain_codes - legacy_codes
        
        if only_in_legacy:
            print(f"\nPumps in Legacy but NOT in Brain ({len(only_in_legacy)}):")
            for pump_code in only_in_legacy:
                # Find the pump in legacy results
                legacy_pump = next((p for p in legacy_results if p['pump_code'] == pump_code), None)
                if legacy_pump:
                    print(f"\n  {pump_code}:")
                    print(f"    Legacy score: {legacy_pump.get('overall_score', 0):.1f}")
                    
                    # Try to evaluate with Brain to see why it was excluded
                    pump_data = repo.get_pump_by_code(pump_code)
                    if pump_data:
                        eval_result = brain.selection.evaluate_single_pump(pump_data, flow, head)
                        if not eval_result['feasible']:
                            print(f"    Brain excluded because: {', '.join(eval_result['exclusion_reasons'])}")
                        else:
                            print(f"    Brain score: {eval_result.get('total_score', 0):.1f}")
                            print(f"    ⚠️  Brain evaluated as feasible but not in results!")
        
        if only_in_brain:
            print(f"\nPumps in Brain but NOT in Legacy ({len(only_in_brain)}):")
            for pump_code in only_in_brain:
                brain_pump = next((p for p in brain_results if p['pump_code'] == pump_code), None)
                if brain_pump:
                    print(f"  {pump_code}: Brain score = {brain_pump.get('total_score', 0):.1f}")
        
        print(f"\n\nLegacy pump list (in order):")
        for i, pump in enumerate(legacy_results, 1):
            print(f"  {i}. {pump['pump_code']:20} Score: {pump.get('overall_score', 0):.1f}")
        
        print(f"\nBrain pump list (in order):")
        for i, pump in enumerate(brain_results, 1):
            print(f"  {i}. {pump['pump_code']:20} Score: {pump.get('total_score', 0):.1f}")

analyze_count_mismatch()