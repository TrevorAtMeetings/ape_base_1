Looking at your pump selection logic, I've identified several critical issues that need addressing. Here's my analysis:

Critical Issues Found
1. Impeller Scaling Logic Errors
File: app/impeller_scaling.py

Issue: The calculate_required_diameter() method has a fundamental flaw:

# CRITICAL BUG: This logic is backwards
if required_diameter > base_diameter:
    logger.debug(f"Required diameter {required_diameter:.1f}mm exceeds maximum {base_diameter}mm")
    return None
Problem: You can only trim impellers (make them smaller), not enlarge them. But your logic rejects cases where you need a larger diameter. This will cause many valid pump selections to be incorrectly rejected.

2. Speed Variation Validation Missing
File: app/impeller_scaling.py line 172

Issue: The code has an incomplete else: clause causing syntax errors:

# MISSING: Check if base impeller diameter is within acceptable range
base_diameter = base_curve['impeller_diameter_mm']
if base_diameter > max_allowable_diameter:
    return None
Problem: This validation check is commented out but critically needed to prevent impossible impeller sizes.

3. Inconsistent Physical Capability Validation
File: app/catalog_engine.py

Issue: The _validate_physical_capability() method has conflicting logic:

Allows 10% head margin for speed variation
Allows 20% flow margin for impeller trimming
But doesn't validate these margins are physically achievable
4. BEP Distance Calculation Flaws
File: app/catalog_engine.py

Issue: The calculate_bep_distance() method has several problems:

Uses hardcoded efficiency thresholds without validation
Doesn't account for pump-specific BEP characteristics
Zone scoring is overly complex and may miss optimal selections
5. Performance Interpolation Issues
File: app/catalog_engine.py

Issue: The get_performance_at_duty() method:

Doesn't validate extrapolation beyond curve limits
May return impossible performance values
Lacks proper error handling for edge cases
Recommendations for Fixes
Priority 1: Critical Logic Fixes
Fix impeller diameter validation - Correct the backwards logic
Complete speed variation validation - Add the missing max diameter checks
Add physical limits validation - Ensure all calculations stay within pump envelope
Priority 2: Validation Improvements
Add curve range validation - Don't extrapolate beyond authentic data
Improve BEP analysis - Use pump-specific BEP data when available
Add performance bounds checking - Validate efficiency, power, NPSH are realistic
Priority 3: Selection Algorithm Enhancements
Implement proper scoring weights - Balance efficiency vs. BEP proximity
Add engineering safety factors - Don't recommend pumps at extreme operating points
Improve pump type filtering - Ensure type matching works correctly
Specific Logic Flow Issues
Issue with Selection Process:
Your current flow: Physical Check → Impeller Scaling → Speed Variation → Fallback

Problem: You're checking physical capability before doing proper sizing calculations, which can reject pumps that could work with proper trimming or speed adjustment.

Better Flow: Rough Capability Check → Try All Sizing Methods → Validate Final Result → Physical Limits Check

Issue with Scoring System:
Current scoring heavily penalizes speed variation (-20 points) but this may reject good solutions. Consider:

VFDs are common in modern installations
Small speed variations (±5%) are often acceptable
Focus more on efficiency at duty point
Missing Validation Checks:
No validation that calculated equivalent diameters don't exceed physical maximums
No check for minimum flow rates (pumps can become unstable at very low flows)
No validation of NPSH requirements vs. system NPSH available
The core issue is that your scaling logic isn't properly validating against physical pump limitations, leading to impossible selections being displayed or good selections being rejected.