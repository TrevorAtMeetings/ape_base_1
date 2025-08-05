# Pump Selection Methodology v5.0
## Comprehensive Best-Fit System with Enhanced Scoring

### Executive Summary
Version 5.0 represents a major evolution in our pump selection methodology, transitioning from a "First Fit" approach to a true "Best Fit" system. This methodology evaluates ALL possible solutions for each pump and selects the optimal configuration based on a comprehensive 100-point scoring system.

### Key Improvements in v5.0

1. **Comprehensive Evaluation**
   - Evaluates ALL pumps against ALL possible operating methods
   - No premature exclusions based on first failure
   - Progressive evaluation through multiple methods

2. **Enhanced Scoring System**
   - 100-point total score with weighted components
   - BEP Proximity: 40 points (reliability focus)
   - Efficiency: 30 points (operating cost)
   - Head Margin: 15 points (right-sizing)
   - NPSH: 15 points (cavitation prevention)

3. **Modification Penalties**
   - Speed variation: Up to -15 points
   - Impeller trimming: Up to -10 points
   - Encourages selection of pumps that work well "as-is"

4. **Transparency Features**
   - Detailed score breakdowns for every pump
   - Clear exclusion reasons with engineering context
   - Near-miss analysis for pumps that almost qualified

## Detailed Methodology

### Phase 1: Initial Screening
```
For each pump in database:
  1. Check for valid performance curves
  2. Verify pump type matches requirements (if specified)
  3. Pre-sort by BEP proximity to target flow
```

### Phase 2: Performance Evaluation Methods

#### Method 1: Direct Interpolation (Preferred)
- **When Used**: Pump can meet requirements without modifications
- **Extrapolation Limits**: 
  - Safe: ±10% of curve range
  - Maximum: ±15% of curve range
- **Score Bonus**: +10 points for no modifications needed

#### Method 2: Impeller Trimming
- **When Used**: Full impeller provides too much head
- **Trim Range**: 75% to 100% of original diameter
- **Calculations**: 
  - H₂ = H₁ × (D₂/D₁)²
  - Efficiency remains approximately constant
- **Penalties**: 0-10 points based on trim amount

#### Method 3: Speed Variation (VFD)
- **When Used**: Need to shift entire curve up/down
- **Speed Range**: 600 to 3600 RPM
- **Calculations**:
  - H₂ = H₁ × (N₂/N₁)²
  - Q₂ = Q₁ × (N₂/N₁)
  - P₂ = P₁ × (N₂/N₁)³
- **Penalties**: 0-15 points based on variation

### Phase 3: Scoring Algorithm

#### BEP Proximity Score (40 points max)
```
Flow Ratio = Duty Flow / BEP Flow

If 0.95 ≤ Flow Ratio ≤ 1.05:      Score = 40 (Optimal)
If 0.70 ≤ Flow Ratio < 0.95:      Score = 30 + (ratio-0.7) × 40
If 1.05 < Flow Ratio ≤ 1.20:      Score = 40 - (ratio-1.05) × 66.67
If 0.50 ≤ Flow Ratio < 0.70:      Score = 20 × (ratio-0.5) / 0.2
If 1.20 < Flow Ratio ≤ 1.50:      Score = 20 × (1.5-ratio) / 0.3
Otherwise:                          Score = 0
```

#### Efficiency Score (30 points max)
```
If Efficiency ≥ 85%:              Score = 30
If 75% ≤ Efficiency < 85%:        Score = 25 + (eff-75) × 0.5
If 65% ≤ Efficiency < 75%:        Score = 20 + (eff-65) × 0.5
If 40% ≤ Efficiency < 65%:        Score = (eff-40) × 0.4
If Efficiency < 40%:              Pump Excluded
```

#### Head Margin Score (15 points max)
```
Margin = (Delivered Head - Required Head) / Required Head × 100

If Margin ≤ 5%:                   Score = 15 (Perfect sizing)
If 5% < Margin ≤ 10%:             Score = 15 - (margin-5) × 1.5
If 10% < Margin ≤ 20%:            Score = 7.5 - (margin-10) × 0.75
If Margin > 20%:                  Score = -(margin-20) × 2 (Penalty)
```

#### NPSH Score (15 points max)
```
NPSH Margin = NPSHa - NPSHr

If Margin ≥ 3.0m:                 Score = 15 (Excellent)
If 1.5m ≤ Margin < 3.0m:          Score = 10 + (margin-1.5) × 3.33
If 0.5m ≤ Margin < 1.5m:          Score = 5 + (margin-0.5) × 5
If 0m ≤ Margin < 0.5m:            Score = margin × 10
If NPSH unknown:                  Score = 7.5 (Neutral)
```

### Phase 4: Final Selection

1. **Calculate Total Score**
   ```
   Total = BEP Score + Efficiency Score + Head Margin Score + NPSH Score - Penalties
   ```

2. **Rank All Feasible Pumps**
   - Sort by total score (highest first)
   - Group by score ranges for recommendations

3. **Categorize Results**
   - **Top Recommendations**: Score ≥ 70
   - **Acceptable Options**: Score 50-70
   - **Marginal Choices**: Score 30-50
   - **Near Misses**: Failed one criterion narrowly

### Implementation Guidelines

#### Database Requirements
- Complete performance curves with at least 5 points
- BEP flow and efficiency data
- Impeller diameter specifications
- NPSH curves (when available)

#### Calculation Precision
- Flow calculations: ±0.1 m³/hr
- Head calculations: ±0.1 m
- Efficiency: ±0.1%
- All interpolations: Quadratic or cubic splines

#### Error Handling
- Missing curves: Exclude with clear reason
- Incomplete data: Use conservative estimates
- Extrapolation failures: Log and exclude

### Example Selection Process

**Given Requirements:**
- Flow: 354 m³/hr
- Head: 308 m
- NPSHa: 10 m

**Pump Evaluation Example:**
```
Pump: 10/12 HSD
BEP: 380 m³/hr @ 91m

Step 1: Check curves - Has 3 curves available
Step 2: Try direct interpolation - Cannot reach 308m head
Step 3: Try speed variation:
  - Test speed: 1480 RPM
  - Required speed: 2857 RPM (to reach 308m)
  - Speed ratio: 1.93
  
Step 4: Calculate scores:
  - BEP Score: 35/40 (93% of BEP flow)
  - Efficiency Score: 22/30 (74% efficiency)
  - Head Margin: 15/15 (exact match)
  - NPSH Score: 12/15 (adequate margin)
  - Speed Penalty: -12 (large speed increase)
  
Total Score: 72/100 - Acceptable Option
```

### Reporting Features

#### Selection Summary
```json
{
  "summary": {
    "total_evaluated": 386,
    "physically_feasible": 14,
    "top_recommendations": 3,
    "excluded": 372,
    "methodology_version": "v5.0"
  }
}
```

#### Pump Comparison Entry
```json
{
  "pump_code": "10/12 HSD",
  "overall_score": 72,
  "score_breakdown": {
    "bep_score": 35,
    "efficiency_score": 22,
    "head_margin_score": 15,
    "npsh_score": 12,
    "speed_penalty": -12
  },
  "performance": {
    "efficiency_at_duty": 74,
    "power_kw": 145,
    "head_at_duty": 308,
    "sizing_method": "speed_variation",
    "required_speed": 2857
  }
}
```

#### Exclusion Analysis
```json
{
  "exclusion_analysis": {
    "No performance curves": 45,
    "Below minimum efficiency": 127,
    "Cannot meet head requirement": 185,
    "Excessive modifications required": 15
  }
}
```

### Benefits of v5.0 Methodology

1. **Engineering Integrity**
   - Respects pump operating limits
   - Applies industry-standard practices
   - Prevents dangerous selections

2. **Cost Optimization**
   - Prioritizes efficiency for lower operating costs
   - Right-sizes pumps to prevent waste
   - Identifies when VFDs are truly needed

3. **Reliability Focus**
   - Heavy weighting on BEP proximity
   - Penalties for extreme modifications
   - NPSH margins for safe operation

4. **User Transparency**
   - Clear scoring breakdowns
   - Understandable exclusion reasons
   - Near-miss analysis for alternatives

### Future Enhancements (v6.0 Planning)

1. **Lifecycle Cost Analysis**
   - 10-year NPV calculations
   - Maintenance cost predictions
   - Energy cost projections

2. **AI-Enhanced Predictions**
   - Failure mode analysis
   - Optimal maintenance scheduling
   - Performance degradation modeling

3. **Multi-Pump Optimization**
   - Parallel pump configurations
   - Duty/standby arrangements
   - Load-sharing strategies

4. **Industry-Specific Scoring**
   - Customizable weights by application
   - Special criteria for critical services
   - Regulatory compliance checking