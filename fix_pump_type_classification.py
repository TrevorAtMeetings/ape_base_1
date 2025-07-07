#!/usr/bin/env python3
"""
Fix Pump Type Classification
Corrects misclassified pump types in the APE catalog database
"""

import json
import os
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_correct_pump_type(source_data: Dict[str, Any]) -> str:
    """
    Determine correct pump type using authentic source data classification
    Based on APE's original filter system
    """
    filter3 = source_data.get('objPump.pFilter3', '').upper()
    filter4 = source_data.get('objPump.pFilter4', '').upper()
    filter7 = source_data.get('objPump.pFilter7', '').upper()
    pump_code = source_data.get('objPump.pPumpCode', '').upper()
    
    # Priority-based classification using APE's authentic filter system
    
    # 1. HSC (Horizontal Split Case) - Filter3 = "HSC"
    if filter3 == 'HSC':
        return 'HSC'
    
    # 2. Vertical Turbine Pumps - VTP series
    if 'VTP' in filter4 or 'VTP' in pump_code:
        return 'VTP'
    
    # 3. Axial Flow - ALE/BLE series
    if 'ALE' in filter4 or 'BLE' in filter4:
        return 'AXIAL_FLOW'
    
    # 4. Multistage - indicated by stages in pump code
    if any(stage in pump_code for stage in ['2P', '3P', '4P', '6P', '8P', '2 STAGE', '3 STAGE']):
        return 'MULTISTAGE'
    
    # 5. High Speed Centrifugal - specific models
    if 'HIGH_SPEED' in filter3 or pump_code.endswith(' HSC'):
        return 'HIGH_SPEED_CENTRIFUGAL'
    
    # 6. Default to End Suction for standard centrifugal pumps
    return 'END_SUCTION'

def load_source_data(pump_code: str) -> Dict[str, Any]:
    """Load original source data for a pump"""
    # Convert pump code to filename format
    filename = pump_code.lower().replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '') + '.txt'
    filepath = os.path.join('data/pump_data', filename)
    
    if not os.path.exists(filepath):
        # Try alternative filename patterns
        alt_filename = pump_code.lower().replace('/', '_').replace(' ', '_').replace('-', '_') + '.txt'
        alt_filepath = os.path.join('data/pump_data', alt_filename)
        if os.path.exists(alt_filepath):
            filepath = alt_filepath
        else:
            return {}
    
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
            
            # Handle malformed JSON - remove trailing comma before closing brace
            if content.endswith(',\n}') or content.endswith(',}'):
                content = content.replace(',\n}', '\n}').replace(',}', '}')
            
            if content.startswith('{') and content.endswith('}'):
                return json.loads(content)
                
    except json.JSONDecodeError as e:
        # Try to extract filter data using regex if JSON parsing fails
        try:
            import re
            filter3_match = re.search(r'"objPump\.pFilter3":"([^"]*)"', content)
            filter4_match = re.search(r'"objPump\.pFilter4":"([^"]*)"', content)
            filter7_match = re.search(r'"objPump\.pFilter7":"([^"]*)"', content)
            pump_code_match = re.search(r'"objPump\.pPumpCode":"([^"]*)"', content)
            
            if filter3_match or filter4_match:
                return {
                    'objPump.pFilter3': filter3_match.group(1) if filter3_match else '',
                    'objPump.pFilter4': filter4_match.group(1) if filter4_match else '',
                    'objPump.pFilter7': filter7_match.group(1) if filter7_match else '',
                    'objPump.pPumpCode': pump_code_match.group(1) if pump_code_match else pump_code
                }
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"Error loading source data for {pump_code}: {e}")
    
    return {}

def fix_pump_type_classifications():
    """Fix pump type classifications in the catalog database"""
    
    # Load current catalog
    with open('data/ape_catalog_database.json', 'r') as f:
        catalog_data = json.load(f)
    
    pump_models = catalog_data.get('pump_models', [])
    
    corrections_made = 0
    hsc_pumps_found = 0
    
    logger.info(f"Analyzing {len(pump_models)} pump models for type classification errors...")
    
    for pump_model in pump_models:
        pump_code = pump_model.get('pump_code', '')
        current_type = pump_model.get('pump_type', '')
        
        # Load source data to determine correct type
        source_data = load_source_data(pump_code)
        
        if source_data:
            correct_type = determine_correct_pump_type(source_data)
            
            if correct_type != current_type:
                logger.info(f"Correcting {pump_code}: {current_type} -> {correct_type}")
                pump_model['pump_type'] = correct_type
                corrections_made += 1
                
                if correct_type == 'HSC':
                    hsc_pumps_found += 1
    
    # Update metadata
    catalog_data['metadata']['last_updated'] = "2025-06-17 09:00:00"
    catalog_data['metadata']['pump_type_corrections'] = corrections_made
    
    # Save corrected catalog
    backup_path = 'data/ape_catalog_database_before_type_fix.json'
    with open(backup_path, 'w') as f:
        json.dump(catalog_data, f, indent=2)
    logger.info(f"Backup saved to {backup_path}")
    
    with open('data/ape_catalog_database.json', 'w') as f:
        json.dump(catalog_data, f, indent=2)
    
    logger.info(f"Pump type classification fix complete:")
    logger.info(f"  - Total corrections made: {corrections_made}")
    logger.info(f"  - HSC pumps now correctly classified: {hsc_pumps_found}")
    
    # Generate summary report
    type_counts = {}
    for pump_model in pump_models:
        pump_type = pump_model.get('pump_type', 'UNKNOWN')
        type_counts[pump_type] = type_counts.get(pump_type, 0) + 1
    
    logger.info("Updated pump type distribution:")
    for pump_type, count in sorted(type_counts.items()):
        logger.info(f"  {pump_type}: {count} pumps")
    
    return corrections_made, hsc_pumps_found

if __name__ == "__main__":
    corrections, hsc_count = fix_pump_type_classifications()
    print(f"Completed pump type classification fix: {corrections} corrections, {hsc_count} HSC pumps found")