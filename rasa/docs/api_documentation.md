# API Documentation - Promogo Multilingual Chatbot

## Base URL
```
https://promogo.souciance.com
```

## Endpoints

### 1. Send Message
Send a message to the chatbot and get a response.

**Endpoint:** `POST /webhooks/rest/webhook`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "sender": "string",      // Unique identifier for the user/session
    "message": "string",     // The message text to send
    "metadata": {
        "language": "string" // Language code (en, ha, ee, tw, dagbani)
    }
}
```

**Language Codes:**
- `en`: English
- `ha`: Hausa
- `ee`: Ewe
- `tw`: Twi
- `dagbani`: Dagbani

**Example Request:**
```json
{
    "sender": "Promogo",
    "message": "sannu",
    "metadata": {
        "language": "ha"
    }
}
```

**Example Response:**
```json
[
    {
        "recipient_id": "Promogo",
        "custom": {
            "intent": "greet",
            "language": "ha",
            "confidence": 0.9,
            "response": "Maakye! Dɛn na metumi ayɛ?"
        }
    }
]
```

### 2. Get Model Status
Check if the model is running and ready to process requests.

**Endpoint:** `GET /status`

**Response:**
```json
{
    "model_file": "20250515-095041-parallel-wetland.tar.gz",
    "model_id": "b27b5e5d8d964490b8700eafe6f3cdef",
    "num_active_training_jobs": 0
}
```

## Common Intents

The chatbot can handle the following intents in multiple languages:

1. **Greetings**
   - English: "hello", "hi", "good morning"
   - Hausa: "sannu", "barka", "barka da safe"
   - Ewe: "Ŋdi na wo", "Woezɔ"
   - Twi: "Maakye", "Maaha", "Maadwo"
   - Dagbani: "Antire", "Dasiba"

2. **Goodbye**
   - English: "bye", "goodbye", "see you later"
   - Hausa: "sai an jima", "sai wata rana"
   - Ewe: "Gbugbɔ dze egɔme", "Miadogo"
   - Twi: "Yɛbɛhyia bio", "Nante yie"
   - Dagbani: "Nasaara", "Nya da pa"

3. **Thank You**
   - English: "thanks", "thank you"
   - Hausa: "na gode", "na gode sosai"
   - Ewe: "Akpe", "Akpe kaka"
   - Twi: "Medaase", "Meda wo ase"
   - Dagbani: "Tipalana", "Tipalana pam"

4. **Help**
   - English: "I need help", "Can you help me?"
   - Hausa: "Don Allah taimaka min"
   - Ewe: "Mebu kpekpeɖeŋu"
   - Twi: "Mesrɛ mmoa"
   - Dagbani: "N bɔra ni n nya sɔŋsim"

5. **Price Inquiry**
   - English: "How much is it?", "What's the price?"
   - Hausa: "Nawa zan biya don wannan?"
   - Ewe: "Nukae nye asixɔxɔ?"
   - Twi: "Ne bo yɛ dɛn?"
   - Dagbani: "Ligidi yɛligu ka?"

## Error Responses

### 400 Bad Request
```json
{
    "error": "Invalid request format",
    "details": "Missing required field: message"
}
```

### 500 Internal Server Error
```json
{
    "error": "Internal server error",
    "details": "Model failed to process request"
}
```

## Best Practices

1. **Sender ID**
   - Use a unique identifier for each user/session
   - Keep the same sender ID for the entire conversation
   - Avoid special characters in the sender ID

2. **Language Selection**
   - Always specify the language in metadata
   - Use the correct language code
   - Keep the language consistent throughout the conversation

3. **Message Format**
   - Keep messages concise
   - Use proper punctuation
   - Avoid special characters unless necessary

4. **Error Handling**
   - Implement proper error handling for all API calls
   - Check response status codes
   - Handle timeout scenarios

## Testing

You can test the API using the following curl command:

```bash
curl -X POST https://promogo.souciance.com/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user",
    "message": "sannu",
    "metadata": {
        "language": "tw"
    }
  }'
```