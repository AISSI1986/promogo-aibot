#!/bin/bash
set -e

echo "Setting up Python environment for Rasa..."

# Check Python version
python --version

# Install dependencies with specific versions to avoid conflicts
pip install --upgrade pip
pip install wheel setuptools

# Try to install Rasa with specific constraint handling
pip install --no-cache-dir rasa==2.8.34 rasa-sdk==2.8.34

# Install other requirements with compatible versions
pip install fastapi==0.68.0 uvicorn==0.15.0 openai==0.28.1 requests>=2.31.0

# Train the Rasa model
echo "Training Rasa model..."
rasa train --force

echo "Build completed successfully!"
