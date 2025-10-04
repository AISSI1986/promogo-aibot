# Promogo Rasa Router

Un chatbot multilingue pour le marketplace Promogo, supportant l'anglais, le hausa, l'ewe, le twi et le dagbani.

## Prérequis

- Python 3.8 ou supérieur
- Docker et Docker Compose
- Git

## Installation

1. Cloner le repository :
```bash
git clone https://github.com/SOUCIANCE-CI/promogo_rasa_router.git
cd promogo_rasa_router
```

2. Créer un environnement virtuel Python :
```bash
python -m venv venv
source venv/bin/activate  # Sur Unix/macOS
# ou
.\venv\Scripts\activate  # Sur Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Configuration

1. Vérifier que le fichier `endpoints.yml` est correctement configuré :
```yaml
action_endpoint:
  url: "http://rasa-actions:5055/webhook"
```

2. Vérifier que le fichier `config.yml` contient les bonnes configurations pour le pipeline NLU et les politiques.

## Structure du Projet

```
promogo_rasa_router/
├── actions/
│   └── actions.py          # Actions personnalisées
├── data/
│   ├── nlu.yml            # Données d'entraînement NLU
│   ├── rules.yml          # Règles de conversation
│   └── stories.yml        # Histoires de conversation
├── config.yml             # Configuration du modèle
├── domain.yml            # Domaine du chatbot
├── endpoints.yml         # Configuration des endpoints
└── README.md            # Ce fichier
```

## Utilisation

### Entraînement du Modèle

Pour entraîner le modèle :

```bash
rasa train
```

### Test du Modèle

Pour tester le modèle :

```bash
rasa test
```

### Démarrage des Services

1. Démarrer le serveur d'actions :
```bash
rasa run actions
```

2. Dans un autre terminal, démarrer le serveur Rasa :
```bash
rasa run --enable-api
```

### Utilisation avec Docker

Pour démarrer tous les services avec Docker Compose :

```bash
docker-compose up
```

## API Endpoints

### Webhook

Le chatbot expose un endpoint webhook pour recevoir les messages :

```
POST /webhooks/rest/webhook
```

Format du message entrant :
```json
{
    "sender": "user_id",
    "message": {
        "language": "hausa",  // ou "english", "ewe", "twi", "dagbani"
        "text": "Medaase"     // le message dans la langue spécifiée
    }
}
```

Format de la réponse :
```json
{
    "recipient_id": "user_id",
    "custom": {
        "intent": "thank",
        "language": "ha",
        "confidence": 0.968,
        "response": "Ba komai! Akwai wani abu da zan iya taimaka maka?"
    }
}
```

## Langues Supportées

Le chatbot supporte les langues suivantes :
- Anglais (en)
- Hausa (ha)
- Ewe (ee)
- Twi (tw)
- Dagbani (dagbani)

## Développement

### Ajouter une Nouvelle Langue

1. Ajouter le code de langue dans le mapping de `ActionDetectLanguage`
2. Ajouter les réponses dans la langue dans `ActionMultilingualResponse`
3. Mettre à jour les données d'entraînement dans `data/nlu.yml`

### Ajouter un Nouvel Intent

1. Ajouter l'intent dans `domain.yml`
2. Ajouter les exemples dans `data/nlu.yml`
3. Ajouter les réponses dans toutes les langues dans `ActionMultilingualResponse`
4. Ajouter les règles ou histoires dans `data/rules.yml` ou `data/stories.yml`

## Dépannage

### Problèmes Courants

1. **Le serveur d'actions ne démarre pas**
   - Vérifier que le port 5055 est disponible
   - Vérifier que toutes les dépendances sont installées

2. **Erreurs de détection de langue**
   - Vérifier que le format du message JSON est correct
   - Vérifier que le code de langue est valide

3. **Erreurs d'entraînement**
   - Vérifier que les données d'entraînement sont valides
   - Vérifier que le domaine est correctement configuré

## Contribution

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Créer une Pull Request

## Licence

GPL-3.0