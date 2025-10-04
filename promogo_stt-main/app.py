from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io
import numpy as np
import soundfile as sf
from typing import Optional, Dict, List, Any
import logging
import time
import threading
import torch
import os
import importlib
import shutil
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurer le répertoire de cache pour les modèles Hugging Face
# Utiliser un répertoire avec les bonnes permissions
MODELS_CACHE_DIR = os.environ.get("MODELS_CACHE_DIR", "/tmp/models_cache")

# Créer le répertoire de cache s'il n'existe pas
os.makedirs(MODELS_CACHE_DIR, exist_ok=True)

# Vérifier les permissions du répertoire
try:
    # Tester si on peut écrire dans le répertoire
    test_file = os.path.join(MODELS_CACHE_DIR, "test_permissions.txt")
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
    logger.info(f"Cache directory {MODELS_CACHE_DIR} is writable")
except Exception as e:
    logger.error(f"Cache directory {MODELS_CACHE_DIR} is not writable: {str(e)}")
    # Essayer un autre répertoire
    MODELS_CACHE_DIR = "/tmp/models_cache_alt"
    os.makedirs(MODELS_CACHE_DIR, exist_ok=True)
    logger.info(f"Using alternative cache directory: {MODELS_CACHE_DIR}")

# Configurer la variable d'environnement pour Hugging Face
os.environ["TRANSFORMERS_CACHE"] = MODELS_CACHE_DIR
os.environ["HF_HOME"] = MODELS_CACHE_DIR

# Initialize FastAPI app
app = FastAPI(
    title="Multilingual Speech Recognition API",
    description="API for speech-to-text transcription in English, Hausa, Twi, and Ewe",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Length", "Content-Range"],
    max_age=1800,
)

# Define response model
class TranscriptionResponse(BaseModel):
    transcription: str
    language: str
    confidence: Optional[float] = None
    processing_time: float
    model_used: str

# Global variables
models = {}
processors = {}
models_status: Dict[str, str] = {}
loading_complete = False

# Define language models with their specific Hugging Face models
LANGUAGE_MODELS = {
    "en": {
        "model_id": "openai/whisper-small",
        "description": "Whisper model for English",
        "name": "English",
    },
    "ha": {
        "model_id": "DrishtiSharma/whisper-large-v2-hausa",
        "description": "Whisper model fine-tuned for Hausa",
        "name": "Hausa"
    },
    "tw": {
        "model_id": "femursmith/intermediate-asr-ashanti-twi",
        "description": "ASR model for Ashanti Twi",
        "name": "Twi (Ashanti)"
    },
    "ee": {
        "model_id": "asr-africa/wav2vec2-xls-r-ewe-100-hours",
        "description": "wave2vec model fine-tuned for Ewe",
        "name": "Ewe"
    }
}

def load_model_for_language(lang: str, model_info: dict):
    """Load a specific model for a language using AutoProcessor and AutoModelForSpeechSeq2Seq"""
    model_id = model_info["model_id"]
    
    try:
        logger.info(f"Loading model for {lang}: {model_id}")
        models_status[lang] = "loading"
        
        # Déterminer le device (GPU ou CPU)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Utiliser AutoProcessor et AutoModelForSpeechSeq2Seq pour tous les modèles
        # Spécifier explicitement le répertoire de cache
        processor = AutoProcessor.from_pretrained(
            model_id,
            cache_dir=MODELS_CACHE_DIR,
            local_files_only=False,
            use_auth_token=os.environ.get("HF_TOKEN")
        )
        
        # Essayer de charger avec AutoModelForSpeechSeq2Seq
        try:
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id,
                cache_dir=MODELS_CACHE_DIR,
                local_files_only=False,
                use_auth_token=os.environ.get("HF_TOKEN")
            ).to(device)
        except Exception as model_error:
            logger.warning(f"Error loading with AutoModelForSpeechSeq2Seq: {str(model_error)}")
            logger.info(f"Trying alternative loading method for {lang}")
            
            # Essayer de détecter automatiquement le bon type de modèle
            from transformers import AutoModelForCTC, WhisperForConditionalGeneration
            
            if "whisper" in model_id.lower():
                model = WhisperForConditionalGeneration.from_pretrained(
                    model_id,
                    cache_dir=MODELS_CACHE_DIR,
                    local_files_only=False,
                    use_auth_token=os.environ.get("HF_TOKEN")
                ).to(device)
                logger.info(f"Loaded {lang} model as WhisperForConditionalGeneration")
            else:
                model = AutoModelForCTC.from_pretrained(
                    model_id,
                    cache_dir=MODELS_CACHE_DIR,
                    local_files_only=False,
                    use_auth_token=os.environ.get("HF_TOKEN")
                ).to(device)
                logger.info(f"Loaded {lang} model as AutoModelForCTC")
        
        processors[lang] = processor
        models[lang] = model
        models_status[lang] = "loaded"
        logger.info(f"Model for {lang} loaded successfully on {device}")
        
    except PermissionError as pe:
        error_msg = f"Permission error loading model for {lang}: {str(pe)}"
        models_status[lang] = f"error: {error_msg}"
        logger.error(error_msg)
        
        # Essayer de nettoyer les fichiers de verrouillage
        try:
            model_cache_path = os.path.join(MODELS_CACHE_DIR, f"models--{model_id.replace('/', '--')}")
            if os.path.exists(model_cache_path):
                lock_files = [f for f in os.listdir(model_cache_path) if f.endswith('.lock')]
                for lock_file in lock_files:
                    lock_path = os.path.join(model_cache_path, lock_file)
                    logger.info(f"Removing lock file: {lock_path}")
                    os.remove(lock_path)
                logger.info(f"Removed {len(lock_files)} lock files for {lang} model")
        except Exception as clean_error:
            logger.error(f"Error cleaning lock files: {str(clean_error)}")
    
    except Exception as e:
        models_status[lang] = f"error: {str(e)}"
        logger.error(f"Error loading model for {lang}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def load_models():
    """Load all models in background"""
    global loading_complete
    
    try:
        # Log system info
        import transformers
        logger.info(f"Transformers version: {transformers.__version__}")
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        
        logger.info(f"Using models cache directory: {MODELS_CACHE_DIR}")
        
        # Load models for each language
        for lang, model_info in LANGUAGE_MODELS.items():
            load_model_for_language(lang, model_info)
    
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
        "message": "Multilingual Speech Recognition API", 
        "available_languages": list(LANGUAGE_MODELS.keys()),
        "models_loaded": list(models.keys()),
        "loading_status": "complete" if loading_complete else "in_progress",
        "models_cache_dir": MODELS_CACHE_DIR,
        "swagger_ui": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", 
    summary="Health Check", 
    description="Returns the health status of the API and models")
async def health_check():
    """Health check endpoint"""
    memory_info = {}
    if torch.cuda.is_available():
        memory_info["cuda"] = {
            "total": f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB",
            "allocated": f"{torch.cuda.memory_allocated() / 1e9:.2f} GB",
            "cached": f"{torch.cuda.memory_reserved() / 1e9:.2f} GB",
        }
    
    # Vérifier l'espace disque disponible pour le cache
    try:
        import shutil
        disk_usage = shutil.disk_usage(MODELS_CACHE_DIR)
        disk_info = {
            "total": f"{disk_usage.total / 1e9:.2f} GB",
            "used": f"{disk_usage.used / 1e9:.2f} GB",
            "free": f"{disk_usage.free / 1e9:.2f} GB",
            "percent_used": f"{disk_usage.used / disk_usage.total * 100:.1f}%"
        }
    except Exception as e:
        disk_info = {"error": str(e)}
    
    return {
        "status": "healthy" if models else "initializing",
        "models_loaded": len(models),
        "models_status": models_status,
        "loading_complete": loading_complete,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "memory": memory_info,
        "disk": disk_info,
        "models_cache_dir": MODELS_CACHE_DIR
    }

@app.post("/transcribe", 
summary="Transcribe Speech", 
description="Converts speech to text in the specified language",
response_model=TranscriptionResponse)
async def transcribe_speech(
    audio: UploadFile = File(...),
    language: str = Form("en")
):
    """Transcribe speech from audio file"""
    language = language.lower()

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
        # Read audio file
        logger.info(f"Processing audio file: {audio.filename} for language: {language}")
        start_time = time.time()
        
        # Read audio content
        audio_content = await audio.read()
        
        # Créer un fichier temporaire pour l'audio d'entrée
        import tempfile
        import subprocess
        import os
        
        # Créer un répertoire temporaire s'il n'existe pas
        temp_dir = "/tmp/audio_processing"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Sauvegarder l'audio reçu dans un fichier temporaire
        input_file = os.path.join(temp_dir, f"input_{int(time.time())}.webm")
        with open(input_file, "wb") as f:
            f.write(audio_content)
        
        logger.info(f"Saved input audio to {input_file}")
        
        # Convertir l'audio en WAV avec ffmpeg
        output_file = os.path.join(temp_dir, f"output_{int(time.time())}.wav")
        
        try:
            # Vérifier si ffmpeg est installé
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
            
            # Convertir l'audio en WAV 16kHz mono
            cmd = [
                "ffmpeg", 
                "-i", input_file,
                "-ar", "16000",  # Fréquence d'échantillonnage 16kHz
                "-ac", "1",      # Mono
                "-y",            # Écraser le fichier de sortie s'il existe
                output_file
            ]
            
            logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"ffmpeg conversion successful: {output_file}")
            
            # Charger l'audio converti avec soundfile
            audio_array, sample_rate = sf.read(output_file)
            logger.info(f"Loaded converted audio: {len(audio_array)} samples, {sample_rate}Hz")
            
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Error with ffmpeg: {str(e)}")
            
            # Fallback: essayer de charger directement le fichier d'entrée
            try:
                audio_array, sample_rate = sf.read(input_file)
                logger.info(f"Loaded input audio directly: {len(audio_array)} samples, {sample_rate}Hz")
            except Exception as sf_error:
                logger.error(f"Error reading input audio with soundfile: {str(sf_error)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported audio format. Please provide a WAV file or install ffmpeg on the server."
                )
        
        finally:
            # Nettoyer les fichiers temporaires
            try:
                if os.path.exists(input_file):
                    os.remove(input_file)
                if os.path.exists(output_file):
                    os.remove(output_file)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary files: {str(e)}")
        
        # Get model and processor
        model = models[language]
        processor = processors[language]
        
        # Process audio with the model
        logger.info(f"Processing audio with model: {LANGUAGE_MODELS[language]['model_id']}")
        
        # Déterminer le type d'entrée attendu par le modèle
        inputs = processor(
            audio_array, 
            sampling_rate=sample_rate, 
            return_tensors="pt"
        )
        
        # Déplacer les entrées sur le même device que le modèle
        for key in inputs:
            if isinstance(inputs[key], torch.Tensor):
                inputs[key] = inputs[key].to(model.device)
        
        # Generate transcription
        with torch.no_grad():
            # Vérifier si le modèle a une méthode generate
            if hasattr(model, 'generate'):
                logger.info(f"Using generate method for {language} model")
                
                # Pour les modèles de type seq2seq (Whisper, etc.)
                generate_kwargs = {}
                
                # Ajouter des paramètres spécifiques pour Whisper si nécessaire
                if "whisper" in LANGUAGE_MODELS[language]["model_id"].lower():
                    if hasattr(processor, 'get_decoder_prompt_ids'):
                        generate_kwargs["forced_decoder_ids"] = processor.get_decoder_prompt_ids(
                            language=language,
                            task="transcribe"
                        )
                
                # Déterminer le nom du paramètre d'entrée
                input_key = None
                if hasattr(inputs, 'input_features'):
                    input_key = 'input_features'
                elif hasattr(inputs, 'input_values'):
                    input_key = 'input_values'
                else:
                    # Essayer de trouver la clé d'entrée dans le dictionnaire
                    for key in ['input_features', 'input_values', 'inputs']:
                        if key in inputs:
                            input_key = key
                            break
                
                if input_key:
                    # Utiliser la clé trouvée
                    generate_kwargs[input_key] = inputs[input_key] if isinstance(inputs, dict) else getattr(inputs, input_key)
                else:
                    # Passer tout le dictionnaire d'entrées
                    generate_kwargs = inputs
                
                # Générer la transcription
                generated_ids = model.generate(**generate_kwargs)
                
                # Décoder les IDs générés
                transcription = processor.batch_decode(
                    generated_ids, 
                    skip_special_tokens=True
                )[0]
                
                confidence = 0.9  # Valeur par défaut
            else:
                logger.info(f"Using logits method for {language} model")
                
                # Pour les modèles de type CTC (Wav2Vec2, etc.)
                # Déterminer le nom du paramètre d'entrée
                if 'input_values' in inputs:
                    logits = model(input_values=inputs['input_values']).logits
                else:
                    # Essayer avec les entrées complètes
                    logits = model(**inputs).logits
                
                predicted_ids = torch.argmax(logits, dim=-1)
                
                # Décoder les IDs prédits
                if hasattr(processor, 'batch_decode'):
                    transcription = processor.batch_decode(predicted_ids)[0]
                else:
                    transcription = processor.decode(predicted_ids[0])
                
                # Calculer la confiance si possible
                if hasattr(torch.nn.functional, 'softmax'):
                    probs = torch.nn.functional.softmax(logits, dim=-1)
                    confidence = float(probs.max(dim=-1).values.mean())
                else:
                    confidence = 0.9  # Valeur par défaut
        
        processing_time = time.time() - start_time
        logger.info(f"Transcription completed in {processing_time:.2f} seconds")
        
        return TranscriptionResponse(
            transcription=transcription.strip(),
            language=language,
            confidence=confidence,
            processing_time=processing_time,
            model_used=LANGUAGE_MODELS[language]["model_id"]
        )
        
    except Exception as e:
        logger.error(f"Error transcribing speech: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error transcribing speech: {str(e)}")

@app.get("/models", 
    summary="List Models", 
    description="Returns a list of all available models and their status")
async def list_models():
    """List all models and their status"""
    models_info = {}
    for lang, info in LANGUAGE_MODELS.items():
        models_info[lang] = {
            **info,
            "status": models_status.get(lang, "not loaded"),
            "loaded": lang in models
        }
    
    return {
        "models": models_info,
        "loading_complete": loading_complete,
        "models_cache_dir": MODELS_CACHE_DIR
    }

@app.get("/languages", 
    summary="List Languages", 
    description="Returns a list of all supported languages with details")
async def list_languages():
    """List all supported languages with details"""
    languages = {}
    for lang, info in LANGUAGE_MODELS.items():
        languages[lang] = {
            "code": lang,
            "name": info.get("name", lang),
            "model_id": info["model_id"],
            "description": info["description"],
            "status": models_status.get(lang, "not loaded")
        }
    return languages

@app.get("/debug", 
    summary="Debug Information", 
    description="Returns debug information about the environment and loaded modules")
async def debug_info():
    """Return debug information"""
    info = {
        "modules": {},
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "models_in_memory": list(models.keys()),
        "processors_in_memory": list(processors.keys()),
        "models_cache_dir": MODELS_CACHE_DIR
    }
    
    # Vérifier les permissions du répertoire de cache
    cache_permissions = {
        "exists": os.path.exists(MODELS_CACHE_DIR),
        "is_dir": os.path.isdir(MODELS_CACHE_DIR) if os.path.exists(MODELS_CACHE_DIR) else False,
    }
    
    if cache_permissions["exists"] and cache_permissions["is_dir"]:
        try:
            # Tester si on peut écrire dans le répertoire
            test_file = os.path.join(MODELS_CACHE_DIR, "test_permissions.txt")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            cache_permissions["writable"] = True
        except Exception as e:
            cache_permissions["writable"] = False
            cache_permissions["error"] = str(e)
        
        # Obtenir les permissions du répertoire
        import stat
        try:
            st = os.stat(MODELS_CACHE_DIR)
            cache_permissions["mode"] = stat.filemode(st.st_mode)
            cache_permissions["uid"] = st.st_uid
            cache_permissions["gid"] = st.st_gid
            
            # Obtenir le propriétaire et le groupe
            import pwd
            import grp
            try:
                cache_permissions["owner"] = pwd.getpwuid(st.st_uid).pw_name
            except:
                cache_permissions["owner"] = f"uid:{st.st_uid}"
            
            try:
                cache_permissions["group"] = grp.getgrgid(st.st_gid).gr_name
            except:
                cache_permissions["group"] = f"gid:{st.st_gid}"
        except Exception as e:
            cache_permissions["stat_error"] = str(e)
    
    info["cache_permissions"] = cache_permissions
    
    # Ajouter des informations sur la mémoire CUDA si disponible
    if torch.cuda.is_available():
        info["cuda_memory"] = {
            "total": f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB",
            "allocated": f"{torch.cuda.memory_allocated() / 1e9:.2f} GB",
            "cached": f"{torch.cuda.memory_reserved() / 1e9:.2f} GB",
        }
    
    # Check important modules
    modules_to_check = [
        "transformers", "torch", "numpy", "soundfile", 
        "librosa", "fastapi", "pydantic"
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
    
    # Ajouter des informations sur les modèles chargés
    model_details = {}
    for lang in models:
        model = models[lang]
        model_details[lang] = {
            "type": type(model).__name__,
            "device": str(next(model.parameters()).device),
            "parameters": sum(p.numel() for p in model.parameters()),
            "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad)
        }
    
    info["model_details"] = model_details
    
    # Vérifier l'espace disque
    try:
        import shutil
        disk_usage = shutil.disk_usage(MODELS_CACHE_DIR)
        info["disk_usage"] = {
            "total": f"{disk_usage.total / 1e9:.2f} GB",
            "used": f"{disk_usage.used / 1e9:.2f} GB",
            "free": f"{disk_usage.free / 1e9:.2f} GB",
            "percent_used": f"{disk_usage.used / disk_usage.total * 100:.1f}%"
        }
    except Exception as e:
        info["disk_usage_error"] = str(e)
    
    # Lister les fichiers dans le répertoire de cache
    try:
        cache_files = os.listdir(MODELS_CACHE_DIR)
        info["cache_files"] = cache_files[:20]  # Limiter à 20 fichiers pour éviter une réponse trop grande
        info["cache_file_count"] = len(cache_files)
    except Exception as e:
        info["cache_files_error"] = str(e)
    
    return info

@app.post("/unload_model/{language}", 
    summary="Unload Model", 
    description="Unloads a model from memory to free up resources")
async def unload_model(language: str):
    """Unload a model from memory"""
    language = language.lower()
    
    if language not in LANGUAGE_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"Language '{language}' not supported. Available: {list(LANGUAGE_MODELS.keys())}"
        )
    
    if language in models:
        try:
            # Supprimer les références aux modèles et processeurs
            del models[language]
            del processors[language]
            
            # Forcer le garbage collector
            import gc
            gc.collect()
            
            # Vider le cache CUDA si disponible
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            models_status[language] = "unloaded"
            logger.info(f"Model for {language} unloaded successfully")
            
            return {"message": f"Model for {language} unloaded successfully"}
        except Exception as e:
            logger.error(f"Error unloading model for {language}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error unloading model: {str(e)}"
            )
    else:
        return {"message": f"Model for {language} was not loaded"}

@app.post("/load_model/{language}", 
    summary="Load Model", 
    description="Loads a model into memory")
async def load_model_endpoint(language: str):
    """Load a model into memory"""
    language = language.lower()
    
    if language not in LANGUAGE_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"Language '{language}' not supported. Available: {list(LANGUAGE_MODELS.keys())}"
        )
    
    if language in models:
        return {"message": f"Model for {language} is already loaded"}
    
    try:
        # Charger le modèle
        load_model_for_language(language, LANGUAGE_MODELS[language])
        
        if language in models:
            return {"message": f"Model for {language} loaded successfully"}
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to load model for {language}: {models_status.get(language, 'unknown error')}"
            )
    except Exception as e:
        logger.error(f"Error loading model for {language}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error loading model: {str(e)}"
        )

@app.post("/clear_cache", 
    summary="Clear Cache", 
    description="Clears the models cache directory to resolve permission issues")
async def clear_cache():
    """Clear the models cache directory"""
    try:
        # Vérifier si des modèles sont chargés
        if models:
            return {
                "success": False,
                "message": "Cannot clear cache while models are loaded. Unload all models first.",
                "loaded_models": list(models.keys())
            }
        
        # Compter les fichiers avant suppression
        file_count_before = sum(len(files) for _, _, files in os.walk(MODELS_CACHE_DIR))
        
        # Supprimer tous les fichiers .lock
        lock_files_removed = 0
        for root, dirs, files in os.walk(MODELS_CACHE_DIR):
            for file in files:
                if file.endswith('.lock'):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        lock_files_removed += 1
                    except Exception as e:
                        logger.error(f"Error removing lock file {file_path}: {str(e)}")
        
        # Compter les fichiers après suppression
        file_count_after = sum(len(files) for _, _, files in os.walk(MODELS_CACHE_DIR))
        
        return {
            "success": True,
            "message": f"Cache cleaned. Removed {lock_files_removed} lock files.",
            "cache_dir": MODELS_CACHE_DIR,
            "files_before": file_count_before,
            "files_after": file_count_after
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "message": f"Error clearing cache: {str(e)}",
            "cache_dir": MODELS_CACHE_DIR
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)
