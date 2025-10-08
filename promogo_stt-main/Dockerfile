FROM python:3.8-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    ffmpeg \
    cmake \
    libboost-all-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Créer un répertoire de cache avec les bonnes permissions
RUN mkdir -p /app/models_cache && chmod 777 /app/models_cache

# Définir la variable d'environnement pour le cache
ENV TRANSFORMERS_CACHE=/app/models_cache
ENV HF_HOME=/app/models_cache
ENV MODELS_CACHE_DIR=/app/models_cache

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer kenlm depuis GitHub
RUN pip install https://github.com/kpu/kenlm/archive/master.zip

# Copier le code de l'application
COPY . .

# Exposer le port
EXPOSE 5006

# Commande par défaut
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5006"]