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

logger = logging.getLogger(__name__)

class CatalogPump:
    """Represents a pump model with multiple performance curves"""

    def __init__(self, pump_data: Dict[str, Any]):
        self.pump_code = pump_data['pump_code']
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
        self.description = pump_data.get('description', f"{self.pump_code} - {self.model_series}")
        self.max_flow_m3hr = pump_data.get('max_flow_m3hr', self._calculate_max_flow())
        self.max_head_m = pump_data.get('max_head_m', self._calculate_max_head())
        self.max_power_kw = pump_data.get('max_power_kw', self._calculate_max_power())
        self.min_efficiency = pump_data.get('min_efficiency', self._calculate_min_efficiency())
        self.max_efficiency = pump_data.get('max_efficiency', self._calculate_max_efficiency())
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
            powers = [p.get('power_kw', 0) for p in curve['performance_points'] if p.get('power_kw')]
            if powers:
                max_power = max(max_power, max(powers))
        return max_power if max_power > 0 else 50.0  # Default estimate

    def _calculate_min_efficiency(self) -> float:
        """Calculate minimum efficiency from all curves"""
        min_eff = 100.0
        for curve in self.curves:
            effs = [p['efficiency_pct'] for p in curve['performance_points'] if p['efficiency_pct'] > 0]
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
                        'impeller_diameter_mm': curve['impeller_diameter_mm']
                    }
        
        return best_bep
    
    def calculate_bep_distance(self, target_flow: float, target_head: float) -> Dict[str, Any]:
        """Calculate distance from BEP and provide industry-standard BEP-based scoring"""
        bep = self.get_bep_point()
        if not bep:
            return {'bep_score': 0, 'distance_pct': float('inf'), 'bep_available': False}
        
        bep_flow = bep['flow_m3hr']
        bep_head = bep['head_m']
        
        # Calculate flow position relative to BEP
        flow_ratio = target_flow / bep_flow if bep_flow > 0 else 0
        flow_distance_pct = abs(target_flow - bep_flow) / bep_flow * 100 if bep_flow > 0 else float('inf')
        head_distance_pct = abs(target_head - bep_head) / bep_head * 100 if bep_head > 0 else float('inf')
        
        # Industry-standard tolerance zones evaluation
        # Preferred operating range: 70% to 120% of BEP flow
        operating_zone = "unknown"
        zone_score = 0
        
        if 0.95 <= flow_ratio <= 1.05:
            # At BEP (95-105%) - Excellent
            operating_zone = "at_bep"
            zone_score = 30
        elif 1.05 < flow_ratio <= 1.20:
            # Right side preferred zone (105-120%) - Industry preference
            operating_zone = "right_preferred"
            zone_score = 25
        elif 0.85 <= flow_ratio < 0.95:
            # Left side acceptable (85-95%) - Good
            operating_zone = "left_acceptable" 
            zone_score = 20
        elif 0.70 <= flow_ratio < 0.85:
            # Lower flow zone (70-85%) - Acceptable but watch efficiency
            operating_zone = "low_flow"
            zone_score = 15
        elif 1.20 < flow_ratio <= 1.30:
            # Extended right side (120-130%) - Acceptable but higher NPSH
            operating_zone = "extended_right"
            zone_score = 12
        elif flow_ratio < 0.70:
            # Below minimum continuous stable flow - Poor
            operating_zone = "unstable_zone"
            zone_score = 5
        else:  # flow_ratio > 1.30
            # Far right - risk of cavitation and high power
            operating_zone = "overload_zone"
            zone_score = 3
        
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

    def get_best_curve_for_duty(self, flow_m3hr: float, head_m: float) -> Optional[Dict[str, Any]]:
        """Find the best curve for the given duty point"""
        best_curve = None
        best_score = float('inf')

        for curve in self.curves:
            # Calculate how well this curve matches the duty point
            points = curve['performance_points']
            flows = [p['flow_m3hr'] for p in points]
            heads = [p['head_m'] for p in points]

            if not flows or not heads:
                continue

            # Check if duty point is within curve range
            flow_in_range = min(flows) <= flow_m3hr <= max(flows)
            head_in_range = min(heads) <= head_m <= max(heads)

            if flow_in_range and head_in_range:
                # Calculate efficiency at duty point
                try:
                    head_interp = interpolate.interp1d(flows, heads, kind='linear', bounds_error=False)
                    eff_interp = interpolate.interp1d(flows, [p['efficiency_pct'] for p in points], 
                                                     kind='linear', bounds_error=False)

                    predicted_head = head_interp(flow_m3hr)
                    efficiency = eff_interp(flow_m3hr)

                    if not np.isnan(predicted_head) and not np.isnan(efficiency):
                        head_error = abs(float(predicted_head) - head_m)
                        score = head_error - efficiency * 0.1  # Favor higher efficiency

                        if score < best_score:
                            best_score = score
                            best_curve = curve

                except Exception as e:
                    logger.debug(f"Interpolation error for {self.pump_code} curve {curve['curve_index']}: {e}")
                    continue

        return best_curve

    def _validate_physical_capability(self, flow_m3hr: float, head_m: float) -> bool:
        """Validate that pump can physically meet the requirements within authentic performance envelope"""
        
        # Check against absolute maximum capabilities from all curves
        max_head = self._calculate_max_head()
        max_flow = self._calculate_max_flow()
        min_flow = min(min(p['flow_m3hr'] for p in curve['performance_points']) for curve in self.curves)
        
        # Hard physical limits - no extrapolation beyond authentic data
        if head_m > max_head * 1.1:  # Allow 10% margin for speed variation
            logger.debug(f"Required head {head_m}m exceeds pump maximum {max_head}m")
            return False
            
        if flow_m3hr > max_flow * 1.2:  # Allow 20% margin for impeller trimming
            logger.debug(f"Required flow {flow_m3hr} m³/hr exceeds pump maximum {max_flow} m³/hr")
            return False
            
        if flow_m3hr < min_flow * 0.5:  # Don't operate at extremely low flows
            logger.debug(f"Required flow {flow_m3hr} m³/hr below practical minimum {min_flow * 0.5} m³/hr")
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
                if curve_flow_range[0] * 0.7 <= flow_m3hr <= curve_flow_range[1] * 1.3:
                    return True
        
        return False

    def _validate_speed_variation_limits(self, speed_result: Dict[str, Any], base_curve: Dict[str, Any]) -> bool:
        """Validate that speed variation results are within reasonable engineering limits"""
        
        # Check speed limits
        required_speed = speed_result.get('required_speed_rpm', 0)
        test_speed = base_curve.get('test_speed_rpm', 980)
        
        # Industry standard: don't exceed 120% or go below 70% of test speed
        if required_speed > test_speed * 1.2 or required_speed < test_speed * 0.7:
            logger.debug(f"Required speed {required_speed} RPM outside safe range for test speed {test_speed} RPM")
            return False
        
        # Check head delivery isn't excessive extrapolation
        base_heads = [p['head_m'] for p in base_curve['performance_points']]
        max_base_head = max(base_heads)
        
        if speed_result['head_m'] > max_base_head * 1.5:  # 50% head increase is maximum reasonable
            logger.debug(f"Speed variation produces excessive head: {speed_result['head_m']}m vs base max {max_base_head}m")
            return False
        
        return True

    def get_performance_at_duty(self, flow_m3hr: float, head_m: float) -> Optional[Dict[str, Any]]:
        """Get performance characteristics at specific duty point using requirement-driven sizing"""
        
        # CRITICAL: Validate against physical pump capabilities first
        if not self._validate_physical_capability(flow_m3hr, head_m):
            logger.debug(f"Pump {self.pump_code} cannot physically meet requirements: {flow_m3hr} m³/hr, {head_m} m")
            return None
        
        from .impeller_scaling import get_impeller_scaling_engine
        
        scaling_engine = get_impeller_scaling_engine()
        
        # Try impeller trimming first
        optimal_sizing = scaling_engine.find_optimal_sizing(self.curves, flow_m3hr, head_m)
        
        # If impeller trimming doesn't work, try speed variation
        if not optimal_sizing:
            pump_specs = {
                'test_speed_rpm': self.specifications.get('test_speed_rpm', 980),
                'max_speed_rpm': self.specifications.get('max_speed_rpm', 1150),
                'min_speed_rpm': self.specifications.get('min_speed_rpm', 700)
            }
            
            # Try speed variation on each curve
            for curve in self.curves:
                speed_result = scaling_engine.calculate_speed_variation(curve, flow_m3hr, head_m, pump_specs)
                if speed_result and speed_result['meets_requirements']:
                    # Double-check that speed variation doesn't exceed physical limits
                    if self._validate_speed_variation_limits(speed_result, curve):
                        return {
                            'curve': curve,
                            'flow_m3hr': speed_result['flow_m3hr'],
                            'head_m': speed_result['head_m'],
                            'efficiency_pct': speed_result['efficiency_pct'],
                            'power_kw': speed_result['power_kw'],
                            'npshr_m': speed_result['npshr_m'],
                            'impeller_diameter_mm': speed_result['impeller_diameter_mm'],
                            'test_speed_rpm': speed_result['test_speed_rpm'],
                            'sizing_info': {
                                'base_diameter_mm': speed_result['impeller_diameter_mm'],
                                'required_diameter_mm': speed_result['impeller_diameter_mm'],
                                'trim_percent': 100.0,
                                'meets_requirements': True,
                                'head_margin_m': speed_result['head_margin_m'],
                                'required_speed_rpm': speed_result['required_speed_rpm'],
                                'speed_variation_pct': speed_result['speed_variation_pct'],
                                'vfd_required': True,
                                'sizing_method': 'speed_variation'
                            }
                        }
        
        if optimal_sizing:
            # Return properly sized pump performance (impeller trimming)
            performance = optimal_sizing['performance']
            sizing = optimal_sizing['sizing']
            curve = optimal_sizing['curve']
            
            return {
                'curve': curve,
                'flow_m3hr': performance['flow_m3hr'],
                'head_m': performance['head_m'],
                'efficiency_pct': performance['efficiency_pct'],
                'power_kw': performance['power_kw'],
                'npshr_m': performance['npshr_m'],
                'impeller_diameter_mm': performance['impeller_diameter_mm'],
                'test_speed_rpm': performance['test_speed_rpm'],
                # Additional sizing information
                'sizing_info': {
                    'base_diameter_mm': sizing['base_diameter_mm'],
                    'required_diameter_mm': sizing['required_diameter_mm'],
                    'trim_percent': sizing['trim_percent'],
                    'meets_requirements': performance['meets_requirements'],
                    'head_margin_m': performance['head_margin_m'],
                    'sizing_method': 'impeller_trimming'
                }
            }
            
        # Fallback to old method if no sizing possible
        return self._get_performance_interpolated(flow_m3hr, head_m)
        
    def _get_performance_interpolated(self, flow_m3hr: float, head_m: float) -> Optional[Dict[str, Any]]:
        """Legacy interpolation method for when sizing is not possible"""
        best_curve = self.get_best_curve_for_duty(flow_m3hr, head_m)

        if not best_curve:
            return None

        points = best_curve['performance_points']
        flows = [p['flow_m3hr'] for p in points]
        heads = [p['head_m'] for p in points]
        effs = [p['efficiency_pct'] for p in points]

        try:
            head_interp = interpolate.interp1d(flows, heads, kind='linear', bounds_error=False)
            eff_interp = interpolate.interp1d(flows, effs, kind='linear', bounds_error=False)

            predicted_head = float(head_interp(flow_m3hr))
            efficiency = float(eff_interp(flow_m3hr))

            # Calculate power using exact VBA formula with pump's actual head
            if efficiency > 0:
                efficiency_decimal = efficiency / 100.0
                sg = 1.0  # Specific gravity for water
                power_kw = (flow_m3hr * predicted_head * sg * 9.81) / (efficiency_decimal * 3600)
                power_kw = round(power_kw, 3)
            else:
                power_kw = 0.0

            # Calculate NPSH if available
            npshr_m = None
            npshs = [p['npshr_m'] for p in points if p['npshr_m'] and p['npshr_m'] > 0]
            if npshs and len(npshs) == len(flows):
                npsh_interp = interpolate.interp1d(flows, npshs, kind='linear', bounds_error=False)
                npshr_m = float(npsh_interp(flow_m3hr))

            return {
                'curve': best_curve,
                'flow_m3hr': flow_m3hr,  # CRITICAL: Always maintain required flow rate
                'head_m': predicted_head,
                'efficiency_pct': efficiency,
                'power_kw': power_kw,
                'npshr_m': npshr_m,
                'impeller_diameter_mm': best_curve['impeller_diameter_mm'],
                'test_speed_rpm': best_curve['test_speed_rpm']
            }

        except Exception as e:
            logger.debug(f"Performance calculation error for {self.pump_code}: {e}")
            return None

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

            logger.info(f"Catalog Engine: Loaded {len(self.pumps)} pump models from repository")
            logger.info(f"Catalog Engine: Total curves: {self.metadata.get('total_curves', 0)}")
            logger.info(f"Catalog Engine: NPSH curves: {self.metadata.get('npsh_curves', 0)} ({self.metadata.get('npsh_curves', 0)/self.metadata.get('total_curves', 1)*100:.1f}%)")

        except Exception as e:
            logger.error(f"Catalog Engine: Error loading from repository: {e}")
            self.pumps = []
            self.metadata = {}

    def load_catalog(self):
        """Reload catalog from repository (for compatibility)"""
        self._load_from_repository()

    def select_pumps(self, flow_m3hr: float, head_m: float, max_results: int = 10, pump_type: str | None = None) -> List[Dict[str, Any]]:
        """Select pumps for given duty point with requirement-driven validation"""
        suitable_pumps = []
        
        # Debug logging for pump type filtering
        logger.info(f"Catalog Engine: Filtering for pump_type='{pump_type}', flow={flow_m3hr}, head={head_m}")
        total_pumps = len(self.pumps)
        filtered_count = 0

        for pump in self.pumps:
            # Filter by pump type if specified
            if pump_type and pump_type.upper() != 'GENERAL':
                # Normalize pump type names to handle form/database mismatches
                form_type = pump_type.upper().replace('_', '')  # MULTI_STAGE -> MULTISTAGE
                db_type = pump.pump_type.upper().replace('_', '')  # Already MULTISTAGE
                
                if form_type != db_type:
                    continue  # Skip pumps that don't match the selected type
                filtered_count += 1
            
            performance = pump.get_performance_at_duty(flow_m3hr, head_m)

            if performance:
                original_delivered_head = performance['head_m']
                original_efficiency = performance['efficiency_pct']

                # Apply tolerance logic to find best operating point
                delivered_head, efficiency, best_flow = self._find_best_operating_point(
                    performance, flow_m3hr, head_m
                )
                
                # Always use the best operating point values for evaluation
                # Update performance object to reflect best operating point
                if best_flow != performance['flow_m3hr']:
                    performance['head_m'] = delivered_head
                    performance['efficiency_pct'] = efficiency
                    performance['flow_m3hr'] = best_flow
                    logger.debug(f"Updated pump {pump.pump_code} to optimal point: {best_flow:.1f} m³/hr at {delivered_head:.1f}m head")

                # Check if pump meets requirements at best operating point
                meets_head_requirement = delivered_head >= head_m
                
                if meets_head_requirement and efficiency >= 40:
                    # Calculate head margin (positive indicates over-delivery)
                    head_margin = delivered_head - head_m
                    head_margin_pct = (head_margin / head_m) * 100

                    # OPTIMIZED SCORING SYSTEM: Efficiency-Prioritized Selection
                    # 1. Efficiency at duty point (80 points max) - Primary performance indicator
                    # 2. BEP proximity (15 points max) - Important for pump longevity but secondary
                    # 3. Head margin bonus (20 points max) - Safety margin
                    
                    # Calculate BEP analysis for this pump
                    bep_analysis = pump.calculate_bep_distance(flow_m3hr, head_m)
                    # Scale BEP score to 15 points max (reduced from 30)
                    bep_score = (bep_analysis.get('bep_score', 0) / 30.0) * 15
                    
                    # Efficiency score (scaled to 80 points max - increased from 70)
                    efficiency_score = (efficiency / 100.0) * 80
                    
                    # Head margin bonus - reward precise delivery and reasonable safety margins
                    if -2 <= head_margin_pct <= 2:
                        # Perfect delivery - meets requirements exactly (±2%)
                        margin_bonus = 20  # Maximum bonus for precise delivery
                    elif 2 < head_margin_pct <= 10:
                        # Good safety margin without over-delivery
                        margin_bonus = 18 - (head_margin_pct - 2) * 0.5  # 18-14 points
                    elif 10 < head_margin_pct <= 20:
                        # Acceptable margin but starting to over-deliver
                        margin_bonus = 14 - (head_margin_pct - 10) * 0.3  # 14-11 points
                    else:
                        # Excessive over-delivery - inefficient pump selection
                        margin_bonus = max(5, 11 - (head_margin_pct - 20) * 0.2)  # Minimum 5 points
                    
                    # Total score: BEP proximity + Efficiency + Margin bonus
                    score = bep_score + efficiency_score + margin_bonus

                    # Check if sizing information is available from requirement-driven approach
                    sizing_validated = False
                    if 'sizing_info' in performance:
                        sizing_info = performance['sizing_info']
                        sizing_validated = sizing_info.get('meets_requirements', False)
                        if not sizing_validated:
                            # Skip pumps that fail sizing validation only if they have sizing info
                            # If no sizing info, rely on tolerance logic validation above
                            continue
                    else:
                        # For pumps without sizing info, they passed tolerance validation above
                        sizing_validated = True

                    result = {
                        'pump': pump,
                        'performance': performance,
                        'suitability_score': score,
                        'head_margin_m': head_margin,
                        'head_margin_pct': head_margin_pct,
                        'efficiency_at_duty': efficiency,
                        'meets_requirements': True,  # All pumps in results meet requirements
                        'sizing_validated': sizing_validated,
                        # BEP analysis data for display and further processing
                        'bep_analysis': bep_analysis,
                        'bep_score': bep_score,
                        'efficiency_score': efficiency_score,
                        'margin_bonus': margin_bonus
                    }
                    suitable_pumps.append(result)

        # Sort by suitability score (descending)
        suitable_pumps.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        # Log filtering results
        logger.info(f"Catalog Engine: Found {len(suitable_pumps)} suitable pumps from {total_pumps} total")
        if pump_type and pump_type.upper() != 'GENERAL':
            logger.info(f"Catalog Engine: Type filtering applied for '{pump_type}' - {filtered_count} pumps passed filter")
        
        # Log top results for debugging
        for i, pump in enumerate(suitable_pumps[:5]):
            logger.info(f"  #{i+1}: {pump['pump'].pump_code} ({pump['pump'].pump_type}) - Score: {pump['suitability_score']:.1f}")

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
                'overall_score': result['suitability_score'],  # Alias for compatibility
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
                'bep_score': result['bep_score'],
                'efficiency_score': result['efficiency_score'],
                'margin_bonus': result['margin_bonus'],
                'sizing_validated': result['sizing_validated']
            }
            formatted_results.append(formatted_result)

        return formatted_results

    def _find_best_operating_point(self, performance: Dict[str, Any], 
                                  target_flow: float, target_head: float) -> tuple:
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
        
        max_head_available = max([p.get('head_m', 0) for p in points if p.get('head_m')], default=0)
        
        # If pump lacks physical capability, return current point
        if max_head_available < target_head:
            return delivered_head, efficiency, current_flow
        
        # Find operating points that meet head requirement
        suitable_points = []
        for p in points:
            if p.get('head_m', 0) >= target_head and p.get('flow_m3hr', 0) > 0:
                suitable_points.append({
                    'flow': p['flow_m3hr'],
                    'head': p['head_m'],
                    'efficiency': p['efficiency_pct'],
                    'flow_diff': abs(p['flow_m3hr'] - target_flow) / target_flow * 100
                })
        
        if not suitable_points:
            return delivered_head, efficiency, current_flow
        
        # Apply flow tolerance (10%)
        within_tolerance = [p for p in suitable_points if p['flow_diff'] <= 10.0]
        
        if not within_tolerance:
            return delivered_head, efficiency, current_flow
        
        # Select best point within tolerance (closest to target flow, highest efficiency)
        best_point = min(within_tolerance, key=lambda p: (p['flow_diff'], -p['efficiency']))
        
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
            'total_models': len(self.pumps),
            'total_curves': self.metadata.get('total_curves', 0),
            'total_points': self.metadata.get('total_points', 0),
            'npsh_curves': self.metadata.get('npsh_curves', 0),
            'npsh_coverage_pct': self.metadata.get('npsh_curves', 0) / self.metadata.get('total_curves', 1) * 100,
            'power_curves': self.metadata.get('power_curves', 0)
        }

# Global catalog engine instance
catalog_engine = None

def get_catalog_engine() -> CatalogEngine:
    """Get global catalog engine instance"""
    global catalog_engine
    if catalog_engine is None:
        catalog_engine = CatalogEngine()
    return catalog_engine

def convert_catalog_pump_to_legacy_format(catalog_pump: CatalogPump, performance: Dict[str, Any]) -> object:
    """Convert catalog pump to legacy format for PDF compatibility with authentic data preservation"""
    curve = performance['curve']

    # Create a legacy-compatible object that preserves authentic data
    class LegacyPumpData:
        def __init__(self, catalog_pump, performance_data):
            self.pump_code = catalog_pump.pump_code

            # Use actual calculated impeller diameter from scaling engine
            # Check if sizing info is available (from new requirement-driven approach)
            if 'sizing_info' in performance_data and performance_data['sizing_info']:
                sizing_info = performance_data['sizing_info']
                self.authentic_impeller_mm = sizing_info.get('required_diameter_mm', curve['impeller_diameter_mm'])
                self.trim_percent = sizing_info.get('trim_percent', 100.0)
                self.base_impeller_mm = sizing_info.get('base_diameter_mm', curve['impeller_diameter_mm'])
                self.trimming_required = sizing_info.get('trimming_required', False)
            else:
                # Fallback to curve diameter if no sizing info
                self.authentic_impeller_mm = curve['impeller_diameter_mm']
                self.trim_percent = 100.0
                self.base_impeller_mm = curve['impeller_diameter_mm']
                self.trimming_required = False

            # Use actual calculated performance values
            self.authentic_power_kw = performance_data.get('power_kw', 31.1)
            self.authentic_efficiency_pct = performance_data.get('efficiency_pct', 82)
            self.authentic_npshr_m = performance_data.get('npshr_m', 2.78)
            self.authentic_head_m = performance_data.get('head_m', 0)
            self.authentic_flow_m3hr = performance_data.get('flow_m3hr', 0)

            # Build legacy format pump_info with authentic values
            self.pump_info = {
                'pPumpCode': catalog_pump.pump_code,
                'pSuppName': catalog_pump.manufacturer,
                'pModel': catalog_pump.pump_code,
                'pSeries': catalog_pump.model_series,
                'pFilter1': catalog_pump.pump_type,
                'pPumpTestSpeed': str(curve['test_speed_rpm']),
                'pMaxQ': str(catalog_pump.specifications.get('max_flow_m3hr', 0)),
                'pMaxH': str(catalog_pump.specifications.get('max_head_m', 0)),
                'pMinImpD': str(catalog_pump.specifications.get('min_impeller_mm', 0)),
                'pMaxImpD': str(catalog_pump.specifications.get('max_impeller_mm', 0)),
                'manufacturer': catalog_pump.manufacturer,
                'rated_speed_rpm': curve['test_speed_rpm'],

                # Use calculated impeller diameter (not base curve diameter)
                'impeller_diameter_mm': self.authentic_impeller_mm,
                'power_kw': self.authentic_power_kw,

                # Convert performance points to legacy format
                'pM_FLOW': ';'.join(str(p['flow_m3hr']) for p in curve['performance_points']),
                'pM_HEAD': ';'.join(str(p['head_m']) for p in curve['performance_points']),
                'pM_EFF': ';'.join(str(p['efficiency_pct']) for p in curve['performance_points']),
                'pM_NP': ';'.join(str(p['npshr_m']) if p['npshr_m'] and p['npshr_m'] > 0 else '0' for p in curve['performance_points']),
                'pM_IMP': str(self.authentic_impeller_mm)  # Use calculated diameter
            }

    return LegacyPumpData(catalog_pump, performance)