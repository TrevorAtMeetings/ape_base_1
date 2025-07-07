#!/usr/bin/env python3
"""
Authentic Pump Type Correction
Corrects pump types based on authentic APE source data, not assumptions
"""

import json
import os
import re
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_source_data(pump_code: str) -> Optional[Dict[str, Any]]:
    """Load original source data for a pump"""
    source_dir = "data/pump_data"
    
    # Find source file
    for filename in os.listdir(source_dir):
        if filename.endswith('.txt') and pump_code.replace('/', '_').replace(' ', '_') in filename:
            filepath = os.path.join(source_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                return parse_source_file(content)
            except Exception as e:
                logger.debug(f"Error reading {filename}: {e}")
                continue
    return None

def parse_source_file(content: str) -> Dict[str, Any]:
    """Parse source data file with error handling"""
    data = {}
    
    # Extract key pump data using regex patterns
    patterns = {
        'objPump.pPumpCode': r'objPump\.pPumpCode\s*=\s*"([^"]*)"',
        'objPump.pFilter3': r'objPump\.pFilter3\s*=\s*"([^"]*)"',
        'objPump.pFilter4': r'objPump\.pFilter4\s*=\s*"([^"]*)"',
        'objPump.pFilter7': r'objPump\.pFilter7\s*=\s*"([^"]*)"',
        'objPump.pSuppName': r'objPump\.pSuppName\s*=\s*"([^"]*)"'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
    
    return data

def determine_correct_pump_type_from_source(source_data: Dict[str, Any]) -> str:
    """Determine correct pump type using authentic APE source data"""
    filter3 = source_data.get('objPump.pFilter3', '').upper()
    filter4 = source_data.get('objPump.pFilter4', '').upper()
    pump_code = source_data.get('objPump.pPumpCode', '').upper()
    
    # Follow APE's authentic classification system from source data
    
    # HSC - Horizontal Split Case (Priority 1)
    if filter3 == 'HSC':
        return 'HSC'
    
    # VTP - Vertical Turbine Pumps (Priority 2)  
    if 'VTP' in filter4 or filter3 == 'VTP':
        return 'VTP'
    
    # Axial Flow - ALE series (Priority 3)
    if 'ALE' in filter4 or 'ALE' in pump_code:
        return 'AXIAL_FLOW'
    
    # Check for authentic multistage indicators in source data
    # Only classify as MULTISTAGE if source data explicitly indicates it
    if any(indicator in filter4 for indicator in ['2P', '3P', '4P', '6P', '8P']) or \
       any(indicator in pump_code for indicator in ['2P', '3P', '4P', '6P', '8P']):
        # But respect source classification - if source says VTP, keep it as VTP
        if filter3 == 'VTP' or 'VTP' in filter4:
            return 'VTP'
        return 'MULTISTAGE'
    
    # 2F pumps - check source classification
    if '2F' in pump_code:
        # If source explicitly classifies as END_SUCTION, respect that
        if filter3 == 'CENTRIFUGAL' or filter3 == 'END SUCTION':
            return 'END_SUCTION'
        return 'MULTISTAGE'
    
    # Default to END_SUCTION for standard centrifugal
    return 'END_SUCTION'

def correct_pump_types_authentically():
    """Correct pump types based on authentic source data"""
    
    # Load current database
    with open('data/ape_catalog_database.json', 'r') as f:
        catalog = json.load(f)
    
    pumps = catalog['pump_models']
    corrections = 0
    ale_corrections = 0
    source_based_corrections = 0
    
    logger.info(f"Correcting pump types based on authentic source data...")
    
    for pump in pumps:
        pump_code = pump.get('pump_code', '')
        current_type = pump.get('pump_type', '')
        
        # Load source data for this pump
        source_data = load_source_data(pump_code)
        
        if source_data:
            # Determine correct type from authentic source
            correct_type = determine_correct_pump_type_from_source(source_data)
            
            if current_type != correct_type:
                logger.info(f"Source-based correction: {pump_code}: {current_type} → {correct_type}")
                pump['pump_type'] = correct_type
                corrections += 1
                source_based_corrections += 1
        else:
            # Handle special cases where source data is missing
            # Only correct obvious ALE pumps to AXIAL_FLOW
            if 'ALE' in pump_code.upper() and current_type != 'AXIAL_FLOW':
                logger.info(f"ALE correction: {pump_code}: {current_type} → AXIAL_FLOW")
                pump['pump_type'] = 'AXIAL_FLOW'
                corrections += 1
                ale_corrections += 1
    
    # Update metadata
    if corrections > 0:
        catalog['metadata']['authentic_corrections'] = corrections
        catalog['metadata']['source_based_corrections'] = source_based_corrections
        catalog['metadata']['ale_corrections'] = ale_corrections
        catalog['metadata']['last_updated'] = "2025-06-17 09:45:00"
        
        # Save corrected database
        with open('data/ape_catalog_database.json', 'w') as f:
            json.dump(catalog, f, indent=2)
        
        logger.info(f"Applied {corrections} authentic corrections")
        logger.info(f"  Source-based: {source_based_corrections}")
        logger.info(f"  ALE pumps: {ale_corrections}")
    else:
        logger.info("No authentic corrections needed")
    
    return corrections

def validate_pump_type_distribution():
    """Validate the distribution of pump types after correction"""
    
    with open('data/ape_catalog_database.json', 'r') as f:
        catalog = json.load(f)
    
    pumps = catalog['pump_models']
    type_counts = {}
    
    for pump in pumps:
        pump_type = pump.get('pump_type', 'Unknown')
        type_counts[pump_type] = type_counts.get(pump_type, 0) + 1
    
    logger.info("Pump type distribution after authentic correction:")
    for pump_type, count in sorted(type_counts.items()):
        logger.info(f"  {pump_type}: {count} pumps")
    
    # Show specific examples
    axial_pumps = [p for p in pumps if p['pump_type'] == 'AXIAL_FLOW']
    multistage_pumps = [p for p in pumps if p['pump_type'] == 'MULTISTAGE']
    
    logger.info(f"\nAXIAL_FLOW pumps ({len(axial_pumps)}):")
    for pump in axial_pumps:
        specs = pump['specifications']
        logger.info(f"  {pump['pump_code']} - Flow: {specs['max_flow_m3hr']}m³/hr, Head: {specs['max_head_m']}m")
    
    logger.info(f"\nMULTISTAGE pumps (first 10 of {len(multistage_pumps)}):")
    for pump in multistage_pumps[:10]:
        specs = pump['specifications']
        logger.info(f"  {pump['pump_code']} - Flow: {specs['max_flow_m3hr']}m³/hr, Head: {specs['max_head_m']}m")

def main():
    """Main execution function"""
    logger.info("Starting authentic pump type correction based on source data...")
    
    corrections = correct_pump_types_authentically()
    validate_pump_type_distribution()
    
    logger.info(f"Authentic pump type correction completed: {corrections} corrections applied")

if __name__ == "__main__":
    main()