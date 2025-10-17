# GhanaNLP Service

This service provides integration with GhanaNLP APIs for translation, speech-to-text, and text-to-speech functionality.

## Features

- **Translation**: Translate text between supported languages (English, Hausa, Twi, Ewe, Ga, Dagbani)
- **Speech-to-Text**: Convert audio to text in multiple languages
- **Text-to-Speech**: Convert text to speech in multiple languages
- **Language Detection**: Automatic language detection and mapping

## API Endpoints

### Translation
- `POST /translate` - Translate text between languages

### Speech-to-Text
- `POST /transcribe` - Convert audio to text

### Text-to-Speech
- `POST /synthesize` - Convert text to speech

### Utility
- `GET /languages` - Get supported languages
- `GET /voices/{language}` - Get available voices for a language
- `GET /health` - Health check

## Environment Variables

- `GHANA_NLP_API_KEY` - Your GhanaNLP API key
- `PORT` - Port to run the service on (default: 8000)

## Usage

1. Set your GhanaNLP API key:
   ```bash
   export GHANA_NLP_API_KEY="your_api_key_here"
   ```

2. Run the service:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

## Supported Languages

- English (en)
- Hausa (ha)
- Twi (tw)
- Ewe (ee)
- Ga (ga)
- Dagbani (dagbani)
