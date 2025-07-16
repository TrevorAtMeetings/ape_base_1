"""
APE Pumps Utilities
Validation and legacy compatibility utilities
"""

import logging
from typing import Dict, Any, List
from .data_models import SiteRequirements

logger = logging.getLogger(__name__)

def validate_site_requirements(form_data: Dict[str, Any]) -> SiteRequirements:
    """Validate and convert form data to SiteRequirements object."""
    try:
        flow_rate = float(form_data.get('flow_m3hr', form_data.get('flow_rate', form_data.get('flow', 0))))
        total_head = float(form_data.get('head_m', form_data.get('total_head', form_data.get('head', 0))))

        if flow_rate <= 0:
            raise ValueError("Flow rate must be greater than 0")
        if total_head <= 0:
            raise ValueError("Total head must be greater than 0")

        # Optional parameters with defaults
        kwargs = {}
        for key in ['customer_name', 'project_name', 'application_type', 'liquid_type', 'pump_type']:
            if key in form_data and form_data[key]:
                kwargs[key] = form_data[key]

        # Numeric optional parameters
        for key in ['temperature_c', 'npsh_available_m', 'max_power_kw', 'preferred_efficiency_min']:
            if key in form_data and form_data[key]:
                try:
                    kwargs[key] = float(form_data[key])
                except (ValueError, TypeError):
                    pass  # Skip invalid numeric values

        return SiteRequirements(flow_rate, total_head, **kwargs)

    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid input data: {str(e)}")

def _parse_performance_curves(obj_pump: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse performance curves from pump data (legacy format)"""
    curves = []
    
    # Get curve data from legacy format
    flow_str = obj_pump.get('pM_FLOW', '')
    head_str = obj_pump.get('pM_HEAD', '')
    eff_str = obj_pump.get('pM_EFF', '')
    npshr_str = obj_pump.get('pM_NP', '')
    impeller_size = obj_pump.get('pM_IMP', '0')
    
    if not flow_str or not head_str:
        return curves
    
    try:
        # Parse semicolon-separated values
        flows = [float(x.strip()) for x in flow_str.split(';') if x.strip()]
        heads = [float(x.strip()) for x in head_str.split(';') if x.strip()]
        efficiencies = [float(x.strip()) for x in eff_str.split(';') if x.strip()]
        npshrs = [float(x.strip()) if x.strip() and float(x.strip()) > 0 else 0 for x in npshr_str.split(';')] if npshr_str else []
        
        # Create curve data
        curve = {
            'impeller_diameter_mm': float(impeller_size) if impeller_size else 0,
            'performance_points': []
        }
        
        # Create performance points
        max_len = min(len(flows), len(heads), len(efficiencies))
        for i in range(max_len):
            point = {
                'flow_m3hr': flows[i],
                'head_m': heads[i],
                'efficiency_pct': efficiencies[i],
                'npshr_m': npshrs[i] if i < len(npshrs) else 0
            }
            curve['performance_points'].append(point)
        
        curves.append(curve)
        
    except Exception as e:
        logger.error(f"Error parsing performance curves: {e}")
    
    return curves

def normalize_pump_data(raw_data: dict) -> dict:
    """
    Normalize legacy pump data keys to modern, consistent field names.
    Accepts a dict with possible legacy keys and returns a dict with only normalized keys.
    """
    mapping = {
        'pPumpCode': 'pump_code',
        'pSuppName': 'manufacturer',
        'pPumpType': 'pump_type',
        'pPumpRange': 'model_series',
        'pPumpTestSpeed': 'test_speed_rpm',
        'pStages': 'stages',
        'pFilter1': 'pump_type',
        'pMaxQ': 'max_flow_m3hr',
        'pMaxH': 'max_head_m',
        'pMinImpD': 'min_impeller_mm',
        'pMaxImpD': 'max_impeller_mm',
        'pKWMax': 'max_power_kw',
        'pBEPFlowStd': 'bep_flow_m3hr',
        'pBEPHeadStd': 'bep_head_m',
        'pNPSHEOC': 'npshr_at_bep',
        # Add more mappings as needed
    }
    normalized = {}
    for k, v in raw_data.items():
        norm_key = mapping.get(k, k)
        normalized[norm_key] = v
    return normalized