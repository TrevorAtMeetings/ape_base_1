# APE Pumps Selection Logic and Scoring Methodology

## Overview
Our pump selection algorithm uses a sophisticated scoring system that balances multiple factors to find the optimal pump for each application. The system prioritizes pumps that operate efficiently near their Best Efficiency Point (BEP) while meeting the required duty conditions.

## Scoring Components (Total: 100 points possible)

### 1. BEP Proximity Score (40 points max) - PRIMARY FACTOR
- **Purpose**: Ensures pump operates near its most efficient point
- **Calculation**: Based on how close the duty point is to the pump's BEP
- **Why it matters**: Pumps operating near BEP have:
  - Longer life due to reduced vibration and wear
  - Better efficiency and lower operating costs
  - More stable operation

### 2. Efficiency Score (35 points max) - SECONDARY FACTOR
- **Purpose**: Rewards pumps with high efficiency at the duty point
- **Calculation**: (Efficiency % / 100) × 35
- **Example**: 86% efficiency = 30.1 points
- **Minimum threshold**: 40% efficiency required for consideration

### 3. Head Margin Bonus/Penalty (15 points max to -∞) - TERTIARY FACTOR
This is where our recent fix was applied to prevent massive oversizing:

#### Scoring Brackets:
- **Perfect Match (-2% to +2%)**: 15 points
  - Example: 30m required, 29.4-30.6m delivered
  
- **Ideal Safety Margin (2-10%)**: 13 to 10.6 points
  - Linear reduction: 13 - (margin% - 2) × 0.3
  - Example: 5% over = 12.1 points
  
- **Acceptable Margin (10-20%)**: 10 to 8 points
  - Linear reduction: 10 - (margin% - 10) × 0.2
  - Example: 15% over = 9 points
  
- **Excessive Margin (20-50%)**: 8 to 2 points
  - Linear reduction: 8 - (margin% - 20) × 0.2
  - Example: 35% over = 5 points
  
- **Wasteful Oversizing (50-100%)**: 2 to -3 points
  - Linear reduction: 2 - (margin% - 50) × 0.1
  - Example: 75% over = -0.5 points
  
- **Extreme Oversizing (>100%)**: -3 points and worse
  - Additional penalty: -3 - (margin% - 100) × 0.05
  - Example: 466% over (like the 400-600 pump) = -21.3 points

### 4. Speed Variation Penalty (0 to -15 points)
For pumps requiring Variable Frequency Drives (VFDs):

- **0-5% speed change**: -0.5 to -2.5 points
  - Minimal penalty as small adjustments are common
  
- **5-10% speed change**: -2.5 to -7.5 points
  - Moderate penalty for more significant speed changes
  
- **>10% speed change**: -7.5 to -15 points (capped)
  - Larger penalty as extreme speed changes affect reliability

### 5. Impeller Trimming Penalty
- **<95% of original diameter**: -0.5 points per % trimmed
- **Example**: 90% trim = -2.5 points
- **Rationale**: Excessive trimming can affect pump hydraulics

## Selection Process

### Step 1: Initial Filtering
- Filter pumps by type if specified
- Calculate performance at duty point
- Exclude pumps with <40% efficiency

### Step 2: Operating Point Optimization
- Find best operating point within ±10% flow tolerance
- Update performance values to optimal point
- Verify pump still meets head requirement

### Step 3: Score Calculation
```
Base Score = BEP Score + Efficiency Score + Head Margin Bonus
Penalties = Speed Penalty + Trimming Penalty
Final Score = Base Score - Penalties
```

### Step 4: Ranking
- Sort pumps by final score (descending)
- Return top 10 selections

## Example Scoring Comparison

### Before Fix - 400-600 Pump Selection:
- Flow: 1500 m³/hr, Required Head: 30m
- Delivered Head: 169.8m (466% over!)
- BEP Score: ~25 points (good)
- Efficiency Score: ~28 points (80% efficiency)
- Head Margin: -21.3 points (massive penalty for 466% oversizing)
- **Total: ~32 points**

### After Fix - 12/14 BLE Selection:
- Flow: 1500 m³/hr, Required Head: 30m
- Delivered Head: 33.2m (10.6% over)
- BEP Score: ~32 points (excellent)
- Efficiency Score: 30.1 points (86.2% efficiency)
- Head Margin: 9.9 points (ideal safety margin)
- Speed Penalty: -2.1 points (small VFD adjustment)
- **Total: 80.1 points**

## Key Improvements Made

1. **Graduated Oversizing Penalties**: Instead of rewarding any pump that meets requirements, we now heavily penalize excessive oversizing
2. **System Curve Visualization**: Charts now show actual system requirements (30m) not pump delivery (169.8m)
3. **Balanced Scoring**: BEP proximity is primary, but efficiency and appropriate sizing are also critical

## Industry Best Practices Incorporated

1. **10-15% safety margin**: Ideal for most applications
2. **BEP operation**: Prioritizes long-term reliability
3. **Energy efficiency**: Considers operating costs
4. **Practical limits**: Allows minor speed/trim adjustments
5. **Right-sizing**: Prevents energy waste from oversized equipment

This methodology ensures users get pumps that are:
- Properly sized for their application
- Energy efficient
- Reliable and long-lasting
- Cost-effective to operate