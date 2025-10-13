from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io
import numpy as np
import soundfile as sf
from typing import Optional, Dict, List
import logging
import time
import threading
import torch
import os
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with metadata for Swagger UI
app = FastAPI(
    title="Multilingual Speech Synthesis API",
    description="API for text-to-speech synthesis in multiple African languages and en",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    # Liste des origines autorisées (votre frontend)
    allow_origins=["*"],
    # Autoriser les cookies dans les requêtes cross-origin
    allow_credentials=True,
    # Méthodes HTTP autorisées
    allow_methods=["GET", "POST", "OPTIONS"],
    # En-têtes HTTP autorisés
    allow_headers=["Content-Type", "Authorization"],
    # En-têtes exposés au navigateur
    expose_headers=["Content-Length", "Content-Range"],
    # Durée de mise en cache des résultats preflight (en secondes)
    max_age=1800,
)

# Define request model with examples for Swagger UI
class TextToSpeechRequest(BaseModel):
    text: str
    language: str
    voice: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Hello, how are you today?",
                "language": "en"
            }
        }

# Global variables
tokenizers = {}
models = {}
kokoro_pipeline = None
models_status: Dict[str, str] = {}
loading_complete = False

# Define language models with their types
# Note: facebook/mms-tts-gaa doesn't exist, using alternative
LANGUAGE_MODELS = {
    "en": {"model": "kokoro", "type": "kokoro"},
    "ha": {"model": "facebook/mms-tts-hau", "type": "mms"},
    "ee": {"model": "facebook/mms-tts-ewe", "type": "mms"},
    "tw": {"model": "facebook/mms-tts-aka", "type": "mms"},
    # "ga": {"model": "facebook/mms-tts-gaa", "type": "mms"}  # This model doesn't exist
}

# Available Kokoro voices
KOKORO_VOICES = [
    "af_heart", "af_sun", "af_moon", "af_star", "af_cloud",
    "en_heart", "en_sun", "en_moon", "en_star", "en_cloud"
]

# Sample texts for each language (for testing)
SAMPLE_TEXTS = {
    "en": "Hello, how are you today?",
    "ha": "Sannu, yaya kake yau?",
    "ee": "Ndi, aleke nèle egbe?",
    "tw": "Mema wo akye, wo ho te sɛn?",
    # "ga": "Ojekoo, te oyaa nɛɛ?"
}

def normalize_audio(audio):
    """Normalize audio to prevent clipping and ensure proper int16 conversion"""
    # Convert to float32 if not already
    audio = audio.astype(np.float32)
    
    # Remove any NaN or Inf values
    audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
    
    # Find the maximum absolute value
    max_val = np.abs(audio).max()
    
    # Normalize to [-1, 1] range if needed
    if max_val > 0:
        audio = audio / max_val * 0.95  # Scale to 95% to avoid clipping
    
    return audio

def load_vits_model(model_name):
    """Load a VITS model using the correct import"""
    try:
        # Try to import VitsModel from the correct location
        try:
            from transformers.models.vits import VitsModel
            logger.info(f"Using VitsModel from transformers.models.vits for {model_name}")
        except ImportError:
            from transformers import VitsModel
            logger.info(f"Using VitsModel from transformers for {model_name}")
        
        from transformers import AutoTokenizer
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = VitsModel.from_pretrained(model_name)
        
        return tokenizer, model
    except Exception as e:
        logger.error(f"Error loading VitsModel for {model_name}: {str(e)}")
        raise

def load_models():
    """Load models in background"""
    global tokenizers, models, kokoro_pipeline, models_status, loading_complete
    
    try:
        # Log versions for debugging
        import transformers
        logger.info(f"Transformers version: {transformers.__version__}")
        
        import huggingface_hub
        logger.info(f"Huggingface Hub version: {huggingface_hub.__version__}")
        
        # Load Kokoro for en
        try:
            from kokoro import KPipeline
            kokoro_pipeline = KPipeline(lang_code='a')  # 'a' for en
            models["en"] = "kokoro_loaded"
            models_status["en"] = "loaded"
            logger.info("Kokoro loaded successfully for en")
        except Exception as e:
            logger.error(f"Error loading Kokoro: {str(e)}")
            models_status["en"] = f"error: {str(e)}"
        
        # Load MMS models using VitsModel
        for lang, info in LANGUAGE_MODELS.items():
            if info["type"] == "mms":  # Skip Kokoro
                try:
                    model_name = info["model"]
                    
                    logger.info(f"Loading VitsModel for {lang}: {model_name}")
                    models_status[lang] = "loading"
                    
                    # Load tokenizer and model
                    tokenizer, model = load_vits_model(model_name)
                    
                    tokenizers[lang] = tokenizer
                    models[lang] = model
                    
                    models_status[lang] = "loaded"
                    logger.info(f"Model for {lang} loaded successfully")
                except Exception as e:
                    models_status[lang] = f"error: {str(e)}"
                    logger.error(f"Error loading model for {lang}: {str(e)}")
                    
                    # Try alternative loading methods
                    try:
                        logger.info(f"Trying alternative loading method for {lang}")
                        # Try using AutoModel
                        from transformers import AutoModel, AutoTokenizer
                        
                        tokenizer = AutoTokenizer.from_pretrained(model_name)
                        model = AutoModel.from_pretrained(model_name)
                        
                        tokenizers[lang] = tokenizer
                        models[lang] = model
                        
                        models_status[lang] = "loaded (AutoModel)"
                        logger.info(f"Model for {lang} loaded successfully using AutoModel")
                    except Exception as e2:
                        logger.error(f"Alternative loading also failed for {lang}: {str(e2)}")
                        models_status[lang] = f"error: All loading methods failed"
    
    except Exception as e:
        logger.error(f"Error during model loading: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    loading_complete = True
    logger.info("Model loading completed")

@app.on_event("startup")
async def startup_event():
    """Start model loading in background"""
    thread = threading.Thread(target=load_models)
    thread.daemon = True
    thread.start()

@app.get("/", 
    summary="API Information", 
    description="Returns information about the API and available languages")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Multilingual Speech Synthesis API", 
        "available_languages": list(LANGUAGE_MODELS.keys()),
        "loaded_languages": list(models.keys()),
        "loading_status": "complete" if loading_complete else "in_progress",
        "swagger_ui": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", 
    summary="Health Check", 
    description="Returns the health status of the API and models")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if models else "initializing",
        "models_loaded": len(models),
        "models_status": models_status,
        "loading_complete": loading_complete
    }

@app.post("/synthesize/", 
    summary="Synthesize Speech", 
    description="Converts text to speech in the specified language",
    response_description="Audio file in WAV format")
async def synthesize_speech(request: TextToSpeechRequest):
    """Generate speech from text"""
    language = request.language.lower()
    
    # Check if language is supported
    if language not in LANGUAGE_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"Language '{language}' not supported. Available: {list(LANGUAGE_MODELS.keys())}"
        )
    
    # Check if model is loaded
    if language not in models:
        if language in models_status and "error" in models_status[language]:
            raise HTTPException(
                status_code=500,
                detail=f"Model for {language} failed to load: {models_status[language]}"
            )
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Model for {language} is still loading. Please try again later."
            )
    
    try:
        # Generate speech
        logger.info(f"Generating speech for text: '{request.text}' in {language}")
        start_time = time.time()
        
        # Get model type
        model_type = LANGUAGE_MODELS[language]["type"]
        
        # Generate audio based on model type
        if model_type == "kokoro":
            # Use Kokoro for en
            if kokoro_pipeline is None:
                raise HTTPException(
                    status_code=500,
                    detail="Kokoro pipeline not loaded"
                )
            
            # Select voice
            voice = request.voice if request.voice in KOKORO_VOICES else "af_heart"
            
            # Generate speech with Kokoro
            logger.info(f"Using Kokoro with voice: {voice}")
            
            # Kokoro returns a generator, we need to collect all audio segments
            audio_segments = []
            sample_rate = 24000  # Kokoro uses 24kHz
            
            generator = kokoro_pipeline(request.text, voice=voice)
            for i, (gs, ps, segment_audio) in enumerate(generator):
                logger.info(f"Generated segment {i}: gs={gs}, ps={ps}, audio shape={segment_audio.shape}")
                audio_segments.append(segment_audio)
            
            # Concatenate all segments
            if audio_segments:
                audio = np.concatenate(audio_segments)
            else:
                raise HTTPException(
                    status_code=500,
                    detail="No audio generated by Kokoro"
                )
            
        else:
            # MMS model (African languages)
            model = models[language]
            tokenizer = tokenizers[language]
            
            logger.info(f"Using model type: {type(model).__name__}")
            
            # Tokenize input
            inputs = tokenizer(request.text, return_tensors="pt")
            
            # Generate audio
            with torch.no_grad():
                output = model(**inputs)
                
                # Get the waveform - try different attributes
                if hasattr(output, 'waveform'):
                    waveform = output.waveform
                elif hasattr(output, 'audio'):
                    waveform = output.audio
                elif hasattr(output, 'last_hidden_state'):
                    # For AutoModel, we might need to process differently
                    logger.warning("Model output has last_hidden_state, not waveform. This might not work correctly.")
                    waveform = output.last_hidden_state
                elif isinstance(output, tuple) and len(output) > 0:
                    waveform = output[0]
                else:
                    raise ValueError(f"Cannot extract waveform from model output of type {type(output)}")
                
                # Squeeze and convert to numpy
                audio = waveform.squeeze().cpu().numpy()
            
            # Get sample rate from model config if available
            sample_rate = getattr(model.config, "sampling_rate", 16000)
            
            logger.info(f"Raw audio shape: {audio.shape}")
            logger.info(f"Raw audio range: [{audio.min():.4f}, {audio.max():.4f}]")
            
            # Normalize audio properly
            audio = normalize_audio(audio)
        
        logger.info(f"Speech generated in {time.time() - start_time:.2f} seconds")
        
        # Use soundfile for WAV writing
        buf = io.BytesIO()
        sf.write(buf, audio, sample_rate, format='WAV', subtype='PCM_16')
        buf.seek(0)
        
        # Set filename for download
        filename = f"{language}_speech.wav"
        
        return StreamingResponse(
            buf, 
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/models", 
    summary="List Models", 
    description="Returns a list of all available models and their status")
async def list_models():
    """List all models and their status"""
    return {
        "available_models": LANGUAGE_MODELS,
        "loaded_models": list(models.keys()),
        "models_status": models_status,
        "loading_complete": loading_complete
    }

@app.get("/languages", 
    summary="List Languages", 
    description="Returns a list of all supported languages with sample texts")
async def list_languages():
    """List all supported languages with sample texts"""
    languages = {}
    for lang in LANGUAGE_MODELS.keys():
        languages[lang] = {
            "model": LANGUAGE_MODELS[lang]["model"],
            "type": LANGUAGE_MODELS[lang]["type"],
            "status": models_status.get(lang, "not loaded"),
            "sample_text": SAMPLE_TEXTS.get(lang, f"Sample text for {lang}")
        }
    return languages

@app.get("/voices", 
    summary="List Available Voices", 
    description="Returns a list of available voices for each language")
async def list_voices():
    """List available voices for each language"""
    return {
        "en": {
            "model": "kokoro",
            "voices": KOKORO_VOICES,
            "default_voice": "af_heart"
        },
        "african_languages": {
            "model": "mms",
            "voices": ["default"],
            "note": "MMS models currently only support a single voice per language"
        }
    }

@app.get("/debug", 
    summary="Debug Information", 
    description="Returns debug information about the environment and loaded modules")
async def debug_info():
    """Return debug information"""
    info = {
        "modules": {},
        "available_mms_models": []
    }
    
    # Check important modules
    modules_to_check = [
        "transformers", "torch", "numpy", "soundfile", 
        "huggingface_hub", "kokoro", "fastapi"
    ]
    
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            info["modules"][module_name] = {
                "version": getattr(module, "__version__", "unknown"),
                "path": getattr(module, "__file__", "unknown")
            }
        except ImportError:
            info["modules"][module_name] = "not installed"
    
    # Check if VitsModel is available
    try:
        from transformers.models.vits import VitsModel
        info["vits_model_available"] = True
        info["vits_model_location"] = "transformers.models.vits"
    except ImportError:
        try:
            from transformers import VitsModel
            info["vits_model_available"] = True
            info["vits_model_location"] = "transformers"
        except ImportError:
            info["vits_model_available"] = False
    
    # List some available MMS models
    info["available_mms_models"] = [
        "facebook/mms-tts-eng",  # en
        "facebook/mms-tts-hau",  # ha
        "facebook/mms-tts-ewe",  # ee
        "facebook/mms-tts-aka",  # tw/Akan
        "facebook/mms-tts-yor",  # Yoruba
        "facebook/mms-tts-ibo",  # Igbo
        "facebook/mms-tts-swa",  # Swahili
        "facebook/mms-tts-zul",  # Zulu
        "facebook/mms-tts-xho",  # Xhosa
        "facebook/mms-tts-amh",  # Amharic
    ]
    
    return info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5007, reload=True)
