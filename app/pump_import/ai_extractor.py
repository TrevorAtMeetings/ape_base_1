import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv
import json
import logging

logger = logging.getLogger(__name__)

# Load environment variables from a .env file
load_dotenv()

def file_to_generative_part(path, mime_type):
    with open(path, "rb") as f:
        data = f.read()
        return {
            "inline_data": {
                "data": base64.b64encode(data).decode("utf-8"),
                "mime_type": mime_type,
            }
        }

def extract_pump_data_from_pdf(pdf_path):
    """
    Extract pump data from a PDF using Gemini API. Returns a Python dict.
    """
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        logger.error(f"[AI Extractor] PDF file does not exist: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Get file size
    file_size = os.path.getsize(pdf_path)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("[AI Extractor] GOOGLE_API_KEY environment variable is not set.")
        raise ValueError("GOOGLE_API_KEY environment variable is not set.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")
    
    pdf_file_part = file_to_generative_part(pdf_path, "application/pdf")
    
    # Use the robust, general prompt for impeller diameter-based curves
    comprehensive_prompt = """
Your task is to act as an expert hydraulic engineer and data extraction specialist. 
Analyze the provided pump performance curve PDF where curves are distinguished by IMPELLER DIAMETER.

Your final output MUST be a single, raw JSON object. Do NOT include any explanations, 
introductory text, or markdown formatting like ```json.

JSON STRUCTURE:
{
  "pumpDetails": { "pumpModel": "", "manufacturer": "", "pumpType": "", "pumpRange": "", "application": "", "constructionStandard": "" },
  "technicalDetails": { "impellerType": "" },
  "specifications": { "testSpeed": 0, "maxFlow": 0, "maxHead": 0, "bepFlow": 0, "bepHead": 0, "npshrAtBep": 0, "minImpeller": 0, "maxImpeller": 0, "variableDiameter": true },
  "curves": [ { "impellerDiameter": 0, "performancePoints": [ { "flow": 0, "head": 0, "efficiency": 0, "npshr": 0 } ] } ]
}

CRITICAL EXTRACTION METHODOLOGY:
1. Grid Analysis & Interpolation: Internally define the graph's coordinate system. For any point, calculate its value by interpolating its position between the nearest grid lines. Do not round.

2. BEP: Locate the Best Efficiency Point. Use the interpolation method to find its precise 'bepFlow' and 'bepHead'.

3. Curve Analysis: Group data into the 'curves' array where each element represents an 'impellerDiameter' in mm.

4. EFFICIENCY CURVE HANDLING (CRITICAL):
   - Look for efficiency curves on the chart (typically curved lines showing efficiency percentages)
   - If efficiency curves are present, trace them to extract efficiency values
   - If no efficiency curves are visible, look for a second curve that represents efficiency
   - For each impeller diameter, extract 7-10 performance points along the curves

5. SPECIAL PROCEDURE FOR MISSING EFFICIENCY DATA:
   If efficiency data appears missing or shows zeros:
   a) Identify the efficiency curve (usually the second curve on the chart)
   b) Select 7-10 points along the head-flow curve for that impeller
   c) For each flow point on the head-flow curve:
      - Find the corresponding efficiency value by tracing to the efficiency curve
      - Read the efficiency value from the y-axis where the efficiency curve intersects
      - Create a performance point with: flow (x-axis), head (from head curve), efficiency (from efficiency curve)
   d) Ensure efficiency values are realistic (typically 40-85% for centrifugal pumps)

6. Data Validation:
   - Efficiency values should be between 30-90%
   - Head values should decrease as flow increases
   - NPSH values should increase as flow increases
   - All values should be realistic for centrifugal pumps

IMPORTANT: Never output efficiency values of 0 unless the chart explicitly shows 0% efficiency. Always extract meaningful efficiency data from the efficiency curves or contours.
"""
    
    try:
        response = model.generate_content([comprehensive_prompt, pdf_file_part])
        
        response_text = response.text.strip()
        
        cleaned_response = response_text
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        # Parse JSON
        parsed_data = json.loads(cleaned_response)
        
        return parsed_data
        
    except json.JSONDecodeError as e:
        logger.error(f"[AI Extractor] JSON parsing error: {e}")
        logger.error(f"[AI Extractor] Failed response text: {response_text}")
        raise
    except Exception as e:
        logger.error(f"[AI Extractor] Extraction error: {e}")
        logger.error(f"[AI Extractor] Error type: {type(e).__name__}")
        raise 