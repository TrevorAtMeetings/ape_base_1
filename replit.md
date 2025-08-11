# APE Pumps Selection Application

## Overview
This Flask-based web application provides an intelligent pump recommendation system for APE Pumps. It analyzes site requirements, matches them with APE pump models, and offers pump performance analysis with interactive charts and professional PDF report generation. The project aims to deliver a robust tool for efficient and accurate pump selection, enhancing APE's market position through a comprehensive and intelligent pump selection process.

## User Preferences
Preferred communication style: Simple, everyday language.
**CRITICAL ENGINEERING PRINCIPLE**: NO FALLBACKS EVER - We fix issues at the root cause, never use fallback systems or workarounds. This principle is now comprehensively enforced throughout the Brain system with all fallback mechanisms, workarounds, and synthetic data generation completely removed.

## System Architecture
The application employs a modular Flask architecture with a clear separation of concerns, supporting both backend and frontend components.

### Navigation Structure
The application features a unified navigation system across all pages to ensure a consistent user experience with main navigation, tools, admin, and help menus, all featuring functional dropdowns and a professional breadcrumb system.

### Data Integrity & Validation
The system prioritizes authentic manufacturer specifications for pump performance data with a strict no-fallback policy for missing data. Validation prevents artificial matches and uses pump-specific thresholds. A "Brain Overlay Schema" protects immutable manufacturer data while enabling enterprise-grade data corrections and quality management with audit trails. 

**CRITICAL BUG FIXES COMPLETED (Aug 2025)**:
- Repository data loading bug fixed - all 369 pumps with performance curves now properly connected to Brain system
- **Interpolation sorting bug fixed** - resolved scipy interpolation failures caused by unsorted flow data that was returning NaN values and causing silent pump rejections
- **Database field mapping corrected** - fixed min_impeller_mm/max_impeller_mm to use correct database column names min_impeller_diameter_mm/max_impeller_diameter_mm
- **QBEP calculation restored** - pump selection scoring now works correctly with authentic BEP data from specifications table
- Power data handling improved with proper hydraulic calculations from authentic manufacturer data
- NPSH interpolation corrected to use sorted data for accurate results
- **Chart API JSON serialization fixed** - robust handling of NumPy booleans from Brain calculations prevents 500 errors
- **Pump sorting functionality restored** - fixed JavaScript selectors and data attribute mapping for proper result sorting
- **PUMP LIST API FULLY RESTORED** - Fixed critical API issue returning 386 pumps instead of 0 pumps
- **PUMP COMPARISON SYSTEM REFACTORED** - Completely Brain-only architecture with NO FALLBACKS EVER implemented
- **CONFIGURATION MANAGEMENT SYSTEM RESTORED** - Fixed blueprint registration issues, Configuration Management now accessible at /admin/config
- **AUTOCOMPLETE SEARCH API FIXED** - Resolved JSON parsing errors in Performance Testing interface, autocomplete now returns proper object format with pump_code and pump_type
- **BEP DATA CONSISTENCY FIXED (Aug 11, 2025)** - Critical fix eliminating mixed BEP data sources. Legacy curve-derived efficiency (84.2%) replaced with authentic manufacturer specifications (84.8%) when operating near BEP flow. Brain performance analysis now prioritizes authentic BEP efficiency within 15% of BEP flow, ensuring single source of truth for all BEP calculations.
- **ENHANCED DIAMETER TRIMMING CALCULATIONS (Aug 11, 2025)** - Implemented direct affinity law formula D₂ = D₁ × sqrt(H₂/H₁) replacing iterative testing method. Provides mathematically precise, efficient diameter calculations with enhanced validation and verification steps. Includes comprehensive debug logging and maintains industry-standard 85-100% trim limits (15% maximum trim, non-negotiable). Pumps requiring more than 15% trim are correctly rejected.
- **LEGACY METHOD DEPRECATION (Aug 11, 2025)** - Removed deprecated `_find_required_diameter_affinity_law` iterative method after validation period. The enhanced `_calculate_required_diameter_direct` method now serves as the sole diameter calculation engine, reducing technical debt and eliminating potential calculation inconsistencies.
- **TUNABLE PHYSICS ENGINE IMPLEMENTATION (Aug 11, 2025)** - Implemented enterprise-grade configuration-driven physics model for BEP migration calculations. Replaced hardcoded exponents (flow: 1.2, head: 2.2, efficiency: 0.1) with dynamically loaded calibration factors from AdminConfigService. Enables no-code tuning of core Brain intelligence through admin interface, supporting profile-based experimentation and full audit trails. PerformanceAnalyzer now uses dependency injection to access calibration factors, maintaining clean architecture separation.
- **INTELLIGENT CURVE SELECTION SYSTEM (Aug 11, 2025)** - Fixed critical issue where pumps with target head below largest curve capability were incorrectly rejected. Algorithm now intelligently selects optimal impeller curves when target head is significantly lower than largest curve output, enabling proper selection of previously excluded pumps like 8/8 DME for 500 m³/hr @ 65m requirements.
- **RESEARCH-BASED PHYSICS ENHANCEMENT (Aug 11, 2025)** - Major upgrade to Brain physics modeling based on industrial trimming research. Implemented trim-dependent affinity law exponents (2.8-3.0 for small trims <5%, 2.0-2.2 for large trims), research-based efficiency penalties (0.15-0.25 for volute pumps, 0.4-0.5 for diffuser pumps using formula Δη = ε(1-d2'/d2)), NPSH degradation validation for heavy trimming >10% with 15% penalty factor, and enhanced calibration factor system with 9 new tunable parameters. Physics model now accurately reflects industry standards and pump trimming behavior documented in technical literature.
- **"NO FALLBACKS EVER" ENFORCEMENT COMPLETED (Aug 11, 2025)** - Comprehensively removed all fallback mechanisms, workarounds, and synthetic data generation from Brain system. AI analysis now requires proper API keys (no engineering fallbacks), missing data defaults eliminated (pumps rejected instead), performance calculation fallback chains removed (explicit PerformanceError raised), exception bypassing fixed (no silent None returns), and hydraulic approximation methods disabled. System now operates exclusively with authentic manufacturer data, enforcing strict data integrity at all levels.
- All Brain system components now fully operational with complete performance calculations and accurate scoring

### Enhanced Performance Testing
Comprehensive Best Efficiency Point (BEP)-centered envelope testing is included with statistical analysis and improved tabular display. It defines clear status legends (Match, Minor, Major) for accuracy metrics. A critical head oversizing penalty system prevents selection of pumps with BEP heads significantly above requirements.

### AI Chatbot Enhancement
The chatbot supports natural language pump selection queries, metric-first design, template card results, and seamless integration for detailed analysis and comparison. It includes shorthand query support, `@pump` lookup with autocomplete, and flexible unit recognition.

### Administrative Feature Toggle System
Comprehensive admin control system with database-backed feature toggles for managing AI chatbot, performance testing, data quality tools, and other administrative features. Features are organized by category (AI, Admin, Features, System) with real-time status management, professional admin interface, and API endpoints for programmatic control.

### User Experience Improvements
Default views are set to "engineering view" for all pump selections, and the shortlist capacity has been increased to 10 pumps. Operating point markers are enhanced on charts with transparent red triangles, crosshairs, and a small red dot. Consistent X-axis ranges are maintained, and hover templates provide comprehensive data.

### Methodology
The pump selection methodology separates fixed-speed (impeller trimming) from VFD (speed variation) logic. It incorporates hard safety gates for NPSH (1.5x margin) and QBP operating range (60-130%). Impeller trim is limited to 85-100% of maximum diameter. The system trusts manufacturer data if performance data exists in the database. The "Brain System" centralizes intelligence for selection logic, performance analysis, and chart intelligence, eliminating calculation inconsistencies and providing real-time intelligence with sub-second performance. The application runs exclusively on the Brain system as the single source of truth, with all legacy systems retired.

### Backend Architecture
- **Flask Framework**: Handles routing and HTTP requests.
- **Repository Pattern**: Centralized data access.
- **Brain Overlay System**: Enterprise-grade data correction and quality management with golden source protection.
- **Processing Engine**: Core pump analysis and selection logic.
- **File Processing**: Support for SCG and TXT pump data files.
- **Chart Generation**: Static (Matplotlib) and interactive (Plotly.js) charts.
- **Configuration Management System**: Centralized threshold and classification management.

### Frontend Architecture
- **Template-Based UI**: Jinja2 templates for server-side rendering.
- **Unified Navigation System**: Consolidated navigation for consistency.
- **Dual-View System**: Engineering data sheet view and Presentation view.
- **Interactive Charts**: Plotly.js for dynamic performance curve visualization.
- **Responsive Design**: Mobile-first responsive system.
- **Professional Theme**: Clean engineering-focused design with a blue gradient.
- **Form Handling**: Multi-step workflow for pump selection input.
- **Advanced Filtering**: Collapsible filter panel with interactive range sliders.

### Key Components
- **Data Management**: Unified access via `PumpRepository` and `SCG Processor`.
- **Selection Engine**: Analyzes user input using intelligent scoring algorithms, performs curve interpolation/extrapolation, and applies affinity law. Focuses on fixed-speed pumps with impeller trimming, hard safety gates, and power consumption as a tie-breaker.
- **Report Generation**: Professional PDF reports using WeasyPrint, embedding static Matplotlib charts, comprehensive analysis, and scoring breakdowns.
- **File Processing**: Native support for APE's SCG format with batch processing and error handling.

### System Design Choices
- **Modular Flask Architecture**: Ensures maintainability and scalability.
- **Repository Pattern**: Decouples data access logic from business logic.
- **Comprehensive Algorithm**: Prioritizes impeller trimming and evaluates all curves with all methods.
- **Admin Configuration System**: Allows for dynamic threshold and scoring weight configuration.
- **Enhanced PDF Reports**: Provide detailed scoring breakdowns and performance charts.

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