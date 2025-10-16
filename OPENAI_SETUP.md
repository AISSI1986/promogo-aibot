# OpenAI Integration Setup Guide

## Overview
The Promogo AI Assistant now includes OpenAI GPT-3.5-turbo integration for handling unrecognized intents. This makes the chatbot much smarter and capable of answering diverse customer queries about Promogo Ghana's products and services.

## Features Added

### 🧠 Smart Response System
- **Predefined Intents**: Handles common queries with fast, consistent responses
- **OpenAI Fallback**: Uses GPT-3.5-turbo for complex or unrecognized queries
- **Knowledge Base**: Trained on data from [Promogo Ghana website](https://promoghana.com/)

### 🌍 Multilingual AI Responses
- **English**: Native English responses from GPT-3.5-turbo
- **Hausa**: Hausa language responses with cultural context
- **Twi**: Twi language responses with local context
- **Eʋegbe**: Eʋegbe language responses with regional context

### 📚 Knowledge Base Content
The chatbot is trained on:
- **Company Information**: Promogo Ghana LTD details
- **Products**: 9+ featured products with prices and descriptions
- **Categories**: 12+ product categories
- **Brands**: 10+ major brands (Samsung, Apple, Toyota, etc.)
- **Policies**: Return policy, delivery, payment information
- **Contact Info**: Phone, email, address details

## Setup Instructions

### 1. Get OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key (starts with `sk-`)

### 2. Configure Environment Variables
In your Render dashboard:

1. Go to your `promogo-rasa` service
2. Navigate to "Environment" tab
3. Add/update the environment variable:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (e.g., `sk-...`)

### 3. Deploy the Updated Service
1. Commit and push your changes to trigger deployment
2. Wait for the service to redeploy (2-3 minutes)
3. Test the smart responses

## How It Works

### Response Flow
```
User Input → Language Detection → Intent Detection
    ↓
Recognized Intent? → Yes → Predefined Response
    ↓
    No → OpenAI GPT-3.5-turbo → Smart Response
```

### Example Interactions

#### English Customer:
- **User**: "What products do you have?"
- **System**: Uses OpenAI with Promogo knowledge base
- **Response**: "We have a wide range of products including Electronics, Phones & Gadgets, Sports & Outdoor, Fashion, and more. Some featured products include the Spinning cardio bike indoor (₵2,700.00), 3D HOLOGRAM DISPLAYER FAN (₵900.00), and Smart TV android 64 inch LG Wisdom (₵6,200.00)."

#### Hausa Customer:
- **User**: "Me kuke sayarwa?"
- **System**: Detects Hausa, uses OpenAI with Hausa instructions
- **Response**: "Muna sayar da kayayyaki da yawa ciki har da na'urorin lantarki, wayoyi da na'urori, wasanni da waje, kayan ado, da sauransu..."

#### Twi Customer:
- **User**: "Ɛdeɛn na wɔtɔn?"
- **System**: Detects Twi, uses OpenAI with Twi instructions
- **Response**: "Yɛtɔ nnuane pii te sɛ Electronics, Phones & Gadgets, Sports & Outdoor, Fashion, ne nnuane foforo..."

## Cost Considerations

### OpenAI Pricing (GPT-3.5-turbo)
- **Input**: $0.0015 per 1K tokens
- **Output**: $0.002 per 1K tokens
- **Estimated cost**: ~$0.01-0.05 per conversation

### Usage Optimization
- Responses limited to 200 tokens max
- Only used for unrecognized intents
- Predefined responses for common queries (free)

## Testing the Integration

### Test Scenarios
1. **Product Questions**: "What electronics do you have?"
2. **Price Inquiries**: "How much is the smart TV?"
3. **Policy Questions**: "What's your return policy?"
4. **Contact Info**: "How can I reach you?"
5. **Complex Queries**: "I need a gift for my mother, what do you recommend?"

### Expected Behavior
- **Fast Responses**: Predefined intents respond instantly
- **Smart Responses**: Complex queries get intelligent answers
- **Multilingual**: Responses in user's detected language
- **Contextual**: Answers based on Promogo Ghana's actual data

## Troubleshooting

### Common Issues
1. **API Key Not Working**: Check if key is correctly set in environment variables
2. **No OpenAI Responses**: Verify API key has sufficient credits
3. **Language Detection Issues**: Check if user input contains language keywords
4. **Knowledge Base Missing**: Ensure `promogo_knowledge_base.json` is in the service directory

### Debug Endpoints
- **Health Check**: `GET /health`
- **Parse Test**: `POST /model/parse` with message
- **Chat Test**: `POST /webhooks/rest/webhook` with message

## Security Notes
- API key is stored securely in environment variables
- No sensitive data is logged
- OpenAI requests are made server-side only
- Rate limiting handled by OpenAI

## Next Steps
1. Set up your OpenAI API key
2. Deploy the updated service
3. Test with various queries in all languages
4. Monitor usage and costs
5. Consider upgrading to GPT-4 for even better responses

The chatbot is now significantly smarter and can handle a much wider range of customer queries while maintaining fast response times for common questions!
