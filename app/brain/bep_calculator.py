"""
BEP Calculator Module
=====================
Best Efficiency Point (BEP) calculation methods
"""

import logging
from typing import Dict, Any, Optional
from ..process_logger import process_logger

logger = logging.getLogger(__name__)



class BEPCalculator:
    """Handles Best Efficiency Point (BEP) calculations"""
    
    @staticmethod
    def calculate_bep_from_curves(pump_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calculate BEP from performance curves when missing from specifications.
        This is authentic engineering practice - BEP is the point of maximum efficiency.
        
        Args:
            pump_data: Pump data dictionary
            
        Returns:
            BEP dictionary or None if calculation fails
        """
        pump_code = pump_data.get('pump_code', 'Unknown')
        process_logger.log(f"Executing: {__name__}.BEPCalculator.calculate_bep_from_curves({pump_code})")
        
        try:
            curves = pump_data.get('curves', [])
            if not curves:
                process_logger.log(f"  → BEP CALCULATION: {pump_code} - No curves available")
                return None
            
            best_bep = None
            highest_efficiency = 0
            
            # Check all curves to find the one with highest efficiency point
            total_curves = len(curves)
            valid_curves = 0
            for curve in curves:
                points = curve.get('performance_points', [])
                if len(points) < 3:  # Need multiple points to find maximum
                    continue
                valid_curves += 1
                
                # Find maximum efficiency point in this curve
                for point in points:
                    efficiency = point.get('efficiency_pct', 0)
                    if efficiency > highest_efficiency:
                        highest_efficiency = efficiency
                        best_bep = {
                            'flow_m3hr': point.get('flow_m3hr', 0),
                            'head_m': point.get('head_m', 0),
                            'efficiency_pct': efficiency
                        }
            
            process_logger.log(f"  BEP CURVE ANALYSIS: {pump_code}")
            process_logger.log(f"    Total Curves: {total_curves}, Valid Curves: {valid_curves}")
            
            if best_bep and best_bep['flow_m3hr'] > 0 and best_bep['head_m'] > 0:
                process_logger.log(f"    → BEP FOUND: Q={best_bep['flow_m3hr']:.1f} m³/hr, H={best_bep['head_m']:.1f}m, Eff={best_bep['efficiency_pct']:.1f}%")
                logger.debug(f"[BEP] {pump_code}: Found BEP at {best_bep['flow_m3hr']:.1f} m³/hr, {best_bep['head_m']:.1f}m, {best_bep['efficiency_pct']:.1f}%")
                return best_bep
            
            process_logger.log(f"    → BEP CALCULATION: {pump_code} - No valid BEP found in curves")
            return None
            
        except Exception as e:
            process_logger.log(f"    → BEP CALCULATION ERROR: {pump_code} - {str(e)}", "WARNING")
            logger.debug(f"Error calculating BEP from curves for {pump_code}: {e}")
            return None
    
    @staticmethod
    def calculate_bep_from_curves_intelligent(pump_data: Dict[str, Any], 
                                            target_flow: float, target_head: float) -> Optional[Dict[str, Any]]:
        """
        Intelligently calculate BEP from curves by selecting the most appropriate curve
        for the target operating conditions, then finding maximum efficiency.
        
        Args:
            pump_data: Pump data dictionary
            target_flow: Target flow rate for curve selection
            target_head: Target head for curve selection
            
        Returns:
            BEP dictionary or None if calculation fails
        """
        pump_code = pump_data.get('pump_code', 'Unknown')
        process_logger.log(f"Executing: {__name__}.BEPCalculator.calculate_bep_from_curves_intelligent({pump_code}, Q={target_flow:.1f}, H={target_head:.1f})")
        
        try:
            curves = pump_data.get('curves', [])
            if not curves:
                process_logger.log(f"  → INTELLIGENT BEP: {pump_code} - No curves available")
                return None
            
            # Score each curve based on how well it matches the target conditions
            curve_scores = []
            
            for curve in curves:
                points = curve.get('performance_points', [])
                if len(points) < 3:
                    continue
                
                # Get curve operating range
                flows = [p.get('flow_m3hr', 0) for p in points if p.get('flow_m3hr', 0) > 0]
                heads = [p.get('head_m', 0) for p in points if p.get('head_m', 0) > 0]
                
                if not flows or not heads:
                    continue
                
                min_flow, max_flow = min(flows), max(flows)
                min_head, max_head = min(heads), max(heads)
                
                # Calculate how well this curve covers the target point
                flow_coverage = 1.0
                if target_flow < min_flow:
                    flow_coverage = min_flow / target_flow if target_flow > 0 else 0
                elif target_flow > max_flow:
                    flow_coverage = max_flow / target_flow if target_flow > 0 else 0
                
                head_coverage = 1.0
                if target_head < min_head:
                    head_coverage = min_head / target_head if target_head > 0 else 0
                elif target_head > max_head:
                    head_coverage = max_head / target_head if target_head > 0 else 0
                
                # Prefer curves that can handle the target conditions
                coverage_score = min(flow_coverage, head_coverage)
                
                # Get curve diameter for tie-breaking (larger = higher flow capability)
                diameter = curve.get('impeller_diameter_mm', 0)
                
                curve_scores.append({
                    'curve': curve,
                    'coverage_score': coverage_score,
                    'diameter': diameter,
                    'points': points
                })
            
            if not curve_scores:
                process_logger.log(f"  → INTELLIGENT BEP: {pump_code} - No valid curves for analysis")
                return None
            
            # Sort by coverage (best coverage first), then by diameter (larger first)
            curve_scores.sort(key=lambda x: (-x['coverage_score'], -x['diameter']))
            best_curve = curve_scores[0]['curve']
            best_points = curve_scores[0]['points']
            best_diameter = curve_scores[0]['diameter']
            best_coverage = curve_scores[0]['coverage_score']
            
            process_logger.log(f"  INTELLIGENT CURVE SELECTION: {pump_code}")
            process_logger.log(f"    Evaluated Curves: {len(curve_scores)}")
            process_logger.log(f"    Selected: {best_diameter:.0f}mm (Coverage: {best_coverage:.3f})")
            
            # Find BEP (maximum efficiency) in the selected curve
            best_bep = None
            highest_efficiency = 0
            
            for point in best_points:
                efficiency = point.get('efficiency_pct', 0)
                if efficiency > highest_efficiency:
                    highest_efficiency = efficiency
                    best_bep = {
                        'flow_m3hr': point.get('flow_m3hr', 0),
                        'head_m': point.get('head_m', 0),
                        'efficiency_pct': efficiency,
                        'diameter_mm': best_curve.get('impeller_diameter_mm', 0)
                    }
            
            if best_bep and best_bep['flow_m3hr'] > 0 and best_bep['head_m'] > 0:
                process_logger.log(f"    → INTELLIGENT BEP FOUND: Q={best_bep['flow_m3hr']:.1f} m³/hr, H={best_bep['head_m']:.1f}m, Eff={best_bep['efficiency_pct']:.1f}% ({best_bep['diameter_mm']:.0f}mm curve)")
                logger.debug(f"[BEP INTELLIGENT] {pump_code}: Selected {best_bep['diameter_mm']}mm curve - "
                           f"BEP at {best_bep['flow_m3hr']:.1f} m³/hr, {best_bep['head_m']:.1f}m, {best_bep['efficiency_pct']:.1f}%")
                return best_bep
            
            process_logger.log(f"    → INTELLIGENT BEP: {pump_code} - No valid BEP found in selected curve")
            return None
            
        except Exception as e:
            process_logger.log(f"    → INTELLIGENT BEP ERROR: {pump_code} - {str(e)}, falling back to simple method", "WARNING")
            logger.debug(f"Error in intelligent BEP calculation for {pump_code}: {e}")
            # Fallback to simple method
            return BEPCalculator.calculate_bep_from_curves(pump_data)