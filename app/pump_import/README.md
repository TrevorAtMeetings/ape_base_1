# Simplified AI Extraction System

This directory contains a simplified AI extraction system for pump data from PDF files. The system has been streamlined to use a single configurable OpenAI model with a customizable prompt.

## Files

### Core Files
- `config.py` - Configuration settings for the AI model and extraction parameters
- `simple_ai_extractor.py` - Main extraction logic using OpenAI
- `extraction_prompt.txt` - The prompt used for AI extraction (easily modifiable)
- `pdf_to_image_converter.py` - Converts PDF pages to images for AI processing

### Legacy Files (Kept for Reference)
- `ai_extractor.py` - Original complex multi-model extractor
- `ai_query_manager.py` - Original query management system
- `specialist_prompts.py` - Original specialized prompts
- `curve_synthesizer.py` - Original curve synthesis logic
- `ape_data_processor.py` - Original APE data processing

## Configuration

### Environment Variables
Set these environment variables to configure the system:

```bash
# AI Model Configuration
AI_MODEL_NAME=gpt-4o                    # OpenAI model to use
AI_API_KEY_ENV=OPENAI_API_KEY          # Environment variable name for API key
OPENAI_API_KEY=your_api_key_here       # Your OpenAI API key

# Extraction Settings
AI_MAX_TOKENS=3500                     # Maximum tokens for AI response
AI_TEMPERATURE=0.1                     # AI temperature (0.0-1.0)
AI_TIMEOUT_SECONDS=120                 # Timeout for API calls

# Validation Settings
AI_ENABLE_VALIDATION=true              # Enable data validation
AI_ENABLE_FALLBACK=true                # Enable fallback data on failure
```

### Prompt Customization
The extraction prompt is stored in `extraction_prompt.txt` and can be easily modified without touching the code. The prompt should:

1. Be clear and specific about the required JSON structure
2. Include all necessary fields for pump data extraction
3. Provide clear instructions for the AI model

## Usage

### Basic Usage
```python
from app.pump_import.simple_ai_extractor import extract_pump_data_from_pdf

# Extract data from a PDF file
data = extract_pump_data_from_pdf("path/to/pump_curves.pdf")
```

### Advanced Usage
```python
from app.pump_import.simple_ai_extractor import SimpleAIExtractor

# Create extractor instance
extractor = SimpleAIExtractor()

# Extract data with custom configuration
data = extractor.extract_pump_data("path/to/pump_curves.pdf")
```

## Output Format

The system returns a JSON object with the following structure:

```json
{
  "pumpDetails": {
    "pumpModel": "",
    "manufacturer": "",
    "pumpType": "",
    "pumpRange": "",
    "application": "",
    "constructionStandard": ""
  },
  "technicalDetails": {
    "impellerType": ""
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
  "curves": [
    {
      "impellerDiameter": 0,
      "performancePoints": [
        {
          "flow": 0,
          "head": 0,
          "efficiency": 0,
          "npshr": 0
        }
      ]
    }
  ]
}
```

## Error Handling

The system includes comprehensive error handling:

1. **API Errors**: Handles rate limits, timeouts, and authentication issues
2. **JSON Parsing**: Validates and cleans AI responses
3. **Data Validation**: Ensures required fields are present
4. **Fallback Data**: Returns structured fallback data if extraction fails

## Migration from Complex System

The simplified system removes:
- Multiple AI model selection (OpenAI, Gemini, Anthropic)
- Processing priority options (speed, accuracy, cost)
- Complex model routing logic
- Performance tracking and comparison
- Specialized prompt management

This makes the system much easier to maintain and configure while still providing high-quality extraction results.

## Troubleshooting

### Common Issues

1. **API Key Not Found**: Ensure `OPENAI_API_KEY` is set in environment
2. **Timeout Errors**: Increase `AI_TIMEOUT_SECONDS` for complex PDFs
3. **Invalid JSON**: Check the prompt in `extraction_prompt.txt`
4. **Memory Issues**: Reduce `AI_MAX_TOKENS` for large files

### Debugging

Enable debug logging by setting the log level:
```python
import logging
logging.getLogger('app.pump_import.simple_ai_extractor').setLevel(logging.DEBUG)
```

## Performance

The simplified system typically processes PDFs in 30-120 seconds depending on:
- PDF complexity and number of pages
- Image quality and resolution
- API response time
- Network latency

## Future Enhancements

Potential improvements:
1. Add support for other AI models
2. Implement batch processing
3. Add more sophisticated data validation
4. Create custom prompt templates for different pump types 