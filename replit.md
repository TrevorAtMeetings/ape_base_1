# APE Pumps Selection Application

## Overview

This is a Flask-based web application for pump selection and evaluation designed for APE Pumps. The application provides an intelligent pump recommendation system that analyzes site requirements and matches them with appropriate pump models from APE's catalog. It features web-based form input, pump performance analysis, interactive charts, and professional PDF report generation.

## System Architecture

The application follows a modular Flask architecture with clear separation of concerns:

### Backend Architecture
- **Flask Application**: Main web framework handling HTTP requests and routing
- **Repository Pattern**: Centralized data access through `pump_repository.py` supporting both JSON and PostgreSQL sources
- **Processing Engine**: Core pump analysis and selection logic in `pump_engine.py`
- **File Processing**: Support for SCG and TXT pump data files with batch processing capabilities
- **Session Management**: Optional session handling with fallback support
- **Chart Generation**: Both static (Matplotlib) and interactive (Plotly.js) chart generation

### Frontend Architecture
- **Template-Based UI**: Jinja2 templates for server-side rendering
- **Interactive Charts**: Plotly.js for dynamic performance curve visualization
- **Responsive Design**: Bootstrap-based styling for mobile compatibility
- **Form Handling**: Multi-step form workflow for pump selection

## Key Components

### Data Management
- **PumpRepository**: Unified data access layer supporting JSON file and PostgreSQL backends
- **Catalog Engine**: Processes pump performance curves and specifications
- **SCG Processor**: Handles authentic APE pump data format conversion
- **Data Validation**: Comprehensive validation for pump performance data

### Selection Engine
- **Site Requirements Analysis**: Processes user input for flow, head, and application requirements
- **Pump Matching Algorithm**: Intelligent scoring system for pump suitability
- **Performance Calculation**: Interpolation and extrapolation of pump curves
- **Impeller Scaling**: Affinity law calculations for optimal pump sizing

### Report Generation
- **PDF Generation**: Professional reports using WeasyPrint with embedded charts
- **Chart Embedding**: Static Matplotlib charts integrated into PDF reports
- **Template System**: Comprehensive report templates with technical analysis

### File Processing
- **SCG File Support**: Native support for APE's SCG pump data format
- **Batch Processing**: Concurrent processing of multiple pump files
- **Format Detection**: Automatic detection of JSON and SCG file formats
- **Error Handling**: Robust error reporting and validation

## Data Flow

1. **User Input**: Web form captures site requirements (flow, head, application)
2. **Data Loading**: Repository loads pump data from configured source (JSON/PostgreSQL)
3. **Selection Analysis**: Engine evaluates all pumps against requirements
4. **Performance Calculation**: Interpolates pump curves for operating point analysis
5. **Ranking**: Pumps scored and ranked by suitability
6. **Visualization**: Interactive charts generated for top selections
7. **Report Generation**: Professional PDF reports with embedded analysis

## External Dependencies

### Core Framework
- **Flask**: Web application framework
- **Gunicorn**: WSGI HTTP server for production deployment
- **psycopg2-binary**: PostgreSQL database adapter

### Data Processing
- **NumPy**: Numerical computing for pump curve analysis
- **SciPy**: Scientific computing for interpolation algorithms
- **Pandas**: Data manipulation (if extended)

### Visualization
- **Matplotlib**: Static chart generation for PDF reports
- **Plotly.js**: Interactive web-based charts

### AI Integration
- **OpenAI API**: GPT-based pump selection reasoning
- **Google Gemini**: Alternative AI model for analysis

### Document Generation
- **WeasyPrint**: PDF generation with HTML/CSS rendering
- **Jinja2**: Template engine for HTML and PDF generation

### Additional Libraries
- **python-dotenv**: Environment variable management
- **email_validator**: Input validation
- **markdown2**: Markdown processing support

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

## Changelog

- August 05, 2025: **Report Layout Reorganization Complete** - moved "Alternative Pump Options" section to appear directly below "Best Efficiency Point (BEP) Analysis" section for improved logical flow, final report structure now follows: 1.Pump Details, 2.Duty Point Requirements, 3.BEP Analysis, 4.Alternative Options, 5.Performance Charts, 6.Performance Analysis
- August 05, 2025: **Report Layout Reorganization & Near-Miss Removal** - moved "Best Efficiency Point (BEP) Analysis" section to appear directly below "Duty Point Requirements" for better logical flow, removed confusing "Near-Miss Pumps" section that showed failed pumps (poor efficiency, oversized) alongside legitimate alternatives, reports now only display properly ranked alternative pumps that meet all selection criteria
- August 05, 2025: **Phase 2.3 Engineering Guidance Features** - implemented comprehensive BEP analysis display showing % QBEP score and operating zone classification (70-120% preferred range), added visual BEP operating range indicator with color-coded zones (optimal 90-110%, good 70-90%/110-120%, marginal <70%/>120%), prominently displays impeller diameter in performance achievement summary, implemented near-miss pump analysis tracking pumps that just missed criteria (within 5% head, 35-40% efficiency, NPSH within 1m), added actionable alternatives section suggesting site adjustments for near-miss pumps with engineering tips for ±5% site flexibility
- August 05, 2025: **NPSHr Chart Display Fixed** - resolved NPSHr chart display issues including y-axis scaling (now shows tight 2.36-4.04 range instead of 0-4), implemented cubic spline interpolation for smooth mother curves between test points, removed monotonic smoothing to preserve authentic test data including non-monotonic behavior (e.g., 134mm impeller showing 3.05m dropping to 2.74m), removed debug console logging for cleaner production output
- August 05, 2025: **Phase 2.2 Algorithm Enhancement: Comprehensive Curve Evaluation** - fixed critical issue where 293 pumps were incorrectly excluded as "no performance data" when they actually HAVE data but duty points fall outside individual curve ranges, implemented comprehensive can_meet_requirements method that checks ALL impeller curves and valid modifications before exclusion, added proper exclusion categorization (flow/head outside range vs actual missing data), fixed exclusion summary display formatting (enum to string conversion), allows 10% safe extrapolation beyond tested ranges, pumps now only excluded after exhaustive evaluation of all curves and scaling methods
- August 05, 2025: **Phase 2.1 Complete: Selection Results Transparency** - implemented exclusion summary and scoring breakdown UI sections in pump reports, fixed critical chart rendering bug by correcting test_speed_rpm access from CatalogPump object, transparency features now display total pumps evaluated (386), feasible pumps count, excluded pumps breakdown by reason, and detailed scoring components (QBP proximity, efficiency, head margin, NPSH, penalties), fixed session data persistence and scoring_details mapping issues
- August 05, 2025: **Phase 1 Complete: Physical Feasibility Gate Implementation** - restructured pump selection to validate physical feasibility BEFORE scoring, implemented comprehensive exclusion tracking system with PumpEvaluation objects, updated efficiency scoring to parabolic formula (efficiency/100)² × 30 reflecting diminishing returns, added transparent exclusion summary logging showing specific reasons for pump exclusions (undertrim, overtrim, underspeed, overspeed, insufficient head, excessive head), system now follows QBP-centric approach with strict physical validation gates
- July 30, 2025: **Production deployment readiness confirmed** - completed comprehensive 6-hour development session, implemented missing admin console endpoints (/admin/upload, /api/chat/status), fixed critical data display issues in admin console to show real PostgreSQL performance data instead of "N/A" values, established strict database governance policy (no modifications to golden source data), conducted full system testing with all 6 critical endpoints operational, confirmed database health with 386 pumps/869 curves/7,043 performance points, application now production-ready with enterprise-grade capabilities
- July 30, 2025: **Admin console endpoints implemented** - added missing /admin/upload and /api/chat/status endpoints, verified 770 zero-flow points are valid shutoff head conditions (not data errors), admin console now fully functional, database analysis shows 3 pumps with incomplete metadata (preserved as-is per user request)
- July 30, 2025: **Implemented comprehensive scoring system update (100 points total)** - added NPSH scoring (15 points) with dual-mode approach for NPSHa known/unknown cases, adjusted BEP score to use squared decay function (40 points max), reduced efficiency score to 30 points, refined head margin scoring with piece-wise function allowing negative scores for >50% oversizing, updated VFD penalty to linear 1.5× speed change (max -15), improved trim penalty to 0.5× trim percentage, documented all changes in PUMP_SELECTION_METHODOLOGY.md
- July 30, 2025: **Fixed critical oversizing issue in pump selection** - implemented graduated oversizing penalties for pumps delivering >100% over required head, fixed system curve generation to show actual system requirements instead of pump delivery point, resolved issue where 400-600 pump (169.8m) was selected for 30m requirement, now correctly selects 12/14 BLE pump (33.2m) with appropriate 10% safety margin
- July 30, 2025: **Unit conversion system completed and verified working** - resolved JavaScript variable declaration conflicts, confirmed accurate conversion formulas (1 GPM = 0.227124 m³/hr, 1 ft = 0.3048 m), fixed blur-based conversion functionality in Imperial mode, implemented bidirectional value storage system, added comprehensive testing and debugging functions, system now working as intended with proper Imperial-to-Metric conversion and unit system switching
- July 30, 2025: **Critical pump selection algorithm fixes implemented** - corrected backwards impeller diameter validation logic, improved speed variation penalty system (graduated penalties instead of flat -20 points), added physical constraints validation, fixed interpolation parameter issues, reordered selection flow to try all sizing methods before validation
- July 29, 2025: Completed deployment readiness fixes - production configuration, security headers, error handling, health checks
- July 29, 2025: Added "Find Best Pump" search button that appears when essential requirements are completed
- July 29, 2025: Created comprehensive build specification document (Spec.md) in docs folder
- July 08, 2025: Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.