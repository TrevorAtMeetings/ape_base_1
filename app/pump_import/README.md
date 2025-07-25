# AI Extraction System Configuration

This directory contains a generic AI extraction system for pump data from PDF files. The system supports multiple AI providers (OpenAI, Anthropic, Google) and uses a configurable model with a customizable prompt.

## Files

### Core Files
- `config.py` - Generic configuration settings for AI providers and extraction parameters
- `simple_ai_extractor.py` - Main extraction logic supporting multiple AI providers
- `extraction_prompt.txt` - The prompt used for AI extraction (easily modifiable)
- `pdf_to_image_converter.py` - Converts PDF pages to images for AI processing


### Step 1: Choose Your AI Provider

Add the following configuration to your `.env` file based on your preferred AI provider:

#### Option A: OpenAI (Recommended - Default)
```bash
# Add these lines to your .env file:
AI_PROVIDER=openai
AI_MODEL_NAME=gpt-4o
AI_API_KEY_ENV=OPENAI_API_KEY
OPENAI_API_KEY=your_actual_openai_api_key_here
```

#### Option B: Anthropic
```bash
# Add these lines to your .env file:
AI_PROVIDER=anthropic
AI_MODEL_NAME=claude-3-5-sonnet-20241022
AI_API_KEY_ENV=ANTHROPIC_API_KEY
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
```

#### Option C: Google
```bash
# Add these lines to your .env file:
AI_PROVIDER=google
AI_MODEL_NAME=gemini-2.0-flash-exp
AI_API_KEY_ENV=GOOGLE_API_KEY
GOOGLE_API_KEY=your_actual_google_api_key_here
```
