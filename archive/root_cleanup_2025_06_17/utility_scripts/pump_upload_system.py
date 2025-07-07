#!/usr/bin/env python3
"""
APE Pumps Data Upload System
Standalone system for uploading 300+ additional pump performance datasets
"""

import json
import csv
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PumpUploadSystem:
    """System for uploading and managing pump data"""
    
    def __init__(self, database_path='data/pumps_database.json'):
        self.database_path = database_path
        self.backup_path = database_path.replace('.json', '_backup.json')
    
    def load_database(self) -> Dict[str, Any]:
        """Load current pump database"""
        try:
            with open(self.database_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "metadata": {
                    "version": "2.0",
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "description": "APE Pumps database",
                    "pump_count": 0
                },
                "pumps": []
            }
    
    def save_database(self, database: Dict[str, Any]) -> bool:
        """Save database with backup"""
        try:
            # Create backup
            if os.path.exists(self.database_path):
                with open(self.database_path, 'r') as f:
                    backup_data = f.read()
                with open(self.backup_path, 'w') as f:
                    f.write(backup_data)
            
            # Save new database
            with open(self.database_path, 'w') as f:
                json.dump(database, f, indent=2)
            
            logger.info(f"Database saved successfully with {database['metadata']['pump_count']} pumps")
            return True
            
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            return False
    
    def process_csv_file(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """Process CSV file and return pump objects"""
        pumps = []
        
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Validate required fields
                    required_fields = ['pump_code', 'test_speed', 'flow_points', 'head_points', 'efficiency_points']
                    for field in required_fields:
                        if not row.get(field):
                            logger.warning(f"Row {row_num}: Missing required field '{field}'")
                            continue
                    
                    pump_obj = {
                        "objPump": {
                            "pPumpCode": row['pump_code'].strip('"'),
                            "pPumpTestSpeed": str(row['test_speed']),
                            "pFilter1": row.get('manufacturer', 'APE PUMPS').strip('"'),
                            "pSuppName": row.get('manufacturer', 'APE PUMPS').strip('"'),
                            "pM_FLOW": row['flow_points'].strip('"'),
                            "pM_HEAD": row['head_points'].strip('"'),
                            "pM_EFF": row['efficiency_points'].strip('"'),
                            "pM_POW": row.get('power_points', '').strip('"'),
                            "pM_NPSH": row.get('npsh_points', '').strip('"'),
                            "pVarD": "True",
                            "pVarN": "True",
                            "nPolyOrder": "3",
                            "pHeadCurvesNo": "1"
                        }
                    }
                    
                    # Validate data points consistency
                    flow_points = len(pump_obj["objPump"]["pM_FLOW"].split(';'))
                    head_points = len(pump_obj["objPump"]["pM_HEAD"].split(';'))
                    eff_points = len(pump_obj["objPump"]["pM_EFF"].split(';'))
                    
                    if flow_points != head_points or flow_points != eff_points:
                        logger.warning(f"Row {row_num}: Inconsistent data points for pump {pump_obj['objPump']['pPumpCode']}")
                        continue
                    
                    pumps.append(pump_obj)
                    logger.info(f"Processed pump: {pump_obj['objPump']['pPumpCode']}")
                    
                except Exception as e:
                    logger.error(f"Error processing row {row_num}: {e}")
                    continue
        
        logger.info(f"Successfully processed {len(pumps)} pumps from CSV")
        return pumps
    
    def add_pumps_to_database(self, new_pumps: List[Dict[str, Any]]) -> int:
        """Add new pumps to database, avoiding duplicates"""
        database = self.load_database()
        
        # Get existing pump codes
        existing_codes = set()
        for pump_entry in database['pumps']:
            if isinstance(pump_entry, dict) and 'objPump' in pump_entry:
                existing_codes.add(pump_entry['objPump'].get('pPumpCode'))
        
        # Add new pumps (skip duplicates)
        pumps_added = 0
        for pump in new_pumps:
            pump_code = pump['objPump'].get('pPumpCode')
            if pump_code not in existing_codes:
                database['pumps'].append(pump)
                existing_codes.add(pump_code)
                pumps_added += 1
            else:
                logger.info(f"Skipping duplicate pump: {pump_code}")
        
        # Update metadata
        database['metadata']['pump_count'] = len(database['pumps'])
        database['metadata']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
        
        # Save database
        if self.save_database(database):
            logger.info(f"Added {pumps_added} new pumps to database")
            return pumps_added
        else:
            logger.error("Failed to save database")
            return 0
    
    def validate_database(self) -> Dict[str, Any]:
        """Validate database integrity"""
        database = self.load_database()
        errors = []
        performance_curves = 0
        
        pump_codes = set()
        for pump_entry in database['pumps']:
            if isinstance(pump_entry, dict) and 'objPump' in pump_entry:
                pump = pump_entry['objPump']
                pump_code = pump.get('pPumpCode')
                
                # Check for duplicate pump codes
                if pump_code in pump_codes:
                    errors.append(f"Duplicate pump code: {pump_code}")
                else:
                    pump_codes.add(pump_code)
                
                # Validate performance data
                flow_data = pump.get('pM_FLOW', '')
                head_data = pump.get('pM_HEAD', '')
                eff_data = pump.get('pM_EFF', '')
                
                if flow_data and head_data and eff_data:
                    flow_points = len(flow_data.split(';'))
                    head_points = len(head_data.split(';'))
                    eff_points = len(eff_data.split(';'))
                    
                    if flow_points != head_points or flow_points != eff_points:
                        errors.append(f"Inconsistent data points for pump {pump_code}")
                    else:
                        performance_curves += 1
                else:
                    errors.append(f"Missing performance data for pump {pump_code}")
        
        return {
            'valid': len(errors) == 0,
            'pump_count': len(database['pumps']),
            'performance_curves': performance_curves,
            'errors': errors
        }
    
    def generate_csv_template(self, output_path='pump_template.csv'):
        """Generate CSV template for pump data entry"""
        template_data = [
            {
                'pump_code': '8 K 8 VANE',
                'test_speed': 1450,
                'manufacturer': 'APE PUMPS',
                'flow_points': '0;120;180;240;300;360',
                'head_points': '45.2;44.1;42.8;40.9;38.2;35.1',
                'efficiency_points': '0;65;75;81;84;79',
                'power_points': '0;85;95;105;115;125',
                'npsh_points': '2.1;2.3;2.8;3.2;3.8;4.5'
            },
            {
                'pump_code': '10 K 10 VANE',
                'test_speed': 1450,
                'manufacturer': 'APE PUMPS',
                'flow_points': '0;150;220;290;380;450',
                'head_points': '52.1;51.2;49.8;47.5;44.2;40.1',
                'efficiency_points': '0;68;78;83;85;81',
                'power_points': '0;105;118;132;148;165',
                'npsh_points': '2.3;2.5;3.0;3.5;4.1;4.8'
            }
        ]
        
        with open(output_path, 'w', newline='') as file:
            fieldnames = ['pump_code', 'test_speed', 'manufacturer', 'flow_points', 
                         'head_points', 'efficiency_points', 'power_points', 'npsh_points']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(template_data)
        
        logger.info(f"CSV template generated: {output_path}")
    
    def add_single_pump(self, pump_data: Dict[str, str]) -> bool:
        """Add a single pump to the database"""
        try:
            pump_obj = {
                "objPump": {
                    "pPumpCode": pump_data['pump_code'],
                    "pPumpTestSpeed": str(pump_data['test_speed']),
                    "pFilter1": "APE PUMPS",
                    "pSuppName": "APE PUMPS",
                    "pM_FLOW": pump_data['flow_data'],
                    "pM_HEAD": pump_data['head_data'],
                    "pM_EFF": pump_data['efficiency_data'],
                    "pM_POW": pump_data.get('power_data', ''),
                    "pM_NPSH": pump_data.get('npsh_data', ''),
                    "pVarD": "True",
                    "pVarN": "True",
                    "nPolyOrder": "3",
                    "pHeadCurvesNo": "1"
                }
            }
            
            pumps_added = self.add_pumps_to_database([pump_obj])
            return pumps_added > 0
            
        except Exception as e:
            logger.error(f"Error adding single pump: {e}")
            return False

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='APE Pumps Data Upload System')
    parser.add_argument('--upload-csv', help='Upload pumps from CSV file')
    parser.add_argument('--validate', action='store_true', help='Validate database integrity')
    parser.add_argument('--generate-template', help='Generate CSV template file')
    parser.add_argument('--status', action='store_true', help='Show database status')
    
    args = parser.parse_args()
    
    upload_system = PumpUploadSystem()
    
    if args.upload_csv:
        if os.path.exists(args.upload_csv):
            new_pumps = upload_system.process_csv_file(args.upload_csv)
            pumps_added = upload_system.add_pumps_to_database(new_pumps)
            print(f"Successfully added {pumps_added} pumps to database")
        else:
            print(f"Error: CSV file not found: {args.upload_csv}")
    
    elif args.validate:
        validation = upload_system.validate_database()
        print(f"Database validation: {'VALID' if validation['valid'] else 'INVALID'}")
        print(f"Total pumps: {validation['pump_count']}")
        print(f"Performance curves: {validation['performance_curves']}")
        if validation['errors']:
            print("Errors found:")
            for error in validation['errors']:
                print(f"  - {error}")
    
    elif args.generate_template:
        upload_system.generate_csv_template(args.generate_template)
        print(f"CSV template generated: {args.generate_template}")
    
    elif args.status:
        database = upload_system.load_database()
        print(f"Database status:")
        print(f"  Total pumps: {database['metadata']['pump_count']}")
        print(f"  Last updated: {database['metadata']['last_updated']}")
        print(f"  Progress to 300 pumps: {(database['metadata']['pump_count'] / 300) * 100:.1f}%")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()