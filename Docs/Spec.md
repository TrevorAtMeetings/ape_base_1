# APE Pumps Selection Application - Build Specification

## Project Overview

**Project Name**: APE Pumps Selection Application  
**Type**: Flask Web Application  
**Version**: 1.0.0  
**Author**: APE Pumps  
**Purpose**: AI-powered pump selection and evaluation system with professional PDF reporting capabilities

The application provides an intelligent pump recommendation system that analyzes site requirements and matches them with appropriate pump models from APE's catalog. It features web-based form input, pump performance analysis, interactive charts, and professional PDF report generation.

## Build System Configuration

### Development Environment
- **Platform**: Replit Cloud Development Platform
- **Primary Language**: Python 3.11
- **Package Manager**: UV (Unified Python Package Manager)
- **Database**: PostgreSQL 16

### Build Tools & Package Management
- **Package Configuration**: `pyproject.toml` with UV lock file (`uv.lock`)
- **Dependencies Management**: UV package manager for Python dependencies
- **Environment Configuration**: `.env` file for development settings
- **Replit Configuration**: `.replit` file for platform-specific settings

### Build Process
The application uses a streamlined build process optimized for Replit:

1. **Dependency Resolution**: UV resolves and locks dependencies from `pyproject.toml`
2. **Environment Setup**: Environment variables loaded from `.env` file
3. **Database Initialization**: PostgreSQL database auto-configured via Replit modules
4. **Application Startup**: Flask application runs via `main.py` entry point

## Architecture Overview

### Application Structure
```
├── app/                          # Main application package
│   ├── __init__.py              # Flask app initialization and configuration
│   ├── route_modules/           # Modular route handlers
│   ├── data_models.py           # Data structures and models
│   ├── pump_repository.py       # Data access layer
│   ├── catalog_engine.py        # Pump analysis engine
│   ├── pdf_generator.py         # Report generation
│   ├── scg_processor.py         # SCG file processing
│   └── static/                  # Frontend assets
├── templates/                   # Jinja2 HTML templates
├── static/                      # Static web assets (CSS, JS)
├── tests/                       # Test suite
├── main.py                      # Application entry point
├── pyproject.toml              # Project configuration and dependencies
└── uv.lock                     # Locked dependency versions
```

### Core Components

#### Backend Architecture
- **Flask Application**: Main web framework with modular blueprint structure
- **Repository Pattern**: Unified data access supporting JSON and PostgreSQL backends
- **Processing Engine**: Core pump analysis and selection algorithms
- **Session Management**: Optional session handling with secure fallback
- **File Processing**: Support for SCG and TXT pump data formats

#### Frontend Architecture
- **Template System**: Server-side rendering with Jinja2 templates
- **Interactive Charts**: Plotly.js for dynamic performance visualizations
- **Responsive Design**: Bootstrap-based responsive UI components
- **Form Workflow**: Multi-step pump selection process

## Dependencies

### Core Framework Dependencies
```toml
flask = ">=3.1.1"                    # Web application framework
gunicorn = ">=23.0.0"               # WSGI HTTP server for production
werkzeug = ">=3.1.3"               # WSGI toolkit (Flask dependency)
flask-sqlalchemy = ">=3.1.1"       # Database ORM integration
psycopg2-binary = ">=2.9.10"       # PostgreSQL adapter
```

### Data Processing & Analysis
```toml
numpy = ">=2.2.6"                   # Numerical computing for pump calculations
scipy = ">=1.15.3"                  # Scientific computing for interpolation
matplotlib = ">=3.10.3"            # Static chart generation for PDFs
```

### AI Integration
```toml
openai = ">=1.84.0"                 # OpenAI GPT integration for analysis
google-generativeai = ">=0.8.5"    # Google Gemini AI model support
```

### Document Generation
```toml
weasyprint = ">=65.1"              # PDF generation from HTML/CSS
markdown2 = ">=2.5.3"              # Markdown processing support
```

### Utility Libraries
```toml  
requests = ">=2.32.3"              # HTTP client for external API calls
email-validator = ">=2.2.0"        # Input validation utilities
trafilatura = ">=2.0.0"            # Web content extraction (if needed)
```

### Development & Testing
```toml
pytest = ">=8.4.0"                 # Testing framework
```

## Build Configuration Files

### Primary Configuration Files

#### `pyproject.toml`
- Project metadata and dependency specifications
- UV package manager configuration
- PyTorch CPU index configuration for ML dependencies
- Build system requirements

#### `uv.lock`
- Locked dependency versions for reproducible builds
- Platform-specific wheel selections
- Dependency resolution graph

#### `.replit`
- Replit platform configuration
- Module dependencies (web, python-3.11, postgresql-16)
- Nix packages for system dependencies
- Deployment configuration for autoscale deployment
- Workflow configuration for development server

#### `.env`
- Development environment variables
- Flask configuration settings
- API keys and secrets (development)

### Database Configuration

#### `database_schema.sql`
- PostgreSQL database schema definition
- Table structures for pump data, specifications, and performance curves
- Indexes and constraints for optimal query performance

#### Database Tables Structure
- **pumps**: Main pump catalog with metadata
- **pump_specifications**: Detailed technical specifications
- **pump_curves**: Performance curve definitions
- **pump_performance_points**: Individual performance data points
- **processed_files**: File processing tracking

## Deployment Configuration

### Development Environment
- **Server**: Flask development server with debug mode
- **Host**: `0.0.0.0` (accessible from Replit environment)
- **Port**: 5000 (configured in workflow)
- **Database**: PostgreSQL with automatic connection management

### Production Deployment
- **Server**: Gunicorn WSGI server
- **Deployment Target**: Replit Autoscale
- **Configuration**: `gunicorn --bind 0.0.0.0:5000 main:app`
- **Database**: PostgreSQL with connection pooling and health checks

### Workflow Configuration
```toml
[workflows]
runButton = "Start Application"

[[workflows.workflow]]
name = "Start Application"
author = "agent"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "python main.py"
waitForPort = 5000
```

## Key Build Features

### Modular Architecture
- **Blueprint-based routing**: Organized route modules for different features
- **Component separation**: Clear separation between data, business logic, and presentation
- **Extensible design**: Easy to add new features and functionality

### Data Management
- **Dual backend support**: JSON file and PostgreSQL database backends
- **File format support**: Native SCG and standard text file processing
- **Batch processing**: Concurrent processing of multiple pump data files
- **Data validation**: Comprehensive validation for pump performance data

### Performance Optimization
- **Database connection pooling**: Efficient database resource management
- **Session management**: Optional sessions with secure fallback
- **Static asset optimization**: Efficient serving of CSS, JS, and image assets
- **Chart caching**: Optimized chart generation and embedding

### Security & Configuration
- **Environment-based configuration**: Secure handling of secrets and settings
- **Session security**: Secure session key management
- **Database security**: Parameterized queries and connection security
- **Input validation**: Comprehensive form and data validation

## Testing Infrastructure

### Test Configuration
- **Framework**: pytest for comprehensive testing
- **Configuration**: `pytest.ini` with test discovery settings
- **Test Structure**: Organized test modules in `tests/` directory

### Test Coverage
- **Unit Tests**: Component-level testing for core functionality
- **Integration Tests**: End-to-end workflow testing
- **Link Testing**: Automated testing of internal application links

## Build Commands

### Development
```bash
# Start development server
python main.py

# Run tests
pytest

# Install dependencies
uv install

# Database operations (via application)
# Database schema is managed through SQLAlchemy models
```

### Production Deployment
```bash
# Production server (configured in .replit)
gunicorn --bind 0.0.0.0:5000 main:app
```

## File Upload & Processing

### Upload Configuration
- **Upload Directory**: `app/static/temp/`
- **Supported Formats**: SCG, TXT, PDF (for data extraction)
- **Processing**: Automatic format detection and validation
- **Storage**: Temporary storage with cleanup mechanisms

### File Processing Pipeline
1. **Upload Validation**: File type and size validation
2. **Format Detection**: Automatic detection of SCG vs standard formats
3. **Data Extraction**: Parsing of pump performance data
4. **Validation**: Data integrity and completeness checks
5. **Storage**: Database insertion or JSON file updates
6. **Cleanup**: Temporary file management

## Integration Points

### AI Model Integration
- **OpenAI GPT**: Advanced pump selection reasoning and analysis
- **Google Gemini**: Alternative AI model for technical insights
- **Model Router**: Intelligent routing between AI providers

### External Dependencies
- **System Packages**: `poppler_utils`, `pkg-config` for PDF processing
- **Web Assets**: Bootstrap, Plotly.js, custom CSS/JS
- **Database**: PostgreSQL with full-text search capabilities

## Performance Considerations

### Optimization Strategies
- **Database Queries**: Optimized queries with proper indexing
- **Chart Generation**: Efficient matplotlib and Plotly.js rendering
- **File Processing**: Concurrent processing for batch operations
- **Memory Management**: Proper cleanup of temporary resources

### Scalability Features
- **Connection Pooling**: Database connection management
- **Stateless Design**: Minimal server-side state management
- **Caching**: Strategic caching of computed results
- **Modular Architecture**: Easy horizontal scaling of components

## Documentation & Maintenance

### Code Documentation
- **Inline Comments**: Comprehensive code documentation
- **Type Hints**: Python type annotations for better maintainability
- **Module Docstrings**: Clear module and function documentation

### Logging & Monitoring
- **Structured Logging**: Comprehensive application logging
- **Error Handling**: Robust error management with user feedback
- **Performance Monitoring**: Built-in performance tracking

This specification provides a comprehensive overview of the APE Pumps Selection Application build system, architecture, and deployment configuration. The application is designed for production use with robust error handling, security features, and scalable architecture.