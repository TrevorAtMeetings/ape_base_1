"""
APE Pumps Selection Engine
Consolidated module containing all pump selection logic
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import interpolate
from .pump_repository import get_pump_repository

logger = logging.getLogger(__name__)

# Data Structures
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

class ParsedPumpData:
    """Data structure to represent a pump with parsed performance curves"""

    def __init__(self, pump_code: str, pump_info: Dict[str, Any]):
        self.pump_code = pump_code
        self.pump_info = pump_info  # Store original pump_info for compatibility

        # Handle authentic APE data field mapping
        self.model = pump_info.get('pModel', pump_info.get('model', pump_code))
        self.manufacturer = pump_info.get('pSuppName', pump_info.get('manufacturer', 'APE Pumps'))
        self.series = pump_info.get('pSeries', pump_info.get('series', ''))
        self.application_type = pump_info.get('pFilter1', pump_info.get('application_type', ''))

        # Convert string values to float where needed
        self.max_flow_m3hr = float(pump_info.get('pMaxQ', pump_info.get('max_flow_m3hr', 0)))
        self.max_head_m = float(pump_info.get('pMaxH', pump_info.get('max_head_m', 0)))
        self.min_flow_m3hr = float(pump_info.get('pMinFlow', pump_info.get('min_flow_m3hr', 0)))
        self.rated_speed_rpm = float(pump_info.get('pPumpTestSpeed', pump_info.get('rated_speed_rpm', 1450)))

        # APE specific attributes
        self.bep_flow_std = float(pump_info.get('pBEPFlowStd', pump_info.get('bep_flow_std', 0)))
        self.bep_head_std = float(pump_info.get('pBEPHeadStd', pump_info.get('bep_head_std', 0)))
        self.bep_eff_std = float(pump_info.get('pBEPEffStd', pump_info.get('bep_eff_std', 75)))

        # Additional APE fields for compatibility
        self.filter1 = pump_info.get('pFilter1', '')
        self.filter2 = pump_info.get('pFilter2', '')
        self.filter3 = pump_info.get('pFilter3', '')
        self.filter4 = pump_info.get('pFilter4', '')
        self.filter5 = pump_info.get('pFilter5', '')

        self.curves = []  # Will be populated by parsing

    def __repr__(self):
        return f"ParsedPumpData({self.pump_code}: {self.model})"

# Utility Functions
def load_catalog_data(catalog_path: str = None) -> List[ParsedPumpData]:
    """Load pump data from repository and convert to ParsedPumpData objects"""
    try:
        # Use repository instead of direct file loading
        repository = get_pump_repository()
        catalog_data = repository.get_catalog_data()
        pump_models = catalog_data.get('pump_models', [])
        
        parsed_pumps = []

        for pump_model in pump_models:
            # For each pump model, create ParsedPumpData objects for each curve
            for curve in pump_model.get('curves', []):
                # Convert catalog format to legacy format for compatibility
                pump_info = {
                    'pPumpCode': pump_model['pump_code'],
                    'pSuppName': pump_model['manufacturer'],
                    'pModel': pump_model['pump_code'],
                    'pSeries': pump_model['model_series'],
                    'pFilter1': pump_model['pump_type'],
                    'pPumpTestSpeed': curve['test_speed_rpm'],
                    'pMaxQ': pump_model['specifications'].get('max_flow_m3hr', 0),
                    'pMaxH': pump_model['specifications'].get('max_head_m', 0),
                    'pMinImpD': pump_model['specifications'].get('min_impeller_mm', 0),
                    'pMaxImpD': pump_model['specifications'].get('max_impeller_mm', 0),

                    # Convert performance points to legacy semicolon format
                    'pM_FLOW': ';'.join(str(p['flow_m3hr']) for p in curve['performance_points']),
                    'pM_HEAD': ';'.join(str(p['head_m']) for p in curve['performance_points']),
                    'pM_EFF': ';'.join(str(p['efficiency_pct']) for p in curve['performance_points']),
                    'pM_NP': ';'.join(str(p['npshr_m']) if p['npshr_m'] and p['npshr_m'] > 0 else '0' for p in curve['performance_points']),
                    'pM_IMP': str(curve['impeller_diameter_mm'])
                }

                # Create ParsedPumpData object
                parsed_pump = ParsedPumpData(pump_model['pump_code'], pump_info)
                parsed_pumps.append(parsed_pump)

        logger.info(f"Pump Engine: Loaded {len(parsed_pumps)} pump curves from repository")
        return parsed_pumps

    except Exception as e:
        logger.error(f"Pump Engine: Error loading catalog data: {e}")
        return []

def load_all_pump_data() -> List[ParsedPumpData]:
    """Load and parse pump database into a list of ParsedPumpData objects."""
    try:
        # Use repository for data loading
        return load_catalog_data()
    except Exception as e:
        logger.error(f"Pump Engine: Error loading pump data: {e}")
        return []

def _normalize_pump_data(pump_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw pump data field names to standard Pythonic conventions."""
    if 'objPump' in pump_entry:
        obj_pump = pump_entry['objPump']
        normalized = {
            'pump_code': obj_pump.get('pPumpCode', ''),
            'supplier_name': obj_pump.get('pSuppName', ''),
            'kw_max': obj_pump.get('pKWMax', 0),
            'bep_flow': obj_pump.get('pBEPFlo', 0),
            'pump_test_speed': obj_pump.get('pPumpTestSpeed', 0),
            'filter1': obj_pump.get('pFilter1', ''),
            'curve_flow_m3hr': obj_pump.get('pM_FLOW', ''),
            'curve_head_m': obj_pump.get('pM_HEAD', ''),
            'curve_efficiency_pct': obj_pump.get('pM_EFF', ''),
            'curve_npshr_m': obj_pump.get('pM_NP', ''),
            'impeller_sizes': obj_pump.get('pM_IMP', ''),
            'sg': obj_pump.get('pSG', 1.0),
            # Keep original objPump for backward compatibility
            'objPump': obj_pump
        }
        return normalized
    else:
        # Already normalized or different format
        return pump_entry

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

# Performance Calculation Functions
def interpolate_value(target_x: float, curve_points: List[Tuple[float, float]]) -> Tuple[Optional[float], bool]:
    """
    Interpolate a Y value for a given X value using linear interpolation.
    Returns: (value, was_extrapolated) tuple
    """
    if not curve_points or len(curve_points) < 2:
        return None, False

    # Sort points by x value
    sorted_points = sorted(curve_points, key=lambda p: p[0])
    x_values = [p[0] for p in sorted_points]
    y_values = [p[1] for p in sorted_points]

    # Check if target is within range with 20% extrapolation margin
    x_min, x_max = min(x_values), max(x_values)
    x_range = x_max - x_min
    extrapolation_margin = 0.2 * x_range

    # Check if extrapolation is needed
    was_extrapolated = target_x < x_min or target_x > x_max

    # Allow extrapolation within 20% of the curve range
    if target_x < (x_min - extrapolation_margin) or target_x > (x_max + extrapolation_margin):
        return None, False

    # Log extrapolation warning with detailed context
    if was_extrapolated:
        logger.debug(f"Extrapolating value for x={target_x} (original range: {x_min}-{x_max}, with 20% margin: {x_min - extrapolation_margin:.1f}-{x_max + extrapolation_margin:.1f})")

    # Use scipy interpolation with extrapolation enabled
    try:
        from scipy.interpolate import interp1d
        # Use bounds_error=False with fill_value='extrapolate' for extrapolation
        f = interp1d(x_values, y_values, kind='linear', bounds_error=False, 
                    fill_value='extrapolate')
        result = f(target_x)
        result_value = float(result)
        logger.debug(f"Interpolation SUCCESS for x={target_x}: {result_value} (extrapolated: {was_extrapolated})")
        return result_value, was_extrapolated
    except Exception as e:
        logger.warning(f"Scipy interpolation failed for x={target_x}: {e}, using manual fallback")
        # Manual linear interpolation fallback
        try:
            result = _linear_interpolate(target_x, sorted_points)
            if result is None:
                logger.error(f"Manual interpolation returned None for x={target_x}, using fallback value")
                return 0.0, was_extrapolated
            logger.info(f"Manual interpolation SUCCESS for x={target_x}: {result} (extrapolated: {was_extrapolated})")
            return float(result), was_extrapolated
        except Exception as e2:
            logger.error(f"Both interpolation methods failed for x={target_x}: {e2}")
            return 0.0, was_extrapolated

def _linear_interpolate(target_x: float, sorted_points: List[Tuple[float, float]]) -> float:
    """Manual linear interpolation implementation as fallback."""
    for i in range(len(sorted_points) - 1):
        x1, y1 = sorted_points[i]
        x2, y2 = sorted_points[i + 1]

        if x1 <= target_x <= x2:
            if x2 == x1:
                return y1
            ratio = (target_x - x1) / (x2 - x1)
            return y1 + ratio * (y2 - y1)

    return sorted_points[0][1]  # Fallback

def calculate_operating_point(parsed_pump: ParsedPumpData, curve_index: int, target_flow: float) -> Dict[str, Any]:
    """Calculate the operating point for a specific pump curve at a target flow rate."""
    # Parse curves from pump_info
    curves = _parse_performance_curves(parsed_pump.pump_info)

    if curve_index >= len(curves):
        return {'error': 'Invalid curve index'}

    curve = curves[curve_index]

    # Check flow range compatibility
    flow_points = [p[0] for p in curve['flow_vs_head']]
    curve_min, curve_max = min(flow_points), max(flow_points)

    # Allow extrapolation within 20% beyond curve range for better coverage
    extrapolation_margin = 0.2
    extended_min = curve_min * (1 - extrapolation_margin)
    extended_max = curve_max * (1 + extrapolation_margin)

    if target_flow < extended_min or target_flow > extended_max:
        return {
            'error': f'Target flow {target_flow} m³/hr outside feasible range [{extended_min:.1f}, {extended_max:.1f}] for {curve["impeller_size"]}',
            'curve_range_min': curve_min,
            'curve_range_max': curve_max
        }

    # Interpolate values at target flow with extrapolation tracking
    head, head_extrapolated = interpolate_value(target_flow, curve['flow_vs_head'])
    efficiency, efficiency_extrapolated = interpolate_value(target_flow, curve['flow_vs_efficiency'])
    power, power_extrapolated = interpolate_value(target_flow, curve['flow_vs_power'])

    # Handle NPSH data availability
    if curve.get('npsh_data_available', True) and curve['flow_vs_npshr']:
        npshr, npshr_extrapolated = interpolate_value(target_flow, curve['flow_vs_npshr'])
    else:
        npshr, npshr_extrapolated = None, False

    # Track overall extrapolation status
    any_extrapolated = head_extrapolated or efficiency_extrapolated or power_extrapolated or npshr_extrapolated

    # Validate interpolation results and provide fallbacks
    if head is None:
        head = _linear_interpolate(target_flow, curve['flow_vs_head'])
    if efficiency is None:
        efficiency = _linear_interpolate(target_flow, curve['flow_vs_efficiency'])
    if power is None:
        power = _linear_interpolate(target_flow, curve['flow_vs_power'])
    if npshr is None and curve.get('npsh_data_available', True):
        npshr = _linear_interpolate(target_flow, curve['flow_vs_npshr'])

    # Final validation - if still None, use reasonable estimates
    if any(val is None for val in [head, efficiency, power]) or any(val <= 0 for val in [head, efficiency, power] if val is not None):
        logger.warning(f"Using fallback interpolation for flow {target_flow} m³/hr")
        if head is None or head <= 0:
            head = max(flow_points) * 0.8  # Conservative head estimate
        if efficiency is None or efficiency <= 0:
            efficiency = 75.0  # Conservative efficiency estimate
        if power is None or power <= 0:
            power = (target_flow * head * 1.0 * 9.81) / (0.75 * 1000)  # Conservative power calc

    # Handle NPSH: None indicates data not available, don't estimate
    if npshr is None and not curve.get('npsh_data_available', True):
        # Keep as None to indicate "N/A" - don't estimate missing NPSH data
        pass
    elif npshr is None:
        npshr = 3.0  # Conservative NPSH estimate only if data should be available

    return {
        'curve_index': curve_index,
        'impeller_size': curve['impeller_size'],
        'flow_m3hr': target_flow,
        'achieved_head_m': head,
        'achieved_efficiency_pct': efficiency,
        'achieved_power_kw': power,
        'achieved_npshr_m': npshr,
        'head_was_extrapolated': head_extrapolated,
        'efficiency_was_extrapolated': efficiency_extrapolated,
        'power_was_extrapolated': power_extrapolated,
        'npshr_was_extrapolated': npshr_extrapolated,
        'operating_point_overall_extrapolated': any_extrapolated,
        'curve_range_min': curve_min,
        'curve_range_max': curve_max,
        'extrapolated': target_flow < curve_min or target_flow > curve_max
    }

# Pump Parsing Functions
def parse_pump_data(pump_json_obj: Dict[str, Any]) -> ParsedPumpData:
    """Parse raw pump JSON object into structured ParsedPumpData with performance curves."""
    # Handle authentic APE data structure with objPump wrapper
    if 'objPump' in pump_json_obj:
        obj_pump = pump_json_obj['objPump']
        pump_code = obj_pump.get('pPumpCode', '')
    else:
        obj_pump = pump_json_obj
        pump_code = pump_json_obj.get('pump_code', '')

    parsed_pump = ParsedPumpData(pump_code, obj_pump)

    # Parse performance curves using the correct data structure
    parsed_pump.curves = _parse_performance_curves(obj_pump)

    return parsed_pump

def _parse_performance_curves(obj_pump: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse the string-encoded performance curve data for all impeller sizes."""
    curves = []

    try:
        # Get curve data strings using authentic APE field names
        flow_data = obj_pump.get('pM_FLOW', '')
        head_data = obj_pump.get('pM_HEAD', '')
        eff_data = obj_pump.get('pM_EFF', '')
        npshr_data = obj_pump.get('pM_NP', '')
        impeller_sizes_str = obj_pump.get('pM_IMP', '')

        # Parse impeller sizes - handle both space and pipe separated formats
        if impeller_sizes_str:
            # Clean up the string and split by spaces, then filter out empty values
            impeller_parts = [x.strip() for x in impeller_sizes_str.replace('|', ' ').split() if x.strip()]
            impeller_sizes = [x for x in impeller_parts if x.replace('.', '').isdigit()]
        else:
            impeller_sizes = ['Standard']

        # Split by '|' for multiple curves (different impeller sizes)
        flow_curves = flow_data.split('|') if flow_data else ['']
        head_curves = head_data.split('|') if head_data else ['']
        eff_curves = eff_data.split('|') if eff_data else ['']
        npshr_curves = npshr_data.split('|') if npshr_data else ['']

        # Parse each curve
        for i, (flow_str, head_str, eff_str, npshr_str) in enumerate(zip(flow_curves, head_curves, eff_curves, npshr_curves)):
            impeller_size = impeller_sizes[i] if i < len(impeller_sizes) else f"Size_{i+1}"

            curve = _parse_single_curve(flow_str, head_str, eff_str, npshr_str, impeller_size)
            if curve:
                curves.append(curve)

    except Exception as e:
        logger.warning(f"Error parsing curves for pump {obj_pump.get('pump_code', 'unknown')}: {e}")

    return curves

def _parse_single_curve(flow_str: str, head_str: str, eff_str: str, npshr_str: str, impeller_size: str, sg: float = 1.0) -> Dict[str, Any]:
    """Parse a single performance curve from string data and calculate power curve."""
    try:
        # Parse data points (separated by ';')
        flows = [float(x.strip()) for x in flow_str.split(';') if x.strip()]
        heads = [float(x.strip()) for x in head_str.split(';') if x.strip()]
        effs = [float(x.strip()) for x in eff_str.split(';') if x.strip()]
        npshrs = [float(x.strip()) for x in npshr_str.split(';') if x.strip()]

        if not flows or len(flows) != len(heads) or len(flows) != len(effs):
            return None

        # Calculate power curve: P(kW) = (Q * H * ρ * g) / (η * 1000)
        powers = []
        for flow, head, eff in zip(flows, heads, effs):
            if eff > 0:
                power_kw = (flow * head * sg * 9.81) / (eff/100 * 1000)
                powers.append(power_kw)
            else:
                powers.append(0)

        # Handle NPSH data - check if all zeros or missing
        npsh_data_available = True
        if not npshrs or all(npsh == 0.0 for npsh in npshrs):
            npsh_data_available = False
            npshrs = []  # Empty list indicates no NPSH data
        else:
            # Pad NPSH data if shorter than flow data
            while len(npshrs) < len(flows):
                npshrs.append(npshrs[-1] if npshrs else 3.0)

        return {
            'impeller_size': impeller_size,
            'flow_vs_head': list(zip(flows, heads)),
            'flow_vs_efficiency': list(zip(flows, effs)),
            'flow_vs_power': list(zip(flows, powers)),
            'flow_vs_npshr': list(zip(flows, npshrs)) if npsh_data_available else [],
            'npsh_data_available': npsh_data_available
        }

    except Exception as e:
        logger.warning(f"Error parsing single curve: {e}")
        return None

# Selection Engine Functions
def find_best_pumps(all_parsed_pumps: List[ParsedPumpData], site_requirements: SiteRequirements) -> List[Dict[str, Any]]:
    """Find the top 3 best pump selections based on site requirements."""
    evaluations = []

    # Filter pumps by type if specified
    filtered_pumps = all_parsed_pumps
    if hasattr(site_requirements, 'pump_type') and site_requirements.pump_type and site_requirements.pump_type != 'General':
        filtered_pumps = [pump for pump in all_parsed_pumps if _matches_pump_type(pump.pump_code, site_requirements.pump_type)]
        logger.info(f"Filtered to {len(filtered_pumps)} pumps of type {site_requirements.pump_type}")

    for pump in filtered_pumps:
        try:
            evaluation = evaluate_pump_for_requirements(pump, site_requirements)
            # Apply minimum quality threshold - reject pumps with severe data issues
            if evaluation and evaluation.get('overall_score', 0) > 25:  # Raised threshold
                evaluations.append(evaluation)
        except Exception as e:
            logger.warning(f"Error evaluating pump {pump.pump_code}: {e}")
            continue

    # Sort by overall score (descending)
    evaluations.sort(key=lambda x: x.get('overall_score', 0), reverse=True)

    # Return top 3 with enhanced details
    top_3 = evaluations[:3]
    for i, eval in enumerate(top_3):
        eval['rank'] = i + 1
        eval['selection_reason'] = _generate_selection_reason(eval, i + 1)

    return top_3

def _matches_pump_type(pump_code: str, pump_type: str) -> bool:
    """Check if pump code matches the specified APE pump category."""
    pump_code_upper = pump_code.upper()

    if pump_type == 'General' or not pump_type:
        return True

    # APE Pump Categories based on actual dataset analysis
    if pump_type == 'END_SUCTION':
        # Single stage centrifugal pumps (no stage indicators)
        return not any(indicator in pump_code_upper for indicator in ['2F', '2P', '3P', '4P', '6P', 'ALE', 'HSC'])

    elif pump_type == 'MULTI_STAGE':
        # Multi-stage pumps with stage indicators
        return any(indicator in pump_code_upper for indicator in ['2F', '2P', '3P', '4P', '6P', 'STAGE', 'MS'])

    elif pump_type == 'HSC':
        # Horizontal Split Case
        return 'HSC' in pump_code_upper or 'HSP' in pump_code_upper

    elif pump_type == 'AXIAL_FLOW':
        # Axial flow pumps - check for ALE designation
        return 'ALE' in pump_code_upper or 'AXIAL' in pump_code_upper

    elif pump_type == 'VTP':
        # Vertical Turbine Pumps
        return any(indicator in pump_code_upper for indicator in ['VTP', 'VERT', 'VERTICAL'])

    return False

def evaluate_pump_for_requirements(parsed_pump: ParsedPumpData, site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Evaluate a single pump against site requirements."""
    # Initialize default evaluation structure
    evaluation = {
        'pump_code': parsed_pump.pump_code,
        'model': parsed_pump.model,
        'manufacturer': parsed_pump.manufacturer,
        'operating_point': {},
        'bep_analysis': {},
        'npsh_analysis': {},
        'power_analysis': {},
        'overall_score': 0,
        'selection_reason': 'Pump not suitable for requirements',
        'error': None
    }

    if not parsed_pump.curves:
        evaluation['error'] = 'No performance curves available'
        return evaluation

    try:
        # Find best curve for the duty point
        best_curve_index, operating_point = find_best_curve_for_duty(
            parsed_pump, site_requirements.flow_m3hr, site_requirements.head_m
        )

        if operating_point and not operating_point.get('error'):
            evaluation['operating_point'] = operating_point

            # Enhanced analysis with proper error handling
            evaluation['bep_analysis'] = _analyze_bep_performance(operating_point, parsed_pump)
            evaluation['npsh_analysis'] = _analyze_npsh_requirements(operating_point, site_requirements)
            evaluation['power_analysis'] = _analyze_power_consumption(operating_point)

            # Calculate overall score with detailed error tracking
            logger.debug(f"Calculating suitability score for pump {parsed_pump.pump_code}")
            logger.debug(f"Operating point data: {operating_point}")

            try:
                base_score = calculate_pump_suitability_score(
                    parsed_pump, site_requirements.flow_m3hr, site_requirements.head_m, site_requirements
                )
                logger.info(f"Suitability score calculated successfully: {base_score}")

                if base_score and base_score.get('overall_score', 0) > 0:
                    evaluation['overall_score'] = base_score.get('overall_score', 0)
                    evaluation['selection_reason'] = _generate_selection_reason(evaluation, 1)
                    logger.info(f"Pump {parsed_pump.pump_code} evaluation completed with score: {evaluation['overall_score']}")
                else:
                    logger.warning(f"Base score invalid for pump {parsed_pump.pump_code}: {base_score}")

            except Exception as score_error:
                logger.error(f"Error calculating suitability score for pump {parsed_pump.pump_code}: {score_error}")
                evaluation['error'] = f'Scoring error: {str(score_error)}'
        else:
            evaluation['error'] = operating_point.get('error', 'Unable to find suitable operating point')

    except Exception as e:
        logger.error(f"Error evaluating pump {parsed_pump.pump_code}: {str(e)}")
        evaluation['error'] = f'Evaluation error: {str(e)}'

    return evaluation

def find_best_curve_for_duty(parsed_pump: ParsedPumpData, target_flow: float, target_head: float) -> Tuple[int, Dict[str, Any]]:
    """Find the best curve (impeller size) for a given duty point."""
    best_score = 0
    best_index = 0
    best_operating_point = {}

    # Parse curves from pump_info
    curves = _parse_performance_curves(parsed_pump.pump_info)

    for i, curve in enumerate(curves):
        operating_point = calculate_operating_point(parsed_pump, i, target_flow)

        if operating_point.get('error'):
            continue

        achieved_head = operating_point.get('achieved_head_m')
        achieved_efficiency = operating_point.get('achieved_efficiency_pct')

        # Comprehensive None checks with logging
        if achieved_head is None:
            logger.warning(f"Head is None for pump {parsed_pump.pump_code}, curve {i}, flow {target_flow}")
            continue

        if achieved_efficiency is None:
            logger.warning(f"Efficiency is None for pump {parsed_pump.pump_code}, curve {i}, flow {target_flow}")
            achieved_efficiency = 0

        if achieved_head <= 0:
            logger.warning(f"Head is non-positive ({achieved_head}) for pump {parsed_pump.pump_code}, curve {i}")
            continue

        # Safe numerical operations with validated inputs
        try:
            head_match_score = 100 - abs(achieved_head - target_head) / target_head * 100
            efficiency_score = max(0, achieved_efficiency)

            # Combined score (weighted)
            combined_score = head_match_score * 0.7 + efficiency_score * 0.3
        except Exception as e:
            logger.error(f"Error calculating score for pump {parsed_pump.pump_code}, curve {i}: {e}")
            continue

        if combined_score > best_score:
            best_score = combined_score
            best_index = i
            best_operating_point = operating_point

    return best_index, best_operating_point

def calculate_pump_suitability_score(parsed_pump: ParsedPumpData, target_flow: float, target_head: float, requirements: SiteRequirements = None) -> Dict[str, Any]:
    """Calculate an overall suitability score for a pump given specific requirements."""
    # Parse curves from pump_info
    curves = _parse_performance_curves(parsed_pump.pump_info)
    if not curves:
        return {'overall_score': 0, 'error': 'No performance curves available'}

    best_curve_index, operating_point = find_best_curve_for_duty(parsed_pump, target_flow, target_head)

    if operating_point.get('error'):
        return {'overall_score': 0, 'error': operating_point['error']}

    achieved_head = operating_point.get('achieved_head_m')
    achieved_eff = operating_point.get('achieved_efficiency_pct')

    # Robust None checks for all numerical operations
    if achieved_head is None:
        logger.warning(f"Head is None for pump {parsed_pump.pump_code}, assigning zero head accuracy score.")
        head_accuracy = 0
    else:
        head_accuracy = max(0, 100 - abs(achieved_head - target_head) / target_head * 100)

    if achieved_eff is None:
        logger.warning(f"Efficiency is None for pump {parsed_pump.pump_code}, assigning zero efficiency score.")
        efficiency_score = 0
    else:
        efficiency_score = min(100, achieved_eff)

    # Apply penalties for data quality issues
    extrapolation_penalty = 0
    efficiency_penalty = 0

    # Severe penalty for extrapolated results
    if operating_point.get('extrapolated', False):
        extrapolation_penalty = 25

    # Penalty for unrealistic efficiency values
    if achieved_eff is not None:
        if achieved_eff < 10:  # Unrealistically low efficiency
            efficiency_penalty = 30
        elif achieved_eff > 95:  # Unrealistically high efficiency for centrifugal pumps
            efficiency_penalty = 15

    # Overall score with penalties applied
    base_score = (head_accuracy or 0) * 0.6 + (efficiency_score or 0) * 0.4
    overall_score = max(0, base_score - extrapolation_penalty - efficiency_penalty)

    return {
        'overall_score': overall_score,
        'head_accuracy_score': head_accuracy,
        'efficiency_score': efficiency_score,
        'operating_point': operating_point,
        'best_curve_index': best_curve_index
    }

def _analyze_bep_performance(operating_point: Dict[str, Any], parsed_pump: ParsedPumpData) -> Dict[str, Any]:
    """Analyze Best Efficiency Point performance."""
    try:
        # Use correct field names from operating_point and handle None values
        efficiency = operating_point.get('achieved_efficiency_pct')
        flow = operating_point.get('flow_m3hr') or operating_point.get('target_flow_m3hr')

        # Handle None values robustly
        if efficiency is None:
            efficiency = 0
            logger.warning(f"Efficiency is None in BEP analysis for pump {parsed_pump.pump_code}")

        if flow is None:
            flow = 0
            logger.warning(f"Flow is None in BEP analysis for pump {parsed_pump.pump_code}")

        # Estimate BEP from pump data with safe defaults
        bep_flow = getattr(parsed_pump, 'bep_flow_std', max(flow * 1.1, 100)) if flow > 0 else 100
        bep_efficiency = getattr(parsed_pump, 'bep_eff_std', max(75, efficiency)) if efficiency > 0 else 75

        # Safe division operations
        efficiency_ratio = efficiency / bep_efficiency if bep_efficiency > 0 and efficiency is not None else 0
        flow_ratio = flow / bep_flow if bep_flow > 0 and flow is not None else 0

        return {
            'operating_efficiency': efficiency,
            'bep_efficiency': bep_efficiency,
            'efficiency_ratio': efficiency_ratio,
            'distance_from_bep': abs(1.0 - flow_ratio) if flow_ratio is not None else 1.0,
            'performance_rating': 'Excellent' if efficiency_ratio > 0.9 else 'Good' if efficiency_ratio > 0.8 else 'Acceptable'
        }
    except Exception as e:
        logger.warning(f"BEP analysis error: {e}")
        return {
            'operating_efficiency': 0,
            'bep_efficiency': 75,
            'efficiency_ratio': 0,
            'distance_from_bep': 1.0,
            'performance_rating': 'Data Unavailable'
        }

def _analyze_npsh_requirements(operating_point: Dict[str, Any], site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Analyze NPSH requirements and availability."""
    try:
        npshr_required = operating_point.get('achieved_npshr_m')

        # Check if NPSH data is available
        if npshr_required is None:
            return {
                'npshr_at_duty': None,
                'npsha_available': None,
                'npsh_margin': None,
                'cavitation_risk': 'Unknown',
                'data_status': 'NPSH Required data not available for this pump/curve',
                'npsh_score': -5  # Slight penalty for unknown risk
            }

        # Calculate NPSHa from site conditions
        elevation = getattr(site_requirements, 'elevation_m', 0)
        temperature = getattr(site_requirements, 'temperature_c', 20)

        # Standard atmospheric pressure minus vapor pressure and losses
        atmospheric_pressure = 10.33 - (elevation * 0.001)  # Approx correction for elevation
        vapor_pressure = 0.024 if temperature <= 20 else 0.048  # Simplified vapor pressure
        npsha_available = atmospheric_pressure - vapor_pressure - 1.0  # 1m safety margin

        npsh_margin = npsha_available - npshr_required

        # Calculate NPSH score based on margin
        if npsh_margin > 2:
            npsh_score = 20  # Excellent margin
            risk = 'Low'
        elif npsh_margin > 1:
            npsh_score = 15  # Good margin
            risk = 'Low'
        elif npsh_margin > 0:
            npsh_score = 5   # Minimal margin
            risk = 'Medium'
        else:
            npsh_score = -30  # Inadequate - major penalty
            risk = 'High'

        return {
            'npshr_at_duty': npshr_required,
            'npsha_available': npsha_available,
            'npsh_margin': npsh_margin,
            'cavitation_risk': risk,
            'data_status': 'Available',
            'npsh_score': npsh_score
        }
    except Exception as e:
        logger.warning(f"NPSH analysis error: {e}")
        return {
            'npshr_at_duty': None,
            'npsha_available': None,
            'npsh_margin': None,
            'cavitation_risk': 'Unknown',
            'data_status': f'Error in NPSH analysis: {e}',
            'npsh_score': -5
        }

def _analyze_power_consumption(operating_point: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze power consumption and efficiency."""
    try:
        # Use correct field names and handle None values
        power_kw = operating_point.get('achieved_power_kw')
        efficiency = operating_point.get('achieved_efficiency_pct')
        flow = operating_point.get('flow_m3hr') or operating_point.get('target_flow_m3hr')

        # Handle None values robustly
        if power_kw is None:
            power_kw = 0
            logger.warning(f"Power is None in power analysis")

        if efficiency is None:
            efficiency = 0
            logger.warning(f"Efficiency is None in power analysis")

        if flow is None:
            flow = 0
            logger.warning(f"Flow is None in power analysis")

        # Calculate specific power consumption with safe division
        specific_power = power_kw / flow if flow > 0 and power_kw is not None else 0

        # Estimate annual energy consumption (8760 hours/year)
        annual_energy_kwh = power_kw * 8760 if power_kw is not None else 0

        return {
            'operating_power_kw': power_kw,
            'efficiency_pct': efficiency,
            'specific_power_kwh_m3': specific_power,
            'annual_energy_kwh': annual_energy_kwh,
            'power_rating': 'Efficient' if efficiency > 80 else 'Standard' if efficiency > 70 else 'Low Efficiency'
        }
    except Exception as e:
        logger.warning(f"Power analysis error: {e}")
        return {
            'operating_power_kw': 0,
            'efficiency_pct': 0,
            'specific_power_kwh_m3': 0,
            'annual_energy_kwh': 0,
            'power_rating': 'Data Unavailable'
        }

def _generate_selection_reason(evaluation: Dict[str, Any], rank: int) -> str:
    """Generate a concise selection reason for the pump ranking."""
    score = evaluation.get('overall_score', 0)
    efficiency = evaluation.get('operating_point', {}).get('achieved_efficiency_pct', 0)

    if rank == 1:
        return f"Top recommendation with {score:.1f}% suitability score and {efficiency:.1f}% efficiency at operating point"
    elif rank == 2:
        return f"Strong alternative with {score:.1f}% suitability score, good efficiency performance"
    else:
        return f"Viable option with {score:.1f}% suitability score, suitable for the application"

def calculate_power_curve(performance_points):
    """Calculate power values for performance points using exact VBA formula."""
    powers = []
    for p in performance_points:
        # Use existing power data if available and valid
        if p.get('power_kw') and p.get('power_kw') > 0:
            powers.append(round(p['power_kw'], 3))
        elif p.get('efficiency_pct') and p.get('efficiency_pct') > 0 and p.get('flow_m3hr', 0) > 0:
            # VBA Formula: P(kW) = (Flow_m3hr * Head_m * SG * 9.81) / (Efficiency_decimal * 3600)
            # This matches the VBA: flowVal * conFlow * headVal * conHead * 9.81 / (effVal/100)
            # where conFlow = 1/3600 (m3/hr to m3/s), conHead = 1 (m to m), SG = 1 for water
            flow_m3hr = p['flow_m3hr']
            head_m = p['head_m']
            efficiency_decimal = p['efficiency_pct'] / 100.0
            sg = 1.0  # Specific gravity for water

            calc_power = (flow_m3hr * head_m * sg * 9.81) / (efficiency_decimal * 3600)
            powers.append(round(calc_power, 3))  # Round to 3 decimal places like VBA
        elif p.get('flow_m3hr', 0) == 0:
            powers.append(0.0)
        else:
            # For missing efficiency data, return 0.0 instead of None
            powers.append(0.0)
    return powers