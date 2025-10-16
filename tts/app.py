from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import requests
import os
import io
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Promogo TTS API (Hugging Face)",
    description="Text-to-Speech service using Hugging Face Inference API",
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

class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "en"
    voice: Optional[str] = None
    
class TextToSpeechResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None
    error: Optional[str] = None

# Language to model mapping - Only Promogo's target languages
# Primary languages: English, Hausa, Twi, Ewe
LANGUAGE_MODELS = {
    "en": "facebook/mms-tts-eng",      # English - High quality
    "ha": "facebook/mms-tts-hau",      # Hausa - Native African language (Nigeria)
    "tw": "facebook/mms-tts-twi",      # Twi - Ghanaian language
    "ee": "facebook/mms-tts-ewe",      # Ewe - Ghanaian language
}

# Primary languages for Promogo
PRIMARY_LANGUAGES = ["en", "ha", "tw", "ee"]

@app.get("/")
async def root():
    return {
        "message": "Promogo TTS API (Hugging Face)",
        "status": "running",
        "primary_languages": PRIMARY_LANGUAGES,
        "supported_languages": list(LANGUAGE_MODELS.keys()),
        "primary_language_info": {
            "en": "English (🇬🇧)",
            "ha": "Hausa (🇳🇬)", 
            "tw": "Twi (🇬🇭)",
            "ee": "Eʋegbe (🇬🇭)"
        },
        "note": "Optimized for English, Hausa, Twi, and Eʋegbe using Hugging Face Inference API"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "TTS",
        "provider": "Hugging Face",
        "memory_usage": "minimal"
    }

@app.get("/languages")
async def get_languages():
    """Get supported languages and their models"""
    return {
        "supported_languages": list(LANGUAGE_MODELS.keys()),
        "models": LANGUAGE_MODELS,
        "note": "Languages supported by Hugging Face MMS-TTS models"
    }

@app.post("/synthesize/", response_class=StreamingResponse)
async def synthesize_speech(request: TextToSpeechRequest):
    """
    Convert text to speech using Hugging Face Inference API
    """
    try:
        # Validate language
        if request.language not in LANGUAGE_MODELS:
            return TextToSpeechResponse(
                success=False,
                message=f"Language '{request.language}' not supported",
                error=f"Supported languages: {list(LANGUAGE_MODELS.keys())}"
            )
        
        # Get Hugging Face token
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token or hf_token == "your_huggingface_token_here":
            logger.error("HUGGINGFACE_TOKEN not found in environment variables")
            return TextToSpeechResponse(
                success=False,
                message="Hugging Face API token not configured",
                error="Please set HUGGINGFACE_TOKEN environment variable"
            )
        
        # Get model for language
        model_name = LANGUAGE_MODELS[request.language]
        logger.info(f"Synthesizing text in {request.language} using model {model_name}")
        
        # Prepare request to Hugging Face API
        hf_url = f"https://api-inference.huggingface.co/models/{model_name}"
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "inputs": request.text,
            "parameters": {
                "return_format": "wav"
            }
        }
        
        # Make request to Hugging Face API
        logger.info(f"Making request to Hugging Face API: {hf_url}")
        response = requests.post(hf_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            # Return audio directly as a stream
            return StreamingResponse(
                io.BytesIO(response.content),
                media_type="audio/wav",
                headers={"Content-Disposition": f"attachment; filename=speech_{request.language}.wav"}
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
                status_code=response.status_code,
                detail=f"Hugging Face API error: {response.text}"
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

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files"""
    audio_path = f"/tmp/{filename}"
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/wav")
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")

@app.post("/synthesize_batch/")
async def synthesize_batch(request: list[TextToSpeechRequest]):
    """
    Synthesize multiple texts in batch
    """
    results = []
    for i, req in enumerate(request):
        try:
            result = await synthesize_speech(req)
            results.append({
                "index": i,
                "text": req.text,
                "language": req.language,
                "result": result
            })
        except Exception as e:
            results.append({
                "index": i,
                "text": req.text,
                "language": req.language,
                "result": TextToSpeechResponse(
                    success=False,
                    message="Batch processing error",
                    error=str(e)
                )
            })
    
    return {
        "success": True,
        "message": f"Processed {len(request)} texts",
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5007))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
