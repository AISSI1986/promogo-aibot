FROM node:16-alpine

WORKDIR /app

# Install serve globally
RUN npm install -g serve

COPY package*.json ./
RUN npm install

COPY . .

# Build the application
RUN npm run build

EXPOSE 3000

# Serve the built application
CMD ["serve", "-s", "build", "-l", "3000"]