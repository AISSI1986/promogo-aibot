# ghananlp_actions.py - GhanaNLP + OpenAI Integration for Rasa

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, UserUtteranceReverted, FollowupAction, ActionExecuted, ActiveLoop
from rasa_sdk.types import DomainDict
import logging
import json
import random
import requests
import openai
import os

logger = logging.getLogger(__name__)

# Configuration
GHANA_NLP_SERVICE_URL = os.getenv("GHANA_NLP_SERVICE_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

class ActionGhanaNLPTranslate(Action):
    """Action to translate text using GhanaNLP service"""
    
    def name(self) -> Text:
        return "action_ghananlp_translate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get the text to translate from the latest message
            text_to_translate = tracker.latest_message.get('text', '')
            source_language = tracker.get_slot('source_language') or 'en'
            target_language = tracker.get_slot('target_language') or 'tw'
            
            # Call GhanaNLP translation service
            translation_response = self.translate_text(text_to_translate, source_language, target_language)
            
            if translation_response:
                translated_text = translation_response.get('translated_text', text_to_translate)
                confidence = translation_response.get('confidence', 0.9)
                
                # Send the translated response
                response_data = {
                    "intent": "translation",
                    "language": target_language,
                    "confidence": confidence,
                    "response": translated_text,
                    "context": "translation",
                    "original_text": text_to_translate,
                    "source_language": source_language,
                    "target_language": target_language
                }
                
                dispatcher.utter_message(json_message=response_data)
            else:
                # Fallback to original text
                dispatcher.utter_message(text=text_to_translate)
                
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            dispatcher.utter_message(text="Translation failed. Please try again.")
        
        return []

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Call GhanaNLP translation service"""
        try:
            payload = {
                "text": text,
                "source_language": source_lang,
                "target_language": target_lang
            }
            
            response = requests.post(
                f"{GHANA_NLP_SERVICE_URL}/translate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"GhanaNLP translation API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Translation service error: {str(e)}")
            return None

class ActionOpenAIResponse(Action):
    """Action to generate responses using OpenAI GPT"""
    
    def name(self) -> Text:
        return "action_openai_response"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get user message and detected language
            user_message = tracker.latest_message.get('text', '')
            detected_language = tracker.get_slot('language') or 'en'
            
            # Get conversation context
            conversation_context = self.get_conversation_context(tracker)
            
            # Generate response using OpenAI
            openai_response = self.generate_openai_response(user_message, detected_language, conversation_context)
            
            if openai_response:
                # Translate response to user's language if needed
                if detected_language != 'en':
                    translated_response = self.translate_response(openai_response, 'en', detected_language)
                    if translated_response:
                        openai_response = translated_response
                
                # Send the response
                response_data = {
                    "intent": "openai_response",
                    "language": detected_language,
                    "confidence": 0.9,
                    "response": openai_response,
                    "context": "ai_generated",
                    "source": "openai"
                }
                
                dispatcher.utter_message(json_message=response_data)
            else:
                # Fallback response
                fallback_responses = {
                    'en': "I'm sorry, I couldn't generate a response. Please try again.",
                    'ha': "Yi hakuri, ban iya samar da amsa ba. Don Allah sake gwada.",
                    'tw': "Mɛsɛɛ, mentumi nnyɛ amsa. Mesrɛ san sɛe bio.",
                    'ee': "Kafukafu, mateƒe kpe ɖe amsa. Taflatse, wòeɖe eŋu bio.",
                    'ga': "Kafukafu, mateƒe kpe ɖe amsa. Taflatse, wòeɖe eŋu bio.",
                    'dagbani': "Sɔŋsim, n ni tooi yɛli amsa. N ni tooi yɛli yɛli yi bio."
                }
                
                fallback_text = fallback_responses.get(detected_language, fallback_responses['en'])
                dispatcher.utter_message(text=fallback_text)
                
        except Exception as e:
            logger.error(f"OpenAI response error: {str(e)}")
            dispatcher.utter_message(text="I'm sorry, I encountered an error. Please try again.")
        
        return []

    def generate_openai_response(self, user_message: str, language: str, context: str) -> str:
        """Generate response using OpenAI GPT"""
        try:
            if not OPENAI_API_KEY:
                logger.warning("OpenAI API key not configured")
                return None
            
            # Create language-specific system prompt
            system_prompt = self.create_system_prompt(language, context)
            
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
            return None

    def create_system_prompt(self, language: str, context: str) -> str:
        """Create language-specific system prompt"""
        
        language_instructions = {
            "en": "You are a helpful customer service assistant for Promogo Ghana, an e-commerce platform in Accra, Ghana. Respond in English. Be friendly, helpful, and informative.",
            "ha": "Kai mai taimako ne na sabis na abokin ciniki na Promogo Ghana, dandalin kasuwanci na e-commerce a Accra, Ghana. Amsa cikin Hausa. Ka kasance mai sada zumunci, mai taimako, da kuma mai ba da labari.",
            "tw": "Woyɛ Promogo Ghana no adwumayɛfoɔ a ɔboa nkurɔfoɔ, e-commerce platform wɔ Accra, Ghana. Fa Twi mu bua. Yɛ adwene, boa, na fa nsɛm ma.",
            "ee": "Nànye Promogo Ghana ƒe kplɔ̃la siwo nàwòa nàwòa, e-commerce platform le Accra, Ghana. Bu be le Eʋegbe me. Nànye adzɔ, wòa, kple nàna nu.",
            "ga": "Nànye Promogo Ghana ƒe kplɔ̃la siwo nàwòa nàwòa, e-commerce platform le Accra, Ghana. Bu be le Ga me. Nànye adzɔ, wòa, kple nàna nu.",
            "dagbani": "N nyɛla Promogo Ghana sɔŋsim nira, e-commerce platform le Accra, Ghana. Bu be le Dagbani me. N nyɛla adzɔ, sɔŋsim, kple n-na nu."
        }
        
        base_instruction = language_instructions.get(language, language_instructions["en"])
        
        return f"""{base_instruction}

Context: {context}

Guidelines:
- Be helpful and informative about Promogo Ghana's services
- If asked about products, mention the marketplace features
- If asked about delivery, mention fast delivery across Ghana
- If asked about returns, mention the return policy
- Keep responses concise and friendly
- Always be professional and helpful"""

    def get_conversation_context(self, tracker: Tracker) -> str:
        """Get conversation context from tracker"""
        # Get recent conversation history
        events = tracker.events
        recent_messages = []
        
        for event in events[-10:]:  # Last 10 events
            if event.get("event") == "user":
                recent_messages.append(f"User: {event.get('text', '')}")
            elif event.get("event") == "bot":
                recent_messages.append(f"Bot: {event.get('text', '')}")
        
        return "\n".join(recent_messages[-6:])  # Last 6 messages

    def translate_response(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate response using GhanaNLP service"""
        try:
            payload = {
                "text": text,
                "source_language": source_lang,
                "target_language": target_lang
            }
            
            response = requests.post(
                f"{GHANA_NLP_SERVICE_URL}/translate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('translated_text', text)
            else:
                logger.error(f"Translation error: {response.status_code}")
                return text
                
        except Exception as e:
            logger.error(f"Translation service error: {str(e)}")
            return text

class ActionDetectLanguage(Action):
    """Enhanced language detection using GhanaNLP"""
    
    def name(self) -> Text:
        return "action_detect_language"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            user_message = tracker.latest_message.get('text', '')
            
            # Use enhanced language detection
            detected_language = self.detect_language_enhanced(user_message)
            
            # Set language slot
            return [SlotSet("language", detected_language)]
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return [SlotSet("language", "en")]  # Default to English

    def detect_language_enhanced(self, text: str) -> str:
        """Enhanced language detection with GhanaNLP support"""
        
        # Language-specific keywords
        language_keywords = {
            "ha": ["sannu", "na gode", "barka", "yaya", "ina", "wane", "me", "don", "za", "kana"],
            "tw": ["akwaaba", "medaase", "ɛte sɛn", "wo ho te sɛn", "ɛdeɛn", "wo", "me", "sɛ", "maakye", "maadwo"],
            "ee": ["woezɔ", "akpe", "aleke", "nànye", "nàwòa", "le", "nu", "siwo", "míeɖe", "taflatse"],
            "ga": ["akwaaba", "medaase", "aleke", "nànye", "nàwòa", "le", "nu", "siwo", "míeɖe", "taflatse"],
            "dagbani": ["dasiba", "antire", "naa", "bɔ", "n-niŋda", "a bora", "tipalana", "m'asante"]
        }
        
        text_lower = text.lower()
        
        # Count keyword matches for each language
        language_scores = {}
        for lang, keywords in language_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            language_scores[lang] = score
        
        # Return language with highest score, default to English if no matches
        if language_scores:
            best_language = max(language_scores, key=language_scores.get)
            if language_scores[best_language] > 0:
                return best_language
        
        return "en"  # Default to English

class ActionMultilingualResponse(Action):
    """Enhanced multilingual response with GhanaNLP and OpenAI integration"""
    
    def name(self) -> Text:
        return "action_multilingual_response"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            latest_message = tracker.latest_message
            intent = latest_message.get('intent', {}).get('name', '')
            confidence = latest_message.get('intent', {}).get('confidence', 0.0)
            
            # Get detected language
            language = tracker.get_slot('language') or 'en'
            
            # Handle different intents
            if intent in ["greet", "goodbye", "thank", "who_are_you"]:
                # Use predefined responses for common intents
                response = self.get_predefined_response(intent, language)
            else:
                # Use OpenAI for complex or unknown intents
                user_message = latest_message.get('text', '')
                response = self.generate_openai_response(user_message, language, {})
            
            # Send response
            response_data = {
                "intent": intent,
                "language": language,
                "confidence": confidence,
                "response": response,
                "context": "multilingual_response"
            }
            
            dispatcher.utter_message(json_message=response_data)
            
        except Exception as e:
            logger.error(f"Multilingual response error: {str(e)}")
            dispatcher.utter_message(text="I'm sorry, I encountered an error. Please try again.")
        
        return []

    def get_predefined_response(self, intent: str, language: str) -> str:
        """Get predefined responses for common intents"""
        
        responses = {
            'greet': {
                'en': "Hello! How can I help you today?",
                'ha': "Sannu! Yaya zan iya taimaka maka yau?",
                'tw': "Maakye! Dɛn na metumi ayɛ?",
                'ee': "Ŋdi na wo! Nukae mate ŋu awɔ?",
                'ga': "Ŋdi na wo! Nukae mate ŋu awɔ?",
                'dagbani': "Dasiba! Bɔ n-niŋda a bora?"
            },
            'goodbye': {
                'en': "Goodbye! Have a great day!",
                'ha': "Sai anjima! Allah ya ba da sa'a!",
                'tw': "Yɛbɛhyia bio! Nante yie!",
                'ee': "Heɖee! Wòeƒo nyuie!",
                'ga': "Heɖee! Wòeƒo nyuie!",
                'dagbani': "Nasaara! Nya da pa!"
            },
            'thank': {
                'en': "You're welcome! Is there anything else I can help you with?",
                'ha': "Ba komai! Akwai wani abu da zan iya taimaka maka?",
                'tw': "Meda wo ase! Ɛdeɛn nso na ɛpɛ sɛ me tɔn?",
                'ee': "Akpe! Nukae nè wòle be míawò?",
                'ga': "Akpe! Nukae nè wòle be míawò?",
                'dagbani': "M'asante! Bɔ n-niŋda a bora?"
            },
            'who_are_you': {
                'en': "I am a shopping assistant bot for Promogo Ghana. I can help you buy and sell products.",
                'ha': "Ni bot ne mai taimaka wajen saye da sayarwa na Promogo Ghana.",
                'tw': "Mɛyɛ bot a ɛboa nneɛma tɔn na Promogo Ghana.",
                'ee': "Nye bot si le kpe ɖe ŋunye be míawò alo míadzra nu na Promogo Ghana.",
                'ga': "Nye bot si le kpe ɖe ŋunye be míawò alo míadzra nu na Promogo Ghana.",
                'dagbani': "N nyɛla bot n-niŋdi sɔŋsim ka a da bini bee ka a kɔhi bini na Promogo Ghana."
            }
        }
        
        intent_responses = responses.get(intent, {})
        return intent_responses.get(language, intent_responses.get('en', "I'm here to help!"))

    def generate_openai_response(self, user_message: str, language: str, context: Dict[str, Any]) -> str:
        """Generate response using OpenAI (fallback method)"""
        try:
            if not OPENAI_API_KEY:
                return "I'm here to help! Please let me know what you need."
            
            # Create system prompt
            system_prompt = self.create_system_prompt(language, context)
            
            # Make request to OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI response generation error: {str(e)}")
            return "I'm here to help! Please let me know what you need."

    def create_system_prompt(self, language: str, context: Dict[str, Any]) -> str:
        """Create system prompt for OpenAI"""
        
        language_instructions = {
            "en": "You are a helpful customer service assistant for Promogo Ghana. Respond in English.",
            "ha": "Kai mai taimako ne na Promogo Ghana. Amsa cikin Hausa.",
            "tw": "Woyɛ Promogo Ghana no adwumayɛfoɔ a ɔboa nkurɔfoɔ. Fa Twi mu bua.",
            "ee": "Nànye Promogo Ghana ƒe kplɔ̃la. Bu be le Eʋegbe me.",
            "ga": "Nànye Promogo Ghana ƒe kplɔ̃la. Bu be le Ga me.",
            "dagbani": "N nyɛla Promogo Ghana sɔŋsim nira. Bu be le Dagbani me."
        }
        
        base_instruction = language_instructions.get(language, language_instructions["en"])
        
        return f"""{base_instruction}

Be helpful, friendly, and informative about Promogo Ghana's e-commerce services.
Keep responses concise and relevant to the user's needs."""
