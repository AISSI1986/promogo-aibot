from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="Simple STT API")

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

@app.get("/")
async def root():
    return {
        "message": "Simple Speech-to-Text API",
        "status": "running",
        "note": "This is a lightweight STT service for free tier deployment"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "memory_usage": "minimal"}

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Simple STT endpoint that returns a mock response
    For free tier deployment - no heavy AI models loaded
    """
    try:
        # Mock response for free tier
        return TranscriptionResponse(
            text="This is a mock transcription for free tier deployment. Upload audio files to get actual transcriptions.",
            confidence=0.95,
            language="en"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_languages():
    """Get supported languages"""
    return {
        "supported_languages": ["en", "fr", "es", "de", "it", "pt", "ru", "zh", "ja", "ko"],
        "note": "Mock languages for free tier deployment"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5006))
    uvicorn.run("simple_app:app", host="0.0.0.0", port=port, reload=True)
