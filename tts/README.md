# API de Synthèse Vocale Multilingue 🎙️

Une API REST puissante pour la synthèse vocale (Text-to-Speech) supportant plusieurs langues africaines et l'anglais, utilisant les modèles Hugging Face.

## 🌍 Langues Supportées

- **Anglais** (English)
- **Haoussa** (Hausa)
- **Éwé** (Ewe)
- **Twi** (Akan)
- **Ga**

## ✨ Fonctionnalités

- API REST simple et intuitive avec FastAPI
- Support multilingue avec des modèles spécialisés pour chaque langue
- Génération audio en temps réel
- Containerisation Docker pour un déploiement facile
- Cache persistant pour les modèles téléchargés
- Support GPU optionnel pour des performances améliorées
- Documentation API automatique (Swagger/OpenAPI)

## 📋 Prérequis

- Python 3.10+
- Docker et Docker Compose (optionnel)
- GPU NVIDIA avec CUDA 11.8+ (optionnel, pour l'accélération GPU)
- Au moins 8GB de RAM
- 20GB d'espace disque libre (pour les modèles)

## 🚀 Installation

### Option 1: Installation Locale

1. **Cloner le repository**
   \`\`\`bash
   git clone https://github.com/votre-username/speech-synthesis-api.git
   cd speech-synthesis-api
   \`\`\`

2. **Créer un environnement virtuel**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   \`\`\`

3. **Installer les dépendances**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Lancer l'API**
   \`\`\`bash
   python app.py
   \`\`\`

### Option 2: Installation avec Docker

1. **Construire et lancer avec Docker Compose**
   \`\`\`bash
   docker-compose up -d
   \`\`\`

2. **Pour le support GPU**
   \`\`\`bash
   docker-compose -f docker-compose.gpu.yml up -d
   \`\`\`

## 📖 Utilisation

### Endpoint Principal

**POST** `/synthesize/`

Génère de la parole à partir du texte fourni.

#### Paramètres de la requête

\`\`\`json
{
  "text": "Texte à synthétiser",
  "language": "hausa",
  "speaker_id": null
}
\`\`\`

- `text` (string, requis): Le texte à convertir en parole
- `language` (string, requis): La langue cible (`english`, `hausa`, `ewe`, `twi`, `ga`)
- `speaker_id` (string, optionnel): ID du locuteur (si supporté par le modèle)

#### Exemple avec cURL

\`\`\`bash
# Synthèse en anglais
curl -X POST "http://localhost:8000/synthesize/" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, how are you?", "language": "english"}' \
     --output english_output.wav

# Synthèse en haoussa
curl -X POST "http://localhost:8000/synthesize/" \
     -H "Content-Type: application/json" \
     -d '{"text": "Sannu, yaya kake?", "language": "hausa"}' \
     --output hausa_output.wav
\`\`\`

### Exemple avec Python

\`\`\`python
import requests

def synthesize_speech(text, language, output_file):
    url = "http://localhost:8000/synthesize/"
    
    payload = {
        "text": text,
        "language": language
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Audio sauvegardé dans {output_file}")
    else:
        print(f"Erreur: {response.status_code}")
        print(response.text)

# Utilisation
synthesize_speech("Bonjour le monde", "english", "output.wav")
\`\`\`

## 📚 Documentation API

Une fois l'API lancée, accédez à la documentation interactive :

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐳 Configuration Docker

### Variables d'environnement

Vous pouvez configurer les variables suivantes dans `docker-compose.yml` :

- `TRANSFORMERS_CACHE`: Chemin du cache pour les modèles Hugging Face
- `PYTORCH_CUDA_ALLOC_CONF`: Configuration de l'allocation mémoire CUDA
- `CUDA_VISIBLE_DEVICES`: GPU à utiliser (pour le support GPU)

### Volumes

- `huggingface-cache`: Stockage persistant pour les modèles téléchargés

## 🔧 Dépannage

### Problème : "Out of Memory"

**Solution** : Augmentez la limite de mémoire dans `docker-compose.yml` ou utilisez un modèle plus petit.

### Problème : "Model not found"

**Solution** : Vérifiez votre connexion internet. Les modèles sont téléchargés automatiquement au premier lancement.

### Problème : Téléchargement lent des modèles

**Solution** : Les modèles peuvent être volumineux (plusieurs GB). Assurez-vous d'avoir une bonne connexion internet. Les modèles sont mis en cache après le premier téléchargement.

### Problème : Qualité audio médiocre

**Solution** : Certaines langues peuvent avoir des modèles de qualité variable. Essayez d'ajuster le texte d'entrée ou envisagez de fine-tuner un modèle personnalisé.

## 🏗️ Architecture

\`\`\`
speech-synthesis-api/
├── app.py              # Application FastAPI principale
├── client.py           # Client Python exemple
├── requirements.txt    # Dépendances Python
├── Dockerfile         # Configuration Docker
├── docker-compose.yml # Configuration Docker Compose
└── README.md          # Ce fichier
\`\`\`

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- [Hugging Face](https://huggingface.co/) pour les modèles de synthèse vocale
- [FastAPI](https://fastapi.tiangolo.com/) pour le framework web
- [Meta AI](https://ai.meta.com/) pour les modèles MMS-TTS
- [Microsoft](https://www.microsoft.com/) pour le modèle SpeechT5

## 📞 Support

Pour toute question ou problème :

- Ouvrez une issue sur GitHub
- Contactez-nous à : [votre-email@example.com]

---

**Note** : Ce projet est en développement actif. Les fonctionnalités et les modèles supportés peuvent évoluer.
\`\`\`

J'ai également créé un fichier README en anglais si vous préférez :

```md project="Speech Synthesis API" file="README.en.md" type="markdown"
# Multilingual Speech Synthesis API 🎙️

A powerful REST API for Text-to-Speech synthesis supporting multiple African languages and English, powered by Hugging Face models.

## 🌍 Supported Languages

- **English**
- **Hausa**
- **Ewe**
- **Twi** (Akan)
- **Ga**

## ✨ Features

- Simple and intuitive REST API with FastAPI
- Multi-language support with specialized models for each language
- Real-time audio generation
- Docker containerization for easy deployment
- Persistent cache for downloaded models
- Optional GPU support for improved performance
- Automatic API documentation (Swagger/OpenAPI)

## 📋 Prerequisites

- Python 3.10+
- Docker and Docker Compose (optional)
- NVIDIA GPU with CUDA 11.8+ (optional, for GPU acceleration)
- At least 8GB RAM
- 20GB free disk space (for models)

## 🚀 Installation

### Option 1: Local Installation

1. **Clone the repository**
   \`\`\`bash
   git clone https://github.com/your-username/speech-synthesis-api.git
   cd speech-synthesis-api
   \`\`\`

2. **Create a virtual environment**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`

3. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Run the API**
   \`\`\`bash
   python app.py
   \`\`\`

### Option 2: Docker Installation

1. **Build and run with Docker Compose**
   \`\`\`bash
   docker-compose up -d
   \`\`\`

2. **For GPU support**
   \`\`\`bash
   docker-compose -f docker-compose.gpu.yml up -d
   \`\`\`

## 📖 Usage

### Main Endpoint

**POST** `/synthesize/`

Generates speech from provided text.

#### Request Parameters

\`\`\`json
{
  "text": "Text to synthesize",
  "language": "hausa",
  "speaker_id": null
}
\`\`\`

- `text` (string, required): The text to convert to speech
- `language` (string, required): Target language (`english`, `hausa`, `ewe`, `twi`, `ga`)
- `speaker_id` (string, optional): Speaker ID (if supported by the model)

#### Example with cURL

\`\`\`bash
# English synthesis
curl -X POST "http://localhost:8000/synthesize/" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, how are you?", "language": "english"}' \
     --output english_output.wav

# Hausa synthesis
curl -X POST "http://localhost:8000/synthesize/" \
     -H "Content-Type: application/json" \
     -d '{"text": "Sannu, yaya kake?", "language": "hausa"}' \
     --output hausa_output.wav
\`\`\`

### Python Example

\`\`\`python
import requests

def synthesize_speech(text, language, output_file):
    url = "http://localhost:8000/synthesize/"
    
    payload = {
        "text": text,
        "language": language
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Audio saved to {output_file}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Usage
synthesize_speech("Hello world", "english", "output.wav")
\`\`\`

## 📚 API Documentation

Once the API is running, access the interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐳 Docker Configuration

### Environment Variables

You can configure the following variables in `docker-compose.yml`:

- `TRANSFORMERS_CACHE`: Cache path for Hugging Face models
- `PYTORCH_CUDA_ALLOC_CONF`: CUDA memory allocation configuration
- `CUDA_VISIBLE_DEVICES`: GPU to use (for GPU support)

### Volumes

- `huggingface-cache`: Persistent storage for downloaded models

## 🔧 Troubleshooting

### Issue: "Out of Memory"

**Solution**: Increase memory limit in `docker-compose.yml` or use a smaller model.

### Issue: "Model not found"

**Solution**: Check your internet connection. Models are downloaded automatically on first run.

### Issue: Slow model download

**Solution**: Models can be large (several GB). Ensure you have a good internet connection. Models are cached after first download.

### Issue: Poor audio quality

**Solution**: Some languages may have varying model quality. Try adjusting input text or consider fine-tuning a custom model.

## 🏗️ Architecture

\`\`\`
speech-synthesis-api/
├── app.py              # Main FastAPI application
├── client.py           # Example Python client
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
└── README.md          # This file
\`\`\`

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🙏 Acknowledgments

- [Hugging Face](https://huggingface.co/) for speech synthesis models
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Meta AI](https://ai.meta.com/) for MMS-TTS models
- [Microsoft](https://www.microsoft.com/) for SpeechT5 model

## 📞 Support

For questions or issues:

- Open an issue on GitHub
- Contact us at: [your-email@example.com]

---

**Note**: This project is under active development. Features and supported models may evolve.
