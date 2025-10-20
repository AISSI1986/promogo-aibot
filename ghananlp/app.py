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
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from openai import OpenAI
from rasa_client import parse_intent_with_rasa

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

# --- Configuration ---
GHANA_NLP_API_KEY = os.getenv("GHANA_NLP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ.setdefault("OPENAI_API_KEY", OPENAI_API_KEY or "")

# Paths
DATA_DIR = os.getenv("PROMOGO_DATA_DIR", "files")
CHROMA_DIR = os.getenv("PROMOGO_CHROMA_DIR", "chroma_db")

# Initialize GhanaNLP
nlp = None

# Initialize GhanaNLP if API key is available
if GHANA_NLP_API_KEY:
    try:
        nlp = GhanaNLP(GHANA_NLP_API_KEY)
        logger.info("GhanaNLP initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GhanaNLP: {str(e)}")
        nlp = None
else:
    logger.warning("No GhanaNLP API key provided")

# Initialize OpenAI + LangChain vector store
llm = None
embeddings_model = None
retriever = None

try:
    if OPENAI_API_KEY:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
        llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
        vector_store = Chroma(
            collection_name="EZPROMO",
            embedding_function=embeddings_model,
            persist_directory=CHROMA_DIR,
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        logger.info("OpenAI + Chroma retriever initialized")
    else:
        logger.warning("OPENAI_API_KEY not provided; RAG disabled")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI/Chroma: {e}")

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

class ChatRequest(BaseModel):
    input_data: str  # raw text or base64 audio (if is_audio true)
    is_audio: bool = False
    source_lang: str = "twi"
    sender_id: str = "Promogo"
    history: Optional[list] = None

class ChatTurn(BaseModel):
    user: str
    bot: str

class ChatResponse(BaseModel):
    history: list

@app.get("/")
async def root():
    return {"message": "GhanaNLP Service API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "ghananlp",
        "ghananlp_available": nlp is not None,
        "api_key_configured": GHANA_NLP_API_KEY is not None
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
        response = nlp.translate(request.text, language_pair=lang_pair)
        
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
            response = nlp.speech_to_text(temp_file_path, language=language)
            
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
    Convert text to speech using GhanaNLP library with fallback
    """
    try:
        # Map language code
        language = LANGUAGE_MAPPING.get(request.language, request.language)
        
        if not nlp:
            logger.warning("GhanaNLP not available, returning placeholder audio")
            return _create_placeholder_audio(request.text, language, request.voice)
        
        # Use GhanaNLP library for TTS
        response = nlp.text_to_speech(request.text, lang=language)
        
        # Handle different response formats
        if isinstance(response, str):
            # If response is a string, it might be a file path or base64 data
            if response.startswith('data:audio') or len(response) > 100:
                # Likely base64 audio data
                audio_data = response
            else:
                # Might be a file path, read the file
                try:
                    with open(response, 'rb') as f:
                        audio_data = base64.b64encode(f.read()).decode('utf-8')
                except:
                    audio_data = base64.b64encode(response.encode()).decode('utf-8')
        elif isinstance(response, dict):
            # Handle dictionary response
            if "audio_data" in response:
                audio_data = response["audio_data"]
            elif "audio" in response:
                audio_data = response["audio"]
            elif "file" in response:
                # Read audio file
                with open(response["file"], 'rb') as f:
                    audio_data = base64.b64encode(f.read()).decode('utf-8')
            else:
                logger.warning(f"Unexpected GhanaNLP TTS response format: {response}, using placeholder")
                return _create_placeholder_audio(request.text, language, request.voice)
        else:
            logger.warning(f"Unexpected GhanaNLP TTS response type: {type(response)}, using placeholder")
            return _create_placeholder_audio(request.text, language, request.voice)
        
        return TTSResponse(
            audio_data=audio_data,
            language=language,
            voice=request.voice or "default"
        )
            
    except Exception as e:
        logger.error(f"TTS error: {str(e)}, using placeholder")
        return _create_placeholder_audio(request.text, language, request.voice)

def _create_placeholder_audio(text: str, language: str, voice: str = None) -> TTSResponse:
    """
    Create a placeholder audio response when GhanaNLP is not available
    """
    # Create a proper WAV file with correct header
    # 44.1kHz, 16-bit, mono, 1 second of silence
    sample_rate = 44100
    duration = 1  # 1 second
    num_samples = sample_rate * duration
    
    # WAV header (44 bytes)
    wav_header = bytearray(44)
    wav_header[0:4] = b'RIFF'
    wav_header[4:8] = (36 + num_samples * 2).to_bytes(4, 'little')  # File size - 8
    wav_header[8:12] = b'WAVE'
    wav_header[12:16] = b'fmt '
    wav_header[16:20] = (16).to_bytes(4, 'little')  # fmt chunk size
    wav_header[20:22] = (1).to_bytes(2, 'little')   # Audio format (PCM)
    wav_header[22:24] = (1).to_bytes(2, 'little')   # Number of channels
    wav_header[24:28] = sample_rate.to_bytes(4, 'little')  # Sample rate
    wav_header[28:32] = (sample_rate * 2).to_bytes(4, 'little')  # Byte rate
    wav_header[32:34] = (2).to_bytes(2, 'little')   # Block align
    wav_header[34:36] = (16).to_bytes(2, 'little')  # Bits per sample
    wav_header[36:40] = b'data'
    wav_header[40:44] = (num_samples * 2).to_bytes(4, 'little')  # Data size
    
    # Create silence data (16-bit samples)
    silence_data = b'\x00' * (num_samples * 2)
    
    # Combine header and data
    wav_data = bytes(wav_header) + silence_data
    audio_data = base64.b64encode(wav_data).decode('utf-8')

    return TTSResponse(
        audio_data=audio_data,
        language=language,
        voice=voice or "default"
    )


def _lang_to_code(name: str) -> str:
    mapping = {
        "english": "en",
        "twi": "tw",
        "ga": "ga",
        "ewe": "ee",
        "hausa": "ha",
        "dagbani": "dagbani",
    }
    return mapping.get((name or "").lower(), "tw")


def _transcribe_audio_file(filepath: str, source_lang: str) -> str:
    # For now always use GhanaNLP STT as per project direction
    if not nlp:
        raise HTTPException(status_code=500, detail="GhanaNLP not initialized - API key required")
    response = nlp.speech_to_text(filepath, language=_lang_to_code(source_lang))
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        if "text" in response:
            return response["text"]
        if "translation" in response:
            return response["translation"]
        if "message" in response:
            logger.warning(f"GhanaNLP STT message: {response['message']}")
            return response["message"]
    return str(response)


def _rag_answer(user_message: str, history: list) -> str:
    if not (llm and retriever):
        return "I'm here to help, but RAG is currently unavailable."
    try:
        docs = retriever.invoke(user_message)
        knowledge = "".join([(d.page_content or "") + "\n\n" for d in docs])
        rag_prompt = f"""
You are an assistant which answers questions based on knowledge provided.
You can also answer questions based on the conversation history.
You can also ask clarifying questions if the user is not clear.
You should treat every instance of the words 'Pramogana', PromoGhana and EZPromo as 'PromoGo'.
The question: {user_message}
Conversation history: {history}
The knowledge: {knowledge}
"""
        accumulated = []
        for chunk in llm.stream(rag_prompt):
            if hasattr(chunk, "content") and chunk.content:
                accumulated.append(chunk.content)
        return "".join(accumulated).strip()
    except Exception as e:
        logger.error(f"RAG error: {e}")
        return "I'm sorry, I couldn't retrieve an answer right now."


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Unified chat endpoint: optional audio STT, Rasa intent, fallback to RAG."""
    history = request.history or []
    source_code = _lang_to_code(request.source_lang)

    # If audio, decode and transcribe via GhanaNLP
    if request.is_audio:
        try:
            audio_bytes = base64.b64decode(request.input_data)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            try:
                user_message = _transcribe_audio_file(temp_path, request.source_lang)
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid audio data: {e}")
    else:
        user_message = request.input_data

    history.append({"user": user_message, "bot": ""})

    # Rasa intent parsing
    intent, bot_text, confidence = parse_intent_with_rasa(request.sender_id, user_message, source_code)
    if intent and confidence >= 0.7 and bot_text:
        history[-1]["bot"] = bot_text
        return ChatResponse(history=history)

    # Fallback to RAG
    answer = _rag_answer(user_message, history)
    history[-1]["bot"] = answer
    return ChatResponse(history=history)

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
