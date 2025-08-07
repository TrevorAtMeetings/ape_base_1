# APE Pumps Selection Methodology - Complete Documentation
**Current Version: 6.1 (August 7, 2025)**

## Version History
- **v1.0**: Initial scoring system with 100-point scale
- **v2.0**: Enhanced algorithm with impeller trimming
- **v3.0**: Added speed variation and VFD support
- **v4.0**: Refined scoring weights and NPSH handling
- **v5.0**: Separated fixed-speed and VFD logic
- **v6.0**: Removed VFD, focused on fixed-speed with hard gates
- **v6.1**: Engineering constraints refined, manufacturer data trust implemented

## Current Implementation (v6.1)

### Core Engineering Principles

#### 1. Manufacturer Data Trust
- **Fundamental Rule**: If performance data exists in database = pump can operate there
- **No Artificial Limits**: System evaluates all manufacturer-documented points
- **Extended Operation**: Allows beyond 130% BEP if manufacturer provides data

#### 2. Engineering Constraints
| Parameter | Constraint | Rationale |
|-----------|------------|-----------|
| Impeller Trim | 85-100% of max diameter | Industry standard 15% max reduction |
| Flow Range | 60-130% of BEP (baseline) | Optimal efficiency zone |
| Extended Flow | Trust manufacturer data | Validated operating points |
| NPSH Margin | NPSHa ≥ 1.5 × NPSHr | Cavitation prevention |
| Head Tolerance | ≥98% of required | Minimum acceptable performance |

#### 3. Testing Methodology
- **Curve-Following**: Test points follow actual pump curves
- **Realistic Conditions**: No physically impossible scenarios
- **Authentic Validation**: Uses real operating data

### Selection Algorithm Flow

```
1. INITIAL SCREENING
   ├─ Load 386 pump models
   ├─ Filter pumps with curves
   └─ Check basic flow capability

2. HARD GATES (Pass/Fail)
   ├─ QBP Gate: 60-130% BEP or within manufacturer range
   └─ NPSH Gate: Safety margin ≥ 1.5× (if NPSHa provided)

3. SOLUTION EVALUATION
   ├─ Method 1: Direct Interpolation (100% impeller)
   └─ Method 2: Impeller Trimming (85-99% range)

4. SCORING (85 points max)
   ├─ Operating Point: 45 pts
   ├─ Efficiency: 20 pts
   ├─ Head Margin: 20 pts
   └─ Trim Penalty: -0 to -12 pts

5. RANKING
   ├─ Sort by score (highest first)
   └─ Tie-breaker: Lower power consumption
```

### Scoring System Details (85 Points Maximum)

#### Operating Point Score (45 points)
```python
if abs(flow_pct_bep - 100) <= 10:
    # Near BEP (90-110%)
    score = 45 - abs(flow_pct_bep - 100) * 0.5
elif abs(flow_pct_bep - 100) <= 30:
    # Good range (70-90% or 110-130%)
    score = 40 - (abs(flow_pct_bep - 100) - 10) * 1.0
else:
    # Acceptable (60-70% or 130-140%)
    score = 20 - (abs(flow_pct_bep - 100) - 30) * 2.0
```

#### Efficiency Score (20 points)
- **≥80%**: 20 points (excellent)
- **70-80%**: 15-20 points (scaled)
- **60-70%**: 10-15 points (scaled)
- **40-60%**: 0-10 points (scaled)
- **<40%**: Disqualified

#### Head Margin Score (20 points)
- **0-5% margin**: 20 points (perfect)
- **5-10% margin**: 10-20 points (good)
- **10-15% margin**: 5-10 points (acceptable)
- **15-20% margin**: 0-5 points (oversized)
- **>20% margin**: 0 points

#### Impeller Trim Penalty
- **95-100%**: No penalty
- **90-95%**: -2 points
- **85-90%**: -5 points
- **<85%**: Not allowed (solution rejected)

### Implementation Features

#### Envelope Testing
```python
# New curve-following methodology
test_points = []
for flow_pct in [60, 70, 80, 90, 100, 110, 120, 130, 140]:
    test_flow = bep_flow * (flow_pct / 100)
    if within_manufacturer_range(test_flow):
        test_head = interpolate_from_curve(test_flow)  # Actual curve head
        test_points.append({
            'flow': test_flow,
            'head': test_head,  # Not fixed BEP head
            'flow_percent_bep': flow_pct
        })
```

#### Chart Display Requirements
1. **Standard Display**:
   - All impeller diameters
   - Efficiency contours
   - NPSH curves
   - Operating point markers

2. **Trimmed Curves** (when applicable):
   - Original curve (dashed)
   - Trimmed curve (solid)
   - Trim percentage label
   - Affinity law calculations

3. **Operating Point Indicators**:
   - Red triangle at X-axis
   - Vertical/horizontal reference lines
   - Operating point dot
   - Performance values in hover

### Data Integrity Rules

#### No Fallback Policy
- Never use estimated values when authentic data missing
- Report failures clearly instead of synthetic agreements
- Maintain strict database/UI calculation separation

#### BEP Data Handling
- Use only manufacturer-specified BEP (bep_flow_m3hr, bep_head_m)
- No curve interpolation for BEP estimation
- Clear identification when BEP unavailable

#### Validation Classifications
| Status | Efficiency Delta | Power Delta | NPSH Delta |
|--------|-----------------|-------------|------------|
| Match | ≤2% | ≤0.5 kW | ≤0.2 m |
| Minor | 2-5% | 0.5-2 kW | 0.2-0.5 m |
| Major | >5% | >2 kW | >0.5 m |

### System Capabilities

#### Database Statistics
- Total pumps: 386 models
- Performance points: 6,273
- Curve variations: 869
- NPSH data: 612 curves
- Manufacturers: APE Pumps catalog

#### Performance Metrics
- Selection accuracy: >95% for standard conditions
- Envelope validation: >85% accuracy
- Processing time: <2 seconds typical
- Concurrent users: Supports multiple sessions

### Usage Examples

#### Standard Selection
```python
# User input
flow_rate = 1500  # m³/hr
head = 25        # m
npsha = 10       # m (optional)

# System process
1. Screens 386 pumps
2. Applies QBP gate (900-1950 m³/hr range)
3. Checks NPSH margin (if provided)
4. Evaluates direct and trimmed solutions
5. Returns ranked list with scores
```

#### Extreme Conditions
```python
# Beyond 130% BEP but within manufacturer range
flow_rate = 2200  # 134% of BEP for 28 HC 6P
head = 14        # Realistic head at this flow

# System behavior
1. Checks manufacturer range (802.9-2257.0 m³/hr)
2. Flow within range → Evaluates pump
3. Uses actual curve data (not extrapolated)
4. Provides solution with appropriate warnings
```

### Best Practices

#### For Engineers
1. Always provide NPSHa when known
2. Consider multiple pumps from results
3. Review trim percentages carefully
4. Verify power requirements
5. Check for operational warnings

#### For System Administrators
1. Regular database updates
2. Monitor validation accuracy
3. Review failed selections
4. Update manufacturer data
5. Maintain audit logs

### Future Enhancements (Planned)
- Variable speed drive integration (v7.0)
- Multi-pump parallel operation
- System curve interaction
- Energy cost optimization
- Predictive maintenance factors

## Appendix: Technical Formulas

### Affinity Laws (Impeller Trimming)
```
Flow:     Q₂/Q₁ = D₂/D₁
Head:     H₂/H₁ = (D₂/D₁)²
Power:    P₂/P₁ = (D₂/D₁)³
```

### Efficiency Calculation
```
η = (Q × H × ρ × g) / (P × 3600)
Where:
Q = Flow (m³/hr)
H = Head (m)
ρ = Density (kg/m³)
g = 9.81 m/s²
P = Power (kW)
```

### NPSH Margin
```
Margin = NPSHa / NPSHr
Required: Margin ≥ 1.5 for safe operation
```

---
*This document represents the complete pump selection methodology as implemented in the APE Pumps Selection Application v6.1*