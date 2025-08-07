"""
APE Pumps Data Models
Essential data structures for pump selection
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Exclusion Tracking System
class ExclusionReason(Enum):
    """Comprehensive tracking of pump exclusion reasons"""
    UNDERTRIM = "Impeller trim below minimum allowed diameter (80%)"
    OVERTRIM = "Impeller trim above maximum allowed diameter (100%)"
    OVERSPEED = "Exceeds maximum motor speed (3600 RPM)"
    UNDERSPEED = "Below minimum viable speed (750 RPM)"
    HEAD_NOT_MET = "Cannot achieve required head within constraints"
    CURVE_INVALID = "Non-monotonic or invalid performance curve"
    EFFICIENCY_MISSING = "No efficiency data available at duty point"
    EFFICIENCY_TOO_LOW = "Efficiency below minimum threshold (40%)"
    ENVELOPE_EXCEEDED = "Outside manufacturer's operating envelope"
    FLOW_OUT_OF_RANGE = "Flow requirement outside pump capacity"
    NPSH_INSUFFICIENT = "NPSHr exceeds NPSHa (when NPSHa is known)"
    NO_PERFORMANCE_DATA = "Unable to calculate performance at duty point"
    COMBINED_LIMITS_EXCEEDED = "Speed and trim combination exceeds limits"

@dataclass
class PumpEvaluation:
    """Comprehensive pump evaluation result with exclusion tracking"""
    pump_code: str
    feasible: bool = False
    exclusion_reasons: List[ExclusionReason] = field(default_factory=list)
    score_components: Dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    performance_data: Optional[Dict[str, Any]] = None
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_exclusion(self, reason: ExclusionReason):
        """Add an exclusion reason and mark as infeasible"""
        self.feasible = False
        if reason not in self.exclusion_reasons:
            self.exclusion_reasons.append(reason)
    
    def get_exclusion_summary(self) -> str:
        """Get human-readable exclusion summary"""
        if self.feasible:
            return "Pump is feasible"
        return "; ".join([reason.value for reason in self.exclusion_reasons])

# Essential Data Structures
class SiteRequirements:
    """Data structure to represent site requirements for pump selection"""

    def __init__(self, flow_m3hr: float, head_m: float, **kwargs):
        self.flow_m3hr = flow_m3hr
        self.head_m = head_m
        self.customer_name = kwargs.get('customer_name', '')
        self.project_name = kwargs.get('project_name', '')
        self.application_type = kwargs.get('application_type', 'general')
        self.liquid_type = kwargs.get('liquid_type', 'water')
        self.temperature_c = kwargs.get('temperature_c', 20)
        # NPSH Available - calculate using engineering defaults if not provided
        self.npsh_available_m = kwargs.get('npsh_available_m', None)
        if self.npsh_available_m is None:
            from .npsh_calculator import NPSHCalculator
            npsha_result = NPSHCalculator.calculate_npsha_with_defaults()
            self.npsh_available_m = npsha_result['npsha_m']
            self.npsha_calculation = npsha_result  # Store full calculation details
        self.max_power_kw = kwargs.get('max_power_kw', None)
        self.preferred_efficiency_min = kwargs.get('preferred_efficiency_min', 70)

        # Add missing attributes to fix selection engine errors
        self.pump_type = kwargs.get('pump_type', 'General')
        self.application = kwargs.get('application', 'general')

    def __repr__(self):
        return f"SiteRequirements(flow={self.flow_m3hr} m³/hr, head={self.head_m} m)" 