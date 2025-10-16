from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import openai
import json
import os
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Promogo Chatbot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Promogo knowledge base
def load_knowledge_base():
    """Load the Promogo knowledge base from JSON file"""
    try:
        with open('promogo_knowledge_base.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Knowledge base file not found, using empty knowledge base")
        return {}
    except Exception as e:
        logger.error(f"Error loading knowledge base: {str(e)}")
        return {}

# Load knowledge base
KNOWLEDGE_BASE = load_knowledge_base()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    Smart multilingual chatbot webhook with OpenAI integration
    """
    try:
        user_message = request.message.strip()
        user_message_lower = user_message.lower()
        
        # Detect language based on content
        detected_language = detect_language(user_message_lower)
        
        # Detect intent
        intent = detect_intent(user_message_lower, detected_language)
        
        # Get appropriate response
        if intent == "default":
            # Use OpenAI for unrecognized intents
            logger.info(f"Using OpenAI for unrecognized intent. Language: {detected_language}")
            response_text = get_openai_response(user_message, detected_language, intent)
        else:
            # Use predefined responses for recognized intents
            response_text = get_response(intent, detected_language)
        
        # Return in Rasa's expected format
        return [{"text": response_text, "recipient_id": request.sender}]
        
    except Exception as e:
        logger.error(f"Error in chat webhook: {str(e)}")
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

def get_openai_response(user_message, detected_language, intent):
    """
    Get smart response from OpenAI GPT-3.5-turbo for unrecognized intents
    """
    try:
        # Create context from knowledge base
        context = create_context_from_knowledge_base()
        
        # Create language-specific system prompt
        system_prompt = create_system_prompt(detected_language, context)
        
        # Make request to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        # Fallback to default response
        language_responses = CHATBOT_RESPONSES.get(detected_language, CHATBOT_RESPONSES["en"])
        return language_responses["default"]

def create_context_from_knowledge_base():
    """Create context string from the knowledge base"""
    if not KNOWLEDGE_BASE:
        return "Promogo Ghana is an e-commerce platform in Accra, Ghana."
    
    context_parts = []
    
    # Company overview
    if 'company_overview' in KNOWLEDGE_BASE:
        co = KNOWLEDGE_BASE['company_overview']
        context_parts.append(f"Company: {co.get('name', 'Promogo Ghana')}")
        context_parts.append(f"Description: {co.get('description', 'E-commerce platform')}")
        context_parts.append(f"Location: {co.get('location', 'Accra, Ghana')}")
        
        if 'contact' in co:
            contact = co['contact']
            context_parts.append(f"Phone: {contact.get('phone', '')}")
            context_parts.append(f"Email: {contact.get('email', '')}")
    
    # Products
    if 'products' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['products']:
        products = KNOWLEDGE_BASE['products'][:5]  # Limit to first 5 products
        product_list = []
        for product in products:
            product_list.append(f"- {product.get('name', '')} ({product.get('price', '')})")
        context_parts.append(f"Featured Products:\n" + "\n".join(product_list))
    
    # Categories
    if 'categories' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['categories']:
        categories = [cat.get('name', '') for cat in KNOWLEDGE_BASE['categories'][:8]]
        context_parts.append(f"Product Categories: {', '.join(categories)}")
    
    # Services
    if 'services' in KNOWLEDGE_BASE and KNOWLEDGE_BASE['services']:
        services = KNOWLEDGE_BASE['services']
        context_parts.append(f"Services: {', '.join(services)}")
    
    # Policies
    if 'policies' in KNOWLEDGE_BASE:
        policies = KNOWLEDGE_BASE['policies']
        policy_info = []
        if 'return_policy' in policies:
            policy_info.append(f"Return Policy: {policies['return_policy']}")
        if 'delivery' in policies:
            policy_info.append(f"Delivery: {policies['delivery']}")
        if 'payment' in policies:
            policy_info.append(f"Payment: {policies['payment']}")
        context_parts.append("Policies: " + "; ".join(policy_info))
    
    return "\n".join(context_parts)

def create_system_prompt(language, context):
    """Create language-specific system prompt for OpenAI"""
    
    language_instructions = {
        "en": "You are a helpful customer service assistant for Promogo Ghana, an e-commerce platform in Accra, Ghana. Respond in English. Be friendly, helpful, and informative. Use the provided context to answer questions about products, services, policies, and company information.",
        "ha": "Kai mai taimako ne na sabis na abokin ciniki na Promogo Ghana, dandalin kasuwanci na e-commerce a Accra, Ghana. Amsa cikin Hausa. Ka kasance mai sada zumunci, mai taimako, da kuma mai ba da labari. Ka yi amfani da bayanan da aka bayar don amsa tambayoyi game da kayayyaki, ayyuka, manufofi, da bayanan kamfani.",
        "tw": "Woyɛ Promogo Ghana no adwumayɛfoɔ a ɔboa nkurɔfoɔ, e-commerce platform wɔ Accra, Ghana. Fa Twi mu bua. Yɛ adwene, boa, na fa nsɛm ma. Fa nsɛm a wɔde ama wo no di dwuma sɛ wubua nsɛm fa nnuane, adwuma, nkɔsoɔ, ne kɔmpɔni nsɛm ho.",
        "ee": "Nànye Promogo Ghana ƒe kplɔ̃la siwo nàwòa nàwòa, e-commerce platform le Accra, Ghana. Bu be le Eʋegbe me. Nànye adzɔ, wòa, kple nàna nu. Na nu siwo wòna be le nu siwo wòna be la ŋuti be nàwòa nu fa nàwòa, nu siwo nàwòa, nu siwo nàwòa, kple kɔmpɔni nu siwo nàwòa."
    }
    
    base_instruction = language_instructions.get(language, language_instructions["en"])
    
    return f"""{base_instruction}

Context about Promogo Ghana:
{context}

Guidelines:
- If asked about specific products, provide details from the context
- If asked about delivery, mention fast delivery across Ghana
- If asked about returns, mention the 7-day return policy
- If asked about contact, provide phone and email information
- If you don't know something specific, say so politely and offer to help with what you do know
- Keep responses concise and helpful
- Always be professional and friendly"""

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
