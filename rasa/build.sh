#!/bin/bash
set -e

echo "Setting up Python environment for Rasa..."

# Check Python version
python --version

# Install dependencies with specific versions to avoid conflicts
pip install --upgrade pip
pip install wheel setuptools

        # Try to install Rasa with specific constraint handling
        pip install --no-cache-dir rasa==3.1.0 rasa-sdk==3.1.1

# Install other requirements
pip install fastapi uvicorn openai>=1.0.0 requests>=2.31.0

# Train the Rasa model
echo "Training Rasa model..."
rasa train --force

echo "Build completed successfully!"
