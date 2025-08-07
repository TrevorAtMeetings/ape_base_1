# Pump Selection Methodology v6.0
## Fixed-Speed "Best Fit" System with Engineering Safety Gates

**Document Version**: 6.0  
**Date**: August 7, 2025  
**Status**: Critical Engineering Update - Implementation Required  
**Major Update**: Power Calculation Enhancement + NPSHa Engineering Calculation + Authentic Database Integration

---

## Executive Summary

### Critical Engineering Issues Resolved in v6.0

**Problem Identified**: The v5.0 system incorrectly mixed impeller trimming (fixed-speed pumps) and speed variation (VFD pumps) methodologies, leading to inappropriate selections and compromised engineering integrity.

**Solution Implemented**: Complete separation of fixed-speed and VFD workflows, with VFD logic temporarily disabled to perfect the fixed-speed methodology first.

### Revolutionary Changes in v6.0

1. **Fixed-Speed Focus**: Exclusively evaluates fixed-speed pumps using impeller trimming methodology
2. **NPSH Safety Gate**: Hard pass/fail NPSH requirement (NPSHa ≥ 1.5 × NPSHr) separate from scoring
3. **QBP Operating Range Gate**: Hard exclusion for pumps outside 60-130% of Best Efficiency Point
4. **Power-Based Tie-Breaking**: Secondary ranking criterion for pumps with similar scores
5. **Authentic Curve Display**: Charts show trimmed impeller curves, not maximum curves
6. **Rebalanced Scoring**: 85-point system with NPSH removed from ranking score
7. **Enhanced Power Calculations**: Proper RPM affinity laws with authentic test speed reference
8. **Engineering NPSHa Calculation**: Automatic calculation using atmospheric pressure, elevation, and system conditions

---

## Core Philosophy

**"Best Fit" Fixed-Speed System**: Evaluates all pumps against the duty point using only impeller trimming modifications. Filters pumps through physical and operational safety gates, then ranks viable solutions based on a comprehensive 85-point scoring system prioritizing reliability, efficiency, and right-sizing.

---

## August 2025 Update: Power & NPSH Calculation Enhancements

### Power Calculation Improvements
**Issue Resolved**: Previous versions used inconsistent power calculations that didn't properly account for RPM variations.

**New Implementation**:
- **Hydraulic Power Formula**: P(kW) = (Q × H × ρ × g) / (3600 × η)
- **Speed Affinity Laws**: P₂ = P₁ × (N₂/N₁)³ when operating speed differs from test speed
- **Test Speed Reference**: Uses authentic manufacturer test speeds from database
- **Impeller Trimming**: Power scales with diameter cubed: P₂ = P₁ × (D₂/D₁)³

### NPSHa Calculation Implementation
**Issue Resolved**: System previously used inappropriate 10.0 m default value.

**New Engineering Calculation**:
```
NPSHa = Atmospheric Pressure Head + Static Suction Head - Vapor Pressure Head - Friction Losses

Engineering Defaults:
- Atmospheric Pressure: 10.33 m (sea level, adjustable for elevation)
- Static Suction Head: +1.0 m (flooded suction assumption)
- Vapor Pressure: 0.02 m (water at 20°C using Antoine equation)
- Friction Losses: 0.5 m (typical piping losses)

Result: NPSHa = 10.81 m (calculated, not dummy value)
```

**Professional Features**:
- Transparent calculation breakdown shown in engineering reports
- Clear assumptions documented for verification
- Elevation-based atmospheric pressure correction
- Temperature-dependent vapor pressure calculation

---

## Detailed Methodology

### Phase 1: Initial Filtering & Pre-Sorting

#### Step 1: Data Validation
```
For each pump in database:
  1. Verify valid performance curves exist
  2. Check curve completeness (minimum 3 data points)
  3. Validate impeller diameter data
```

#### Step 2: Type Filtering
```
If pump_type specified:
  1. Filter by exact type match
  2. Log type-based exclusions
```

#### Step 3: BEP Proximity Pre-Sort
```
Sort remaining pumps by:
  Primary: |Pump_BEP_Flow - Required_Flow|
  Purpose: Performance optimization (evaluate best candidates first)
  Note: This is NOT an exclusion step
```

### Phase 2: Hard Feasibility Gates

All pumps must pass these non-negotiable safety and operational gates. **Failure at any gate excludes the pump with a clear engineering reason.**

#### Gate 1: QBP Operating Range Gate
**Purpose**: Ensure operation within acceptable Best Efficiency Point range

```
Calculation:
  BEP_Flow = Pump's nominal BEP flow rate
  QBP_Percentage = (Required_Flow / BEP_Flow) × 100

Hard Rule:
  IF QBP_Percentage < 60% OR QBP_Percentage > 130%:
    EXCLUDE pump
    Reason: "Operating point outside acceptable 60-130% BEP range"
```

**Engineering Rationale**: Operation outside 60-130% BEP leads to:
- Below 60%: Recirculation, cavitation risk, unstable operation
- Above 130%: Excessive vibration, accelerated wear, efficiency degradation

#### Gate 2: NPSH Safety Gate
**Purpose**: Prevent cavitation through adequate NPSH margin

**When Applied**: Only when user provides NPSHa (NPSH Available)

```
Calculation:
  NPSHr = NPSH Required at duty point (from pump curves)
  Safety_Factor = 1.5 (industry standard)

Hard Rule:
  IF NPSHa < (NPSHr × 1.5):
    EXCLUDE pump
    Reason: "Fails to meet required 1.5× NPSH safety margin"
```

**Engineering Rationale**: 1.5× safety margin accounts for:
- Pump manufacturing tolerances
- System calculation uncertainties
- Operational variations
- Long-term reliability requirements

#### Gate 3: Physical Feasibility Gate (Impeller Trimming)
**Purpose**: Ensure pump can meet duty point within acceptable trimming limits

```
Calculation:
  Required_Trim = Calculate impeller diameter needed for duty head
  Trim_Percentage = (Required_Diameter / Maximum_Diameter) × 100

Hard Rule:
  IF Trim_Percentage < 75%:
    EXCLUDE pump
    Reason: "Requires excessive impeller trim below 75% minimum"
```

**Engineering Rationale**: Excessive trimming (>25%) causes:
- Hydraulic instability
- Increased NPSH requirements
- Reduced efficiency
- Flow recirculation patterns

### Phase 3: "Best Fit" Evaluation & Scoring

For pumps passing all feasibility gates, find the optimal configuration using **fixed-speed methodology only**.

#### Evaluation Method: Impeller Trimming Analysis

**Step 1**: Direct Interpolation Check
```
Can pump meet duty point with maximum (100%) impeller?
  YES: Use direct interpolation, apply no trim penalty
  NO: Calculate required impeller trim
```

**Step 2**: Impeller Trim Calculation
```
Using Affinity Laws:
  H₂ = H₁ × (D₂/D₁)²
  Q₂ ≈ Q₁ × (D₂/D₁)  [approximately constant for small trims]
  Efficiency ≈ Constant [for trims 85-100%]

Calculate Required Diameter:
  D_required = D_max × √(H_required / H_max_curve)
```

#### Scoring Algorithm: 85-Point System

**Total Possible Score**: 85 points (expandable to 100 when additional criteria added)

##### 1. BEP Proximity Score (45 points max)
**Weight**: 52.9% of total score - **THE RELIABILITY FACTOR**

```python
Flow_Ratio = Required_Flow / BEP_Flow

if 0.95 <= Flow_Ratio <= 1.05:     # Sweet spot
    BEP_Score = 45
elif 0.90 <= Flow_Ratio < 0.95 or 1.05 < Flow_Ratio <= 1.10:
    BEP_Score = 40
elif 0.80 <= Flow_Ratio < 0.90 or 1.10 < Flow_Ratio <= 1.20:
    BEP_Score = 30
elif 0.70 <= Flow_Ratio < 0.80 or 1.20 < Flow_Ratio <= 1.30:
    BEP_Score = 20
else:  # 0.60-0.70 or 1.30-1.40 (gate allows up to 60-130%)
    BEP_Score = 10
```

##### 2. Efficiency Score (35 points max)
**Weight**: 41.2% of total score - **THE OPERATING COST FACTOR**

```python
Efficiency_Pct = Pump efficiency at duty point

if Efficiency_Pct >= 85:
    Efficiency_Score = 35
elif Efficiency_Pct >= 75:
    Efficiency_Score = 30 + (Efficiency_Pct - 75) * 0.5
elif Efficiency_Pct >= 65:
    Efficiency_Score = 25 + (Efficiency_Pct - 65) * 0.5
elif Efficiency_Pct >= 45:
    Efficiency_Score = 10 + (Efficiency_Pct - 45) * 0.75
else:  # 40-45% (gate excludes below 40%)
    Efficiency_Score = (Efficiency_Pct - 40) * 2
```

##### 3. Head Margin Score (20 points max)
**Weight**: 23.5% of total score - **THE RIGHT-SIZING FACTOR**

```python
Margin_Pct = ((Delivered_Head - Required_Head) / Required_Head) * 100

if Margin_Pct <= 5:                    # Perfect sizing
    Margin_Score = 20
elif 5 < Margin_Pct <= 10:            # Good sizing
    Margin_Score = 20 - (Margin_Pct - 5) * 2
elif 10 < Margin_Pct <= 15:           # Acceptable sizing  
    Margin_Score = 10 - (Margin_Pct - 10) * 1
else:  # 15-20% (higher margins penalized more heavily)
    Margin_Score = 5 - (Margin_Pct - 15) * 2
    Margin_Score = max(0, Margin_Score)  # Floor at 0
```

##### 4. NPSH Score: REMOVED
**Previous Weight**: 15 points - **NOW 0 POINTS**

**Rationale**: Inconsistent NPSH data availability makes fair comparison impossible. NPSH is now handled by the hard safety gate only.

##### 5. Impeller Trim Penalty (Deduction)
```python
if Trim_Percentage >= 95:             # Minimal trim
    Trim_Penalty = 0
elif Trim_Percentage >= 90:           # Light trim
    Trim_Penalty = -2
elif Trim_Percentage >= 85:           # Moderate trim
    Trim_Penalty = -5
elif Trim_Percentage >= 80:           # Heavy trim
    Trim_Penalty = -8
else:  # 75-80% trim (maximum allowed)
    Trim_Penalty = -12
```

### Phase 4: Final Ranking & Selection

#### Ranking Algorithm
```
1. Calculate Total Score for each pump:
   Total_Score = BEP_Score + Efficiency_Score + Margin_Score + Trim_Penalty

2. Primary Sort: Total Score (descending)

3. Secondary Sort (TIE-BREAKER): Power Consumption (ascending)
   Purpose: When scores are similar, prefer lower power consumption
   
4. Tertiary Sort: QBP Percentage proximity to 100%
   Purpose: Final tie-breaker for identical scores and power
```

#### Result Categorization
```
Top Recommendations:    Score ≥ 70 (82.4% of maximum)
Acceptable Options:     Score 55-69 (64.7-81.2%)
Marginal Choices:      Score 40-54 (47.1-63.5%)
Not Recommended:       Score < 40
```

---

## Engineering Standards & Limits

### Fixed-Speed Operating Constraints

#### Impeller Trimming Limits
- **Minimum Trim**: 75% of original diameter
- **Maximum Trim**: 100% (no trimming)
- **Optimal Range**: 85-100% for best hydraulic performance

#### Speed Constraints (VFD Logic Disabled)
- **Fixed Speed**: Pumps operate at rated speed only
- **No Speed Variation**: Speed modification algorithms disabled
- **Future Enhancement**: VFD logic to be re-implemented separately

### Safety Margins

#### NPSH Safety Requirements
- **Minimum Margin**: NPSHa ≥ 1.5 × NPSHr
- **Recommended Margin**: NPSHa ≥ 2.0 × NPSHr for continuous duty
- **Critical Applications**: NPSHa ≥ 3.0 × NPSHr for boiler feed, etc.

#### Head Delivery Tolerances
- **Minimum**: 100% of required head (exact match)
- **Optimal**: 102-105% of required head
- **Acceptable**: Up to 115% of required head
- **Excessive**: Above 120% (heavily penalized)

---

## Exclusion Categories & Engineering Guidance

### Primary Exclusion Reasons

#### 1. QBP Range Violation
**Trigger**: Operating point outside 60-130% of BEP
**Message**: "Operating point [X%] outside acceptable 60-130% BEP range"
**Engineering Action**:
- Below 60%: Consider smaller pump or multiple pump system
- Above 130%: Consider larger pump or system modification

#### 2. NPSH Safety Violation
**Trigger**: NPSHa < 1.5 × NPSHr
**Message**: "NPSH margin insufficient - requires [X]m, available [Y]m"
**Engineering Action**:
- Increase NPSHa: Lower suction lift, reduce suction losses
- Consider booster pump or pump relocation

#### 3. Excessive Trimming Required
**Trigger**: Required impeller trim < 75%
**Message**: "Requires excessive impeller trim ([X%] < 75% minimum)"
**Engineering Action**:
- Select smaller pump model
- Consider multi-stage configuration

#### 4. No Performance Data
**Trigger**: No valid performance curves available
**Message**: "No performance data available for evaluation"
**Engineering Action**:
- Contact manufacturer for performance data
- Consider alternative pump models

### Near-Miss Analysis

Pumps that fail feasibility gates by narrow margins receive special attention:

#### Near-Miss Criteria
- **QBP**: Within 5% of 60% or 130% boundaries
- **NPSH**: Within 0.5m of safety margin requirement
- **Head**: Within 2% of deliverable head

#### Near-Miss Guidance
Provides specific engineering recommendations:
- System modifications to accommodate pump
- Alternative pump configurations
- Parallel/series arrangements
- VFD consideration (future enhancement)

---

## Implementation Requirements

### Backend Changes Required

#### 1. Disable VFD Logic (`app/catalog_engine.py`)
```python
# Comment out or remove speed variation methods:
# - _calculate_speed_variation()
# - speed_variation paths in can_meet_requirements()
# - VFD-related scoring components

# Focus exclusively on impeller_trimming methods
```

#### 2. Implement QBP Gate
```python
def validate_qbp_range(self, pump, required_flow):
    """Hard gate: 60-130% BEP range check"""
    bep_flow = pump.get_bep_flow()
    if bep_flow:
        qbp_pct = (required_flow / bep_flow) * 100
        if qbp_pct < 60 or qbp_pct > 130:
            return False, f"QBP {qbp_pct:.1f}% outside 60-130% range"
    return True, ""
```

#### 3. Implement NPSH Gate
```python
def validate_npsh_safety(self, performance, npsha_available):
    """Hard gate: 1.5x NPSH safety margin"""
    if npsha_available:
        npshr = performance.get('npshr_m', 0)
        if npshr > 0:
            required_margin = npshr * 1.5
            if npsha_available < required_margin:
                return False, f"NPSH safety margin insufficient"
    return True, ""
```

#### 4. Update Scoring System
```python
def calculate_score_v6(self, performance, bep_analysis, sizing_info):
    """v6.0: 85-point scoring system"""
    # Remove NPSH scoring component
    # Rebalance weights: BEP=45, Efficiency=35, Margin=20
    # Add impeller trim penalties
    # Remove speed variation penalties
```

#### 5. Update Ranking Logic
```python
def rank_pumps_v6(self, evaluated_pumps):
    """v6.0: Multi-criteria ranking"""
    return sorted(evaluated_pumps, key=lambda x: (
        -x['total_score'],          # Primary: highest score
        x['power_consumption'],     # Secondary: lowest power
        abs(x['qbp_pct'] - 100)    # Tertiary: closest to 100% BEP
    ))
```

### Frontend Changes Required

#### 1. Fix Chart Display (`static/js/charts.js`)
```javascript
// Ensure trimmed curve data is passed to charts
// Current: Charts show maximum impeller curve
// Required: Charts show actual operating curve (trimmed)

function updateChartData(pumpData) {
    // Use trimmed_curve_data instead of max_curve_data
    const operatingCurve = pumpData.selected_curve;
    const trimmedPoints = calculateTrimmedCurve(
        pumpData.max_curve, 
        operatingCurve.trim_percentage
    );
    
    // Plot trimmed curve data
    plotPerformanceCurve(trimmedPoints);
}
```

#### 2. Update Score Display Components
```html
<!-- Remove NPSH scoring displays -->
<!-- Update total score to /85 instead of /100 -->
<!-- Add QBP gate status indicators -->
<!-- Add NPSH gate status indicators -->
```

#### 3. Fix Comparison Sorting (`templates/compare.html`)
```javascript
// Fix QBP column sorting
// Current: Sorts by raw percentage
// Required: Sorts by absolute distance from 100%

function sortByQBP(a, b) {
    const aDist = Math.abs(a.qbp_percentage - 100);
    const bDist = Math.abs(b.qbp_percentage - 100);
    return aDist - bDist;
}
```

---

## Testing & Validation

### Critical Test Cases

#### 1. QBP Gate Validation
```
Test Flow: 100 m³/hr, Head: 50m
Pump BEP: 200 m³/hr (QBP = 50%)
Expected: EXCLUDE (below 60% threshold)
```

#### 2. NPSH Gate Validation
```
NPSHa Available: 5m
Pump NPSHr: 4m
Required Margin: 4 × 1.5 = 6m
Expected: EXCLUDE (5m < 6m required)
```

#### 3. Scoring Validation
```
BEP Score: 40/45 (Flow ratio = 0.98)
Efficiency Score: 30/35 (82% efficiency)  
Margin Score: 15/20 (3% head margin)
Trim Penalty: -2 (95% trim)
Total: 83/85 points
```

#### 4. Tie-Breaker Validation
```
Pump A: Score=75, Power=50kW
Pump B: Score=75, Power=45kW  
Expected: Pump B ranked higher (lower power)
```

---

## Migration from v5.0 to v6.0

### Backward Compatibility

#### Database Schema
- **No changes required**: Existing pump data compatible
- **Performance curves**: Use existing impeller diameter data
- **BEP data**: Leverage existing specifications table

#### Session Data
- **Selection results**: Format remains compatible
- **Exclusion tracking**: Enhanced with new gate information
- **Score breakdowns**: Updated component weights

#### API Endpoints
- **Selection endpoints**: Maintain same interface
- **Response format**: Compatible with additional gate information
- **Chart data**: Enhanced with trimmed curve information

### Deployment Strategy

#### Phase 1: Backend Implementation
1. Implement QBP and NPSH gates
2. Disable VFD logic pathways
3. Update scoring algorithm
4. Add power-based tie-breaking

#### Phase 2: Frontend Updates
1. Fix chart trimmed curve display
2. Update score display components
3. Fix comparison table sorting
4. Add gate status indicators

#### Phase 3: Testing & Validation
1. Validate all test cases
2. Performance regression testing
3. User interface validation
4. Chart accuracy verification

---

## Future Enhancements

### v7.0 Planned Features

#### 1. VFD Logic Re-Implementation
- **Separate VFD Workflow**: Dedicated speed variation methodology
- **Dual Selection Mode**: User chooses fixed-speed or VFD
- **VFD-Specific Scoring**: Optimized for variable speed operation

#### 2. Enhanced Safety Gates
- **Cavitation Risk Assessment**: Advanced NPSH analysis
- **Vibration Limits**: Frequency-based exclusions  
- **Temperature Constraints**: Fluid property considerations

#### 3. Multi-Pump Configurations
- **Parallel Operation**: Multiple pump arrangements
- **Duty/Standby**: Redundancy planning
- **Staged Systems**: Progressive capacity systems

### v8.0+ Future Vision

#### 1. AI-Enhanced Selection
- **Machine Learning**: Pattern recognition in selection history
- **Predictive Maintenance**: Selection optimized for reliability
- **Cost Optimization**: Total cost of ownership analysis

#### 2. Industry-Specific Modules
- **Water Treatment**: Specialized requirements and constraints
- **HVAC**: Building system integration
- **Industrial Process**: Chemical compatibility and special materials

---

## Conclusion

Methodology v6.0 represents a fundamental restructuring of the pump selection algorithm to address critical engineering concerns. By separating fixed-speed and VFD methodologies, implementing hard safety gates, and rebalancing the scoring system, v6.0 provides a robust foundation for reliable pump selection.

The emphasis on engineering safety, authentic performance data, and transparent decision-making ensures that selections meet both technical requirements and practical operational constraints. This methodology serves as the definitive specification for implementing a world-class pump selection system.

**Next Steps**: Implementation of backend algorithm changes, followed by frontend updates and comprehensive testing validation.

---

**Document Control**
- **Author**: Engineering Analysis Team  
- **Review**: Senior Pump Engineers
- **Approval**: Technical Director
- **Distribution**: Development Team, QA Team, Product Management