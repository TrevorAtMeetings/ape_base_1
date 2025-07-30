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

- July 30, 2025: **Critical pump selection algorithm fixes implemented** - corrected backwards impeller diameter validation logic, improved speed variation penalty system (graduated penalties instead of flat -20 points), added physical constraints validation, fixed interpolation parameter issues, reordered selection flow to try all sizing methods before validation
- July 29, 2025: Completed deployment readiness fixes - production configuration, security headers, error handling, health checks
- July 29, 2025: Added "Find Best Pump" search button that appears when essential requirements are completed
- July 29, 2025: Created comprehensive build specification document (Spec.md) in docs folder
- July 08, 2025: Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.