# actions.py - GhanaNLP + OpenAI Integration for Promogo

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

# Import GhanaNLP actions
from .ghananlp_actions import (
    ActionGhanaNLPTranslate,
    ActionOpenAIResponse,
    ActionDetectLanguage,
    ActionMultilingualResponse
)

logger = logging.getLogger(__name__)

class ActionMultilingualResponse(Action):
    def name(self) -> Text:
        return "action_multilingual_response"

    def get_conversation_context(self, tracker: Tracker) -> Dict[str, Any]:
        """
        Détermine le contexte de la conversation basé sur l'historique
        """
        # Récupérer la dernière intention pour comprendre le contexte
        events = tracker.events
        latest_intent = None
        
        for event in reversed(events):
            if event.get("event") == "user":
                latest_intent = event.get("parse_data", {}).get("intent", {}).get("name")
                if latest_intent:
                    break
        
        # Log pour déboguer
        logger.info(f"Latest intent: {latest_intent}")
        
        # Déterminer le contexte basé sur l'intention
        if latest_intent in ["login", "signup"]:
            return "authentication"
        elif latest_intent in ["contact_support", "complaint"]:
            return "support"
        elif latest_intent in ["product_search", "price_inquiry"]:
            return "shopping"
        elif latest_intent in ["open_seller_app", "open_buyer_app", "open_delivery_app"]:
            return "app_navigation"
        
        # Contexte par défaut
        return "general"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        latest_message = tracker.latest_message
        intent = latest_message.get('intent', {}).get('name', '')
        confidence = latest_message.get('intent', {}).get('confidence', 0.0)
        
        logger.info(f"ActionMultilingualResponse - Intent détecté: {intent}")
        logger.info(f"ActionMultilingualResponse - Confidence: {confidence}")
        
        # Vérifier si un formulaire est actif
        active_form = tracker.active_loop.get('name') if tracker.active_loop else None
        logger.info(f"ActionMultilingualResponse - Formulaire actif: {active_form}")

        # Liste des intents prioritaires qui nécessitent une redirection immédiate
        priority_intents = {
            "login": "action_redirect_login",
            "signup": "action_redirect_signup",
            "contact_support": "action_contact_support",
            "complaint": "action_multilingual_response",
            "open_seller_app": "action_open_seller_app",
            "open_buyer_app": "action_open_buyer_app",
            "open_delivery_app": "action_open_delivery_app"
        }

        # Si l'intent est prioritaire, gérer en conséquence
        if intent in priority_intents:
            logger.info(f"ActionMultilingualResponse - Intent prioritaire détecté: {intent}")
            
            # Si un formulaire est actif, l'interrompre
            if active_form:
                logger.info(f"ActionMultilingualResponse - Interruption du formulaire {active_form}")
                events = [
                    ActionExecuted("action_reset_slots"),
                    ActiveLoop(None),
                    SlotSet("requested_slot", None)
                ]
            else:
                events = []

            # Ajouter l'action de redirection appropriée
            events.append(FollowupAction(priority_intents[intent]))
            return events
        
        # Pour les intents buy et sell, laisser les formulaires les gérer
        if intent in ["buy", "sell"]:
            logger.info(f"ActionMultilingualResponse - Intent {intent} ignoré pour laisser le formulaire le gérer")
            return []
        
        language = latest_message.get('metadata', {}).get('language', 'en')
        logger.info(f"ActionMultilingualResponse - Langue détectée: {language}")
        
        context = self.get_conversation_context(tracker)
        logger.info(f"ActionMultilingualResponse - Contexte de conversation: {context}")
        
        # Définir les réponses multilingues
        responses = {
            'greet': {
                'en': [
                    "Hello! How can I help you today?",
                    "Hi there! What can I do for you?",
                    "Greetings! How may I assist you?"
                ],
                'ha': [
                    "Sannu! Yaya zan iya taimaka maka yau?",
                    "Sannu da zuwa! Me zan iya yi maka?",
                    "Barka da zuwa! Yaya zan iya taimaka maka?"
                ],
                'ee': [
                    "Ŋdi na wo! Nukae mate ŋu awɔ?",
                    "Woezɔ! Nukae mate ŋu awɔ?",
                    "Ŋdi na wo! Nukae mate ŋu awɔ?"
                ],
                'tw': [
                    "Maakye! Dɛn na metumi ayɛ?",
                    "Maaha! Dɛn na metumi ayɛ?",
                    "Maadwo! Dɛn na metumi ayɛ?"
                ],
                'dagbani': [
                    "Dasiba! Bɔ n-niŋda a bora?",
                    "Antire! Bɔ n-niŋda a bora?",
                    "Naa! Bɔ n-niŋda a bora?"
                ]
            },
            'goodbye': {
                'en': [
                    "Goodbye! Have a great day!",
                    "See you later! Take care!",
                    "Farewell! Come back soon!"
                ],
                'ha': [
                    "Sai anjima! Allah ya ba da sa'a!",
                    "Sai wata rana! Allah ya kiyaye hanya!",
                    "Sai gobe! Allah ya ba da sa'a!"
                ],
                'ee': [
                    "Heɖee! Wòeƒo nyuie!",
                    "Gbugbɔ dze egɔme! Wòeƒo nyuie!",
                    "Miadogo! Wòeƒo nyuie!"
                ],
                'tw': [
                    "Yɛbɛhyia bio! Nante yie!",
                    "Da yie! Yɛbɛhyia bio!",
                    "Daakye! Nante yie!"
                ],
                'dagbani': [
                    "Nasaara! Nya da pa!",
                    "Nya da pa! Ti ni lahi nya taba!",
                    "Naa niŋ pa! Nya da pa!"
                ]
            },
            'thank': {
                'en': [
                    "You're welcome! Is there anything else I can help you with?",
                    "My pleasure! What else can I do for you?",
                    "Happy to help! Do you need anything else?"
                ],
                'ha': [
                    "Ba komai! Akwai wani abu da zan iya taimaka maka?",
                    "Ba komai! Wani abu kuma?",
                    "Ba komai! Ina bukatar taimako?"
                ],
                'ee': [
                    "Akpe! Nukae nè wòle be míawò?",
                    "Akpe kaka! Nukae nè wòle be míawò?",
                    "Akpe na mi! Nukae nè wòle be míawò?"
                ],
                'tw': [
                    "Meda wo ase! Ɛdeɛn nso na ɛpɛ sɛ me tɔn?",
                    "Meda wo ase paa! Ɛdeɛn nso na ɛpɛ sɛ me tɔn?",
                    "Meda wo ase kɛse! Ɛdeɛn nso na ɛpɛ sɛ me tɔn?"
                ],
                'dagbani': [
                    "M'asante! Bɔ n-niŋda a bora?",
                    "Tipalana! Bɔ n-niŋda a bora?",
                    "Tipalana pam! Bɔ n-niŋda a bora?"
                ]
            },
            'who_are_you': {
                'en': [
                    "I am a shopping assistant bot. I can help you buy and sell products.",
                    "I'm your friendly shopping bot! I can help with buying and selling.",
                    "Hello! I'm a shopping assistant that can help you with purchases and sales."
                ],
                'ha': [
                    "Ni bot ne mai taimaka wajen saye da sayarwa.",
                    "Ni abokin cinikin ku ne. Zan iya taimaka maka don sayen ko sayar da kaya.",
                    "Sannu! Ni bot ne mai taimaka wajen saye da sayarwa."
                ],
                'ee': [
                    "Nye bot si le kpe ɖe ŋunye be míawò alo míadzra nu.",
                    "Nye bot si le kpe ɖe ŋunye be míawò.",
                    "Ŋdi na wo! Nye bot si le kpe ɖe ŋunye."
                ],
                'tw': [
                    "Mɛyɛ bot a ɛboa nneɛma tɔn. Mɛtumi aboa wo sɛ wobɛtɔn anaa wobɛtɔn biribi.",
                    "Mɛyɛ bot a ɛboa wo sɛ wobɛtɔn biribi.",
                    "Maakye! Mɛyɛ bot a ɛboa wo."
                ],
                'dagbani': [
                    "N nyɛla bot n-niŋdi sɔŋsim ka a da bini bee ka a kɔhi bini.",
                    "N nyɛla bot n-niŋdi sɔŋsim.",
                    "Dasiba! N nyɛla bot n-niŋdi sɔŋsim."
                ]
            },
            'out_of_scope': {
                'en': [
                    "I'm sorry, I can't help with that. I can only assist with buying and selling products.",
                    "I apologize, but that's outside my capabilities. I can help you with shopping-related tasks.",
                    "I'm afraid I can't help with that. I'm designed to assist with purchases and sales."
                ],
                'ha': [
                    "Yi hakuri, ban iya taimaka maka ba game da wannan. Zan iya taimaka kawai game da saye da sayarwa.",
                    "Yi hakuri, amma wannan ba cikin iyawata ba ne. Zan iya taimaka kawai game da saye da sayarwa.",
                    "Yi hakuri, ban iya taimaka maka ba. An kera ni don taimaka game da saye da sayarwa."
                ],
                'ee': [
                    "Míeɖe kuku, mateƒe kpe ɖe ŋunye. Mateƒe kpe ɖe ŋunye be míawò alo míadzra nu.",
                    "Míeɖe kuku, amma eyae menye o. Mateƒe kpe ɖe ŋunye be míawò alo míadzra nu.",
                    "Míeɖe kuku, mateƒe kpe ɖe ŋunye. Wòle be míawò alo míadzra nu."
                ],
                'tw': [
                    "Mɛsɛɛ, mentumi nnyɛ saa. Mɛtumi aboa wo sɛ wobɛtɔn anaa wobɛtɔn biribi.",
                    "Mɛsɛɛ, nanso ɛnyɛ saa. Mɛtumi aboa wo sɛ wobɛtɔn anaa wobɛtɔn biribi.",
                    "Mɛsɛɛ, mentumi nnyɛ saa. Mɛyɛ bot a ɛboa wo sɛ wobɛtɔn anaa wobɛtɔn biribi."
                ],
                'dagbani': [
                    "N niŋdi yɛlimaŋli, n ni tooi sɔŋ a ka a yɛli. N ni tooi sɔŋ a ka a da bini bee ka a kɔhi bini.",
                    "N niŋdi yɛlimaŋli, amma ɛnyɛ saa. N ni tooi sɔŋ a ka a da bini bee ka a kɔhi bini.",
                    "N niŋdi yɛlimaŋli, n ni tooi sɔŋ a ka a yɛli. N nyɛla bot n-niŋdi sɔŋsim ka a da bini bee ka a kɔhi bini."
                ]
            },
            'contact_support': {
                'en': [
                    "I'll help you get in touch with our support team. How would you like to contact them?",
                    "Let me connect you with our customer support. They can assist you with your specific needs.",
                    "I can help you reach our support team. They're available to address your concerns."
                ],
                'ha': [
                    "Zan taimaka maka tuntuɓar ƙungiyar tallafin mu. Ta yaya kake son tuntuɓar su?",
                    "Bari in haɗa ka da tallafin abokin cinikinmu. Za su iya taimaka maka da bukatun ka na musamman.",
                    "Zan iya taimaka maka isa ƙungiyar tallafin mu. Suna nan don magance damuwarku."
                ],
                'ee': [
                    "Makpe ɖe ŋuwò nàde míaƒe kpekpeɖeŋu hatso ŋu. Aleke nèdi be yeade wo ŋu?",
                    "Na matsɔ wò ade míaƒe asixɔlawo ƒe kpekpeɖeŋu ŋu. Woate ŋu akpe ɖe ŋuwò le wò nuhiahiã tɔxɛwo ŋu.",
                    "Mate ŋu akpe ɖe ŋuwò nàɖo míaƒe kpekpeɖeŋu hatso ŋu. Woli be woaɖo wò nyawo ŋu."
                ],
                'tw': [
                    "Mɛboa wo ma wo ne yɛn support team nkasa. Ɔkwan bɛn so na wopɛ sɛ wode wɔn nkasa?",
                    "Ma mede wo abɔ yɛn customer support. Wɔbɛtumi aboa wo wɔ wo ahiade pɔtee ho.",
                    "Mɛtumi aboa wo ma wo nnya yɛn support team. Wɔwɔ hɔ a wɔbɛtumi atie wo nsɛm."
                ],
                'dagbani': [
                    "N ni sɔŋ a ka a paai ti sɔŋsim team. Wula ka a bɔra ni a paai ba?",
                    "N ni paai a ni ti customer support. Ba ni tooi sɔŋ a a bɔhibu shɛli.",
                    "N ni tooi sɔŋ a ka a nya ti sɔŋsim team. Ba be ka ba mali a taɣibu maa."
                ]
            }
        }
        
        # Get response based on intent and language
        if intent in responses and language in responses[intent]:
            response = random.choice(responses[intent][language])
        else:
            # Define language-specific fallback responses (multiple variations per language)
            fallback_responses = {
                "en": [
                    "I'm sorry, I didn't understand that.",
                    "I didn't quite get that. Could you rephrase?",
                    "Sorry, I didn't follow you. Could you say that differently?"
                ],
                "ha": [
                    "Yi hakuri, ban fahimta ba.",
                    "Yi hakuri, ban gane abin da kace ba. Za ka iya maimaita?",
                    "Na kasa fahimta. Don Allah ka sake fada."
                ],
                "ee": [
                    "Kafukafu, menye o, medze o.",
                    "Mete o ta, taflatse, eɖe eŋu bio?",
                    "Menye be metee nu sia. Taflatse, katae ɖo o."
                ],
                "tw": [
                    "Kafra, mente aseɛ.",
                    "Mesrɛ, menteɛ mu yiye. Wobɛtumi asan akyerɛ me?",
                    "Medɔ wo kyɛ, ɛdɛn na wokae? Mesrɛ san ka bio."
                ],
                "dagbani": [
                    "Saa nyɛ, o ba laal maa.",
                    "N ni tooi yɛli. Ka yɛli bio?",
                    "N ba lafa yɛli ni a yɛlimaŋli. A yɛli bio."
                ]
            }

            # Pick a random fallback based on detected language, defaulting to English
            response = random.choice(fallback_responses.get(language, fallback_responses["en"]))
        
        # Create custom response
        custom_response = {
            "intent": intent,
            "language": language,
            "confidence": confidence,
            "response": response,
            "context": context
        }
        
        # Send response
        dispatcher.utter_message(json_message=custom_response)
        
        return []

class ActionFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Define responses for each language
        responses = {
            'en': [
                "I'm sorry, I didn't understand that. Please try again.",
                "I'm not sure I follow. Could you rephrase that?",
                "I didn't quite catch that. Can you say it differently?"
            ],
            'ha': [
                "Yi hakuri, ban fahimci abin da kuka ce ba. Don Allah sake gwada.",
                "Ban fahimci abin da kuka ce ba. Don Allah sake fadada.",
                "Ban fahimci abin da kuka ce ba. Don Allah sake ce."
            ],
            'ee': [
                "Kafukafu, menye o, medze o. Taflatse, wòeɖe eŋu bio.",
                "Menye o, medze o. Taflatse, wòeɖe eŋu bio.",
                "Menye o, medze o. Taflatse, wòeɖe eŋu bio."
            ],
            'tw': [
                "Kafra, minnyɛ asɛm yi akyerɛ me no. Mesrɛ sɛ wobɛsan akyerɛ me bio.",
                "Minnyɛ asɛm yi akyerɛ me no. Mesrɛ sɛ wobɛsan akyerɛ me bio.",
                "Minnyɛ asɛm yi akyerɛ me no. Mesrɛ sɛ wobɛsan akyerɛ me bio."
            ],
            'dagbani': [
                "Sɔŋsim, n ni tooi yɛli ni n yɛli yɛli yi. N ni tooi yɛli ni n yɛli yɛli yi bio.",
                "N ni tooi yɛli ni n yɛli yɛli yi. N ni tooi yɛli ni n yɛli yɛli yi bio.",
                "N ni tooi yɛli ni n yɛli yɛli yi. N ni tooi yɛli ni n yɛli yɛli yi bio."
            ]
        }
        
        # Get response list for the detected language or default to English
        response_list = responses.get(language, responses['en'])
        
        # Select a random response from the list
        response = random.choice(response_list)
        
        # Structure the response for API consumption
        response_data = {
            "intent": "fallback",
            "language": language,
            "confidence": 0.0,
            "response": response
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return [UserUtteranceReverted()]

class ActionProcessPurchase(Action):
    """
    Action to process a purchase after collecting product and quantity information.
    This action is triggered after the product_form is completed.
    """
    def name(self) -> Text:
        return "action_process_purchase"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Get slots with validation
        product = tracker.get_slot("product")
        quantity = tracker.get_slot("quantity")
        
        # Log the slots for debugging
        logger.info(f"Processing purchase with product={product}, quantity={quantity}")
        
        # Validate required slots
        if not product:
            logger.warning("Product slot is missing, requesting product information")
            return [FollowupAction("purchase_form")]
        
        if not quantity:
            # Default to 1 if quantity is not specified
            quantity = 1
            logger.info(f"Quantity not specified, defaulting to {quantity}")
        
        # Generate checkout URL with proper URL encoding
        import urllib.parse
        encoded_product = urllib.parse.quote(product)
        checkout_url = f"https://promoghana.com/products?name={encoded_product}&product_name={encoded_product}&quantity={quantity}&data_from=search"
        
        # Multilingual responses with proper formatting
        responses = {
            'en': f"Great! You're purchasing {quantity} {product}. Here's your checkout link.",
            'ha': f"Da kyau! Kana sayen {quantity} {product}. Ga hanyar biyan kuɗi.",
            'ee': f"Enyo! Èle {quantity} {product} ƒlem. Esia nye wò checkout link.",
            'tw': f"Ɛyɛ papa! Woretɔ {quantity} {product}. Wei ne wo checkout link.",
            'dagbani': f"Ka viɛnyɛla! A dara {quantity} {product}. Ŋuna nyɛla a checkout link."
        }
        
        # Get response in appropriate language with fallback to English
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption with comprehensive metadata
        response_data = {
            "intent": "purchase_confirmation",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "purchase_confirmation",
            "redirect_url": checkout_url,
            "product_details": {
                "product": product,
                "quantity": quantity
            },
            "buttons": [
                {
                    "title": "Proceed to Checkout",
                    "payload": checkout_url,
                    "type": "url"
                }
            ]
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        # Reset slots after the confirmation for a clean state
        return [
            SlotSet("product", None),
            SlotSet("quantity", None),
            SlotSet("conversation_state", "greeting")
        ]

class ActionResetSlots(Action):
    def name(self) -> Text:
        return "action_reset_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Conserver la langue
        language = tracker.get_slot("language")
        
        return [
            SlotSet("product", None),
            SlotSet("conversation_state", "greeting"),
            SlotSet("language", language)
        ]

class ActionDetectLanguage(Action):
    def name(self) -> Text:
        return "action_detect_language"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Récupérer la langue depuis les métadonnées du message
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Vérifier si la langue est supportée, sinon utiliser l'anglais
        supported_languages = ['en', 'ha', 'ee', 'tw', 'dagbani']
        if language not in supported_languages:
            language = 'en'
        
        # Log pour déboguer
        logger.info(f"Detected language: {language}")
        
        # Définir le slot de langue
        return [SlotSet("language", language)]
    

class ActionProcessSale(Action):
    """
    Action to process a sale after collecting product, price, condition, and location information.
    This action is triggered after the sales_form is completed.
    """
    def name(self) -> Text:
        return "action_process_sale"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Get slots with validation
        product = tracker.get_slot("product")
        price = tracker.get_slot("price")
        condition = tracker.get_slot("condition")
        location = tracker.get_slot("location")
        
        # Log the slots for debugging
        logger.info(f"Processing sale with product={product}, price={price}, condition={condition}, location={location}")
        
        # Validate required slots
        if not product:
            logger.warning("Product slot is missing, requesting product information")
            return [FollowupAction("sales_form")]
        
        if not price:
            logger.warning("Price slot is missing, requesting price information")
            return [FollowupAction("sales_form")]
            
        if not condition:
            logger.warning("Condition slot is missing, requesting condition information")
            return [FollowupAction("sales_form")]
            
        if not location:
            logger.warning("Location slot is missing, requesting location information")
            return [FollowupAction("sales_form")]
        
        # Generate listing URL with proper URL encoding
        import urllib.parse
        encoded_product = urllib.parse.quote(product)
        encoded_condition = urllib.parse.quote(condition)
        encoded_location = urllib.parse.quote(location)
        listing_url = f"https://promoghana.com/sell?product={encoded_product}&price={price}&condition={encoded_condition}&location={encoded_location}"
        
        # Multilingual responses with proper formatting
        responses = {
            'en': f"Great! Your {product} is now listed for sale at {price} in {condition} condition from {location}. Here's your listing link.",
            'ha': f"Da kyau! An sanya {product} naka don sayarwa a {price} cikin yanayin {condition} daga {location}. Ga hanyar sayarwa.",
            'ee': f"Enyo! Wò {product} le dzadzra ɖo na na {price} le {condition} ƒe nɔnɔme me tso {location}. Esia nye wò listing link.",
            'tw': f"Ɛyɛ papa! Wo {product} no ɛwɔ hɔ sɛ wɔbɛtɔn wɔ {price} a ɛwɔ {condition} tebea mu wɔ {location}. Wei ne wo listing link.",
            'dagbani': f"Ka viɛnyɛla! A {product} kpahiri ni n-nyɛ daara {price} ni {condition} noli ni {location}. Ŋuna nyɛla a listing link."
        }
        
        # Get response in appropriate language with fallback to English
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption with comprehensive metadata
        response_data = {
            "intent": "sale_confirmation",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "sale_confirmation",
            "redirect_url": listing_url,
            "product_details": {
                "product": product,
                "price": price,
                "condition": condition,
                "location": location
            },
            "buttons": [
                {
                    "title": "View Your Listing",
                    "payload": listing_url,
                    "type": "url"
                }
            ]
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        # Reset slots after the confirmation for a clean state
        return [
            SlotSet("product", None),
            SlotSet("price", None),
            SlotSet("condition", None),
            SlotSet("location", None),
            SlotSet("conversation_state", "greeting")
        ]

class ActionAskProductSales(Action):
    """
    Custom action to ask for product in sales form with JSON format.
    """
    def name(self) -> Text:
        # Conforme au schéma Rasa : action_ask_<form_name>_<slot>
        return "action_ask_sales_form_product"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Multilingual prompts
        prompts = {
            'en': "What product would you like to sell?",
            'ha': "Wane kaya kake son sayarwa?",
            'ee': "Nu ka nèdi be yeadzra?",
            'tw': "Ɛdeɛn nneɛma na wopɛ sɛ wotɔn?",
            'dagbani': "Bɔ bini n-niŋda a bora ni a kɔhi?"
        }
        
        # Get prompt in appropriate language
        prompt = prompts.get(language, prompts['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "product_inquiry_sales",
            "language": language,
            "confidence": 1.0,
            "response": prompt,
            "context": "product_selection_sales",
            "expected_entity": "product"
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []

class ActionAskProduct(Action):
    """
    Custom action to ask for product in purchase flow with JSON format.
    """
    def name(self) -> Text:
        # Conforme au schéma Rasa : action_ask_<form_name>_<slot>
        return "action_ask_purchase_form_product"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Multilingual prompts
        prompts = {
            'en': "What product are you looking to buy?",
            'ha': "Wane kaya kake son saya?",
            'ee': "Nu ka nèle dii be yeaƒle?",
            'tw': "Ɛdeɛn nneɛma na wopɛ sɛ wotɔ?",
            'dagbani': "Bɔ bini n-niŋda a bora ni a da?"
        }
        
        # Get prompt in appropriate language
        prompt = prompts.get(language, prompts['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "product_inquiry_purchase",
            "language": language,
            "confidence": 1.0,
            "response": prompt,
            "context": "product_selection_purchase",
            "expected_entity": "product"
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        # Set conversation state to product_selection
        return [SlotSet("conversation_state", "product_selection")]

class ActionAskPrice(Action):
    """
    Custom action to ask for price in sales form with JSON format.
    """
    def name(self) -> Text:
        return "action_ask_sales_form_price"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Get product name for context
        product = tracker.get_slot("product") or "product"
        
        # Multilingual prompts
        prompts = {
            'en': f"What price are you selling your {product} for?",
            'ha': f"Wane farashi kake sayar da {product} naka?",
            'ee': f"Ga home nèle wò {product} dzadzra ɖo?",
            'tw': f"Sika ahe na wopɛ sɛ wotɔn wo {product} no?",
            'dagbani': f"Ligri shɛli ka a ni kɔhi a {product} maa?"
        }
        
        # Get prompt in appropriate language
        prompt = prompts.get(language, prompts['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "price_inquiry",
            "language": language,
            "confidence": 1.0,
            "response": prompt,
            "context": "price_selection",
            "expected_entity": "price",
            "product_context": product
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []

class ActionAskCondition(Action):
    """
    Custom action to ask for condition in sales form with JSON format.
    """
    def name(self) -> Text:
        return "action_ask_sales_form_condition"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Get product name for context
        product = tracker.get_slot("product") or "product"
        
        # Multilingual prompts
        prompts = {
            'en': f"What is the condition of your {product}? (new, used, etc.)",
            'ha': f"Yaya yanayin {product} naka yake? (sabon, an yi amfani da shi, etc.)",
            'ee': f"Aleke wò {product} le? (yeye, wozãe xoxo, etc.)",
            'tw': f"Sɛn na wo {product} no tebea te? (foforɔ, wɔde adi dwuma, etc.)",
            'dagbani': f"Wula ka a {product} maa be? (paalli, kpahirili, etc.)"
        }
        
        # Get prompt in appropriate language
        prompt = prompts.get(language, prompts['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "condition_inquiry",
            "language": language,
            "confidence": 1.0,
            "response": prompt,
            "context": "condition_selection",
            "expected_entity": "condition",
            "product_context": product,
            "suggested_values": ["new", "used", "like new", "refurbished"]
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []

class ActionAskLocation(Action):
    """
    Custom action to ask for location in sales form with JSON format.
    """
    def name(self) -> Text:
        return "action_ask_sales_form_location"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Get product name for context
        product = tracker.get_slot("product") or "product"
        
        # Multilingual prompts
        prompts = {
            'en': f"Where are you located for the sale of your {product}?",
            'ha': f"Ina kake don sayar da {product} naka?",
            'ee': f"Afika nèle hena {product} dzadzra?",
            'tw': f"Ɛhe na wowɔ a wopɛ sɛ wotɔn wo {product} no?",
            'dagbani': f"Yin ka a be ni a ni kɔhi a {product} maa?"
        }
        
        # Get prompt in appropriate language
        prompt = prompts.get(language, prompts['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "location_inquiry",
            "language": language,
            "confidence": 1.0,
            "response": prompt,
            "context": "location_selection",
            "expected_entity": "location",
            "product_context": product
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []
    

class ActionRedirectSignup(Action):
    def name(self) -> Text:
        return "action_redirect_signup"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Generate signup URL
        signup_url = "https://promoghana.com/customer/auth/sign-up"
        
        # Multilingual responses
        responses = {
            'en': "I'll redirect you to our signup page where you can create your account.",
            'ha': "Zan mai da kai zuwa shafin rajista inda za ka iya ƙirƙiran account ɗinka.",
            'ee': "Matrɔ wò ayi míaƒe ŋkɔŋɔŋlɔ axa la dzi afisi nàte ŋu awɔ wò akɔnt le.",
            'tw': "Mɛma wo akɔ yɛn signup page a wobɛtumi ayɛ wo account wɔ hɔ.",
            'dagbani': "N ni zaŋ a ti ti signup page din ni a ni tooi sabili a account maa."
        }
        
        # Get response in appropriate language
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "signup_redirect",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "signup_redirect",
            "redirect_url": signup_url,
            "buttons": [
                {
                    "title": "Sign Up",
                    "payload": signup_url,
                    "type": "url"
                },
                {
                    "title": "Already have an account? Login",
                    "payload": "https://promoghana.com/customer/auth/login",
                    "type": "url"
                }
            ]
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []

class ActionRedirectLogin(Action):
    def name(self) -> Text:
        return "action_redirect_login"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Generate login URL
        login_url = "https://promoghana.com/customer/auth/login"
        
        # Multilingual responses
        responses = {
            'en': "I'll redirect you to our login page where you can access your account.",
            'ha': "Zan mai da kai zuwa shafin shiga inda za ka iya samun damar shiga account ɗinka.",
            'ee': "Matrɔ wò ayi míaƒe geɖeme axa la dzi afisi nàte ŋu aʋu wò akɔnt le.",
            'tw': "Mɛma wo akɔ yɛn login page a wobɛtumi akɔ wo account mu wɔ hɔ.",
            'dagbani': "N ni zaŋ a ti ti login page din ni a ni tooi kpe a account maa ni."
        }
        
        # Get response in appropriate language
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "login_redirect",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "login_redirect",
            "redirect_url": login_url,
            "buttons": [
                {
                    "title": "Login",
                    "payload": login_url,
                    "type": "url"
                },
                {
                    "title": "Don't have an account? Sign Up",
                    "payload": "https://promoghana.com/customer/auth/sign-up",
                    "type": "url"
                }
            ]
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []
    

class ActionContactSupport(Action):
    def name(self) -> Text:
        return "action_contact_support"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Customer service contact information
        phone_number = "+233596782334"
        email = "contact@promogo.ga"
        whatsapp = "+233596782334"
        
        # Multilingual responses
        responses = {
            'en': f"You can contact our support team via:\n- Phone: {phone_number}\n- Email: {email}\n- WhatsApp: {whatsapp}\nOr click the button below to start a conversation.",
            'ha': f"Kana iya tuntuɓar ƙungiyar tallafin mu ta hanyar:\n- Waya: {phone_number}\n- Imel: {email}\n- WhatsApp: {whatsapp}\nKo danna maɓallin da ke ƙasa don fara tattaunawa.",
            'ee': f"Àte ŋu ade míaƒe kpekpeɖeŋu hatso ŋu to:\n- Kaƒomɔ: {phone_number}\n- Email: {email}\n- WhatsApp: {whatsapp}\nAlo zi bɔtini si le ete la dzi be nàdze dzeɖoɖo gɔme.",
            'tw': f"Wobɛtumi aka yɛn support team:\n- Phone: {phone_number}\n- Email: {email}\n- WhatsApp: {whatsapp}\nAnaa klik button a ɛwɔ aseɛ yi na woahyɛ nkɔmmɔdie ase.",
            'dagbani': f"A ni tooi paai ti sɔŋsim team:\n- Phone: {phone_number}\n- Email: {email}\n- WhatsApp: {whatsapp}\nBee nya button din be tiŋa ni ka a pili suhudoo."
        }
        
        # Get response in appropriate language
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "contact_support",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "customer_support",
            "contact_info": {
                "phone": phone_number,
                "email": email,
                "whatsapp": whatsapp
            },
            "buttons": [
                {
                    "title": "Call Support",
                    "payload": f"tel:{phone_number}",
                    "type": "phone"
                },
                {
                    "title": "Email Support",
                    "payload": f"mailto:{email}",
                    "type": "email"
                },
                {
                    "title": "WhatsApp Support",
                    "payload": f"https://api.whatsapp.com/send/?phone={whatsapp.replace('+', '')}&text&type=phone_number",
                    "type": "url"
                }
            ]
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []

class ActionSearchProducts(Action):
    """
    Action to search for products and provide search results with links.
    This is triggered after the purchase form collects the product information.
    """
    def name(self) -> Text:
        return "action_search_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Get the product from slot
        product = tracker.get_slot("product")
        
        if not product:
            # If no product, ask for it
            return [FollowupAction("purchase_form")]
        
        # Generate search URL with proper URL encoding
        import urllib.parse
        encoded_product = urllib.parse.quote(product)
        search_url = f"https://promoghana.com/products?name={encoded_product}&global_search_input=1&data_from=search&category=all"
        
        # Multilingual responses for search results
        responses = {
            'en': f"Great! Here are the search results for '{product}'. You can browse available options and make your purchase.",
            'ha': f"Da kyau! Ga sakamakon binciken '{product}'. Za ka iya duba zaɓuɓɓukan da ake da su ka yi saya.",
            'ee': f"Enyo! Esia nye '{product}' ƒe didiwo ƒe emetsonuwo. Àte ŋu akpɔ tiatia siwo li eye nàƒle.",
            'tw': f"Ɛyɛ papa! Yei ne '{product}' ho nhwehwɛmu. Wobɛtumi ahwɛ nneɛma a ɛwɔ hɔ na woatɔ.",
            'dagbani': f"Ka viɛnyɛla! Ŋuna nyɛla '{product}' ŋɔ dɔɣim mali. A ni tooi kpɛm bini siɛla bee ka a da."
        }
        
        # Get response in appropriate language
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "product_search_results",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "product_search_results",
            "redirect_url": search_url,
            "product_searched": product,
            "buttons": [
                {
                    "title": "View Search Results",
                    "payload": search_url,
                    "type": "url"
                }
            ]
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        # Reset the product slot for next search
        return [SlotSet("product", None)]

class ValidatePurchaseForm(FormValidationAction):
    """
    Validates the purchase form inputs
    """
    def name(self) -> Text:
        return "validate_purchase_form"

    def validate_product(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate product slot."""
        
        # Get language from metadata
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        if slot_value and len(slot_value.strip()) > 0:
            # Product is valid
            return {"product": slot_value.strip()}
        else:
            # Product is invalid, ask again
            error_messages = {
                'en': "Please specify a valid product name.",
                'ha': "Da fatan za ka bayyana sunan kaya mai inganci.",
                'ee': "Taflatse gblɔ nu ƒe ŋkɔ nyuitɔ.",
                'tw': "Yɛsrɛ wo sɛ ka nneɛma no din a ɛfata.",
                'dagbani': "Tuma ka a goli bini yuli mali."
            }
            
            error_message = error_messages.get(language, error_messages['en'])
            dispatcher.utter_message(text=error_message)
            return {"product": None}

class ValidateSalesForm(FormValidationAction):
    """
    Validates the sales form inputs
    """
    def name(self) -> Text:
        return "validate_sales_form"

    def validate_product(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate product slot."""
        
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        if slot_value and len(slot_value.strip()) > 0:
            return {"product": slot_value.strip()}
        else:
            error_messages = {
                'en': "Please specify a valid product name.",
                'ha': "Da fatan za ka bayyana sunan kaya mai inganci.",
                'ee': "Taflatse gblɔ nu ƒe ŋkɔ nyuitɔ.",
                'tw': "Yɛsrɛ wo sɛ ka nneɛma no din a ɛfata.",
                'dagbani': "Tuma ka a goli bini yuli mali."
            }
            
            error_message = error_messages.get(language, error_messages['en'])
            dispatcher.utter_message(text=error_message)
            return {"product": None}

    def validate_price(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate price slot."""
        
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        try:
            # Try to convert to float
            if slot_value is not None:
                price_value = float(slot_value)
                if price_value > 0:
                    return {"price": price_value}
                else:
                    raise ValueError("Price must be positive")
            else:
                raise ValueError("Price is required")
        except (ValueError, TypeError):
            error_messages = {
                'en': "Please enter a valid price (positive number).",
                'ha': "Da fatan za ka shigar da farashi mai inganci (lamba mai kyau).",
                'ee': "Taflatse de asi home nyuitɔ (xexlẽme nyuitɔ).",
                'tw': "Yɛsrɛ wo sɛ fa sika a ɛfata (nɔma pa) to mu.",
                'dagbani': "Tuma ka a goli ligri mali (nambarɔ mali)."
            }
            
            error_message = error_messages.get(language, error_messages['en'])
            dispatcher.utter_message(text=error_message)
            return {"price": None}

    def validate_condition(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate condition slot."""
        
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        if slot_value and len(slot_value.strip()) > 0:
            # Normalize common condition values
            condition_lower = slot_value.lower().strip()
            valid_conditions = {
                'new': ['new', 'neuf', 'nouveau', 'yeye', 'foforɔ', 'paalli'],
                'used': ['used', 'occasion', 'utilisé', 'wozãe', 'wɔde adi dwuma', 'kpahirili'],
                'like new': ['like new', 'comme neuf', 'abe yeye ene', 'sɛ foforɔ', 'sɔŋ paalli'],
                'refurbished': ['refurbished', 'rénové', 'wɔtrɔe', 'wɔasiesie', 'zaŋ paalli']
            }
            
            # Check if the condition matches any known values
            for standard_condition, variations in valid_conditions.items():
                if condition_lower in variations:
                    return {"condition": standard_condition}
            
            # If not a standard condition, accept the user input
            return {"condition": slot_value.strip()}
        else:
            error_messages = {
                'en': "Please specify the condition of your product (new, used, etc.).",
                'ha': "Da fatan za ka bayyana yanayin kayan ku (sabon, an yi amfani da shi, da sauransu).",
                'ee': "Taflatse gblɔ wò nu ƒe nɔnɔme (yeye, wozãe, etc.).",
                'tw': "Yɛsrɛ wo sɛ ka wo nneɛma no tebea (foforɔ, wɔde adi dwuma, etc.).",
                'dagbani': "Tuma ka a goli a bini maa noli (paalli, kpahirili, etc.)."
            }
            
            error_message = error_messages.get(language, error_messages['en'])
            dispatcher.utter_message(text=error_message)
            return {"condition": None}

    def validate_location(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate location slot."""
        
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        if slot_value and len(slot_value.strip()) > 0:
            return {"location": slot_value.strip()}
        else:
            error_messages = {
                'en': "Please specify your location for the sale.",
                'ha': "Da fatan za ka bayyana inda kake don sayarwa.",
                'ee': "Taflatse gblɔ afisi nèle na dzadzra.",
                'tw': "Yɛsrɛ wo sɛ ka baabi a wowɔ a wopɛ sɛ wotɔn.",
                'dagbani': "Tuma ka a goli yin ka a be ni a ni kɔhi."
            }
            
            error_message = error_messages.get(language, error_messages['en'])
            dispatcher.utter_message(text=error_message)
            return {"location": None}

class ActionOpenSellerApp(Action):
    def name(self) -> Text:
        return "action_open_seller_app"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Generate seller app URL
        seller_app_url = "https://promoghana.com/seller-app"
        
        # Multilingual responses
        responses = {
            'en': "I'll redirect you to our seller app where you can manage your listings.",
            'ha': "Zan mai da kai zuwa app ɗin mai sayarwa inda za ka iya sarrafa jerin kayan ka.",
            'ee': "Matrɔ wò ayi míaƒe dzrala ƒe app si me nàte ŋu aɖo wò nudzralawo ŋu le.",
            'tw': "Mɛma wo akɔ yɛn seller app a wobɛtumi ahwɛ wo nneɛma a wotɔn no so.",
            'dagbani': "N ni zaŋ a ti seller app din ni a ni tooi sɔŋ a kɔhibu maa."
        }
        
        # Get response in appropriate language
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "open_seller_app",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "app_redirect",
            "redirect_url": seller_app_url
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []

class ActionOpenBuyerApp(Action):
    def name(self) -> Text:
        return "action_open_buyer_app"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Generate buyer app URL
        buyer_app_url = "https://promoghana.com/buyer-app"
        
        # Multilingual responses
        responses = {
            'en': "I'll redirect you to our buyer app where you can browse and purchase products.",
            'ha': "Zan mai da kai zuwa app ɗin mai saya inda za ka iya duba da sayen kayayyaki.",
            'ee': "Matrɔ wò ayi míaƒe nuƒlela ƒe app si me nàte ŋu akpɔ eye nàƒle nuwo le.",
            'tw': "Mɛma wo akɔ yɛn buyer app a wobɛtumi ahwɛ na woatɔ nneɛma wɔ hɔ.",
            'dagbani': "N ni zaŋ a ti buyer app din ni a ni tooi kpɛm bee da bini."
        }
        
        # Get response in appropriate language
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "open_buyer_app",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "app_redirect",
            "redirect_url": buyer_app_url
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []

class ActionOpenDeliveryApp(Action):
    def name(self) -> Text:
        return "action_open_delivery_app"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get language from metadata or default to English
        language = tracker.latest_message.get('metadata', {}).get('language', 'en')
        
        # Generate delivery app URL
        delivery_app_url = "https://promoghana.com/delivery-app"
        
        # Multilingual responses
        responses = {
            'en': "I'll redirect you to our delivery app where you can track your orders and deliveries.",
            'ha': "Zan mai da kai zuwa app ɗin isar da kaya inda za ka iya bin diddigin odar ka da isar da kaya.",
            'ee': "Matrɔ wò ayi míaƒe ɖoɖo ƒe app si me nàte ŋu akpɔ wò ɖoɖowo kple ɖoɖowo ŋu le.",
            'tw': "Mɛma wo akɔ yɛn delivery app a wobɛtumi ahwɛ wo orders ne deliveries.",
            'dagbani': "N ni zaŋ a ti delivery app din ni a ni tooi kpɛm a orders bee deliveries maa."
        }
        
        # Get response in appropriate language
        response = responses.get(language, responses['en'])
        
        # Structure the response for API consumption
        response_data = {
            "intent": "open_delivery_app",
            "language": language,
            "confidence": 1.0,
            "response": response,
            "context": "app_redirect",
            "redirect_url": delivery_app_url
        }
        
        # Send the structured data for API
        dispatcher.utter_message(json_message=response_data)
        
        return []