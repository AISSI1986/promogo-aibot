from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Promogo Chatbot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    message: str
    sender: str = "user"

class MessageResponse(BaseModel):
    text: str
    recipient_id: str = "user"

# Simple chatbot responses
CHATBOT_RESPONSES = {
    "hello": "Hello! How can I help you today?",
    "hi": "Hi there! What can I do for you?",
    "help": "I'm here to help! You can ask me questions or tell me what you need.",
    "goodbye": "Goodbye! Have a great day!",
    "thanks": "You're welcome! Is there anything else I can help you with?",
    "default": "I understand. Could you please provide more details about what you need help with?"
}

@app.get("/")
async def root():
    return {"message": "Promogo Chatbot API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhooks/rest/webhook", response_model=list)
async def chat_webhook(request: MessageRequest):
    """
    Simple chatbot webhook that mimics Rasa's webhook interface
    """
    try:
        user_message = request.message.lower().strip()
        
        # Simple keyword matching
        response_text = CHATBOT_RESPONSES.get(user_message, CHATBOT_RESPONSES["default"])
        
        # Return in Rasa's expected format
        return [{"text": response_text, "recipient_id": request.sender}]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/model/parse")
async def parse_message(request: MessageRequest):
    """
    Parse endpoint for NLU (mimics Rasa's parse endpoint)
    """
    try:
        user_message = request.message.lower().strip()
        
        # Simple intent detection
        intent = "general"
        confidence = 0.8
        
        if any(word in user_message for word in ["hello", "hi", "hey"]):
            intent = "greeting"
            confidence = 0.9
        elif any(word in user_message for word in ["help", "support", "assist"]):
            intent = "help"
            confidence = 0.9
        elif any(word in user_message for word in ["goodbye", "bye", "see you"]):
            intent = "goodbye"
            confidence = 0.9
        
        return {
            "text": request.message,
            "intent": {"name": intent, "confidence": confidence},
            "entities": [],
            "intent_ranking": [{"name": intent, "confidence": confidence}]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5005, reload=True)
