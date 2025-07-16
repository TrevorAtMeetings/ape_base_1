import os
import base64
import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryStage(Enum):
    DOCUMENT_ANALYSIS = "document_analysis"
    PUMP_DETAILS = "pump_details"
    CURVE_EXTRACTION = "curve_extraction"
    BEP_IDENTIFICATION = "bep_identification"
    VALIDATION = "validation"

@dataclass
class QueryResult:
    success: bool
    data: Optional[Dict] = None
    error_message: Optional[str] = None
    confidence: float = 0.0
    processing_time: float = 0.0

@dataclass
class ExtractionContext:
    """Context that flows between pipeline stages"""
    pdf_path: str
    base64_images: List[str]
    axis_definitions: Optional[Dict] = None
    pump_details: Optional[Dict] = None
    coordinate_system: Optional[Dict] = None
    stage_images: Optional[Dict] = None

class AIQueryManager:
    """
    Enhanced AI Query Manager with true pipeline architecture and context passing
    """

    STAGE_MODELS = {
        QueryStage.DOCUMENT_ANALYSIS: "gpt-4o",
        QueryStage.PUMP_DETAILS: "gpt-4o",
        QueryStage.CURVE_EXTRACTION: "gpt-4o",
        QueryStage.BEP_IDENTIFICATION: "gpt-4o",
        QueryStage.VALIDATION: "gpt-4o"
    }

    STAGE_TIMEOUTS = {
        QueryStage.DOCUMENT_ANALYSIS: 60,
        QueryStage.PUMP_DETAILS: 45,
        QueryStage.CURVE_EXTRACTION: 90,
        QueryStage.BEP_IDENTIFICATION: 45,
        QueryStage.VALIDATION: 30
    }

    def __init__(self, client):
        self.client = client
        self.context = None
        self.results = {}

    def execute_extraction_pipeline(self, pdf_path: str, base64_images: List[str]) -> Dict[str, Any]:
        """
        Execute the complete 5-stage extraction pipeline with context passing
        """
        logger.info("[AI Query Manager] Starting enhanced pipeline with context passing")

        # Initialize extraction context
        self.context = ExtractionContext(
            pdf_path=pdf_path,
            base64_images=base64_images,
            stage_images={
                QueryStage.DOCUMENT_ANALYSIS: base64_images,
                QueryStage.PUMP_DETAILS: base64_images,
                QueryStage.CURVE_EXTRACTION: base64_images[:1],  # Use first image for curve extraction
                QueryStage.BEP_IDENTIFICATION: base64_images[:1],
                QueryStage.VALIDATION: base64_images
            }
        )

        pipeline_start = time.time()

        # Stage 1: Document Analysis - Establish coordinate system
        logger.info("[AI Query Manager] Stage 1: Document Analysis")
        doc_result = self._execute_document_analysis()
        self.results[QueryStage.DOCUMENT_ANALYSIS] = doc_result

        if doc_result.success and doc_result.data:
            # Pass coordinate system to context for subsequent stages
            self.context.coordinate_system = doc_result.data.get("coordinateSystem")
            self.context.axis_definitions = self.context.coordinate_system
            logger.info(f"[AI Query Manager] Coordinate system established: {self.context.coordinate_system}")
        else:
            logger.warning("[AI Query Manager] Document analysis failed, proceeding without coordinate system")

        # Stage 2: Pump Details Extraction
        logger.info("[AI Query Manager] Stage 2: Pump Details Extraction")
        pump_result = self._execute_pump_details()
        self.results[QueryStage.PUMP_DETAILS] = pump_result

        if pump_result.success and pump_result.data:
            # Pass pump details to context
            self.context.pump_details = pump_result.data
            logger.info(f"[AI Query Manager] Pump details extracted: {pump_result.data.get('pumpDetails', {}).get('pumpModel', 'Unknown')}")

        # Stage 3: Curve Extraction with Context
        logger.info("[AI Query Manager] Stage 3: Context-Aware Curve Extraction")
        try:
            curve_result = self._execute_curve_extraction(self.context.coordinate_system)
            self.results[QueryStage.CURVE_EXTRACTION] = curve_result

            if not curve_result.success:
                logger.warning(f"[AI Query Manager] Curve extraction failed: {curve_result.error_message}")
                # Continue with partial data instead of failing completely
                curve_result = QueryResult(success=True, data={"performanceAnchorPoints": []}, confidence=0.1)
                self.results[QueryStage.CURVE_EXTRACTION] = curve_result
        except Exception as e:
            logger.error(f"[AI Query Manager] Curve extraction error: {e}")
            # Create empty result to allow pipeline continuation
            curve_result = QueryResult(success=True, data={"performanceAnchorPoints": []}, confidence=0.0)
            self.results[QueryStage.CURVE_EXTRACTION] = curve_result

        # Stage 4: BEP Identification with Context
        logger.info("[AI Query Manager] Stage 4: BEP Identification")
        bep_result = self._execute_bep_identification(self.context.coordinate_system)
        self.results[QueryStage.BEP_IDENTIFICATION] = bep_result

        # Stage 5: Validation with Full Context
        logger.info("[AI Query Manager] Stage 5: Cross-Validation")
        validation_result = self._execute_validation()
        self.results[QueryStage.VALIDATION] = validation_result

        # Combine results using context
        combined_data = self._combine_pipeline_results()

        # Add pipeline metrics
        processing_time = time.time() - pipeline_start
        combined_data["_qualityMetrics"] = {
            "overallConfidence": self._calculate_overall_confidence(),
            "processingTime": processing_time,
            "stageResults": {stage.value: result.confidence for stage, result in self.results.items()},
            "pipelineMethod": "context_aware_specialist_queries"
        }

        logger.info(f"[AI Query Manager] Pipeline completed in {processing_time:.2f}s")
        return combined_data

    def _execute_document_analysis(self) -> QueryResult:
        """Stage 1: Analyze document structure and coordinate system"""
        try:
            from .specialist_prompts import SpecialistPrompts
            prompt = SpecialistPrompts.get_document_analysis_prompt()
            images = self.context.stage_images[QueryStage.DOCUMENT_ANALYSIS]

            data = self._make_api_call(QueryStage.DOCUMENT_ANALYSIS, prompt, images)

            # Validate coordinate system structure
            if "coordinateSystem" in data:
                coord_system = data["coordinateSystem"]
                confidence = 0.9 if self._validate_coordinate_system(coord_system) else 0.6
            else:
                confidence = 0.3

            return QueryResult(
                success=True,
                data=data,
                confidence=confidence,
                processing_time=0.0  # Will be updated by _make_api_call
            )

        except Exception as e:
            logger.error(f"[AI Query Manager] Document analysis failed: {e}")
            return QueryResult(
                success=False,
                error_message=str(e),
                confidence=0.0
            )

    def _execute_pump_details(self) -> QueryResult:
        """Stage 2: Extract pump specifications and metadata"""
        try:
            from .specialist_prompts import SpecialistPrompts
            prompt = SpecialistPrompts.get_pump_info_extraction_prompt()
            images = self.context.stage_images[QueryStage.PUMP_DETAILS]

            data = self._make_api_call(QueryStage.PUMP_DETAILS, prompt, images)

            # Calculate confidence based on completeness
            pump_details = data.get("pumpDetails", {})
            required_fields = ["pumpModel", "manufacturer", "pumpType"]
            found_fields = sum(1 for field in required_fields if pump_details.get(field))
            confidence = found_fields / len(required_fields)

            return QueryResult(
                success=True,
                data=data,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"[AI Query Manager] Pump details extraction failed: {e}")
            return QueryResult(
                success=False,
                error_message=str(e),
                confidence=0.0
            )

    def _execute_curve_extraction(self, coordinate_system: Optional[Dict]) -> QueryResult:
        """Stage 3: Extract curve anchor points with coordinate system context"""
        try:
            from .specialist_prompts import SpecialistPrompts
            # Pass coordinate system context to the prompt
            prompt = SpecialistPrompts.get_head_efficiency_chart_prompt(coordinate_system)
            images = self.context.stage_images[QueryStage.CURVE_EXTRACTION]

            if coordinate_system:
                x_axis = coordinate_system.get('sharedXAxis', {})
                # Look for Head chart in the charts array
                head_chart = None
                charts = coordinate_system.get('charts', [])
                for chart in charts:
                    if chart.get('chartName', '').lower() == 'head':
                        head_chart = chart
                        break

                if head_chart:
                    left_y = head_chart.get('yAxis', {})
                else:
                    left_y = coordinate_system.get('leftYAxis', {})

                right_y = coordinate_system.get('rightYAxis', {})

                # Build coordinate context safely
                x_min = x_axis.get('min', 0)
                x_max = x_axis.get('max', 2000)
                x_unit = x_axis.get('unit', 'm³/hr')
                y_min = left_y.get('min', 0)
                y_max = left_y.get('max', 35)
                y_unit = left_y.get('unit', 'm')
                r_min = right_y.get('min', 0)
                r_max = right_y.get('max', 100)
                r_unit = right_y.get('unit', '%')

                coordinate_context = f"""
Use the following coordinate system for accurate data extraction:
X-axis (Flow Rate): min={x_min}, max={x_max}, unit={x_unit}
Y-axis (Head): min={y_min}, max={y_max}, unit={y_unit}
Right-Y-axis (Efficiency): min={r_min}, max={r_max}, unit={r_unit}
"""
                prompt += coordinate_context

            data = self._make_api_call(QueryStage.CURVE_EXTRACTION, prompt, images)

            # Validate extracted anchor points
            anchor_points = data.get("performanceAnchorPoints", [])
            num_curves = len(anchor_points)
            total_points = sum(len(curve.get("anchorPoints", [])) for curve in anchor_points)

            # Log curve extraction details
            logger.info(f"[AI Query Manager] Extracted {num_curves} curves with {total_points} total anchor points")
            for i, curve in enumerate(anchor_points):
                impeller = curve.get("impellerDiameter", 0)
                points_count = len(curve.get("anchorPoints", []))
                logger.info(f"[AI Query Manager] Curve {i+1}: {impeller}mm impeller, {points_count} anchor points")

            # Higher confidence if we have multiple curves with good density
            if num_curves >= 2 and total_points >= 18:  # 2+ curves with 9 points each
                confidence = 0.9
            elif num_curves >= 2 and total_points >= 12:  # 2+ curves with 6+ points each
                confidence = 0.7
            elif total_points >= 9:  # At least one complete curve
                confidence = 0.5
            else:
                confidence = 0.3
                logger.warning(f"[AI Query Manager] Low curve extraction: only {num_curves} curves, {total_points} points")

            return QueryResult(
                success=True,
                data=data,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"[AI Query Manager] Curve extraction failed: {e}")
            return QueryResult(
                success=False,
                error_message=str(e),
                confidence=0.0
            )

    def _execute_bep_identification(self, coordinate_system: Optional[Dict]) -> QueryResult:
        """Stage 4: Identify Best Efficiency Points"""
        try:
            from .specialist_prompts import SpecialistPrompts
            prompt = SpecialistPrompts.get_bep_identification_prompt()
            images = self.context.stage_images[QueryStage.BEP_IDENTIFICATION]

            data = self._make_api_call(QueryStage.BEP_IDENTIFICATION, prompt, images)

            # Validate BEP markers
            bep_markers = data.get("bepMarkers", [])
            main_bep = data.get("mainBEP", {})

            confidence = 0.8 if (bep_markers and main_bep.get("bepFlow", 0) > 0) else 0.4

            return QueryResult(
                success=True,
                data=data,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"[AI Query Manager] BEP identification failed: {e}")
            return QueryResult(
                success=False,
                error_message=str(e),
                confidence=0.0
            )

    def _execute_validation(self) -> QueryResult:
        """Stage 5: Cross-validate all extracted data"""
        try:
            from .specialist_prompts import SpecialistPrompts

            # Create validation context from all previous results
            validation_context = {
                "coordinate_system": self.context.coordinate_system,
                "pump_details": self.context.pump_details,
                "curve_data": self.results.get(QueryStage.CURVE_EXTRACTION, {}).data,
                "bep_data": self.results.get(QueryStage.BEP_IDENTIFICATION, {}).data
            }

            prompt = SpecialistPrompts.get_cross_validation_prompt()
            images = self.context.stage_images[QueryStage.VALIDATION]

            data = self._make_api_call(QueryStage.VALIDATION, prompt, images)

            # Validation confidence based on consistency checks
            validation_results = data.get("validationResults", {})
            overall_passed = validation_results.get("physicsValidation", {}).get("passed", False)
            confidence = 0.9 if overall_passed else 0.6

            return QueryResult(
                success=True,
                data=data,
                confidence=confidence
            )

        except Exception as e:
            logger.warning(f"[AI Query Manager] Validation failed (non-critical): {e}")
            return QueryResult(
                success=False,
                error_message=str(e),
                confidence=0.5  # Validation failure doesn't invalidate extraction
            )

    def _make_api_call(self, stage: QueryStage, prompt: str, images: List[str]) -> Dict:
        """Generic helper to make API calls with validation and error handling"""
        model = self.STAGE_MODELS[stage]
        timeout = self.STAGE_TIMEOUTS[stage]

        # Prepare content
        content = [{"type": "text", "text": prompt}]

        for img_data in images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_data}",
                    "detail": "high"
                }
            })

        try:
            call_start = time.time()

            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
                max_tokens=3500,
                temperature=0.1,
                timeout=timeout
            )

            call_time = time.time() - call_start
            response_text = response.choices[0].message.content.strip()

            logger.info(f"[AI Query Manager] {stage.value} API call completed in {call_time:.2f}s")

            # Validate and clean response
            cleaned_response = self._clean_response(response_text)

            # Parse JSON
            try:
                data = json.loads(cleaned_response)
                return data
            except json.JSONDecodeError as e:
                logger.error(f"[AI Query Manager] JSON parsing failed for {stage.value}: {e}")
                raise ValueError(f"Invalid JSON response from {stage.value}: {e}")

        except Exception as e:
            logger.error(f"[AI Query Manager] API call failed for {stage.value}: {e}")
            raise

    def _clean_response(self, response_text: str) -> str:
        """Clean and validate API response"""
        if not response_text or len(response_text.strip()) < 10:
            raise ValueError("Response is empty or too short")

        # Remove markdown formatting
        cleaned = response_text.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Validate JSON structure
        if not (cleaned.startswith('{') and cleaned.endswith('}')):
            raise ValueError("Response doesn't contain valid JSON structure")

        return cleaned

    def _validate_coordinate_system(self, coord_system: Dict) -> bool:
        """Validate coordinate system structure"""
        try:
            shared_x = coord_system.get("sharedXAxis", {})
            charts = coord_system.get("charts", [])

            # Check X-axis
            if not (shared_x.get("min", 0) < shared_x.get("max", 0)):
                return False

            # Check each chart Y-axis
            for chart in charts:
                y_axis = chart.get("yAxis", {})
                if not (y_axis.get("min", 0) < y_axis.get("max", 0)):
                    return False

            return True
        except:
            return False

    def _combine_pipeline_results(self) -> Dict[str, Any]:
        """Combine results from all pipeline stages into final extraction data"""
        combined_data = {}

        # Add pump details
        if QueryStage.PUMP_DETAILS in self.results and self.results[QueryStage.PUMP_DETAILS].success:
            pump_data = self.results[QueryStage.PUMP_DETAILS].data
            combined_data.update(pump_data)

        # Add coordinate system
        if self.context.coordinate_system:
            combined_data["coordinateSystem"] = self.context.coordinate_system

        # Process curve data through synthesizer
        if QueryStage.CURVE_EXTRACTION in self.results and self.results[QueryStage.CURVE_EXTRACTION].success:
            from .curve_synthesizer import CurveSynthesizer
            synthesizer = CurveSynthesizer()

            anchor_data = self.results[QueryStage.CURVE_EXTRACTION].data

            # NEW VALIDATION STEP (moved here to validate before synthesis)
            if not self._validate_anchor_points(anchor_data):
                logger.error("[AI Query Manager] CRITICAL FAILURE: Anchor point extraction failed or returned invalid data. Aborting pipeline.")
                return self._create_fallback_result("Anchor point extraction failed")

            synthesized_data = synthesizer.synthesize_performance_curves(anchor_data)

            # Validate synthesized curves
            if synthesized_data and self._validate_synthesized_curves(synthesized_data.get("curves", [])):
                combined_data["curves"] = synthesized_data.get("curves", [])
                combined_data["efficiency_contours"] = synthesized_data.get("efficiency_contours", [])
            else:
                 logger.error("[AI Query Manager] CRITICAL FAILURE: Curve synthesis failed or produced invalid results. Aborting pipeline.")
                 return self._create_fallback_result("Curve synthesis failed validation")

        # Add BEP data
        if QueryStage.BEP_IDENTIFICATION in self.results and self.results[QueryStage.BEP_IDENTIFICATION].success:
            bep_data = self.results[QueryStage.BEP_IDENTIFICATION].data
            combined_data["bepMarkers"] = bep_data.get("bepMarkers", [])
            if "mainBEP" in bep_data:
                combined_data["mainBEP"] = bep_data["mainBEP"]

        return combined_data

    def _calculate_overall_confidence(self) -> float:
        """Calculate overall pipeline confidence"""
        if not self.results:
            return 0.0

        confidences = [result.confidence for result in self.results.values() if result.success]
        if not confidences:
            return 0.0

        # Weighted average with more weight on critical stages
        weights = {
            QueryStage.DOCUMENT_ANALYSIS: 0.15,
            QueryStage.PUMP_DETAILS: 0.20,
            QueryStage.CURVE_EXTRACTION: 0.40,  # Most critical
            QueryStage.BEP_IDENTIFICATION: 0.20,
            QueryStage.VALIDATION: 0.05
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for stage, result in self.results.items():
            if result.success:
                weight = weights.get(stage, 0.1)
                weighted_sum += result.confidence * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _validate_synthesized_curves(self, curves: List[Dict]) -> bool:
        """Validate that synthesized curves contain reasonable data"""
        if not curves or not isinstance(curves, list):
            logger.error("Validation failed: No curves or invalid curve format")
            return False

        for curve in curves:
            if not isinstance(curve, dict):
                logger.error("Validation failed: Curve is not a dictionary")
                return False

            # Check for required fields
            required_fields = ['impeller_diameter_mm', 'flow_data', 'head_data', 'efficiency_data']
            for field in required_fields:
                if field not in curve:
                    logger.error(f"Validation failed: Missing required field '{field}' in curve")
                    return False

            # Check data arrays have same length and reasonable values
            flow_data = curve['flow_data']
            head_data = curve['head_data']

            if not isinstance(flow_data, list) or not isinstance(head_data, list):
                logger.error("Validation failed: Flow or head data is not a list")
                return False

            if len(flow_data) != len(head_data) or len(flow_data) < 5:
                logger.error(f"Validation failed: Data length mismatch or insufficient points: flow={len(flow_data)}, head={len(head_data)}")
                return False

            # Check for reasonable value ranges
            if max(flow_data) <= 0 or max(head_data) <= 0:
                logger.error("Validation failed: Flow or head data contains no positive values")
                return False

        logger.info("Synthesized curves validation passed.")
        return True

    def _create_fallback_result(self, error_message: str) -> Dict[str, Any]:
        """Create fallback result when pipeline fails"""
        return {
            "pumpDetails": {"pumpModel": "Unknown", "manufacturer": "Unknown"},
            "curves": [],
            "bepMarkers": [],
            "_qualityMetrics": {
                "overallConfidence": 0.0,
                "processingTime": 0.0,
                "stageResults": {},
                "error": error_message
            }
        }

    def _validate_anchor_points(self, data: Dict) -> bool:
        """Validates that the AI returned usable anchor points before continuing pipeline."""
        if not data or "performanceAnchorPoints" not in data:
            logger.error("[Validation] FAILED: 'performanceAnchorPoints' key is missing.")
            return False

        anchor_groups = data["performanceAnchorPoints"]
        if not isinstance(anchor_groups, list) or not anchor_groups:
            logger.error("[Validation] FAILED: 'performanceAnchorPoints' is not a non-empty list.")
            return False

        # Check each group for structure and minimum points
        valid_groups = 0
        for i, group in enumerate(anchor_groups):
            if "impellerDiameter" not in group or "anchorPoints" not in group:
                logger.warning(f"[Validation] Group {i} missing 'impellerDiameter' or 'anchorPoints'.")
                continue

            anchor_points = group["anchorPoints"]
            if not isinstance(anchor_points, list) or len(anchor_points) < 3:
                logger.warning(f"[Validation] Group {i} has insufficient anchor points ({len(anchor_points) if isinstance(anchor_points, list) else 0}).")
                continue

            # Validate point structure
            valid_points = 0
            for point in anchor_points:
                if isinstance(point, dict) and "flow" in point and "head" in point:
                    valid_points += 1

            if valid_points >= 3:
                valid_groups += 1
                logger.info(f"[Validation] Group {i} (diameter: {group.get('impellerDiameter')}) passed with {valid_points} valid points.")

        if valid_groups == 0:
            logger.error("[Validation] FAILED: No valid anchor point groups found.")
            return False

        logger.info(f"[Validation] PASSED: {valid_groups} valid anchor point groups found.")
        return True

    def _create_extraction_result(self, success: bool, data: Dict[str, Any] = None, 
                                error: str = None, stage: QueryStage = None) -> ExtractionResult:
        """Create extraction result with success, data, error and stage"""
        return QueryResult(
            success=success,
            data=data,
            error_message=error,
            confidence=0.0,
            processing_time=0.0
        )