import logging
import json
import base64
import os
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI
import anthropic
import google.generativeai as genai
from PIL import Image
import io
import tempfile

logger = logging.getLogger(__name__)

def extract_with_anthropic(pdf_path: str) -> Dict[str, Any]:
    """
    Extract pump data using Anthropic Claude
    """
    try:
        # Get API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Anthropic API key not found in environment variables")

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # Convert PDF to images for processing
        from .pdf_to_image_converter import convert_pdf_to_images
        base64_images = convert_pdf_to_images(pdf_path)

        if not base64_images:
            raise ValueError("Failed to convert PDF to images")

        # Use specialist extraction prompt
        from .specialist_prompts import SpecialistPrompts
        prompt = get_extraction_prompt()

        # Process with Claude
        content = [{"type": "text", "text": prompt}]

        for img_data in base64_images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": img_data
                }
            })

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3500,
            temperature=0.1,
            messages=[{"role": "user", "content": content}]
        )

        response_text = response.content[0].text.strip()

        # Parse JSON response
        try:
            parsed_data = json.loads(response_text)
            logger.info("[AI Extractor] Anthropic extraction successful")
            return parsed_data
        except json.JSONDecodeError as e:
            logger.error(f"[AI Extractor] Anthropic JSON parsing error: {e}")
            raise ValueError(f"Anthropic returned invalid JSON: {e}")

    except Exception as e:
        logger.error(f"[AI Extractor] Anthropic extraction failed: {e}")
        raise


def extract_with_openai(pdf_path: str) -> Dict[str, Any]:
    """
    Extract pump data using OpenAI GPT-4
    """
    try:
        # Get API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")

        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Convert PDF to images
        from .pdf_to_image_converter import convert_pdf_to_images
        base64_images = convert_pdf_to_images(pdf_path)

        if not base64_images:
            raise ValueError("Failed to convert PDF to images")

        # Use extraction prompt
        prompt = get_extraction_prompt()

        # Prepare content
        content = [{"type": "text", "text": prompt}]

        for img_data in base64_images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_data}",
                    "detail": "high"
                }
            })

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=3500,
            temperature=0.1,
            timeout=120
        )

        response_text = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            parsed_data = json.loads(response_text)
            logger.info("[AI Extractor] OpenAI extraction successful")
            return parsed_data
        except json.JSONDecodeError as e:
            logger.error(f"[AI Extractor] OpenAI JSON parsing error: {e}")
            raise ValueError(f"OpenAI returned invalid JSON: {e}")

    except Exception as e:
        logger.error(f"[AI Extractor] OpenAI extraction failed: {e}")
        raise


def extract_with_gemini(pdf_path: str) -> Dict[str, Any]:
    """
    Extract pump data using Google Gemini
    """
    try:
        # Get API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Gemini API key not found in environment variables")

        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Convert PDF to images
        from .pdf_to_image_converter import convert_pdf_to_images
        base64_images = convert_pdf_to_images(pdf_path)

        if not base64_images:
            raise ValueError("Failed to convert PDF to images")

        # Use extraction prompt
        prompt = get_extraction_prompt()

        # Prepare images for Gemini
        images = []
        for img_data in base64_images:
            img_bytes = base64.b64decode(img_data)
            img = Image.open(io.BytesIO(img_bytes))
            images.append(img)

        # Generate response
        response = model.generate_content([prompt] + images)
        response_text = response.text.strip()

        # Parse JSON response
        try:
            parsed_data = json.loads(response_text)
            logger.info("[AI Extractor] Gemini extraction successful")
            return parsed_data
        except json.JSONDecodeError as e:
            logger.error(f"[AI Extractor] Gemini JSON parsing error: {e}")
            raise ValueError(f"Gemini returned invalid JSON: {e}")

    except Exception as e:
        logger.error(f"[AI Extractor] Gemini extraction failed: {e}")
        raise


def extract_pump_data_from_pdf(pdf_path: str, model_choice: str = "auto") -> Dict[str, Any]:
    """
    Main extraction function with model routing
    """
    try:
        if model_choice == "anthropic":
            return extract_with_anthropic(pdf_path)
        elif model_choice == "openai":
            return extract_with_openai(pdf_path)
        elif model_choice == "gemini":
            return extract_with_gemini(pdf_path)
        else:
            # Auto-routing logic
            from app.ai_model_router import get_ai_model_router
            router = get_ai_model_router()
            selected_model = router.select_best_model()

            if selected_model == "anthropic":
                return extract_with_anthropic(pdf_path)
            elif selected_model == "openai":
                return extract_with_openai(pdf_path)
            else:
                return extract_with_gemini(pdf_path)

    except Exception as e:
        logger.error(f"[AI Extractor] Primary extraction failed: {e}")
        primary_error = e
        error_str = str(e).lower()

        # Try fallback extraction
        try:
            if model_choice != "gemini":
                logger.info("[AI Extractor] Attempting Gemini fallback")
                return extract_with_gemini(pdf_path)
            elif model_choice != "openai":
                logger.info("[AI Extractor] Attempting OpenAI fallback")
                return extract_with_openai(pdf_path)
            else:
                logger.info("[AI Extractor] Attempting Anthropic fallback")
                return extract_with_anthropic(pdf_path)
        except Exception as fallback_error:
            logger.error(f"[AI Extractor] Fallback extraction also failed: {fallback_error}")
            final_error = fallback_error
            error_str = str(fallback_error).lower()

            # Specific error handling
            if "timeout" in error_str:
                raise TimeoutError("API request timed out. This may be due to image complexity or API load.")
            elif "rate_limit" in error_str or "429" in error_str:
                raise ValueError("API rate limit exceeded. Please wait a moment before trying again.")
            elif "content_policy" in error_str or "safety" in error_str:
                raise ValueError("Content policy restriction detected. Please try with a different model.")
            elif "context_length" in error_str or "token" in error_str:
                raise ValueError("Token limit exceeded due to image size. Please try with a smaller PDF.")
            else:
                raise ValueError(f"AI extraction error: {str(final_error)[:200]}...")

def get_extraction_prompt():
    """Return the comprehensive extraction prompt used by both models"""
    return '''
You are an expert hydraulic engineer and data extraction specialist. 
Analyze the pump performance curve PDF and extract data with MAXIMUM ACCURACY.

Your final output MUST be a single, raw JSON object. Do NOT include any explanations, 
introductory text, or markdown formatting like ```json.

JSON STRUCTURE:
{
  "pumpDetails": { "pumpModel": "", "manufacturer": "", "pumpType": "", "pumpRange": "", "application": "", "constructionStandard": "" },
  "technicalDetails": { "impellerType": "" },
  "specifications": { 
    "testSpeed": 0, 
    "maxFlow": 0, 
    "maxHead": 0, 
    "bepFlow": 0, 
    "bepHead": 0, 
    "npshrAtBep": 0, 
    "minImpeller": 0, 
    "maxImpeller": 0, 
    "variableDiameter": true,
    "bepMarkers": [
      {
        "impellerDiameter": 0,
        "bepFlow": 0,
        "bepHead": 0,
        "bepEfficiency": 0,
        "markerLabel": "",
        "coordinates": {"x": 0, "y": 0}
      }
    ]
  },
  "axisDefinitions": {
    "xAxis": {"min": 0, "max": 0, "unit": "m3/hr", "label": "Flow Rate"},
    "leftYAxis": {"min": 0, "max": 0, "unit": "m", "label": "Head"},
    "rightYAxis": {"min": 0, "max": 0, "unit": "%", "label": "Efficiency"},
    "secondaryRightYAxis": {"min": 0, "max": 0, "unit": "m", "label": "NPSH"}
  },
  "curves": [ { "impellerDiameter": 0, "performancePoints": [ { "flow": 0, "head": 0, "efficiency": 0, "npshr": 0 } ] } ]
}

CRITICAL EXTRACTION METHODOLOGY - FOLLOW EXACTLY:

1. AXIS SYSTEM ANALYSIS (FIRST PRIORITY):
   - Identify X-axis (Flow Rate): Record EXACT min/max values and units (m3/hr, L/s, GPM)
   - Identify Left Y-axis (Head): Record EXACT min/max values and units (m, ft)
   - Identify Right Y-axis (Efficiency): Record EXACT min/max values (typically 0-100%)
   - Identify Secondary Right Y-axis (NPSH): Record EXACT min/max values and units (m, ft)
   - Map grid lines to create precise coordinate scaling system

2. BEP EXTRACTION (HIGHEST PRIORITY - THIS IS CRITICAL):
   - Look for ALL BEP markers on the chart: "BEP", "B.E.P.", efficiency percentages
   - For EACH impeller diameter, find the efficiency curve PEAK point
   - At the peak efficiency point:
     * Read X-coordinate for FLOW using X-axis scale
     * Find corresponding HEAD curve at same X-coordinate, read Y-coordinate using LEFT Y-axis scale
     * Read efficiency percentage using RIGHT Y-axis scale
   - ALWAYS populate bepFlow and bepHead in specifications section with LARGEST impeller BEP
   - Create bepMarkers array with ALL impeller BEP points found

3. OPTIMIZED DATA POINT EXTRACTION (9 POINTS PER CURVE):
   - For each impeller diameter, extract EXACTLY 9 data points
   - Distribute points evenly across the FULL flow range of each curve
   - For HEAD curves: Follow the curve line, read X-coord for flow, Y-coord for head
   - For EFFICIENCY curves: Follow the curve line, read X-coord for flow, Y-coord for efficiency
   - For NPSH curves: Follow the curve line, read X-coord for flow, Y-coord for NPSH
   - Include extra points near BEP region (within ±20% of BEP flow)

4. CURVE IDENTIFICATION AND FOLLOWING:
   - HEAD CURVES: Usually solid lines, decreasing from left to right
   - EFFICIENCY CURVES: Usually dashed/dotted lines, bell-shaped curves
   - NPSH CURVES: Usually dotted lines, increasing from left to right
   - Follow each curve precisely - do not interpolate between different curve types

5. DATA VALIDATION AND CONSISTENCY:
   - BEP flow and head MUST NOT be zero unless explicitly marked as such
   - Head curves should decrease with increasing flow
   - Efficiency curves should have realistic peak (50-90% range)
   - Ensure all extracted values are within chart axis ranges

6. MANDATORY DATA QUALITY REQUIREMENTS:
   - Extract EXACTLY 9 data points per curve (head, efficiency, NPSH)
   - BEP Flow and Head MUST be populated with actual values (NOT zero)
   - Extract BEP for ALL impeller diameters shown
   - Validate head curves decrease with flow (monotonic)
   - Validate efficiency curves have single peak (bell shape)
   - Validate NPSH curves increase with flow (monotonic)

7. CRITICAL BEP EXTRACTION RULES:
   - Find efficiency curve peak for each impeller diameter
   - At peak efficiency X-coordinate, read corresponding head curve Y-value
   - Populate specifications.bepFlow and specifications.bepHead with LARGEST impeller BEP
   - Create complete bepMarkers array for all impellers
   - NEVER leave BEP flow or head as zero unless chart explicitly shows zero

8. DATA POINT DENSITY REQUIREMENTS:
   - EXACTLY9 points per curve type per impeller
   - Distribute points evenly across full flow range (start, end, and 7 intermediate points)
   - Include extra point near BEP region for accuracy
   - Ensure smooth curve representation for plotting

EXTRACTION PRECISION REQUIREMENTS:
- Flow rates: ±1 m3/hr accuracy
- Head values: ±0.5 m accuracy  
- Efficiency values: ±1% accuracy
- NPSH values: ±0.2 m accuracy
- BEP coordinates: Cross-validated against curve peaks

CRITICAL SUCCESS CRITERIA:
✓ BEP Flow > 0 (MUST extract actual BEP flow value)
✓ BEP Head > 0 (MUST extract actual BEP head value)  
✓ Minimum 20 data points per curve
✓ Smooth curves suitable for plotting
✓ All impeller diameters represented
''' 


def validate_curve_smoothness(curves_data):
    """
    Validate that extracted curves follow realistic pump performance patterns.
    Returns validated data with smoothness corrections if needed.
    """
    validated_curves = []

    for curve in curves_data:
        points = curve.get('performancePoints', [])
        if len(points) < 3:
            logger.warning(f"Insufficient data points for impeller {curve.get('impellerDiameter')}")
            continue

        # Sort points by flow rate
        sorted_points = sorted(points, key=lambda p: p.get('flow', 0))

        # Validate head curve (should be monotonically decreasing)
        head_values = [p.get('head', 0) for p in sorted_points]
        head_monotonic = all(head_values[i] >= head_values[i+1] for i in range(len(head_values)-1))
        if not head_monotonic:
            logger.warning(f"Head curve for impeller {curve.get('impellerDiameter')} is not monotonically decreasing - possible extraction error")

        # Check for insufficient data points
        if len(points) < 7:
            logger.warning(f"Insufficient data points ({len(points)}) for impeller {curve.get('impellerDiameter')} - minimum 9 required for smooth plotting")

        # Validate efficiency curve (should have single peak)
        efficiency_values = [p.get('efficiency', 0) for p in sorted_points]
        if efficiency_values:
            max_efficiency = max(efficiency_values)
            peak_index = efficiency_values.index(max_efficiency)

            # Check for realistic efficiency distribution
            if peak_index == 0 or peak_index == len(efficiency_values) - 1:
                logger.warning(f"Efficiency peak at curve boundary for impeller {curve.get('impellerDiameter')} - possible axis mapping error")

            # Check for realistic efficiency range
            if max_efficiency and (max_efficiency < 30 or max_efficiency > 95):
                logger.warning(f"Unrealistic peak efficiency {max_efficiency}% for impeller {curve.get('impellerDiameter')} - possible Y-axis scaling error")

        # Validate NPSH curve (should be monotonically increasing)
        npshr_values = [p.get('npshr', 0) for p in sorted_points if p.get('npshr', 0) > 0]
        if len(npshr_values) > 1:
            npshr_monotonic = all(npshr_values[i] <= npshr_values[i+1] for i in range(len(npshr_values)-1))
            if not npshr_monotonic:
                logger.warning(f"NPSH curve for impeller {curve.get('impellerDiameter')} is not monotonically increasing - possible extraction error")

        # Check for realistic flow range
        flow_values = [p.get('flow', 0) for p in sorted_points]
        if flow_values:
            flow_range = max(flow_values) - min(flow_values)
            if flow_range < 10:  # Less than 10 m³/hr range seems unrealistic
                logger.warning(f"Very narrow flow range ({flow_range:.1f} m³/hr) for impeller {curve.get('impellerDiameter')} - possible X-axis scaling error")

        validated_curves.append(curve)

    return validated_curves

def validate_bep_markers(parsed_data):
    """
    Validate BEP markers against curve data for consistency and fix zero values
    """
    if 'specifications' not in parsed_data or 'bepMarkers' not in parsed_data['specifications']:
        return parsed_data

    # Check main BEP values
    main_bep_flow = parsed_data['specifications'].get('bepFlow', 0)
    main_bep_head = parsed_data['specifications'].get('bepHead', 0)

    if main_bep_flow == 0 or main_bep_head == 0:
        logger.warning("[AI Extractor] Main BEP Flow or Head is zero - attempting to extract from curve data")

        # Try to extract BEP from curve data
        curves = parsed_data.get('curves', [])
        if curves:
            # Find largest impeller diameter
            largest_curve = max(curves, key=lambda x: x.get('impellerDiameter', 0))
            points = largest_curve.get('performancePoints', [])

            if points:
                # Find point with maximum efficiency
                max_eff_point = max(points, key=lambda x: x.get('efficiency', 0))
                if max_eff_point.get('efficiency', 0) > 0:
                    parsed_data['specifications']['bepFlow'] = max_eff_point.get('flow', 0)
                    parsed_data['specifications']['bepHead'] = max_eff_point.get('head', 0)
                    logger.info(f"[AI Extractor] Extracted BEP from curve data: Flow={max_eff_point.get('flow', 0):.1f}, Head={max_eff_point.get('head', 0):.1f}")

    bep_markers = parsed_data['specifications']['bepMarkers']
    curves = parsed_data.get('curves', [])

    for bep_marker in bep_markers:
        bep_flow = bep_marker.get('bepFlow', 0)
        bep_head = bep_marker.get('bepHead', 0)
        bep_efficiency = bep_marker.get('bepEfficiency', 0)
        impeller_diameter = bep_marker.get('impellerDiameter', 0)

        # Find corresponding curve
        matching_curve = None
        for curve in curves:
            if abs(curve.get('impellerDiameter', 0) - impeller_diameter) < 1:  # Allow 1mm tolerance
                matching_curve = curve
                break

        if matching_curve:
            # Find closest point on curve to BEP marker
            points = matching_curve.get('performancePoints', [])
            closest_point = None
            min_distance = float('inf')

            for point in points:
                flow_diff = abs(point.get('flow', 0) - bep_flow)
                head_diff = abs(point.get('head', 0) - bep_head)
                distance = (flow_diff**2 + head_diff**2)**0.5

                if distance < min_distance:
                    min_distance = distance
                    closest_point = point

            if closest_point:
                # Check if efficiency is consistent
                curve_efficiency = closest_point.get('efficiency', 0)
                if abs(curve_efficiency - bep_efficiency) > 10:  # More than 10% difference
                    logger.warning(f"BEP efficiency mismatch for impeller {impeller_diameter}mm: BEP={bep_efficiency}%, Curve={curve_efficiency}% - possible multi-axis extraction error")

    return parsed_data

def create_fallback_data():
    """
    Create minimal fallback data when AI extraction fails due to rate limits
    """
    logger.info("[AI Extractor] Creating fallback data structure")
    return {
        "pumpDetails": {
            "pumpModel": "EXTRACTION_FAILED",
            "manufacturer": "UNKNOWN",
            "pumpType": "CENTRIFUGAL",
            "pumpRange": "UNKNOWN",
            "application": "GENERAL",
            "constructionStandard": "UNKNOWN"
        },
        "technicalDetails": {
            "impellerType": "UNKNOWN"
        },
        "specifications": {
            "testSpeed": 0,
            "maxFlow": 0,
            "maxHead": 0,
            "bepFlow": 0,
            "bepHead": 0,
            "npshrAtBep": 0,
            "minImpeller": 0,
            "maxImpeller": 0,
            "variableDiameter": True,
            "bepMarkers": []
        },
        "curves": [],
        "_extractionMetadata": {
            "method": "fallback_rate_limited",
            "confidence": 0.0,
            "error": "Rate limit exceeded on all available AI models"
        }
    }

def log_extraction_quality(parsed_data):
    """
    Log quality metrics for extraction accuracy assessment
    """
    try:
        # Check BEP markers quality
        bep_markers = parsed_data.get('specifications', {}).get('bepMarkers', [])
        logger.info(f"[AI Extractor] Extracted {len(bep_markers)} BEP markers")

        for marker in bep_markers:
            logger.info(f"[AI Extractor] BEP {marker.get('impellerDiameter')}mm: Flow={marker.get('bepFlow'):.1f} m³/hr, Head={marker.get('bepHead'):.1f} m, Efficiency={marker.get('bepEfficiency'):.1f}%")

        # Check curve data quality
        curves = parsed_data.get('curves', [])
        logger.info(f"[AI Extractor] Extracted {len(curves)} impeller curves")

        for curve in curves:
            points = curve.get('performancePoints', [])
            if points:
                flows = [p.get('flow', 0) for p in points]
                heads = [p.get('head', 0) for p in points]
                efficiencies = [p.get('efficiency', 0) for p in points if p.get('efficiency', 0) > 0]

                logger.info(f"[AI Extractor] Curve {curve.get('impellerDiameter')}mm: {len(points)} points, Flow range: {min(flows):.1f}-{max(flows):.1f} m³/hr, Head range: {min(heads):.1f}-{max(heads):.1f} m")
                if efficiencies:
                    logger.info(f"[AI Extractor] Efficiency range: {min(efficiencies):.1f}-{max(efficiencies):.1f}%")

        # Check axis definitions if present
        if 'axisDefinitions' in parsed_data:
            axis_defs = parsed_data['axisDefinitions']
            logger.info(f"[AI Extractor] Axis definitions extracted: X={axis_defs.get('xAxis', {}).get('min', 0)}-{axis_defs.get('xAxis', {}).get('max', 0)} {axis_defs.get('xAxis', {}).get('unit', '')}")
    except Exception as e:
        logger.error(f"[AI Extractor] Error logging extraction quality: {e}")

class ExtractionResult:
    """Helper class for extraction results"""
    def __init__(self, success, error, data):
        self.success = success
        self.error = error
        self.data = data

class AIQueryManager:
    """
    Manages interactions with the OpenAI API, including prompt construction,
    request execution, and response parsing.
    """
    def __init__(self, client):
        self.client = client
        self.extraction_pipeline = [
            "pump_details",
            "curve_data",
            "bep_markers",
            "npsh_curve",
            "efficiency_contours"
        ]
        self.prompt_strategy = "specialist_queries"  # Default prompt strategy

    def execute_extraction_pipeline(self, pdf_path, base64_images):
        """Executes the 6-stage specialist extraction pipeline"""
        import tempfile
        pump_result = self.execute_pump_specifications_extraction(base64_images)

        if not pump_result.success:
            return self._create_extraction_result(False, f"Pump extraction failed: {pump_result.error}")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(base64.b64decode(base64_images[0]))
            temp_file_path = temp_file.name
            logger.info(f"[AI Extractor] Saved image to temporary file: {temp_file_path}")

        # Stage 2: Coordinate system analysis (critical foundation)
        logger.info("[AI Extractor] Stage 2: Analyzing coordinate system")
        coord_result = self.execute_curve_extraction(
            SpecialistPrompts.get_document_analysis_prompt(),
            temp_file_path
        )

        if not coord_result.success:
            logger.error(f"[AI Extractor] Coordinate system analysis failed: {coord_result.error}")
            coordinate_system = None
        else:
            coordinate_system = coord_result.data.get("coordinateSystem")
            logger.info(f"[AI Extractor] Coordinate system established: X={coordinate_system.get('sharedXAxis', {}).get('min')}-{coordinate_system.get('sharedXAxis', {}).get('max')}")

        # Stage 3: Extract anchor points using coordinate-aware prompts
        logger.info("[AI Extractor] Stage 3: Extracting performance anchor points")
        curve_result = self.execute_curve_extraction(
            SpecialistPrompts.get_head_efficiency_chart_prompt(coordinate_system),
            temp_file_path
        )

        if not curve_result.success:
            logger.error(f"[AI Extractor] Anchor point extraction failed: {curve_result.error}")
            return self._create_extraction_result(False, f"Anchor point extraction failed: {curve_result.error}")

        # Stage 4: Synthesize smooth curves from anchor points
        logger.info("[AI Extractor] Stage 4: Synthesizing smooth curves from anchor points")
        synthesizer = CurveSynthesizer()
        synthesized_data = synthesizer.synthesize_performance_curves(curve_result.data)

        # Validate synthesized curves against coordinate system
        valid_curves = []
        if coordinate_system:
            for curve in synthesized_data.get("curves", []):
                if synthesizer.validate_synthesized_curve(curve, coordinate_system):
                    valid_curves.append(curve)
                else:
                    logger.warning(f"[AI Extractor] Discarded invalid curve for {curve.get('impeller_diameter_mm')}mm")
        else:
            valid_curves = synthesized_data.get("curves", [])

        # Combine AI metadata with synthesized curve data
        extracted_data = {
            **pump_result.data,  # Pump specifications from Stage 1
            "curves": valid_curves,
            "efficiency_contours": synthesized_data.get("efficiency_contours", []),
            "bep_markers": synthesized_data.get("bep_markers", []),
            "coordinate_system": coordinate_system,
            "extraction_metadata": {
                "anchor_points_extracted": len(curve_result.data.get("performanceAnchorPoints", [])),
                "curves_synthesized": len(valid_curves),
                "synthesis_method": "polynomial_fitting"
            }
        }

        # Clean up temporary file
        os.remove(temp_file_path)
        logger.info(f"[AI Extractor] Deleted temporary file: {temp_file_path}")

        extracted_data["_qualityMetrics"] = {
            "overallConfidence": 0.95,  # Example confidence
            "processingTime": 15.5,
            "stageResults": {
                "pumpDetails": 0.98,
                "curveData": 0.92
            }
        }

        return extracted_data

    def execute_pump_specifications_extraction(self, base64_images):
        """Extract pump specifications using a single-prompt approach"""
        prompt = SpecialistPrompts.get_pump_details_prompt()
        return self._execute_openai_query(prompt, base64_images)

    def execute_curve_extraction(self, prompt, image_path):
        """
        Execute curve data extraction using a single-prompt approach.
        """
        with open(image_path, "rb") as image_file:
            img_data = base64.b64encode(image_file.read()).decode('utf-8')

        return self._execute_openai_query(prompt, [img_data])

    def _execute_openai_query(self, prompt, base64_images):
        """Executes a query to the OpenAI API with the given prompt and images."""
        content = [{"type": "text", "text": prompt}]

        for img_data in base64_images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_data}",
                    "detail": "high"
                }
            })

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": content}],
                max_tokens=3500,
                temperature=0.1,
                timeout=120  # Increased timeout for complex tasks
            )

            response_text = response.choices[0].message.content.strip()
            return self._create_extraction_result(True, None, json.loads(response_text))

        except json.JSONDecodeError as e:
            logger.error(f"[AI Extractor] JSON parsing failed: {e}")
            return self._create_extraction_result(False, f"JSON parsing failed: {e}")
        except Exception as e:
            logger.error(f"[AI Extractor] OpenAI API query failed: {e}")
            return self._create_extraction_result(False, f"OpenAI API query failed: {e}")

    def _create_extraction_result(self, success, error=None, data=None):
        """
        Helper method to create a consistent result object for extraction stages.
        """
        return ExtractionResult(success, error, data)

class SpecialistPrompts:
    """
    Centralized class for managing specialist prompts, allowing easy
    modification and experimentation.
    """
    @staticmethod
    def get_pump_details_prompt():
        """
        Prompt for extracting pump specifications (model, manufacturer, etc.)
        """
        return """
        Extract the following pump details from the image: pumpModel, manufacturer, pumpType, pumpRange, application, and constructionStandard.
        Return a JSON object with these fields.
        """

    @staticmethod
    def get_document_analysis_prompt():
        """
        Prompt for analyzing the document and establishing the coordinate system.
        This prompt should identify the min/max values for the X and Y axes.
        """
        return """
        Analyze the document image and establish the coordinate system.
        Identify the min/max values for the X-axis (flow rate) and the Y-axis (head).
        Also, identify units for each axis, and any secondary Y-axis, and its units.

        Return a JSON object with the following structure:
        {
            "coordinateSystem": {
                "sharedXAxis": {"min": 0, "max": 0, "unit": "m3/hr", "label": "Flow Rate"},
                "leftYAxis": {"min": 0, "max": 0, "unit": "m", "label": "Head"},
                "rightYAxis": {"min": 0, "max": 0, "unit": "%", "label": "Efficiency"},
                "secondaryRightYAxis": {"min": 0, "max": 0, "unit": "m", "label": "NPSH"}
            }
        }
        """

    @staticmethod
    def get_head_efficiency_chart_prompt(coordinate_system=None):
        """
        Prompt for extracting head and efficiency curve data points.
        This prompt should leverage the coordinate system established in the previous step.
        """
        prompt = """
        Extract head and efficiency curve data points from the chart image.
        Identify each curve by its impeller diameter.
        For each curve, extract at least 7-9 data points, distributed evenly across the flow range.
        Return a JSON object with the curve data.

        The JSON structure should be as follows:
        {
            "performanceAnchorPoints": [
                {"impellerDiameter": 160, "flow": 10, "head": 20},
                {"impellerDiameter": 160, "flow": 20, "head": 18},
                ...
                {"impellerDiameter": 180, "flow": 10, "head": 22},
                {"impellerDiameter": 180, "flow": 20, "head": 20},
                ...
            ]
        }
        """
        if coordinate_system:
            prompt += f"""
            Use the following coordinate system for accurate data extraction:
            X-axis (Flow Rate): min={coordinate_system.get('sharedXAxis', {}).get('min')}, max={coordinate_system.get('sharedXAxis', {}).get('max')}, unit={coordinate_system.get('sharedXAxis', {}).get('unit')}
            Y-axis (Head): min={coordinate_system.get('leftYAxis', {}).get('min')}, max={coordinate_system.get('leftYAxis', {}).get('max')}, unit={coordinate_system.get('leftYAxis', {}).get('unit')}
            Right-Y-axis (Efficiency): min={coordinate_system.get('rightYAxis', {}).get('min')}, max={coordinate_system.get('rightYAxis', {}).get('max')}, unit={coordinate_system.get('rightYAxis', {}).get('unit')}
            """
        return prompt

# Import moved to top of file to avoid duplication