"""
Pump Selection Methodology v5.0
================================
Enhanced pump selection system with improved scoring, transparency, and real-world validation.

Key Improvements in v5:
1. Refined BEP proximity scoring with better curve fitting
2. Enhanced efficiency calculations with real curve data
3. Improved head margin scoring to prevent oversizing
4. Better handling of speed variation and trimming
5. Transparent scoring breakdown for all evaluations
6. Support for near-miss analysis and recommendations
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from scipy import interpolate

logger = logging.getLogger(__name__)


class SelectionMethodology:
    """V5 Pump Selection Methodology - Best Fit with Enhanced Scoring"""
    
    # Scoring weights (total 100 points)
    BEP_WEIGHT = 40  # Reliability factor
    EFFICIENCY_WEIGHT = 30  # Operating cost
    HEAD_MARGIN_WEIGHT = 15  # Right-sizing
    NPSH_WEIGHT = 15  # Cavitation risk
    
    # Penalty factors
    SPEED_PENALTY_MAX = 15  # Maximum penalty for speed variation
    TRIM_PENALTY_MAX = 10  # Maximum penalty for impeller trimming
    
    # Engineering limits
    MIN_EFFICIENCY = 40  # Minimum acceptable efficiency
    MAX_HEAD_MARGIN = 20  # Maximum acceptable head oversizing (%)
    MIN_TRIM = 75  # Minimum impeller trim (%)
    MAX_TRIM = 100  # Maximum impeller trim (%)
    MIN_SPEED = 600  # Minimum motor speed (RPM)
    MAX_SPEED = 3600  # Maximum motor speed (RPM)
    
    # Extrapolation limits
    SAFE_EXTRAPOLATION = 10  # Safe extrapolation (%)
    MAX_EXTRAPOLATION = 15  # Maximum extrapolation (%)
    
    def __init__(self):
        self.scoring_history = []
        self.evaluation_count = 0
        
    def evaluate_pump(self, pump_data: Dict, flow_m3hr: float, head_m: float, 
                     npsha_m: Optional[float] = None) -> Dict[str, Any]:
        """
        Evaluate a single pump against requirements using v5 methodology.
        
        Returns comprehensive evaluation including:
        - Feasibility status
        - Performance at duty point
        - Score breakdown
        - Exclusion reasons (if any)
        """
        self.evaluation_count += 1
        
        evaluation = {
            'pump_code': pump_data.get('pump_code', 'Unknown'),
            'feasible': False,
            'score': 0,
            'score_breakdown': {},
            'performance': None,
            'exclusion_reasons': [],
            'near_miss_info': None
        }
        
        # Step 1: Check if pump has valid curves
        curves = pump_data.get('performance_curves', [])
        if not curves:
            evaluation['exclusion_reasons'].append('No performance curves available')
            return evaluation
            
        # Step 2: Find best solution across all curves and methods
        best_solution = self._find_best_solution(curves, flow_m3hr, head_m)
        
        if not best_solution:
            evaluation['exclusion_reasons'].append('Cannot meet duty requirements')
            return evaluation
            
        # Step 3: Calculate performance at duty point
        performance = best_solution['performance']
        
        # Step 4: Apply minimum efficiency check
        if performance['efficiency_pct'] < self.MIN_EFFICIENCY:
            evaluation['exclusion_reasons'].append(
                f"Efficiency {performance['efficiency_pct']:.1f}% below minimum {self.MIN_EFFICIENCY}%"
            )
            evaluation['near_miss_info'] = {
                'efficiency': performance['efficiency_pct'],
                'efficiency_deficit': self.MIN_EFFICIENCY - performance['efficiency_pct']
            }
            return evaluation
            
        # Step 5: Check head delivery
        if performance['head_m'] < head_m:
            evaluation['exclusion_reasons'].append(
                f"Cannot deliver required head: {performance['head_m']:.1f}m < {head_m}m"
            )
            evaluation['near_miss_info'] = {
                'head_delivered': performance['head_m'],
                'head_deficit': head_m - performance['head_m']
            }
            return evaluation
            
        # Step 6: Calculate comprehensive score
        score_breakdown = self._calculate_score(
            performance, flow_m3hr, head_m, npsha_m, best_solution
        )
        
        # Step 7: Apply modification penalties
        if best_solution['method'] == 'speed_variation':
            speed_penalty = self._calculate_speed_penalty(best_solution.get('speed_ratio', 1.0))
            score_breakdown['speed_penalty'] = -speed_penalty
            
        elif best_solution['method'] == 'impeller_trimming':
            trim_penalty = self._calculate_trim_penalty(best_solution.get('trim_percent', 100))
            score_breakdown['trim_penalty'] = -trim_penalty
            
        # Calculate total score
        total_score = sum(score_breakdown.values())
        
        # Update evaluation
        evaluation.update({
            'feasible': True,
            'score': total_score,
            'score_breakdown': score_breakdown,
            'performance': performance,
            'solution_method': best_solution['method'],
            'modification_details': best_solution.get('modification_details', {})
        })
        
        return evaluation
        
    def _find_best_solution(self, curves: List[Dict], flow_m3hr: float, 
                           head_m: float) -> Optional[Dict]:
        """
        Find the best solution across all curves and modification methods.
        Evaluates in order of preference:
        1. Direct interpolation (no modifications)
        2. Impeller trimming
        3. Speed variation
        """
        solutions = []
        
        for curve in curves:
            # Method 1: Direct interpolation
            direct_solution = self._try_direct_interpolation(curve, flow_m3hr, head_m)
            if direct_solution:
                direct_solution['method'] = 'direct'
                direct_solution['curve'] = curve
                solutions.append(direct_solution)
                
            # Method 2: Impeller trimming
            trim_solution = self._try_impeller_trimming(curve, flow_m3hr, head_m)
            if trim_solution:
                trim_solution['method'] = 'impeller_trimming'
                trim_solution['curve'] = curve
                solutions.append(trim_solution)
                
            # Method 3: Speed variation
            speed_solution = self._try_speed_variation(curve, flow_m3hr, head_m)
            if speed_solution:
                speed_solution['method'] = 'speed_variation'
                speed_solution['curve'] = curve
                solutions.append(speed_solution)
                
        if not solutions:
            return None
            
        # Score each solution and return the best
        best_solution = None
        best_score = -float('inf')
        
        for solution in solutions:
            # Quick scoring for solution selection
            score = solution['performance']['efficiency_pct']
            
            # Prefer direct solutions
            if solution['method'] == 'direct':
                score += 10
            # Small penalty for modifications
            elif solution['method'] == 'impeller_trimming':
                score -= 5
            elif solution['method'] == 'speed_variation':
                score -= 8
                
            if score > best_score:
                best_score = score
                best_solution = solution
                
        return best_solution
        
    def _try_direct_interpolation(self, curve: Dict, flow_m3hr: float, 
                                 head_m: float) -> Optional[Dict]:
        """Try to meet requirements through direct interpolation."""
        points = curve.get('performance_points', [])
        if len(points) < 2:
            return None
            
        flows = np.array([p['flow_m3hr'] for p in points])
        heads = np.array([p['head_m'] for p in points])
        efficiencies = np.array([p['efficiency_pct'] for p in points])
        
        # Check if within acceptable extrapolation range
        flow_min, flow_max = flows.min(), flows.max()
        
        # Progressive extrapolation limits
        if not (flow_min * (1 - self.MAX_EXTRAPOLATION/100) <= flow_m3hr <= 
                flow_max * (1 + self.MAX_EXTRAPOLATION/100)):
            return None
            
        try:
            # Create interpolation functions
            head_interp = interpolate.interp1d(flows, heads, kind='quadratic', 
                                             bounds_error=False, fill_value='extrapolate')
            eff_interp = interpolate.interp1d(flows, efficiencies, kind='quadratic',
                                            bounds_error=False, fill_value='extrapolate')
            
            # Calculate performance
            head_at_flow = float(head_interp(flow_m3hr))
            eff_at_flow = float(eff_interp(flow_m3hr))
            
            # Check if meets head requirement
            if head_at_flow >= head_m and eff_at_flow >= self.MIN_EFFICIENCY:
                # Calculate power
                power_kw = (flow_m3hr * head_at_flow * 9.81) / (3600 * eff_at_flow / 100)
                
                # Calculate NPSH if available
                npshr = self._interpolate_npsh(curve, flow_m3hr)
                
                return {
                    'performance': {
                        'flow_m3hr': flow_m3hr,
                        'head_m': head_at_flow,
                        'efficiency_pct': eff_at_flow,
                        'power_kw': power_kw,
                        'npshr_m': npshr
                    }
                }
                
        except Exception as e:
            logger.debug(f"Direct interpolation failed: {e}")
            
        return None
        
    def _try_impeller_trimming(self, curve: Dict, flow_m3hr: float, 
                              head_m: float) -> Optional[Dict]:
        """Try to meet requirements through impeller trimming."""
        # Get current impeller diameter
        current_diameter = curve.get('impeller_diameter_mm', 0)
        if current_diameter <= 0:
            return None
            
        # Find point on curve at target flow
        performance_at_flow = self._get_performance_at_flow(curve, flow_m3hr)
        if not performance_at_flow:
            return None
            
        current_head = performance_at_flow['head_m']
        
        # Apply affinity laws to find required diameter
        # H2/H1 = (D2/D1)^2
        required_diameter_ratio = np.sqrt(head_m / current_head)
        required_diameter = current_diameter * required_diameter_ratio
        
        # Calculate trim percentage
        trim_percent = (required_diameter / current_diameter) * 100
        
        # Check if within acceptable trim range
        if not (self.MIN_TRIM <= trim_percent <= self.MAX_TRIM):
            return None
            
        # Calculate trimmed performance
        trimmed_efficiency = performance_at_flow['efficiency_pct']  # Efficiency remains roughly constant
        power_kw = (flow_m3hr * head_m * 9.81) / (3600 * trimmed_efficiency / 100)
        
        # Adjust NPSH for trimming (conservative approach)
        npshr = performance_at_flow.get('npshr_m', 0)
        if npshr > 0:
            npshr = npshr * required_diameter_ratio  # NPSH scales with diameter
            
        return {
            'performance': {
                'flow_m3hr': flow_m3hr,
                'head_m': head_m,
                'efficiency_pct': trimmed_efficiency,
                'power_kw': power_kw,
                'npshr_m': npshr
            },
            'trim_percent': trim_percent,
            'modification_details': {
                'original_diameter': current_diameter,
                'trimmed_diameter': required_diameter,
                'trim_percent': trim_percent
            }
        }
        
    def _try_speed_variation(self, curve: Dict, flow_m3hr: float, 
                            head_m: float) -> Optional[Dict]:
        """Try to meet requirements through speed variation."""
        # Get test speed
        test_speed = curve.get('test_speed_rpm', 1450)
        
        # Find point on curve at target flow
        performance_at_flow = self._get_performance_at_flow(curve, flow_m3hr)
        if not performance_at_flow:
            return None
            
        current_head = performance_at_flow['head_m']
        
        # Apply affinity laws to find required speed
        # H2/H1 = (N2/N1)^2
        required_speed_ratio = np.sqrt(head_m / current_head)
        required_speed = test_speed * required_speed_ratio
        
        # Check if within acceptable speed range
        if not (self.MIN_SPEED <= required_speed <= self.MAX_SPEED):
            return None
            
        # Calculate performance at new speed
        # Q2/Q1 = N2/N1 (flow scales linearly with speed)
        # P2/P1 = (N2/N1)^3 (power scales with cube of speed)
        
        adjusted_efficiency = performance_at_flow['efficiency_pct']  # Efficiency remains roughly constant
        power_at_test = (flow_m3hr * current_head * 9.81) / (3600 * adjusted_efficiency / 100)
        adjusted_power = power_at_test * (required_speed_ratio ** 3)
        
        # Adjust NPSH for speed variation
        npshr = performance_at_flow.get('npshr_m', 0)
        if npshr > 0:
            npshr = npshr * (required_speed_ratio ** 2)  # NPSH scales with square of speed
            
        return {
            'performance': {
                'flow_m3hr': flow_m3hr,
                'head_m': head_m,
                'efficiency_pct': adjusted_efficiency,
                'power_kw': adjusted_power,
                'npshr_m': npshr
            },
            'speed_ratio': required_speed_ratio,
            'modification_details': {
                'test_speed': test_speed,
                'required_speed': required_speed,
                'speed_variation_pct': (required_speed_ratio - 1) * 100
            }
        }
        
    def _get_performance_at_flow(self, curve: Dict, flow_m3hr: float) -> Optional[Dict]:
        """Get interpolated performance at specified flow."""
        points = curve.get('performance_points', [])
        if len(points) < 2:
            return None
            
        flows = np.array([p['flow_m3hr'] for p in points])
        heads = np.array([p['head_m'] for p in points])
        efficiencies = np.array([p['efficiency_pct'] for p in points])
        
        try:
            head_interp = interpolate.interp1d(flows, heads, kind='quadratic',
                                             bounds_error=False, fill_value='extrapolate')
            eff_interp = interpolate.interp1d(flows, efficiencies, kind='quadratic',
                                            bounds_error=False, fill_value='extrapolate')
            
            head_at_flow = float(head_interp(flow_m3hr))
            eff_at_flow = float(eff_interp(flow_m3hr))
            
            npshr = self._interpolate_npsh(curve, flow_m3hr)
            
            return {
                'flow_m3hr': flow_m3hr,
                'head_m': head_at_flow,
                'efficiency_pct': eff_at_flow,
                'npshr_m': npshr
            }
            
        except Exception:
            return None
            
    def _interpolate_npsh(self, curve: Dict, flow_m3hr: float) -> float:
        """Interpolate NPSH at given flow."""
        points = curve.get('performance_points', [])
        npsh_data = [(p['flow_m3hr'], p.get('npshr_m', 0)) for p in points if p.get('npshr_m')]
        
        if len(npsh_data) < 2:
            return 0.0
            
        flows, npshs = zip(*npsh_data)
        
        try:
            npsh_interp = interpolate.interp1d(flows, npshs, kind='linear',
                                             bounds_error=False, fill_value='extrapolate')
            return max(0, float(npsh_interp(flow_m3hr)))
        except Exception:
            return 0.0
            
    def _calculate_score(self, performance: Dict, flow_m3hr: float, head_m: float,
                        npsha_m: Optional[float], solution: Dict) -> Dict[str, float]:
        """Calculate comprehensive score breakdown."""
        scores = {}
        
        # 1. BEP Proximity Score (40 points max)
        bep_score = self._calculate_bep_score(solution['curve'], flow_m3hr)
        scores['bep_score'] = bep_score
        
        # 2. Efficiency Score (30 points max)
        efficiency = performance['efficiency_pct']
        if efficiency >= 85:
            eff_score = 30
        elif efficiency >= 75:
            eff_score = 25 + (efficiency - 75) * 0.5
        elif efficiency >= 65:
            eff_score = 20 + (efficiency - 65) * 0.5
        else:
            eff_score = max(0, (efficiency - 40) * 0.4)
        scores['efficiency_score'] = eff_score
        
        # 3. Head Margin Score (15 points max)
        head_margin_pct = ((performance['head_m'] - head_m) / head_m) * 100
        if head_margin_pct <= 5:
            margin_score = 15
        elif head_margin_pct <= 10:
            margin_score = 15 - (head_margin_pct - 5) * 1.5
        elif head_margin_pct <= self.MAX_HEAD_MARGIN:
            margin_score = 7.5 - (head_margin_pct - 10) * 0.75
        else:
            margin_score = -((head_margin_pct - self.MAX_HEAD_MARGIN) * 2)
        scores['head_margin_score'] = margin_score
        
        # 4. NPSH Score (15 points max)
        if npsha_m and performance.get('npshr_m'):
            npsh_margin = npsha_m - performance['npshr_m']
            if npsh_margin >= 3:
                npsh_score = 15
            elif npsh_margin >= 1.5:
                npsh_score = 10 + (npsh_margin - 1.5) * 3.33
            elif npsh_margin >= 0.5:
                npsh_score = 5 + (npsh_margin - 0.5) * 5
            else:
                npsh_score = max(0, npsh_margin * 10)
            scores['npsh_score'] = npsh_score
        else:
            scores['npsh_score'] = 7.5  # Neutral score when NPSH unknown
            
        return scores
        
    def _calculate_bep_score(self, curve: Dict, flow_m3hr: float) -> float:
        """Calculate BEP proximity score with improved algorithm."""
        points = curve.get('performance_points', [])
        if not points:
            return 0
            
        # Find BEP (highest efficiency point)
        bep_point = max(points, key=lambda p: p.get('efficiency_pct', 0))
        bep_flow = bep_point['flow_m3hr']
        bep_efficiency = bep_point['efficiency_pct']
        
        if bep_flow <= 0:
            return 0
            
        # Calculate flow ratio
        flow_ratio = flow_m3hr / bep_flow
        
        # Optimal zone: 70-120% of BEP
        if 0.7 <= flow_ratio <= 1.2:
            # Peak score at 95-105% of BEP
            if 0.95 <= flow_ratio <= 1.05:
                return 40
            elif flow_ratio < 0.95:
                # Linear decay from 70% to 95%
                return 30 + (flow_ratio - 0.7) * 40
            else:
                # Linear decay from 105% to 120%
                return 40 - (flow_ratio - 1.05) * 66.67
        
        # Marginal zones
        elif 0.5 <= flow_ratio < 0.7:
            return 20 * (flow_ratio - 0.5) / 0.2
        elif 1.2 < flow_ratio <= 1.5:
            return 20 * (1.5 - flow_ratio) / 0.3
        else:
            return 0
            
    def _calculate_speed_penalty(self, speed_ratio: float) -> float:
        """Calculate penalty for speed variation."""
        speed_variation_pct = abs(speed_ratio - 1) * 100
        
        if speed_variation_pct <= 5:
            return 0
        elif speed_variation_pct <= 10:
            return (speed_variation_pct - 5) * 1.5
        elif speed_variation_pct <= 20:
            return 7.5 + (speed_variation_pct - 10) * 0.75
        else:
            return self.SPEED_PENALTY_MAX
            
    def _calculate_trim_penalty(self, trim_percent: float) -> float:
        """Calculate penalty for impeller trimming."""
        trim_amount = 100 - trim_percent
        
        if trim_amount <= 2:
            return 0
        elif trim_amount <= 10:
            return (trim_amount - 2) * 0.625
        elif trim_amount <= 20:
            return 5 + (trim_amount - 10) * 0.5
        else:
            return self.TRIM_PENALTY_MAX
            
    def generate_selection_report(self, evaluations: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive selection report with transparency."""
        feasible_pumps = [e for e in evaluations if e['feasible']]
        excluded_pumps = [e for e in evaluations if not e['feasible']]
        
        # Sort feasible pumps by score
        feasible_pumps.sort(key=lambda x: x['score'], reverse=True)
        
        # Identify near-miss pumps
        near_miss_pumps = []
        for pump in excluded_pumps:
            if pump.get('near_miss_info'):
                near_miss_pumps.append(pump)
                
        return {
            'summary': {
                'total_evaluated': len(evaluations),
                'physically_feasible': len(feasible_pumps),
                'excluded': len(excluded_pumps),
                'near_miss': len(near_miss_pumps),
                'methodology_version': 'v5.0'
            },
            'top_recommendations': feasible_pumps[:10],
            'all_feasible': feasible_pumps,
            'near_miss_pumps': near_miss_pumps,
            'exclusion_analysis': self._analyze_exclusions(excluded_pumps)
        }
        
    def _analyze_exclusions(self, excluded_pumps: List[Dict]) -> Dict[str, int]:
        """Analyze exclusion reasons for transparency."""
        reason_counts = {}
        
        for pump in excluded_pumps:
            for reason in pump.get('exclusion_reasons', []):
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
                
        return reason_counts