#!/usr/bin/env python3
"""
Comprehensive Pump Validation Fix
Resolves all database validation issues using authentic APE source data
"""

import json
import os
import re
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PumpValidationFixer:
    def __init__(self):
        self.source_dir = "data/pump_data"
        self.catalog_path = "data/ape_catalog_database.json"
        
    def load_validation_report(self) -> Dict[str, Any]:
        """Load the current validation report"""
        with open('database_validation_report.json', 'r') as f:
            return json.load(f)
    
    def find_source_file(self, pump_code: str) -> Optional[str]:
        """Find source file for a pump with fuzzy matching"""
        if not os.path.exists(self.source_dir):
            return None
            
        # Clean pump code for matching
        clean_code = pump_code.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')
        
        for filename in os.listdir(self.source_dir):
            if filename.endswith('.txt'):
                # Try exact match first
                if clean_code.lower() in filename.lower():
                    return os.path.join(self.source_dir, filename)
                
                # Try partial matches
                code_parts = pump_code.split()
                if len(code_parts) > 1 and all(part.lower() in filename.lower() for part in code_parts[:2]):
                    return os.path.join(self.source_dir, filename)
        
        return None
    
    def parse_source_file(self, filepath: str) -> Dict[str, Any]:
        """Parse source data file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            data = {}
            patterns = {
                'objPump.pPumpCode': r'objPump\.pPumpCode\s*=\s*"([^"]*)"',
                'objPump.pFilter3': r'objPump\.pFilter3\s*=\s*"([^"]*)"',
                'objPump.pFilter4': r'objPump\.pFilter4\s*=\s*"([^"]*)"',
                'objPump.pFilter7': r'objPump\.pFilter7\s*=\s*"([^"]*)"',
                'objPump.pSuppName': r'objPump\.pSuppName\s*=\s*"([^"]*)"',
                'objPump.pBEPFlow': r'objPump\.pBEPFlow\s*=\s*([0-9.]+)',
                'objPump.pBEPHead': r'objPump\.pBEPHead\s*=\s*([0-9.]+)',
                'objPump.pMaxFlow': r'objPump\.pMaxFlow\s*=\s*([0-9.]+)',
                'objPump.pMaxHead': r'objPump\.pMaxHead\s*=\s*([0-9.]+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if key in ['objPump.pBEPFlow', 'objPump.pBEPHead', 'objPump.pMaxFlow', 'objPump.pMaxHead']:
                        try:
                            data[key] = float(value)
                        except:
                            data[key] = value
                    else:
                        data[key] = value
            
            return data
            
        except Exception as e:
            logger.debug(f"Error parsing {filepath}: {e}")
            return {}
    
    def determine_authentic_pump_type(self, source_data: Dict[str, Any], pump_code: str) -> str:
        """Determine pump type using authentic APE classification logic"""
        if not source_data:
            # Fallback logic for pumps without source files
            return self.fallback_pump_type_classification(pump_code)
        
        filter3 = source_data.get('objPump.pFilter3', '').upper()
        filter4 = source_data.get('objPump.pFilter4', '').upper()
        filter7 = source_data.get('objPump.pFilter7', '').upper()
        pump_code_upper = pump_code.upper()
        
        # APE's authentic classification hierarchy
        
        # 1. HSC - Horizontal Split Case (highest priority)
        if filter3 == 'HSC':
            return 'HSC'
        
        # 2. VTP - Vertical Turbine Pumps
        if filter3 == 'VTP' or 'VTP' in filter4:
            return 'VTP'
        
        # 3. Axial Flow - ALE series
        if 'ALE' in filter4 or 'ALE' in pump_code_upper:
            return 'AXIAL_FLOW'
        
        # 4. Check for multistage indicators but respect source classification
        if any(indicator in pump_code_upper for indicator in ['2P', '3P', '4P', '6P', '8P']):
            # If source says VTP, keep as VTP even with stage indicators
            if filter3 == 'VTP':
                return 'VTP'
            return 'MULTISTAGE'
        
        # 5. 2F pumps - check source filter3 for guidance
        if '2F' in pump_code_upper:
            if filter3 in ['CENTRIFUGAL', 'END SUCTION', '']:
                return 'END_SUCTION'
            return 'MULTISTAGE'
        
        # 6. Double suction
        if 'DOUBLE' in filter7 or 'DS' in pump_code_upper:
            return 'DOUBLE_SUCTION'
        
        # 7. Default to END_SUCTION
        return 'END_SUCTION'
    
    def fallback_pump_type_classification(self, pump_code: str) -> str:
        """Fallback classification for pumps without source files"""
        pump_code_upper = pump_code.upper()
        
        # Clear ALE pumps
        if 'ALE' in pump_code_upper:
            return 'AXIAL_FLOW'
        
        # Clear HSC indicators
        if 'HSC' in pump_code_upper or 'GME' in pump_code_upper:
            return 'HSC'
        
        # Stage indicators
        if any(indicator in pump_code_upper for indicator in ['2P', '3P', '4P', '6P', '8P']):
            return 'MULTISTAGE'
        
        # VTP indicators
        if 'VTP' in pump_code_upper or any(x in pump_code_upper for x in ['WO', 'HC', 'XHC', 'MC', 'LC']):
            return 'VTP'
        
        return 'END_SUCTION'
    
    def fix_pump_type_issues(self) -> int:
        """Fix pump type classification issues"""
        # Load database
        with open(self.catalog_path, 'r') as f:
            catalog = json.load(f)
        
        pumps = catalog['pump_models']
        corrections = 0
        
        # Load validation issues
        validation_report = self.load_validation_report()
        pump_type_issues = [issue for issue in validation_report.get('issues_by_type', {}).get('PUMP_TYPE_MISMATCH', [])]
        
        logger.info(f"Fixing {len(pump_type_issues)} pump type mismatches...")
        
        for issue in pump_type_issues:
            pump_code = issue['pump_code']
            expected_type = issue['expected']
            
            # Find pump in database
            pump = next((p for p in pumps if p['pump_code'] == pump_code), None)
            if not pump:
                continue
            
            # Load source data to verify
            source_file = self.find_source_file(pump_code)
            if source_file:
                source_data = self.parse_source_file(source_file)
                authentic_type = self.determine_authentic_pump_type(source_data, pump_code)
            else:
                authentic_type = self.fallback_pump_type_classification(pump_code)
            
            # Apply correction if needed
            current_type = pump['pump_type']
            if current_type != authentic_type:
                logger.info(f"Correcting {pump_code}: {current_type} → {authentic_type}")
                pump['pump_type'] = authentic_type
                corrections += 1
        
        # Save corrected database
        if corrections > 0:
            catalog['metadata']['validation_fixes'] = corrections
            catalog['metadata']['last_updated'] = "2025-06-17 09:50:00"
            
            with open(self.catalog_path, 'w') as f:
                json.dump(catalog, f, indent=2)
        
        return corrections
    
    def fix_missing_specifications(self) -> int:
        """Fix missing pump specifications using source data"""
        with open(self.catalog_path, 'r') as f:
            catalog = json.load(f)
        
        pumps = catalog['pump_models']
        spec_fixes = 0
        
        for pump in pumps:
            pump_code = pump['pump_code']
            source_file = self.find_source_file(pump_code)
            
            if source_file:
                source_data = self.parse_source_file(source_file)
                specs = pump.get('specifications', {})
                
                # Fix missing flow/head data
                if 'objPump.pMaxFlow' in source_data and specs.get('max_flow_m3hr', 0) == 0:
                    specs['max_flow_m3hr'] = source_data['objPump.pMaxFlow']
                    spec_fixes += 1
                
                if 'objPump.pMaxHead' in source_data and specs.get('max_head_m', 0) == 0:
                    specs['max_head_m'] = source_data['objPump.pMaxHead']
                    spec_fixes += 1
        
        if spec_fixes > 0:
            with open(self.catalog_path, 'w') as f:
                json.dump(catalog, f, indent=2)
        
        return spec_fixes
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation summary"""
        with open(self.catalog_path, 'r') as f:
            catalog = json.load(f)
        
        pumps = catalog['pump_models']
        
        # Count pump types
        type_counts = {}
        for pump in pumps:
            pump_type = pump.get('pump_type', 'Unknown')
            type_counts[pump_type] = type_counts.get(pump_type, 0) + 1
        
        # Find pumps suitable for test cases
        multistage_suitable = []
        axial_suitable = []
        
        for pump in pumps:
            specs = pump['specifications']
            if pump['pump_type'] == 'MULTISTAGE' and specs['max_flow_m3hr'] >= 1250 and specs['max_head_m'] >= 350:
                multistage_suitable.append(pump)
            elif pump['pump_type'] == 'AXIAL_FLOW' and specs['max_flow_m3hr'] >= 500 and specs['max_head_m'] >= 50:
                axial_suitable.append(pump)
        
        return {
            'total_pumps': len(pumps),
            'type_distribution': type_counts,
            'multistage_for_1250_350': len(multistage_suitable),
            'axial_for_500_50': len(axial_suitable),
            'multistage_examples': [p['pump_code'] for p in multistage_suitable[:3]],
            'axial_examples': [p['pump_code'] for p in axial_suitable[:3]]
        }

def main():
    """Execute comprehensive pump validation fix"""
    logger.info("Starting comprehensive pump validation fix...")
    
    fixer = PumpValidationFixer()
    
    # Fix pump type issues
    type_corrections = fixer.fix_pump_type_issues()
    logger.info(f"Applied {type_corrections} pump type corrections")
    
    # Fix missing specifications
    spec_fixes = fixer.fix_missing_specifications()
    logger.info(f"Fixed {spec_fixes} missing specifications")
    
    # Generate summary
    summary = fixer.generate_summary_report()
    
    logger.info("=== VALIDATION FIX SUMMARY ===")
    logger.info(f"Total pumps: {summary['total_pumps']}")
    logger.info("Pump type distribution:")
    for pump_type, count in sorted(summary['type_distribution'].items()):
        logger.info(f"  {pump_type}: {count}")
    
    logger.info(f"\nMulti-stage pumps suitable for Flow:1250, Head:350: {summary['multistage_for_1250_350']}")
    if summary['multistage_examples']:
        logger.info(f"Examples: {', '.join(summary['multistage_examples'])}")
    
    logger.info(f"\nAxial flow pumps suitable for Flow:500, Head:50: {summary['axial_for_500_50']}")
    if summary['axial_examples']:
        logger.info(f"Examples: {', '.join(summary['axial_examples'])}")
    
    # Save summary report
    with open('pump_validation_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("\nValidation fix complete. Summary saved to pump_validation_summary.json")

if __name__ == "__main__":
    main()