"""
Chart Intelligence Module
========================
Intelligent chart configuration and optimization
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ChartIntelligence:
    """Intelligence for chart visualization and configuration"""
    
    def __init__(self, brain):
        """
        Initialize with reference to main Brain.
        
        Args:
            brain: Parent PumpBrain instance
        """
        self.brain = brain
        
        # Chart configuration parameters
        self.margin_percent = {
            'web': 0.1,      # 10% margin for web display
            'pdf': 0.15,     # 15% margin for PDF reports
            'report': 0.12   # 12% margin for detailed reports
        }
        
        # Annotation preferences
        self.annotation_config = {
            'show_bep': True,
            'show_operating_point': True,
            'show_efficiency_zones': True,
            'show_npsh_margin': True
        }
    
    def get_optimal_config(self, pump: Dict[str, Any], context: str = "web") -> Dict[str, Any]:
        """
        Get optimal chart configuration for pump visualization.
        
        Args:
            pump: Pump data with curves
            context: Display context (web/pdf/report)
        
        Returns:
            Optimized chart configuration
        """
        config = {
            'context': context,
            'margin': self.margin_percent.get(context, 0.1),
            'annotations': [],
            'axis_ranges': {},
            'display_options': {}
        }
        
        try:
            # Get pump curves
            curves = pump.get('curves', [])
            if not curves:
                logger.warning(f"No curves for pump {pump.get('pump_code')}")
                return config
            
            # Determine axis ranges
            all_flows = []
            all_heads = []
            all_effs = []
            all_powers = []
            
            for curve in curves:
                points = curve.get('performance_points', [])
                for point in points:
                    all_flows.append(point.get('flow_m3hr', 0))
                    all_heads.append(point.get('head_m', 0))
                    all_effs.append(point.get('efficiency_pct', 0))
                    if point.get('power_kw'):
                        all_powers.append(point['power_kw'])
            
            if all_flows and all_heads:
                # Calculate optimal ranges with margin
                margin = config['margin']
                
                config['axis_ranges'] = {
                    'flow': {
                        'min': 0,  # Always start at 0 for flow
                        'max': max(all_flows) * (1 + margin)
                    },
                    'head': {
                        'min': 0,  # Always start at 0 for head
                        'max': max(all_heads) * (1 + margin)
                    },
                    'efficiency': {
                        'min': 0,
                        'max': min(100, max(all_effs) * (1 + margin * 0.5))
                    }
                }
                
                if all_powers:
                    config['axis_ranges']['power'] = {
                        'min': 0,
                        'max': max(all_powers) * (1 + margin)
                    }
            
            # Configure display options based on context
            if context == 'web':
                config['display_options'] = {
                    'interactive': True,
                    'show_hover': True,
                    'show_toolbar': True,
                    'responsive': True
                }
            elif context == 'pdf':
                config['display_options'] = {
                    'interactive': False,
                    'show_hover': False,
                    'show_toolbar': False,
                    'high_resolution': True
                }
            else:  # report
                config['display_options'] = {
                    'interactive': False,
                    'show_hover': False,
                    'show_toolbar': False,
                    'detailed_annotations': True
                }
            
            # Add BEP annotation if available
            specs = pump.get('specifications', {})
            bep_flow = specs.get('bep_flow_m3hr')
            bep_head = specs.get('bep_head_m')
            
            if bep_flow and bep_head and self.annotation_config['show_bep']:
                config['annotations'].append({
                    'type': 'point',
                    'x': bep_flow,
                    'y': bep_head,
                    'text': 'BEP',
                    'style': 'star',
                    'color': 'gold'
                })
            
        except Exception as e:
            logger.error(f"Error generating chart config: {str(e)}")
        
        return config
    
    def generate_annotations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate intelligent annotations based on analysis.
        
        Args:
            analysis: Pump analysis results
        
        Returns:
            List of annotation configurations
        """
        annotations = []
        
        try:
            # Operating point annotation
            if self.annotation_config['show_operating_point']:
                flow = analysis.get('flow_m3hr')
                head = analysis.get('head_m')
                if flow and head:
                    annotations.append({
                        'type': 'point',
                        'x': flow,
                        'y': head,
                        'text': 'Operating Point',
                        'style': 'circle',
                        'color': 'red',
                        'size': 8
                    })
            
            # Efficiency zone annotations
            if self.annotation_config['show_efficiency_zones']:
                efficiency = analysis.get('efficiency_pct')
                if efficiency:
                    zone = self._get_efficiency_zone(efficiency)
                    annotations.append({
                        'type': 'text',
                        'text': f'Efficiency: {efficiency:.1f}% ({zone})',
                        'position': 'top-right',
                        'style': 'badge',
                        'color': self._get_efficiency_color(efficiency)
                    })
            
            # NPSH margin annotation
            if self.annotation_config['show_npsh_margin']:
                npshr = analysis.get('npshr_m')
                npsha = analysis.get('npsha_m')
                if npshr and npsha:
                    margin = npsha - npshr
                    status = 'OK' if margin > 1.5 else 'Warning'
                    annotations.append({
                        'type': 'text',
                        'text': f'NPSH Margin: {margin:.1f}m ({status})',
                        'position': 'bottom-right',
                        'style': 'badge',
                        'color': 'green' if margin > 1.5 else 'orange'
                    })
            
            # Head margin annotation
            head_margin = analysis.get('head_margin_m')
            if head_margin is not None:
                annotations.append({
                    'type': 'text',
                    'text': f'Head Margin: {head_margin:.1f}m',
                    'position': 'top-left',
                    'style': 'info'
                })
            
            # Trimming annotation
            trim_percent = analysis.get('trim_percent')
            if trim_percent and trim_percent < 100:
                annotations.append({
                    'type': 'text',
                    'text': f'Impeller Trim: {trim_percent:.1f}%',
                    'position': 'bottom-left',
                    'style': 'info',
                    'color': 'blue'
                })
            
        except Exception as e:
            logger.error(f"Error generating annotations: {str(e)}")
        
        return annotations
    
    def calculate_axis_ranges(self, curves: List[Dict[str, Any]], 
                            operating_point: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Calculate optimal axis ranges for chart display.
        
        Args:
            curves: List of performance curves
            operating_point: Optional (flow, head) tuple
        
        Returns:
            Axis range configuration
        """
        ranges = {
            'flow': {'min': 0, 'max': 100},
            'head': {'min': 0, 'max': 100},
            'efficiency': {'min': 0, 'max': 100},
            'power': {'min': 0, 'max': 100}
        }
        
        try:
            # Collect all data points
            all_flows = []
            all_heads = []
            all_effs = []
            all_powers = []
            
            for curve in curves:
                points = curve.get('performance_points', [])
                for point in points:
                    all_flows.append(point.get('flow_m3hr', 0))
                    all_heads.append(point.get('head_m', 0))
                    all_effs.append(point.get('efficiency_pct', 0))
                    if point.get('power_kw'):
                        all_powers.append(point['power_kw'])
            
            # Include operating point if provided
            if operating_point:
                all_flows.append(operating_point[0])
                all_heads.append(operating_point[1])
            
            # Calculate ranges with smart margins
            if all_flows:
                flow_max = max(all_flows)
                # Round up to nice number
                flow_max_rounded = self._round_up_nice(flow_max * 1.1)
                ranges['flow'] = {'min': 0, 'max': int(flow_max_rounded)}
            
            if all_heads:
                head_max = max(all_heads)
                head_max_rounded = self._round_up_nice(head_max * 1.1)
                ranges['head'] = {'min': 0, 'max': int(head_max_rounded)}
            
            if all_effs:
                eff_max = min(100, max(all_effs) * 1.05)
                ranges['efficiency'] = {'min': 0, 'max': eff_max}
            
            if all_powers:
                power_max = max(all_powers)
                power_max_rounded = self._round_up_nice(power_max * 1.1)
                ranges['power'] = {'min': 0, 'max': int(power_max_rounded)}
            
        except Exception as e:
            logger.error(f"Error calculating axis ranges: {str(e)}")
        
        return ranges
    
    def _round_up_nice(self, value: float) -> float:
        """
        Round up to a nice number for axis display.
        
        Args:
            value: Value to round
        
        Returns:
            Rounded value
        """
        if value <= 0:
            return 10
        
        # Find order of magnitude
        magnitude = 10 ** np.floor(np.log10(value))
        
        # Round up to nearest nice number
        normalized = value / magnitude
        
        if normalized <= 1:
            return magnitude
        elif normalized <= 2:
            return 2 * magnitude
        elif normalized <= 5:
            return 5 * magnitude
        else:
            return 10 * magnitude
    
    def generate_chart_data_payload(self, pump: Dict[str, Any], evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete chart data payload ready for frontend plotting.
        Brain Intelligence handles ALL chart logic - API just passes this through.
        
        Args:
            pump: Complete pump data from repository
            evaluation_result: Brain evaluation result for duty point
            
        Returns:
            Complete chart data payload ready for JSON serialization
        """
        try:
            pump_code = pump.get('pump_code', '')
            curves = pump.get('curves', [])
            
            if not curves:
                logger.warning(f"No curves available for pump {pump_code}")
                return {}
            
            # Build complete chart data structure - BRAIN INTELLIGENCE
            chart_data = {
                'pump_code': pump_code,
                'pump_info': {
                    'manufacturer': pump.get('manufacturer', 'APE PUMPS'),
                    'series': pump.get('model_series', ''),
                    'description': pump.get('pump_code', pump_code)
                },
                'curves': [],
                'operating_point': {
                    'flow_m3hr': evaluation_result.get('flow_m3hr', 0),
                    'head_m': evaluation_result.get('head_m', 0),
                    'efficiency_pct': evaluation_result.get('efficiency_pct', 0),
                    'power_kw': evaluation_result.get('power_kw', 0),
                    'npshr_m': evaluation_result.get('npshr_m', 0),
                    'impeller_diameter_mm': evaluation_result.get('impeller_diameter_mm', 0),
                    'trim_percent': evaluation_result.get('trim_percent', 100),
                    'qbep_percentage': evaluation_result.get('qbep_percentage', 100),
                    'extrapolated': evaluation_result.get('extrapolated', False),
                    'sizing_info': evaluation_result.get('sizing_info', {})
                },
                'brain_config': {
                    'context': 'web',
                    'annotations': [],
                    'axis_ranges': {'flow': {'min': 0, 'max': 600}, 'head': {'min': 0, 'max': 100}},
                    'display_options': {'interactive': True, 'show_hover': True}
                },
                'metadata': {
                    'flow_units': 'm³/hr', 'head_units': 'm', 'efficiency_units': '%',
                    'power_units': 'kW', 'npshr_units': 'm', 'brain_generated': True,
                    'generation_timestamp': evaluation_result.get('timestamp', '')
                }
            }
            
            # Add BEP annotation if available - BRAIN INTELLIGENCE
            bep_flow = evaluation_result.get('bep_flow_m3hr')
            bep_head = evaluation_result.get('bep_head_m')
            if bep_flow and bep_head:
                chart_data['brain_config']['annotations'].append({
                    'type': 'point', 'x': bep_flow, 'y': bep_head, 
                    'text': 'BEP', 'style': 'star', 'color': 'gold'
                })
            
            # Process curves - BRAIN HANDLES ALL TRANSFORMATIONS
            for i, curve in enumerate(curves):
                # Brain generates intelligent display labels
                impeller_mm = curve.get('impeller_diameter_mm', 0)
                display_label = f"{impeller_mm}mm Impeller" if impeller_mm > 0 else f"Curve {i+1}"
                
                # Determine if this curve is selected (matches evaluation result)
                is_selected = False
                eval_impeller = evaluation_result.get('impeller_diameter_mm', 0)
                if eval_impeller > 0 and impeller_mm > 0:
                    is_selected = abs(eval_impeller - impeller_mm) < 1.0  # 1mm tolerance
                elif i == 0:  # Default to first curve if no match
                    is_selected = True
                
                # CRITICAL FIX: Extract performance points into separate arrays
                performance_points = curve.get('performance_points', [])
                
                # Initialize arrays for chart data
                flow_data = []
                head_data = []
                efficiency_data = []
                power_data = []
                npshr_data = []
                
                # Extract data from performance points
                for point in performance_points:
                    flow_m3hr = point.get('flow_m3hr', 0)
                    head_m = point.get('head_m', 0)
                    efficiency_pct = point.get('efficiency_pct', 0)
                    npshr_m = point.get('npshr_m', 0)
                    
                    flow_data.append(flow_m3hr)
                    head_data.append(head_m)
                    efficiency_data.append(efficiency_pct)
                    npshr_data.append(npshr_m)
                    
                    # Calculate power from authentic manufacturer data using hydraulic formula
                    # This is standard engineering practice, not fallback data
                    power_kw = point.get('power_kw', None)
                    if power_kw is None and efficiency_pct > 0 and flow_m3hr > 0 and head_m > 0:
                        # Standard hydraulic power calculation: P = ρgQH/η
                        rho = 1000  # kg/m³ for water
                        g = 9.81    # m/s²
                        flow_m3s = flow_m3hr / 3600  # Convert to m³/s
                        power_kw = (rho * g * flow_m3s * head_m) / (efficiency_pct / 100 * 1000)
                        logger.debug(f"Calculated power for {pump_code} curve {i}: {power_kw:.2f}kW from authentic data")
                    elif power_kw is None:
                        power_kw = 0
                    
                    power_data.append(power_kw)
                
                chart_data['curves'].append({
                    'curve_index': i,
                    'impeller_size': curve.get('impeller_size', display_label),
                    'impeller_diameter_mm': impeller_mm,
                    'display_label': display_label,  # Brain-generated label
                    'flow_data': flow_data,
                    'head_data': head_data,
                    'efficiency_data': efficiency_data,
                    'power_data': power_data,
                    'npshr_data': npshr_data,
                    'is_selected': is_selected
                })
            
            logger.info(f"Brain generated chart payload for {pump_code} with {len(chart_data['curves'])} curves")
            return chart_data
            
        except Exception as e:
            logger.error(f"Error in Brain chart payload generation: {str(e)}")
            return {}
    
    def _get_efficiency_zone(self, efficiency: float) -> str:
        """Get efficiency zone description."""
        if efficiency >= 85:
            return "Excellent"
        elif efficiency >= 75:
            return "Good"
        elif efficiency >= 65:
            return "Fair"
        elif efficiency >= 50:
            return "Poor"
        else:
            return "Very Poor"
    
    def _get_efficiency_color(self, efficiency: float) -> str:
        """Get color based on efficiency."""
        if efficiency >= 85:
            return "green"
        elif efficiency >= 75:
            return "lightgreen"
        elif efficiency >= 65:
            return "yellow"
        elif efficiency >= 50:
            return "orange"
        else:
            return "red"