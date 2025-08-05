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

**✅ ADMIN CONFIGURATION SYSTEM IMPLEMENTED**
- **Separate Schema Protection** - Created `admin_config` schema to isolate configuration from golden source pump data
- **Application Profiles** - 6 pre-configured profiles (General Purpose, Municipal Water, Industrial, HVAC, Fire Protection, Chemical)
- **Configurable Parameters**:
  - Scoring weights (BEP, efficiency, head margin, NPSH) - must total 100
  - Efficiency thresholds (minimum, fair, good, excellent)
  - BEP operating zones (optimal flow range)
  - NPSH safety margins (minimum, good, excellent)
  - Modification penalties (speed variation, impeller trimming)
  - Reporting preferences (thresholds, near-miss count)
- **Locked Engineering Constants** - Display-only reference for:
  - Affinity laws (flow, head, power relationships)
  - Impeller trimming laws
  - Physical limits (speed range, trim limits)
  - NPSH requirements
  - Interpolation methods
- **Audit Trail** - Complete change history with user, timestamp, and reason
- **Caching System** - 5-minute TTL for performance optimization
- **Admin Dashboard** - Located at `/admin/config/` with profile management interface
**✅ PHASE 1: FRONTEND FIXES COMPLETED**
- **Refactored charts.js** with 7 helper functions, eliminating ~400 lines of duplicate code
- **Fixed critical API bug** - Changed endpoint from `/api/chart_data_safe/` to `/api/chart_data/`
- **Resolved btoa() encoding issue** - Replaced with encodeURIComponent() for special characters
- **Improved code maintainability** - Created shared helpers (getImpellerName, calculateDataRanges, etc.)

**✅ PHASE 2: BEST FIT ALGORITHM IMPLEMENTED**
- **Transformed get_performance_at_duty()** from "First Fit" to "Best Fit" approach
- **Evaluates ALL possible methods** - Direct interpolation, impeller trimming, speed variation
- **Comprehensive scoring system** - BEP proximity (40pts), efficiency (30pts), head margin (15pts), NPSH (15pts)
- **Applies modification penalties** - Speed variation (up to -15pts), trimming (up to -10pts)
- **Returns highest scoring solution** - No longer returns first viable option

**✅ PHASE 3: BEP-CENTRIC OPTIMIZATION COMPLETED**
- **Implemented pre-sorting algorithm** - Pumps sorted by BEP proximity before evaluation
- **Optimizes performance** - Most likely candidates evaluated first
- **No pumps filtered out** - Sort only, maintains comprehensive evaluation
- **Fixed runtime errors** - NoneType comparisons, missing helper functions, API routing for pump codes with slashes
- **System fully operational** - 386 pumps evaluated, charts rendering correctly

**✅ PHASE 4.2: ENHANCED PDF REPORTS COMPLETED**
- **Created generate_enhanced_pdf_report()** - New comprehensive PDF generation function
- **Added scoring breakdown display** - All score components visible in PDF reports
- **Integrated performance charts** - All 4 charts (head, efficiency, power, NPSH) included
- **Fixed PDF generation dependencies** - Installed system libraries (pango, cairo) for WeasyPrint
- **Added Enhanced Report button** - Green button in pump comparison for detailed scoring PDF

**✅ PHASE 4.3: SMART SEARCH & FILTERING STARTED (August 5, 2025)**
- **Advanced Filter Panel Implemented** - Collapsible filter panel with Material Design UI
- **Four Filter Categories Added**:
  - Efficiency Range (0-100%)
  - Power Consumption (0-500 kW)
  - Impeller Diameter (200-800 mm)
  - Overall Score (0-100)
- **Interactive Range Sliders** - Real-time value display as users adjust filters
- **Filter Badge Counter** - Shows number of active filters applied
- **No Results Handling** - User-friendly message when no pumps match criteria
- **Filter Actions** - Apply and Reset buttons with toast notifications

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



### 🎯 **PHASE 4: ENHANCED USER EXPERIENCE (NEXT PRIORITY)**

#### **Phase 4.1: Advanced Results Visualization**
**Objective:** Enhanced transparency and user guidance in pump selection results

**PLANNED FEATURES:**
- **Score Breakdown Display** - Show individual score components (BEP: 35/40, Efficiency: 25/30, etc.)
- **Visual Score Indicators** - Progress bars or gauges for each scoring criterion
- **Pump Comparison Table** - Side-by-side comparison of top 5 pumps with key metrics
- **Performance Zone Visualization** - Color-coded operating zones on selection results
- **Modification Indicators** - Clear visual markers for trimmed impellers or VFD requirements

#### **Phase 4.2: Enhanced PDF Reports**  
**Objective:** Professional documentation with comprehensive technical details

**PLANNED FEATURES:**
- **Executive Summary Page** - One-page overview with key selection rationale
- **Detailed Score Analysis** - Full breakdown of 100-point scoring calculation
- **Alternative Options Section** - Top 3 alternatives with comparison rationale
- **Technical Appendix** - Complete curve data, calculations, and methodology
- **QR Code Integration** - Link to interactive online version of report

#### **Phase 4.3: Smart Search & Filtering**
**Objective:** Faster pump discovery and refined selection

**PLANNED FEATURES:**
- **Advanced Filter Panel** - Filter by efficiency range, impeller size, NPSH requirements
- **Smart Search Suggestions** - Auto-complete with pump model predictions
- **Saved Searches** - Store and recall common pump selection criteria
- **Quick Actions** - "Find Similar Pumps" or "Show Larger/Smaller Options"
- **Flow/Head Range Slider** - Visual input method for specifications

### 🎯 **PHASE 5: INTELLIGENT FEATURES (FUTURE VISION)**

#### **Phase 5.1: AI-Powered Insights**
**Objective:** Leverage AI for advanced pump selection guidance

**PLANNED FEATURES:**
- **Natural Language Queries** - "Find a pump for my cooling tower with 500 GPM"
- **Predictive Maintenance Alerts** - AI analysis of operating conditions vs pump capabilities
- **Energy Optimization Suggestions** - Recommend VFD settings for optimal efficiency
- **Application-Specific Guidance** - Tailored recommendations based on industry use cases
- **Failure Mode Predictions** - Identify potential issues based on operating conditions

#### **Phase 5.2: Integration Capabilities**
**Objective:** Seamless integration with engineering workflows

**PLANNED FEATURES:**
- **API for Third-Party Integration** - RESTful API for pump selection services
- **CAD File Downloads** - 2D/3D drawings in multiple formats
- **BIM Integration** - Export pump data for building information modeling
- **Specification Sheet Generator** - Auto-generate submittal documents
- **Multi-Language Support** - Interface and reports in multiple languages

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