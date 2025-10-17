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

# GhanaNLP API Configuration
GHANA_NLP_API_KEY = os.getenv("GHANA_NLP_API_KEY")
GHANA_NLP_BASE_URL = "https://api.ghananlp.org"  # Update with actual API URL
TRANSLATION_API_URL = "https://translation.ghananlp.org/api/translate"

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
    return {"status": "healthy", "service": "ghananlp"}

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text using GhanaNLP Translation API
    """
    try:
        # Map language codes
        source_lang = LANGUAGE_MAPPING.get(request.source_language, request.source_language)
        target_lang = LANGUAGE_MAPPING.get(request.target_language, request.target_language)
        
        # Prepare request for GhanaNLP API
        payload = {
            "text": request.text,
            "source_language": source_lang,
            "target_language": target_lang
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GHANA_NLP_API_KEY}" if GHANA_NLP_API_KEY else None
        }
        
        # Remove None values from headers
        headers = {k: v for k, v in headers.items() if v is not None}
        
        # Make request to GhanaNLP API
        response = requests.post(
            TRANSLATION_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return TranslationResponse(
                translated_text=result.get("translated_text", request.text),
                source_language=source_lang,
                target_language=target_lang,
                confidence=result.get("confidence", 0.9)
            )
        else:
            logger.error(f"GhanaNLP API error: {response.status_code} - {response.text}")
            # Fallback to simple response
            return TranslationResponse(
                translated_text=request.text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.0
            )
            
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(request: STTRequest):
    """
    Convert speech to text using GhanaNLP STT API
    """
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Map language code
        language = LANGUAGE_MAPPING.get(request.language, request.language)
        
        # Prepare files for GhanaNLP STT API
        files = {
            "audio": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")
        }
        
        data = {
            "language": language
        }
        
        headers = {
            "Authorization": f"Bearer {GHANA_NLP_API_KEY}" if GHANA_NLP_API_KEY else None
        }
        
        # Remove None values from headers
        headers = {k: v for k, v in headers.items() if v is not None}
        
        # Make request to GhanaNLP STT API
        stt_url = f"{GHANA_NLP_BASE_URL}/stt/transcribe"
        response = requests.post(
            stt_url,
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return STTResponse(
                text=result.get("text", ""),
                language=language,
                confidence=result.get("confidence", 0.9)
            )
        else:
            logger.error(f"GhanaNLP STT API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Speech-to-text conversion failed")
            
    except Exception as e:
        logger.error(f"STT error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")

@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using GhanaNLP TTS API
    """
    try:
        # Map language code
        language = LANGUAGE_MAPPING.get(request.language, request.language)
        
        # Prepare request for GhanaNLP TTS API
        payload = {
            "text": request.text,
            "language": language,
            "voice": request.voice or "default"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GHANA_NLP_API_KEY}" if GHANA_NLP_API_KEY else None
        }
        
        # Remove None values from headers
        headers = {k: v for k, v in headers.items() if v is not None}
        
        # Make request to GhanaNLP TTS API
        tts_url = f"{GHANA_NLP_BASE_URL}/tts/synthesize"
        response = requests.post(
            tts_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return TTSResponse(
                audio_data=result.get("audio_data", ""),
                language=language,
                voice=result.get("voice", "default")
            )
        else:
            logger.error(f"GhanaNLP TTS API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Text-to-speech conversion failed")
            
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
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
