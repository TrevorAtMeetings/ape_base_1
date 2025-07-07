"""
Batch SCG Processor for APE Pumps Selection Application
Processes multiple SCG files concurrently with progress tracking and error reporting
"""

import os
import json
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dataclasses import dataclass, field

from scg_processor import SCGProcessor, ProcessingResult
from scg_catalog_adapter import SCGCatalogAdapter, AdapterResult, CatalogEngineIntegrator

logger = logging.getLogger(__name__)

@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    max_workers: int = 4
    timeout_per_file: int = 60
    update_existing: bool = False
    validate_data: bool = True
    generate_report: bool = True
    output_directory: str = "batch_output"

@dataclass
class BatchResult:
    """Result of batch processing operation"""
    batch_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_files: int = 0
    processed_files: int = 0
    successful_pumps: int = 0
    failed_files: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    file_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    processing_time: float = 0.0
    report_path: Optional[str] = None

class BatchProgressTracker:
    """Tracks progress of batch processing operations"""
    
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0
        self.current_file = ""
        self.progress_callbacks: List[Callable] = []
        self._lock = threading.Lock()
    
    def add_progress_callback(self, callback: Callable):
        """Add callback function for progress updates"""
        self.progress_callbacks.append(callback)
    
    def update_progress(self, file_name: str, success: bool):
        """Update processing progress"""
        with self._lock:
            self.processed_files += 1
            if success:
                self.successful_files += 1
            else:
                self.failed_files += 1
            self.current_file = file_name
            
            # Notify callbacks
            progress_data = {
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'successful_files': self.successful_files,
                'failed_files': self.failed_files,
                'current_file': file_name,
                'progress_percent': (self.processed_files / self.total_files) * 100
            }
            
            for callback in self.progress_callbacks:
                try:
                    callback(progress_data)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress status"""
        with self._lock:
            return {
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'successful_files': self.successful_files,
                'failed_files': self.failed_files,
                'current_file': self.current_file,
                'progress_percent': (self.processed_files / self.total_files) * 100 if self.total_files > 0 else 0
            }

class BatchSCGProcessor:
    """Batch processor for multiple SCG files with concurrent processing"""
    
    def __init__(self, config: Optional[BatchProcessingConfig] = None):
        self.config = config or BatchProcessingConfig()
        self.scg_processor = SCGProcessor()
        self.catalog_adapter = SCGCatalogAdapter()
        self.catalog_integrator = CatalogEngineIntegrator()
        self.active_batches: Dict[str, BatchResult] = {}
        self._batch_counter = 0
    
    def process_files(self, file_paths: List[str], progress_callback: Optional[Callable] = None) -> BatchResult:
        """
        Process multiple SCG files concurrently
        
        Args:
            file_paths: List of SCG file paths to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            BatchResult with processing details
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._batch_counter}"
        self._batch_counter += 1
        
        batch_result = BatchResult(
            batch_id=batch_id,
            start_time=datetime.now(),
            total_files=len(file_paths)
        )
        
        self.active_batches[batch_id] = batch_result
        
        # Setup progress tracking
        progress_tracker = BatchProgressTracker(len(file_paths))
        if progress_callback:
            progress_tracker.add_progress_callback(progress_callback)
        
        logger.info(f"Starting batch processing {batch_id} with {len(file_paths)} files")
        
        try:
            # Process files concurrently
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_file = {
                    executor.submit(self._process_single_file, file_path, batch_id): file_path
                    for file_path in file_paths
                }
                
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    file_name = os.path.basename(file_path)
                    
                    try:
                        file_result = future.result(timeout=self.config.timeout_per_file)
                        batch_result.file_results[file_name] = file_result
                        
                        if file_result['success']:
                            batch_result.successful_pumps += 1
                            progress_tracker.update_progress(file_name, True)
                        else:
                            batch_result.failed_files += 1
                            batch_result.errors.extend(file_result.get('errors', []))
                            progress_tracker.update_progress(file_name, False)
                            
                    except Exception as e:
                        error_msg = f"Error processing {file_name}: {str(e)}"
                        batch_result.errors.append(error_msg)
                        batch_result.failed_files += 1
                        batch_result.file_results[file_name] = {
                            'success': False,
                            'errors': [error_msg]
                        }
                        progress_tracker.update_progress(file_name, False)
                        logger.error(error_msg, exc_info=True)
        
        except Exception as e:
            batch_result.errors.append(f"Batch processing failed: {str(e)}")
            logger.error(f"Batch processing error: {e}", exc_info=True)
        
        finally:
            batch_result.end_time = datetime.now()
            batch_result.processing_time = (batch_result.end_time - batch_result.start_time).total_seconds()
            batch_result.processed_files = len(batch_result.file_results)
            
            # Generate report if requested
            if self.config.generate_report:
                batch_result.report_path = self._generate_batch_report(batch_result)
            
            logger.info(f"Batch processing {batch_id} completed: {batch_result.successful_pumps}/{batch_result.total_files} successful")
        
        return batch_result
    
    def _process_single_file(self, file_path: str, batch_id: str) -> Dict[str, Any]:
        """Process single SCG file with full pipeline"""
        file_result = {
            'file_path': file_path,
            'success': False,
            'pump_code': '',
            'errors': [],
            'warnings': [],
            'processing_steps': {}
        }
        
        try:
            # Step 1: Process SCG file
            scg_result = self.scg_processor.process_scg_file(file_path)
            file_result['processing_steps']['scg_processing'] = {
                'success': scg_result.success,
                'processing_time': scg_result.processing_time,
                'errors': scg_result.errors,
                'warnings': scg_result.warnings
            }
            
            if not scg_result.success:
                file_result['errors'].extend(scg_result.errors)
                return file_result
            
            file_result['warnings'].extend(scg_result.warnings)
            pump_code = scg_result.pump_data.get('pump_info', {}).get('pPumpCode', 'unknown')
            file_result['pump_code'] = pump_code
            
            # Step 2: Convert to catalog format
            adapter_result = self.catalog_adapter.map_scg_to_catalog(scg_result.pump_data)
            file_result['processing_steps']['catalog_conversion'] = {
                'success': adapter_result.success,
                'errors': adapter_result.errors,
                'warnings': adapter_result.warnings
            }
            
            if not adapter_result.success:
                file_result['errors'].extend(adapter_result.errors)
                return file_result
            
            file_result['warnings'].extend(adapter_result.warnings)
            
            # Step 3: Integrate with catalog engine
            integration_result = self.catalog_integrator.integrate_pump_data(
                adapter_result.catalog_data,
                update_existing=self.config.update_existing
            )
            file_result['processing_steps']['catalog_integration'] = integration_result
            
            if integration_result['success']:
                file_result['success'] = True
                file_result['action'] = integration_result['action']
                file_result['message'] = integration_result['message']
            else:
                file_result['errors'].extend(integration_result.get('errors', []))
            
        except Exception as e:
            file_result['errors'].append(f"Unexpected error: {str(e)}")
            logger.error(f"Error in single file processing {file_path}: {e}", exc_info=True)
        
        return file_result
    
    def _generate_batch_report(self, batch_result: BatchResult) -> str:
        """Generate comprehensive batch processing report"""
        try:
            # Create output directory
            os.makedirs(self.config.output_directory, exist_ok=True)
            
            report_filename = f"batch_report_{batch_result.batch_id}.json"
            report_path = os.path.join(self.config.output_directory, report_filename)
            
            # Prepare report data
            report_data = {
                'batch_summary': {
                    'batch_id': batch_result.batch_id,
                    'start_time': batch_result.start_time.isoformat(),
                    'end_time': batch_result.end_time.isoformat() if batch_result.end_time else None,
                    'processing_time_seconds': batch_result.processing_time,
                    'total_files': batch_result.total_files,
                    'processed_files': batch_result.processed_files,
                    'successful_pumps': batch_result.successful_pumps,
                    'failed_files': batch_result.failed_files,
                    'success_rate': (batch_result.successful_pumps / batch_result.total_files) * 100 if batch_result.total_files > 0 else 0
                },
                'overall_errors': batch_result.errors,
                'overall_warnings': batch_result.warnings,
                'file_results': batch_result.file_results,
                'processing_statistics': {
                    'scg_processor_stats': self.scg_processor.get_processing_stats(),
                    'catalog_adapter_stats': self.catalog_adapter.get_conversion_stats(),
                    'catalog_integrator_stats': self.catalog_integrator.get_integration_stats()
                },
                'configuration': {
                    'max_workers': self.config.max_workers,
                    'timeout_per_file': self.config.timeout_per_file,
                    'update_existing': self.config.update_existing,
                    'validate_data': self.config.validate_data
                }
            }
            
            # Write report
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Batch report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating batch report: {e}")
            return None
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific batch"""
        batch_result = self.active_batches.get(batch_id)
        if not batch_result:
            return None
        
        return {
            'batch_id': batch_id,
            'start_time': batch_result.start_time.isoformat(),
            'end_time': batch_result.end_time.isoformat() if batch_result.end_time else None,
            'total_files': batch_result.total_files,
            'processed_files': batch_result.processed_files,
            'successful_pumps': batch_result.successful_pumps,
            'failed_files': batch_result.failed_files,
            'is_complete': batch_result.end_time is not None,
            'processing_time': batch_result.processing_time,
            'errors_count': len(batch_result.errors),
            'warnings_count': len(batch_result.warnings)
        }
    
    def list_active_batches(self) -> List[str]:
        """List all active batch IDs"""
        return list(self.active_batches.keys())
    
    def cleanup_completed_batches(self, max_age_hours: int = 24):
        """Remove completed batches older than specified hours"""
        current_time = datetime.now()
        expired_batches = []
        
        for batch_id, batch_result in self.active_batches.items():
            if batch_result.end_time:
                age_hours = (current_time - batch_result.end_time).total_seconds() / 3600
                if age_hours > max_age_hours:
                    expired_batches.append(batch_id)
        
        for batch_id in expired_batches:
            del self.active_batches[batch_id]
            logger.info(f"Cleaned up expired batch: {batch_id}")

# Utility functions for file discovery and validation
def discover_scg_files(directory: str, recursive: bool = True) -> List[str]:
    """Discover SCG files in directory"""
    scg_files = []
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.scg'):
                    scg_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            if file.lower().endswith('.scg') and os.path.isfile(os.path.join(directory, file)):
                scg_files.append(os.path.join(directory, file))
    
    return sorted(scg_files)

def validate_scg_files(file_paths: List[str]) -> Dict[str, List[str]]:
    """Validate SCG files before processing"""
    valid_files = []
    invalid_files = []
    
    for file_path in file_paths:
        try:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                # Basic validation - check if file has pump code
                with open(file_path, 'r') as f:
                    content = f.read(1000)  # Read first 1KB
                    if 'pPumpCode=' in content:
                        valid_files.append(file_path)
                    else:
                        invalid_files.append(file_path)
            else:
                invalid_files.append(file_path)
        except Exception:
            invalid_files.append(file_path)
    
    return {
        'valid_files': valid_files,
        'invalid_files': invalid_files
    }

# Usage example
if __name__ == "__main__":
    # Example batch processing
    config = BatchProcessingConfig(
        max_workers=2,
        timeout_per_file=30,
        update_existing=False,
        generate_report=True
    )
    
    processor = BatchSCGProcessor(config)
    
    # Example file paths (would be real SCG files)
    test_files = ["test1.scg", "test2.scg"]
    
    def progress_callback(progress_data):
        print(f"Progress: {progress_data['progress_percent']:.1f}% ({progress_data['processed_files']}/{progress_data['total_files']})")
    
    # Process files
    result = processor.process_files(test_files, progress_callback)
    
    print(f"Batch {result.batch_id} completed:")
    print(f"Success rate: {(result.successful_pumps / result.total_files) * 100:.1f}%")
    if result.report_path:
        print(f"Report saved to: {result.report_path}")