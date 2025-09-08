# Pump Selection Process - Runtime Execution Flow

## User Input → Results: Actual File Execution Order

When a user enters pump flow and head requirements, the following files are executed in sequence:

### Step 1: `selection_core.py`
- **Entry Point**: `find_best_pumps()` method
- **Function**: Main orchestrator that handles pre-filtering of pumps based on flow/head ranges, coordinates evaluation, and returns ranked results
- **Key Operations**: 
  - Pre-filters pumps (40%-300% flow range, 30%-200% head range)
  - Loops through filtered pumps for evaluation
  - Ranks results by total score

### Step 2: `pump_evaluator.py`
- **Called By**: selection_core.py during pump evaluation loop
- **Function**: Evaluates each individual pump using three-path logic
- **Key Operations**:
  - Determines evaluation path (trim-only, VFD-only, or flexible)
  - Calculates scoring components
  - Returns pump evaluation results

### Step 3: `physical_validator.py`
- **Called By**: pump_evaluator.py for validation
- **Function**: Validates pump can physically deliver required performance
- **Key Operations**:
  - Interpolates pump curves
  - Checks if pump can deliver required head at specified flow
  - Returns validation status

### Step 4: `performance_core.py`
- **Called By**: pump_evaluator.py for performance calculations
- **Function**: Central performance calculation coordinator
- **Key Operations**:
  - Delegates to specialized calculators
  - Handles both fixed and variable speed calculations
  - Returns performance metrics

### Step 5: `performance_advanced.py`
- **Called By**: performance_core.py
- **Function**: Routes to appropriate specialized calculator
- **Key Operations**:
  - Determines calculation method (trim vs VFD)
  - Delegates to industry standard or VFD calculator
  - Handles calculation orchestration

### Step 6: `performance_industry_standard.py`
- **Called By**: performance_advanced.py for impeller trim calculations
- **Function**: Performs affinity law calculations for impeller trimming
- **Key Operations**:
  - Starts with largest impeller
  - Calculates trim requirements using affinity laws
  - Returns trimmed performance data

### Step 7: `performance_vfd.py`
- **Called By**: performance_advanced.py for VFD calculations
- **Function**: Calculates performance with Variable Frequency Drive
- **Key Operations**:
  - Analyzes system curves
  - Calculates speed variation requirements
  - Returns VFD performance data

### Step 8: `performance_validation.py`
- **Called By**: performance_advanced.py for validation support
- **Function**: Provides validation utilities for performance calculations
- **Key Operations**:
  - Validates calculation inputs
  - Provides physics model references
  - Ensures data integrity

### Step 9: `physics_models.py`
- **Called By**: performance_validation.py and performance_industry_standard.py
- **Function**: Provides pump-type-specific affinity law exponents
- **Key Operations**:
  - Returns flow, head, and power scaling exponents
  - Provides pump-type-specific physics models
  - Supports accurate affinity law calculations

### Step 10: `scoring_utils.py`
- **Called By**: pump_evaluator.py for scoring explanations
- **Function**: Generates explanatory text for scoring components
- **Key Operations**:
  - Explains BEP proximity scoring (45 points max)
  - Explains efficiency scoring (35 points max)
  - Explains head margin scoring (20 points max)
  - Provides human-readable scoring reasons

## Summary
The selection process flows through 10 key files in the `/app/brain` folder, starting from the main orchestrator (selection_core.py) through evaluation, validation, performance calculation, and finally scoring. Each file has a specific role in the pump selection pipeline, ensuring accurate and optimized pump recommendations based on user requirements.