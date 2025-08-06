"""
APE Catalog Engine
Updated pump selection engine using authentic APE catalog structure
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import interpolate
from .pump_repository import get_pump_repository
from .data_models import PumpEvaluation, ExclusionReason

logger = logging.getLogger(__name__)


class CatalogPump:
    """Represents a pump model with multiple performance curves"""

    def __init__(self, pump_data: Dict[str, Any]):
        self.pump_code = pump_data['pump_code']
        self.pump_id = pump_data.get('pump_id',
                                     None)  # Add pump_id for BEP markers
        self.manufacturer = pump_data['manufacturer']
        self.pump_type = pump_data['pump_type']
        self.model_series = pump_data['model_series']
        self.specifications = pump_data['specifications']
        self.curves = pump_data['curves']
        self.curve_count = pump_data['curve_count']
        self.total_points = pump_data['total_points']
        self.npsh_curves = pump_data['npsh_curves']
        self.power_curves = pump_data['power_curves']

        # Additional attributes for compatibility
        self.description = pump_data.get(
            'description', f"{self.pump_code} - {self.model_series}")
        self.max_flow_m3hr = pump_data.get('max_flow_m3hr',
                                           self._calculate_max_flow())
        self.max_head_m = pump_data.get('max_head_m',
                                        self._calculate_max_head())
        self.max_power_kw = pump_data.get('max_power_kw',
                                          self._calculate_max_power())
        self.min_efficiency = pump_data.get('min_efficiency',
                                            self._calculate_min_efficiency())
        self.max_efficiency = pump_data.get('max_efficiency',
                                            self._calculate_max_efficiency())
        self.connection_size = pump_data.get('connection_size', 'Standard')
        self.materials = pump_data.get('materials', 'Cast Iron')

    def _calculate_max_flow(self) -> float:
        """Calculate maximum flow from all curves"""
        max_flow = 0.0
        for curve in self.curves:
            flows = [p['flow_m3hr'] for p in curve['performance_points']]
            if flows:
                max_flow = max(max_flow, max(flows))
        return max_flow

    def _calculate_max_head(self) -> float:
        """Calculate maximum head from all curves"""
        max_head = 0.0
        for curve in self.curves:
            heads = [p['head_m'] for p in curve['performance_points']]
            if heads:
                max_head = max(max_head, max(heads))
        return max_head

    def _calculate_max_power(self) -> float:
        """Calculate maximum power from all curves"""
        max_power = 0.0
        for curve in self.curves:
            powers = [
                p.get('power_kw', 0) for p in curve['performance_points']
                if p.get('power_kw')
            ]
            if powers:
                max_power = max(max_power, max(powers))
        return max_power if max_power > 0 else 50.0  # Default estimate

    def _calculate_min_efficiency(self) -> float:
        """Calculate minimum efficiency from all curves"""
        min_eff = 100.0
        for curve in self.curves:
            effs = [
                p['efficiency_pct'] for p in curve['performance_points']
                if p['efficiency_pct'] > 0
            ]
            if effs:
                min_eff = min(min_eff, min(effs))
        return min_eff if min_eff < 100.0 else 0.0

    def _calculate_max_efficiency(self) -> float:
        """Calculate maximum efficiency from all curves"""
        max_eff = 0.0
        for curve in self.curves:
            effs = [p['efficiency_pct'] for p in curve['performance_points']]
            if effs:
                max_eff = max(max_eff, max(effs))
        return max_eff

    def get_bep_point(self) -> Optional[Dict[str, Any]]:
        """Find the Best Efficiency Point (BEP) across all curves"""
        # Find BEP from curve analysis

        # Fallback to curve analysis
        best_bep = None
        best_efficiency = 0.0

        for curve in self.curves:
            points = curve['performance_points']
            for point in points:
                efficiency = point.get('efficiency_pct', 0)
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_bep = {
                        'flow_m3hr': point['flow_m3hr'],
                        'head_m': point['head_m'],
                        'efficiency_pct': efficiency,
                        'power_kw': point.get('power_kw'),
                        'npshr_m': point.get('npshr_m'),
                        'curve_id': curve['curve_id'],
                        'impeller_diameter_mm': curve['impeller_diameter_mm'],
                        'source': 'curve_analysis'
                    }

        return best_bep

    def calculate_bep_distance(self, target_flow: float,
                               target_head: float) -> Dict[str, Any]:
        """Calculate distance from BEP and provide industry-standard BEP-based scoring"""
        bep = self.get_bep_point()
        if not bep:
            return {
                'bep_score': 0,
                'distance_pct': float('inf'),
                'bep_available': False
            }

        bep_flow = bep['flow_m3hr']
        bep_head = bep['head_m']

        # Calculate flow position relative to BEP
        flow_ratio = target_flow / bep_flow if bep_flow > 0 else 0
        flow_distance_pct = abs(
            target_flow -
            bep_flow) / bep_flow * 100 if bep_flow > 0 else float('inf')
        head_distance_pct = abs(
            target_head -
            bep_head) / bep_head * 100 if bep_head > 0 else float('inf')

        # CORRECTED: Industry-standard tolerance zones with stricter evaluation
        # Preferred operating range: 80% to 110% of BEP flow (tighter than before)
        operating_zone = "unknown"
        zone_score = 0

        if 0.95 <= flow_ratio <= 1.05:
            # At BEP (95-105%) - Excellent - HIGHEST PRIORITY
            operating_zone = "at_bep"
            zone_score = 30
        elif 0.90 <= flow_ratio < 0.95:
            # Left side of BEP (90-95%) - Very Good
            operating_zone = "left_good"
            zone_score = 28
        elif 1.05 < flow_ratio <= 1.10:
            # Right side preferred zone (105-110%) - Very Good
            operating_zone = "right_good"
            zone_score = 26
        elif 0.85 <= flow_ratio < 0.90:
            # Left acceptable (85-90%) - Good but efficiency drops
            operating_zone = "left_acceptable"
            zone_score = 22
        elif 1.10 < flow_ratio <= 1.15:
            # Extended right (110-115%) - Good but NPSH increases
            operating_zone = "right_acceptable"
            zone_score = 20
        elif 0.80 <= flow_ratio < 0.85:
            # Lower flow zone (80-85%) - Marginal, efficiency concerns
            operating_zone = "low_flow"
            zone_score = 15
        elif 1.15 < flow_ratio <= 1.25:
            # Far right (115-125%) - Marginal, cavitation risk
            operating_zone = "extended_right"
            zone_score = 12
        elif 0.70 <= flow_ratio < 0.80:
            # Very low flow (70-80%) - Poor, potential instability
            operating_zone = "very_low_flow"
            zone_score = 8
        elif 1.25 < flow_ratio <= 1.35:
            # Overload zone (125-135%) - Poor, high power/cavitation risk
            operating_zone = "overload_zone"
            zone_score = 5
        else:
            # Outside reasonable operating envelope - Unacceptable
            operating_zone = "outside_envelope"
            zone_score = 0

        # Head tolerance check (±15% typical)
        head_tolerance_met = head_distance_pct <= 15
        if not head_tolerance_met:
            zone_score = max(0, zone_score - 10)  # Penalty for head mismatch

        # Additional bonus for ideal right-side operation (105-115% BEP)
        if 1.05 <= flow_ratio <= 1.15:
            zone_score += 4  # Industry preference bonus (total 29 points for right preferred zone)

        return {
            'bep_score': zone_score,
            'distance_pct': round(flow_distance_pct, 1),
            'flow_ratio': round(flow_ratio, 2),
            'operating_zone': operating_zone,
            'head_tolerance_met': head_tolerance_met,
            'flow_distance_pct': round(flow_distance_pct, 1),
            'head_distance_pct': round(head_distance_pct, 1),
            'bep_available': True,
            'bep_flow': bep_flow,
            'bep_head': bep_head,
            'bep_efficiency': bep['efficiency_pct'],
            'on_right_side': target_flow > bep_flow * 0.95
        }

    def get_best_curve_for_duty(self, flow_m3hr: float,
                                head_m: float) -> Optional[Dict[str, Any]]:
        """Find the best curve for the given duty point - allows safe extrapolation up to 20%"""
        best_curve = None
        best_score = float('inf')

        for curve in self.curves:
            # Calculate how well this curve matches the duty point
            points = curve['performance_points']
            flows = [p['flow_m3hr'] for p in points]
            heads = [p['head_m'] for p in points]

            if not flows or not heads:
                continue

            # Industry-standard extrapolation: try 15% first, then 20% for comprehensive coverage
            flow_min, flow_max = min(flows), max(flows)
            head_min, head_max = min(heads), max(heads)
            
            # Calculate extrapolation requirements
            flow_extrapolation = 0
            head_extrapolation = 0
            
            if flow_m3hr < flow_min:
                flow_extrapolation = (flow_min - flow_m3hr) / flow_min * 100
            elif flow_m3hr > flow_max:
                flow_extrapolation = (flow_m3hr - flow_max) / flow_max * 100
                
            if head_m < head_min:
                head_extrapolation = (head_min - head_m) / head_min * 100
            elif head_m > head_max:
                head_extrapolation = (head_m - head_max) / head_max * 100
            
            max_extrapolation = max(flow_extrapolation, head_extrapolation)
            
            # Allow up to 20% extrapolation (industry standard)
            flow_in_range = flow_min * 0.8 <= flow_m3hr <= flow_max * 1.2
            head_in_range = head_min * 0.8 <= head_m <= head_max * 1.2

            if flow_in_range and head_in_range:
                # Calculate efficiency at duty point
                try:
                    head_interp = interpolate.interp1d(flows,
                                                       heads,
                                                       kind='linear',
                                                       bounds_error=False,
                                                       fill_value=0)
                    eff_interp = interpolate.interp1d(
                        flows, [p['efficiency_pct'] for p in points],
                        kind='linear',
                        bounds_error=False,
                                                      fill_value=0)

                    predicted_head = head_interp(flow_m3hr)
                    efficiency = eff_interp(flow_m3hr)

                    if not np.isnan(predicted_head) and not np.isnan(
                            efficiency):
                        head_error = abs(float(predicted_head) - head_m)
                        score = head_error - efficiency * 0.1  # Favor higher efficiency

                        if score < best_score:
                            best_score = score
                            best_curve = curve

                except Exception as e:
                    logger.debug(
                        f"Interpolation error for {self.pump_code} curve {curve['curve_index']}: {e}"
                    )
                    continue

        return best_curve

    def find_best_solution_for_duty(self, flow_m3hr: float, head_m: float, npsha_available: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """v6.0 UNIFIED EVALUATION: Single authoritative "Best Fit" function that replaces both can_meet_requirements and get_performance_at_duty
        
        This function embodies the true "Best Fit" philosophy by:
        1. Applying hard gates first (QBP, NPSH)
        2. Evaluating ALL possible fixed-speed methods
        3. Scoring each viable solution  
        4. Returning the single best solution (or None if no solution exists)
        
        Returns: Complete solution dict with performance data and score, or None if infeasible
        """
        from .impeller_scaling import get_impeller_scaling_engine
        scaling_engine = get_impeller_scaling_engine()
        
        # Step 1: Basic validation - Check if curves exist
        if not self.curves or not any(curve.get('performance_points') for curve in self.curves):
            logger.debug(f"Pump {self.pump_code}: No performance data available")
            return None
        
        # Step 2: Apply v6.0 HARD GATES first
        
        # Hard Gate 1: QBP Range (60-130% of BEP)
        qbp_gate_result = self._validate_qbp_range(flow_m3hr)
        if not qbp_gate_result['passed']:
            logger.debug(f"Pump {self.pump_code}: Failed QBP gate - {qbp_gate_result['reason']}")
            return None
        
        # Step 3: Initialize solutions list for "Best Fit" evaluation
        possible_solutions = []
        
        # Step 4: Systematically evaluate ALL fixed-speed methods
        
        # Method 1: Direct Interpolation (within existing curves, 100% trim)
        interpolated = self._get_performance_interpolated(flow_m3hr, head_m)
        if interpolated and interpolated.get('head_m', 0) >= head_m * 0.98:  # 2% tolerance
            performance = interpolated
            
            # Hard Gate 2: NPSH Safety (apply to this solution)
            npsh_gate_result = self._validate_npsh_safety_gate(performance, npsha_available)
            if npsh_gate_result['passed']:
                # Calculate score for this solution
                sizing_info = {
                    'method': 'direct_interpolation',
                    'trim_percent': 100.0,
                    'meets_requirements': True,
                    'head_margin_m': performance['head_m'] - head_m,
                    'sizing_method': 'direct_interpolation'
                }
                score = self._calculate_solution_score(performance, sizing_info, flow_m3hr, head_m)
                
                solution = {
                    'method': 'direct_interpolation',
                    'performance': performance,
                    'sizing_info': sizing_info,
                    'score': score
                }
                possible_solutions.append(solution)
                logger.debug(f"Pump {self.pump_code}: Direct interpolation solution - Score: {score:.1f}")
            else:
                logger.debug(f"Pump {self.pump_code}: Direct solution failed NPSH gate - {npsh_gate_result['reason']}")
        
        # Method 2: Impeller Trimming (75-99% trim)  
        optimal_sizing = scaling_engine.find_optimal_sizing(self.curves, flow_m3hr, head_m)
        if optimal_sizing:
            performance = optimal_sizing['performance']
            sizing = optimal_sizing['sizing']
            
            # Validate trim percentage is within acceptable range
            trim_percent = sizing.get('trim_percent', 100)
            if 75 <= trim_percent <= 99:  # Valid trimming range
                
                # Hard Gate 2: NPSH Safety (apply to this solution)
                npsh_gate_result = self._validate_npsh_safety_gate(performance, npsha_available)
                if npsh_gate_result['passed']:
                    # Calculate score for this solution
                    score = self._calculate_solution_score(performance, sizing, flow_m3hr, head_m)
                    
                    solution = {
                        'method': 'impeller_trimming',
                        'performance': performance,
                        'sizing_info': sizing,
                        'score': score
                    }
                    possible_solutions.append(solution)
                    logger.debug(f"Pump {self.pump_code}: Impeller trimming solution - {sizing['base_diameter_mm']}mm → {sizing['required_diameter_mm']}mm ({trim_percent:.1f}% trim), Score: {score:.1f}")
                else:
                    logger.debug(f"Pump {self.pump_code}: Trimming solution failed NPSH gate - {npsh_gate_result['reason']}")
            else:
                logger.debug(f"Pump {self.pump_code}: Trimming requires {trim_percent:.1f}% (outside 75-99% range)")
        
        # v6.0: Method 3 (Speed Variation) DISABLED - Fixed-speed methodology only
        
        # Step 5: Make the final decision
        if not possible_solutions:
            logger.debug(f"Pump {self.pump_code}: No viable solutions found")
            return None
        
        # Select the solution with the highest score (True "Best Fit")
        best_solution = max(possible_solutions, key=lambda x: x['score'])
        
        logger.debug(f"Pump {self.pump_code}: Selected best solution - {best_solution['method']} with score {best_solution['score']:.1f}")
        
        # Return complete solution with all data needed for ranking
        return {
            'method': best_solution['method'],
            'flow_m3hr': best_solution['performance']['flow_m3hr'],
            'head_m': best_solution['performance']['head_m'], 
            'efficiency_pct': best_solution['performance']['efficiency_pct'],
            'power_kw': best_solution['performance']['power_kw'],
            'npshr_m': best_solution['performance'].get('npshr_m', 0),
            'impeller_diameter_mm': best_solution['performance']['impeller_diameter_mm'],
            'test_speed_rpm': best_solution['performance']['test_speed_rpm'],
            'sizing_info': best_solution['sizing_info'],
            'score': best_solution['score'],
            'curve': best_solution['performance'].get('curve', {}),
            # v6.0: Fixed-speed values
            'speed_variation_pct': 0.0,
            'vfd_required': False
        }

    def _validate_physical_capability(self, flow_m3hr: float,
                                      head_m: float) -> bool:
        """Validate that pump can physically meet the requirements within authentic performance envelope"""

        # Check against absolute maximum capabilities from all curves
        max_head = self._calculate_max_head()
        max_flow = self._calculate_max_flow()
        min_flow = min(
            min(p['flow_m3hr'] for p in curve['performance_points'])
            for curve in self.curves)

        # Hard physical limits - no extrapolation beyond authentic data
        if head_m > max_head * 1.1:  # Allow 10% margin for speed variation
            logger.debug(
                f"Required head {head_m}m exceeds pump maximum {max_head}m")
            return False

        if flow_m3hr > max_flow * 1.2:  # Allow 20% margin for impeller trimming
            logger.debug(
                f"Required flow {flow_m3hr} m³/hr exceeds pump maximum {max_flow} m³/hr"
            )
            return False

        if flow_m3hr < min_flow * 0.5:  # Don't operate at extremely low flows
            logger.debug(
                f"Required flow {flow_m3hr} m³/hr below practical minimum {min_flow * 0.5} m³/hr"
            )
            return False

        # Check if any curve can potentially meet requirements with reasonable scaling
        for curve in self.curves:
            curve_points = curve['performance_points']
            curve_heads = [p['head_m'] for p in curve_points]
            curve_flows = [p['flow_m3hr'] for p in curve_points]

            # Check if this curve's envelope could accommodate the requirement
            curve_max_head = max(curve_heads)
            curve_flow_range = (min(curve_flows), max(curve_flows))

            # Allow for reasonable speed variation (up to 20% head increase)
            if head_m <= curve_max_head * 1.2:
                # Check if flow is within reasonable range (consider impeller trimming)
                if curve_flow_range[0] * 0.7 <= flow_m3hr <= curve_flow_range[
                        1] * 1.3:
                    return True

        return False

    def _validate_speed_variation_limits(self, speed_result: Dict[str, Any],
                                         base_curve: Dict[str, Any]) -> bool:
        """Validate that speed variation results are within reasonable engineering limits"""

        # Check speed limits
        required_speed = speed_result.get('required_speed_rpm', 0)
        test_speed = base_curve.get('test_speed_rpm', 980)

        # Industry standard: don't exceed 120% or go below 70% of test speed
        if required_speed > test_speed * 1.2 or required_speed < test_speed * 0.7:
            logger.debug(
                f"Required speed {required_speed} RPM outside safe range for test speed {test_speed} RPM"
            )
            return False

        # Check head delivery isn't excessive extrapolation
        base_heads = [p['head_m'] for p in base_curve['performance_points']]
        max_base_head = max(base_heads)

        if speed_result[
                'head_m'] > max_base_head * 1.5:  # 50% head increase is maximum reasonable
            logger.debug(
                f"Speed variation produces excessive head: {speed_result['head_m']}m vs base max {max_base_head}m"
            )
            return False

        return True

    def _validate_qbp_range(self, required_flow: float) -> Dict[str, Any]:
        """v6.0 HARD GATE: Validate QBP operating range (60-130% of BEP)"""
        try:
            # Get pump's nominal BEP flow
            bep_flow = self.specifications.get('q_bep', 0)
            
            # If no BEP data in specs, estimate from curves
            if bep_flow <= 0:
                bep_point = self.get_bep_point()
                if bep_point:
                    bep_flow = bep_point.get('flow_m3hr', 0)
            
            if bep_flow > 0:
                qbp_percentage = (required_flow / bep_flow) * 100
                if qbp_percentage < 60 or qbp_percentage > 130:
                    return {
                        'passed': False,
                        'reason': f"Operating point {qbp_percentage:.1f}% outside acceptable 60-130% BEP range"
                    }
            
            # Pass if we can't determine BEP (will rely on other evaluation methods)
            return {'passed': True, 'reason': ''}
            
        except Exception as e:
            logger.debug(f"QBP validation error for {self.pump_code}: {e}")
            return {'passed': True, 'reason': ''}  # Don't exclude on validation errors

    def _validate_npsh_safety_gate(self, performance: Dict[str, Any], npsha_available: Optional[float] = None) -> Dict[str, Any]:
        """v6.0 HARD GATE: Validate NPSH safety margin (NPSHa >= 1.5 × NPSHr)"""
        if not npsha_available:
            return {'passed': True, 'reason': ''}  # Only apply when NPSHa is provided
        
        try:
            npshr = performance.get('npshr_m', 0)
            if npshr and npshr > 0:
                required_margin = npshr * 1.5
                if npsha_available < required_margin:
                    return {
                        'passed': False,
                        'reason': f"NPSH safety margin insufficient: {npsha_available:.1f}m < {required_margin:.1f}m required (1.5× {npshr:.1f}m)"
                    }
            
            return {'passed': True, 'reason': ''}
            
        except Exception as e:
            logger.debug(f"NPSH validation error for {self.pump_code}: {e}")
            return {'passed': True, 'reason': ''}  # Don't exclude on validation errors

    def _calculate_solution_score(self, performance: Dict[str, Any], 
                                 sizing_info: Dict[str, Any],
                                 target_flow: float,
                                 target_head: float) -> float:
        """Calculate comprehensive score for a pump solution (v6.0: 85-point system)
        
        Returns total score (0-85) based on:
        - BEP proximity (45 points) - THE RELIABILITY FACTOR  
        - Efficiency (35 points) - THE OPERATING COST FACTOR
        - Head margin (20 points) - THE RIGHT-SIZING FACTOR
        - Impeller trim penalties (negative points)
        
        v6.0 Changes: NPSH removed from scoring, VFD penalties removed, rebalanced weights
        """
        score = 0.0
        
        # 1. BEP Proximity Score (45 points max) - v6.0: Increased from 35 to 45
        bep_analysis = self.calculate_bep_distance(target_flow, target_head)
        if bep_analysis.get('bep_available'):
            flow_ratio = bep_analysis.get('flow_ratio', 1.0)
            if 0.95 <= flow_ratio <= 1.05:  # Sweet spot
                bep_score = 45
            elif 0.90 <= flow_ratio < 0.95 or 1.05 < flow_ratio <= 1.10:
                bep_score = 40
            elif 0.80 <= flow_ratio < 0.90 or 1.10 < flow_ratio <= 1.20:
                bep_score = 30
            elif 0.70 <= flow_ratio < 0.80 or 1.20 < flow_ratio <= 1.30:
                bep_score = 20
            else:  # 0.60-0.70 or 1.30-1.40 (gate allows up to 60-130%)
                bep_score = 10
        else:
            bep_score = 22.5  # Default if no BEP data (50% of max)
        
        score += bep_score
        
        # 2. Efficiency Score (35 points max) - v6.0: Increased from 30 to 35
        efficiency = performance.get('efficiency_pct', 0)
        if efficiency >= 85:
            eff_score = 35
        elif efficiency >= 75:
            eff_score = 30 + (efficiency - 75) * 0.5
        elif efficiency >= 65:
            eff_score = 25 + (efficiency - 65) * 0.5
        elif efficiency >= 45:
            eff_score = 10 + (efficiency - 45) * 0.75
        else:  # 40-45% (gate excludes below 40%)
            eff_score = max(0, (efficiency - 40) * 2)
        
        score += eff_score
        
        # 3. Head Margin Score (20 points max) - v6.0: Increased from 15 to 20
        head_margin = performance.get('head_m', 0) - target_head
        head_margin_pct = (head_margin / target_head) * 100 if target_head > 0 else 0
        
        if head_margin_pct <= 5:  # Perfect sizing
            margin_score = 20
        elif 5 < head_margin_pct <= 10:  # Good sizing
            margin_score = 20 - (head_margin_pct - 5) * 2
        elif 10 < head_margin_pct <= 15:  # Acceptable sizing  
            margin_score = 10 - (head_margin_pct - 10) * 1
        else:  # 15-20% (higher margins penalized more heavily)
            margin_score = 5 - (head_margin_pct - 15) * 2
            margin_score = max(0, margin_score)  # Floor at 0
        
        score += margin_score
        
        # v6.0: NPSH Score REMOVED - inconsistent data makes fair comparison impossible
        # NPSH safety is now handled by hard gate only
        
        # 4. Apply Impeller Trim Penalty (negative points only)
        trim_percent = sizing_info.get('trim_percent', 100)
        if trim_percent >= 95:  # Minimal trim
            trim_penalty = 0
        elif trim_percent >= 90:  # Light trim
            trim_penalty = -2
        elif trim_percent >= 85:  # Moderate trim
            trim_penalty = -5
        elif trim_percent >= 80:  # Heavy trim
            trim_penalty = -8
        else:  # 75-80% trim (maximum allowed)
            trim_penalty = -12
            
        score += trim_penalty  # Add negative penalty
        
        # v6.0: VFD/Speed variation penalties REMOVED - fixed-speed only
        
        # Ensure score doesn't go negative
        return max(0, score)

    # v6.0: get_performance_at_duty() REMOVED - replaced by find_best_solution_for_duty()
    # The old method is part of the "First Fit vs Best Fit" conflict that has been resolved

    def _get_performance_interpolated(
            self, flow_m3hr: float, head_m: float) -> Optional[Dict[str, Any]]:
        """Legacy interpolation method for when sizing is not possible"""
        best_curve = self.get_best_curve_for_duty(flow_m3hr, head_m)

        if not best_curve:
            return None

        points = best_curve['performance_points']
        flows = [p['flow_m3hr'] for p in points]
        heads = [p['head_m'] for p in points]
        effs = [p['efficiency_pct'] for p in points]

        try:
            head_interp = interpolate.interp1d(flows,
                                               heads,
                                               kind='linear',
                                               bounds_error=False)
            eff_interp = interpolate.interp1d(flows,
                                              effs,
                                              kind='linear',
                                              bounds_error=False)

            predicted_head = float(head_interp(flow_m3hr))
            efficiency = float(eff_interp(flow_m3hr))

            # Calculate power using exact VBA formula with pump's actual head
            if efficiency > 0:
                efficiency_decimal = efficiency / 100.0
                sg = 1.0  # Specific gravity for water
                power_kw = (flow_m3hr * predicted_head * sg *
                            9.81) / (efficiency_decimal * 3600)
                power_kw = round(power_kw, 3)
            else:
                power_kw = 0.0

            # Calculate NPSH if available
            npshr_m = None
            npshs = [
                p['npshr_m'] for p in points
                if p['npshr_m'] and p['npshr_m'] > 0
            ]
            if npshs and len(npshs) == len(flows):
                npsh_interp = interpolate.interp1d(flows,
                                                   npshs,
                                                   kind='linear',
                                                   bounds_error=False)
                npshr_m = float(npsh_interp(flow_m3hr))

            return {
                'curve': best_curve,
                'flow_m3hr':
                flow_m3hr,  # CRITICAL: Always maintain required flow rate
                'head_m': predicted_head,
                'efficiency_pct': efficiency,
                'power_kw': power_kw,
                'npshr_m': npshr_m,
                'impeller_diameter_mm': best_curve['impeller_diameter_mm'],
                'test_speed_rpm': best_curve['test_speed_rpm']
            }

        except Exception as e:
            logger.debug(
                f"Performance calculation error for {self.pump_code}: {e}")
            return None

    def get_any_performance_point(
            self, target_flow: float,
            target_head: float) -> Optional[Dict[str, Any]]:
        """Force performance calculation at any operating point for direct search analysis"""
        if not self.curves:
            return None

        # Try to find the best available curve, even if outside normal operating range
        best_curve = None
        best_match_score = -1

        for curve in self.curves:
            points = curve['performance_points']
            if not points:
                continue

            # Calculate how well this curve might work for the target conditions
            flows = [p['flow_m3hr'] for p in points]
            heads = [p['head_m'] for p in points]

            # Check if we can extrapolate to target flow
            min_flow, max_flow = min(flows), max(flows)
            flow_coverage = 1.0 if min_flow <= target_flow <= max_flow else 0.5

            # Prefer curves with higher efficiency potential
            avg_efficiency = sum(p['efficiency_pct']
                                 for p in points) / len(points)

            match_score = flow_coverage * avg_efficiency

            if match_score > best_match_score:
                best_match_score = match_score
                best_curve = curve

        if not best_curve:
            # Return the first available curve as fallback
            best_curve = self.curves[0]

        points = best_curve['performance_points']
        flows = [p['flow_m3hr'] for p in points]
        heads = [p['head_m'] for p in points]
        effs = [p['efficiency_pct'] for p in points]

        try:
            # Use linear interpolation with clamping (no extrapolation beyond bounds)
            head_interp = interpolate.interp1d(flows,
                                               heads,
                                               kind='linear',
                                               bounds_error=False,
                                               fill_value=0)
            eff_interp = interpolate.interp1d(flows,
                                              effs,
                                              kind='linear',
                                              bounds_error=False,
                                              fill_value=0)

            predicted_head = float(head_interp(target_flow))
            efficiency = float(eff_interp(target_flow))

            # Ensure reasonable bounds for extrapolated values
            efficiency = max(0, min(100,
                                    efficiency))  # Clamp efficiency to 0-100%
            predicted_head = max(0, predicted_head)  # Ensure positive head

            # Calculate power
            if efficiency > 0:
                efficiency_decimal = efficiency / 100.0
                sg = 1.0  # Specific gravity for water
                power_kw = (target_flow * predicted_head * sg *
                            9.81) / (efficiency_decimal * 3600)
                power_kw = round(power_kw, 3)
            else:
                power_kw = 0.0

            # Calculate NPSH if available
            npshr_m = None
            npshs = [
                p['npshr_m'] for p in points
                if p['npshr_m'] and p['npshr_m'] > 0
            ]
            if npshs and len(npshs) == len(flows):
                try:
                    npsh_interp = interpolate.interp1d(
                        flows,
                        npshs,
                        kind='linear',
                        bounds_error=False,
                        fill_value=0)
                    npshr_m = max(0, float(
                        npsh_interp(target_flow)))  # Ensure positive NPSH
                except:
                    npshr_m = None

            return {
                'curve': best_curve,
                'flow_m3hr': target_flow,
                'head_m': predicted_head,
                'efficiency_pct': efficiency,
                'power_kw': power_kw,
                'npshr_m': npshr_m,
                'impeller_diameter_mm': best_curve['impeller_diameter_mm'],
                'test_speed_rpm': best_curve['test_speed_rpm'],
                'extrapolated':
                True  # Flag to indicate this is extrapolated data
            }

        except Exception as e:
            logger.warning(
                f"Forced performance calculation failed for {self.pump_code}: {e}"
            )
            # Return minimal data to allow analysis to continue
            return {
                'curve': best_curve,
                'flow_m3hr': target_flow,
                'head_m': 0,
                'efficiency_pct': 0,
                'power_kw': 0,
                'npshr_m': None,
                'impeller_diameter_mm': best_curve['impeller_diameter_mm'],
                'test_speed_rpm': best_curve['test_speed_rpm'],
                'calculation_error': True
            }

    def to_dict(self) -> Dict[str, Any]:
        """Converts the CatalogPump object to a JSON-serializable dictionary."""
        return {
            'pump_code': self.pump_code,
            'pump_id': self.pump_id,
            'manufacturer': self.manufacturer,
            'pump_type': self.pump_type,
            'model_series': self.model_series,
            'specifications': self.specifications,
            'curves': self.curves,
            'curve_count': self.curve_count,
            'total_points': self.total_points,
            'npsh_curves': self.npsh_curves,
            'power_curves': self.power_curves,
            'description': self.description,
            'max_flow_m3hr': self.max_flow_m3hr,
            'max_head_m': self.max_head_m,
            'max_power_kw': self.max_power_kw,
            'min_efficiency': self.min_efficiency,
            'max_efficiency': self.max_efficiency,
            'connection_size': self.connection_size,
            'materials': self.materials,
        }


class CatalogEngine:
    """APE Catalog-based pump selection engine"""

    def __init__(self):
        # Use repository instead of direct file loading
        self.repository = get_pump_repository()
        self.pumps = []
        self.metadata = {}
        self._load_from_repository()

    def _load_from_repository(self):
        """Load data from centralized repository"""
        try:
            # Get data from repository
            catalog_data = self.repository.get_catalog_data()
            self.metadata = catalog_data.get('metadata', {})
            pump_models = catalog_data.get('pump_models', [])

            self.pumps = [CatalogPump(pump_data) for pump_data in pump_models]

            logger.info(
                f"Catalog Engine: Loaded {len(self.pumps)} pump models from repository"
            )
            logger.info(
                f"Catalog Engine: Total curves: {self.metadata.get('total_curves', 0)}"
            )
            logger.info(
                f"Catalog Engine: NPSH curves: {self.metadata.get('npsh_curves', 0)} ({self.metadata.get('npsh_curves', 0)/self.metadata.get('total_curves', 1)*100:.1f}%)"
            )

        except Exception as e:
            logger.error(f"Catalog Engine: Error loading from repository: {e}")
            self.pumps = []
            self.metadata = {}

    def load_catalog(self):
        """Reload catalog from repository (for compatibility)"""
        # Force repository to reload data
        self.repository.reload_catalog()
        self._load_from_repository()

    def select_pumps(self,
                     flow_m3hr: float,
                     head_m: float,
                     max_results: int = 10,
                     pump_type: str | None = None,
                     return_exclusions: bool = False) -> Dict[str, Any] | List[Dict[str, Any]]:
        """
        Select pumps for given duty point with physical feasibility gate.
        
        Args:
            flow_m3hr: Required flow rate in m³/hr
            head_m: Required head in meters
            max_results: Maximum number of suitable pumps to return
            pump_type: Filter by pump type (optional)
            return_exclusions: If True, also return excluded pumps with reasons
            
        Returns:
            List of pump evaluations (suitable pumps, and optionally excluded pumps)
        """
        from .data_models import PumpEvaluation, ExclusionReason
        
        suitable_pumps = []
        excluded_pumps = []
        near_miss_pumps = []  # Track pumps that just missed criteria

        # Debug logging for pump type filtering
        logger.info(
            f"Catalog Engine: QBP-centric selection for flow={flow_m3hr}, head={head_m}, type='{pump_type}'"
        )
        total_pumps = len(self.pumps)
        excluded_count = 0
        feasible_count = 0

        # PHASE 3 IMPLEMENTATION: BEP-centric pre-sorting
        # Sort pumps by proximity to BEP before evaluation
        pumps_to_evaluate = list(self.pumps)  # Create a copy of the pump list
        
        # Pre-sort by BEP proximity (most likely candidates first)
        def bep_proximity_key(pump):
            """Calculate BEP proximity for sorting"""
            try:
                # Get nominal BEP flow from specifications
                bep_flow = pump.specifications.get('q_bep', 0)
                if bep_flow <= 0:
                    # If no BEP data, estimate from curves
                    if pump.curves:
                        # Use middle of flow range as estimate
                        all_flows = []
                        for curve in pump.curves:
                            flows = [p['flow_m3hr'] for p in curve.get('performance_points', [])]
                            if flows:
                                all_flows.extend(flows)
                        if all_flows:
                            bep_flow = (min(all_flows) + max(all_flows)) / 2
                
                if bep_flow > 0:
                    # Return absolute difference between pump BEP and required flow
                    return abs(bep_flow - flow_m3hr)
                else:
                    # No BEP data - put at end of list
                    return float('inf')
            except Exception:
                # Error calculating BEP - put at end of list
                return float('inf')
        
        # Sort pumps by BEP proximity (closest BEP to duty point first)
        pumps_to_evaluate.sort(key=bep_proximity_key)
        
        logger.info(f"Catalog Engine: Pre-sorted {len(pumps_to_evaluate)} pumps by BEP proximity")
        
        # Now evaluate pumps in BEP-optimized order
        for pump in pumps_to_evaluate:
            # Create evaluation object for this pump
            evaluation = PumpEvaluation(pump_code=pump.pump_code)
            
            # Filter by pump type if specified
            if pump_type and pump_type.upper() not in ('GENERAL', 'GENERAL',
                                                       'ALL TYPES'):
                # Normalize both pump types for comparison
                selected_type = pump_type.upper().strip()
                pump_db_type = pump.pump_type.upper().strip()

                # Direct comparison with database pump types
                if selected_type != pump_db_type:
                    logger.debug(
                        f"Skipping pump {pump.pump_code} - type '{pump_db_type}' doesn't match selected '{selected_type}'"
                    )
                    continue  # Skip pumps that don't match the selected type

            # v6.0 UNIFIED EVALUATION: Single "Best Fit" function call eliminates "First Fit vs Best Fit" conflict
            best_solution = pump.find_best_solution_for_duty(flow_m3hr, head_m)
            
            if best_solution is None:
                # Pump failed hard gates or has no viable solutions
                evaluation.add_exclusion(ExclusionReason.ENVELOPE_EXCEEDED)
                excluded_pumps.append(evaluation)
                excluded_count += 1
                logger.debug(f"Pump {pump.pump_code} excluded: Failed unified evaluation (hard gates or no viable solutions)")
                continue
            
            # Extract performance data and score from the unified best solution
            performance = {
                'flow_m3hr': best_solution['flow_m3hr'],
                'head_m': best_solution['head_m'], 
                'efficiency_pct': best_solution['efficiency_pct'],
                'power_kw': best_solution['power_kw'],
                'npshr_m': best_solution['npshr_m'],
                'impeller_diameter_mm': best_solution['impeller_diameter_mm'],
                'test_speed_rpm': best_solution['test_speed_rpm'],
                'curve': best_solution['curve'],
                'sizing_info': best_solution['sizing_info']
            }
            
            # Score is already calculated by the unified function
            score = best_solution['score']
            
            # v6.0: Physical feasibility and scoring handled by unified function
            # Pump passed all hard gates and has optimal solution with calculated score
            feasible_count += 1
            evaluation.feasible = True
            evaluation.performance_data = performance

            # v6.0: Performance values are already optimal from unified function
            delivered_head = performance['head_m']
            efficiency = performance['efficiency_pct']
            
            # Calculate head margin for display
            head_margin = delivered_head - head_m
            head_margin_pct = (head_margin / head_m) * 100
            
            # Calculate BEP analysis for this pump (for display purposes)
            bep_analysis = pump.calculate_bep_distance(flow_m3hr, head_m)
            
            # Store sizing validation flag
            sizing_validated = performance.get('sizing_info', {}).get('meets_requirements', True)
            
            # Create result using unified function's score and data
            result = {
                'pump': pump,
                'performance': performance,
                'suitability_score': score,
                'head_margin_m': head_margin,
                'head_margin_pct': head_margin_pct, 
                'efficiency_at_duty': efficiency,
                'meets_requirements': True,  # All pumps in results meet requirements via hard gates
                'sizing_validated': sizing_validated,
                'bep_analysis': bep_analysis,
                'evaluation': evaluation
            }
            suitable_pumps.append(result)

        # v6.0 UNIFIED EVALUATION COMPLETE: All pumps processed with unified "Best Fit" methodology

        # Sort by suitability score (descending)
        # v6.0 RANKING: Multi-criteria ranking with power-based tie-breaking
        suitable_pumps.sort(key=lambda x: (
            -x['suitability_score'],                              # Primary: highest score
            x['performance'].get('power_kw', float('inf')),       # Secondary: lowest power (tie-breaker)
            abs(x.get('bep_analysis', {}).get('flow_ratio', 1.0) * 100 - 100)  # Tertiary: closest to 100% BEP
        ))

        # Log filtering results with transparency
        logger.info(
            f"Catalog Engine: Evaluated {total_pumps} pumps - {feasible_count} feasible, {excluded_count} excluded"
        )
        logger.info(
            f"Catalog Engine: Found {len(suitable_pumps)} suitable pumps meeting all criteria"
        )
        if pump_type and pump_type.upper() != 'GENERAL':
            logger.info(
                f"Catalog Engine: Type filtering applied for '{pump_type}'"
            )

        # Log top results for debugging
        for i, pump in enumerate(suitable_pumps[:5]):
            logger.info(
                f"  #{i+1}: {pump['pump'].pump_code} ({pump['pump'].pump_type}) - Score: {pump['suitability_score']:.1f}"
            )

        # Format results for web app compatibility
        formatted_results = []
        for result in suitable_pumps[:max_results]:
            pump_obj = result['pump']
            performance = result['performance']

            formatted_result = {
                # Direct access fields for compatibility
                'pump_code': pump_obj.pump_code,
                'pump_type': pump_obj.pump_type,
                'manufacturer': pump_obj.manufacturer,
                'selection_score': result['suitability_score'],
                'overall_score':
                result['suitability_score'],  # Alias for compatibility
                'efficiency_at_duty': result['efficiency_at_duty'],
                'head_margin_m': result['head_margin_m'],
                'head_margin_pct': result['head_margin_pct'],
                'meets_requirements': result['meets_requirements'],

                # Original nested objects for detailed processing
                'pump': pump_obj,
                'performance': performance,

                # Additional analysis data
                'suitability_score': result['suitability_score'],
                'bep_analysis': result['bep_analysis'],
                'bep_score': result['bep_analysis'].get('bep_score', 0),
                'efficiency_score': result['efficiency_at_duty'],  # Use actual efficiency
                'margin_score': result['head_margin_pct'],  # Use head margin percentage
                'npsh_score': 0,  # v6.0: NPSH removed from scoring
                'sizing_validated': result['sizing_validated'],
                
                # Scoring details for transparency
                'scoring_details': {
                    'qbp_proximity': {
                        'score': result.get('evaluation', {}).score_components.get('qbp_proximity', 0) if result.get('evaluation') else result.get('bep_score', 0),
                        'description': f"Operating at {result.get('evaluation', {}).calculation_metadata.get('flow_ratio', 1.0) * 100:.0f}% of Best Efficiency Point flow" if result.get('evaluation') else 'BEP Proximity',
                        'formula': '40 × max(0, 1 - ((flow_ratio - 1) / 0.5)²)'
                    },
                    'efficiency': {
                        'score': result.get('evaluation', {}).score_components.get('efficiency', 0) if result.get('evaluation') else result.get('efficiency_score', 0),
                        'description': f"Efficiency at duty point: {result['efficiency_at_duty']:.1f}%",
                        'formula': '(efficiency/100)² × 30'
                    },
                    'head_margin': {
                        'score': result.get('evaluation', {}).score_components.get('head_margin', 0) if result.get('evaluation') else result.get('margin_score', 0),
                        'description': f"Head margin: {result['head_margin_pct']:.1f}%",
                        'formula': 'Graduated scoring based on margin percentage'
                    },
                    'npsh': {
                        'score': result.get('evaluation', {}).score_components.get('npsh', 0) if result.get('evaluation') else result.get('npsh_score', 0),
                        'description': f"NPSHr: {performance.get('npshr_m', 'N/A'):.1f}m" if performance.get('npshr_m') else "No NPSH data",
                        'formula': '15 × max(0, (8 - NPSHr) / 6)' if performance.get('npshr_m') else 'N/A'
                    },
                    'speed_penalty': {
                        'score': result.get('evaluation', {}).score_components.get('speed_penalty', 0) if result.get('evaluation') else 0,
                        'description': f"Speed variation: {performance.get('sizing_info', {}).get('speed_variation_pct', 0):.1f}%" if performance.get('sizing_info', {}).get('vfd_required') else "No speed variation",
                        'formula': '1.5 × speed_change_% (max -15)'
                    },
                    'trim_penalty': {
                        'score': result.get('evaluation', {}).score_components.get('trim_penalty', 0) if result.get('evaluation') else 0,
                        'description': f"Impeller trim: {100 - performance.get('sizing_info', {}).get('trim_percent', 100):.1f}%" if performance.get('sizing_info', {}).get('trim_percent', 100) < 100 else "No trimming",
                        'formula': '0.5 × trim_%'
                    }
                }
            }
            formatted_results.append(formatted_result)

        # Log exclusion summary for transparency
        exclusion_summary = {}
        if excluded_pumps:
            for eval in excluded_pumps:
                for reason in eval.exclusion_reasons:
                    # Convert enum name to lowercase with underscores for template compatibility
                    reason_key = reason.name.lower()
                    exclusion_summary[reason_key] = exclusion_summary.get(reason_key, 0) + 1
            
            logger.info("Exclusion Summary:")
            for reason_key, count in sorted(exclusion_summary.items(), key=lambda x: x[1], reverse=True):
                # Convert back to enum for logging
                reason_enum = ExclusionReason[reason_key.upper()]
                logger.info(f"  {reason_enum.value}: {count} pumps")

        # Sort near-miss pumps by how close they came to meeting requirements
        # Lower head deficit percentage = closer to meeting requirements
        near_miss_pumps.sort(key=lambda x: x['head_deficit_pct'])
        
        # Enhanced near-miss summary with engineering guidance
        if near_miss_pumps:
            logger.info(f"Found {len(near_miss_pumps)} near-miss pumps that just missed selection criteria")
            for i, near_miss in enumerate(near_miss_pumps[:3]):  # Log top 3 near-miss pumps
                logger.info(f"  Near-miss #{i+1}: {near_miss['pump_code']} - {', '.join(near_miss['near_miss_reasons'])}")
                if near_miss.get('engineering_guidance'):
                    for guidance in near_miss['engineering_guidance'][:2]:  # Show top 2 suggestions
                        logger.info(f"    → {guidance}")
        
        # Return exclusion data if requested
        if return_exclusions:
            return {
                'suitable_pumps': formatted_results,
                'excluded_pumps': excluded_pumps,
                'near_miss_pumps': near_miss_pumps[:5],  # Return top 5 near-miss pumps
                'exclusion_summary': exclusion_summary,
                'total_evaluated': total_pumps,
                'feasible_count': feasible_count,
                'excluded_count': excluded_count
            }
        
        return formatted_results

    def _assess_right_of_bep_potential(self, pump: 'CatalogPump', flow_m3hr: float) -> Dict[str, Any]:
        """Assess potential for right-of-BEP operation (105-115% sweet spot)"""
        try:
            bep_analysis = pump.calculate_bep_distance(flow_m3hr, flow_m3hr)  # Dummy head for BEP calc
            if not bep_analysis.get('bep_available'):
                return {'potential': 'unknown', 'guidance': 'BEP data not available'}
            
            bep_flow = bep_analysis.get('bep_flow', 0)
            if bep_flow <= 0:
                return {'potential': 'unknown', 'guidance': 'Invalid BEP flow'}
            
            flow_ratio = flow_m3hr / bep_flow
            
            if 1.05 <= flow_ratio <= 1.15:
                return {
                    'potential': 'optimal',
                    'flow_ratio': flow_ratio,
                    'guidance': f'Operating in ideal right-of-BEP zone ({flow_ratio:.2f}x BEP)'
                }
            elif flow_ratio < 1.05:
                bep_shortfall = (1.05 - flow_ratio) * bep_flow
                return {
                    'potential': 'increase_flow',
                    'flow_ratio': flow_ratio,
                    'guidance': f'Increase flow by {bep_shortfall:.1f} m³/hr to reach right-of-BEP zone'
                }
            else:
                return {
                    'potential': 'acceptable',
                    'flow_ratio': flow_ratio,
                    'guidance': f'Operating right of BEP ({flow_ratio:.2f}x) - acceptable for most applications'
                }
        except Exception as e:
            logger.debug(f"Error assessing right-of-BEP potential: {e}")
            return {'potential': 'error', 'guidance': 'Unable to assess BEP positioning'}

    def _validate_physical_feasibility(self, pump: 'CatalogPump', 
                                     performance: Dict[str, Any],
                                     required_head: float,
                                     evaluation: 'PumpEvaluation') -> bool:
        """
        Validate physical feasibility BEFORE scoring.
        Returns True if pump is feasible, False otherwise.
        Updates evaluation with exclusion reasons.
        """
        from .data_models import ExclusionReason
        
        # Extract sizing information
        sizing_info = performance.get('sizing_info', {})
        
        # 1. Check impeller trim limits (80-100% typical)
        trim_percent = sizing_info.get('trim_percent', 100)
        if trim_percent < 80:
            evaluation.add_exclusion(ExclusionReason.UNDERTRIM)
            logger.debug(f"Pump {pump.pump_code} excluded: undertrim at {trim_percent:.1f}%")
        elif trim_percent > 100:
            evaluation.add_exclusion(ExclusionReason.OVERTRIM)
            logger.debug(f"Pump {pump.pump_code} excluded: overtrim at {trim_percent:.1f}%")
        
        # 2. Check speed limits (750-3600 RPM typical)
        base_speed = performance.get('test_speed_rpm', 1480)  # Default to 1480 RPM
        speed_rpm = sizing_info.get('operating_speed_rpm', base_speed)
        
        if sizing_info.get('vfd_required', False):
            speed_variation_pct = sizing_info.get('speed_variation_pct', 0)
            actual_speed = base_speed * (1 + speed_variation_pct / 100)
            
            if actual_speed < 750:
                evaluation.add_exclusion(ExclusionReason.UNDERSPEED)
                logger.debug(f"Pump {pump.pump_code} excluded: underspeed at {actual_speed:.0f} RPM")
            elif actual_speed > 3600:
                evaluation.add_exclusion(ExclusionReason.OVERSPEED)
                logger.debug(f"Pump {pump.pump_code} excluded: overspeed at {actual_speed:.0f} RPM")
        
        # 3. Check head achievement (must meet required head)
        delivered_head = performance.get('head_m', 0)
        if delivered_head < required_head * 0.98:  # Allow 2% tolerance
            evaluation.add_exclusion(ExclusionReason.HEAD_NOT_MET)
            logger.debug(f"Pump {pump.pump_code} excluded: head {delivered_head:.1f}m < required {required_head:.1f}m")
        
        # 4. Check efficiency threshold
        efficiency = performance.get('efficiency_pct', 0)
        if efficiency < 40:
            evaluation.add_exclusion(ExclusionReason.EFFICIENCY_TOO_LOW)
            logger.debug(f"Pump {pump.pump_code} excluded: efficiency {efficiency:.1f}% < 40%")
        
        # 5. Check for valid performance data
        if efficiency == 0 or delivered_head == 0:
            evaluation.add_exclusion(ExclusionReason.NO_PERFORMANCE_DATA)
            logger.debug(f"Pump {pump.pump_code} excluded: invalid performance data")
        
        # v6.0: Combined VFD/trim limits check REMOVED - fixed-speed only
        
        # 7. Check NPSH if available
        npsha = performance.get('npsha_m')
        npshr = performance.get('npshr_m')
        if npsha is not None and npshr is not None and npsha > 0 and npshr > 0:
            if npshr >= npsha:
                evaluation.add_exclusion(ExclusionReason.NPSH_INSUFFICIENT)
                logger.debug(f"Pump {pump.pump_code} excluded: NPSHr {npshr:.1f}m >= NPSHa {npsha:.1f}m")
        
        # Return feasibility status
        return len(evaluation.exclusion_reasons) == 0

    def _find_best_operating_point(self, performance: Dict[str, Any],
                                   target_flow: float,
                                   target_head: float) -> tuple:
        """Find the best operating point within tolerance for a pump"""

        delivered_head = performance['head_m']
        efficiency = performance['efficiency_pct']
        current_flow = performance['flow_m3hr']

        # If pump already meets requirements, return current point
        if delivered_head >= target_head:
            return delivered_head, efficiency, current_flow

        # Check if pump has capability at other operating points
        curve = performance.get('curve', {})
        points = curve.get('performance_points', [])

        if not points:
            return delivered_head, efficiency, current_flow

        max_head_available = max(
            [p.get('head_m', 0) for p in points if p.get('head_m')], default=0)

        # If pump lacks physical capability, return current point
        if max_head_available < target_head:
            return delivered_head, efficiency, current_flow

        # Find operating points that meet head requirement
        suitable_points = []
        for p in points:
            if p.get('head_m', 0) >= target_head and p.get('flow_m3hr', 0) > 0:
                suitable_points.append({
                    'flow':
                    p['flow_m3hr'],
                    'head':
                    p['head_m'],
                    'efficiency':
                    p['efficiency_pct'],
                    'flow_diff':
                    abs(p['flow_m3hr'] - target_flow) / target_flow * 100
                })

        if not suitable_points:
            return delivered_head, efficiency, current_flow

        # Apply flow tolerance (10%)
        within_tolerance = [
            p for p in suitable_points if p['flow_diff'] <= 10.0
        ]

        if not within_tolerance:
            return delivered_head, efficiency, current_flow

        # Select best point within tolerance (closest to target flow, highest efficiency)
        best_point = min(within_tolerance,
                         key=lambda p: (p['flow_diff'], -p['efficiency']))

        return best_point['head'], best_point['efficiency'], best_point['flow']

    def get_pump_by_code(self, pump_code: str) -> Optional[CatalogPump]:
        """Get specific pump by code"""
        for pump in self.pumps:
            if pump.pump_code == pump_code:
                return pump
        return None

    def get_catalog_stats(self) -> Dict[str, Any]:
        """Get catalog statistics"""
        return {
            'total_models':
            len(self.pumps),
            'total_curves':
            self.metadata.get('total_curves', 0),
            'total_points':
            self.metadata.get('total_points', 0),
            'npsh_curves':
            self.metadata.get('npsh_curves', 0),
            'npsh_coverage_pct':
            self.metadata.get('npsh_curves', 0) /
            self.metadata.get('total_curves', 1) * 100,
            'power_curves':
            self.metadata.get('power_curves', 0)
        }


# Global catalog engine instance
catalog_engine = None


def get_catalog_engine() -> CatalogEngine:
    """Get global catalog engine instance"""
    global catalog_engine
    if catalog_engine is None:
        catalog_engine = CatalogEngine()
    return catalog_engine


def convert_catalog_pump_to_legacy_format(
        catalog_pump: CatalogPump, performance: Dict[str, Any]) -> object:
    """Convert catalog pump to legacy format for PDF compatibility with authentic data preservation"""
    curve = performance['curve']

    # Create a legacy-compatible object that preserves authentic data
    class LegacyPumpData:

        def __init__(self, catalog_pump, performance_data):
            self.pump_code = catalog_pump.pump_code

            # Use actual calculated impeller diameter from scaling engine
            # Check if sizing info is available (from new requirement-driven approach)
            if 'sizing_info' in performance_data and performance_data[
                    'sizing_info']:
                sizing_info = performance_data['sizing_info']
                self.authentic_impeller_mm = sizing_info.get(
                    'required_diameter_mm', curve['impeller_diameter_mm'])
                self.trim_percent = sizing_info.get('trim_percent', 100.0)
                self.base_impeller_mm = sizing_info.get(
                    'base_diameter_mm', curve['impeller_diameter_mm'])
                self.trimming_required = sizing_info.get(
                    'trimming_required', False)
            else:
                # Fallback to curve diameter if no sizing info
                self.authentic_impeller_mm = curve['impeller_diameter_mm']
                self.trim_percent = 100.0
                self.base_impeller_mm = curve['impeller_diameter_mm']
                self.trimming_required = False

            # Use actual calculated performance values
            self.authentic_power_kw = performance_data.get('power_kw', 31.1)
            self.authentic_efficiency_pct = performance_data.get(
                'efficiency_pct', 82)
            self.authentic_npshr_m = performance_data.get('npshr_m', 2.78)
            self.authentic_head_m = performance_data.get('head_m', 0)
            self.authentic_flow_m3hr = performance_data.get('flow_m3hr', 0)

            # Build legacy format pump_info with authentic values
            self.pump_info = {
                'pPumpCode':
                catalog_pump.pump_code,
                'pSuppName':
                catalog_pump.manufacturer,
                'pModel':
                catalog_pump.pump_code,
                'pSeries':
                catalog_pump.model_series,
                'pFilter1':
                catalog_pump.pump_type,
                'pPumpTestSpeed':
                str(curve['test_speed_rpm']),
                'pMaxQ':
                str(catalog_pump.specifications.get('max_flow_m3hr', 0)),
                'pMaxH':
                str(catalog_pump.specifications.get('max_head_m', 0)),
                'pMinImpD':
                str(catalog_pump.specifications.get('min_impeller_mm', 0)),
                'pMaxImpD':
                str(catalog_pump.specifications.get('max_impeller_mm', 0)),
                'manufacturer':
                catalog_pump.manufacturer,
                'rated_speed_rpm':
                curve['test_speed_rpm'],

                # Use calculated impeller diameter (not base curve diameter)
                'impeller_diameter_mm':
                self.authentic_impeller_mm,
                'power_kw':
                self.authentic_power_kw,

                # Convert performance points to legacy format
                'pM_FLOW':
                ';'.join(
                    str(p['flow_m3hr']) for p in curve['performance_points']),
                'pM_HEAD':
                ';'.join(
                    str(p['head_m']) for p in curve['performance_points']),
                'pM_EFF':
                ';'.join(
                    str(p['efficiency_pct'])
                    for p in curve['performance_points']),
                'pM_NP':
                ';'.join(
                    str(p['npshr_m']
                        ) if p['npshr_m'] and p['npshr_m'] > 0 else '0'
                    for p in curve['performance_points']),
                'pM_IMP':
                str(self.authentic_impeller_mm)  # Use calculated diameter
            }

    return LegacyPumpData(catalog_pump, performance)
