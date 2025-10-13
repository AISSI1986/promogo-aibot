from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="Simple TTS API")

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

@app.get("/")
async def root():
    return {
        "message": "Simple Text-to-Speech API",
        "status": "running",
        "note": "This is a lightweight TTS service for free tier deployment"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "memory_usage": "minimal"}

@app.post("/synthesize/")
async def synthesize_speech(request: TextToSpeechRequest):
    """
    Simple TTS endpoint that returns a mock response
    For free tier deployment - no heavy AI models loaded
    """
    try:
        # Mock response for free tier
        return {
            "success": True,
            "message": f"Text '{request.text}' would be synthesized in {request.language}",
            "audio_url": None,
            "note": "This is a mock response for free tier deployment. Upgrade to use actual TTS models."
        }
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
    port = int(os.environ.get("PORT", 5007))
    uvicorn.run("simple_app:app", host="0.0.0.0", port=port, reload=True)
