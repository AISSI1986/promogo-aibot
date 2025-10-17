#!/bin/bash
set -e

echo "Setting up Python environment for Rasa..."

# Check Python version
python --version

# Install dependencies with specific versions to avoid conflicts
pip install --upgrade pip
pip install wheel setuptools

# Try to install Rasa with specific constraint handling
pip install --no-cache-dir rasa==1.7.0 rasa-sdk==1.7.0

# Install other requirements
pip install fastapi uvicorn openai>=1.0.0 requests>=2.31.0

echo "Build completed successfully!"
