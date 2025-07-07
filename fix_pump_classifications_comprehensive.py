#!/usr/bin/env python3
"""
Comprehensive Pump Type Classification Fix
Corrects misclassified pump types in the APE catalog database
- ALE pumps should be AXIAL_FLOW, not HSC
- Ensures multi-stage pumps are properly classified
"""

import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_pump_type_classifications():
    """Fix pump type classifications in the catalog database"""
    
    # Load current database
    with open('data/ape_catalog_database.json', 'r') as f:
        catalog = json.load(f)
    
    pumps = catalog['pump_models']
    corrections = 0
    
    logger.info(f"Checking {len(pumps)} pumps for classification errors...")
    
    for pump in pumps:
        pump_code = pump.get('pump_code', '')
        current_type = pump.get('pump_type', '')
        correct_type = None
        
        # Fix ALE pumps - should be AXIAL_FLOW
        if 'ALE' in pump_code.upper():
            if current_type != 'AXIAL_FLOW':
                correct_type = 'AXIAL_FLOW'
                logger.info(f"Correcting {pump_code}: {current_type} → AXIAL_FLOW")
        
        # Fix multi-stage indicators
        elif any(stage in pump_code.upper() for stage in ['2P', '3P', '4P', '6P', '8P', '2F']):
            if current_type != 'MULTISTAGE':
                correct_type = 'MULTISTAGE'
                logger.info(f"Correcting {pump_code}: {current_type} → MULTISTAGE")
        
        # Apply correction
        if correct_type:
            pump['pump_type'] = correct_type
            corrections += 1
    
    # Update metadata
    if corrections > 0:
        catalog['metadata']['pump_type_corrections'] = corrections
        catalog['metadata']['last_updated'] = "2025-06-17 09:40:00"
        
        # Save updated database
        with open('data/ape_catalog_database.json', 'w') as f:
            json.dump(catalog, f, indent=2)
        
        logger.info(f"Applied {corrections} pump type corrections")
    else:
        logger.info("No corrections needed")
    
    return corrections

def validate_corrections():
    """Validate that corrections were applied correctly"""
    
    with open('data/ape_catalog_database.json', 'r') as f:
        catalog = json.load(f)
    
    pumps = catalog['pump_models']
    
    # Check ALE pumps
    ale_pumps = [p for p in pumps if 'ALE' in p['pump_code'].upper()]
    axial_ale = [p for p in ale_pumps if p['pump_type'] == 'AXIAL_FLOW']
    
    logger.info(f"ALE pumps: {len(ale_pumps)} total, {len(axial_ale)} classified as AXIAL_FLOW")
    
    # Check multi-stage pumps
    multistage_indicators = ['2P', '3P', '4P', '6P', '8P', '2F']
    potential_multistage = []
    actual_multistage = []
    
    for pump in pumps:
        pump_code = pump['pump_code'].upper()
        if any(stage in pump_code for stage in multistage_indicators):
            potential_multistage.append(pump)
            if pump['pump_type'] == 'MULTISTAGE':
                actual_multistage.append(pump)
    
    logger.info(f"Multi-stage pumps: {len(potential_multistage)} with indicators, {len(actual_multistage)} classified as MULTISTAGE")
    
    # Show examples
    logger.info("\nAXIAL_FLOW pumps after correction:")
    axial_pumps = [p for p in pumps if p['pump_type'] == 'AXIAL_FLOW']
    for pump in axial_pumps[:5]:
        specs = pump['specifications']
        logger.info(f"  {pump['pump_code']} - Flow: {specs['max_flow_m3hr']}m³/hr, Head: {specs['max_head_m']}m")
    
    logger.info(f"\nMULTISTAGE pumps after correction:")
    multistage_pumps = [p for p in pumps if p['pump_type'] == 'MULTISTAGE']
    for pump in multistage_pumps[:5]:
        specs = pump['specifications']
        logger.info(f"  {pump['pump_code']} - Flow: {specs['max_flow_m3hr']}m³/hr, Head: {specs['max_head_m']}m")

def main():
    """Main execution function"""
    logger.info("Starting comprehensive pump type classification fix...")
    
    corrections = fix_pump_type_classifications()
    validate_corrections()
    
    logger.info(f"Pump type classification fix completed: {corrections} corrections applied")

if __name__ == "__main__":
    main()