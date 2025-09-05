"""This commit includes changes to ensure BEP markers are stored with efficiency data and to retrieve BEP markers for display."""
"""
Centralized Pump Repository - Delegation Facade
Single source of truth for pump data loading and management.
Delegates to specialized modules for different operations.
"""

import logging
from typing import List, Dict, Any, Optional

# Import specialized modules
from .pump_repository_core import (
    PumpRepository, 
    PumpRepositoryConfig, 
    DataSource,
    get_pump_repository,
    clear_pump_repository,
    load_all_pump_data
)
from .pump_repository_insertion import insert_extracted_pump_data

logger = logging.getLogger(__name__)

# Re-export core classes for backward compatibility
# Classes are now defined in pump_repository_core.py

# Main class is now defined in pump_repository_core.py
# This file serves as a delegation facade for backward compatibility

# Functions are now defined in specialized modules
# Re-exported here for backward compatibility