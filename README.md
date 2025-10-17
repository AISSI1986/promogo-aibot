# 🚀 Promogo - Multilingual AI Chatbot

A powerful multilingual AI chatbot that supports 6 African languages with voice and text capabilities, powered by GhanaNLP, Rasa, and OpenAI.

## 🌍 Supported Languages

- **English** 🇬🇧
- **Hausa** 🇳🇬
- **Twi** 🇬🇭
- **Eʋegbe** 🇬🇭
- **Ga** 🇬🇭
- **Dagbani** 🇬🇭

## ✨ Features

- 🎤 **Voice Input/Output** - Speech-to-text and text-to-speech
- 🌐 **Multilingual Support** - 6 African languages
- 🤖 **AI-Powered Responses** - OpenAI GPT-3.5-turbo integration
- 🔄 **Real-time Translation** - GhanaNLP translation services
- 💬 **Natural Conversations** - Rasa dialogue management
- 📱 **Responsive Design** - Works on all devices
- 🎨 **Modern UI** - Beautiful, intuitive interface

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   GhanaNLP      │    │   Rasa + OpenAI │
│   (React App)   │◄──►│   Service       │◄──►│   Service       │
│                 │    │   (STT/TTS/     │    │   (Chatbot +    │
│                 │    │   Translation)  │    │   Actions)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 One-Click Deployment

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Prerequisites

Before deploying, you'll need:

1. **GhanaNLP API Key** - Get from [GhanaNLP Translation API](https://translation.ghananlp.org/)
2. **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/api-keys)

### Deployment Steps

1. **Click the Deploy Button** above
2. **Connect your GitHub account** to Render
3. **Fork this repository** to your GitHub account
4. **Enter your API keys** when prompted:
   - `GHANA_NLP_API_KEY`: Your GhanaNLP API key
   - `OPENAI_API_KEY`: Your OpenAI API key
5. **Deploy** and wait for all services to be ready

## 🔧 Manual Setup

If you prefer to set up manually:

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/promogo.git
cd promogo
```

### 2. Set Up Environment Variables
```bash
# GhanaNLP Service
export GHANA_NLP_API_KEY="your_ghananlp_api_key_here"

# Rasa Service  
export OPENAI_API_KEY="your_openai_api_key_here"
export GHANA_NLP_SERVICE_URL="https://promogo-ghananlp.onrender.com"

# Frontend
export REACT_APP_RASA_URL="https://promogo-rasa.onrender.com/webhooks/rest/webhook"
export REACT_APP_GHANA_NLP_URL="https://promogo-ghananlp.onrender.com"
```

### 3. Deploy Services

**GhanaNLP Service:**
```bash
cd ghananlp
pip install -r requirements.txt
python app.py
```

**Rasa Service:**
```bash
cd rasa
pip install -r requirements.txt
rasa run --enable-api --cors "*" --actions
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## 🧪 Testing

### Test GhanaNLP Service
```bash
curl -X POST https://your-ghananlp-url.onrender.com/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "source_lang": "en", "target_lang": "ha"}'
```

### Test Rasa Service
```bash
curl -X POST https://your-rasa-url.onrender.com/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "message": "Hello"}'
```

## 📱 Usage

1. **Select Language** - Choose from 6 supported languages
2. **Voice Input** - Click the microphone to speak
3. **Text Input** - Type messages using the keyboard
4. **Get Responses** - Receive AI-powered responses in your language
5. **Voice Output** - Listen to responses in your selected language

## 🔑 API Endpoints

### GhanaNLP Service
- `POST /translate` - Translate text between languages
- `POST /transcribe` - Convert speech to text
- `POST /synthesize` - Convert text to speech

### Rasa Service
- `POST /webhooks/rest/webhook` - Chat with the bot
- `GET /webhooks/rest/webhook` - Health check

## 🛠️ Development

### Local Development
```bash
# Install dependencies
npm install  # Frontend
pip install -r requirements.txt  # Python services

# Run services
npm start  # Frontend
python ghananlp/app.py  # GhanaNLP service
cd rasa && rasa run --enable-api --cors "*" --actions  # Rasa service
```

### Project Structure
```
promogo/
├── frontend/           # React frontend
│   ├── app.js         # Main application logic
│   ├── styles.css     # Styling
│   └── index.html     # HTML template
├── ghananlp/          # GhanaNLP service
│   ├── app.py         # FastAPI application
│   └── requirements.txt
├── rasa/              # Rasa chatbot
│   ├── actions/       # Custom actions
│   ├── data/          # Training data
│   └── config.yml     # Rasa configuration
└── render.yaml        # Deployment configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [GhanaNLP](https://ghananlp.org/) - For African language processing
- [Rasa](https://rasa.com/) - For conversational AI framework
- [OpenAI](https://openai.com/) - For AI-powered responses
- [Render](https://render.com/) - For hosting platform

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/promogo/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/promogo/wiki)
- **Community**: [Discussions](https://github.com/yourusername/promogo/discussions)

---

**Made with ❤️ for African languages and communities**
