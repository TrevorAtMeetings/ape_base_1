import logging
from typing import Dict, Any, List
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pump_engine import SiteRequirements, ParsedPumpData

logger = logging.getLogger(__name__)

def generate_report_context(selected_pump_evaluation: Dict[str, Any],
                          parsed_pump: ParsedPumpData,
                          site_requirements: SiteRequirements,
                          alternatives: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate comprehensive report context for PDF generation.
    
    This function assembles all data and reasoning needed for a professional
    customer-facing pump selection report.
    
    Args:
        selected_pump_evaluation: Detailed evaluation of the selected pump
        parsed_pump: ParsedPumpData object for the selected pump
        site_requirements: Original site requirements
        alternatives: List of alternative pump evaluations (optional)
        
    Returns:
        Dictionary containing all report context data
    """
    logger.info(f"Generating report context for pump: {parsed_pump.pump_code}")
    
    try:
        # Basic report metadata
        report_context = {
            'generated_date': datetime.now().strftime('%B %d, %Y'),
            'generated_time': datetime.now().strftime('%I:%M %p'),
            'report_title': 'Pump Selection Analysis Report',
            'company_name': 'APE Pumps',
            'prepared_for': _format_customer_info(site_requirements),
        }
        
        # Executive Summary
        report_context['executive_summary'] = _generate_executive_summary(
            selected_pump_evaluation, parsed_pump, site_requirements
        )
        
        # Site Requirements Summary
        report_context['site_requirements'] = _format_site_requirements(site_requirements)
        
        # Selected Pump Details
        report_context['selected_pump'] = _format_selected_pump_details(
            selected_pump_evaluation, parsed_pump
        )
        
        # Performance Analysis
        report_context['performance_analysis'] = _generate_performance_analysis(
            selected_pump_evaluation, parsed_pump, site_requirements
        )
        
        # Technical Reasoning
        report_context['technical_reasoning'] = _generate_technical_reasoning(
            selected_pump_evaluation, parsed_pump
        )
        
        # Alternative Options (if provided)
        if alternatives:
            report_context['alternatives'] = _format_alternatives(alternatives)
        
        # Recommendations and Next Steps
        report_context['recommendations'] = _generate_recommendations(
            selected_pump_evaluation, site_requirements
        )
        
        # Technical Specifications Table
        report_context['specifications'] = _generate_specifications_table(
            selected_pump_evaluation, parsed_pump
        )
        
        logger.debug("Report context generated successfully")
        return report_context
        
    except Exception as e:
        logger.error(f"Error generating report context: {str(e)}")
        # Return minimal context on error
        return {
            'generated_date': datetime.now().strftime('%B %d, %Y'),
            'report_title': 'Pump Selection Analysis Report',
            'error': f"Error generating report: {str(e)}",
            'selected_pump': {'pump_code': parsed_pump.pump_code if parsed_pump else 'Unknown'}
        }

def _format_customer_info(site_requirements: SiteRequirements) -> Dict[str, str]:
    """Format customer and project information."""
    return {
        'contact_name': getattr(site_requirements, 'contact_name', 'Valued Customer'),
        'company': getattr(site_requirements, 'company', ''),
        'email': getattr(site_requirements, 'email', ''),
        'project_name': getattr(site_requirements, 'project_name', 'Pump Selection Project'),
        'project_location': getattr(site_requirements, 'project_location', '')
    }

def _generate_executive_summary(evaluation: Dict[str, Any], 
                              parsed_pump: ParsedPumpData,
                              site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Generate executive summary for the report."""
    summary = {
        'recommendation': f"{parsed_pump.manufacturer} {parsed_pump.model}",
        'key_benefits': [],
        'performance_highlights': {},
        'confidence_level': 'High'
    }
    
    try:
        operating_point = evaluation.get('operating_point', {})
        
        # Performance highlights
        if operating_point.get('achieved_efficiency_pct'):
            summary['performance_highlights']['efficiency'] = f"{operating_point['achieved_efficiency_pct']:.1f}%"
        
        if operating_point.get('achieved_power_kw'):
            summary['performance_highlights']['power'] = f"{operating_point['achieved_power_kw']:.1f} kW"
        
        if operating_point.get('achieved_head_m'):
            summary['performance_highlights']['head'] = f"{operating_point['achieved_head_m']:.1f} m"
        
        # Key benefits
        bep_analysis = evaluation.get('bep_analysis', {})
        if bep_analysis.get('distance_from_bep_pct', 100) <= 15:
            summary['key_benefits'].append("Operates near Best Efficiency Point for optimal performance")
        
        power_analysis = evaluation.get('power_analysis', {})
        if power_analysis.get('efficiency_rating') in ['Excellent', 'Very Good']:
            summary['key_benefits'].append("High efficiency reduces operating costs")
        
        filter_match = evaluation.get('filter_matching', {})
        if filter_match.get('filter_score', 0) >= 20:
            summary['key_benefits'].append("Perfect match for specified application requirements")
        
        npsh_analysis = evaluation.get('npsh_analysis', {})
        if npsh_analysis.get('npsh_adequate') is True:
            summary['key_benefits'].append("NPSH requirements fully satisfied")
        
        # Confidence level based on overall score
        overall_score = evaluation.get('overall_score', 0)
        if overall_score >= 90:
            summary['confidence_level'] = 'Very High'
        elif overall_score >= 80:
            summary['confidence_level'] = 'High'
        elif overall_score >= 70:
            summary['confidence_level'] = 'Good'
        else:
            summary['confidence_level'] = 'Moderate'
        
    except Exception as e:
        logger.error(f"Error in executive summary: {str(e)}")
        summary['error'] = str(e)
    
    return summary

def _format_site_requirements(site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Format site requirements for report display."""
    return {
        'flow_rate': f"{site_requirements.flow_m3hr} m³/hr",
        'total_head': f"{site_requirements.head_m} m",
        'liquid_type': getattr(site_requirements, 'liquid_type', 'Water'),
        'application': getattr(site_requirements, 'application', 'General'),
        'pump_type': getattr(site_requirements, 'pump_type', 'Not specified'),
        'temperature': f"{getattr(site_requirements, 'temperature', 20)}°C",
        'specific_gravity': getattr(site_requirements, 'specific_gravity', 1.0),
        'npsh_available': f"{getattr(site_requirements, 'npsh_available_m', 'Not specified')} m" if getattr(site_requirements, 'npsh_available_m', None) else 'Not specified',
        'max_power': f"{getattr(site_requirements, 'max_power', 'Not specified')} kW" if getattr(site_requirements, 'max_power', None) else 'Not specified'
    }

def _format_selected_pump_details(evaluation: Dict[str, Any], 
                                parsed_pump: ParsedPumpData) -> Dict[str, Any]:
    """Format selected pump details for report."""
    operating_point = evaluation.get('operating_point', {})
    
    return {
        'manufacturer': parsed_pump.manufacturer,
        'model': parsed_pump.model,
        'series': parsed_pump.series,
        'pump_code': parsed_pump.pump_code,
        'description': parsed_pump.description,
        'impeller_size': operating_point.get('impeller_size', 'Standard'),
        'nominal_speed': f"{parsed_pump.nominal_speed} RPM",
        'construction_type': parsed_pump.filter5 or 'Standard',
        'orientation': parsed_pump.filter4 or 'Horizontal',
        'overall_score': evaluation.get('overall_score', 0),
        'quality_rating': evaluation.get('quality_assessment', {}).get('category', 'Good')
    }

def _generate_performance_analysis(evaluation: Dict[str, Any],
                                 parsed_pump: ParsedPumpData,
                                 site_requirements: SiteRequirements) -> Dict[str, Any]:
    """Generate detailed performance analysis."""
    operating_point = evaluation.get('operating_point', {})
    
    analysis = {
        'duty_point': {
            'required_flow': f"{site_requirements.flow_m3hr} m³/hr",
            'required_head': f"{site_requirements.head_m} m",
            'achieved_flow': f"{site_requirements.flow_m3hr} m³/hr",
            'achieved_head': f"{operating_point.get('achieved_head_m', 0):.1f} m",
            'achieved_efficiency': f"{operating_point.get('achieved_efficiency_pct', 0):.1f}%",
            'power_consumption': f"{operating_point.get('achieved_power_kw', 0):.1f} kW",
            'npshr_required': f"{operating_point.get('achieved_npshr_m', 0):.2f} m"
        },
        'bep_comparison': {},
        'efficiency_analysis': {},
        'npsh_analysis': {}
    }
    
    # BEP comparison
    bep_analysis = evaluation.get('bep_analysis', {})
    if bep_analysis.get('distance_from_bep_pct') is not None:
        analysis['bep_comparison'] = {
            'bep_flow': f"{parsed_pump.bep_flow_std} m³/hr",
            'bep_head': f"{parsed_pump.bep_head_std} m",
            'bep_efficiency': f"{parsed_pump.bep_eff_std}%",
            'distance_from_bep': f"{bep_analysis['distance_from_bep_pct']:.1f}%",
            'favorable_side': bep_analysis.get('on_favorable_side', False)
        }
    
    # Efficiency analysis
    power_analysis = evaluation.get('power_analysis', {})
    analysis['efficiency_analysis'] = {
        'efficiency_rating': power_analysis.get('efficiency_rating', 'Good'),
        'annual_energy_estimate': _calculate_annual_energy_estimate(operating_point),
        'efficiency_benefits': _generate_efficiency_benefits(power_analysis)
    }
    
    # NPSH analysis
    npsh_data = evaluation.get('npsh_analysis', {})
    analysis['npsh_analysis'] = {
        'npshr_at_duty': f"{npsh_data.get('npshr_at_duty', 0):.2f} m",
        'npsha_required': f">{npsh_data.get('npshr_at_duty', 0):.2f} m",
        'margin_status': 'Adequate' if npsh_data.get('npsh_adequate') else 'Requires verification',
        'cavitation_risk': 'Low' if npsh_data.get('npsh_adequate') else 'Medium'
    }
    
    return analysis

def _generate_technical_reasoning(evaluation: Dict[str, Any], 
                                parsed_pump: ParsedPumpData) -> List[Dict[str, str]]:
    """Generate technical reasoning sections."""
    reasoning_sections = []
    
    # Selection rationale
    detailed_reasoning = evaluation.get('detailed_reasoning', [])
    if detailed_reasoning:
        reasoning_sections.append({
            'title': 'Selection Rationale',
            'content': '. '.join(detailed_reasoning) + '.'
        })
    
    # BEP benefits
    bep_analysis = evaluation.get('bep_analysis', {})
    if bep_analysis.get('distance_from_bep_pct', 100) <= 20:
        reasoning_sections.append({
            'title': 'Best Efficiency Point Operation',
            'content': f"Operating within {bep_analysis.get('distance_from_bep_pct', 0):.1f}% of the pump's BEP ensures optimal hydraulic efficiency, reduced wear, lower vibration, and extended service life. This translates to lower operating costs and improved reliability."
        })
    
    # Application suitability
    filter_match = evaluation.get('filter_matching', {})
    if filter_match.get('matching_filters'):
        reasoning_sections.append({
            'title': 'Application Suitability',
            'content': f"This pump is specifically designed for {', '.join(filter_match['matching_filters']).lower()}, ensuring optimal performance and longevity in your application."
        })
    
    # NPSH considerations
    npsh_analysis = evaluation.get('npsh_analysis', {})
    if npsh_analysis.get('npshr_at_duty'):
        content = f"The pump requires {npsh_analysis['npshr_at_duty']:.2f}m NPSH at the duty point. "
        if npsh_analysis.get('npsh_adequate') is True:
            content += "The system NPSH available meets this requirement with adequate margin."
        else:
            content += "Please verify that system NPSH available exceeds this value to prevent cavitation."
        
        reasoning_sections.append({
            'title': 'NPSH Requirements',
            'content': content
        })
    
    return reasoning_sections

def _format_alternatives(alternatives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format alternative pump options."""
    formatted_alternatives = []
    
    for alt in alternatives[:2]:  # Limit to 2 alternatives
        try:
            operating_point = alt.get('operating_point', {})
            
            formatted_alternatives.append({
                'model': alt.get('model', 'Unknown'),
                'manufacturer': alt.get('manufacturer', 'Unknown'),
                'efficiency': f"{operating_point.get('achieved_efficiency_pct', 0):.1f}%",
                'power': f"{operating_point.get('achieved_power_kw', 0):.1f} kW",
                'score': alt.get('overall_score', 0),
                'key_difference': _identify_key_difference(alt)
            })
        except Exception as e:
            logger.error(f"Error formatting alternative: {str(e)}")
            continue
    
    return formatted_alternatives

def _generate_recommendations(evaluation: Dict[str, Any],
                            site_requirements: SiteRequirements) -> List[str]:
    """Generate recommendations and next steps."""
    recommendations = []
    
    # Standard recommendations
    recommendations.append("Verify all site conditions match the specified requirements")
    recommendations.append("Confirm electrical supply compatibility with motor requirements")
    recommendations.append("Ensure proper foundation and piping design")
    
    # Specific recommendations based on analysis
    npsh_analysis = evaluation.get('npsh_analysis', {})
    if not npsh_analysis.get('npsha_available'):
        recommendations.append("Calculate and verify system NPSH available")
    
    bep_analysis = evaluation.get('bep_analysis', {})
    if bep_analysis.get('distance_from_bep_pct', 0) > 25:
        recommendations.append("Consider system modifications to operate closer to pump BEP")
    
    # Maintenance recommendations
    recommendations.append("Implement regular condition monitoring for optimal performance")
    recommendations.append("Follow manufacturer's maintenance schedule")
    
    return recommendations

def _generate_specifications_table(evaluation: Dict[str, Any],
                                 parsed_pump: ParsedPumpData) -> List[Dict[str, str]]:
    """Generate technical specifications table."""
    operating_point = evaluation.get('operating_point', {})
    
    specifications = [
        {'parameter': 'Pump Model', 'value': parsed_pump.model},
        {'parameter': 'Manufacturer', 'value': parsed_pump.manufacturer},
        {'parameter': 'Pump Type', 'value': parsed_pump.filter3},
        {'parameter': 'Impeller Diameter', 'value': operating_point.get('impeller_size', 'Standard')},
        {'parameter': 'Nominal Speed', 'value': f"{parsed_pump.nominal_speed} RPM"},
        {'parameter': 'Flow Rate', 'value': f"{operating_point.get('target_flow_m3hr', 0)} m³/hr"},
        {'parameter': 'Total Head', 'value': f"{operating_point.get('achieved_head_m', 0):.1f} m"},
        {'parameter': 'Efficiency', 'value': f"{operating_point.get('achieved_efficiency_pct', 0):.1f}%"},
        {'parameter': 'Power Consumption', 'value': f"{operating_point.get('achieved_power_kw', 0):.1f} kW"},
        {'parameter': 'NPSHr', 'value': f"{operating_point.get('achieved_npshr_m', 0):.2f} m"},
        {'parameter': 'Maximum Head', 'value': f"{parsed_pump.max_head} m"},
        {'parameter': 'Flow Range', 'value': f"{parsed_pump.min_flow}-{parsed_pump.max_flow} m³/hr"}
    ]
    
    return specifications

def _calculate_annual_energy_estimate(operating_point: Dict[str, Any]) -> str:
    """Calculate estimated annual energy consumption."""
    try:
        power_kw = operating_point.get('achieved_power_kw', 0)
        if power_kw > 0:
            # Assume 8760 hours/year operation (adjust as needed)
            annual_kwh = power_kw * 8760
            return f"{annual_kwh:,.0f} kWh/year"
        return "Not calculated"
    except:
        return "Not calculated"

def _generate_efficiency_benefits(power_analysis: Dict[str, Any]) -> List[str]:
    """Generate efficiency benefits list."""
    benefits = []
    rating = power_analysis.get('efficiency_rating', 'Good')
    
    if rating in ['Excellent', 'Very Good']:
        benefits.append("Reduced energy costs")
        benefits.append("Lower carbon footprint")
        benefits.append("Minimal heat generation")
    
    benefits.append("Reliable long-term operation")
    return benefits

def _identify_key_difference(alternative: Dict[str, Any]) -> str:
    """Identify key differentiating factor for alternative pump."""
    # Simple logic to identify key difference
    power_analysis = alternative.get('power_analysis', {})
    bep_analysis = alternative.get('bep_analysis', {})
    
    if power_analysis.get('power_at_duty_kw', 0) > 0:
        return f"Lower power consumption"
    elif bep_analysis.get('distance_from_bep_pct', 100) <= 10:
        return "Closer to BEP operation"
    else:
        return "Alternative design approach"
