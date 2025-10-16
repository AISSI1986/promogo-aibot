from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Promogo STT API (Hugging Face)",
    description="Speech-to-Text service using Hugging Face Inference API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptionResponse(BaseModel):
    text: str
    confidence: float
    language: str
    duration: Optional[float] = None
    model_used: str

class TranscriptionRequest(BaseModel):
    language: Optional[str] = None
    model: Optional[str] = None

# Language to model mapping for STT - Optimized for Promogo's target languages
# Primary languages: English, Hausa, Twi, Ewe
LANGUAGE_MODELS = {
    # Primary languages for Promogo (your preferred languages)
    "en": "facebook/wav2vec2-base-960h",           # English - High quality
    "ha": "facebook/wav2vec2-large-xlsr-53-hausa", # Hausa - Native African language (Nigeria)
    "tw": "facebook/wav2vec2-large-xlsr-53-twi",   # Twi - Ghanaian language
    "ee": "facebook/wav2vec2-large-xlsr-53-ewe",   # Ewe - Ghanaian language
    
    # Additional supported languages
    "fr": "facebook/wav2vec2-large-xlsr-53-french",
    "es": "facebook/wav2vec2-large-xlsr-53-spanish", 
    "de": "facebook/wav2vec2-large-xlsr-53-german",
    "it": "facebook/wav2vec2-large-xlsr-53-italian",
    "pt": "facebook/wav2vec2-large-xlsr-53-portuguese",
    "ru": "facebook/wav2vec2-large-xlsr-53-russian",
    "zh": "facebook/wav2vec2-large-xlsr-53-chinese-zh-cn",
    "ja": "facebook/wav2vec2-large-xlsr-53-japanese",
    "ko": "facebook/wav2vec2-large-xlsr-53-korean",
}

# Primary languages for Promogo
PRIMARY_LANGUAGES = ["en", "ha", "tw", "ee"]

# Multilingual models that can handle multiple languages
MULTILINGUAL_MODELS = {
    "multilingual": "facebook/wav2vec2-large-xlsr-53",
    "xlsr": "facebook/wav2vec2-xlsr-53-espeak-cv-ft",
    "mms": "facebook/mms-1b-fl102"
}

@app.get("/")
async def root():
    return {
        "message": "Promogo STT API (Hugging Face)",
        "status": "running",
        "primary_languages": PRIMARY_LANGUAGES,
        "supported_languages": list(LANGUAGE_MODELS.keys()),
        "multilingual_models": list(MULTILINGUAL_MODELS.keys()),
        "primary_language_info": {
            "en": "English (🇬🇧)",
            "ha": "Hausa (🇳🇬)", 
            "tw": "Twi (🇬🇭)",
            "ee": "Ewe (🇬🇭)"
        },
        "note": "Optimized for English, Hausa, Twi, and Ewe using Hugging Face Inference API"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "STT", 
        "provider": "Hugging Face",
        "memory_usage": "minimal"
    }

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check environment variables"""
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    return {
        "token_configured": bool(hf_token),
        "token_length": len(hf_token) if hf_token else 0,
        "token_starts_with_hf": hf_token.startswith("hf_") if hf_token else False,
        "token_preview": f"{hf_token[:10]}..." if hf_token and len(hf_token) > 10 else hf_token,
        "all_env_vars": {k: v for k, v in os.environ.items() if "HUGGINGFACE" in k}
    }

@app.get("/languages")
async def get_languages():
    """Get supported languages and their models"""
    return {
        "supported_languages": list(LANGUAGE_MODELS.keys()),
        "language_models": LANGUAGE_MODELS,
        "multilingual_models": MULTILINGUAL_MODELS,
        "note": "Languages supported by Hugging Face wav2vec2 models"
    }

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = None,
    model: Optional[str] = None
):
    """
    Convert speech to text using Hugging Face Inference API
    """
    try:
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload an audio file."
            )
        
        # Get Hugging Face token
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token or hf_token == "your_huggingface_token_here":
            logger.error("HUGGINGFACE_TOKEN not found in environment variables")
            raise HTTPException(
                status_code=500,
                detail="Hugging Face API token not configured. Please set HUGGINGFACE_TOKEN environment variable."
            )
        
        # Determine model to use
        if model and model in MULTILINGUAL_MODELS:
            model_name = MULTILINGUAL_MODELS[model]
            logger.info(f"Using multilingual model: {model_name}")
        elif language and language in LANGUAGE_MODELS:
            model_name = LANGUAGE_MODELS[language]
            logger.info(f"Using language-specific model for {language}: {model_name}")
        else:
            # Default to multilingual model
            model_name = MULTILINGUAL_MODELS["multilingual"]
            logger.info(f"Using default multilingual model: {model_name}")
        
        # Prepare request to Hugging Face API
        hf_url = f"https://api-inference.huggingface.co/models/{model_name}"
        headers = {
            "Authorization": f"Bearer {hf_token}"
        }
        
        # Read audio file
        audio_content = await audio.read()
        
        # Make request to Hugging Face API
        logger.info(f"Making request to Hugging Face API: {hf_url}")
        response = requests.post(
            hf_url, 
            headers=headers, 
            data=audio_content,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract text from response
            if isinstance(result, dict):
                text = result.get("text", "")
                confidence = result.get("confidence", 0.95)
            elif isinstance(result, list) and len(result) > 0:
                text = result[0].get("text", "")
                confidence = result[0].get("confidence", 0.95)
            else:
                text = str(result)
                confidence = 0.95
            
            # Clean up text
            text = text.strip()
            
            logger.info(f"Transcription successful: {text[:50]}...")
            
            return TranscriptionResponse(
                text=text,
                confidence=confidence,
                language=language or "auto",
                model_used=model_name
            )
            
        elif response.status_code == 503:
            # Model is loading
            logger.warning("Model is loading, please try again in a few seconds")
            raise HTTPException(
                status_code=503,
                detail="Model is loading, please try again in a few seconds"
            )
            
        else:
            logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"API error: {response.status_code} - {response.text}"
            )
            
    except requests.exceptions.Timeout:
        logger.error("Request timeout to Hugging Face API")
        raise HTTPException(
            status_code=504,
            detail="Request timeout - please try again"
        )
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Network error: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

@app.post("/transcribe_batch/")
async def transcribe_batch(
    audio_files: list[UploadFile] = File(...),
    language: Optional[str] = None,
    model: Optional[str] = None
):
    """
    Transcribe multiple audio files in batch
    """
    results = []
    
    for i, audio_file in enumerate(audio_files):
        try:
            result = await transcribe_audio(audio_file, language, model)
            results.append({
                "index": i,
                "filename": audio_file.filename,
                "result": result
            })
        except Exception as e:
            results.append({
                "index": i,
                "filename": audio_file.filename,
                "error": str(e)
            })
    
    return {
        "success": True,
        "message": f"Processed {len(audio_files)} audio files",
        "results": results
    }

@app.get("/models")
async def get_available_models():
    """Get information about available models"""
    return {
        "language_specific_models": LANGUAGE_MODELS,
        "multilingual_models": MULTILINGUAL_MODELS,
        "recommendations": {
            "for_english": "facebook/wav2vec2-base-960h",
            "for_multilingual": "facebook/wav2vec2-large-xlsr-53",
            "for_african_languages": "facebook/wav2vec2-large-xlsr-53"
        }
    }

@app.post("/detect_language/")
async def detect_language(audio: UploadFile = File(...)):
    """
    Detect the language of the audio file
    """
    try:
        # Use a multilingual model for language detection
        model_name = MULTILINGUAL_MODELS["multilingual"]
        
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            raise HTTPException(
                status_code=500,
                detail="Hugging Face API token not configured"
            )
        
        hf_url = f"https://api-inference.huggingface.co/models/{model_name}"
        headers = {
            "Authorization": f"Bearer {hf_token}"
        }
        
        audio_content = await audio.read()
        
        response = requests.post(
            hf_url,
            headers=headers,
            data=audio_content,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # This is a simplified language detection
            # In practice, you might need a dedicated language detection model
            return {
                "success": True,
                "detected_language": "auto",  # Placeholder
                "confidence": 0.8,
                "model_used": model_name
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Language detection failed: {response.status_code}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Language detection error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5006))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
