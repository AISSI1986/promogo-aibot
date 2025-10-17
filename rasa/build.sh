#!/bin/bash
set -e

echo "Setting up Python environment for Rasa..."

# Install dependencies with specific versions to avoid conflicts
pip install --upgrade pip
pip install wheel setuptools

# Install Rasa and dependencies with specific versions
pip install rasa==1.10.2 rasa-sdk==1.10.2

# Install other requirements
pip install fastapi uvicorn openai>=1.0.0 requests>=2.31.0

echo "Build completed successfully!"
