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

### 🎯 **PHASE 2: ALGORITHM EXCELLENCE (CURRENT PRIORITY)**
**Status: TEMPLATE REFACTORING COMPLETE, ALGORITHM ENHANCEMENT IN PROGRESS**

#### **Phase 2.2: Algorithm Enhancement - Comprehensive Curve Evaluation (PRIORITY)**
**Objective:** Fix premature pump exclusions and implement comprehensive evaluation system

**🔄 ACTIVE DEVELOPMENT:**
- **Problem**: Current algorithm excludes pumps when duty point falls outside ANY single curve, without evaluating ALL curves or applying affinity laws
- **Impact**: 293 pumps incorrectly excluded as "no performance data" when they actually have data but duty points fall outside individual curve ranges

**REQUIRED IMPROVEMENTS:**
1. **Comprehensive Curve Evaluation**:
   - Fix `get_best_curve_for_duty()` to evaluate ALL impeller curves before exclusion
   - Implement proper exclusion categorization system
   - Add interpolation between curves for intermediate trims
   - Allow safe extrapolation (±10%) beyond tested ranges

2. **Exclusion Categories** (instead of generic "no data"):
   - "No performance data" - only when literally no curves exist
   - "Flow outside pump capacity" - duty exceeds all curves at max trim
   - "Head outside pump envelope" - cannot achieve within limits  
   - "Excessive trim required" - would need <80% or >100% impeller
   - "Speed out of range" - would exceed 750-3600 RPM

3. **Engineering Guidance Features**:
   - Near-miss analysis ("5% more head enables 6 pumps")
   - Parallel pump suggestions for oversized duties
   - Right-of-BEP preference indicators (105-115% sweet spot)
   - Actionable alternatives when no exact match

#### **Phase 2.3: Improved Results Visualization (PLANNED)**
**Objective:** Enhanced transparency and user guidance in pump selection results

**PLANNED FEATURES:**
- Scoring heat map in comparison view
- Radar charts for pump strengths/weaknesses  
- Traffic light system for feasibility indicators
- Tooltips explaining scoring components

#### **Phase 2.4: Selection Process Visibility (PLANNED)**  
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