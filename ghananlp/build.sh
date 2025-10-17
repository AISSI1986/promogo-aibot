#!/bin/bash
set -e

echo "Setting up Python environment for GhanaNLP service..."

# Install dependencies
pip install --upgrade pip
pip install wheel setuptools

# Install requirements
pip install fastapi>=0.104.1 uvicorn>=0.24.0 requests>=2.31.0 pydantic>=2.5.0 python-multipart>=0.0.6

echo "Build completed successfully!"
