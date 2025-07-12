"""
APE Pumps Data Models
Essential data structures for pump selection
"""

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
        self.npsh_available_m = kwargs.get('npsh_available_m', None)
        self.max_power_kw = kwargs.get('max_power_kw', None)
        self.preferred_efficiency_min = kwargs.get('preferred_efficiency_min', 70)

        # Add missing attributes to fix selection engine errors
        self.pump_type = kwargs.get('pump_type', 'General')
        self.application = kwargs.get('application', 'general')

    def __repr__(self):
        return f"SiteRequirements(flow={self.flow_m3hr} m³/hr, head={self.head_m} m)" 