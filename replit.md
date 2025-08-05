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
**✅ CRITICAL ALGORITHM FIXES COMPLETED**
- Fixed pump selection priority logic bug (impeller trimming now properly prioritized)
- Fixed impeller trimming calculation logic (now calculates actual optimal sizes)
- Enhanced smart trimming decisions with proper affinity law implementation
- Added comprehensive logging for transparency in selection methodology

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

**🎯 PHASE 2.3 OBJECTIVES (NEXT BUILD):**

**Primary Goals:**
1. **Extend Extrapolation Limits**: 10% → 15-20% for safe engineering operation
2. **Cross-Curve Optimization**: Smart curve selection before trimming analysis
3. **Comprehensive Evaluation**: Try ALL methods before exclusion
4. **Enhanced Logging**: Visibility into evaluation decisions and near-misses

**Technical Implementation:**
- Modify `can_meet_requirements()` extrapolation bounds
- Add smart curve ranking based on duty point proximity
- Implement fallback evaluation chain: direct → best-curve-trim → multi-curve-speed → combined
- Add detailed exclusion reasons with engineering guidance

**Expected Results:**
- Reduce false exclusions from 293 to <50 pumps
- Provide actionable alternatives for excluded pumps
- Maintain engineering safety while maximizing selection options



#### **Phase 2.4: Improved Results Visualization (PLANNED)**
**Objective:** Enhanced transparency and user guidance in pump selection results

**PLANNED FEATURES:**
- Scoring heat map in comparison view
- Radar charts for pump strengths/weaknesses  
- Traffic light system for feasibility indicators
- Tooltips explaining scoring components

#### **Phase 2.5: Selection Process Visibility (PLANNED)**  
**Objective:** Complete transparency in selection methodology

**PLANNED FEATURES:**
- "Show Selection Process" button with detailed breakdown
- Total pumps evaluated counter
- Exclusion statistics by reason
- Score distribution histogram

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