# APE Pumps Selection Application

## Overview
This Flask-based web application provides an intelligent pump recommendation system for APE Pumps. It analyzes site requirements, matches them with APE pump models, and offers pump performance analysis with interactive charts and professional PDF report generation. The project aims to deliver a robust tool for efficient and accurate pump selection, enhancing APE's market position through a comprehensive and intelligent pump selection process.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application employs a modular Flask architecture with a clear separation of concerns, supporting both backend and frontend components.

### Navigation Structure (Updated August 2025)
**Main Navigation:**
- **Selection**: Primary pump selection tool (homepage)
- **Tools Menu**: 
  - Pump Comparison: Compare multiple pumps side-by-side
  - Shortlist Compare: Compare shortlisted pumps from selection
  - Pump Editor: Manual pump data entry tool
  - AI Data Extract: Extract pump data from documents
  - Database Manager: View and manage pump database
- **Admin Menu**:
  - Configuration: System configuration and profiles
  - AI Admin: Manage AI knowledge base
  - Documents: Document library
  - AI Console: Interactive AI chat console
- **Help Menu**:
  - User Guide: Application help guide
  - Features: External features page
  - About: Application information

### Recent Major Update - Methodology v6.0 (August 2025)
**CRITICAL**: New engineering methodology developed based on expert feedback identifying fundamental flaws in v5.0 approach. Key architectural changes required:
- **Algorithm Separation**: Fixed-speed (impeller trimming) completely separated from VFD (speed variation) logic
- **Hard Safety Gates**: NPSH and QBP operating range implemented as pass/fail filters before scoring
- **Rebalanced Scoring**: 85-point system with NPSH removed from ranking, power-based tie-breaking added
- **Chart Display Fix**: Must show trimmed curves instead of maximum impeller curves

### Backend Architecture
- **Flask Framework**: Handles routing and HTTP requests.
- **Repository Pattern**: Centralized data access via `pump_repository.py`, supporting JSON and PostgreSQL.
- **Processing Engine**: Core pump analysis and selection logic in `pump_engine.py`.
- **File Processing**: Support for SCG and TXT pump data files, including batch processing.
- **Chart Generation**: Capabilities for both static (Matplotlib) and interactive (Plotly.js) charts.
- **Configuration Management System**: Centralized threshold and classification management with dynamic status determination, helper functions, and environment-based configuration.

### Frontend Architecture
- **Template-Based UI**: Jinja2 templates for server-side rendering with dynamic configuration.
- **Dual-View System**: Engineering data sheet view (industry-standard format) and Presentation view (modern UI with visual charts).
- **Interactive Charts**: Plotly.js for dynamic performance curve visualization, displayed one per row for easy sequential review.
- **Responsive Design**: Bootstrap-based styling ensures mobile compatibility.
- **Form Handling**: Multi-step workflow for pump selection input.
- **Advanced Filtering**: Collapsible filter panel with interactive range sliders for efficiency, power, impeller diameter, and overall score.

### Key Components
- **Data Management**: Unified access via `PumpRepository`, `Catalog Engine` for processing performance curves, and `SCG Processor` for authentic APE data conversion with validation.
- **Selection Engine**: Analyzes user input (flow, head, application) using intelligent scoring algorithms, performs curve interpolation/extrapolation, and applies affinity law for impeller scaling. **v6.0 UPDATE**: Now focuses exclusively on fixed-speed pumps with impeller trimming, implements hard safety gates (QBP 60-130% range, NPSH 1.5x margin), and uses power consumption as tie-breaker for similar scores.
- **Report Generation**: Professional PDF reports using WeasyPrint, embedding static Matplotlib charts, comprehensive analysis, scoring breakdowns, and detailed technical information via Jinja2 templates.
- **File Processing**: Native support for APE's SCG format, with batch processing, automatic format detection, and robust error handling.

### System Design Choices
- **Modular Flask Architecture**: Ensures maintainability and scalability.
- **Repository Pattern**: Decouples data access logic from business logic.
- **Comprehensive Algorithm**: Prioritizes impeller trimming over speed scaling and evaluates all curves with all methods before exclusion, using industry-standard extrapolation and modification ranges.
- **Admin Configuration System**: Allows for dynamic threshold and scoring weight configuration through a dedicated UI with application profiles and an audit trail.
- **Enhanced PDF Reports**: Provide detailed scoring breakdowns, performance charts, and comprehensive technical information.

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