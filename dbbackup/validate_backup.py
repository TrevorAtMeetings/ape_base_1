#!/usr/bin/env python3
"""
Database Backup Validation Script
Validates the integrity and completeness of the APE Pumps database backup
"""

import psycopg2
import os
import sys

def validate_backup():
    """Validate the current database state matches expected backup contents."""
    
    print("APE Pumps Database Backup Validation")
    print("=" * 50)
    
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ ERROR: DATABASE_URL environment variable not set")
            return False
            
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Expected record counts (from backup validation)
        expected_counts = {
            'pumps': 386,
            'pump_curves': 869,
            'pump_performance_points': 7043,
            'pump_specifications': 386,
            'engineering_constants': 9,
            'pump_diameters': 3072,
            'pump_eff_iso': 3087,
            'pump_speeds': 3071
        }
        
        print("Validating Core Tables:")
        all_valid = True
        
        for table, expected in expected_counts.items():
            try:
                cur.execute(f'SELECT COUNT(*) FROM {table}')
                actual = cur.fetchone()[0]
                
                if actual == expected:
                    print(f"  ✅ {table}: {actual:,} records (✓)")
                else:
                    print(f"  ❌ {table}: {actual:,} records (expected {expected:,})")
                    all_valid = False
                    
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")
                all_valid = False
        
        # Validate Brain system components
        print("\nValidating Brain System:")
        
        # Check engineering constants
        cur.execute("SELECT name, value FROM engineering_constants ORDER BY name")
        constants = cur.fetchall()
        
        required_constants = [
            'bep_efficiency_exponent', 'bep_flow_exponent', 'bep_head_exponent',
            'flow_vs_diameter_exp', 'head_vs_diameter_exp', 'large_trim_head_exp',
            'power_vs_diameter_exp', 'small_trim_head_exp', 'volute_efficiency_penalty'
        ]
        
        constant_names = [c[0] for c in constants]
        for req_const in required_constants:
            if req_const in constant_names:
                print(f"  ✅ {req_const}: Present")
            else:
                print(f"  ❌ {req_const}: Missing")
                all_valid = False
        
        # Check schemas
        print("\nValidating Schemas:")
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('public', 'admin_config', 'brain_overlay')
            ORDER BY schema_name
        """)
        schemas = [row[0] for row in cur.fetchall()]
        
        for schema in ['admin_config', 'brain_overlay', 'public']:
            if schema in schemas:
                print(f"  ✅ {schema}: Present")
            else:
                print(f"  ❌ {schema}: Missing")
                all_valid = False
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 50)
        if all_valid:
            print("✅ BACKUP VALIDATION PASSED")
            print("Database state matches expected backup contents")
            return True
        else:
            print("❌ BACKUP VALIDATION FAILED")
            print("Database state differs from expected backup contents")
            return False
            
    except Exception as e:
        print(f"❌ VALIDATION ERROR: {e}")
        return False

if __name__ == "__main__":
    success = validate_backup()
    sys.exit(0 if success else 1)