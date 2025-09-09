"""
Configuration Manager
======================
Singleton class for centralized configuration management.
Loads configuration from app/brain/brain_config/config.json and provides typed access to all constants.
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Singleton configuration manager for the Brain system"""
    
    _instance = None
    _config = None
    _validation_errors = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from app/brain/brain_config/config.json"""
        config_path = Path(__file__).parent / 'brain_config' / 'config.json'
        
        try:
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r') as f:
                data = json.load(f)
                self._config = data.get('hardcoded_values', {})
                
                if not self._config:
                    raise ValueError("Configuration file is missing 'hardcoded_values' section")
                
                self._process_config()
                self._validate_required_keys()
                
        except FileNotFoundError as e:
            # Critical error - config file must exist
            print(f"CRITICAL ERROR: Configuration file not found at {config_path}")
            print("The application cannot start without config.json")
            print("Please ensure app/brain/brain_config/config.json exists with proper configuration")
            self._set_defaults()  # Use emergency defaults
            print("WARNING: Using emergency default values - system may not function correctly")
            
        except json.JSONDecodeError as e:
            # Critical error - config file is corrupted
            print(f"CRITICAL ERROR: Configuration file is corrupted: {e}")
            print("Please fix the JSON syntax in app/brain/brain_config/config.json")
            self._set_defaults()  # Use emergency defaults
            print("WARNING: Using emergency default values - system may not function correctly")
            
        except Exception as e:
            print(f"ERROR: Unexpected error loading config: {e}")
            self._set_defaults()  # Use emergency defaults
            print("WARNING: Using emergency default values - system may not function correctly")
    
    def _process_config(self):
        """Process raw config into structured format by category"""
        self.ai_analysis = self._extract_values('ai_analysis_constants')
        self.ai_analyst = self._extract_values('ai_analyst_constants')
        self.performance_affinity = self._extract_values('performance_affinity_constants')
        self.performance_curves = self._extract_values('performance_curves_constants')
        self.physics_models = self._extract_values('physics_models_constants')
        self.validation = self._extract_values('validation_constants')
        self.cache = self._extract_values('cache_constants')
        self.charts = self._extract_values('charts_constants')
        self.hydraulic_classifier = self._extract_values('hydraulic_classifier_constants')
        self.proximity_searcher = self._extract_values('proximity_searcher_constants')
        self.pump_evaluator = self._extract_values('pump_evaluator_constants')
        self.performance_vfd = self._extract_values('performance_vfd_constants')
        
        # Selection core constants (to be added when found)
        self.selection_core = self._extract_values('selection_core_constants')
        
        # Physical validator constants (to be added when found)
        self.physical_validator = self._extract_values('physical_validator_constants')
        
        # Performance core constants (to be added when found)
        self.performance_core = self._extract_values('performance_core_constants')
        
        # Performance advanced constants (to be added when found)
        self.performance_advanced = self._extract_values('performance_advanced_constants')
        
        # Performance industry standard constants (to be added when found)
        self.performance_industry_standard = self._extract_values('performance_industry_standard_constants')
        
        # Performance optimization constants (to be added when found)
        self.performance_optimization = self._extract_values('performance_optimization_constants')
        
        # Performance validation constants (to be added when found)
        self.performance_validation = self._extract_values('performance_validation_constants')
        
        # BEP calculator constants (to be added when found)
        self.bep_calculator = self._extract_values('bep_calculator_constants')
        
        # Scoring utils constants (to be added when found)
        self.scoring_utils = self._extract_values('scoring_utils_constants')
    
    def _validate_required_keys(self):
        """Validate that all required configuration keys are present"""
        # Basic validation - check that main sections exist and have some content
        required_sections = ['pump_evaluator', 'performance_vfd', 'validation', 'performance_affinity', 'physics_models']
        
        for section_name in required_sections:
            section = getattr(self, section_name, {})
            value_keys = [k for k in section.keys() if k.endswith('_value')]
            if len(value_keys) == 0:
                self._validation_errors.append(f"Section '{section_name}' has no configuration values")
        
        if self._validation_errors:
            print("CONFIG VALIDATION ERRORS:")
            for error in self._validation_errors:
                print(f"  - {error}")
            print("WARNING: Some configuration sections are missing or empty")
        else:
            print("CONFIG: All main sections validated successfully")
    
    def _extract_values(self, section_name: str) -> Dict[str, Any]:
        """Extract values from a config section into a structured dict"""
        result = {}
        section = self._config.get(section_name, [])
        
        for item in section:
            # Use the explicit constant name if available, otherwise fall back to description-based key
            if 'constant' in item:
                key = item['constant']
            else:
                # Fallback for old format - create key from description
                description = item.get('description', '')
                key = description.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
                # Remove special characters
                key = ''.join(c if c.isalnum() or c == '_' else '' for c in key)
            
            # Store value with metadata
            result[key] = {
                'value': item.get('value'),
                'description': item.get('description'),
                'constant': item.get('constant')
            }
            
            # Also create direct value access (for backward compatibility)
            result[f"{key}_value"] = item.get('value')
        
        return result
    
    def _set_defaults(self):
        """Set default values if config file cannot be loaded"""
        # AI Analysis defaults
        self.ai_analysis = {
            'model_value': 'gpt-3.5-turbo',
            'max_tokens_value': 500,
            'temperature_value': 0.3,
            'word_limit_value': 300,
            'gemini_model_value': 'gemini-1.5-flash',
            'excellent_efficiency_value': 80.0,
            'good_efficiency_value': 75.0,
            'adequate_efficiency_value': 65.0
        }
        
        # AI Analyst defaults
        self.ai_analyst = {
            'model_value': 'gpt-4o',
            'temperature_value': 0.3,
            'max_tokens_value': 1000
        }
        
        # Performance Affinity defaults
        self.performance_affinity = {
            'min_efficiency_value': 40.0,
            'min_trim_percentage_value': 85.0,
            'max_trim_percentage_value': 100.0,
            'flow_exponent_value': 1.0,
            'head_exponent_value': 2.0,
            'power_exponent_value': 3.0,
            'efficiency_exponent_value': 0.8,
            'bep_flow_exponent_value': 1.2,
            'bep_head_exponent_value': 2.2,
            'trim_small_exponent_value': 2.9,
            'trim_large_exponent_value': 2.1,
            'volute_penalty_value': 0.20,
            'diffuser_penalty_value': 0.45,
            'npsh_threshold_value': 10.0,
            'npsh_factor_value': 1.15,
            'water_density_value': 1000,
            'gravity_value': 9.81,
            'seconds_per_hour_value': 3600
        }
        
        # Performance Curves defaults
        self.performance_curves = {
            'min_efficiency_value': 40.0,
            'min_trim_percentage_value': 85.0,
            'max_trim_percentage_value': 100.0,
            'flow_min_tolerance_value': 0.9,
            'flow_max_tolerance_value': 1.1,
            'head_min_factor_value': 0.98,
            'head_max_factor_value': 1.10,
            'head_bonus_factor_value': 0.7,
            'fallback_efficiency_value': 70.0,
            'water_density_value': 1000,
            'gravity_value': 9.81,
            'seconds_per_hour_value': 3600
        }
        
        # Physics Models defaults
        self.physics_models = {
            'axial_flow_exponent_value': 0.95,
            'axial_head_exponent_value': 1.65,
            'axial_power_exponent_value': 2.60,
            'axial_npsh_exponent_value': 1.70,
            'end_suction_flow_exponent_value': 1.00,
            'end_suction_head_exponent_value': 1.95
        }
        
        # Validation defaults
        self.validation = {
            'gpm_to_m3hr_value': 0.227124,
            'lps_to_m3hr_value': 3.6,
            'lpm_to_m3hr_value': 0.06,
            'mgd_to_m3hr_value': 157.725,
            'feet_to_meters_value': 0.3048,
            'psi_to_meters_value': 0.703070,
            'bar_to_meters_value': 10.1972,
            'kpa_to_meters_value': 0.101972,
            'hp_to_kw_value': 0.745699872,
            'w_to_kw_value': 0.001,
            'inches_to_mm_value': 25.4,
            'min_flow_value': 0.1,
            'max_flow_value': 50000,
            'max_head_value': 5000,
            'max_power_value': 10000,
            'max_npsh_value': 100,
            'min_impeller_value': 50,
            'max_impeller_value': 5000,
            'max_speed_value': 7200
        }
        
        # Cache defaults
        self.cache = {
            'max_size_value': 1000,
            'default_ttl_value': 300
        }
        
        # Charts defaults
        self.charts = {
            'web_margin_value': 0.1,
            'pdf_margin_value': 0.15,
            'detailed_margin_value': 0.12
        }
        
        # Hydraulic Classifier defaults
        self.hydraulic_classifier = {
            'default_speed_value': 2960,
            'seconds_per_hour_value': 3600,
            'low_specific_speed_value': 30,
            'mid_specific_speed_value': 60,
            'high_specific_speed_value': 120
        }
        
        # Proximity Searcher defaults
        self.proximity_searcher = {
            'max_flow_value': 20000,
            'max_head_value': 2000,
            'top_pumps_value': 20
        }
        
        # Pump Evaluator defaults
        self.pump_evaluator = {
            'bep_proximity_weight_value': 45,
            'efficiency_weight_value': 35,
            'head_margin_weight_value': 20,
            'head_oversize_threshold_value': 150.0,
            'severe_oversize_threshold_value': 300.0
        }
        
        # Performance VFD defaults
        self.performance_vfd = {
            'default_speed_value': 1450,
            'min_speed_ratio_value': 0.3,
            'max_speed_ratio_value': 1.2,
            'static_head_ratio_value': 0.4,
            'base_frequency_value': 50
        }
        
        # Initialize empty sections for files not in config yet
        self.selection_core = {}
        self.physical_validator = {}
        self.performance_core = {}
        self.performance_advanced = {}
        self.performance_industry_standard = {}
        self.performance_optimization = {}
        self.performance_validation = {}
        self.bep_calculator = {}
        self.scoring_utils = {}
    
    def get(self, section: str, key: str) -> Any:
        """
        Get a configuration value. 
        No default fallback - config must contain the value.
        Raises KeyError if value not found.
        """
        section_data = getattr(self, section, {})
        
        # First try the direct key (new format)
        if key in section_data:
            value_data = section_data[key]
            if isinstance(value_data, dict) and 'value' in value_data:
                return value_data['value']
            else:
                return value_data
        
        # Then try the old _value suffix format (backward compatibility)
        value_key = f"{key}_value"
        if value_key in section_data:
            return section_data[value_key]
        
        # Debug info for troubleshooting
        available_keys = list(section_data.keys())[:10]  # Show first 10 keys
        error_msg = f"Configuration value not found: {section}.{key}"
        error_msg += f"\nAvailable keys in {section}: {available_keys}"
        if len(section_data) > 10:
            error_msg += f" ... and {len(section_data) - 10} more"
        if self._validation_errors:
            error_msg += "\nNote: Config validation errors were detected. Check logs above."
        raise KeyError(error_msg)
    
    def get_safe(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with a fallback default.
        Use this only during migration or for truly optional values.
        """
        try:
            return self.get(section, key)
        except KeyError:
            return default
    
    def is_valid(self) -> bool:
        """Check if configuration is valid and complete"""
        return len(self._validation_errors) == 0


# Create singleton instance
config = ConfigManager()