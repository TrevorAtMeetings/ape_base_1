"""
Process Flow Logger Module
==========================
Comprehensive logging system for tracking pump selection process with full data capture.
Includes easy toggle mechanism via environment variable or config file.
"""

import os
import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

class ProcessLogger:
    """
    Centralized process logging with toggle mechanism.
    Priority: Environment Variable > Config File > Default (disabled)
    """
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.enabled = self._check_enabled()
        self.logger = self._null_logger()  # Start with null logger - only create real logger when needed
        self.flow_head_suffix = ""  # Will be set when pump selection starts
        self._logger_initialized = False  # Track if we've created a real logger yet
    
    def _check_enabled(self) -> bool:
        """Check if logging is enabled from multiple sources."""
        # 1. Check environment variable (highest priority)
        env_setting = os.getenv('ENABLE_PROCESS_LOGGING')
        if env_setting is not None:
            return env_setting.lower() in ('true', '1', 'yes', 'on')
        
        # 2. Check config file
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'features.json')
            if os.path.exists(config_path):
                with open(config_path) as f:
                    features = json.load(f)
                    if 'process_logging' in features:
                        return features['process_logging']
        except Exception:
            pass
        
        # 3. Default to disabled for production safety
        return False
    
    def _setup_logger(self, flow: float = None, head: float = None) -> logging.Logger:
        """Setup the actual file logger."""
        # Create log directory
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'process', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create timestamped log file with optional flow/head suffix
        if flow is not None and head is not None:
            date_stamp = datetime.now().strftime("%Y%m%d")
            log_filename = f"{date_stamp}_flow_{int(flow)}_head_{int(head)}.txt"
        else:
            log_filename = f"{self.session_id}.txt"
        
        log_file = os.path.join(log_dir, log_filename)
        
        # Configure logger
        logger = logging.getLogger(f'process_flow_{self.session_id}')
        logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        logger.handlers = []
        
        # File handler with detailed formatting
        handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Also log toggle status
        logger.info(f"Process logging ENABLED - Log file: {log_file}")
        
        return logger
    
    def _null_logger(self) -> logging.Logger:
        """Create a dummy logger that does nothing when disabled."""
        logger = logging.getLogger('process_flow_disabled')
        logger.addHandler(logging.NullHandler())
        logger.setLevel(logging.CRITICAL)  # Effectively disables all logging
        return logger
    
    def log(self, message: str, level: str = 'INFO'):
        """Main logging method with automatic formatting."""
        if not self.enabled:
            return
        
        if level == 'DEBUG':
            self.logger.debug(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        elif level == 'ERROR':
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def log_separator(self, char: str = "-", length: int = 80):
        """Log a separator line."""
        self.log(char * length)
    
    def log_section(self, title: str):
        """Log a section header."""
        self.log("="*80)
        self.log(f"{title}")
        self.log("="*80)
    
    def log_data(self, label: str, data: Any, indent: int = 2):
        """Log data with automatic formatting and type handling."""
        if not self.enabled:
            return
        
        try:
            # Handle different data types
            if data is None:
                self.log(f"{label}: None")
            elif isinstance(data, (str, int, float, bool)):
                self.log(f"{label}: {data}")
            elif isinstance(data, (list, tuple)):
                self.log(f"{label}: [{len(data)} items]")
                for i, item in enumerate(data[:10]):  # Limit to first 10 items
                    self.log(f"  [{i}] {self._format_value(item)}")
                if len(data) > 10:
                    self.log(f"  ... and {len(data) - 10} more items")
            elif isinstance(data, dict):
                self.log(f"{label}:")
                self._log_dict(data, indent)
            else:
                self.log(f"{label}: {str(data)}")
        except Exception as e:
            self.log(f"{label}: [Error formatting data: {e}]")
    
    def _log_dict(self, data: dict, indent: int = 2):
        """Recursively log dictionary data."""
        prefix = " " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                self.log(f"{prefix}{key}:")
                self._log_dict(value, indent + 2)
            elif isinstance(value, (list, tuple)):
                self.log(f"{prefix}{key}: [{len(value)} items]")
                for i, item in enumerate(value[:3]):  # Show first 3 items
                    self.log(f"{prefix}  [{i}] {self._format_value(item)}")
                if len(value) > 3:
                    self.log(f"{prefix}  ... and {len(value) - 3} more")
            else:
                self.log(f"{prefix}{key}: {self._format_value(value)}")
    
    def _format_value(self, value: Any) -> str:
        """Format a single value for logging."""
        if value is None:
            return "None"
        elif isinstance(value, float):
            return f"{value:.2f}"
        elif isinstance(value, np.ndarray):
            return f"array(shape={value.shape})"
        elif isinstance(value, (np.integer, np.floating)):
            return str(value.item())
        elif isinstance(value, dict):
            return f"dict({len(value)} keys)"
        elif isinstance(value, (list, tuple)):
            return f"{type(value).__name__}({len(value)} items)"
        else:
            return str(value)
    
    def log_pump_evaluation(self, pump_code: str, pump_data: dict, 
                           flow: float, head: float, evaluation: dict):
        """Specialized logging for individual pump evaluation."""
        if not self.enabled:
            return
        
        self.log("=" * 80)
        
        self.log(f"EVALUATING PUMP: {pump_code}")
            
        self.log(f"  Target: {flow:.1f} m³/hr @ {head:.1f}m")
        
        # Log specifications
        specs = pump_data.get('specifications', {})
        if specs:
            self.log("  Specifications:")
            self.log(f"    BEP Flow: {specs.get('bep_flow_m3hr', 'N/A')} m³/hr")
            self.log(f"    BEP Head: {specs.get('bep_head_m', 'N/A')} m")
            self.log(f"    Max Impeller: {specs.get('max_impeller_diameter_mm', 'N/A')} mm")
            self.log(f"    Min Impeller: {specs.get('min_impeller_diameter_mm', 'N/A')} mm")
            self.log(f"    Pump Type: {pump_data.get('pump_type', 'N/A')}")
            self.log(f"    Variable Speed: {specs.get('variable_speed', False)}")
            self.log(f"    Variable Diameter: {specs.get('variable_diameter', True)}")
        
        # Log evaluation results
        if evaluation:
            self.log("  Evaluation Results:")
            self.log(f"    Operating Zone: {evaluation.get('operating_zone', 'N/A')}")
            self.log(f"    QBP: {evaluation.get('qbp_percent', 0):.1f}%")
            self.log(f"    Feasible: {evaluation.get('feasible', False)}")
            
            # Score breakdown
            scores = evaluation.get('score_components', {})
            if scores:
                self.log("  Score Components:")
                for component, score in scores.items():
                    self.log(f"    {component}: {score}")
                self.log(f"  TOTAL SCORE: {evaluation.get('total_score', 0):.1f}")
            
            # Performance data
            self.log(f"    Efficiency: {evaluation.get('efficiency_pct', 0):.1f}%")
            self.log(f"    Power: {evaluation.get('power_kw', 0):.1f} kW")
            self.log(f"    NPSH: {evaluation.get('npshr_m', 0):.1f} m")
            self.log(f"    Trim: {evaluation.get('trim_percent', 100):.1f}%")
            
            # Exclusion reasons if any
            if evaluation.get('exclusion_reasons'):
                self.log(f"  Exclusion Reasons: {', '.join(evaluation['exclusion_reasons'])}")
    
    def log_performance_calculation(self, pump_code: str, flow: float, head: float,
                                   method: str, inputs: dict, outputs: dict):
        """Log performance calculation details."""
        if not self.enabled:
            return
        
        self.log(f"PERFORMANCE CALCULATION: {pump_code}")
        self.log(f"  Method: {method}")
        self.log(f"  Target: {flow:.1f} m³/hr @ {head:.1f}m")
        
        if inputs:
            self.log("  Inputs:")
            for key, value in inputs.items():
                self.log(f"    {key}: {self._format_value(value)}")
        
        if outputs:
            self.log("  Outputs:")
            for key, value in outputs.items():
                self.log(f"    {key}: {self._format_value(value)}")
    
    def log_selection_summary(self, total_pumps: int, filtered_pumps: int,
                             feasible_pumps: int, exclusion_summary: dict,
                             tiered_results: dict):
        """Log the final selection summary."""
        if not self.enabled:
            return
        
        self.log_section("FINAL SELECTION SUMMARY")
        self.log(f"Total Repository Pumps: {total_pumps}")
        self.log(f"After Pre-filtering: {filtered_pumps}")
        self.log(f"Feasible Pumps: {feasible_pumps}")
        
        # Exclusion breakdown
        if exclusion_summary:
            self.log("\nExclusion Breakdown:")
            for reason, count in exclusion_summary.items():
                self.log(f"  {reason}: {count} pumps")
        
        # Tiered results
        if tiered_results:
            for tier_name, pumps in tiered_results.items():
                if pumps:
                    self.log(f"\n{tier_name.upper()} TIER ({len(pumps)} pumps):")
                    for i, pump in enumerate(pumps[:5], 1):  # Show top 5 per tier
                        self.log(f"  {i}. {pump.get('pump_code', 'N/A')}: "
                               f"Score={pump.get('total_score', 0):.1f}, "
                               f"Eff={pump.get('efficiency_pct', 0):.1f}%, "
                               f"Power={pump.get('power_kw', 0):.1f}kW, "
                               f"QBP={pump.get('qbp_percent', 0):.1f}%")
                    if len(pumps) > 5:
                        self.log(f"  ... and {len(pumps) - 5} more pumps")

    def log_final_rankings(self, feasible_pumps: list, excluded_pumps: list = None):
        """Log individual pump rankings and UI placement after evaluation."""
        if not self.enabled:
            return
        
        self.log_section("FINAL UI RANKINGS")
        
        # Group feasible pumps by operating zone for tier rankings
        tier_groups = {
            'preferred': [p for p in feasible_pumps if p.get('operating_zone') == 'preferred'],
            'allowable': [p for p in feasible_pumps if p.get('operating_zone') == 'allowable'],
            'acceptable': [p for p in feasible_pumps if p.get('operating_zone') == 'acceptable'],
            'marginal': [p for p in feasible_pumps if p.get('operating_zone') == 'marginal']
        }
        
        # Log ranking for each pump with UI placement
        overall_rank = 1
        for tier_name, tier_pumps in tier_groups.items():
            if tier_pumps:
                self.log(f"\n{tier_name.upper()} TIER RANKINGS:")
                tier_rank = 1
                for pump in tier_pumps:
                    pump_code = pump.get('pump_code', 'N/A')
                    score = pump.get('total_score', 0)
                    qbp = pump.get('qbp_percent', 0)
                    efficiency = pump.get('efficiency_pct', 0)
                    
                    # Log individual pump with both overall and tier ranking
                    self.log(f"  Rank #{overall_rank}: {pump_code} | "
                           f"Tier Rank #{tier_rank} | "
                           f"Score={score:.1f} | QBP={qbp:.1f}% | Eff={efficiency:.1f}%")
                    
                    overall_rank += 1
                    tier_rank += 1
        
        # Log excluded pumps
        if excluded_pumps:
            self.log(f"\nEXCLUDED PUMPS ({len(excluded_pumps)} pumps):")
            for pump in excluded_pumps[:10]:  # Show top 10 excluded
                pump_code = pump.get('pump_code', 'N/A')
                reasons = pump.get('exclusion_reasons', [])
                reason_text = ', '.join(reasons[:2]) if reasons else 'Unknown reason'
                if len(reasons) > 2:
                    reason_text += f" (+{len(reasons)-2} more)"
                
                self.log(f"  {pump_code}: UI Ranking = N/A (excluded) | Reason: {reason_text}")
            
            if len(excluded_pumps) > 10:
                self.log(f"  ... and {len(excluded_pumps) - 10} more excluded pumps")
        
        self.log(f"\nTotal Pumps Displayed to User: {len(feasible_pumps)}")
        self.log(f"Total Pumps Excluded from UI: {len(excluded_pumps) if excluded_pumps else 0}")
    
    def toggle(self, enabled: Optional[bool] = None) -> bool:
        """Toggle logging on/off at runtime."""
        if enabled is None:
            self.enabled = not self.enabled
        else:
            self.enabled = enabled
        
        # Reinitialize logger if state changed
        if self.enabled:
            # Don't create logger immediately - wait for set_pump_selection_context()
            self._logger_initialized = False
            self.logger = self._null_logger()
        else:
            self.logger = self._null_logger()
            self._logger_initialized = False
        
        return self.enabled
    
    def set_pump_selection_context(self, flow: float, head: float):
        """Set flow and head context and initialize logger with descriptive filename."""
        if not self.enabled:
            return
            
        # If this is the first time we're creating a real logger, initialize it
        if not self._logger_initialized:
            self.logger = self._setup_logger(flow, head)
            self._logger_initialized = True
            
            # Log initialization with context
            self.log("="*80)
            self.log(f"PROCESS LOGGING INITIALIZED - Session: {self.session_id}")
            self.log(f"PUMP SELECTION CONTEXT SET - Flow: {flow} m³/hr, Head: {head} m")
            self.log("="*80)
        else:
            # Safe handler cleanup for existing logger - handle already-closed handlers gracefully
            if self.logger:
                for handler in self.logger.handlers[:]:
                    try:
                        handler.close()
                    except Exception:
                        pass  # Handler already closed, ignore
                    try:
                        self.logger.removeHandler(handler)
                    except Exception:
                        pass  # Handler already removed, ignore
                
                # Clear handlers list to ensure clean state
                self.logger.handlers = []
            
            # Reinitialize logger with new flow/head filename
            self.logger = self._setup_logger(flow, head)
            
            # Log the context switch
            self.log("="*80)
            self.log(f"PUMP SELECTION CONTEXT SET - Flow: {flow} m³/hr, Head: {head} m")
            self.log("="*80)
    
    def get_log_file_path(self) -> Optional[str]:
        """Get the current log file path if logging is enabled."""
        if self.enabled and hasattr(self.logger, 'handlers') and self.logger.handlers:
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    return handler.baseFilename
        return None


# Create global singleton instance
process_logger = ProcessLogger()


# Convenience functions for direct access
def log(message: str, level: str = 'INFO'):
    """Global log function."""
    process_logger.log(message, level)

def log_data(label: str, data: Any):
    """Global log data function."""
    process_logger.log_data(label, data)

def log_section(title: str):
    """Global log section function."""
    process_logger.log_section(title)

def log_pump_evaluation(pump_code: str, pump_data: dict, flow: float, head: float, evaluation: dict):
    """Global pump evaluation logging."""
    process_logger.log_pump_evaluation(pump_code, pump_data, flow, head, evaluation)

def is_logging_enabled() -> bool:
    """Check if logging is currently enabled."""
    return process_logger.enabled

def get_log_file() -> Optional[str]:
    """Get current log file path."""
    return process_logger.get_log_file_path()

def set_pump_selection_context(flow: float, head: float):
    """Set pump selection context with flow and head parameters."""
    process_logger.set_pump_selection_context(flow, head)