import os
import requests
from typing import Tuple, Optional


def parse_intent_with_rasa(sender_id: str, text: str, language_code: str = "en") -> Tuple[Optional[str], Optional[str], float]:
    """Parse intent using Rasa's HTTP API and optionally fetch a bot response.

    Returns: (intent_name, bot_text_response, confidence)
    """
    base_url = os.getenv("RASA_BASE_URL", "https://promogo-rasa.onrender.com")

    # 1) Parse intent
    intent_name: Optional[str] = None
    confidence: float = 0.0
    try:
        parse_resp = requests.post(
            f"{base_url}/model/parse",
            json={"text": text},
            timeout=15,
        )
        if parse_resp.ok:
            data = parse_resp.json()
            intent = data.get("intent") or {}
            intent_name = intent.get("name")
            confidence = float(intent.get("confidence") or 0.0)
    except Exception:
        pass

    # 2) If intent looks good, get response via REST webhook
    bot_text: Optional[str] = None
    if intent_name and confidence > 0.0:
        try:
            resp = requests.post(
                f"{base_url}/webhooks/rest/webhook",
                json={"sender": sender_id, "message": text},
                timeout=20,
            )
            if resp.ok:
                messages = resp.json() or []
                # Concatenate all bot messages' text
                texts = [m.get("text") for m in messages if isinstance(m, dict) and m.get("text")]
                if texts:
                    bot_text = "\n".join(texts)
        except Exception:
            pass

    return intent_name, bot_text, confidence


