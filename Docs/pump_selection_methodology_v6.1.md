# Pump Selection Methodology v6.1
**Last Updated: August 7, 2025**

## Executive Summary
This document defines the comprehensive pump selection methodology implemented in the APE Pumps Selection Application. Version 6.1 represents a significant refinement focusing on engineering best practices, manufacturer data trust, and realistic operating conditions.

## Core Principles

### 1. Manufacturer Data Trust
- **Fundamental Rule**: If performance data exists in the database, the manufacturer has validated that the pump can operate at those conditions
- **Implementation**: System evaluates all points within manufacturer's documented range, not artificially limited to theoretical percentages

### 2. Engineering Constraints
- **Impeller Trimming**: 85-100% of maximum diameter (15% maximum reduction)
- **Flow Operating Range**: 60-130% of BEP for standard selection
- **Extended Operation**: Allows manufacturer-documented points beyond 130% BEP
- **NPSH Safety Margin**: Required NPSHa ≥ 1.5 × NPSHr

### 3. Realistic Testing
- **Curve-Following Methodology**: Test points follow actual pump curves
- **No Impossible Conditions**: Eliminates physically unrealistic test scenarios
- **Authentic Validation**: Uses real operating conditions for accuracy assessment

## Selection Algorithm (v6.1)

### Phase 1: Initial Screening
1. **Load Pump Database**: Access all 386 pump models
2. **Basic Filtering**: Remove pumps without performance data
3. **Flow Range Check**: Verify pump can handle required flow rate

### Phase 2: Hard Gates (Pass/Fail Criteria)
1. **QBP Gate (Flow Range)**:
   - Primary range: 60-130% of BEP
   - Extended range: Trust manufacturer data beyond 130%
   - Logic: If flow is within manufacturer's documented range → PASS

2. **NPSH Safety Gate**:
   - Requirement: NPSHa ≥ 1.5 × NPSHr
   - Applied only when NPSHa is provided
   - Critical for cavitation prevention

### Phase 3: Solution Evaluation
1. **Method 1 - Direct Interpolation**:
   - Use existing curves at 100% impeller diameter
   - Linear interpolation between data points
   - No mechanical modifications required

2. **Method 2 - Impeller Trimming**:
   - Range: 85-100% of maximum diameter
   - Maximum reduction: 15%
   - Applies affinity laws for performance adjustment
   - Formula: Q₂/Q₁ = D₂/D₁, H₂/H₁ = (D₂/D₁)², P₂/P₁ = (D₂/D₁)³

### Phase 4: Scoring System (85 Points Maximum)

#### Operating Point Score (45 points)
- **Perfect Match (40-45 points)**: 
  - Flow within ±10% of BEP
  - Calculated as: 45 - |ΔFlow%| × 0.5
- **Good Match (20-40 points)**:
  - Flow 10-30% from BEP
  - Linear scaling based on deviation
- **Acceptable (0-20 points)**:
  - Flow 30-60% from BEP
  - Reduced scoring for suboptimal operation

#### Efficiency Score (20 points)
- **Excellent (18-20 points)**: η ≥ 80%
- **Good (10-18 points)**: 60% ≤ η < 80%
- **Acceptable (0-10 points)**: 40% ≤ η < 60%
- **Poor (0 points)**: η < 40%

#### Head Margin Score (20 points)
- **Perfect Sizing (20 points)**: 0-5% margin
- **Good Sizing (10-20 points)**: 5-10% margin
- **Acceptable (5-10 points)**: 10-15% margin
- **Oversized (0-5 points)**: 15-20% margin

#### Impeller Trim Penalty (Negative Points)
- **No Trim (0 penalty)**: 95-100% diameter
- **Light Trim (-2 points)**: 90-95% diameter
- **Moderate Trim (-5 points)**: 85-90% diameter
- **Not Allowed**: Below 85% diameter

### Phase 5: Ranking and Selection
1. Sort pumps by total score (highest first)
2. For equal scores, use power consumption as tie-breaker (lower is better)
3. Return top candidates with complete performance data

## Envelope Testing Methodology

### Curve-Following Approach (New in v6.1)
Instead of using a fixed head value across all flow rates, the system now:
1. **Extracts actual pump curve data** from manufacturer specifications
2. **Generates test points** that follow the natural pump curve
3. **Interpolates head values** at each test flow rate
4. **Validates performance** at realistic operating conditions

### Test Point Generation
```
Test Flow Percentages: [60%, 70%, 80%, 90%, 100%, 110%, 120%, 130%, 140%]
For each percentage:
  - Calculate test flow = BEP flow × percentage
  - Interpolate actual head from pump curve at this flow
  - Compare database vs UI calculations at realistic conditions
```

### Benefits
- Eliminates physically impossible test scenarios
- Improves validation accuracy
- Provides realistic performance assessment
- Supports manufacturer data beyond standard ranges

## Chart Display Requirements

### Standard Curves
- Display all available impeller diameters
- Show efficiency contours when available
- Mark operating point clearly
- Include NPSH curve if data exists

### Trimmed Curves (When Applicable)
- Generate and display trimmed performance curve
- Apply affinity laws for accurate representation
- Show both original and trimmed curves for comparison
- Label trim percentage clearly

### Operating Point Indicators
- Red triangle marker at X-axis pointing up to operating flow
- Vertical dotted line at operating flow
- Horizontal dotted line at operating head
- Small red dot at actual operating point intersection
- Display efficiency and power at operating point

## Data Integrity Principles

### No Fallback Logic
- Never use estimated values when authentic data is missing
- Report clear failures instead of artificial agreements
- Maintain strict separation between database and UI calculations

### Authentic BEP Usage
- Use manufacturer-specified BEP values (bep_flow_m3hr, bep_head_m)
- No interpolation or estimation of BEP from curves
- Clear identification when BEP data is unavailable

### Validation Status Definitions
- **Match**: ≤2% efficiency difference, ≤0.5kW power difference
- **Minor Difference**: 2-5% efficiency, 0.5-2kW power
- **Major Difference**: >5% efficiency, >2kW power
- **No Data**: Missing values on either side

## Implementation Status (August 7, 2025)

### Completed Features ✓
- Impeller trim range enforcement (85-100%)
- QBP gate with manufacturer data trust
- Curve-following envelope testing
- Trimmed curve chart display support
- Power-based tie-breaking for equal scores
- NPSH safety margin validation
- Authentic BEP data usage

### System Capabilities
- Total pump database: 386 models
- Performance points: 6,273
- Curve variations: 869
- NPSH data coverage: 612 curves
- Validation accuracy: >85% for standard operating ranges

## Usage Guidelines

### For Standard Selection
1. Enter flow rate and head requirements
2. Optionally provide NPSHa for cavitation check
3. System automatically evaluates all pumps
4. Returns ranked list with scores and methods

### For Extreme Conditions
1. System checks manufacturer data first
2. Allows operation beyond 130% BEP if documented
3. Clearly indicates when extrapolation is used
4. Provides warnings for unusual operating points

### For Report Generation
1. Includes complete scoring breakdown
2. Shows all evaluation methods attempted
3. Displays trimmed curves when applicable
4. Provides comprehensive technical data

## Conclusion
Pump Selection Methodology v6.1 represents a mature, engineering-focused approach that balances theoretical best practices with real-world manufacturer specifications. The system prioritizes authentic data, realistic operating conditions, and transparent evaluation methods to provide reliable pump recommendations for industrial applications.

---
*This document is maintained as part of the APE Pumps Selection Application and should be updated whenever methodology changes are implemented.*