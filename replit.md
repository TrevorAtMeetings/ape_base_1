# APE Pumps Selection Application

## Overview
This Flask-based web application provides an intelligent pump recommendation system for APE Pumps. It analyzes site requirements, matches them with APE pump models, and offers pump performance analysis with interactive charts and professional PDF report generation. The project aims to deliver a robust tool for efficient and accurate pump selection, enhancing APE's market position.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application employs a modular Flask architecture with a clear separation of concerns, supporting both backend and frontend components.

### Backend Architecture
- **Flask Framework**: Handles routing and HTTP requests.
- **Repository Pattern**: Centralized data access via `pump_repository.py`, supporting JSON and PostgreSQL.
- **Processing Engine**: Core pump analysis and selection logic in `pump_engine.py`.
- **File Processing**: Support for SCG and TXT pump data files, including batch processing.
- **Chart Generation**: Capabilities for both static (Matplotlib) and interactive (Plotly.js) charts.

### Configuration Management System
- **Template Configuration Module**: Centralized threshold and classification management
- **Dynamic Status Determination**: Runtime calculation of pump ratings and zones
- **Helper Function Library**: 14 specialized functions for consistent status display
- **Environment-Based Configuration**: Configurable thresholds without code changes

### Frontend Architecture
- **Template-Based UI**: Jinja2 templates for server-side rendering with dynamic configuration
- **Interactive Charts**: Plotly.js for dynamic performance curve visualization
- **Responsive Design**: Bootstrap-based styling ensures mobile compatibility
- **Form Handling**: Multi-step workflow for pump selection input

### Key Components
- **Data Management**: Unified access via `PumpRepository`, `Catalog Engine` for processing performance curves, and `SCG Processor` for authentic APE data conversion with validation.
- **Selection Engine**: Analyzes user input (flow, head, application) using intelligent scoring algorithms, performs curve interpolation/extrapolation, and applies affinity law for impeller scaling.
- **Report Generation**: Professional PDF reports using WeasyPrint, embedding static Matplotlib charts and comprehensive analysis via Jinja2 templates.
- **File Processing**: Native support for APE's SCG format, with batch processing, automatic format detection, and robust error handling.

### Data Flow
The process involves capturing user input, loading pump data, evaluating pumps against requirements, calculating performance, ranking selections, visualizing results, and finally generating professional PDF reports.

## External Dependencies
- **Flask**: Web application framework.
- **Gunicorn**: WSGI HTTP server.
- **psycopg2-binary**: PostgreSQL adapter.
- **NumPy**: Numerical computing.
- **SciPy**: Scientific computing for interpolation.
- **Matplotlib**: Static chart generation.
- **Plotly.js**: Interactive web charts.
- **OpenAI API**: GPT-based pump selection reasoning.
- **Google Gemini**: Alternative AI model.
- **WeasyPrint**: PDF generation.
- **Jinja2**: Template engine.
- **python-dotenv**: Environment variable management.
- **email_validator**: Input validation.
- **markdown2**: Markdown processing.

## Master Development Plan & Roadmap

### 🎯 **RECENT ACHIEVEMENTS (August 5, 2025)**
**✅ PHASE 1: FRONTEND FIXES COMPLETED**
- **Refactored charts.js** with 7 helper functions, eliminating ~400 lines of duplicate code
- **Fixed critical API bug** - Changed endpoint from `/api/chart_data_safe/` to `/api/chart_data/`
- **Resolved btoa() encoding issue** - Replaced with encodeURIComponent() for special characters
- **Improved code maintainability** - Created shared helpers (getImpellerName, calculateDataRanges, etc.)

**✅ PHASE 2: BEST FIT ALGORITHM IMPLEMENTED**
- **Transformed get_performance_at_duty()** from "First Fit" to "Best Fit" approach
- **Evaluates ALL possible methods** - Direct interpolation, impeller trimming, speed variation
- **Comprehensive scoring system** - BEP proximity (35pts), efficiency (30pts), head margin (15pts), NPSH (15pts)
- **Applies modification penalties** - Speed variation (up to -15pts), trimming (up to -10pts)
- **Returns highest scoring solution** - No longer returns first viable option

**🚀 PHASE 3: BEP-CENTRIC OPTIMIZATION IN PROGRESS**
- **Implemented pre-sorting algorithm** - Pumps sorted by BEP proximity before evaluation
- **Optimizes performance** - Most likely candidates evaluated first
- **No pumps filtered out** - Sort only, maintains comprehensive evaluation

### 🎯 **PHASE 2: ALGORITHM EXCELLENCE (MAJOR PROGRESS)**
**Status: CRITICAL IMPELLER TRIMMING LOGIC FIXED ✅**

#### **Phase 2.2: Algorithm Enhancement - Core Logic Fixes (COMPLETED ✅)**
**Objective:** Fix premature pump exclusions and implement comprehensive evaluation system

**🎉 MAJOR BREAKTHROUGHS ACHIEVED (August 5, 2025):**

1. **✅ FIXED: Pump Selection Priority Logic Bug**
   - **Problem**: Speed scaling was being returned before checking impeller trimming results
   - **Solution**: Restructured `get_performance_at_duty()` to properly prioritize trimming
   - **Result**: System now correctly prefers impeller trimming over speed variation

2. **✅ FIXED: Impeller Trimming Calculation Logic**
   - **Problem**: Algorithm immediately returned 100% trim when full impeller could meet requirements
   - **Solution**: Always calculate optimal diameter using affinity laws first
   - **Result**: System now calculates actual trimming percentages (e.g., 98.2% instead of 100%)

3. **✅ ENHANCED: Smart Trimming Decisions**
   - **Logic**: Only use full impeller when optimal trim would be minimal (>98%)
   - **Engineering**: Proper application of affinity law calculations (H₂ = H₁ × (D₂/D₁)²)
   - **Logging**: Clear visibility into trimming decisions and calculations

**VERIFICATION RESULTS:**
- **Before**: "Using impeller trimming - 560.0mm → 560.0mm (100.0% trim)"
- **After**: "Using impeller trimming - 560.0mm → 550.0mm (98.2% trim)"
- **Evidence**: System now properly calculates when smaller impellers are optimal

#### **Phase 2.3: Comprehensive Curve Evaluation (COMPLETED ✅)**
**Objective:** Eliminate 293 false pump exclusions through enhanced evaluation criteria

**🎉 MAJOR ACHIEVEMENTS (August 5, 2025):**

1. **✅ COMPREHENSIVE EVALUATION SYSTEM**
   - **Algorithm**: Now tries ALL curves with ALL methods before exclusion
   - **Logic**: Method 1 (direct) → Method 2 (extended extrapolation) → Method 3 (trimming) → Method 4 (speed variation)
   - **Result**: Dramatically reduced false exclusions while maintaining engineering safety

2. **✅ INDUSTRY-STANDARD EXTRAPOLATION**
   - **Before**: Conservative 10% extrapolation limit
   - **After**: Progressive 10% → 15% (industry-acceptable engineering operation)
   - **Impact**: Enables selection of pumps near duty point boundaries

3. **✅ ENHANCED MODIFICATION RANGES**
   - **Trimming**: Extended from 80-100% to 75-100% (industry standard)
   - **Speed**: Extended from 750-3600 to 600-3600 RPM (comprehensive coverage)
   - **Physical Limits**: Increased margins from 20% to 25% for engineering flexibility

4. **✅ PROPER EXCLUSION CATEGORIZATION**
   - **Before**: Generic "no performance data" or "envelope exceeded"
   - **After**: Specific reasons like "Curve 2: Requires 73.2% trim (below 75% minimum)"
   - **Engineering Value**: Clear guidance on why pumps excluded and potential alternatives



### 🎯 **PHASE 3: ENHANCED USER EXPERIENCE (NEXT PRIORITY)**

#### **Phase 3.1: Advanced Results Visualization (PLANNED)**
**Objective:** Enhanced transparency and user guidance in pump selection results

**PLANNED FEATURES:**
- **Interactive comparison matrix** with scoring heat maps
- **Radar charts** showing pump strengths/weaknesses across criteria
- **Traffic light feasibility indicators** (green/yellow/red zones)
- **Smart tooltips** explaining scoring components and exclusion reasons
- **Near-miss alternatives** with actionable engineering guidance

#### **Phase 3.2: Selection Process Transparency (PLANNED)**  
**Objective:** Complete visibility into selection methodology for engineering confidence

**PLANNED FEATURES:**
- **"Show Selection Process"** expandable section with detailed evaluation breakdown
- **Pump evaluation statistics** (total evaluated, excluded by reason, feasibility rates)
- **Exclusion heat map** by duty point and pump type
- **Score distribution analysis** to understand selection quality
- **Engineering decision log** showing why each pump was selected/excluded

#### **Phase 3.3: Performance Optimization (PLANNED)**
**Objective:** Maintain fast response times with comprehensive evaluation

**PLANNED IMPROVEMENTS:**
- **Parallel curve evaluation** for faster processing
- **Smart caching** of frequently accessed pump data
- **Progressive loading** of detailed performance data
- **Background pre-calculation** of common duty points

### 🎯 **PHASE 3: ARCHITECTURE EXCELLENCE (COMPLETED)**
**Status: TEMPLATE REFACTORING COMPLETE ✅**

#### **Phase 3.1: Template Refactoring (COMPLETED)**
**Objective:** Eliminate hard-coded logic and centralize configuration management

**✅ ACHIEVEMENTS:**
- **Centralized Configuration Module**: Created `app/template_config.py` with 14 helper functions
- **Backend Integration**: Enhanced `app/route_modules/reports.py` with dynamic preprocessing
- **Template Modernization**: Refactored `templates/professional_pump_report.html`
- **Proven Functionality**: App functionality completely maintained, charts working correctly

## Deployment Strategy

### Development Environment
- **Replit**: Cloud-based development platform
- **Hot Reload**: Flask debug mode for rapid development
- **Environment Variables**: `.env` file for configuration

### Production Configuration
- **Database**: PostgreSQL for production data storage
- **File Storage**: Local file system for uploads and temporary files
- **Logging**: Structured logging for monitoring and debugging
- **Error Handling**: Comprehensive error management with user feedback

### Configuration Management
- **Environment Variables**: Database URLs, API keys, and feature flags
- **Repository Configuration**: Switchable between JSON and PostgreSQL sources
- **Session Configuration**: Optional session management with secure defaults