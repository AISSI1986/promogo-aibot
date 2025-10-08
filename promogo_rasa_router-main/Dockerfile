FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    git \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for models
RUN mkdir -p models/embeddings

# Copy the rest of the application
COPY . .

EXPOSE 5005

# Create a non-root user and switch to it
RUN useradd -m -u 1000 rasa
RUN chown -R rasa:rasa /app
USER root

# Set environment variables
ENV PYTHONPATH=/app
ENV TF_CPP_MIN_LOG_LEVEL=2

# Command to run when the container starts
ENTRYPOINT ["rasa"]
CMD ["run", "--enable-api", "--cors", "*"]
