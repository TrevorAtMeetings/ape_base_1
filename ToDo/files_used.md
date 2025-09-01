# Files and Methods Used in Pump Selection Process

## Sequential Flow of Files and Methods

### 1. User Input Processing
- `templates/input_form.html` - Form display
- `app/route_modules/main_flow.py / pump_selection()` - Form submission handler
- `app/route_modules/main_flow.py / pump_options()` - Main processing entry point

### 2. Data Models and Validation
- `app/data_models.py / SiteRequirements.__init__()` - Create site requirements object
- `app/utils.py / validate_site_requirements()` - Input validation

### 3. Brain System Initialization
- `app/pump_brain.py / get_pump_brain()` - Get singleton Brain instance
- `app/pump_brain.py / PumpBrain.__init__()` - Initialize Brain modules
- `app/brain/selection.py / SelectionIntelligence.__init__()` - Initialize selection module
- `app/brain/performance.py / PerformanceAnalyzer.__init__()` - Initialize performance module
- `app/brain/charts.py / ChartIntelligence.__init__()` - Initialize chart module
- `app/brain/validation.py / DataValidator.__init__()` - Initialize validator
- `app/brain/ai_analyst.py / AIAnalyst.__init__()` - Initialize AI analyst
- `app/brain/cache.py / BrainCache.__init__()` - Initialize caching

### 4. Core Selection Process
- `app/pump_brain.py / find_best_pumps()` - Main selection method
- `app/brain/selection.py / SelectionIntelligence.find_best_pumps()` - Core selection logic
- `app/pump_repository.py / get_pump_models()` - Load all pump data from repository

### 5. Pre-filtering Phase
- `app/brain/selection.py / SelectionIntelligence.find_best_pumps()` - Smart pre-filtering logic
  - Flow range filtering
  - Head range filtering  
  - Pump type constraint filtering

### 6. Individual Pump Evaluation Loop
- `app/brain/selection.py / SelectionIntelligence.evaluate_single_pump()` - Evaluate each pump
  - Three-Path Selection Logic (FLEXIBLE/TRIM_ONLY/VFD_ONLY/FIXED)
  - BEP analysis and QBP calculation
  - Operating zone classification (preferred/allowable/acceptable/marginal)
  - Physical capability validation

### 7. Performance Calculations
- `app/brain/performance.py / PerformanceAnalyzer.calculate_at_point()` - Main calculation entry
- `app/brain/performance.py / PerformanceAnalyzer.calculate_at_point_industry_standard()` - Industry standard method
- `app/brain/performance.py / PerformanceAnalyzer._calculate_required_diameter_direct()` - Affinity law calculations
- `app/brain/performance.py / PerformanceAnalyzer.calculate_performance_with_speed_variation()` - VFD calculations (if applicable)

### 8. Scoring System
- `app/brain/selection.py / SelectionIntelligence.evaluate_single_pump()` - Scoring components:
  - BEP proximity scoring
  - Efficiency scoring
  - Head margin scoring
  - Penalty calculations (oversizing, physical limitations)
  - Total score calculation

### 9. Physical Validation
- `app/brain/selection.py / SelectionIntelligence._validate_physical_capability_at_point()` - Physical capability check

### 10. Data Aggregation and Categorization
- `app/route_modules/main_flow.py / pump_options()` - Result processing:
  - Tier-based grouping (preferred/allowable/acceptable/marginal)
  - Essential result creation via `create_essential_result()`

### 11. Session Management
- `app/session_manager.py / store_pumps_optimized()` - Store pump results
- `app/session_manager.py / safe_session_set()` - Store tiered results
- `app/session_manager.py / safe_session_get()` - Retrieve stored data

### 12. Template Data Preparation
- `app/route_modules/main_flow.py / create_essential_result()` - Convert to template format

### 13. Results Rendering
- `templates/pump_options.html` - Results page display

### 14. Supporting Utilities and Services
- `app/admin_config_service.py / get_calibration_factors()` - Physics parameters
- `app/brain/physics_models.py / get_exponents_for_pump_type()` - Pump-specific physics
- `app/impeller_scaling.py` - Impeller sizing calculations (if needed)
- `app/brain/cache.py / BrainCache.get()` - Cache retrieval
- `app/brain/cache.py / BrainCache.set()` - Cache storage

### 15. Error Handling and Logging
- `app/route_modules/main_flow.py / pump_options()` - Exception handling
- `app/pump_brain.py / measure_performance()` - Performance monitoring decorator
- `app/pump_brain.py / BrainMetrics.record_operation()` - Metrics collection
- `app/pump_brain.py / BrainMetrics.record_error()` - Error tracking

---

## File Dependencies Summary

### Primary Flow Files:
1. `app/route_modules/main_flow.py`
2. `app/pump_brain.py`
3. `app/brain/selection.py`
4. `app/brain/performance.py`
5. `app/pump_repository.py`

### Supporting Files:
6. `app/data_models.py`
7. `app/session_manager.py`
8. `app/admin_config_service.py`
9. `app/brain/cache.py`
10. `app/brain/validation.py`
11. `app/brain/charts.py`
12. `app/brain/ai_analyst.py`
13. `app/brain/physics_models.py`
14. `app/impeller_scaling.py`
15. `app/utils.py`

### Templates:
16. `templates/input_form.html`
17. `templates/pump_options.html`

---

## Key Method Call Sequence

```
main_flow.pump_selection() 
  ↓
main_flow.pump_options()
  ↓
get_pump_brain()
  ↓
PumpBrain.find_best_pumps()
  ↓  
SelectionIntelligence.find_best_pumps()
  ↓
pump_repository.get_pump_models() 
  ↓
[For each pump:]
  SelectionIntelligence.evaluate_single_pump()
    ↓
  PerformanceAnalyzer.calculate_at_point()
    ↓
  PerformanceAnalyzer.calculate_at_point_industry_standard()
    ↓
  PerformanceAnalyzer._calculate_required_diameter_direct()
  ↓
[End loop]
  ↓
session_manager.store_pumps_optimized()
  ↓
main_flow.create_essential_result() [for each pump]
  ↓
render_template('pump_options.html')
```