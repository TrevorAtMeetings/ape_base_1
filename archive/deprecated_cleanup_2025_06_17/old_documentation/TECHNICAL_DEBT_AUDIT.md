# Technical Debt Audit Report

## Legacy Processing Code Identified

### Obsolete Functions in app/routes.py

**1. `convert_txt_to_scg_format(txt_data)`** - Lines 610-687
- **Status**: OBSOLETE - Replaced by UnifiedPumpProcessor
- **Risk**: Still referenced but no longer needed
- **Impact**: Maintains old TXT-to-SCG conversion logic

**2. `parse_curve_data(data_str)`** - Lines 688-728
- **Status**: OBSOLETE - Replaced by enhanced parsing in UnifiedPumpProcessor
- **Risk**: Duplicates functionality in enhanced_scg_processor.py
- **Impact**: Basic string parsing vs advanced type-safe parsing

**3. Legacy TXT Processing Chain**
- **Status**: REPLACED - process_txt_upload() now wraps unified processor
- **Risk**: Old conversion logic still exists as dead code
- **Impact**: Code maintenance burden

### Obsolete Processing Logic in scg_processor.py

**1. `process_pump_data()` method** - Large complex function
- **Status**: SUPERSEDED by EnhancedSCGProcessor
- **Risk**: Contains outdated power calculation logic
- **Impact**: Inconsistent with unified processing standards

**2. Original SCGProcessor class**
- **Status**: REPLACED by UnifiedPumpProcessor
- **Risk**: May still be imported in some routes
- **Impact**: Dual processing paths create inconsistency

### Multiple Processing Engine Risk

**Current State**: 
- UnifiedPumpProcessor (NEW - Correct)
- SCGProcessor (OLD - Legacy)
- Enhanced_scg_processor.py (INTERMEDIATE - Proof of concept)

**Risk Assessment**: HIGH
- Multiple code paths for same functionality
- Inconsistent power calculations across processors
- Maintenance nightmare with 3 different implementations

## Recommended Cleanup Actions

### Phase 1: Remove Dead Code
1. Delete `convert_txt_to_scg_format()` function
2. Delete `parse_curve_data()` function  
3. Clean up unused imports

### Phase 2: Consolidate Processors
1. Remove old SCGProcessor class
2. Archive enhanced_scg_processor.py (development artifact)
3. Ensure all routes use UnifiedPumpProcessor

### Phase 3: Route Cleanup
1. Update any remaining SCG route references
2. Standardize error handling across all upload types
3. Remove conditional processing logic

## Implementation Priority: CRITICAL
Multiple processing engines create data consistency risks and maintenance overhead.