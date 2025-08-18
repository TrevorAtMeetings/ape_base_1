# APE Pumps Selection Application

## Overview
This Flask-based web application provides an intelligent pump recommendation system for APE Pumps. It analyzes site requirements, matches them with APE pump models, and offers pump performance analysis with interactive charts and professional PDF report generation. The project aims to deliver a robust tool for efficient and accurate pump selection, enhancing APE's market position through a comprehensive and intelligent pump selection process.

## User Preferences
Preferred communication style: Simple, everyday language.
**CRITICAL ENGINEERING PRINCIPLE**: NO FALLBACKS EVER - We fix issues at the root cause, never use fallback systems or workarounds.

## System Architecture
The application employs a modular Flask architecture with a clear separation of concerns, supporting both backend and frontend components. It enforces a strict "no fallback" policy for missing or ambiguous data, relying exclusively on authentic manufacturer specifications.

### UI/UX Decisions
The application features a unified navigation system for consistent user experience, including main navigation, tools, admin, and help menus with dropdowns and a professional breadcrumb system. Default views are "engineering view" for pump selections, with an increased shortlist capacity of 10 pumps. Operating point markers on charts are enhanced with transparent red triangles, crosshairs, and a small red dot. X-axis ranges are consistent, and hover templates provide comprehensive data. The design is clean, engineering-focused, with a blue gradient theme and a mobile-first responsive system.

### Technical Implementations
The core system, referred to as the "Brain System," centralizes all intelligence for pump selection logic, performance analysis, and chart generation, ensuring a single source of truth and real-time intelligence. It operates exclusively on authentic manufacturer data.

Key technical decisions include:
- **Data Integrity**: Prioritizes authentic manufacturer specifications with a strict no-fallback policy for missing data. A "Brain Overlay Schema" protects immutable manufacturer data while enabling enterprise-grade data corrections.
- **Performance Analysis**: Comprehensive Best Efficiency Point (BEP)-centered envelope testing with statistical analysis and clear status legends (Match, Minor, Major). Includes a critical head oversizing penalty system.
- **Physics Engine**: Implements a tunable, configuration-driven physics model for BEP migration calculations and polymorphic physics models with pump-type-specific affinity law exponents.
- **Diameter Trimming**: Uses a direct affinity law formula for precise and efficient diameter calculations with strict validation and 15% maximum trim limits.
- **Curve Selection**: Intelligently selects optimal impeller curves, even when target head is significantly lower than largest curve output.
- **Backend Architecture**: Utilizes Flask, Repository Pattern for data access, Brain Overlay System for data quality, a Processing Engine for core logic, and supports SCG/TXT file processing.
- **Frontend Architecture**: Employs Jinja2 templates, a dual-view system (engineering and presentation), Plotly.js for interactive charts, multi-step form handling, and advanced filtering.
- **Report Generation**: Professional PDF reports using WeasyPrint, embedding static Matplotlib charts, comprehensive analysis, and scoring breakdowns.

### Feature Specifications
- **AI Chatbot**: Supports natural language pump selection queries, metric-first design, template card results, and seamless integration for detailed analysis. Includes shorthand query support, `@pump` lookup with autocomplete, and flexible unit recognition.
- **Administrative Feature Toggle System**: A config-based architecture using `config/features.json` for version-controllable feature management, organized by category (AI, Admin, Features, System).
- **Pump Selection Methodology**: Separates fixed-speed (impeller trimming) from VFD (speed variation) logic. Incorporates hard safety gates for NPSH (1.5x margin) and QBP operating range (60-130%). Impeller trim is limited to 85-100% of maximum diameter.

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