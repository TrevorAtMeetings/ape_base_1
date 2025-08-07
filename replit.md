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
### August 7, 2025 - Show Data Enhancement & Issues Resolution
- **Enhanced Show Data Functionality**: Implemented comprehensive data display for presentation page with pump specifications, performance metrics, and impeller details
- **Fixed Template Syntax Issues**: Resolved 40 LSP diagnostics by simplifying CSS/JS implementation, reduced to 32 diagnostics
- **Created Issues Log**: Comprehensive forensic analysis documented in `Docs/issues_log_2025_08_07.md`
- **Verified Application State**: Confirmed main pump selection flow functional, charts rendering correctly, database integration stable
- **Identified Critical Logic Issues**: Documented existing impeller scaling and validation issues requiring future attention