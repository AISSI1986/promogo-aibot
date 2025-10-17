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

class ActionFallback(Action):
    """Action to handle fallback responses"""
    
    def name(self) -> Text:
        return "action_default_fallback"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the latest user message
        user_message = tracker.latest_message.get('text', '')
        
        # Log the fallback
        logger.warning(f"Fallback triggered for message: {user_message}")
        
        # Send a fallback response
        dispatcher.utter_message(text="Sorry, I didn't understand that. Can you try again?")
        
        return []

class ActionRestart(Action):
    """Action to restart the conversation"""
    
    def name(self) -> Text:
        return "action_restart"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Reset all slots
        return [SlotSet(slot, None) for slot in tracker.slots.keys()]

class ActionResetSlots(Action):
    """Action to reset conversation slots"""
    
    def name(self) -> Text:
        return "action_reset_slots"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Reset form-related slots
        return [
            SlotSet("product", None),
            SlotSet("price", None),
            SlotSet("condition", None),
            SlotSet("location", None),
            SlotSet("quantity", None),
            SlotSet("requested_slot", None)
        ]

class ActionProcessPurchase(Action):
    """Action to process purchase requests"""
    
    def name(self) -> Text:
        return "action_process_purchase"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        product = tracker.get_slot("product")
        
        if product:
            dispatcher.utter_message(text=f"Great! I'll help you find {product}. Let me search our inventory...")
        else:
            dispatcher.utter_message(text="I'd be happy to help you find products. What are you looking for?")
        
        return []

class ActionProcessSale(Action):
    """Action to process sale requests"""
    
    def name(self) -> Text:
        return "action_process_sale"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        product = tracker.get_slot("product")
        price = tracker.get_slot("price")
        condition = tracker.get_slot("condition")
        location = tracker.get_slot("location")
        
        dispatcher.utter_message(
            text=f"Perfect! I've recorded your listing: {product} for {price} ({condition}) in {location}. "
                 "Your item will be posted on our platform shortly!"
        )
        
        return []

class ActionSearchProducts(Action):
    """Action to search for products"""
    
    def name(self) -> Text:
        return "action_search_products"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        product = tracker.get_slot("product")
        
        if product:
            dispatcher.utter_message(text=f"Searching for {product}... Here are some options I found!")
        else:
            dispatcher.utter_message(text="I'd be happy to help you search for products. What are you looking for?")
        
        return []

class ActionRedirectSignup(Action):
    """Action to redirect to signup"""
    
    def name(self) -> Text:
        return "action_redirect_signup"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="To sign up, please visit our website or download our mobile app!")
        
        return []

class ActionRedirectLogin(Action):
    """Action to redirect to login"""
    
    def name(self) -> Text:
        return "action_redirect_login"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="To log in, please visit our website or use our mobile app!")
        
        return []

class ActionContactSupport(Action):
    """Action to contact support"""
    
    def name(self) -> Text:
        return "action_contact_support"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(
            text="For support, you can reach us at support@promogo.com or call +233-XXX-XXXX. "
                 "We're here to help!"
        )
        
        return []

class ActionOpenSellerApp(Action):
    """Action to open seller app"""
    
    def name(self) -> Text:
        return "action_open_seller_app"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="To access the seller app, please download it from the App Store or Google Play!")
        
        return []

class ActionOpenBuyerApp(Action):
    """Action to open buyer app"""
    
    def name(self) -> Text:
        return "action_open_buyer_app"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="To access the buyer app, please download it from the App Store or Google Play!")
        
        return []

class ActionOpenDeliveryApp(Action):
    """Action to open delivery app"""
    
    def name(self) -> Text:
        return "action_open_delivery_app"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="To access the delivery app, please download it from the App Store or Google Play!")
        
        return []

# Form validation actions
class ValidatePurchaseForm(FormValidationAction):
    """Validates purchase form inputs"""
    
    def name(self) -> Text:
        return "validate_purchase_form"
    
    def validate_product(self, slot_value: Any, dispatcher: CollectingDispatcher,
                        tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        
        if slot_value:
            return {"product": slot_value}
        else:
            dispatcher.utter_message(text="What product are you looking for?")
            return {"product": None}

class ValidateSalesForm(FormValidationAction):
    """Validates sales form inputs"""
    
    def name(self) -> Text:
        return "validate_sales_form"
    
    def validate_product(self, slot_value: Any, dispatcher: CollectingDispatcher,
                        tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        
        if slot_value:
            return {"product": slot_value}
        else:
            dispatcher.utter_message(text="What product do you want to sell?")
            return {"product": None}
    
    def validate_price(self, slot_value: Any, dispatcher: CollectingDispatcher,
                      tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        
        if slot_value and isinstance(slot_value, (int, float)) and slot_value > 0:
            return {"price": slot_value}
        else:
            dispatcher.utter_message(text="What price do you want to sell it for?")
            return {"price": None}
    
    def validate_condition(self, slot_value: Any, dispatcher: CollectingDispatcher,
                          tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        
        if slot_value:
            return {"condition": slot_value}
        else:
            dispatcher.utter_message(text="What condition is the item in? (new, used, etc.)")
            return {"condition": None}
    
    def validate_location(self, slot_value: Any, dispatcher: CollectingDispatcher,
                         tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        
        if slot_value:
            return {"location": slot_value}
        else:
            dispatcher.utter_message(text="Where are you located?")
            return {"location": None}