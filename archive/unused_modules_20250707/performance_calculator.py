import logging
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pump_engine import ParsedPumpData, SiteRequirements

logger = logging.getLogger(__name__)

def interpolate_value(target_x: float, curve_points: List[Tuple[float, float]]) -> Optional[float]:
    """
    Interpolate a Y value for a given X value using linear interpolation.

    Args:
        target_x: The X value to interpolate for
        curve_points: List of (x, y) tuples representing the curve

    Returns:
        Interpolated Y value or None if target_x is outside curve range
    """
    try:
        if not curve_points or len(curve_points) < 2:
            logger.warning("Insufficient curve points for interpolation")
            return None

        # Sort points by x value
        sorted_points = sorted(curve_points, key=lambda p: p[0])
        x_values = [p[0] for p in sorted_points]
        y_values = [p[1] for p in sorted_points]

        # Check if target is within range with some tolerance
        x_min, x_max = min(x_values), max(x_values)
        tolerance = (x_max - x_min) * 0.1  # 10% tolerance for extrapolation

        if target_x < (x_min - tolerance) or target_x > (x_max + tolerance):
            logger.warning(f"Target value {target_x} far outside curve range [{x_min}, {x_max}] with tolerance")
            return None

        # Allow limited extrapolation within tolerance
        if target_x < x_min:
            logger.debug(f"Extrapolating below minimum: {target_x} < {x_min}")
        elif target_x > x_max:
            logger.debug(f"Extrapolating above maximum: {target_x} > {x_max}")

        # Use numpy interpolation if available, otherwise implement linear interpolation
        try:
            return float(np.interp(target_x, x_values, y_values))
        except ImportError:
            # Fallback to manual linear interpolation
            return _linear_interpolate(target_x, sorted_points)

    except Exception as e:
        logger.error(f"Error in interpolation: {str(e)}")
        return None

def _linear_interpolate(target_x: float, sorted_points: List[Tuple[float, float]]) -> float:
    """
    Manual linear interpolation implementation as fallback.

    Args:
        target_x: The X value to interpolate for
        sorted_points: List of (x, y) tuples sorted by x value

    Returns:
        Interpolated Y value
    """
    # Find the two points that bracket target_x
    for i in range(len(sorted_points) - 1):
        x1, y1 = sorted_points[i]
        x2, y2 = sorted_points[i + 1]

        if x1 <= target_x <= x2:
            if x1 == x2:  # Avoid division by zero
                return y1

            # Linear interpolation formula: y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
            return y1 + (y2 - y1) * (target_x - x1) / (x2 - x1)

    # This should not happen if target_x is within range
    return sorted_points[0][1]

def calculate_operating_point(parsed_pump: ParsedPumpData, curve_index: int, 
                            target_flow: float) -> Optional[Dict[str, Any]]:
    """
    Calculate the operating point for a specific pump curve at a target flow rate.

    Args:
        parsed_pump: ParsedPumpData object
        curve_index: Index of the curve to use
        target_flow: Target flow rate in m³/hr

    Returns:
        Dictionary containing operating point details
    """
    try:
        if curve_index >= len(parsed_pump.curves):
            raise ValueError(f"Curve index {curve_index} out of range")

        curve = parsed_pump.curves[curve_index]

        # Interpolate performance values at target flow with safety checks
        head = interpolate_value(target_flow, curve['flow_vs_head'])
        efficiency = interpolate_value(target_flow, curve['flow_vs_efficiency'])
        power = interpolate_value(target_flow, curve['flow_vs_power'])
        npshr = interpolate_value(target_flow, curve['flow_vs_npshr'])

        # Check if interpolation failed (None values)
        failed_interpolations = []
        if head is None:
            failed_interpolations.append('head')
        if efficiency is None:
            failed_interpolations.append('efficiency')
        if power is None:
            failed_interpolations.append('power')
        if npshr is None:
            failed_interpolations.append('npshr')

        if failed_interpolations:
            logger.warning(f"Interpolation failed for pump {parsed_pump.pump_code} at flow {target_flow} - failed: {failed_interpolations}")

            # Try to provide partial results if some interpolations succeeded
            return {
                'pump_code': parsed_pump.pump_code,
                'curve_index': curve_index,
                'impeller_size': curve.get('impeller_size', 'Unknown'),
                'target_flow_m3hr': target_flow,
                'achieved_head_m': head,
                'achieved_efficiency_pct': efficiency,
                'achieved_power_kw': power,
                'achieved_npshr_m': npshr,
                'within_curve_range': False,
                'error': f'Interpolation failed for: {", ".join(failed_interpolations)}',
                'partial_result': len(failed_interpolations) < 4
            }

        # Calculate additional metrics
        operating_point = {
            'pump_code': parsed_pump.pump_code,
            'curve_index': curve_index,
            'impeller_size': curve['impeller_size'],
            'target_flow_m3hr': target_flow,
            'achieved_head_m': head,
            'achieved_efficiency_pct': efficiency,
            'achieved_power_kw': power,
            'achieved_npshr_m': npshr,
            'within_curve_range': True,
            'distance_from_bep': None,
            'efficiency_ratio': None
        }

        # Check if operating point is within curve range
        flow_points = [p[0] for p in curve['flow_vs_head']]
        flow_min, flow_max = min(flow_points), max(flow_points)
        if target_flow < flow_min or target_flow > flow_max:
            operating_point['within_curve_range'] = False
            logger.warning(f"Target flow {target_flow} outside curve range [{flow_min}, {flow_max}]")

        # Calculate distance from BEP if BEP data is available
        if parsed_pump.bep_flow_std and parsed_pump.bep_flow_std > 0:
            bep_flow = parsed_pump.bep_flow_std
            operating_point['distance_from_bep'] = abs(target_flow - bep_flow) / bep_flow * 100

        # Calculate efficiency ratio compared to BEP
        if efficiency and parsed_pump.bep_eff_std and parsed_pump.bep_eff_std > 0:
            operating_point['efficiency_ratio'] = efficiency / parsed_pump.bep_eff_std

        # Add quality assessment
        operating_point['quality_assessment'] = _assess_operating_point_quality(
            operating_point, parsed_pump
        )

        logger.debug(f"Calculated operating point for {parsed_pump.pump_code}: "
                    f"Flow={target_flow}, Head={head}, Eff={efficiency}%")

        return operating_point

    except Exception as e:
        logger.error(f"Error calculating operating point: {str(e)}")
        return {
            'pump_code': parsed_pump.pump_code,
            'curve_index': curve_index,
            'target_flow_m3hr': target_flow,
            'achieved_head_m': None,
            'achieved_efficiency_pct': None,
            'achieved_power_kw': None,
            'achieved_npshr_m': None,
            'within_curve_range': False,
            'error': str(e)
        }

def _assess_operating_point_quality(operating_point: Dict[str, Any], 
                                  parsed_pump: ParsedPumpData) -> Dict[str, Any]:
    """
    Assess the quality of an operating point based on various criteria.

    Args:
        operating_point: Operating point data
        parsed_pump: ParsedPumpData object

    Returns:
        Dictionary containing quality assessment
    """
    assessment = {
        'overall_score': 0,
        'efficiency_score': 0,
        'bep_proximity_score': 0,
        'range_score': 0,
        'recommendations': []
    }

    try:
        # Efficiency scoring (0-40 points)
        efficiency = operating_point.get('achieved_efficiency_pct', 0)
        if efficiency:
            if efficiency >= 85:
                assessment['efficiency_score'] = 40
            elif efficiency >= 80:
                assessment['efficiency_score'] = 35
            elif efficiency >= 75:
                assessment['efficiency_score'] = 30
            elif efficiency >= 70:
                assessment['efficiency_score'] = 25
            elif efficiency >= 60:
                assessment['efficiency_score'] = 15
            else:
                assessment['efficiency_score'] = 5
                assessment['recommendations'].append("Low efficiency - consider alternative pump")

        # BEP proximity scoring (0-30 points)
        distance_from_bep = operating_point.get('distance_from_bep')
        if distance_from_bep is not None:
            if distance_from_bep <= 5:  # Within 5% of BEP
                assessment['bep_proximity_score'] = 30
            elif distance_from_bep <= 10:
                assessment['bep_proximity_score'] = 25
            elif distance_from_bep <= 20:
                assessment['bep_proximity_score'] = 20
            elif distance_from_bep <= 30:
                assessment['bep_proximity_score'] = 15
            else:
                assessment['bep_proximity_score'] = 5
                assessment['recommendations'].append("Operating far from BEP - reduced efficiency and lifespan")

        # Operating range scoring (0-30 points)
        if operating_point.get('within_curve_range', False):
            assessment['range_score'] = 30
        else:
            assessment['range_score'] = 0
            assessment['recommendations'].append("Operating outside recommended curve range")

        # Calculate overall score
        assessment['overall_score'] = (
            assessment['efficiency_score'] + 
            assessment['bep_proximity_score'] + 
            assessment['range_score']
        )

        # Add performance category
        if assessment['overall_score'] >= 90:
            assessment['category'] = 'Excellent'
        elif assessment['overall_score'] >= 80:
            assessment['category'] = 'Very Good'
        elif assessment['overall_score'] >= 70:
            assessment['category'] = 'Good'
        elif assessment['overall_score'] >= 60:
            assessment['category'] = 'Fair'
        else:
            assessment['category'] = 'Poor'

    except Exception as e:
        logger.error(f"Error in quality assessment: {str(e)}")
        assessment['error'] = str(e)

    return assessment

def find_best_curve_for_duty(parsed_pump: ParsedPumpData, target_flow: float, 
                           target_head: float) -> Tuple[int, Optional[Dict[str, Any]]]:
    """
    Find the best curve (impeller size) for a given duty point.

    Args:
        parsed_pump: ParsedPumpData object
        target_flow: Target flow rate in m³/hr
        target_head: Target head in m

    Returns:
        Tuple of (best_curve_index, operating_point_data)
    """
    if not parsed_pump.curves:
        logger.warning(f"No curves available for pump {parsed_pump.pump_code}")
        return -1, {
            'error': 'No curves available',
            'flow_m3hr': target_flow,
            'head_m': target_head,
            'efficiency_pct': 0,
            'power_kw': 0,
            'npshr_m': 0
        }

    best_curve_index = -1
    best_operating_point = None
    best_score = -1

    for i, curve in enumerate(parsed_pump.curves):
        try:
            operating_point = calculate_operating_point(parsed_pump, i, target_flow)

            # Skip if we couldn't calculate a valid operating point
            if not operating_point or not operating_point.get('achieved_head_m'):
                continue

            # Check if this curve can meet the head requirement with tolerance
            achieved_head = operating_point['achieved_head_m']
            head_tolerance = target_head * 0.05  # 5% tolerance
            if achieved_head < (target_head - head_tolerance):
                continue  # Cannot meet head requirement

            # Score this operating point
            quality_score = operating_point.get('quality_assessment', {}).get('overall_score', 0)

            # Bonus for meeting head with minimal excess (prefer efficiency over excess head)
            head_excess_penalty = max(0, (achieved_head - target_head) / target_head * 10)
            final_score = quality_score - head_excess_penalty

            if final_score > best_score:
                best_score = final_score
                best_curve_index = i
                best_operating_point = operating_point

        except Exception as e:
            logger.error(f"Error evaluating curve {i}: {str(e)}")
            continue

    if best_curve_index >= 0:
        logger.debug(f"Best curve for {parsed_pump.pump_code}: index {best_curve_index}, score {best_score}")
        return best_curve_index, best_operating_point
    else:
        logger.warning(f"No suitable curve found for {parsed_pump.pump_code}")
        return -1, {}

def calculate_pump_suitability_score(parsed_pump: ParsedPumpData, target_flow: float, 
                                   target_head: float, requirements: Any = None) -> Dict[str, Any]:
    """
    Calculate an overall suitability score for a pump given specific requirements.

    Args:
        parsed_pump: ParsedPumpData object
        target_flow: Target flow rate in m³/hr
        target_head: Target head in m
        requirements: SiteRequirements object (optional)

    Returns:
        Dictionary containing suitability analysis
    """
    try:
        # Find the best curve for this duty
        best_curve_index, best_operating_point = find_best_curve_for_duty(
            parsed_pump, target_flow, target_head
        )

        if best_curve_index < 0:
            return {
                'pump_code': parsed_pump.pump_code,
                'suitable': False,
                'overall_score': 0,
                'reason': 'Cannot meet head requirement',
                'best_curve_index': -1,
                'operating_point': None
            }

        # Get quality assessment from operating point
        if best_operating_point is None:
            return {
                'pump_code': parsed_pump.pump_code,
                'suitable': False,
                'overall_score': 0,
                'reason': 'Operating point calculation failed',
                'best_curve_index': -1,
                'operating_point': None
            }
            
        quality_assessment = best_operating_point.get('quality_assessment', {})
        base_score = quality_assessment.get('overall_score', 0)

        # Additional scoring factors
        bonus_points = 0
        penalties = 0

        # Type matching bonus (if specified)
        if requirements and hasattr(requirements, 'pump_type') and requirements.pump_type:
            if parsed_pump.filter3.upper() == requirements.pump_type.upper():
                bonus_points += 10

        # Application matching bonus
        if requirements and hasattr(requirements, 'application'):
            app = requirements.application.lower()
            if ('water' in app and 'water' in parsed_pump.filter1.lower()) or \
               ('industrial' in app and 'industrial' in parsed_pump.filter2.lower()):
                bonus_points += 5

        # NPSH check (if available)
        if requirements and hasattr(requirements, 'npsh_available_m') and requirements.npsh_available_m:
            achieved_npshr = best_operating_point.get('achieved_npshr_m', 0)
            if achieved_npshr and achieved_npshr > requirements.npsh_available_m:
                penalties += 20  # Severe penalty for NPSH issues

        # Calculate final score
        final_score = min(100, max(0, base_score + bonus_points - penalties))

        return {
            'pump_code': parsed_pump.pump_code,
            'model': parsed_pump.model,
            'manufacturer': parsed_pump.manufacturer,
            'suitable': final_score > 30,  # Minimum threshold
            'overall_score': final_score,
            'best_curve_index': best_curve_index,
            'operating_point': best_operating_point,
            'quality_assessment': quality_assessment,
            'bonus_points': bonus_points,
            'penalties': penalties,
            'recommendations': quality_assessment.get('recommendations', [])
        }

    except Exception as e:
        logger.error(f"Error calculating suitability score for {parsed_pump.pump_code}: {str(e)}")
        return {
            'pump_code': parsed_pump.pump_code,
            'suitable': False,
            'overall_score': 0,
            'error': str(e),
            'best_curve_index': -1,
            'operating_point': None
        }