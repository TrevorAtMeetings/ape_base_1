# Archive Directory
## Date: August 8, 2025

This directory contains decommissioned code from the Brain System migration project.

## Structure

### `/legacy_code`
Contains the original calculation and selection logic that has been replaced by the Brain system.
- Legacy pump selection algorithms
- Old scoring calculations
- Deprecated affinity law implementations

### `/debug_scripts`
Contains debug and analysis scripts used during the Brain-Legacy parity work.
- `analyze_brain_discrepancies.py` - Used to compare Brain vs Legacy results
- Various debugging utilities

### `/shadow_mode`
Contains the shadow mode comparison infrastructure that is no longer needed.
- Shadow mode wrappers
- Comparison logging code
- A/B testing infrastructure

## Why Archived?

These files were archived after the successful activation of the Brain system on August 8, 2025.
The Brain achieved a 76.5% match rate with Legacy, with the remaining 23.5% representing 
cases where Brain correctly applies stricter engineering criteria.

## Important Note

This code is kept for historical reference only. The Brain system is now the sole 
source of truth for all pump calculations and selections. Do not reintroduce any 
of this code back into the production system.