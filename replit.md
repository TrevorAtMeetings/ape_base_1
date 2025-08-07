# APE Pumps Selection Application

## Overview
This Flask-based web application provides an intelligent pump recommendation system for APE Pumps. It analyzes site requirements, matches them with APE pump models, and offers pump performance analysis with interactive charts and professional PDF report generation. The project aims to deliver a robust tool for efficient and accurate pump selection, enhancing APE's market position through a comprehensive and intelligent pump selection process.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
The application employs a modular Flask architecture with a clear separation of concerns, supporting both backend and frontend components.

### Navigation Structure (Updated August 2025)
**Main Navigation:**
- **Selection**: Primary pump selection tool (homepage) - `/`
- **Tools Menu**: 
  - Pump Comparison: Compare multiple pumps side-by-side - `/pump_comparison`
  - Shortlist Compare: Compare shortlisted pumps from selection - `/shortlist_comparison`
  - Pump Editor: Manual pump data entry tool - `/pump_editor`
  - AI Data Extract: Extract pump data from documents - `/ai_extract`
- **Admin Menu**:
  - Configuration: System configuration and profiles - `/admin_config`
  - AI Admin: Manage AI knowledge base - `/admin/ai`
  - Performance Testing: Database vs UI validation tool - `/admin/testing`
  - Documents: Document library - `/admin`
- **Help Menu**:
  - User Guide: Application help guide - `/guide`
  - Features: External features page (external link)
  - About: Application information - `/about`

### Recent Major Update - CRITICAL Data Integrity Fixes (August 7, 2025)

**CRITICAL DATA INTEGRITY OVERHAUL - PHASE 2 COMPLETE**:
- **Eliminated All Fallback Logic**: Removed dangerous UI performance fallbacks that created artificial agreement between database and UI calculations
- **Fixed BEP Field Mapping**: Corrected database field mapping to use authentic manufacturer specifications (bep_flow_m3hr, bep_head_m) instead of missing fields
- **Strict No-Fallback Policy**: System now fails clearly when authentic BEP data is missing instead of using estimated/interpolated values
- **Artificial Match Prevention**: Added validation to prevent counting None=None as "exact matches" - only real data comparisons are considered valid
- **Authentic Data Enforcement**: Envelope testing now anchors to authentic manufacturer BEP specifications (12.33 m³/hr @ 23.45m) instead of curve-estimated values (10 m³/hr @ 13.6m)
- **Clear Failure Reporting**: UI calculation failures now report as 'ui_calculation_failed' instead of falling back to database interpolation methods

**CRITICAL BUG FIXES (August 7, 2025)**:
- **Status Case Mismatch Fixed**: Corrected return values from 'MATCH'/'MINOR'/'MAJOR' to 'match'/'minor_diff'/'major_diff' to fix completely broken accuracy statistics
- **Default Value Contamination Removed**: Eliminated hardcoded defaults like trim_percent=100 and method assumptions that injected fake data into validation
- **Invalid Power Comparisons Removed**: Discovered database contains NO authentic power data - removed all power validation to prevent false accuracy metrics 
- **Pump-Specific Thresholds Implemented**: Replaced universal hardcoded thresholds with pump-specific logic based on max_power_kw specifications
- **Authentic Operating Envelopes**: Replaced fixed BEP percentages (60-140%) with authentic pump curve operating ranges from database
- **Real Operating Regions**: Removed fake "Part Load/Optimal/Overload" assumptions, now uses authentic flow ranges from pump curves

**PHASE 3 - Trust Manufacturer Data (August 7, 2025)**:
- **Root Cause Identified**: UI calculations failing because of overly restrictive validation gates that don't trust manufacturer data
- **QBP Gate Conflict**: Test points at 137% BEP are within manufacturer's documented range but exceed 130% QBP gate limit
- **Solution Implemented**: Modified physical capability validation to trust manufacturer data ranges with minimal extrapolation margins
- **Interpolation Enhanced**: Enabled edge value extrapolation for manufacturer-provided operating ranges
- **Core Principle**: If data exists in database = manufacturer says it's viable for operation

### Recent Major Update - Enhanced Performance Testing with Table Format (August 7, 2025)

**Enhanced Test Coverage Implementation**:
- **Phase 1 Complete**: BEP-centered envelope testing with systematic flow percentages (9 test points)
- **BEP-Anchored Approach**: 4 points decreasing both flow and head (60%, 70%, 80%, 90%), BEP (100%), 4 points increasing both flow and head (110%, 120%, 130%, 140%)
- **Statistical Analysis**: Comprehensive accuracy metrics, error distribution, and confidence intervals
- **Improved Table Display**: Professional comparison format with clear status explanations and testing insights
- **Status Legend Integration**: Clear definitions for Match (≤2% efficiency, ≤0.5kW power), Minor (2-5%, 0.5-2kW), Major (>5%, >2kW)
- **Enhanced Summary Statistics**: Percentage breakdowns and acceptable accuracy metrics with validation explanations

### Recent Major Update - Navigation System Unification (August 7, 2025)
**CRITICAL Navigation Architecture Overhaul**:
- **Resolved Blueprint Conflicts**: Removed duplicate `reports_bp` registration by eliminating dead code (`reports_old.py`)
- **Unified Navigation System**: Converted all pages to use single navigation architecture instead of conflicting dual systems
- **Template System Consolidation**: Fixed hybrid templates (input_form.html, pump_options.html) that were showing double navigation bars
- **Route Reference Standardization**: All unified navigation now uses Flask `url_for()` instead of hardcoded paths for maintainability
- **Template Block Cleanup**: Removed orphaned Jinja2 template blocks causing rendering errors
- **Consistent Navigation Experience**: All pages now follow unified navigation design patterns with proper dropdown styling

**User Experience Improvements (August 7, 2025)**:
- **Engineering View Default**: Changed all pump selections (main results and shortlist) to default to engineering view instead of presentation view
- **Expanded Shortlist Capacity**: Increased shortlist limit from 3 to 10 pumps for better comparison options when available
- **Comprehensive Limit Updates**: Updated all backend validation, frontend JavaScript, session storage, and report generation to support 10-pump shortlists

**Chart Improvements (August 7, 2025)**:
- Fixed operating point markers to use transparent red triangles positioned at X-axis (Y=0) pointing upward
- Triangle now sits on the X-axis with tip pointing toward the operating point intersection
- Added both vertical (flow) and horizontal (value) red dotted reference lines forming crosshairs
- Small red dot added at actual operating point for visual clarity
- Ensured consistent X-axis ranges across engineering view charts for proper comparison
- Enhanced hover templates with comprehensive pump performance data including BEP position

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