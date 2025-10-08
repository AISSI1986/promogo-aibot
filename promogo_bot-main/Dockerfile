# Utiliser une image de base Node.js
FROM node:16-alpine

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances
COPY package*.json ./
RUN npm install

# Copier le reste des fichiers de l'application
COPY . .

# Construire l'application (si nécessaire)
# RUN npm run build

# Exposer le port sur lequel l'application va tourner
EXPOSE 3000

# Démarrer l'application
CMD ["npm", "start"] 