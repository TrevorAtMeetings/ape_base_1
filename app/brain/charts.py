"""
Chart Intelligence Module
========================
Intelligent chart configuration and optimization
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from .config_manager import config

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
            'web': config.get('charts', 'chart_margin_for_web_display_10'),      # 10% margin for web display
            'pdf': config.get('charts', 'chart_margin_for_pdf_reports_15'),     # 15% margin for PDF reports
            'report': config.get('charts', 'chart_margin_for_detailed_reports_12')   # 12% margin for detailed reports
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
            all_npshrs = []
            
            for curve in curves:
                points = curve.get('performance_points', [])
                for point in points:
                    all_flows.append(point.get('flow_m3hr', 0))
                    all_heads.append(point.get('head_m', 0))
                    all_effs.append(point.get('efficiency_pct', 0))
                    if point.get('power_kw'):
                        all_powers.append(point['power_kw'])
                    if point.get('npshr_m'):
                        all_npshrs.append(point['npshr_m'])
            
            if all_flows and all_heads:
                # Calculate optimal ranges with margin
                margin = config['margin']
                
                config['axis_ranges'] = {
                    'flow': {
                        'min': min(all_flows) * 0.9 if all_flows else 0,  # Start below minimum data
                        'max': max(all_flows) * (1 + margin)
                    },
                    'head': {
                        'min': min(all_heads) * 0.9 if all_heads else 0,  # Start below minimum data
                        'max': max(all_heads) * (1 + margin)
                    },
                    'efficiency': {
                        'min': max(0, min(all_effs) - 5) if all_effs else 0,  # Start 5% below minimum
                        'max': min(100, max(all_effs) + 5) if all_effs else 100  # End 5% above maximum
                    },
                    'power': {
                        'min': min(all_powers) * 0.9 if all_powers else 0,
                        'max': max(all_powers) * (1 + margin) if all_powers else 200
                    },
                    'npshr': {
                        'min': 0,  # NPSHr always starts from 0 for safety visualization
                        'max': max(all_npshrs) * 1.2 if all_npshrs else 20  # 20% margin above max
                    }
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
            
            # Add enhanced BEP annotation with authentic manufacturer data
            specs = pump.get('specifications', {})
            bep_flow = specs.get('bep_flow_m3hr')
            bep_head = specs.get('bep_head_m')
            
            if bep_flow and bep_head and self.annotation_config['show_bep']:
                # Enhanced BEP annotation with flow/head values
                bep_text = f'BEP: {bep_flow:.0f} m³/hr @ {bep_head:.1f}m'
                config['annotations'].append({
                    'type': 'point',
                    'x': bep_flow,
                    'y': bep_head,
                    'text': bep_text,
                    'style': 'circle',
                    'color': 'blue',
                    'size': 10,
                    'label_position': 'top-right'
                })
            
        except Exception as e:
            logger.error(f"[CHART CONFIG] Error generating chart config: {str(e)}")
            # Chart configuration is non-critical - return basic config for visualization
            config['annotations'] = []  # Clear any partial annotations
            config['display_options'] = {'interactive': True, 'show_hover': True}
        
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
            logger.error(f"[CHART ANNOTATIONS] Error generating annotations: {str(e)}")
            # Annotation failures are non-critical - return empty list for basic charts
            
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
                ranges['flow'] = {'min': int(min(all_flows) * 0.9), 'max': int(flow_max_rounded)}
            
            if all_heads:
                head_max = max(all_heads)
                head_max_rounded = self._round_up_nice(head_max * 1.1)
                ranges['head'] = {'min': int(min(all_heads) * 0.9), 'max': int(head_max_rounded)}
            
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
            
            # Get optimal configuration with calculated axis ranges - BRAIN INTELLIGENCE
            optimal_config = self.get_optimal_config(pump, 'web')
            
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
                    'sizing_info': evaluation_result.get('sizing_info', {}),
                    'bep_flow_m3hr': 0,  # Will be populated with authentic data below
                    'bep_head_m': 0,     # Will be populated with authentic data below
                },
                'brain_config': {
                    'context': 'web',
                    'annotations': optimal_config.get('annotations', []),
                    'axis_ranges': optimal_config.get('axis_ranges', {'flow': {'min': 0, 'max': 600}, 'head': {'min': 0, 'max': 100}}),
                    'display_options': optimal_config.get('display_options', {'interactive': True, 'show_hover': True})
                },
                'metadata': {
                    'flow_units': 'm³/hr', 'head_units': 'm', 'efficiency_units': '%',
                    'power_units': 'kW', 'npshr_units': 'm', 'brain_generated': True,
                    'generation_timestamp': evaluation_result.get('timestamp', '')
                }
            }
            
            # Add enhanced BEP annotation with authentic manufacturer data - BRAIN INTELLIGENCE
            specs = pump.get('specifications', {})
            bep_flow = specs.get('bep_flow_m3hr')
            bep_head = specs.get('bep_head_m')
            
            if bep_flow and bep_head:
                # Calculate BEP percentage relative to operating point
                op_flow = evaluation_result.get('flow_m3hr', 0)
                qbep_percentage = (op_flow / bep_flow * 100) if bep_flow > 0 else 0
                
                # Enhanced BEP annotation with blue marker and detailed info
                bep_text = f'BEP: {bep_flow:.0f} m³/hr @ {bep_head:.1f}m'
                chart_data['brain_config']['annotations'].extend([
                    {
                        'type': 'point', 
                        'x': bep_flow, 
                        'y': bep_head,
                        'text': bep_text,
                        'style': 'circle', 
                        'color': 'blue',
                        'size': 12,
                        'label_position': 'top-right'
                    }
                ])
                
                # Add BEP data to operating point for enhanced display
                chart_data['operating_point']['bep_flow_m3hr'] = bep_flow
                chart_data['operating_point']['bep_head_m'] = bep_head
                chart_data['operating_point']['qbep_percentage'] = qbep_percentage
                
                # DEBUG: Log BEP data inclusion for chart markers
                logger.info(f"[CHART DEBUG] {pump_code}: BEP marker data - Flow: {bep_flow} m³/hr, Head: {bep_head} m")
            else:
                # DEBUG: Log when BEP data is missing
                logger.warning(f"[CHART DEBUG] {pump_code}: No BEP data available - Flow: {bep_flow}, Head: {bep_head}")
            
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
                
                # Generate power curves using Brain performance analysis
                # This ensures consistency with pump selection power values
                for point in performance_points:
                    flow_m3hr = point.get('flow_m3hr', 0)
                    head_m = point.get('head_m', 0)
                    efficiency_pct = point.get('efficiency_pct', 0)
                    npshr_m = point.get('npshr_m', 0)
                    
                    # Skip points with zero flow for better curve quality
                    if flow_m3hr <= 0:
                        continue
                    
                    # Use Brain's hydraulic power calculation for consistency with pump selection
                    power_kw = point.get('power_kw')
                    if power_kw is None and efficiency_pct > 20 and flow_m3hr > 0 and head_m > 0:
                        # Use same hydraulic calculation as Brain performance analysis
                        flow_m3s = flow_m3hr / 3600  # Convert to m³/s
                        rho = 1000  # kg/m³ for water (hardcoded for chart display) 
                        g = 9.81    # m/s² (hardcoded for chart display)
                        power_kw = (rho * g * flow_m3s * head_m) / (efficiency_pct / 100 * 1000)
                        logger.debug(f"Brain hydraulic power for {pump_code} curve {i}: {power_kw:.2f}kW")
                    elif power_kw is None or power_kw <= 0:
                        # Skip invalid power points to improve curve quality
                        continue
                    
                    # Only add valid points to all arrays together
                    flow_data.append(flow_m3hr)
                    head_data.append(head_m)
                    efficiency_data.append(efficiency_pct)
                    npshr_data.append(npshr_m)
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
            
            # Calculate power and NPSHr axis ranges from generated curve data
            all_power_values = []
            all_npshr_values = []
            for curve in chart_data['curves']:
                power_data = curve.get('power_data', [])
                npshr_data = curve.get('npshr_data', [])
                all_power_values.extend([p for p in power_data if p and p > 0])
                all_npshr_values.extend([n for n in npshr_data if n and n > 0])
            
            if all_power_values:
                margin = config.get('charts', 'chart_margin_for_web_display_10')  # 10% margin
                power_min = min(all_power_values) * 0.9
                power_max = max(all_power_values) * (1 + margin)
                chart_data['brain_config']['axis_ranges']['power'] = {
                    'min': power_min,
                    'max': power_max
                }
                logger.info(f"Generated power axis range from curve data: min={power_min:.2f}, max={power_max:.2f}")
            
            if all_npshr_values:
                npshr_max = max(all_npshr_values) * 1.2  # 20% margin
                chart_data['brain_config']['axis_ranges']['npshr'] = {
                    'min': 0,  # NPSHr always starts from 0
                    'max': npshr_max
                }
                logger.info(f"Generated NPSHr axis range from curve data: min=0, max={npshr_max:.2f}")
            
            # FORCE efficiency axis ranges from generated curve data - OVERRIDE initial calculation
            all_efficiency_values = []
            for curve in chart_data['curves']:
                efficiency_data = curve.get('efficiency_data', [])
                all_efficiency_values.extend([e for e in efficiency_data if e and e > 0])
            
            # ALWAYS update efficiency ranges with curve data (more accurate than initial calculation)
            if all_efficiency_values:
                efficiency_min = max(0, min(all_efficiency_values) - 5)  # Start 5% below minimum, but not below 0
                efficiency_max = min(100, max(all_efficiency_values) + 5)  # End 5% above maximum, but not above 100
                # FORCE override the axis ranges
                if 'axis_ranges' not in chart_data['brain_config']:
                    chart_data['brain_config']['axis_ranges'] = {}
                chart_data['brain_config']['axis_ranges']['efficiency'] = {
                    'min': efficiency_min,
                    'max': efficiency_max
                }
                logger.info(f"OVERRIDE: Generated efficiency axis range from curve data: min={efficiency_min:.2f}, max={efficiency_max:.2f} (min_data={min(all_efficiency_values)}, max_data={max(all_efficiency_values)})")
            else:
                logger.warning("OVERRIDE: No efficiency values found in curve data for axis range calculation")
            
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