#!/usr/bin/env python
"""
Initialize the admin configuration database tables and seed data
Run this script to set up the admin configuration system
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import admin_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize admin configuration system"""
    try:
        logger.info("Initializing admin configuration database...")
        
        # Create tables
        admin_db.init_tables()
        logger.info("Tables created successfully")
        
        # Seed engineering constants
        admin_db.seed_engineering_constants()
        logger.info("Engineering constants seeded successfully")
        
        # Seed default profiles
        admin_db.seed_default_profiles()
        logger.info("Default profiles seeded successfully")
        
        logger.info("\nAdmin configuration system initialized successfully!")
        logger.info("Access the admin dashboard at: /admin/config/")
        logger.info("\nNote: Admin panel is now accessible without authentication.")
        
    except Exception as e:
        logger.error(f"Failed to initialize admin configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()