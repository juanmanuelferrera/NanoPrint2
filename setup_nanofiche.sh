#!/bin/bash

# Setup script for NanoFiche Image Prep

echo "Setting up NanoFiche Image Prep..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv nanofiche_env

# Activate virtual environment
echo "Activating virtual environment..."
source nanofiche_env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the application:"
echo "  source nanofiche_env/bin/activate"
echo "  python nanofiche_image_prep.py"
echo ""
echo "To deactivate the virtual environment when done:"
echo "  deactivate"