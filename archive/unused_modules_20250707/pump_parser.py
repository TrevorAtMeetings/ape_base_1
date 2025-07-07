import logging
from typing import Dict, List, Tuple, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pump_engine import ParsedPumpData

logger = logging.getLogger(__name__)

def parse_pump_data(pump_json_obj: Dict[str, Any]) -> ParsedPumpData:
    """
    Parse raw pump JSON object into structured ParsedPumpData with performance curves.

    This function extracts pump information and parses the string-encoded curve data
    for multiple impeller sizes. It also calculates power curves from flow, head, and efficiency.

    Args:
        pump_json_obj: Raw pump object from JSON database

    Returns:
        ParsedPumpData object with parsed curves
    """
    try:
        obj_pump = pump_json_obj.get('objPump', {})
        pump_code = obj_pump.get('pPumpCode', 'Unknown')

        logger.debug(f"Parsing pump data for: {pump_code}")

        # Create the parsed pump data object
        parsed_pump = ParsedPumpData(pump_code, obj_pump)

        # Parse curve data
        parsed_pump.curves = _parse_performance_curves(obj_pump)

        logger.debug(f"Successfully parsed {len(parsed_pump.curves)} curves for pump {pump_code}")

        return parsed_pump

    except Exception as e:
        logger.error(f"Error parsing pump data: {str(e)}")
        # Return a basic ParsedPumpData object even on error
        pump_code = pump_json_obj.get('objPump', {}).get('pPumpCode', 'Unknown')
        return ParsedPumpData(pump_code, pump_json_obj.get('objPump', {}))

def _parse_performance_curves(obj_pump: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse the string-encoded performance curve data for all impeller sizes.

    The curve data is encoded as:
    - Multiple curves separated by '|'
    - Data points within a curve separated by ';'
    - Each curve corresponds to a different impeller diameter

    Args:
        obj_pump: Pump object dictionary

    Returns:
        List of curve dictionaries with parsed data points
    """
    curves = []

    try:
        # Get the number of curves and curve data
        num_curves = obj_pump.get('pHeadCurvesNo', 0)
        flow_data = obj_pump.get('pM_FLOW', '')
        head_data = obj_pump.get('pM_HEAD', '')
        eff_data = obj_pump.get('pM_EFF', '')
        npshr_data = obj_pump.get('pM_NP', '')
        impeller_data = obj_pump.get('pM_IMP', '')

        if not all([flow_data, head_data, eff_data]):
            logger.warning(f"Missing curve data for pump {obj_pump.get('pPumpCode', 'Unknown')}")
            return curves

        # Split curve data by '|' to get individual curves
        flow_curves = flow_data.split('|')
        head_curves = head_data.split('|')
        eff_curves = eff_data.split('|')
        npshr_curves = npshr_data.split('|') if npshr_data else []
        impeller_sizes = impeller_data.split('|') if impeller_data else []

        # Ensure we have consistent number of curves
        max_curves = min(len(flow_curves), len(head_curves), len(eff_curves))
        if num_curves > 0:
            max_curves = min(max_curves, num_curves)

        logger.debug(f"Processing {max_curves} curves")

        for i in range(max_curves):
            try:
                curve = _parse_single_curve(
                    flow_curves[i], 
                    head_curves[i], 
                    eff_curves[i],
                    npshr_curves[i] if i < len(npshr_curves) else '',
                    impeller_sizes[i] if i < len(impeller_sizes) else f"Curve_{i+1}",
                    obj_pump.get('pSG', 1.0)
                )

                if curve:
                    curves.append(curve)

            except Exception as e:
                logger.error(f"Error parsing curve {i}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error parsing performance curves: {str(e)}")

    return curves

def _parse_single_curve(flow_str: str, head_str: str, eff_str: str, 
                       npshr_str: str, impeller_size: str, sg: float = 1.0) -> Dict[str, Any]:
    """
    Parse a single performance curve from string data and calculate power curve.

    Args:
        flow_str: Flow data points separated by ';' (m³/hr)
        head_str: Head data points separated by ';' (m)
        eff_str: Efficiency data points separated by ';' (%)
        npshr_str: NPSHr data points separated by ';' (m)
        impeller_size: Impeller diameter or identifier
        sg: Specific gravity for power calculation

    Returns:
        Dictionary containing parsed curve data
    """
    try:
        # Parse data points
        flows = [float(x.strip()) for x in flow_str.split(';') if x.strip()]
        heads = [float(x.strip()) for x in head_str.split(';') if x.strip()]
        effs = [float(x.strip()) for x in eff_str.split(';') if x.strip()]
        npshrs = []

        if npshr_str:
            npshrs = [float(x.strip()) for x in npshr_str.split(';') if x.strip()]

        # Ensure all arrays have the same length
        min_length = min(len(flows), len(heads), len(effs))
        flows = flows[:min_length]
        heads = heads[:min_length]
        effs = effs[:min_length]

        if npshrs:
            npshrs = npshrs[:min_length]
        else:
            npshrs = [0.0] * min_length  # Default NPSHr if not provided

        # Calculate power curve points
        # Power (kW) = (Flow (m³/s) * Head (m) * SG * ρ * g) / (η * 1000)
        # Where ρ = 1000 kg/m³ for water, g = 9.81 m/s²
        powers = []
        for flow_m3hr, head_m, eff_pct in zip(flows, heads, effs):
            if eff_pct > 0:  # Avoid division by zero
                flow_m3s = flow_m3hr / 3600  # Convert m³/hr to m³/s
                eff_decimal = eff_pct / 100  # Convert % to decimal
                power_kw = (flow_m3s * head_m * sg * 1000 * 9.81) / (eff_decimal * 1000)
                powers.append(round(power_kw, 2))
            else:
                powers.append(0.0)

        # Create curve data structure
        curve = {
            'impeller_size': impeller_size,
            'flow_vs_head': list(zip(flows, heads)),
            'flow_vs_efficiency': list(zip(flows, effs)),
            'flow_vs_power': list(zip(flows, powers)),
            'flow_vs_npshr': list(zip(flows, npshrs)),
            'flow_range': (min(flows), max(flows)),
            'head_range': (min(heads), max(heads)),
            'efficiency_range': (min(effs), max(effs)),
            'power_range': (min(powers), max(powers)),
            'npshr_range': (min(npshrs), max(npshrs)) if npshrs else (0, 0)
        }

        logger.debug(f"Parsed curve for impeller {impeller_size}: {len(flows)} points")

        return curve

    except Exception as e:
        logger.error(f"Error parsing single curve: {str(e)}")
        return None

def get_curve_summary(parsed_pump: ParsedPumpData) -> Dict[str, Any]:
    """
    Generate a summary of the pump's performance characteristics.

    Args:
        parsed_pump: ParsedPumpData object

    Returns:
        Dictionary containing pump summary information
    """
    if not parsed_pump.curves:
        return {
            'pump_code': parsed_pump.pump_code,
            'num_curves': 0,
            'flow_range': (0, 0),
            'head_range': (0, 0),
            'max_efficiency': 0
        }

    # Aggregate ranges across all curves
    all_flows = []
    all_heads = []
    all_effs = []

    for curve in parsed_pump.curves:
        flows, heads = zip(*curve['flow_vs_head'])
        _, effs = zip(*curve['flow_vs_efficiency'])

        all_flows.extend(flows)
        all_heads.extend(heads)
        all_effs.extend(effs)

    return {
        'pump_code': parsed_pump.pump_code,
        'manufacturer': parsed_pump.manufacturer,
        'model': parsed_pump.model,
        'num_curves': len(parsed_pump.curves),
        'flow_range': (min(all_flows), max(all_flows)),
        'head_range': (min(all_heads), max(all_heads)),
        'max_efficiency': max(all_effs) if all_effs else 0,
        'bep_flow': parsed_pump.bep_flow_std,
        'bep_head': parsed_pump.bep_head_std,
        'bep_efficiency': parsed_pump.bep_eff_std
    }