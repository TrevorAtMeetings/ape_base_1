#!/usr/bin/env python3
"""
Example usage of the Pump Repository with different data sources.
Demonstrates how to configure and use the repository with JSON or PostgreSQL.
"""

from app.pump_repository import (
    PumpRepositoryConfig, 
    DataSource, 
    get_pump_repository,
    switch_repository_data_source
)

def example_json_source():
    """Example: Use repository with JSON file source"""
    print("=== JSON File Source Example ===")
    
    # Create config for JSON source (default)
    config = PumpRepositoryConfig(
        data_source=DataSource.JSON_FILE,
        catalog_path="data/ape_catalog_database.json"
    )
    
    # Get repository instance
    repository = get_pump_repository(config)
    
    # Check data source
    print(f"Data source: {repository.get_data_source()}")
    
    # Get pump data
    pump_models = repository.get_pump_models()
    metadata = repository.get_metadata()
    
    print(f"Loaded {len(pump_models)} pump models")
    print(f"Total curves: {metadata.get('total_curves', 0)}")
    
    # Get specific pump
    if pump_models:
        first_pump = pump_models[0]
        pump_code = first_pump.get('pump_code', 'Unknown')
        found_pump = repository.get_pump_by_code(pump_code)
        print(f"Found pump: {found_pump.get('pump_code') if found_pump else 'Not found'}")
    
    print()

def example_postgresql_source():
    """Example: Use repository with PostgreSQL source (stub)"""
    print("=== PostgreSQL Source Example ===")
    
    # Create config for PostgreSQL source using DATABASE_URL
    config = PumpRepositoryConfig(
        data_source=DataSource.POSTGRESQL,
        database_url="postgresql://postgres:password@localhost:5432/pump_selection"
    )
    
    # Get repository instance
    repository = get_pump_repository(config)
    
    # Check data source
    print(f"Data source: {repository.get_data_source()}")
    
    # Get pump data (will be empty due to stub implementation)
    pump_models = repository.get_pump_models()
    metadata = repository.get_metadata()
    
    print(f"Loaded {len(pump_models)} pump models")
    print(f"Source status: {metadata.get('status', 'unknown')}")
    print(f"Database URL: {metadata.get('database_url', 'not_set')}")
    
    print()

def example_runtime_switch():
    """Example: Switch data source at runtime"""
    print("=== Runtime Data Source Switch Example ===")
    
    # Start with JSON source
    repository = get_pump_repository()
    print(f"Initial data source: {repository.get_data_source()}")
    print(f"Initial pump count: {repository.get_pump_count()}")
    
    # Switch to PostgreSQL (stub)
    success = switch_repository_data_source(DataSource.POSTGRESQL)
    print(f"Switch to PostgreSQL successful: {success}")
    print(f"New data source: {repository.get_data_source()}")
    print(f"New pump count: {repository.get_pump_count()}")
    
    # Switch back to JSON
    success = switch_repository_data_source(DataSource.JSON_FILE)
    print(f"Switch back to JSON successful: {success}")
    print(f"Final data source: {repository.get_data_source()}")
    print(f"Final pump count: {repository.get_pump_count()}")
    
    print()

def example_environment_config():
    """Example: Configure based on environment variables"""
    print("=== Environment-Based Configuration Example ===")
    
    import os
    
    # Check environment variable for data source
    data_source_env = os.getenv('PUMP_DATA_SOURCE', 'json_file')
    
    if data_source_env == 'postgresql':
        # Use DATABASE_URL from environment
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
    
    repository = get_pump_repository(config)
    print(f"Environment-based data source: {repository.get_data_source()}")
    print(f"Pump count: {repository.get_pump_count()}")
    
    if repository.get_data_source() == DataSource.POSTGRESQL:
        metadata = repository.get_metadata()
        print(f"Database URL: {metadata.get('database_url', 'not_set')}")
    
    print()

def example_database_url_formats():
    """Example: Different DATABASE_URL formats"""
    print("=== DATABASE_URL Format Examples ===")
    
    # Different DATABASE_URL formats
    urls = [
        "postgresql://postgres:password@localhost:5432/pump_selection",
        "postgresql://user:pass@db.example.com:5432/pump_db",
        "postgresql://localhost/pump_selection",  # Default user/pass
        "postgresql://user@localhost/pump_selection",  # No password
        "postgresql://user:pass@localhost/pump_selection?sslmode=require",  # With SSL
    ]
    
    for i, url in enumerate(urls, 1):
        print(f"Example {i}: {url}")
        
        config = PumpRepositoryConfig(
            data_source=DataSource.POSTGRESQL,
            database_url=url
        )
        
        repository = get_pump_repository(config)
        metadata = repository.get_metadata()
        print(f"  Status: {metadata.get('status', 'unknown')}")
        print(f"  Database URL: {metadata.get('database_url', 'not_set')}")
        print()
    
    print()

if __name__ == "__main__":
    print("Pump Repository Examples")
    print("=" * 50)
    
    # Run examples
    example_json_source()
    example_postgresql_source()
    example_runtime_switch()
    example_environment_config()
    example_database_url_formats()
    
    print("Examples completed!") 