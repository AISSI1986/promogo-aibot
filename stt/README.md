### API de Reconnaissance Vocale Multilingue

Une API de reconnaissance vocale (STT - Speech-to-Text) multilingue basée sur FastAPI qui prend en charge l'anglais et plusieurs langues africaines (haoussa, twi, ewe) en utilisant des modèles spécifiques de Hugging Face.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Modèles utilisés](#-modèles-utilisés)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Déploiement avec Docker](#-déploiement-avec-docker)
- [Utilisation de l'API](#-utilisation-de-lapi)
- [Structure du projet](#-structure-du-projet)
- [Configuration](#-configuration)
- [Optimisation des performances](#-optimisation-des-performances)
- [Dépannage](#-dépannage)
- [FAQ](#-faq)
- [Licence](#-licence)


## ✨ Fonctionnalités

- Reconnaissance vocale pour 4 langues : anglais, haoussa, twi (ashanti) et ewe
- Modèles spécifiques optimisés pour chaque langue
- API RESTful avec documentation Swagger intégrée
- Chargement asynchrone des modèles
- Support GPU pour des performances optimales
- Déploiement facile avec Docker
- Monitoring et health checks
- Gestion des erreurs robuste


## 🤖 Modèles utilisés

L'API utilise des modèles spécifiques de Hugging Face pour chaque langue :

| Langue | Modèle | Type | Description
|-----|-----|-----|-----
| Anglais (en) | [jonatasgrosman/wav2vec2-large-xlsr-53-english](https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-english) | Wav2Vec2 | Modèle Wav2Vec2 optimisé pour l'anglais
| Haoussa (ha) | [DrishtiSharma/whisper-large-v2-hausa](https://huggingface.co/DrishtiSharma/whisper-large-v2-hausa) | Whisper | Whisper Large V2 fine-tuné pour le haoussa
| Twi (tw) | [femursmith/intermediate-asr-ashanti-twi](https://huggingface.co/femursmith/intermediate-asr-ashanti-twi) | Wav2Vec2 | Modèle ASR spécialisé pour l'Ashanti Twi
| Ewe (ee) | [abiyo27/whisper-small-ewe](https://huggingface.co/abiyo27/whisper-small-ewe) | Whisper | Whisper Small fine-tuné pour l'ewe


## 📋 Prérequis

- Python 3.10 ou supérieur
- PyTorch 2.0 ou supérieur
- CUDA (recommandé pour les performances)
- 8 Go de RAM minimum (16 Go recommandés)
- Espace disque : au moins 10 Go pour les modèles


## 🚀 Installation

### Installation locale

1. Clonez le dépôt :


```shellscript
git clone https://github.com/votre-username/stt-api.git
cd stt-api
```

2. Créez un environnement virtuel :


```shellscript
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Installez les dépendances :


```shellscript
pip install -r requirements.txt
```

4. Lancez l'application :


```shellscript
uvicorn app:app --host 0.0.0.0 --port 9000 --reload
```

L'API sera accessible à l'adresse : [http://localhost:9000](http://localhost:9000)

### Installation des dépendances système (Linux)

Sur Ubuntu/Debian, installez les dépendances système nécessaires :

```shellscript
sudo apt-get update
sudo apt-get install -y \
    libsndfile1 \
    ffmpeg \
    libportaudio2 \
    build-essential
```

## 🐳 Déploiement avec Docker

### Utilisation de docker-compose

1. Assurez-vous que Docker et docker-compose sont installés sur votre système.
2. Construisez et démarrez les conteneurs :


```shellscript
docker-compose up -d
```

3. Vérifiez les logs :


```shellscript
docker-compose logs -f stt-api
```

### Utilisation du GPU (optionnel)

Pour utiliser le GPU avec Docker :

1. Assurez-vous que [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker) est installé.
2. Utilisez le fichier docker-compose.gpu.yml :


```shellscript
docker-compose -f docker-compose.gpu.yml up -d
```

### Commandes Docker utiles

```shellscript
# Arrêter les services
docker-compose down

# Reconstruire sans cache
docker-compose build --no-cache

# Entrer dans le conteneur
docker exec -it stt-promogo bash

# Voir l'utilisation des ressources
docker stats stt-promogo
```

## 📝 Utilisation de l'API

### Endpoints principaux

| Endpoint | Méthode | Description
|-----|-----|-----|-----
| `/` | GET | Informations sur l'API
| `/health` | GET | Vérification de l'état de l'API
| `/transcribe` | POST | Transcription audio en texte
| `/models` | GET | Liste des modèles disponibles
| `/languages` | GET | Liste des langues supportées
| `/debug` | GET | Informations de débogage


### Exemple de transcription avec curl

```shellscript
curl -X POST "http://localhost:9000/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@chemin/vers/votre/audio.wav" \
  -F "language=en"
```

### Exemple de transcription avec Python

```python
import requests

url = "http://localhost:9000/transcribe"
files = {"audio": open("audio.wav", "rb")}
data = {"language": "ha"}  # haoussa

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Transcription: {result['transcription']}")
print(f"Confiance: {result['confidence']}")
print(f"Temps de traitement: {result['processing_time']} secondes")
```

### Exemple de transcription avec JavaScript

```javascript
async function transcribeAudio(audioBlob, language = 'en') {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav");
    formData.append("language", language);

    const response = await fetch("http://localhost:9000/transcribe", {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`STT Error: ${response.status}`);
    }
    
    const data = await response.json();
    return data.transcription;
}
```

### Documentation interactive

Une documentation interactive Swagger UI est disponible à l'adresse :

```plaintext
http://localhost:9000/docs
```

## 📁 Structure du projet

```plaintext
stt-api/
├── app.py                  # Application FastAPI principale
├── requirements.txt        # Dépendances Python
├── Dockerfile              # Configuration Docker (CPU)
├── Dockerfile.gpu          # Configuration Docker (GPU)
├── docker-compose.yml      # Configuration docker-compose
├── docker-compose.gpu.yml  # Configuration docker-compose avec GPU
├── .dockerignore           # Fichiers à ignorer dans Docker
├── .env                    # Variables d'environnement
├── nginx.conf              # Configuration Nginx
├── start.sh                # Script de démarrage
├── models_cache/           # Cache pour les modèles téléchargés
└── logs/                   # Logs de l'application
```

## ⚙️ Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```plaintext
# Environment
ENVIRONMENT=production  # production ou development

# API Configuration
API_PORT=9000
API_WORKERS=1

# Model Configuration
PRELOAD_MODELS=false
MODEL_CACHE_DIR=/app/models_cache

# Resource Limits
MAX_MEMORY=8G
MAX_CPU=4

# Logging
LOG_LEVEL=info
```

### Configuration Nginx

Pour déployer l'API derrière Nginx, utilisez la configuration fournie dans `nginx.conf` :

```shellscript
# Copier la configuration
sudo cp nginx.conf /etc/nginx/sites-available/stt-promogo.souciance.com

# Créer un lien symbolique
sudo ln -s /etc/nginx/sites-available/stt-promogo.souciance.com /etc/nginx/sites-enabled/

# Vérifier la configuration
sudo nginx -t

# Redémarrer Nginx
sudo systemctl restart nginx
```

## ⚡ Optimisation des performances

### Utilisation du GPU

Pour des performances optimales, utilisez un GPU. L'API détecte automatiquement la disponibilité de CUDA.

### Quantification des modèles

Pour réduire l'utilisation de la mémoire, vous pouvez activer la quantification des modèles en modifiant `app.py` :

```python
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_compute_dtype=torch.float16
)

model = WhisperForConditionalGeneration.from_pretrained(
    model_id,
    quantization_config=quantization_config
)
```

### Chargement à la demande

Si vous avez des contraintes de mémoire, vous pouvez implémenter le chargement des modèles à la demande :

```python
def load_model_on_demand(language: str):
    """Load a model only when needed"""
    if language not in models:
        model_info = LANGUAGE_MODELS[language]
        load_model_for_language(language, model_info)
```

## 🔧 Dépannage

### Problèmes courants

| Problème | Solution
|-----|-----|-----|-----
| Erreur "CUDA out of memory" | Réduisez la taille des modèles ou utilisez la quantification
| Modèles lents à charger | Utilisez un volume persistant pour le cache des modèles
| Erreur "Failed to load model" | Vérifiez votre connexion internet et l'accès à Hugging Face
| Timeout lors des requêtes | Augmentez les timeouts dans Nginx et uvicorn


### Logs

Pour consulter les logs :

```shellscript
# Logs Docker
docker-compose logs -f stt-api

# Logs système (si déployé sans Docker)
journalctl -u stt-api.service -f
```

## ❓ FAQ

**Q: Combien de mémoire est nécessaire pour exécuter tous les modèles ?**R: Au moins 8 Go de RAM, mais 16 Go sont recommandés pour des performances optimales.

**Q: Puis-je ajouter d'autres langues ?**R: Oui, vous pouvez ajouter d'autres langues en modifiant le dictionnaire `LANGUAGE_MODELS` dans `app.py`.

**Q: L'API fonctionne-t-elle sans GPU ?**R: Oui, mais les performances seront considérablement réduites, surtout pour les modèles Whisper.

**Q: Comment puis-je optimiser l'API pour la production ?**R: Utilisez Gunicorn avec uvicorn workers, activez la quantification des modèles, et déployez derrière Nginx.

**Q: Quels formats audio sont supportés ?**R: WAV, MP3, FLAC, et OGG sont supportés. Le format WAV est recommandé pour de meilleurs résultats.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.