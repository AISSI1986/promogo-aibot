#!/bin/bash
set -e

echo "Setting up Python environment for GhanaNLP service..."

# Install dependencies
pip install --upgrade pip
pip install wheel setuptools

# Install requirements from requirements.txt
pip install -r requirements.txt

echo "Build completed successfully!"
