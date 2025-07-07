#!/usr/bin/env python3
"""
Root Directory Cleanup Analysis
Identifies files that can be safely removed from the root directory
"""

import os
from pathlib import Path

def analyze_root_files():
    """Analyze files in root directory for cleanup opportunities"""
    
    # Files that can be safely removed
    removable_files = {
        'old_documentation': [
            'AI_CHATBOT_DEPLOYMENT_COMPLETE.md',
            'AI_CHATBOT_IMPLEMENTATION_STATUS.md', 
            'AI_CHATBOT_MASTER_PLAN.md',
            'CATALOG_DATABASE_BREAKTHROUGH.md',
            'CHATBOT_IMPLEMENTATION_SUMMARY.md',
            'DEPLOYMENT_READINESS.md',
            'FINAL_STATUS_REPORT.md',
            'MASTER_PLAN_FINAL.md',
            'NEXT_STEPS_ROADMAP.md',
            'PROCESSING_ENHANCEMENTS_SUMMARY.md',
            'PRODUCTION_DEPLOYMENT_GUIDE.md',
            'PRODUCTION_DEPLOYMENT_STATUS.md',
            'PUMP_DATA_UPLOAD_GUIDE.md',
            'PUMP_LOGIC_CLEANUP_SUMMARY.md',
            'SCG_DATA_INGESTION_REVIEW.md',
            'SCG_IMPLEMENTATION_COMPLETE.md',
            'SCG_INTEGRATION_PLAN.md',
            'STRATEGIC_NEXT_STEPS.md',
            'TECHNICAL_DEBT_CLEANUP_COMPLETE.md',
            'TECHNICAL_DEBT_RESOLUTION_REPORT.md',
            'UNIFIED_PROCESSING_IMPLEMENTATION.md'
        ],
        'test_pdfs': [
            'refined_5_k.pdf',
            'refined_6_8_ale.pdf', 
            'refined_6_k_6_vane.pdf',
            'refined_pdf.pdf',
            'refined_technical_reasoning.pdf',
            'test_chart_fix.pdf',
            'test_chart_pdf.pdf',
            'validation_test.pdf',
            'web_interface_test.pdf'
        ],
        'utility_scripts': [
            'cleanup_deprecated_pump_logic.py',  # This analysis script itself
            'llm_pdf_poc.py',  # Proof of concept, no longer needed
            'pump_cache.py',  # Redundant caching logic
            'pump_json_converter.py',  # Legacy converter
            'pump_upload_system.py'  # Superseded by unified processing
        ],
        'temporary_files': [
            'gemini_file_mapping.json',  # Temporary mapping file
            'pump_knowledge_index.db'  # Can be regenerated
        ]
    }
    
    # Core files that MUST be kept
    core_files = [
        'app.py',
        'main.py', 
        'pyproject.toml',
        'uv.lock',
        '.replit',
        # Core pump logic
        'catalog_engine.py',
        'impeller_scaling.py',
        'pdf_generator.py',
        'pump_engine.py',
        'unified_pump_processor.py',
        'scg_catalog_adapter.py',
        'scg_processor.py',
        'batch_scg_processor.py',
        'bulk_pump_uploader.py'
    ]
    
    print("=== ROOT DIRECTORY CLEANUP ANALYSIS ===\n")
    
    total_removable = 0
    for category, files in removable_files.items():
        print(f"📁 {category.upper().replace('_', ' ')} ({len(files)} files)")
        category_size = 0
        for file_name in files:
            if Path(file_name).exists():
                size = Path(file_name).stat().st_size
                category_size += size
                print(f"   ✓ {file_name} ({size/1024:.1f} KB)")
                total_removable += 1
            else:
                print(f"   ✗ {file_name} (not found)")
        print(f"   Category total: {category_size/1024:.1f} KB\n")
    
    print(f"🗂️  CORE FILES TO KEEP ({len(core_files)} files)")
    for file_name in core_files:
        if Path(file_name).exists():
            size = Path(file_name).stat().st_size
            print(f"   ✓ {file_name} ({size/1024:.1f} KB)")
        else:
            print(f"   ✗ {file_name} (missing - may need attention)")
    
    print(f"\n📊 SUMMARY")
    print(f"Files that can be removed: {total_removable}")
    print(f"Core files to preserve: {len([f for f in core_files if Path(f).exists()])}")
    
    return removable_files

def execute_cleanup(removable_files):
    """Execute the cleanup by moving files to archive"""
    
    archive_dir = Path('archive/root_cleanup_2025_06_17')
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    moved_count = 0
    
    for category, files in removable_files.items():
        category_dir = archive_dir / category
        category_dir.mkdir(exist_ok=True)
        
        for file_name in files:
            file_path = Path(file_name)
            if file_path.exists():
                try:
                    archive_path = category_dir / file_name
                    file_path.rename(archive_path)
                    print(f"✓ Moved {file_name} to archive/{category}/")
                    moved_count += 1
                except Exception as e:
                    print(f"✗ Failed to move {file_name}: {e}")
    
    print(f"\n🎉 CLEANUP COMPLETE")
    print(f"Successfully moved {moved_count} files to archive/")
    print(f"Root directory is now clean and organized!")

if __name__ == "__main__":
    print("Analyzing root directory for cleanup opportunities...")
    removable_files = analyze_root_files()
    
    print("\nDo you want to execute the cleanup? (This will move files to archive/)")
    # For automated execution, we'll proceed
    execute_cleanup(removable_files)