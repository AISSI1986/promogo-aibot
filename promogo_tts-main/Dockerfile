FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt before installing dependencies
COPY requirements.txt .

# Install specific versions of dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create a directory for model caching
RUN mkdir -p /root/.cache/huggingface

# Expose the port the app runs on
EXPOSE 5007

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5007"]
