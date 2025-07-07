#!/usr/bin/env python3
"""
Bulk Pump Uploader for APE Pumps Database
Processes all 386 pump files in categorized batches with comprehensive logging
"""

import json
import os
import glob
import logging
from datetime import datetime
from typing import Dict, List, Any
from pump_json_converter import convert_json_pump_data
from pump_upload_system import PumpUploadSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BulkPumpUploader:
    """Bulk uploader for pump database with categorized processing"""
    
    def __init__(self, data_folder='data/pump_data'):
        self.data_folder = data_folder
        self.upload_system = PumpUploadSystem()
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'total_pumps_added': 0,
            'categories_processed': 0,
            'start_time': None,
            'errors': []
        }
    
    def categorize_pump_files(self) -> Dict[str, List[str]]:
        """Categorize pump files by series/type"""
        files = glob.glob(os.path.join(self.data_folder, '*.txt'))
        categories = {}
        
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Extract category from filename
            if filename.startswith('8x10x13'):
                category = 'Multistage_8x10x13'
            elif filename.startswith('8312-'):
                category = 'Series_8312'
            elif filename.startswith('4503-') or filename.startswith('4504-') or filename.startswith('4505-') or filename.startswith('4506-'):
                category = 'Series_4500'
            elif 'wln' in filename.lower():
                category = 'WLN_Series'
            elif 'hc' in filename.lower() and not 'xhc' in filename.lower():
                category = 'HC_Series'
            elif 'xhc' in filename.lower():
                category = 'XHC_Series'
            elif filename.startswith('pj_'):
                category = 'PJ_Series'
            elif filename.startswith('pl_'):
                category = 'PL_Series'
            elif filename.startswith('vbk_'):
                category = 'VBK_Series'
            elif filename.startswith('wxh-'):
                category = 'WXH_Series'
            elif any(char.isdigit() for char in filename.split('_')[0]):
                # Numeric series (like 6_, 8_, 10_, etc.)
                prefix = filename.split('_')[0]
                category = f'Series_{prefix}'
            else:
                category = 'Miscellaneous'
            
            if category not in categories:
                categories[category] = []
            categories[category].append(file_path)
        
        return categories
    
    def process_category(self, category_name: str, file_paths: List[str]) -> Dict[str, Any]:
        """Process a single category of pump files"""
        logger.info(f"Processing category: {category_name} ({len(file_paths)} files)")
        
        category_stats = {
            'files_processed': 0,
            'files_failed': 0,
            'pumps_added': 0,
            'errors': []
        }
        
        converted_pumps = []
        
        for file_path in file_paths:
            try:
                filename = os.path.basename(file_path)
                logger.info(f"  Processing: {filename}")
                
                pumps = convert_json_pump_data(file_path)
                converted_pumps.extend(pumps)
                
                category_stats['files_processed'] += 1
                logger.info(f"    Converted: {len(pumps)} pump curves")
                
            except Exception as e:
                error_msg = f"Failed to process {filename}: {str(e)}"
                logger.error(f"    {error_msg}")
                category_stats['errors'].append(error_msg)
                category_stats['files_failed'] += 1
        
        # Upload converted pumps for this category
        if converted_pumps:
            try:
                pumps_added = self.upload_system.add_pumps_to_database(converted_pumps)
                category_stats['pumps_added'] = pumps_added
                logger.info(f"  Uploaded: {pumps_added} pumps from {category_name}")
            except Exception as e:
                error_msg = f"Failed to upload category {category_name}: {str(e)}"
                logger.error(error_msg)
                category_stats['errors'].append(error_msg)
        
        return category_stats
    
    def run_bulk_upload(self) -> Dict[str, Any]:
        """Run the complete bulk upload process"""
        self.stats['start_time'] = datetime.now()
        logger.info("Starting bulk pump upload process")
        
        # Get current database state
        initial_validation = self.upload_system.validate_database()
        initial_pump_count = initial_validation['pump_count']
        logger.info(f"Initial database state: {initial_pump_count} pumps")
        
        # Categorize files
        categories = self.categorize_pump_files()
        self.stats['total_files'] = sum(len(files) for files in categories.values())
        
        logger.info(f"Found {len(categories)} categories with {self.stats['total_files']} total files")
        
        # Process each category
        for category_name, file_paths in categories.items():
            category_stats = self.process_category(category_name, file_paths)
            
            # Update overall stats
            self.stats['processed_files'] += category_stats['files_processed']
            self.stats['failed_files'] += category_stats['files_failed']
            self.stats['total_pumps_added'] += category_stats['pumps_added']
            self.stats['categories_processed'] += 1
            self.stats['errors'].extend(category_stats['errors'])
            
            logger.info(f"Category {category_name} complete: {category_stats['pumps_added']} pumps added")
        
        # Final validation
        final_validation = self.upload_system.validate_database()
        final_pump_count = final_validation['pump_count']
        
        # Complete stats
        self.stats['end_time'] = datetime.now()
        self.stats['duration'] = self.stats['end_time'] - self.stats['start_time']
        self.stats['initial_pump_count'] = initial_pump_count
        self.stats['final_pump_count'] = final_pump_count
        self.stats['net_pumps_added'] = final_pump_count - initial_pump_count
        
        return self.stats
    
    def generate_report(self) -> str:
        """Generate comprehensive upload report"""
        report = [
            "=== APE Pumps Bulk Upload Report ===",
            f"Upload completed: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {self.stats['duration']}",
            "",
            "Summary:",
            f"  Files processed: {self.stats['processed_files']}/{self.stats['total_files']}",
            f"  Files failed: {self.stats['failed_files']}",
            f"  Categories processed: {self.stats['categories_processed']}",
            f"  Initial pump count: {self.stats['initial_pump_count']}",
            f"  Final pump count: {self.stats['final_pump_count']}",
            f"  Net pumps added: {self.stats['net_pumps_added']}",
            ""
        ]
        
        if self.stats['errors']:
            report.extend([
                "Errors encountered:",
                *[f"  - {error}" for error in self.stats['errors']],
                ""
            ])
        
        report.extend([
            "Database validation:",
            f"  Status: {'PASSED' if self.upload_system.validate_database()['valid'] else 'FAILED'}",
            f"  Total pumps: {self.upload_system.validate_database()['pump_count']}",
            f"  Performance curves: {self.upload_system.validate_database()['performance_curves']}"
        ])
        
        return '\n'.join(report)

def main():
    """Main execution function"""
    uploader = BulkPumpUploader()
    
    try:
        stats = uploader.run_bulk_upload()
        report = uploader.generate_report()
        
        # Save report
        with open('bulk_upload_report.txt', 'w') as f:
            f.write(report)
        
        print(report)
        
        return stats
        
    except Exception as e:
        logger.error(f"Bulk upload failed: {e}")
        raise

if __name__ == "__main__":
    main()