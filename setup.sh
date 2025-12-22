#!/bin/bash
# Setup script for Javadoc AI Automation

set -e

echo "======================================"
echo "Javadoc AI Automation - Setup Script"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python version: $PYTHON_VERSION"

# Check Git
echo "Checking Git installation..."
if ! command -v git &> /dev/null; then
    echo "Error: Git is not installed. Please install Git."
    exit 1
fi
echo "Git is installed: $(git --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
else
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy config template if config doesn't exist
echo ""
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from template..."
    cp config.yaml.template config.yaml
    echo "Config file created. Please edit config.yaml with your settings."
else
    echo "config.yaml already exists. Skipping."
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your GitLab, LLM, and email settings"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the automation: python javadoc_automation.py"
echo ""
echo "To schedule nightly runs, add to crontab:"
echo "0 2 * * * cd $(pwd) && $(pwd)/venv/bin/python javadoc_automation.py >> $(pwd)/javadoc_automation.log 2>&1"
echo ""
