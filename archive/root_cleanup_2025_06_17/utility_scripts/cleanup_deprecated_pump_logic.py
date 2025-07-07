#!/usr/bin/env python3
"""
Cleanup Deprecated Pump Logic Files
Removes outdated test files, debug scripts, and redundant pump processing code
"""

import os
import shutil
from pathlib import Path

def cleanup_deprecated_files():
    """Remove deprecated pump logic files"""
    
    # Files to remove - all are debug/test files no longer needed
    deprecated_files = [
        # Debug and analysis files
        'analyze_28hc6p_data.py',
        'debug_28hc6p_selection.py', 
        'trace_28hc6p_selection.py',
        'comprehensive_npsh_scan.py',
        'quick_npsh_scan.py',
        'comprehensive_pdf_validation.py',
        
        # Test files - many are outdated/redundant
        'test_28hc6p_selection.py',
        'test_28hc6p_sizing.py',
        'test_catalog_integration.py',
        'test_chart_generation.py',
        'test_direct_query.py',
        'test_impeller_scaling.py',
        'test_pdf_fix.py',
        'test_power_validation.py',
        'test_pump_selection.py',
        'test_requirement_validation.py',
        'test_scg_integration.py',
        'test_scg_power_validation.py',
        'test_unified_processing.py',
        
        # Redundant utility files
        'pump_data_analyzer.py',
        'pump_data_structure_analysis.py',
        'power_calculation_validator.py',
        'npsh_analysis.py',
        'fix_document_query.py',
        
        # Old deployment/validation files now replaced
        'deployment_readiness_check.py',
        'deployment_validation.py',
        'pre_deployment_validation.py',
        
        # Outdated processing files
        'rebuild_pump_database.py',
        'create_catalog_database.py',  # Now part of unified processing
    ]
    
    # Documentation files to archive
    deprecated_docs = [
        'BUILD_ISSUES_DOCUMENT.md',
        'CODEBASE_CRITICAL_ISSUES_REPORT.md', 
        'TECHNICAL_DEBT_AUDIT.md',
        'APPLICATION_REVIEW_REPORT.md',
        'APPLICATION_REVIEW_SUMMARY.md',
        'COMPREHENSIVE_BUILD_STATUS.md',
        'FINAL_BUILD_VALIDATION_REPORT.md',
        'FINAL_CODEBASE_REVIEW.md',
        'QA_AUDIT_REPORT.md',
        'MASTER_PLAN_UPDATE.md',
        'MASTER_PLAN_UPDATE_2025_06_14.md',
        'TASK_4_1_1_COMPLETION_REPORT.md',
    ]
    
    removed_files = []
    archived_docs = []
    
    # Create archive directory if it doesn't exist
    archive_dir = Path('archive/deprecated_cleanup_2025_06_17')
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove deprecated Python files
    for file_name in deprecated_files:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                # Move to archive instead of deleting
                archive_path = archive_dir / file_name
                shutil.move(str(file_path), str(archive_path))
                removed_files.append(file_name)
                print(f"✓ Archived: {file_name}")
            except Exception as e:
                print(f"✗ Failed to archive {file_name}: {e}")
    
    # Archive old documentation
    docs_archive = archive_dir / 'old_documentation'
    docs_archive.mkdir(exist_ok=True)
    
    for doc_name in deprecated_docs:
        doc_path = Path(doc_name)
        if doc_path.exists():
            try:
                archive_path = docs_archive / doc_name
                shutil.move(str(doc_path), str(archive_path))
                archived_docs.append(doc_name)
                print(f"✓ Archived doc: {doc_name}")
            except Exception as e:
                print(f"✗ Failed to archive {doc_name}: {e}")
    
    return removed_files, archived_docs

def cleanup_log_files():
    """Clean up old log files and temporary files"""
    
    log_patterns = [
        '*.log',
        'bulk_upload_report.txt',
        'response.html',
        'llm_pdf_assessment.json',
        'deployment_readiness_report.json',
        'pre_deployment_validation_report.md',
        'pump_calculation_logic_review.md',
        'processing.md'
    ]
    
    cleaned_files = []
    
    for pattern in log_patterns:
        for file_path in Path('.').glob(pattern):
            if file_path.is_file():
                try:
                    # Move to archive
                    archive_path = Path('archive/deprecated_cleanup_2025_06_17') / file_path.name
                    shutil.move(str(file_path), str(archive_path))
                    cleaned_files.append(str(file_path))
                    print(f"✓ Archived log: {file_path}")
                except Exception as e:
                    print(f"✗ Failed to archive {file_path}: {e}")
    
    return cleaned_files

def main():
    """Execute the cleanup process"""
    print("=== APE Pumps Deprecated Logic Cleanup ===")
    print("Archiving deprecated test files, debug scripts, and old documentation...\n")
    
    # Clean up deprecated files
    removed_files, archived_docs = cleanup_deprecated_files()
    
    # Clean up log files
    cleaned_logs = cleanup_log_files()
    
    # Summary
    print(f"\n=== Cleanup Summary ===")
    print(f"Python files archived: {len(removed_files)}")
    print(f"Documentation archived: {len(archived_docs)}")
    print(f"Log files archived: {len(cleaned_logs)}")
    print(f"Total files cleaned: {len(removed_files) + len(archived_docs) + len(cleaned_logs)}")
    
    print(f"\n=== Current Active Pump Logic ===")
    print("Core pump processing files remaining:")
    
    active_pump_files = [
        'catalog_engine.py',           # Main catalog-based selection engine
        'impeller_scaling.py',         # Impeller sizing calculations
        'unified_pump_processor.py',   # Unified file processing
        'scg_catalog_adapter.py',      # SCG format adapter
        'batch_scg_processor.py',      # Batch processing
        'pump_engine.py',              # Legacy pump engine (still used)
        'pdf_generator.py',            # PDF report generation
        'app/selection_engine.py',     # UI selection logic
        'app/performance_calculator.py' # Performance calculations
    ]
    
    for file_name in active_pump_files:
        if Path(file_name).exists():
            print(f"✓ Active: {file_name}")
        else:
            print(f"✗ Missing: {file_name}")
    
    print(f"\nCleanup complete! All deprecated files archived to: archive/deprecated_cleanup_2025_06_17/")

if __name__ == "__main__":
    main()