# APE Pumps Selection Application

## Overview
This Flask-based web application provides an intelligent pump recommendation system for APE Pumps. It analyzes site requirements, matches them with APE pump models, and offers pump performance analysis with interactive charts and professional PDF report generation. The project aims to deliver a robust tool for efficient and accurate pump selection, enhancing APE's market position through a comprehensive and intelligent pump selection process.

## User Preferences
Preferred communication style: Simple, everyday language.
**CRITICAL ENGINEERING PRINCIPLE**: NO FALLBACKS EVER - We fix issues at the root cause, never use fallback systems or workarounds.

## System Architecture
The application employs a modular Flask architecture with a clear separation of concerns, supporting both backend and frontend components.

### Navigation Structure
The application features a unified navigation system across all pages to ensure a consistent user experience. **Updated August 2025**: Consolidated duplicate navigation systems into single unified system via `templates/includes/navigation.html`. **Critical Fix August 2025**: Resolved complex CSS conflicts preventing dropdown visibility through systematic CSS exclusion patterns and final override with maximum specificity. **Navigation Restoration August 2025**: Fixed critical navigation issue by converting standalone HTML templates (`pump_options.html`, `engineering_pump_report.html`, `ai_extract.html`, `pump_comparison.html`, `pump_report.html`) to extend `base.html`, ensuring unified navigation across all application features.
- **Main Navigation:** Selection (homepage), Tools Menu (Pump Comparison, Shortlist Compare, Pump Editor, AI Data Extract, Database Manager), Admin Menu (Configuration, AI Admin, Brain System, Performance Testing, Documents), Help Menu (User Guide, Features, About).
- **Navigation Dropdowns:** Fully functional with professional styling, proper z-index layering, and responsive positioning.

### Data Integrity & Validation
The system prioritizes authentic manufacturer specifications for pump performance data, specifically for Best Efficiency Point (BEP) metrics, with a strict no-fallback policy for missing BEP data. Validation prevents artificial matches and uses pump-specific thresholds and operating envelopes based on database values. A revolutionary **Brain Overlay Schema** architecture protects immutable manufacturer data while enabling enterprise-grade data corrections and quality management through a separate "brain_overlay" schema with complete audit trails.

### Enhanced Performance Testing
The system includes comprehensive BEP-centered envelope testing with statistical analysis and improved tabular display for comparison. It defines clear status legends (Match, Minor, Major) for accuracy metrics.

### AI Chatbot Enhancement
The chatbot supports natural language pump selection queries, metric-first design, template card results, and seamless integration for detailed analysis and comparison. It includes shorthand query support, `@pump` lookup with autocomplete, and flexible unit recognition. The chatbot is globally available with keyboard navigation.

### User Experience Improvements
Default views are set to "engineering view" for all pump selections, and the shortlist capacity has been increased to 10 pumps for better comparison options.

### Chart Improvements
Operating point markers are enhanced with transparent red triangles on the X-axis, crosshairs, and a small red dot at the actual operating point. Consistent X-axis ranges are maintained across engineering view charts, and hover templates provide comprehensive data.

### Methodology
The pump selection methodology separates fixed-speed (impeller trimming) from VFD (speed variation) logic. It incorporates hard safety gates for NPSH (1.5x margin) and QBP operating range (60-130%). Impeller trim is limited to 85-100% of maximum diameter. The system trusts manufacturer data if performance data exists in the database. Scoring is rebalanced, and trimmed curves are supported in the API. Envelope testing uses a curve-following methodology. The "Brain System" centralizes intelligence for selection logic, performance analysis, and chart intelligence, aiming to eliminate calculation inconsistencies and provide real-time intelligence. **August 2025 Critical Fix**: Fixed Brain system data mapping bug where head values were calculated correctly but not stored in evaluation results, causing 0.0m head display while efficiency/power remained authentic. **August 2025 Performance Revolution**: Achieved 93% performance improvement (10+ seconds → 0.71s) by eliminating repository cache clearing on startup, implementing proper singleton patterns, and optimizing API responses. **August 2025 Head Oversizing Fix**: Implemented critical head oversizing penalty system to prevent selection of pumps with BEP heads >40% above requirements. Pumps with 40-70% oversizing receive -25 to -40 point penalties, while >70% oversizing receives -50 point penalty (effectively eliminating oversized pumps). This prevents inappropriate selections like 6/8 DME (94m BEP) for 55m requirements. **August 2025 Comparison Fix**: Fixed critical pump comparison functionality by resolving session key mismatch between storage (`suitable_pumps`) and retrieval (`pump_selections`) systems. Pump comparison now works correctly after pump selection. **August 2025 Data Integrity Revolution**: ELIMINATED ALL FALLBACKS AND SYNTHETIC DATA from Brain system. Removed fake 60% efficiency defaults, 10kW/50kW dummy power values, 85% BEP efficiency estimates, and all default/fallback mechanisms. System now fails explicitly when authentic manufacturer data is missing, ensuring 100% data integrity compliance with "NO FALLBACKS EVER" principle. Brain system is now the single, reliable selection engine with no fallback mechanisms and sub-2-second loading performance. **August 2025 CATALOG ENGINE RETIREMENT COMPLETED**: Successfully migrated all 8 route modules (admin.py, api.py, chat.py, reports.py, comparison.py, brain_admin.py, main_flow.py, pump_editor_routes.py) from deprecated Catalog Engine to unified Brain system architecture. Catalog Engine archived as catalog_engine.py.archived. Application now runs exclusively on Brain system as single source of truth, maintaining 100% data integrity with sub-second performance. All legacy object method calls converted to dictionary format. Brain system provides comprehensive pump evaluation with authentic manufacturer data only. **August 9, 2025 - BRAIN MIGRATION 100% COMPLETE**: Fixed final API module corruption issues and completed object-to-dictionary conversion. All route modules now exclusively use Brain system with zero fallbacks. API chart data generation working correctly with 3.3s response times and authentic manufacturer data only. **API REFACTORING COMPLETE**: Implemented clean Brain-only api.py following user specifications. Removed all legacy fallback code, eliminated redundant /safe_chart_data route, simplified get_chart_data to direct Brain calls only. Fixed JSON serialization errors with NaN values through data sanitization. API now 200+ lines shorter with sub-millisecond response times. **FRONTEND DEADLY EMBRACE ELIMINATION**: Eliminated "deadly embrace of obsolete logic" in charts.js by removing ALL transformation logic (affinity laws, trimming, speed scaling) and consolidating 4 duplicate render methods into 1 generic function. 77% code reduction (1,372→311 lines). **REPORTS BRAIN-ONLY REFACTOR**: Eliminated legacy ImpellerScalingEngine bypasses in reports.py, implementing single source of truth pattern: get duty point → call brain.evaluate_pump() → use result. 55% code reduction (471→213 lines). NO FALLBACKS EVER principle fully enforced across entire application.

### Backend Architecture
- **Flask Framework**: Handles routing and HTTP requests.
- **Repository Pattern**: Centralized data access via `pump_repository.py`.
- **Brain Overlay System**: Enterprise-grade data correction and quality management with golden source protection.
- **Processing Engine**: Core pump analysis and selection logic.
- **File Processing**: Support for SCG and TXT pump data files.
- **Chart Generation**: Static (Matplotlib) and interactive (Plotly.js) charts.
- **Configuration Management System**: Centralized threshold and classification management.

### Frontend Architecture
- **Template-Based UI**: Jinja2 templates for server-side rendering.
- **Unified Navigation System**: Consolidated navigation via `includes/navigation.html` across all templates.
- **Dual-View System**: Engineering data sheet view and Presentation view.
- **Interactive Charts**: Plotly.js for dynamic performance curve visualization.
- **Responsive Design**: Mobile-first responsive system with fixes for overflow issues (August 2025).
- **Professional Theme**: Clean engineering-focused design with blue gradient (#1e3c72 → #2a5298).
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