"""
Pump Selection Engine
Advanced pump selection algorithms with comprehensive analysis
"""
import logging
import sys
import os
from typing import List, Dict, Any, Tuple

# Import from pump_engine.py as single source of truth
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pump_engine import ParsedPumpData, SiteRequirements
from .performance_calculator import calculate_pump_suitability_score
from .llm_reasoning import llm_reasoning
from .advanced_analysis import advanced_analyzer
from .pump_comparison import pump_comparator
from .system_curve_analysis import system_curve_analyzer

logger = logging.getLogger(__name__)

def find_best_pumps(all_parsed_pumps: List[ParsedPumpData], 
                   site_requirements: SiteRequirements) -> List[Dict[str, Any]]:
    """
    Find the top 3 best pump selections based on site requirements.

    This function evaluates all pumps against the site requirements and returns
    the top 3 selections with detailed scoring and reasoning.

    Args:
        all_parsed_pumps: List of ParsedPumpData objects
        site_requirements: SiteRequirements object with duty point and constraints

    Returns:
        List of top 3 pump selections with detailed analysis
    """
    logger.info(f"Evaluating {len(all_parsed_pumps)} pumps for requirements: {site_requirements}")

    pump_evaluations = []

    # Evaluate each pump
    for parsed_pump in all_parsed_pumps:
        try:
            evaluation = evaluate_pump_for_requirements(parsed_pump, site_requirements)
            if evaluation['suitable']:
                pump_evaluations.append(evaluation)

        except Exception as e:
            logger.error(f"Error evaluating pump {parsed_pump.pump_code}: {str(e)}")
            continue

    # Sort by overall score (descending)
    pump_evaluations.sort(key=lambda x: x['overall_score'], reverse=True)

    # Return top 3
    top_3 = pump_evaluations[:3]

    logger.info(f"Found {len(pump_evaluations)} suitable pumps, returning top {len(top_3)}")

    # Add ranking information and LLM-enhanced reasoning
    for i, evaluation in enumerate(top_3):
        evaluation['rank'] = i + 1

        # Generate selection reasoning - only LLM for top choice to prevent timeout
        try:
            parsed_pump = next((p for p in all_parsed_pumps if p.pump_code == evaluation['pump_code']), None)

            if not parsed_pump:
                logger.error(f"Cannot find parsed pump for code: {evaluation['pump_code']}")
                evaluation['selection_reason'] = f"Rank {i + 1} selection"
                continue

            if i == 0:  # Only use LLM for top recommendation
                # Only generate LLM reasoning if we have a valid operating point
                operating_point = evaluation.get('operating_point', {})
                if (operating_point and 
                    isinstance(operating_point, dict) and 
                    operating_point.get('achieved_head_m') is not None and
                    not operating_point.get('error')):
                    try:
                        evaluation['selection_reason'] = llm_reasoning.generate_selection_reasoning(
                            evaluation, parsed_pump, site_requirements, i + 1
                        )
                    except Exception as e:
                        logger.error(f"Error generating LLM reasoning: {str(e)}")
                        evaluation['selection_reason'] = _generate_selection_reason(evaluation, i + 1)
                    # Generate detailed technical analysis for top choice only
                    technical_analysis = llm_reasoning.generate_technical_analysis(evaluation, parsed_pump)
                    evaluation.update(technical_analysis)
                else:
                    evaluation['selection_reason'] = _generate_selection_reason(evaluation, i + 1)

                # Add advanced analysis for top choice
                try:
                    lifecycle_analysis = advanced_analyzer.calculate_lifecycle_cost(
                        parsed_pump, evaluation['operating_point'], site_requirements
                    )
                    evaluation['lifecycle_cost'] = {
                        'initial_cost': lifecycle_analysis.initial_cost,
                        'annual_energy_cost': lifecycle_analysis.annual_energy_cost,
                        'maintenance_cost': lifecycle_analysis.maintenance_cost,
                        'total_10_year_cost': lifecycle_analysis.total_10_year_cost,
                        'cost_per_m3': lifecycle_analysis.cost_per_m3
                    }

                    environmental_impact = advanced_analyzer.calculate_environmental_impact(
                        evaluation['operating_point']
                    )
                    evaluation['environmental_impact'] = {
                        'annual_co2_kg': environmental_impact.annual_co2_kg,
                        'annual_kwh': environmental_impact.annual_kwh,
                        'efficiency_rating': environmental_impact.efficiency_rating,
                        'carbon_footprint_score': environmental_impact.carbon_footprint_score
                    }

                    vfd_analysis = advanced_analyzer.analyze_variable_speed_potential(
                        parsed_pump, site_requirements
                    )
                    evaluation['vfd_analysis'] = vfd_analysis

                except Exception as e:
                    logger.error(f"Error in advanced analysis for {parsed_pump.pump_code}: {str(e)}")
            else:
                # Use fast template-based reasoning for alternatives
                evaluation['selection_reason'] = _generate_selection_reason(evaluation, i + 1)

        except Exception as e:
            logger.error(f"Error generating reasoning for {evaluation['pump_code']}: {e}")
            evaluation['selection_reason'] = _generate_selection_reason(evaluation, i + 1)

    # Add comprehensive comparison analysis for all pumps
    try:
        comparison_analysis = pump_comparator.generate_detailed_comparison(
            top_3, [next(p for p in all_parsed_pumps if p.pump_code == eval['pump_code']) for eval in top_3]
        )

        # Add system curve analysis
        system_analysis = system_curve_analyzer.analyze_system_curve(site_requirements)

        # Add to results context
        for i, evaluation in enumerate(top_3):
            evaluation['comparison_rank'] = i + 1
            if i == 0:  # Add detailed analysis to top choice
                evaluation['system_curve_analysis'] = system_analysis
                evaluation['comparison_analysis'] = comparison_analysis

    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")

    return top_3

def evaluate_pump_for_requirements(parsed_pump: ParsedPumpData, 
                                 site_requirements: SiteRequirements) -> Dict[str, Any]:
    """
    Evaluate a single pump against site requirements.

    Args:
        parsed_pump: ParsedPumpData object to evaluate
        site_requirements: SiteRequirements object

    Returns:
        Dictionary containing detailed evaluation results
    """
    try:
        # Import from pump_engine for consistent data structure
        from pump_engine import find_best_curve_for_duty, calculate_operating_point
        
        # Find best curve for the duty point
        best_curve_index, operating_point = find_best_curve_for_duty(
            parsed_pump, site_requirements.flow_m3hr, site_requirements.head_m
        )
        
        if not operating_point or operating_point.get('error'):
            return {
                'pump_code': parsed_pump.pump_code,
                'suitable': False,
                'overall_score': 0,
                'error': 'No suitable operating point found'
            }

        # Get basic suitability score with error handling
        try:
            suitability = calculate_pump_suitability_score(
                parsed_pump, 
                site_requirements.flow_m3hr, 
                site_requirements.head_m,
                site_requirements
            )
            overall_score = suitability.get('overall_score', 75) if isinstance(suitability, dict) else 75
        except Exception as score_error:
            logger.warning(f"Suitability scoring failed for {parsed_pump.pump_code}: {score_error}")
            overall_score = 75

        # Return complete evaluation structure
        return {
            'pump_code': parsed_pump.pump_code,
            'suitable': True,
            'overall_score': overall_score,
            'score': overall_score,  # Alias for compatibility
            'operating_point': operating_point,
            'pump_info': parsed_pump.pump_info,
            'selected_curve': {
                'impeller_size': operating_point.get('impeller_size', 'N/A'),
                'is_selected': True,
                'curve_index': best_curve_index
            },
            'selection_reason': f"Selected for {overall_score:.1f}% suitability score"
        }

    except Exception as e:
        logger.error(f"Error in pump evaluation: {str(e)}")
        return {
            'pump_code': parsed_pump.pump_code,
            'suitable': False,
            'overall_score': 0,
            'error': str(e)
        }

def enhance_pump_evaluation(base_evaluation: Dict[str, Any], 
                          parsed_pump: ParsedPumpData,
                          site_requirements: SiteRequirements) -> Dict[str, Any]:
    """
    Enhance the basic pump evaluation with additional selection criteria.

    Args:
        base_evaluation: Basic suitability evaluation
        parsed_pump: ParsedPumpData object
        site_requirements: SiteRequirements object

    Returns:
        Enhanced evaluation dictionary
    """
    evaluation = base_evaluation.copy()

    try:
        operating_point = evaluation.get('operating_point', {})

        # Only perform detailed analysis if operating point is valid and not None
        if (operating_point and 
            operating_point.get('achieved_head_m') is not None and 
            not operating_point.get('error')):
            # BEP Analysis Enhancement
            bep_analysis = _analyze_bep_operation(parsed_pump, operating_point, site_requirements)
            evaluation['bep_analysis'] = bep_analysis

            # NPSH Analysis
            npsh_analysis = _analyze_npsh_requirements(operating_point, site_requirements)
            evaluation['npsh_analysis'] = npsh_analysis

            # Power Analysis
            power_analysis = _analyze_power_consumption(operating_point, site_requirements)
            evaluation['power_analysis'] = power_analysis
        else:
            # Set default values for failed operating point calculations
            evaluation['bep_analysis'] = {'bep_score': 0, 'recommendations': ['Operating point calculation failed']}
            evaluation['npsh_analysis'] = {'npsh_adequate': False, 'recommendations': ['Unable to calculate NPSH']}
            evaluation['power_analysis'] = {'power_efficiency_score': 0, 'recommendations': ['Power calculation unavailable']}

        # Filter Matching Analysis (independent of operating point)
        filter_match = _analyze_filter_matching(parsed_pump, site_requirements)
        evaluation['filter_matching'] = filter_match

        # Recalculate overall score with enhancements
        evaluation['overall_score'] = _calculate_enhanced_score(evaluation)

        # Generate detailed reasoning
        evaluation['detailed_reasoning'] = _generate_detailed_reasoning(evaluation, parsed_pump)

        logger.debug(f"Enhanced evaluation for {parsed_pump.pump_code}: score {evaluation['overall_score']}")

    except Exception as e:
        logger.error(f"Error enhancing pump evaluation: {str(e)}")
        evaluation['enhancement_error'] = str(e)

    return evaluation

def _analyze_bep_operation(parsed_pump: ParsedPumpData, operating_point: Dict[str, Any],
                          site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Analyze how close the operating point is to the pump's BEP."""
    analysis = {
        'distance_from_bep_pct': None,
        'on_favorable_side': None,
        'efficiency_at_duty': None,
        'bep_score': 0,
        'recommendations': []
    }

    try:
        target_flow = site_requirements.flow_m3hr
        bep_flow = parsed_pump.bep_flow_std
        achieved_efficiency = operating_point.get('achieved_efficiency_pct')

        if bep_flow and bep_flow > 0:
            distance_pct = abs(target_flow - bep_flow) / bep_flow * 100
            analysis['distance_from_bep_pct'] = round(distance_pct, 1)

            # Check if operating on the favorable (right) side of BEP
            if target_flow > bep_flow:
                analysis['on_favorable_side'] = True
                analysis['bep_score'] += 5  # Slight bonus for right side operation
            else:
                analysis['on_favorable_side'] = False

            # BEP proximity scoring
            if distance_pct <= 5:
                analysis['bep_score'] += 30
            elif distance_pct <= 10:
                analysis['bep_score'] += 25
            elif distance_pct <= 15:
                analysis['bep_score'] += 20
            elif distance_pct <= 25:
                analysis['bep_score'] += 10
            else:
                analysis['recommendations'].append(
                    f"Operating {distance_pct:.1f}% from BEP may reduce efficiency and pump life"
                )

        if achieved_efficiency:
            analysis['efficiency_at_duty'] = achieved_efficiency
            if achieved_efficiency >= 85:
                analysis['bep_score'] += 15
            elif achieved_efficiency >= 80:
                analysis['bep_score'] += 10
            elif achieved_efficiency >= 75:
                analysis['bep_score'] += 5

    except Exception as e:
        logger.error(f"Error in BEP analysis: {str(e)}")
        analysis['error'] = str(e)

    return analysis

def _analyze_filter_matching(parsed_pump: ParsedPumpData, 
                           site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Analyze how well the pump matches the application filters."""
    analysis = {
        'type_match': False,
        'application_match': False,
        'liquid_match': False,
        'filter_score': 0,
        'matching_filters': []
    }

    try:
        # Pump type matching
        if hasattr(site_requirements, 'pump_type') and site_requirements.pump_type:
            req_type = site_requirements.pump_type.upper()
            if req_type in parsed_pump.filter3.upper():
                analysis['type_match'] = True
                analysis['filter_score'] += 20
                analysis['matching_filters'].append(f"Pump type: {parsed_pump.filter3}")

        # Application matching
        if hasattr(site_requirements, 'application') and site_requirements.application:
            req_app = site_requirements.application.lower()
            pump_app = parsed_pump.filter2.lower()
            if req_app in pump_app or pump_app in req_app:
                analysis['application_match'] = True
                analysis['filter_score'] += 10
                analysis['matching_filters'].append(f"Application: {parsed_pump.filter2}")

        # Liquid type matching
        if hasattr(site_requirements, 'liquid_type') and site_requirements.liquid_type:
            req_liquid = site_requirements.liquid_type.lower()
            pump_liquid = parsed_pump.filter1.lower()
            if req_liquid in pump_liquid or pump_liquid in req_liquid:
                analysis['liquid_match'] = True
                analysis['filter_score'] += 10
                analysis['matching_filters'].append(f"Liquid: {parsed_pump.filter1}")

    except Exception as e:
        logger.error(f"Error in filter analysis: {str(e)}")
        analysis['error'] = str(e)

    return analysis

def _analyze_npsh_requirements(operating_point: Dict[str, Any], 
                             site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Analyze NPSH requirements and available NPSH."""
    analysis = {
        'npshr_at_duty': None,
        'npsha_available': None,
        'npsh_margin': None,
        'npsh_adequate': None,
        'npsh_score': 0,
        'recommendations': []
    }

    try:
        npshr = operating_point.get('achieved_npshr_m')
        npsha = getattr(site_requirements, 'npsh_available_m', None)

        if npshr is not None:
            analysis['npshr_at_duty'] = round(npshr, 2)

            if npsha is not None:
                analysis['npsha_available'] = npsha
                margin = npsha - npshr
                analysis['npsh_margin'] = round(margin, 2)

                if margin >= 2.0:  # Good margin
                    analysis['npsh_adequate'] = True
                    analysis['npsh_score'] = 20
                elif margin >= 1.0:  # Minimum margin
                    analysis['npsh_adequate'] = True
                    analysis['npsh_score'] = 15
                    analysis['recommendations'].append("NPSH margin is minimal - verify system calculations")
                elif margin >= 0:  # Marginal
                    analysis['npsh_adequate'] = True
                    analysis['npsh_score'] = 5
                    analysis['recommendations'].append("NPSH margin is very tight - may cause cavitation")
                else:  # Inadequate
                    analysis['npsh_adequate'] = False
                    analysis['npsh_score'] = -50  # Heavy penalty
                    analysis['recommendations'].append("Insufficient NPSH available - cavitation will occur")
            else:
                analysis['recommendations'].append("System NPSH available not specified - must be verified")

    except Exception as e:
        logger.error(f"Error in NPSH analysis: {str(e)}")
        analysis['error'] = str(e)

    return analysis

def _analyze_power_consumption(operating_point: Dict[str, Any], 
                             site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Analyze power consumption and efficiency."""
    analysis = {
        'power_at_duty_kw': None,
        'within_power_limit': None,
        'power_score': 0,
        'efficiency_rating': None,
        'recommendations': []
    }

    try:
        power_kw = operating_point.get('achieved_power_kw')
        max_power = getattr(site_requirements, 'max_power', None)
        efficiency = operating_point.get('achieved_efficiency_pct')

        if power_kw is not None:
            analysis['power_at_duty_kw'] = round(power_kw, 2)

            if max_power is not None:
                if power_kw <= max_power:
                    analysis['within_power_limit'] = True
                    analysis['power_score'] += 10
                else:
                    analysis['within_power_limit'] = False
                    analysis['power_score'] -= 20
                    analysis['recommendations'].append(f"Power consumption ({power_kw:.1f} kW) exceeds limit ({max_power} kW)")

        if efficiency is not None:
            if efficiency >= 85:
                analysis['efficiency_rating'] = 'Excellent'
                analysis['power_score'] += 15
            elif efficiency >= 80:
                analysis['efficiency_rating'] = 'Very Good'
                analysis['power_score'] += 12
            elif efficiency >= 75:
                analysis['efficiency_rating'] = 'Good'
                analysis['power_score'] += 8
            elif efficiency >= 70:
                analysis['efficiency_rating'] = 'Fair'
                analysis['power_score'] += 4
            else:
                analysis['efficiency_rating'] = 'Poor'
                analysis['recommendations'].append("Low efficiency - consider more efficient alternatives")

    except Exception as e:
        logger.error(f"Error in power analysis: {str(e)}")
        analysis['error'] = str(e)

    return analysis

def _calculate_enhanced_score(evaluation: Dict[str, Any]) -> float:
    """Calculate enhanced overall score from all analysis components."""
    try:
        base_score = evaluation.get('overall_score', 0)

        # Add component scores
        bep_score = evaluation.get('bep_analysis', {}).get('bep_score', 0)
        filter_score = evaluation.get('filter_matching', {}).get('filter_score', 0)
        npsh_score = evaluation.get('npsh_analysis', {}).get('npsh_score', 0)
        power_score = evaluation.get('power_analysis', {}).get('power_score', 0)

        enhanced_score = base_score + bep_score + filter_score + npsh_score + power_score

        # Ensure score is within bounds
        return min(100, max(0, enhanced_score))

    except Exception as e:
        logger.error(f"Error calculating enhanced score: {str(e)}")
        return evaluation.get('overall_score', 0)

def _generate_detailed_reasoning(evaluation: Dict[str, Any], 
                               parsed_pump: ParsedPumpData) -> List[str]:
    """Generate detailed reasoning for pump selection."""
    reasoning = []

    try:
        operating_point = evaluation.get('operating_point', {})

        # Basic performance
        if operating_point.get('achieved_efficiency_pct'):
            eff = operating_point['achieved_efficiency_pct']
            reasoning.append(f"Operates at {eff:.1f}% efficiency at the duty point")

        # BEP analysis
        bep_analysis = evaluation.get('bep_analysis', {})
        if bep_analysis and isinstance(bep_analysis, dict) and bep_analysis.get('distance_from_bep_pct') is not None:
            distance = bep_analysis['distance_from_bep_pct']
            if distance <= 10:
                reasoning.append(f"Operates close to BEP ({distance:.1f}% away), ensuring optimal efficiency and longevity")
            else:
                reasoning.append(f"Operates {distance:.1f}% from BEP - acceptable but not optimal")

        # Filter matching
        filter_match = evaluation.get('filter_matching', {})
        if filter_match and isinstance(filter_match, dict) and filter_match.get('matching_filters'):
            reasoning.append(f"Well-suited for application: {', '.join(filter_match['matching_filters'])}")

        # NPSH
        npsh_analysis = evaluation.get('npsh_analysis', {})
        if npsh_analysis and isinstance(npsh_analysis, dict) and npsh_analysis.get('npsh_adequate') is True:
            margin = npsh_analysis.get('npsh_margin', 0)
            reasoning.append(f"NPSH requirement met with {margin:.1f}m margin")
        elif npsh_analysis and isinstance(npsh_analysis, dict) and npsh_analysis.get('npsh_adequate') is False:
            reasoning.append("CAUTION: NPSH requirement not met - system modifications required")

        # Power
        power_analysis = evaluation.get('power_analysis', {})
        if power_analysis and isinstance(power_analysis, dict) and power_analysis.get('power_at_duty_kw'):
            power = power_analysis['power_at_duty_kw']
            rating = power_analysis.get('efficiency_rating', 'Good')
            reasoning.append(f"Power consumption: {power:.1f} kW ({rating.lower()} efficiency)")

        # Quality category
        quality = evaluation.get('quality_assessment', {})
        if quality and isinstance(quality, dict) and quality.get('category'):
            reasoning.append(f"Overall performance rating: {quality['category']}")

    except Exception as e:
        logger.error(f"Error generating reasoning: {str(e)}")
        reasoning.append("Analysis completed with some limitations")

    return reasoning

def _generate_selection_reason(evaluation: Dict[str, Any], rank: int) -> str:
    """Generate a concise selection reason for the pump ranking."""
    try:
        if rank == 1:
            reason = "Top recommendation - "
        elif rank == 2:
            reason = "Strong alternative - "
        else:
            reason = "Good option - "

        # Add key differentiator
        bep_analysis = evaluation.get('bep_analysis', {})
        power_analysis = evaluation.get('power_analysis', {})

        if bep_analysis.get('distance_from_bep_pct', 100) <= 10:
            reason += "operates near BEP for optimal efficiency"
        elif power_analysis.get('efficiency_rating') == 'Excellent':
            reason += "excellent efficiency performance"
        elif evaluation.get('filter_matching', {}).get('filter_score', 0) >= 20:
            reason += "perfect application match"
        else:
            reason += "meets all requirements reliably"

        return reason

    except Exception as e:
        logger.error(f"Error generating selection reason: {str(e)}")
        return f"Rank {rank} selection"

def generate_reasoning_text(evaluation):
    """Generate human-readable reasoning for pump selection."""
    reasoning = []

    try:
        # Validate evaluation input
        if not evaluation or not isinstance(evaluation, dict):
            logger.warning("Invalid evaluation data for reasoning generation")
            return ["Pump analysis completed - detailed reasoning unavailable"]

        # Operating point
        op = evaluation.get('operating_point', {})
        if op and isinstance(op, dict):
            flow = op.get('flow_m3hr', 0)
            head = op.get('head_m', 0)
            efficiency = op.get('efficiency_pct', 0)

            if flow > 0 and head > 0:
                reasoning.append(f"Operating at {flow:.0f} m³/hr and {head:.1f}m head with {efficiency:.1f}% efficiency")

            # Check for calculation errors
            if op.get('error'):
                reasoning.append(f"Note: {op['error']}")

        # BEP analysis
        bep_analysis = evaluation.get('bep_analysis', {})
        if bep_analysis and isinstance(bep_analysis, dict):
            distance = bep_analysis.get('distance_from_bep_pct', 0)
            if distance and distance > 0:
                if distance < 15:
                    reasoning.append("Operating near Best Efficiency Point (BEP) for optimal performance")
                elif distance < 30:
                    reasoning.append("Operating within acceptable range of BEP")
                else:
                    reasoning.append("Operating away from BEP - consider alternative pump size")

        # NPSH
        npsh_analysis = evaluation.get('npsh_analysis', {})
        if npsh_analysis and isinstance(npsh_analysis, dict):
            if npsh_analysis.get('npsh_adequate') is True:
                margin = npsh_analysis.get('npsh_margin', 0)
                reasoning.append(f"NPSH requirement met with {margin:.1f}m margin")
            elif npsh_analysis.get('npsh_adequate') is False:
                reasoning.append("CAUTION: NPSH requirement not met - system modifications required")

        # Power
        power_analysis = evaluation.get('power_analysis', {})
        if power_analysis and isinstance(power_analysis, dict):
            power = power_analysis.get('power_at_duty_kw', 0)
            if power and power > 0:
                rating = power_analysis.get('efficiency_rating', 'Good')
                reasoning.append(f"Power consumption: {power:.1f} kW ({rating.lower()} efficiency)")

        # Quality category
        quality = evaluation.get('quality_assessment', {})
        if quality and isinstance(quality, dict):
            category = quality.get('category')
            if category:
                reasoning.append(f"Overall performance rating: {category}")

        # If no reasoning was generated, provide fallback
        if not reasoning:
            pump_code = evaluation.get('pump_code', 'Unknown')
            reasoning.append(f"Pump {pump_code} evaluated for specified requirements")

    except Exception as e:
        logger.error(f"Error generating reasoning: {str(e)}", exc_info=True)
        reasoning.append("Analysis completed with some limitations")

    return reasoning

def evaluate_pump_for_requirements(parsed_pump: ParsedPumpData, 
                                 site_requirements: SiteRequirements) -> Dict[str, Any]:
    """
    Evaluate a single pump against site requirements.

    Args:
        parsed_pump: ParsedPumpData object to evaluate
        site_requirements: SiteRequirements object
    Returns:
        Dict containing detailed evaluation of pump suitability
    """
    try:
        # Import required functions from pump_engine
        from pump_engine import find_best_curve_for_duty, calculate_pump_suitability_score
        
        # Find best curve for the given requirements
        best_curve_index, operating_point = find_best_curve_for_duty(
            parsed_pump, site_requirements.flow_m3hr, site_requirements.head_m
        )
        
        if operating_point is None:
            return {
                "pump_code": parsed_pump.pump_code,
                "suitable": False,
                "reason": "No suitable operating point found",
                "score": 0,
                "efficiency": 0,
                "power": 0,
                "npsh_required": 0,
                "curve_index": -1
            }
        
        # Calculate suitability score
        try:
            from pump_engine import calculate_pump_suitability_score as engine_calc_score
            suitability = engine_calc_score(
                parsed_pump, site_requirements.flow_m3hr, site_requirements.head_m, site_requirements
            )
        except Exception as calc_error:
            logger.error(f"Error calculating suitability score: {calc_error}")
            suitability = {'overall_score': 50, 'error': str(calc_error)}
        
        # Ensure suitability has the required structure
        if not isinstance(suitability, dict) or 'overall_score' not in suitability:
            suitability = {'overall_score': 50, 'error': 'Invalid suitability calculation'}
        
        return {
            "pump_code": parsed_pump.pump_code,
            "suitable": True,
            "score": suitability.get("overall_score", 50),
            "efficiency": operating_point.get("efficiency", 0),
            "power": operating_point.get("power", 0),
            "npsh_required": operating_point.get("npsh_required", 0),
            "curve_index": best_curve_index,
            "operating_point": operating_point,
            "suitability_analysis": suitability,
            "pump_info": parsed_pump.pump_info,
            "selected_curve": parsed_pump.curves[best_curve_index] if best_curve_index >= 0 else None
        }
        
    except Exception as e:
        logger.error(f"Error evaluating pump {parsed_pump.pump_code}: {e}")
        return {
            "pump_code": parsed_pump.pump_code,
            "suitable": False,
            "reason": f"Evaluation error: {str(e)}",
            "score": 0,
            "efficiency": 0,
            "power": 0,
            "npsh_required": 0,
            "curve_index": -1
        }
