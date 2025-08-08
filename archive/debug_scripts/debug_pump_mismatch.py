#!/usr/bin/env python3
"""Debug script to analyze top pump mismatches between Legacy and Brain systems."""

import os
import json
os.environ['BRAIN_MODE'] = 'shadow'

from app.catalog_engine import CatalogEngine
from app.pump_brain import get_pump_brain
from app.pump_repository import get_pump_repository

def analyze_mismatch(flow, head):
    """Analyze scoring differences for a specific test case."""
    
    repo = get_pump_repository()
    catalog = CatalogEngine()
    brain = get_pump_brain(repo)
    
    print(f"=" * 70)
    print(f"ANALYZING: Flow={flow} m³/hr, Head={head} m")
    print(f"=" * 70)
    
    # Get Legacy results
    legacy_results = catalog.select_pumps(flow_m3hr=flow, head_m=head, max_results=5)
    
    # Get Brain results
    brain_results = brain.selection.find_best_pumps(flow, head)
    
    if legacy_results and brain_results:
        # Show top 3 from each
        print("\nLEGACY TOP 3:")
        print("-" * 40)
        for i, pump in enumerate(legacy_results[:3], 1):
            print(f"\n{i}. {pump['pump_code']:20} Total: {pump.get('overall_score', 0):.1f}")
            breakdown = pump.get('score_breakdown', {})
            if breakdown:
                bep = breakdown.get('bep_proximity', {})
                eff = breakdown.get('efficiency', {})
                margin = breakdown.get('head_margin', {})
                trim = breakdown.get('trim_penalty', {})
                
                print(f"   BEP Proximity  : {bep.get('score', 0):6.1f} pts (QBP: {bep.get('qbp_percent', 0):.0f}%)")
                print(f"   Efficiency     : {eff.get('score', 0):6.1f} pts ({eff.get('efficiency_pct', 0):.1f}%)")
                print(f"   Head Margin    : {margin.get('score', 0):6.1f} pts ({margin.get('margin_pct', 0):.1f}%)")
                if trim.get('score', 0) != 0:
                    print(f"   Trim Penalty   : {trim.get('score', 0):6.1f} pts ({trim.get('trim_percent', 100):.1f}%)")
        
        print("\n\nBRAIN TOP 3:")
        print("-" * 40)
        for i, pump in enumerate(brain_results[:3], 1):
            print(f"\n{i}. {pump['pump_code']:20} Total: {pump.get('total_score', 0):.1f}")
            components = pump.get('score_components', {})
            if components:
                print(f"   BEP Proximity  : {components.get('bep_proximity', 0):6.1f} pts (QBP: {pump.get('qbp_percent', 0):.0f}%)")
                print(f"   Efficiency     : {components.get('efficiency', 0):6.1f} pts ({pump.get('efficiency_pct', 0):.1f}%)")
                print(f"   Head Margin    : {components.get('head_margin', 0):6.1f} pts ({pump.get('head_margin_pct', 0):.1f}%)")
                if 'trim_penalty' in components:
                    print(f"   Trim Penalty   : {components.get('trim_penalty', 0):6.1f} pts ({pump.get('trim_percent', 100):.1f}%)")
        
        # Check if top pump is different
        legacy_top = legacy_results[0]['pump_code']
        brain_top = brain_results[0]['pump_code']
        
        if legacy_top != brain_top:
            print(f"\n⚠️  TOP PUMP MISMATCH!")
            print(f"   Legacy chooses: {legacy_top}")
            print(f"   Brain chooses:  {brain_top}")
            
            # Find Brain's ranking of Legacy's top pump
            brain_rank = None
            for idx, pump in enumerate(brain_results):
                if pump['pump_code'] == legacy_top:
                    brain_rank = idx + 1
                    print(f"\n   Brain ranks '{legacy_top}' at position #{brain_rank}")
                    print(f"   Brain score for '{legacy_top}': {pump.get('total_score', 0):.1f}")
                    break
            
            if brain_rank is None:
                print(f"\n   Brain did not include '{legacy_top}' in results!")
        else:
            print(f"\n✅ Both systems agree on top pump: {legacy_top}")

# Load discrepancies and analyze top pump mismatches
with open('brain_discrepancies.json', 'r') as f:
    discrepancies = json.load(f)

top_mismatches = [d for d in discrepancies if d['type'] == 'top_pump_mismatch']

if top_mismatches:
    # Analyze first mismatch case
    case = top_mismatches[0]
    analyze_mismatch(case['flow'], case['head'])