# APE Pumps Selection Process - Complete Flow Analysis

## Overview
This document provides a comprehensive analysis of the pump selection process from the user input form to the results page, documenting all classes, methods, data transformations, formulas, and conditional logic.

---

## 1. User Input & Form Submission

### **Entry Point: Pump Selection Form**
- **Template**: `input_form.html`
- **User Inputs**:
  - Flow Rate (m³/hr): e.g., 1781
  - Total Head (m): e.g., 22
  - Unit System: Metric/Imperial
  - Pump Type: All Types/HSC/End Suction/Multi-Stage/VTP/Axial Flow
  - Application Type: General/Water

### **Route Handler**: `/pump_selection` POST
- **File**: `app/route_modules/main_flow.py`
- **Method**: `pump_selection()`
- **Data Processing**:
  1. **Input Validation**:
     ```python
     flow_val = float(flow_m3hr)
     head_val = float(head_m)
     
     # Range validation
     if flow_val <= 0 or head_val <= 0:
         # Error handling
     if flow_val > 10000:  # Upper limit check
     if head_val > 1000:   # Upper limit check
     ```
  
  2. **Data Flow**: Redirects to `/pump_options` with parameters:
     ```python
     return redirect(url_for('main_flow.pump_options', 
                            flow=str(flow_val), 
                            head=str(head_val),
                            application_type=request.form.get('application', 'water'),
                            pump_type=selected_pump_type))
     ```

---

## 2. Main Processing Pipeline

### **Route Handler**: `/pump_options` GET
- **File**: `app/route_modules/main_flow.py`
- **Method**: `pump_options()`

#### **Step 1: Input Sanitization & Validation**
```python
# NaN protection and validation
if flow_str.lower() in ('nan', 'inf', '-inf'):
    flow = 0
else:
    flow = float(flow_str)
    if not (flow == flow):  # NaN check
        flow = 0

# Same for head validation
# Final validation: flow <= 0 or head <= 0 triggers error
```

#### **Step 2: Site Requirements Creation**
- **Class**: `SiteRequirements` (`app/data_models.py`)
- **Data Structure**:
  ```python
  site_requirements = SiteRequirements(
      flow_m3hr=flow,
      head_m=head,
      pump_type=pump_type,
      application_type=application_type
  )
  ```

#### **Step 3: Brain System Initialization**
- **Core Class**: `PumpBrain` (`app/pump_brain.py`)
- **Method**: `get_pump_brain()`
- **Brain Modules Initialized**:
  1. `SelectionIntelligence` - Pump selection logic
  2. `PerformanceAnalyzer` - Performance calculations
  3. `ChartIntelligence` - Chart generation
  4. `DataValidator` - Input validation
  5. `AIAnalyst` - AI-powered insights

---

## 3. Core Selection Intelligence

### **Primary Method**: `brain.find_best_pumps(site_reqs, constraints, include_exclusions=True)`
- **File**: `app/brain/selection.py`
- **Class**: `SelectionIntelligence`
- **Method**: `find_best_pumps()`

#### **Step 1: Repository Data Loading**
- **Method**: `self.brain.repository.get_pump_models()`
- **Data Source**: All pump models from database/repository
- **Logging**: Records total pumps loaded

#### **Step 2: Smart Pre-Filtering**
**Purpose**: Eliminate obviously incompatible pumps before detailed analysis

**Flow Range Filter**:
```python
min_flow_threshold = max(flow * 0.4, 5.0)  # Minimum 40% of required flow
max_flow_threshold = flow * 3.0            # Maximum 300% of required flow
```

**Head Range Filter**:
```python
min_head_threshold = head * 0.3   # Minimum 30% of required head
max_head_threshold = head * 2.0   # Maximum 200% of required head
```

**Exclusion Logic**:
- Pumps outside flow range: Skip to next pump
- Pumps outside head range: Skip to next pump
- **Conditional**: Debug logging for specific pump codes (HC series)

#### **Step 3: Pump Type Filtering**
**Conditional Logic**:
```python
if constraints.get('pump_type') and constraints['pump_type'] != 'GENERAL':
    pump_type = pump_data.get('pump_type', '').upper()
    constraint_type = constraints['pump_type'].upper()
    
    if pump_type != constraint_type:
        # Exclude pump - add to exclusion list
        excluded_pumps.append({...})
        continue
```

---

## 4. Individual Pump Evaluation

### **Method**: `evaluate_single_pump(pump_data, flow, head)`
- **File**: `app/brain/selection.py`
- **Returns**: Complete evaluation dictionary with scores and performance data

#### **Step 1: Three-Path Selection Logic**
**Purpose**: Determine pump operation method based on specifications

**Path Decision Matrix**:
```python
variable_speed = specs.get('variable_speed', False)
variable_diameter = specs.get('variable_diameter', True)

if variable_speed and variable_diameter:
    # PATH A: FLEXIBLE PUMPS - Can use either method
    operation_mode = 'FLEXIBLE'
    selection_method = 'IMPELLER_TRIM'  # Default choice
    
elif not variable_speed and variable_diameter:
    # PATH B: TRIM-ONLY PUMPS - Traditional fixed-speed
    operation_mode = 'TRIM_ONLY'
    selection_method = 'IMPELLER_TRIM'
    
elif variable_speed and not variable_diameter:
    # PATH C: VFD-ONLY PUMPS - Modern variable-speed
    operation_mode = 'VFD_ONLY'
    selection_method = 'SPEED_VARIATION'
    evaluation['vfd_required'] = True
    
else:
    # EDGE CASE: Both FALSE - Fixed configuration
    operation_mode = 'FIXED'
    selection_method = 'NONE'
```

#### **Step 2: BEP Analysis & Operating Zone Classification**
**Data Sources**:
- `bep_flow = specs.get('bep_flow_m3hr', 0)` - Manufacturer BEP flow
- `bep_head = specs.get('bep_head_m', 0)` - Manufacturer BEP head

**QBP Calculation**:
```python
qbp = (flow / bep_flow) * 100  # Percentage of BEP flow
```

**Tiered Operating Zone Classification**:
```python
if 80 <= qbp <= 110:
    operating_zone = 'preferred'  # Tier 1 - Optimal
    tier = 1
elif 60 <= qbp < 80 or 110 < qbp <= 140:
    operating_zone = 'allowable'  # Tier 2 - Good
    tier = 2
elif 50 <= qbp < 60 or 140 < qbp <= 200:
    operating_zone = 'acceptable' # Tier 3 - Industrial acceptable
    tier = 3
else:
    operating_zone = 'marginal'   # Tier 4 - Outside typical range
    tier = 4
```

#### **Step 3: Physical Capability Validation**
**Method**: `_validate_physical_capability_at_point(pump_data, flow, head)`
**Conditional Logic**:
```python
if not physical_capable:
    evaluation['score_components']['physical_limitation_penalty'] = -50
    evaluation['operating_zone'] = 'marginal'  # Force to marginal tier
    evaluation['tier'] = 4
```

---

## 5. Performance Calculations

### **Method**: `brain.performance.calculate_at_point(pump_data, flow, head)`
- **File**: `app/brain/performance.py`
- **Class**: `PerformanceAnalyzer`

#### **Core Calculation Path**:
1. **Industry Standard Method**: `calculate_at_point_industry_standard()`
2. **Direct Affinity Law Formula**: `_calculate_required_diameter_direct()`

#### **Affinity Law Implementation**
**Mathematical Formula**:
```python
# H₂ = H₁ × (D₂/D₁)²  →  D₂ = D₁ × sqrt(H₂/H₁)
# Enhanced with research-based trim-dependent physics

# Step 1: Interpolate head at target flow on largest curve
head_interp = interpolate.interp1d(flows_sorted, heads_sorted, kind='linear')
base_head_at_flow = float(head_interp(target_flow))

# Step 2: Check if target achievable (trimming reduces head)
if target_head > base_head_at_flow * tolerance:
    return None, None  # Cannot achieve higher head by trimming

# Step 3: Calculate required diameter using physics-based exponent
if estimated_trim_pct < 5.0:
    head_exponent = 2.9  # Small trim: higher exponent (research-based)
else:
    head_exponent = 2.1  # Large trim: standard exponent

# Formula: D₂ = D₁ × (H₂/H₁)^(1/head_exponent)
diameter_ratio = (target_head / base_head_at_flow) ** (1.0 / head_exponent)
required_diameter = largest_diameter * diameter_ratio
```

#### **Trim Percentage Calculation**:
```python
trim_percent = (required_diameter / largest_diameter) * 100
```

#### **Performance Interpolation**:
- **Efficiency**: Interpolated from performance curves
- **Power**: Calculated using affinity laws with power exponent
- **NPSH**: Interpolated from NPSH curves

---

## 6. Scoring System

### **Scoring Components** (Legacy v6.0 Point-Based System)

#### **1. BEP Proximity Score** (Max: 45 points)
```python
flow_ratio = flow / bep_flow

if 0.95 <= flow_ratio <= 1.05:     # Sweet spot
    bep_score = 45
elif 0.90 <= flow_ratio < 0.95 or 1.05 < flow_ratio <= 1.10:
    bep_score = 40
elif 0.80 <= flow_ratio < 0.90 or 1.10 < flow_ratio <= 1.20:
    bep_score = 30
elif 0.70 <= flow_ratio < 0.80 or 1.20 < flow_ratio <= 1.30:
    bep_score = 20
else:  # 0.60-0.70 or 1.30-1.40
    bep_score = 10
```

#### **2. Efficiency Score** (Max: 35 points)
```python
efficiency = performance.get('efficiency_pct', 0)

if efficiency >= 85:
    eff_score = 35
elif efficiency >= 75:
    eff_score = 30 + (efficiency - 75) * 0.5
elif efficiency >= 65:
    eff_score = 25 + (efficiency - 65) * 0.5
elif efficiency >= 45:
    eff_score = 10 + (efficiency - 45) * 0.75
else:  # 40-45%
    eff_score = max(0, (efficiency - 40) * 2)
```

#### **3. Head Margin Score** (Max: 20 points)
```python
head_margin_pct = (head_margin_m / head) * 100

if head_margin_pct <= 5:        # Perfect sizing
    margin_score = 20
elif 5 < head_margin_pct <= 10:  # Good sizing
    margin_score = 20 - (head_margin_pct - 5) * 2
elif 10 < head_margin_pct <= 15: # Acceptable sizing
    margin_score = 10 - (head_margin_pct - 10) * 1
else:  # 15-20%
    margin_score = 5 - (head_margin_pct - 15) * 2
    margin_score = max(0, margin_score)
```

#### **4. Penalty Systems**

**Head Oversizing Penalty**:
```python
head_ratio_pct = ((bep_head - head) / head) * 100

if head_ratio_pct > 150.0:  # Oversizing threshold
    if head_ratio_pct > 300.0:  # Severe oversizing
        oversizing_penalty = -30  # Heavy penalty
    else:  # Moderate oversizing (150-300%)
        oversizing_penalty = -15 - (head_ratio_pct - 150.0) * 0.1
```

**Physical Limitation Penalty**:
```python
if not physical_capable:
    evaluation['score_components']['physical_limitation_penalty'] = -50
```

#### **Total Score Calculation**:
```python
total_score = (bep_score + eff_score + margin_score + 
              oversizing_penalty + physical_limitation_penalty)
```

---

## 7. Data Aggregation & Session Storage

### **Result Categorization**
```python
# Tier-based grouping
preferred_pumps = [p for p in pump_selections if p.get('operating_zone') == 'preferred']
allowable_pumps = [p for p in pump_selections if p.get('operating_zone') == 'allowable']
acceptable_pumps = [p for p in pump_selections if p.get('operating_zone') == 'acceptable']
marginal_pumps = [p for p in pump_selections if p.get('operating_zone') == 'marginal']
```

### **Session Storage** (`app/session_manager.py`)
**Data Stored**:
1. `suitable_pumps` - All evaluated pumps with scores
2. `preferred_pumps` - Tier 1 pumps (80-110% BEP)
3. `allowable_pumps` - Tier 2 pumps (60-140% BEP)
4. `acceptable_pumps` - Tier 3 pumps (50-200% BEP)
5. `marginal_pumps` - Tier 4 pumps (outside typical ranges)
6. `site_requirements` - Original user inputs
7. `exclusion_data` - Summary of excluded pumps

### **Template Data Preparation**
**Method**: `create_essential_result(pump_data)`
**Purpose**: Convert raw pump data to template-compatible format

```python
essential = {
    'pump_code': pump_data.get('pump_code', 'N/A'),
    'suitability_score': pump_data.get('total_score', 0),
    'efficiency_pct': pump_data.get('efficiency_pct', 0),
    'power_kw': pump_data.get('power_kw', 0),
    'npshr_m': pump_data.get('npshr_m', 0),
    'qbp_percent': pump_data.get('qbp_percent', 100),
    'trim_percent': pump_data.get('trim_percent', 100),
    'operating_zone': pump_data.get('operating_zone', 'unknown'),
    'performance': {
        'efficiency_pct': pump_data.get('efficiency_pct', 0),
        'power_kw': pump_data.get('power_kw', 0),
        'npshr_m': pump_data.get('npshr_m', 0),
        'flow_m3hr': pump_data.get('flow_m3hr', 0),
        'head_m': pump_data.get('head_m', 0),
        'impeller_diameter_mm': pump_data.get('impeller_diameter_mm', 187)
    },
    'pump': {
        'manufacturer': pump_data.get('manufacturer', 'APE PUMPS'),
        'pump_type': pump_data.get('pump_type', 'END SUCTION'),
        'model_series': pump_data.get('model_series', 'Industrial'),
        'stages': pump_data.get('stages', '1')
    },
    'score_breakdown': {
        'bep_score': pump_data.get('bep_score', 0),
        'efficiency_score': pump_data.get('efficiency_score', 0),
        'margin_score': pump_data.get('margin_score', 0),
        'npsh_score': pump_data.get('npsh_score', 0)
    }
}
```

---

## 8. Results Rendering

### **Template**: `pump_options.html`
**Key Template Variables**:
- `pump_selections` - All pumps with essential data structure
- `preferred_pumps` - Tier 1 results (80-110% BEP)
- `allowable_pumps` - Tier 2 results (60-140% BEP)
- `acceptable_pumps` - Tier 3 results (50-200% BEP)
- `marginal_pumps` - Tier 4 results (outside typical ranges)
- `site_requirements` - Original search parameters
- `exclusion_data` - Summary statistics

### **Results Summary Calculation**
```python
total_pumps = len(preferred_pumps) + len(allowable_pumps) + len(acceptable_pumps) + len(marginal_pumps)
```

### **Display Data**:
- **Total Count**: Number of suitable pumps found
- **Flow/Head**: Original search parameters (1781.0 m³/hr @ 22.0m)
- **Best Score**: Highest suitability score achieved
- **Best Efficiency**: Highest efficiency percentage
- **Min Power**: Lowest power consumption

---

## 9. Key Conditional Logic Points

### **1. Input Validation Gates**
- **Condition**: `flow <= 0 or head <= 0`
- **Action**: Redirect to form with error message
- **Condition**: `flow > 10000 or head > 1000`
- **Action**: Warning message but continue processing

### **2. Pump Type Filtering**
- **Condition**: `constraints['pump_type'] != 'GENERAL'`
- **Action**: Apply pump type constraint
- **Else**: Allow all pump types

### **3. Pre-filtering Logic**
- **Flow Filter**: `min_flow_threshold <= bep_flow <= max_flow_threshold`
- **Head Filter**: `min_head_threshold <= bep_head <= max_head_threshold`
- **Action if fails**: Skip pump (add to filtered count)

### **4. Three-Path Selection**
- **Condition**: `variable_speed AND variable_diameter`
- **Action**: FLEXIBLE mode (default to impeller trimming)
- **Condition**: `NOT variable_speed AND variable_diameter`
- **Action**: TRIM_ONLY mode
- **Condition**: `variable_speed AND NOT variable_diameter`
- **Action**: VFD_ONLY mode (speed variation)
- **Else**: FIXED mode (no adjustments)

### **5. Physical Capability Check**
- **Condition**: `not physical_capable`
- **Action**: Apply -50 point penalty, force to marginal tier
- **Else**: Continue normal evaluation

### **6. Performance Calculation Fallbacks**
- **Condition**: `target_head > base_head_at_flow * tolerance`
- **Action**: Return None (pump cannot achieve required head)
- **Condition**: `trim_percent < min_trim_percent`
- **Action**: Use minimum allowed trim
- **Condition**: `trim_percent > max_trim_percent`
- **Action**: Use full impeller

### **7. Scoring Penalties**
- **Condition**: `head_ratio_pct > 150.0`
- **Action**: Apply head oversizing penalty
- **Condition**: `head_ratio_pct > 300.0`
- **Action**: Apply severe oversizing penalty (-30 points)

---

## 10. Data Transformations Summary

### **Input Transformations**:
1. String inputs → Float validation → NaN protection
2. User units → Internal metric units (if needed)
3. Form data → `SiteRequirements` object

### **Processing Transformations**:
1. Raw pump data → Filtered pump list (pre-filtering)
2. Pump specifications → BEP analysis (QBP calculation)
3. Operating point + pump curves → Performance data (affinity laws)
4. Performance data → Score components → Total score
5. Scored pumps → Tiered categorization (preferred/allowable/acceptable/marginal)

### **Output Transformations**:
1. Internal pump objects → Template-compatible dictionaries
2. Technical data → User-friendly display format
3. Tiered results → Session storage → Template rendering

---

## 11. Performance Monitoring

### **Brain Metrics** (`BrainMetrics` class)
- **Operations Tracking**: Duration of each Brain operation
- **Error Tracking**: Failed operations with error details
- **Discrepancy Tracking**: Legacy vs Brain calculation differences

### **Caching Strategy**
- **Cache Keys**: Generated from operation + parameters
- **TTL**: 300 seconds (5 minutes) for selection results
- **Cache Hierarchy**: Brain cache → Session storage → Database

---

## Summary

The pump selection process follows a sophisticated multi-stage pipeline:

1. **Input Validation** → **Site Requirements Creation** → **Brain System Initialization**
2. **Smart Pre-Filtering** → **Individual Pump Evaluation** → **Performance Calculations**
3. **Scoring & Ranking** → **Tiered Categorization** → **Session Storage** → **Results Rendering**

Each stage involves multiple conditional logic points, mathematical transformations, and data validations to ensure accurate and reliable pump selection results. The system is designed to be both technically rigorous (using industry-standard affinity laws and physics models) and user-friendly (with tiered results and clear explanations).

The entire process is logged and monitored for performance, with comprehensive error handling and fallback mechanisms throughout the pipeline.