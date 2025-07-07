# Dual Source Pump Repository Enhancement

**Date:** 2025-07-07  
**Status:** ✅ Completed and Tested

## Overview

Successfully enhanced the `pump_repository.py` to support both JSON file and PostgreSQL database data sources based on a configuration flag. The repository now provides a flexible architecture that can switch between data sources seamlessly using the standard `DATABASE_URL` format.

## New Features

### 1. **Dual Data Source Support**
```python
from app.pump_repository import DataSource, PumpRepositoryConfig

# JSON file source (default)
config = PumpRepositoryConfig(data_source=DataSource.JSON_FILE)

# PostgreSQL source using DATABASE_URL
config = PumpRepositoryConfig(
    data_source=DataSource.POSTGRESQL,
    database_url="postgresql://postgres:password@localhost:5432/pump_selection"
)
```

### 2. **Configuration-Driven Architecture**
```python
@dataclass
class PumpRepositoryConfig:
    # Data source configuration
    data_source: DataSource = DataSource.JSON_FILE
    
    # JSON file configuration
    catalog_path: str = "data/ape_catalog_database.json"
    
    # PostgreSQL configuration using DATABASE_URL format
    database_url: str = "postgresql://postgres:password@localhost:5432/pump_selection"
    
    # General configuration
    cache_enabled: bool = True
    reload_on_change: bool = False
```

### 3. **Runtime Data Source Switching**
```python
from app.pump_repository import switch_repository_data_source

# Switch from JSON to PostgreSQL
success = switch_repository_data_source(DataSource.POSTGRESQL)

# Switch back to JSON
success = switch_repository_data_source(DataSource.JSON_FILE)
```

## Implementation Details

### **JSON File Source** (`_load_from_json`)
- ✅ **Fully implemented** and working
- Loads data from `data/ape_catalog_database.json`
- Maintains backward compatibility
- Provides 386 pump models with 869 curves

### **PostgreSQL Source** (`_load_from_postgresql`)
- 🔄 **Stub implementation** ready for future development
- Uses standard `DATABASE_URL` format for configuration
- Returns empty data structure with status indicators
- Includes TODO comments for full implementation
- Logs appropriate warnings about unimplemented functionality

## Usage Examples

### **Basic Usage (JSON Default)**
```python
from app.pump_repository import get_pump_repository

# Uses JSON file by default
repository = get_pump_repository()
pump_models = repository.get_pump_models()
```

### **Explicit JSON Configuration**
```python
from app.pump_repository import PumpRepositoryConfig, DataSource, get_pump_repository

config = PumpRepositoryConfig(data_source=DataSource.JSON_FILE)
repository = get_pump_repository(config)
```

### **PostgreSQL Configuration with DATABASE_URL**
```python
config = PumpRepositoryConfig(
    data_source=DataSource.POSTGRESQL,
    database_url="postgresql://postgres:password@localhost:5432/pump_selection"
)
repository = get_pump_repository(config)
```

### **Environment-Based Configuration**
```python
import os
from app.pump_repository import PumpRepositoryConfig, DataSource

data_source_env = os.getenv('PUMP_DATA_SOURCE', 'json_file')

if data_source_env == 'postgresql':
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/pump_selection')
    config = PumpRepositoryConfig(
        data_source=DataSource.POSTGRESQL,
        database_url=database_url
    )
else:
    config = PumpRepositoryConfig(
        data_source=DataSource.JSON_FILE,
        catalog_path=os.getenv('CATALOG_PATH', 'data/ape_catalog_database.json')
    )
```

### **Supported DATABASE_URL Formats**
```python
# Standard format
"postgresql://postgres:password@localhost:5432/pump_selection"

# With custom host
"postgresql://user:pass@db.example.com:5432/pump_db"

# Default user/password
"postgresql://localhost/pump_selection"

# No password
"postgresql://user@localhost/pump_selection"

# With SSL
"postgresql://user:pass@localhost/pump_selection?sslmode=require"
```

## Testing Results

✅ **JSON Source:** Loads 386 pump models successfully  
✅ **PostgreSQL Stub:** Returns empty data with proper status  
✅ **DATABASE_URL Parsing:** Correctly logs URL format  
✅ **Runtime Switching:** Successfully switches between sources  
✅ **Backward Compatibility:** All existing functionality preserved  
✅ **App Integration:** Flask app runs normally with enhanced repository  

## Future PostgreSQL Implementation

When ready to implement PostgreSQL support, the `_load_from_postgresql` method should:

1. **Parse DATABASE_URL**
   ```python
   from urllib.parse import urlparse
   
   parsed = urlparse(self.config.database_url)
   connection_params = {
       'host': parsed.hostname,
       'port': parsed.port,
       'database': parsed.path[1:],  # Remove leading '/'
       'user': parsed.username,
       'password': parsed.password
   }
   ```

2. **Establish Database Connection**
   ```python
   import psycopg2
   from psycopg2.extras import RealDictCursor
   
   connection = psycopg2.connect(**connection_params)
   ```

3. **Query Pump Data**
   ```python
   with connection.cursor(cursor_factory=RealDictCursor) as cursor:
       cursor.execute("""
           SELECT pump_code, manufacturer, pump_type, 
                  model_series, specifications, curves
           FROM pump_models
       """)
       pump_models = cursor.fetchall()
   ```

4. **Convert to Catalog Format**
   ```python
   catalog_data = {
       'metadata': {
           'total_curves': len(curves),
           'npsh_curves': len([c for c in curves if c.get('npsh_data')]),
           'source': 'postgresql',
           'database_url': self.config.database_url
       },
       'pump_models': [convert_db_row_to_catalog_format(row) for row in pump_models]
   }
   ```

## Benefits Achieved

### ✅ **Flexibility**
- Support for multiple data sources
- Easy switching between JSON and database
- Environment-based configuration
- Standard `DATABASE_URL` format

### ✅ **Future-Proofing**
- Ready for PostgreSQL implementation
- Maintains JSON file compatibility
- No breaking changes to existing code
- Industry-standard connection format

### ✅ **Testing & Development**
- Stub implementation allows testing
- Clear separation of concerns
- Easy to mock different data sources
- DATABASE_URL parsing examples included

### ✅ **Production Readiness**
- Can switch data sources at runtime
- Environment variable configuration
- Proper error handling and logging
- Standard database connection format

## Files Modified

- ✅ `app/pump_repository.py` - Enhanced with dual source support and DATABASE_URL
- ✅ `example_repository_usage.py` - **UPDATED** (DATABASE_URL examples)

## Files Unchanged

- ✅ All existing app modules continue to work unchanged
- ✅ No breaking changes to existing functionality

---

**Result:** Successfully implemented flexible dual-source pump repository with JSON file support and PostgreSQL stub using standard `DATABASE_URL` format ready for future implementation. 