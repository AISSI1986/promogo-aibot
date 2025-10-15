"""
Language configuration for Promogo Assistant
Optimized for English, Hausa, Twi, and Ewe
"""

# Primary languages supported by Promogo
PROMOGO_LANGUAGES = {
    "en": {
        "name": "English",
        "flag": "🇬🇧",
        "country": "United Kingdom",
        "tts_model": "facebook/mms-tts-eng",
        "stt_model": "facebook/wav2vec2-base-960h",
        "priority": 1
    },
    "ha": {
        "name": "Hausa",
        "flag": "🇳🇬", 
        "country": "Nigeria",
        "tts_model": "facebook/mms-tts-hau",
        "stt_model": "facebook/wav2vec2-large-xlsr-53-hausa",
        "priority": 2
    },
    "tw": {
        "name": "Twi",
        "flag": "🇬🇭",
        "country": "Ghana", 
        "tts_model": "facebook/mms-tts-twi",
        "stt_model": "facebook/wav2vec2-large-xlsr-53-twi",
        "priority": 3
    },
    "ee": {
        "name": "Eʋegbe",
        "flag": "🇬🇭",
        "country": "Ghana",
        "tts_model": "facebook/mms-tts-ewe", 
        "stt_model": "facebook/wav2vec2-large-xlsr-53-ewe",
        "priority": 4
    }
}

# Additional supported languages (lower priority)
ADDITIONAL_LANGUAGES = {
    "fr": {
        "name": "French",
        "flag": "🇫🇷",
        "country": "France",
        "tts_model": "facebook/mms-tts-fra",
        "stt_model": "facebook/wav2vec2-large-xlsr-53-french",
        "priority": 5
    },
    "es": {
        "name": "Spanish", 
        "flag": "🇪🇸",
        "country": "Spain",
        "tts_model": "facebook/mms-tts-spa",
        "stt_model": "facebook/wav2vec2-large-xlsr-53-spanish",
        "priority": 6
    },
    "de": {
        "name": "German",
        "flag": "🇩🇪", 
        "country": "Germany",
        "tts_model": "facebook/mms-tts-deu",
        "stt_model": "facebook/wav2vec2-large-xlsr-53-german",
        "priority": 7
    }
}

# Combined language configuration
ALL_LANGUAGES = {**PROMOGO_LANGUAGES, **ADDITIONAL_LANGUAGES}

# Get primary languages only
def get_primary_languages():
    """Get only the primary Promogo languages"""
    return PROMOGO_LANGUAGES

# Get all supported languages
def get_all_languages():
    """Get all supported languages"""
    return ALL_LANGUAGES

# Get TTS models for primary languages
def get_tts_models():
    """Get TTS model mapping for primary languages"""
    return {lang: config["tts_model"] for lang, config in PROMOGO_LANGUAGES.items()}

# Get STT models for primary languages  
def get_stt_models():
    """Get STT model mapping for primary languages"""
    return {lang: config["stt_model"] for lang, config in PROMOGO_LANGUAGES.items()}

# Language validation
def is_supported_language(lang_code):
    """Check if language code is supported"""
    return lang_code in ALL_LANGUAGES

def is_primary_language(lang_code):
    """Check if language is a primary Promogo language"""
    return lang_code in PROMOGO_LANGUAGES

# Get language info
def get_language_info(lang_code):
    """Get detailed information about a language"""
    return ALL_LANGUAGES.get(lang_code, None)

# Default language
DEFAULT_LANGUAGE = "en"

# Language display order (primary languages first)
LANGUAGE_ORDER = ["en", "ha", "tw", "ee", "fr", "es", "de"]
