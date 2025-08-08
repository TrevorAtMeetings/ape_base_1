# APE Pumps Selection Application

## Overview
This Flask-based web application provides an intelligent pump recommendation system for APE Pumps. It analyzes site requirements, matches them with APE pump models, and offers pump performance analysis with interactive charts and professional PDF report generation. The project aims to deliver a robust tool for efficient and accurate pump selection, enhancing APE's market position through a comprehensive and intelligent pump selection process.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application employs a modular Flask architecture with a clear separation of concerns, supporting both backend and frontend components.

### Navigation Structure
**Main Navigation:**
- **Selection**: Primary pump selection tool (homepage) - `/`
- **Tools Menu**: Pump Comparison, Shortlist Compare, Pump Editor, AI Data Extract
- **Admin Menu**: Configuration, AI Admin, Performance Testing, Documents
- **Help Menu**: User Guide, Features, About

### Data Integrity & Validation
The system prioritizes authentic manufacturer specifications for pump performance data, specifically for Best Efficiency Point (BEP) metrics. It has a strict no-fallback policy for missing BEP data, ensuring that calculations are based on genuine information. Validation prevents artificial matches and uses pump-specific thresholds and operating envelopes based on database values.

### Enhanced Performance Testing
The system includes comprehensive BEP-centered envelope testing with statistical analysis and improved tabular display for comparison. It defines clear status legends (Match, Minor, Major) for accuracy metrics.

### AI Chatbot Enhancement
The chatbot supports natural language pump selection queries, metric-first design, template card results, and seamless integration for detailed analysis and comparison. It includes shorthand query support, `@pump` lookup with autocomplete, and flexible unit recognition. The chatbot is globally available with keyboard navigation.

### Navigation System Unification
The application utilizes a unified navigation system across all pages, resolving blueprint conflicts and template inconsistencies to ensure a consistent user experience.

### User Experience Improvements
Default views are set to "engineering view" for all pump selections, and the shortlist capacity has been increased to 10 pumps for better comparison options.

### Chart Improvements
Operating point markers are enhanced with transparent red triangles on the X-axis, crosshairs, and a small red dot at the actual operating point. Consistent X-axis ranges are maintained across engineering view charts, and hover templates provide comprehensive data.

### Methodology
The pump selection methodology separates fixed-speed (impeller trimming) from VFD (speed variation) logic. It incorporates hard safety gates for NPSH (1.5x margin) and QBP operating range (60-130%). Impeller trim is limited to 85-100% of maximum diameter. The system trusts manufacturer data if performance data exists in the database. Scoring is rebalanced, and trimmed curves are supported in the API. Envelope testing uses a curve-following methodology.

### Backend Architecture
- **Flask Framework**: Handles routing and HTTP requests.
- **Repository Pattern**: Centralized data access via `pump_repository.py`.
- **Processing Engine**: Core pump analysis and selection logic.
- **File Processing**: Support for SCG and TXT pump data files.
- **Chart Generation**: Static (Matplotlib) and interactive (Plotly.js) charts.
- **Configuration Management System**: Centralized threshold and classification management.

### Frontend Architecture
- **Template-Based UI**: Jinja2 templates for server-side rendering.
- **Dual-View System**: Engineering data sheet view and Presentation view.
- **Interactive Charts**: Plotly.js for dynamic performance curve visualization.
- **Responsive Design**: Bootstrap-based styling.
- **Form Handling**: Multi-step workflow for pump selection input.
- **Advanced Filtering**: Collapsible filter panel with interactive range sliders.

### Key Components
- **Data Management**: Unified access via `PumpRepository`, `Catalog Engine`, and `SCG Processor`.
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

## Recent Changes
### August 8, 2025 - Phase 1 Brain System Implementation Complete
- **PHASE 1 DELIVERED**: Core Brain module infrastructure now operational in shadow mode
- **ARCHITECTURE IMPLEMENTED**: Created PumpBrain class with 5 intelligence sub-modules (selection, performance, charts, validation, cache)
- **SHADOW MODE ACTIVE**: Brain runs parallel to legacy code, logging discrepancies without affecting production
- **TESTING COMPLETE**: 14 comprehensive unit tests all passing, validating Brain calculations and consistency
- **KEY CONSOLIDATIONS**: Migrated impeller scaling logic, affinity laws, and performance calculations to centralized Brain
- **MONITORING ENABLED**: Real-time metrics tracking for operations, cache hit rates, and discrepancy logging
- **FILES CREATED**: app/pump_brain.py, app/brain/ sub-modules, tests/test_pump_brain.py
- **INTEGRATION POINT**: CatalogEngine.select_pumps() now runs Brain in shadow mode for A/B comparison

### August 8, 2025 - Master Plan: Centralized Brain System Architecture
- **STRATEGIC INITIATIVE PLANNED**: Comprehensive transformation to centralized "Brain" system for all application intelligence
- **ARCHITECTURE VISION**: Single PumpBrain module consolidating selection logic, performance analysis, and chart intelligence
- **IMPLEMENTATION ROADMAP**: 8-week phased migration from distributed to centralized architecture
- **EXPECTED BENEFITS**: Elimination of calculation inconsistencies, real-time intelligence, foundation for ML integration
- **DOCUMENTATION**: Created master_plan_brain_feature.md with complete technical specifications and migration strategy

### August 8, 2025 - Critical Data Integrity Issues Identified
- **MAJOR DATABASE DISCREPANCY FOUND**: 65-200 1F pump missing manufacturer-rated 200.5mm impeller curve - database only contains 218mm maximum curve
- **Manufacturer vs Database**: Pump rated at 60 m³/hr @ 40m head with 200.5mm impeller vs database showing ~48.84m head with 218mm impeller
- **Impeller Scaling Logic Fixed**: Updated adaptive interpolation in impeller_scaling.py to match catalog_engine.py methodology
- **Root Cause of Selection Issues**: Missing authentic manufacturer curves causing incorrect head calculations and improper impeller trimming applications
- **Data Integrity Priority**: System requires complete manufacturer curve sets (all impeller diameters) not just maximum impeller curves

### August 8, 2025 - Critical Fixes: Double Transformation Bug + Adaptive Interpolation Implementation
- **MAJOR FIX: Resolved Double Data Transformation Bug**: Fixed critical issue where both backend (api.py) and frontend (charts.js) were applying affinity laws for impeller trimming, causing severely incorrect performance curves (head scaling by diameter_ratio⁴ instead of diameter_ratio²)
- **Backend Source of Truth Established**: Confirmed api.py correctly applies affinity laws; removed all duplicate transformations from frontend charts.js
- **Adaptive Interpolation Implemented**: Revolutionary improvement using all available data points with intelligent method selection (cubic ≥4 points, quadratic 3 points, linear fallback 2 points) for accurate curve representation
- **8K Pump Mathematical Validation**: Head calculation improved from 48.75m (linear) to 49.27m (cubic) at BEP flow, reducing discrepancy with 50.01m specification from 1.26m to 0.74m
- **System-Wide Performance Enhancement**: All pumps with dense performance data now benefit from superior curve fitting, especially those with ≥4 data points
- **Surgical Patch A - Spec/Curve Guard**: Only considers curves with actual performance_points data when computing min/max impeller specifications, preventing pollution from invalid curves
- **Surgical Patch B - Max Impeller Trim Enforcement**: Enforces ≤15% trim limit relative to actual maximum impeller diameter, independent of base curve selection
- **Surgical Patch C - Pump Code Normalization**: Implemented consistent whitespace/case normalization in get_pump_by_code for reliable lookup between charts and reports
- **Enhanced Data Integrity**: System validates BEP specifications against interpolated curve data, with comprehensive debug logging for troubleshooting
- **Architectural Improvement**: Frontend charts.js only renders data from backend, eliminating transformation conflicts and maintaining single source of truth

### August 7, 2025 - Quality Issues Resolution & Comparison Enhancement
- **Fixed JavaScript Errors**: Resolved `resetZoom()` function call errors by converting from object method to standalone function
- **Enhanced Show Data Functionality**: Improved toggleChartData() with better error handling and user feedback
- **Restored Comparison Page**: Fixed data structure mismatch (overall_score vs suitability_score) and restored original cost breakdown functionality
- **Added Comparison Navigation**: Verified "Add to Compare" buttons working on pump report pages with proper API integration
- **Improved User Experience**: Added explanation of "Add to Compare" feature in comparison page hero banner
- **Enhanced Cost Analysis**: Full lifecycle cost analysis with R/kWh calculations, annual costs, and 10-year financial impact comparisons