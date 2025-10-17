from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import requests
import json
import os
import logging
from typing import Optional, Dict, Any
import base64
import io
import tempfile
from ghana_nlp import GhanaNLP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GhanaNLP Service API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GhanaNLP Configuration
GHANA_NLP_API_KEY = os.getenv("GHANA_NLP_API_KEY")
logger.info(f"GhanaNLP API Key present: {bool(GHANA_NLP_API_KEY)}")

try:
    nlp = GhanaNLP(GHANA_NLP_API_KEY) if GHANA_NLP_API_KEY else None
    logger.info(f"GhanaNLP initialized: {nlp is not None}")
except Exception as e:
    logger.error(f"Failed to initialize GhanaNLP: {str(e)}")
    nlp = None

# Language mapping for GhanaNLP
LANGUAGE_MAPPING = {
    "en": "en",
    "ha": "ha",  # Hausa
    "tw": "tw",  # Twi
    "ee": "ee",  # Ewe
    "ga": "ga",  # Ga
    "dagbani": "dagbani"
}

class TranslationRequest(BaseModel):
    text: str
    source_language: str = "en"
    target_language: str = "tw"

class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    confidence: float

class STTRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: str = "en"

class STTResponse(BaseModel):
    text: str
    language: str
    confidence: float

class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    voice: Optional[str] = None

class TTSResponse(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: str
    voice: str

@app.get("/")
async def root():
    return {"message": "GhanaNLP Service API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "ghananlp",
        "api_key_present": bool(GHANA_NLP_API_KEY),
        "nlp_initialized": nlp is not None
    }

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text using GhanaNLP library
    """
    try:
        if not nlp:
            raise HTTPException(status_code=500, detail="GhanaNLP not initialized - API key required")
        
        # Map language codes
        source_lang = LANGUAGE_MAPPING.get(request.source_language, request.source_language)
        target_lang = LANGUAGE_MAPPING.get(request.target_language, request.target_language)
        
        # Create language pair (e.g., "tw-en" for Twi to English)
        lang_pair = f"{source_lang}-{target_lang}"
        
        # Use GhanaNLP library for translation
        response = nlp.translate(request.text, lang_pair)
        
        # Handle different response formats
        if isinstance(response, str):
            translated_text = response
        elif isinstance(response, dict):
            if "translation" in response:
                translated_text = response["translation"]
            elif "translated_text" in response:
                translated_text = response["translated_text"]
            elif "message" in response:
                logger.warning(f"Translation failed: {response['message']}")
                translated_text = request.text  # Return original text
            else:
                translated_text = str(response)
        else:
            translated_text = str(response)
        
        return TranslationResponse(
            translated_text=translated_text,
            source_language=source_lang,
            target_language=target_lang,
            confidence=0.9  # Default confidence
        )
            
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(request: STTRequest):
    """
    Convert speech to text using GhanaNLP library
    """
    try:
        if not nlp:
            raise HTTPException(status_code=500, detail="GhanaNLP not initialized - API key required")
        
        # Decode base64 audio data and save to temporary file
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Map language code
            language = LANGUAGE_MAPPING.get(request.language, request.language)
            
            # Use GhanaNLP library for STT
            response = nlp.stt(temp_file_path)
            
            # Handle different response formats (inspired by the example code)
            if isinstance(response, str):
                text = response
            elif isinstance(response, dict):
                # Handle known key formats
                if "text" in response:
                    text = response["text"]
                elif "translation" in response:
                    text = response["translation"]
                elif "message" in response:
                    logger.warning(f"GhanaNLP returned message: {response['message']}")
                    text = response["message"]
                else:
                    text = str(response)
            else:
                # Fallback to string version of response
                text = str(response)
            
            return STTResponse(
                text=text,
                language=language,
                confidence=0.9  # Default confidence
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
            
    except Exception as e:
        logger.error(f"STT error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")

@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using GhanaNLP library
    """
    try:
        logger.info(f"TTS request: text='{request.text[:50]}...', language='{request.language}'")
        
        if not nlp:
            logger.error("GhanaNLP not initialized - API key required")
            raise HTTPException(status_code=500, detail="GhanaNLP not initialized - API key required")
        
        # Map language code
        language = LANGUAGE_MAPPING.get(request.language, request.language)
        logger.info(f"Mapped language: {request.language} -> {language}")
        
        # Use GhanaNLP library for TTS
        logger.info("Calling nlp.tts()...")
        response = nlp.tts(request.text, language)
        logger.info(f"GhanaNLP TTS response type: {type(response)}")
        logger.info(f"GhanaNLP TTS response: {str(response)[:200]}...")
        
        # Handle different response formats
        if isinstance(response, str):
            # If response is a string, it might be a file path or base64 data
            if response.startswith('data:audio') or len(response) > 100:
                # Likely base64 audio data
                audio_data = response
                logger.info("Using response as base64 audio data")
            else:
                # Might be a file path, read the file
                try:
                    logger.info(f"Trying to read file: {response}")
                    with open(response, 'rb') as f:
                        audio_data = base64.b64encode(f.read()).decode('utf-8')
                    logger.info("Successfully read audio file")
                except Exception as file_error:
                    logger.warning(f"Could not read file {response}: {file_error}")
                    audio_data = base64.b64encode(response.encode()).decode('utf-8')
                    logger.info("Using response as text (encoded)")
        elif isinstance(response, dict):
            # Handle dictionary response
            logger.info(f"Processing dict response with keys: {list(response.keys())}")
            if "audio_data" in response:
                audio_data = response["audio_data"]
            elif "audio" in response:
                audio_data = response["audio"]
            elif "file" in response:
                # Read audio file
                with open(response["file"], 'rb') as f:
                    audio_data = base64.b64encode(f.read()).decode('utf-8')
            else:
                logger.error(f"Unexpected GhanaNLP TTS response format: {response}")
                raise HTTPException(status_code=500, detail="Unexpected TTS response format")
        else:
            logger.error(f"Unexpected GhanaNLP TTS response type: {type(response)}")
            raise HTTPException(status_code=500, detail="Unexpected TTS response type")
        
        logger.info("TTS request completed successfully")
        return TTSResponse(
            audio_data=audio_data,
            language=language,
            voice=request.voice or "default"
        )
            
    except Exception as e:
        logger.error(f"TTS error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")

@app.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    return {
        "supported_languages": list(LANGUAGE_MAPPING.keys()),
        "language_mapping": LANGUAGE_MAPPING
    }

@app.get("/voices/{language}")
async def get_available_voices(language: str):
    """
    Get available voices for a specific language
    """
    # Map language code
    lang_code = LANGUAGE_MAPPING.get(language, language)
    
    # Default voices for each language
    voices = {
        "en": ["default", "male", "female"],
        "ha": ["default", "male", "female"],
        "tw": ["default", "male", "female"],
        "ee": ["default", "male", "female"],
        "ga": ["default", "male", "female"],
        "dagbani": ["default", "male", "female"]
    }
    
    return {
        "language": lang_code,
        "available_voices": voices.get(lang_code, ["default"])
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
