import numpy as np
from typing import List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class CurveSynthesizer:
    """
    Mathematical curve fitting and synthesis from AI-extracted anchor points.
    Converts sparse anchor points into smooth, high-density performance curves.
    """

    def __init__(self):
        self.default_point_density = 9  # Target 9 points per curve as specified

    def synthesize_performance_curves(self, anchor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main synthesis method: converts anchor points to smooth curves

        Args:
            anchor_data: JSON from AI extraction containing anchor points

        Returns:
            Dictionary with synthesized curves ready for frontend rendering
        """
        try:
            # Handle empty or invalid anchor data
            if not anchor_data or not isinstance(anchor_data, dict):
                logger.warning("Empty or invalid anchor data provided to synthesizer")
                return {"curves": [], "efficiency_contours": [], "bep_markers": []}
            synthesized_data = {
                "curves": [],
                "efficiency_contours": [],
                "bep_markers": anchor_data.get("bepMarkers", [])
            }

            # Process performance curves
            if "performanceAnchorPoints" in anchor_data:
                performance_anchor_points = anchor_data["performanceAnchorPoints"]
                synthesized_curves = []
                for curve_data in performance_anchor_points:
                    synthesized_curve = self._synthesize_single_curve(curve_data)
                    if synthesized_curve is not None:  # Only add valid curves
                        synthesized_curves.append(synthesized_curve)
                    else:
                        logger.warning(f"[CurveSynthesizer] Skipped invalid curve for diameter: {curve_data.get('impellerDiameter')}")

                if not synthesized_curves:
                    logger.error("[CurveSynthesizer] CRITICAL: No valid curves could be synthesized")
                    return {"curves": [], "efficiency_contours": [], "bep_markers": []}
                synthesized_data["curves"] = synthesized_curves


            # Process efficiency contours
            if "efficiencyContours" in anchor_data:
                for contour_data in anchor_data["efficiencyContours"]:
                    synthesized_contour = self._synthesize_efficiency_contour(contour_data)
                    if synthesized_contour:
                        synthesized_data["efficiency_contours"].append(synthesized_contour)

            logger.info(f"Synthesized {len(synthesized_data['curves'])} curves with {self.default_point_density} points each")
            return synthesized_data

        except Exception as e:
            logger.error(f"Curve synthesis failed: {str(e)}")
            return {"curves": [], "efficiency_contours": [], "bep_markers": []}

    def _synthesize_single_curve(self, curve_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize a single performance curve using anchor points
        """
        try:
            impeller_diameter = curve_data.get("impellerDiameter")
            anchor_points = curve_data.get("anchorPoints", [])

            # NEW DEFENSIVE CHECK
            if not impeller_diameter or not isinstance(anchor_points, list) or len(anchor_points) < 3:
                logger.error(f"[CurveSynthesizer] REJECTED invalid anchor data for impeller '{impeller_diameter}'. "
                           f"Need valid diameter and at least 3 anchor points, got {len(anchor_points) if isinstance(anchor_points, list) else 'invalid'}")
                return None  # Explicitly return None for bad input

            # Validate anchor point data quality
            valid_points = []
            for point in anchor_points:
                if isinstance(point, dict) and "flow" in point and "head" in point:
                    flow = point["flow"]
                    head = point["head"]
                    if isinstance(flow, (int, float)) and isinstance(head, (int, float)) and flow > 0 and head > 0:
                        valid_points.append(point)
                    else:
                        logger.warning(f"[CurveSynthesizer] Skipping invalid anchor point: {point}")
                else:
                    logger.warning(f"[CurveSynthesizer] Skipping malformed anchor point: {point}")

            if len(valid_points) < 3:
                logger.error(f"[CurveSynthesizer] Insufficient valid anchor points for {impeller_diameter}mm: {len(valid_points)}/3 minimum")
                return None

            anchor_points = valid_points  # Use only validated points

            logger.info(f"[CurveSynthesizer] Synthesizing curve for {impeller_diameter}mm impeller with {len(anchor_points)} validated anchor points")

            if not anchor_points:
                logger.warning(f"[CurveSynthesizer] No anchor points provided for {impeller_diameter}mm")
                return None

            # Extract flows and heads from anchor points
            flows = [point["flow"] for point in anchor_points]
            heads = [point["head"] for point in anchor_points]

            # Sort by flow to ensure proper curve progression
            sorted_pairs = sorted(zip(flows, heads))
            flows, heads = zip(*sorted_pairs)

            # Determine polynomial degree (2nd or 3rd degree typically works well)
            poly_degree = min(3, len(anchor_points) - 1)

            # Fit polynomial to anchor points
            coefficients = np.polyfit(flows, heads, poly_degree)
            polynomial = np.poly1d(coefficients)

            # Generate smooth curve points
            flow_min, flow_max = min(flows), max(flows)
            smooth_flows = np.linspace(flow_min, flow_max, self.default_point_density)
            smooth_heads = polynomial(smooth_flows)

            # Ensure no negative heads (physical constraint)
            smooth_heads = np.maximum(smooth_heads, 0)

            # Extract efficiency and NPSH data from anchor points if available
            efficiency_data = []
            npsh_data = []

            for point in anchor_points:
                if "efficiency" in point and point["efficiency"] > 0:
                    efficiency_data.append(point["efficiency"])
                if "npsh" in point and point["npsh"] > 0:
                    npsh_data.append(point["npsh"])
                elif "npshr" in point and point["npshr"] > 0:
                    npsh_data.append(point["npshr"])

            # Generate efficiency and NPSH curves if we have anchor data
            smooth_efficiency = []
            smooth_npsh = []

            if len(efficiency_data) >= 3:
                # Fit efficiency curve (bell-shaped)
                eff_coeffs = np.polyfit(flows, efficiency_data, min(2, len(efficiency_data)-1))
                eff_poly = np.poly1d(eff_coeffs)
                smooth_efficiency = np.maximum(eff_poly(smooth_flows), 0).tolist()

            if len(npsh_data) >= 3:
                # Fit NPSH curve (typically increasing)
                npsh_coeffs = np.polyfit(flows, npsh_data, min(2, len(npsh_data)-1))
                npsh_poly = np.poly1d(npsh_coeffs)
                smooth_npsh = np.maximum(npsh_poly(smooth_flows), 0).tolist()

            # Build synthesized curve data structure
            synthesized_curve = {
                "impeller_diameter_mm": impeller_diameter,
                "curve_index": 0,  # Will be set by caller
                "is_selected": False,  # Will be determined by selection logic
                "flow_data": smooth_flows.tolist(),
                "head_data": smooth_heads.tolist(),
                "efficiency_data": smooth_efficiency,
                "power_data": [],      # Will be populated if power data available
                "npshr_data": smooth_npsh,
                "synthesis_metadata": {
                    "anchor_point_count": len(anchor_points),
                    "polynomial_degree": poly_degree,
                    "flow_range": [flow_min, flow_max],
                    "synthesis_method": "polynomial_fitting",
                    "has_efficiency": len(smooth_efficiency) > 0,
                    "has_npsh": len(smooth_npsh) > 0
                }
            }

            logger.info(f"Synthesized curve for {impeller_diameter}mm: {len(anchor_points)} anchors → {self.default_point_density} smooth points")
            return synthesized_curve

        except Exception as e:
            logger.error(f"Failed to synthesize curve for {curve_data.get('impellerDiameter')}: {str(e)}")
            return None

    def _synthesize_efficiency_contour(self, contour_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert efficiency contour anchor points to smooth contour boundary

        Args:
            contour_data: Efficiency value and anchor points defining contour

        Returns:
            Synthesized efficiency contour for overlay on charts
        """
        try:
            efficiency_value = contour_data.get("efficiency")
            anchor_points = contour_data.get("anchorPoints", [])

            if len(anchor_points) < 3:
                logger.warning(f"Insufficient anchor points for efficiency contour {efficiency_value}%")
                return None

            # Extract flows and heads
            flows = [point["flow"] for point in anchor_points]
            heads = [point["head"] for point in anchor_points]

            # For contours, we typically want to create a closed boundary
            # Use spline interpolation for smooth contour boundaries
            from scipy.interpolate import make_interp_spline

            # Sort points by flow for proper interpolation
            sorted_pairs = sorted(zip(flows, heads))
            flows, heads = zip(*sorted_pairs)

            # Create smooth contour boundary
            flows_array = np.array(flows)
            heads_array = np.array(heads)

            # Generate more points for smooth contour
            contour_resolution = 20
            flow_smooth = np.linspace(flows_array.min(), flows_array.max(), contour_resolution)

            # Use spline interpolation if scipy available, otherwise polynomial
            try:
                spline = make_interp_spline(flows_array, heads_array, k=min(3, len(flows)-1))
                head_smooth = spline(flow_smooth)
            except ImportError:
                # Fallback to polynomial if scipy not available
                poly_degree = min(2, len(flows) - 1)
                coefficients = np.polyfit(flows, heads, poly_degree)
                polynomial = np.poly1d(coefficients)
                head_smooth = polynomial(flow_smooth)

            return {
                "efficiency": efficiency_value,
                "contour_points": [
                    {"flow": float(f), "head": float(h)} 
                    for f, h in zip(flow_smooth, head_smooth)
                ],
                "anchor_count": len(anchor_points)
            }

        except Exception as e:
            logger.error(f"Failed to synthesize efficiency contour {contour_data.get('efficiency')}%: {str(e)}")
            return None

    def validate_synthesized_curve(self, curve_data: Dict[str, Any], coordinate_system: Dict[str, Any]) -> bool:
        """
        Validate that synthesized curve respects coordinate system boundaries

        Args:
            curve_data: Synthesized curve data
            coordinate_system: Coordinate bounds from layout analysis

        Returns:
            True if curve is valid, False otherwise
        """
        try:
            flows = curve_data.get("flow_data", [])
            heads = curve_data.get("head_data", [])

            if not flows or not heads:
                return False

            # Get coordinate bounds
            x_axis = coordinate_system.get("sharedXAxis", {})
            head_chart = next((c for c in coordinate_system.get("charts", []) if c["chartName"] == "Head"), {})
            y_axis = head_chart.get("yAxis", {})

            flow_min, flow_max = x_axis.get("min", 0), x_axis.get("max", 2000)
            head_min, head_max = y_axis.get("min", 0), y_axis.get("max", 35)

            # Check bounds
            if min(flows) < flow_min or max(flows) > flow_max:
                logger.warning(f"Flow values outside bounds: {min(flows)}-{max(flows)} vs {flow_min}-{flow_max}")
                return False

            if min(heads) < head_min or max(heads) > head_max:
                logger.warning(f"Head values outside bounds: {min(heads)}-{max(heads)} vs {head_min}-{head_max}")
                return False

            return True

        except Exception as e:
            logger.error(f"Curve validation failed: {str(e)}")
            return False