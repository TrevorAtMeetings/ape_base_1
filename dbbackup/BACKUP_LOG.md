# Database Backup Log

## Latest Backup - August 13, 2025

### Binary Backup (Custom Format)
- **File**: `brain_system_binary_backup_20250813_095111.dump`
- **Size**: 243 KB
- **Format**: PostgreSQL custom binary format (compressed)
- **Created**: August 13, 2025 at 09:51:11
- **Purpose**: Fast restore, smaller file size, includes all database objects

### Plain SQL Backup
- **File**: `brain_system_full_backup_20250813_095111.sql`
- **Size**: 503 KB  
- **Format**: Plain SQL text format
- **Created**: August 13, 2025 at 09:51:11
- **Purpose**: Human-readable, cross-platform compatible, version control friendly

## Database Contents
- **Total Pumps**: 386
- **Total Curves**: 869
- **Performance Points**: 7,043
- **Tables Backed Up**:
  - ai_prompts
  - engineering_constants
  - extras
  - processed_files
  - pump_bep_markers
  - pump_curves
  - pump_diameters
  - pump_eff_iso
  - pump_names
  - pump_performance_points
  - pump_specifications
  - pump_speeds
  - pumps

## Restore Instructions

### To restore the binary backup:
```bash
pg_restore -d "$DATABASE_URL" dbbackup/brain_system_binary_backup_20250813_095111.dump
```

### To restore the SQL backup:
```bash
psql "$DATABASE_URL" < dbbackup/brain_system_full_backup_20250813_095111.sql
```

## Previous Backups
- `brain_system_full_backup_20250812_132431.sql` - August 12, 2025 (503 KB)
- `backup.sql` - August 12, 2025 (941 bytes) - Initial small backup

## Notes
- Binary format (.dump) is recommended for production restores (faster, smaller)
- SQL format (.sql) is better for inspection, partial restores, and version control
- Both backups contain identical data, just in different formats
- Backups include all Brain system data and manufacturer specifications