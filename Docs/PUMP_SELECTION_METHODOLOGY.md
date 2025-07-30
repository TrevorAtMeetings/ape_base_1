# APE Pumps Selection Logic and Scoring Methodology

## Overview
Our pump selection algorithm uses a comprehensive scoring system that balances multiple factors to find the optimal pump for each application. The system prioritizes pumps that operate efficiently near their Best Efficiency Point (BEP) while meeting the required duty conditions.

## Scoring Components (Total: 100 points possible)

### 1. BEP Proximity Score (40 points max) - THE RELIABILITY FACTOR
- **Purpose**: To heavily reward operation near the pump's Best Efficiency Point (BEP)
- **Formula**: Squared decay function that creates a "peak" at the BEP
  - Let Flow_Ratio = Duty_Flow / BEP_Flow
  - Score = 40 × max(0, 1 - ((Flow_Ratio - 1) / 0.5)²)
- **Behavior**:
  - At BEP (Flow_Ratio = 1.0): 40 points
  - At 70% or 130% of BEP flow: 3.6 points
  - At 50% or 150% of BEP flow: 0 points
  - Outside 50% deviation: 0 points (naturally filters egregiously misapplied pumps)

### 2. Efficiency Score (30 points max) - THE OPERATING COST FACTOR
- **Purpose**: To reward high efficiency at the duty point
- **Formula**: Score = (Efficiency_at_Duty_Point % / 100) × 30
- **Example**: 86% efficiency = 25.8 points
- **Minimum threshold**: Pumps with <40% efficiency are disqualified before scoring

### 3. Head Margin Score (15 points max to -∞) - THE RIGHT-SIZING FACTOR
- **Purpose**: To reward ideal safety margins and aggressively penalize oversizing using a smooth, continuous function
- **Formula**: Piece-wise function based on Margin % = ((Delivered_Head / Required_Head) - 1) × 100

| Margin (%) Range | Formula for Score | Example (15% margin) |
|------------------|-------------------|---------------------|
| < -2% (Under-sized) | Disqualified | N/A |
| -2% to +5% (Ideal) | 15 | 15 points |
| +5% to +20% (Good) | 15 - 0.5 × (Margin - 5) | 10 points |
| +20% to +50% (Excessive) | 7.5 - 0.25 × (Margin - 20) | N/A |
| > +50% (Wasteful) | 0 - 0.1 × (Margin - 50) | N/A |

- **Behavior**:
  - An ideal safety margin of 2-5% gets the full 15 points
  - The score decreases linearly to 7.5 points at a 20% margin
  - The penalty slope steepens, reaching 0 points at a 50% margin
  - Beyond 50%, the score becomes negative and continues to decrease

### 4. NPSH Score (15 points max) - THE CAVITATION RISK FACTOR
- **Purpose**: To holistically evaluate the pump's suitability for the suction conditions
- **Two modes based on user input**:

#### Mode A: NPSHa is KNOWN (Margin-Based Scoring)
- **Formula**: Based on NPSH_Margin_Ratio = NPSHa / NPSHr
  - Score = 15 × max(0, min(1, (NPSH_Margin_Ratio - 1.1) / (2.0 - 1.1)))
- **Behavior**:
  - If ratio ≤ 1.1 (minimal margin): 0 points
  - Linear scaling from 0 to 15 points as ratio increases from 1.1 to 2.0
  - If ratio ≥ 2.0 (excellent margin): 15 points (capped)
- **Hard Filter**: Pumps where NPSHr ≥ NPSHa are disqualified before scoring

#### Mode B: NPSHa is UNKNOWN (Requirement-Based Scoring)
- **Purpose**: To reward pumps that are inherently less risky and easier to apply
- **Formula**: Based on the absolute NPSHr value (in meters)
  - Score = 15 × max(0, (8 - NPSHr) / (8 - 2))
- **Behavior**:
  - If NPSHr ≤ 2m (excellent, very low requirement): 15 points (capped)
  - Linear scaling down as NPSHr increases
  - If NPSHr ≥ 8m (very demanding): 0 points

### 5. Speed Variation Penalty (Deducts up to 15 points)
- **Formula**: Penalty = 1.5 × Speed_Change % (capped at max penalty of 15)
- **Examples**:
  - 5% speed change: -7.5 penalty
  - 10% or greater speed change: -15 penalty (maximum)

### 6. Impeller Trimming Penalty (Deducts points)
- **Formula**: Penalty = 0.5 × Trim %
- **Example**: 10% trim (to 90% diameter) gives a -5 point penalty

## Final Calculation Process

1. **Initial Filtering**: Apply hard filters (Pump Type, Min Efficiency, Under-sized Head, NPSHa/NPSHr check if applicable)
2. **Optimization**: Find best operating point within ±10% flow
3. **Calculate Base Score**: Score = BEP_Score + Efficiency_Score + Head_Margin_Score + NPSH_Score
4. **Apply Penalties**: Final Score = Base_Score - VFD_Penalty - Trim_Penalty
5. **Rank pumps by Final Score**

## Selection Process

### Step 1: Initial Filtering
- Filter pumps by type if specified
- Calculate performance at duty point
- Exclude pumps with <40% efficiency
- If NPSHa is provided, exclude pumps where NPSHr ≥ NPSHa

### Step 2: Operating Point Optimization
- Find best operating point within ±10% flow tolerance
- Update performance values to optimal point
- Verify pump still meets head requirement

### Step 3: Score Calculation
```
Base Score = BEP Score + Efficiency Score + Head Margin Score + NPSH Score
Penalties = Speed Penalty + Trimming Penalty
Final Score = Base Score - Penalties
```

### Step 4: Ranking
- Sort pumps by final score (descending)
- Return top 10 selections

## Example Scoring Comparison

### Example 1: Properly Sized Pump (12/14 BLE)
- **Requirements**: Flow: 1500 m³/hr, Head: 30m
- **Delivered**: Head: 33.2m (10.6% over)
- **Scoring Breakdown**:
  - BEP Score: 32 points (excellent - near BEP)
  - Efficiency Score: 25.9 points (86.2% efficiency)
  - Head Margin Score: 9.7 points (good safety margin)
  - NPSH Score: 12.5 points (NPSHr = 3.5m - low requirement)
  - Speed Penalty: -3.2 points (2.1% speed adjustment)
  - **Total: 76.9 points**

### Example 2: Oversized Pump (400-600)
- **Requirements**: Flow: 1500 m³/hr, Head: 30m
- **Delivered**: Head: 169.8m (466% over!)
- **Scoring Breakdown**:
  - BEP Score: 25 points (good)
  - Efficiency Score: 24 points (80% efficiency)
  - Head Margin Score: -41.6 points (extreme oversizing penalty)
  - NPSH Score: 10 points (NPSHr = 4.5m - moderate requirement)
  - **Total: 17.4 points**

### Key Differences:
- The properly sized pump scores 4.4x higher (76.9 vs 17.4 points)
- The head margin score alone creates a 51.3 point difference
- NPSH scoring adds valuable differentiation between pumps

## Key Improvements in This Update

1. **Comprehensive Scoring System**: 
   - Added NPSH scoring (15 points) for cavitation risk assessment
   - Adjusted efficiency score from 35 to 30 points
   - Refined head margin scoring with smoother transitions
   
2. **NPSH Dual-Mode Scoring**:
   - Mode A: When user provides NPSHa - uses margin-based scoring
   - Mode B: When NPSHa unknown - uses requirement-based scoring
   - Graceful handling of pumps without NPSH data (26.4% of catalog)

3. **Improved Penalty System**:
   - VFD penalty: Linear 1.5× speed change (was graduated)
   - Trim penalty: Linear 0.5× trim percentage
   - Both capped at reasonable limits

4. **BEP Scoring Enhancement**:
   - Squared decay function for sharper differentiation
   - Zero points beyond 50% flow deviation from BEP
   - Natural filtering of severely misapplied pumps

## Industry Best Practices Incorporated

1. **Safety Margins**: 2-5% ideal, up to 20% acceptable
2. **BEP Operation**: Primary focus on reliability
3. **NPSH Safety**: 1.1-2.0 margin ratio recommended
4. **Energy Efficiency**: Minimum 40% efficiency requirement
5. **Right-Sizing**: Aggressive penalties for >50% oversizing

## Benefits of This Methodology

- **Reliability**: Prioritizes pumps operating near BEP
- **Safety**: Ensures adequate NPSH margins to prevent cavitation
- **Efficiency**: Balances initial cost with operating costs
- **Flexibility**: Accommodates missing data without penalizing pumps
- **Precision**: Delivers properly sized equipment for each application
- Cost-effective to operate