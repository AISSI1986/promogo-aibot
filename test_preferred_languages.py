#!/usr/bin/env python3
"""
Test script for Promogo's preferred languages
Tests: English, Hausa, Twi, Ewe
"""

import requests
import json
import time

# Your preferred languages
PREFERRED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧", "test_text": "Hello, how are you today?"},
    "ha": {"name": "Hausa", "flag": "🇳🇬", "test_text": "Sannu, yaya kuke?"},
    "tw": {"name": "Twi", "flag": "🇬🇭", "test_text": "Akwaaba, ɛte sɛn?"},
    "ee": {"name": "Ewe", "flag": "🇬🇭", "test_text": "Woezɔ, alekea?"}
}

# Service URLs (update these with your actual Render URLs)
SERVICES = {
    "tts": "https://promogo-tts.onrender.com",
    "stt": "https://promogo-stt.onrender.com",
    "chatbot": "https://promogo-rasa.onrender.com"
}

def test_service_health():
    """Test if all services are running"""
    print("🔍 Testing service health...")
    
    for service_name, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ {service_name.upper()} service is healthy")
            else:
                print(f"❌ {service_name.upper()} service returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {service_name.upper()} service is not responding: {e}")
    
    print()

def test_language_support():
    """Test language support in TTS and STT services"""
    print("🌍 Testing language support...")
    
    # Test TTS language support
    try:
        response = requests.get(f"{SERVICES['tts']}/languages", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ TTS Language Support:")
            for lang_code in PREFERRED_LANGUAGES.keys():
                if lang_code in data.get("supported_languages", []):
                    lang_info = PREFERRED_LANGUAGES[lang_code]
                    print(f"   {lang_info['flag']} {lang_info['name']} ({lang_code}) - ✅ Supported")
                else:
                    lang_info = PREFERRED_LANGUAGES[lang_code]
                    print(f"   {lang_info['flag']} {lang_info['name']} ({lang_code}) - ❌ Not supported")
        else:
            print("❌ Could not fetch TTS language support")
    except requests.exceptions.RequestException as e:
        print(f"❌ TTS language test failed: {e}")
    
    # Test STT language support
    try:
        response = requests.get(f"{SERVICES['stt']}/languages", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ STT Language Support:")
            for lang_code in PREFERRED_LANGUAGES.keys():
                if lang_code in data.get("supported_languages", []):
                    lang_info = PREFERRED_LANGUAGES[lang_code]
                    print(f"   {lang_info['flag']} {lang_info['name']} ({lang_code}) - ✅ Supported")
                else:
                    lang_info = PREFERRED_LANGUAGES[lang_code]
                    print(f"   {lang_info['flag']} {lang_info['name']} ({lang_code}) - ❌ Not supported")
        else:
            print("❌ Could not fetch STT language support")
    except requests.exceptions.RequestException as e:
        print(f"❌ STT language test failed: {e}")
    
    print()

def test_tts_synthesis():
    """Test TTS synthesis for each preferred language"""
    print("🔊 Testing TTS synthesis...")
    
    for lang_code, lang_info in PREFERRED_LANGUAGES.items():
        print(f"Testing {lang_info['flag']} {lang_info['name']} TTS...")
        
        try:
            payload = {
                "text": lang_info["test_text"],
                "language": lang_code
            }
            
            response = requests.post(
                f"{SERVICES['tts']}/synthesize/",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"   ✅ Success: {data.get('message')}")
                else:
                    print(f"   ❌ Failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        
        time.sleep(1)  # Be nice to the API
    
    print()

def test_chatbot_integration():
    """Test chatbot integration"""
    print("🤖 Testing chatbot integration...")
    
    try:
        payload = {
            "sender": "test_user",
            "message": "Hello, this is a test message"
        }
        
        response = requests.post(
            f"{SERVICES['chatbot']}/webhooks/rest/webhook",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                print(f"✅ Chatbot responded: {data[0].get('text', 'No text')}")
            else:
                print("❌ Chatbot returned empty response")
        else:
            print(f"❌ Chatbot HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Chatbot test failed: {e}")
    
    print()

def main():
    """Run all tests"""
    print("🚀 Promogo Language Testing Suite")
    print("=" * 50)
    print(f"Testing preferred languages: {', '.join([f'{info[\"flag\"]} {info[\"name\"]}' for info in PREFERRED_LANGUAGES.values()])}")
    print()
    
    # Run tests
    test_service_health()
    test_language_support()
    test_tts_synthesis()
    test_chatbot_integration()
    
    print("🏁 Testing complete!")
    print()
    print("📋 Next steps:")
    print("1. Get your Hugging Face token from https://huggingface.co/settings/tokens")
    print("2. Update render.yaml with your token")
    print("3. Redeploy your services")
    print("4. Test with real audio files for STT")

if __name__ == "__main__":
    main()
