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

# Multilingual chatbot responses for Promogo's target languages
CHATBOT_RESPONSES = {
    "en": {
        "greeting": "Hello! How can I help you today?",
        "help": "I'm here to help! You can ask me questions or tell me what you need.",
        "goodbye": "Goodbye! Have a great day!",
        "thanks": "You're welcome! Is there anything else I can help you with?",
        "seller_app": "I'll help you access the seller app. Please visit https://seller.promogo.com",
        "default": "I understand. Could you please provide more details about what you need help with?"
    },
    "ha": {
        "greeting": "Sannu! Yaya zan iya taimaka muku a yau?",
        "help": "Ina nan don taimaka! Kuna iya tambayar ni tambayoyi ko gaya mani abin da kuke bukata.",
        "goodbye": "Barka da zuwa! Ku sami ranar mai kyau!",
        "thanks": "Barka da zuwa! Akwai wani abu da zan iya taimaka muku?",
        "seller_app": "Zan taimaka muku shiga app na mai sayarwa. Don Allah ku ziyarci https://seller.promogo.com",
        "default": "Na fahimci. Don Allah ku ba da cikakkun bayanai game da abin da kuke bukata."
    },
    "tw": {
        "greeting": "Akwaaba! Ɛdeɛn na metumi ayɛ wo anɔpa yi?",
        "help": "Mewɔ hɔ sɛ mebɛboa wo! Wubetumi ase me nsɛm anaa ka deɛ wohia no kyerɛ me.",
        "goodbye": "Akyire! Wonya da pa!",
        "thanks": "Akwaaba! Wɔwɔ biribi foforo a metumi ayɛ wo?",
        "seller_app": "Mebɛboa wo sɛ wokɔ seller app no mu. Yɛsrɛ wo kɔ https://seller.promogo.com",
        "default": "Mete aseɛ. Yɛsrɛ wo ma nsɛm a ɛho hia no fa deɛ wohia no ho."
    },
    "ee": {
        "greeting": "Woezɔ! Aleke nànye nàwòa le ɣeyiɣi sia?",
        "help": "Meléa nàwòa! Àte ŋu àbi nànye nàwòa le nu siwo nàdi be?",
        "goodbye": "Woezɔ! Nàwòa ɣeyiɣi nyuie!",
        "thanks": "Woezɔ! Meléa nu bubu siwo nàte ŋu àwòa?",
        "seller_app": "Mawòa nàkɔ seller app la me. Yèsrɛ nàkɔ https://seller.promogo.com",
        "default": "Mete ŋu. Yèsrɛ nàna nu siwo nàdi be le nu siwo nàdi be la ŋuti."
    }
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
    Multilingual chatbot webhook that mimics Rasa's webhook interface
    """
    try:
        user_message = request.message.lower().strip()
        
        # Detect language based on content
        detected_language = detect_language(user_message)
        
        # Detect intent
        intent = detect_intent(user_message, detected_language)
        
        # Get appropriate response
        response_text = get_response(intent, detected_language)
        
        # Return in Rasa's expected format
        return [{"text": response_text, "recipient_id": request.sender}]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def detect_language(text):
    """
    Simple language detection based on keywords
    """
    # Hausa keywords
    hausa_keywords = ["sannu", "na gode", "barka", "yaya", "ina", "wane", "me", "don"]
    # Twi keywords  
    twi_keywords = ["akwaaba", "medaase", "ɛte sɛn", "wo ho te sɛn", "ɛdeɛn", "wo", "me", "sɛ"]
    # Ewe keywords
    ewe_keywords = ["woezɔ", "akpe", "aleke", "nànye", "nàwòa", "le", "nu", "siwo"]
    
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in hausa_keywords):
        return "ha"
    elif any(keyword in text_lower for keyword in twi_keywords):
        return "tw"
    elif any(keyword in text_lower for keyword in ewe_keywords):
        return "ee"
    else:
        return "en"  # Default to English

def detect_intent(text, language):
    """
    Detect user intent based on keywords
    """
    text_lower = text.lower()
    
    # Greeting patterns
    greeting_patterns = {
        "en": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
        "ha": ["sannu", "barka", "yaya"],
        "tw": ["akwaaba", "ɛte sɛn", "wo ho te sɛn"],
        "ee": ["woezɔ", "aleke", "nànye"]
    }
    
    # Help patterns
    help_patterns = {
        "en": ["help", "support", "assist", "how", "what", "can you"],
        "ha": ["taimaka", "yaya", "me", "za"],
        "tw": ["boa", "sɛn", "deɛ", "wo"],
        "ee": ["wòa", "aleke", "nu", "siwo"]
    }
    
    # Seller app patterns
    seller_patterns = {
        "en": ["seller", "app", "sell", "marketplace", "business"],
        "ha": ["mai sayarwa", "app", "sayar", "kasuwa"],
        "tw": ["seller", "app", "tɔn", "kasuwa"],
        "ee": ["seller", "app", "tɔn", "kasuwa"]
    }
    
    # Goodbye patterns
    goodbye_patterns = {
        "en": ["goodbye", "bye", "see you", "farewell"],
        "ha": ["barka", "zuwa", "sai"],
        "tw": ["akyire", "da", "pa"],
        "ee": ["woezɔ", "ɣeyiɣi", "nyuie"]
    }
    
    # Thanks patterns
    thanks_patterns = {
        "en": ["thank", "thanks", "appreciate"],
        "ha": ["na gode", "gode", "na"],
        "tw": ["medaase", "daase", "meda"],
        "ee": ["akpe", "akpe na", "akpe"]
    }
    
    if any(pattern in text_lower for pattern in greeting_patterns.get(language, greeting_patterns["en"])):
        return "greeting"
    elif any(pattern in text_lower for pattern in help_patterns.get(language, help_patterns["en"])):
        return "help"
    elif any(pattern in text_lower for pattern in seller_patterns.get(language, seller_patterns["en"])):
        return "seller_app"
    elif any(pattern in text_lower for pattern in goodbye_patterns.get(language, goodbye_patterns["en"])):
        return "goodbye"
    elif any(pattern in text_lower for pattern in thanks_patterns.get(language, thanks_patterns["en"])):
        return "thanks"
    else:
        return "default"

def get_response(intent, language):
    """
    Get appropriate response based on intent and language
    """
    language_responses = CHATBOT_RESPONSES.get(language, CHATBOT_RESPONSES["en"])
    return language_responses.get(intent, language_responses["default"])

@app.post("/model/parse")
async def parse_message(request: MessageRequest):
    """
    Parse endpoint for NLU (mimics Rasa's parse endpoint)
    """
    try:
        user_message = request.message.lower().strip()
        
        # Detect language and intent
        detected_language = detect_language(user_message)
        intent = detect_intent(user_message, detected_language)
        
        # Set confidence based on language detection
        confidence = 0.9 if detected_language != "en" else 0.8
        
        return {
            "text": request.message,
            "intent": {"name": intent, "confidence": confidence},
            "entities": [{"entity": "language", "value": detected_language, "confidence": 0.9}],
            "intent_ranking": [{"name": intent, "confidence": confidence}]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5005))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
