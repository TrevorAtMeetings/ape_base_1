#!/usr/bin/env python3
"""
Verify PostgreSQL backup integrity
This script checks that a backup file contains expected tables and data
"""

import subprocess
import sys
import re
from datetime import datetime

def verify_backup(backup_file):
    """Verify the contents of a PostgreSQL backup file"""
    
    print(f"Verifying backup: {backup_file}")
    print("=" * 60)
    
    try:
        # List contents of the backup
        result = subprocess.run(
            ['pg_restore', '--list', backup_file],
            capture_output=True,
            text=True,
            check=True
        )
        
        contents = result.stdout
        
        # Expected tables
        expected_tables = [
            'pumps',
            'pump_specifications',
            'pump_curves',
            'pump_performance_points',
            'pump_bep_markers',
            'pump_diameters',
            'pump_speeds',
            'pump_names',
            'pump_eff_iso',
            'engineering_constants',
            'ai_prompts',
            'processed_files',
            'extras'
        ]
        
        # Check for each expected table
        print("Checking for required tables:")
        missing_tables = []
        found_tables = []
        
        for table in expected_tables:
            if f'TABLE DATA public {table}' in contents or f'TABLE public {table}' in contents:
                found_tables.append(table)
                print(f"  ✓ {table}")
            else:
                missing_tables.append(table)
                print(f"  ✗ {table} - MISSING")
        
        # Count total objects
        lines = contents.split('\n')
        table_count = len([l for l in lines if 'TABLE DATA' in l])
        index_count = len([l for l in lines if 'INDEX' in l])
        constraint_count = len([l for l in lines if 'CONSTRAINT' in l])
        
        print(f"\nBackup Statistics:")
        print(f"  Tables with data: {table_count}")
        print(f"  Indexes: {index_count}")
        print(f"  Constraints: {constraint_count}")
        print(f"  Found tables: {len(found_tables)}/{len(expected_tables)}")
        
        # Check for Brain overlay schema
        if 'brain_overlay' in contents:
            print("\n✓ Brain overlay schema included")
            brain_tables = [
                'configuration_history',
                'data_corrections',
                'data_quality_issues',
                'decision_traces',
                'manufacturer_selections',
                'performance_analyses',
                'selection_comparisons'
            ]
            for table in brain_tables:
                if f'brain_overlay {table}' in contents:
                    print(f"  ✓ brain_overlay.{table}")
        
        # Summary
        print("\n" + "=" * 60)
        if missing_tables:
            print(f"⚠️  WARNING: {len(missing_tables)} tables missing!")
            print(f"   Missing: {', '.join(missing_tables)}")
            return False
        else:
            print("✅ Backup verification PASSED!")
            print("   All essential tables present")
            print(f"   Backup file is ready for offline restore")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error verifying backup: {e}")
        print(f"   Make sure pg_restore is installed")
        return False
    except FileNotFoundError:
        print(f"❌ pg_restore not found. Install PostgreSQL client tools to verify.")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        backup_file = sys.argv[1]
    else:
        # Find the latest backup
        import glob
        import os
        backups = glob.glob("*.dump")
        if backups:
            backup_file = max(backups, key=os.path.getctime)
            print(f"Using latest backup: {backup_file}\n")
        else:
            print("Usage: python verify_backup.py <backup_file.dump>")
            print("Or run in directory with .dump files to verify the latest one")
            sys.exit(1)
    
    success = verify_backup(backup_file)
    sys.exit(0 if success else 1)