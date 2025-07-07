# APE Pumps Calculation Logic Review

## Overview
The APE Pumps selection system uses authentic pump performance data with engineering-driven calculations based on affinity laws and requirement-driven sizing methodology.

## 1. Pump Selection Process

### Primary Selection Algorithm (catalog_engine.py)
```python
def select_pumps(flow_m3hr, head_m, max_results=10, pump_type=None):
    # 1. Filter pumps by type if specified
    # 2. Find pumps that can meet requirements through sizing
    # 3. Score pumps based on efficiency and head margin
    # 4. Return ranked results
```

**Scoring Logic:**
- Primary: Efficiency at duty point (higher is better)
- Secondary: Head margin above requirement
- Penalty: Distance from Best Efficiency Point (BEP)

### Curve Selection for Each Pump
```python
def get_best_curve_for_duty(flow_m3hr, head_m):
    # Find curve with best efficiency at target flow/head
    # Score = head_error - efficiency * 0.1  # Favor higher efficiency
```

## 2. Impeller Scaling Engine (impeller_scaling.py)

### Core Affinity Laws Implementation

**Flow Scaling:**
```
Q₂ = Q₁ × (D₂/D₁) × (N₂/N₁)
```
- Q = Flow rate (m³/hr)
- D = Impeller diameter (mm)
- N = Speed (RPM)

**Head Scaling:**
```
H₂ = H₁ × (D₂/D₁)² × (N₂/N₁)²
```
- H = Head (m)

**Power Scaling:**
```
P₂ = P₁ × (D₂/D₁)³ × (N₂/N₁)³
```
- P = Power (kW)

**NPSH Scaling:**
```
NPSH₂ = NPSH₁ × (D₂/D₁)² × (N₂/N₁)²
```

### Impeller Trimming Logic

**Diameter Calculation:**
```python
# Calculate required diameter using affinity laws
# H₂ = H₁ × (D₂/D₁)²  =>  D₂ = D₁ × √(H₂/H₁)
diameter_ratio = sqrt(target_head / base_head_at_flow)
required_diameter = base_diameter * diameter_ratio
```

**Trimming Constraints:**
- Minimum trim: 85% (industry standard)
- Maximum efficiency loss: 5% from trimming
- Continuous trimming between min/max diameters

**Efficiency Penalty for Trimming:**
```python
efficiency_penalty = max(0, (100 - trim_percent) * 0.3)  # ~0.3% loss per 1% trim
actual_efficiency = base_efficiency - efficiency_penalty
```

## 3. Performance Calculation at Duty Point

### Power Calculation
```python
# Standard hydraulic power formula
efficiency_decimal = actual_efficiency / 100.0
sg = 1.0  # Specific gravity for water
actual_power = (flow_m3hr * head_m * sg * 9.81) / (efficiency_decimal * 3600)
```

### Interpolation Method
- Uses scipy.interpolate.interp1d with linear interpolation
- Interpolates between actual performance curve points
- Validates results are within curve bounds

## 4. Multi-Curve Optimization

### Sizing Approaches (find_optimal_sizing)

**Approach 1: Direct Calculation**
- Uses exact affinity law calculation for required diameter
- Validates against trimming limits

**Approach 2: Enhanced Sizing**
- Explores alternative diameter configurations
- Designed for pumps with multiple curves

**Approach 3: Continuous Trimming**
- Tests intermediate diameters in 10mm increments
- Supports user requirement for any diameter between min/max

### Scoring Algorithm
```python
efficiency_score = 100 - performance['efficiency_pct']  # Lower is better
trim_penalty = abs(100 - sizing['trim_percent']) * 0.5  # Penalty for trimming
total_score = efficiency_score + trim_penalty
```

## 5. Data Sources and Validation

### Authentic Pump Data
- Performance curves from manufacturer test data
- Multiple curves per pump model (different impeller sizes)
- NPSH curves (70.4% of pumps have NPSH data)
- Pump type classification from source data filters

### Example: 28 HC 6P Data
```json
{
  "pump_code": "28 HC 6P",
  "pump_type": "VTP", // From source: "VERTICAL TURBINE"
  "specifications": {
    "min_impeller_mm": 451.0,
    "max_impeller_mm": 501.0,
    "test_speed_rpm": 980
  },
  "curves": [
    {
      "impeller_diameter_mm": 451.0,
      "performance_points": [
        {"flow_m3hr": 763.5, "head_m": 22.8, "efficiency_pct": 70.74},
        {"flow_m3hr": 1648.0, "head_m": 16.5, "efficiency_pct": 81.9}
      ]
    },
    {
      "impeller_diameter_mm": 501.0,
      "performance_points": [
        {"flow_m3hr": 1648.0, "head_m": 24.2, "efficiency_pct": 85.0}
      ]
    }
  ]
}
```

## 6. Engineering Validation

### Requirement Checking
- Flow within pump curve range
- Head achievable with available impeller sizes
- Efficiency within acceptable range
- NPSH requirements met (when data available)

### Physical Constraints
- Impeller diameter cannot exceed maximum available
- Trimming limited to industry-standard minimums
- Speed variations within manufacturer limits

## 7. Results Presentation

### Performance Output
```python
{
  'flow_m3hr': 1781.0,
  'head_m': 24.20,
  'efficiency_pct': 85.0,
  'power_kw': 170.87,
  'npshr_m': 6.91,
  'impeller_diameter_mm': 501.0,
  'sizing_info': {
    'required_diameter_mm': 501.0,
    'trim_percent': 100.0,
    'meets_requirements': True,
    'head_margin_m': 0.20
  }
}
```

## 8. Calculation Accuracy

### Data Integrity
- All calculations use authentic manufacturer performance curves
- No synthetic or interpolated base data
- Pump type classifications from source data
- Performance points from actual test results

### Engineering Standards
- Affinity laws per Hydraulic Institute standards
- Industry-standard trimming limits
- Conservative efficiency penalties for modifications
- Proper power calculation using hydraulic formulas

### Validation Methods
- Cross-reference with multiple curves when available
- Boundary checking for all interpolations
- Physical constraint validation
- Engineering margin requirements

This calculation system provides engineering-grade pump selection using authentic manufacturer data with proper scaling methodologies to meet specific client requirements.