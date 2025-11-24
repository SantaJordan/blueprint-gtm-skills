#!/bin/bash
# Domain Resolver - Quick Setup Script

echo "=================================="
echo "Domain Resolver Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Check if Ollama is installed
echo "Checking for Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama found"

    # Check if model is installed
    echo "Checking for Qwen 2.5 14B model..."
    if ollama list | grep -q "qwen2.5:14b"; then
        echo "✓ Model already installed"
    else
        echo "Model not found. Installing qwen2.5:14b (this may take a few minutes)..."
        ollama pull qwen2.5:14b

        if [ $? -eq 0 ]; then
            echo "✓ Model installed successfully"
        else
            echo "⚠️  Failed to install model. You can install it later with: ollama pull qwen2.5:14b"
        fi
    fi
else
    echo "⚠️  Ollama not found"
    echo ""
    echo "Please install Ollama:"
    echo "  1. Visit: https://ollama.com"
    echo "  2. Download and install for your OS"
    echo "  3. Run: ollama pull qwen2.5:14b"
    echo ""
fi

# Create output directories
echo ""
echo "Creating output directories..."
mkdir -p output logs
echo "✓ Directories created"

# Check config
echo ""
echo "Checking configuration..."
if [ -f "config.yaml" ]; then
    if grep -q "e69a4729139f6830beb880fc9ce91b78d3021c64" config.yaml; then
        echo "✓ API keys configured"
    else
        echo "⚠️  API keys may not be configured. Please check config.yaml"
    fi
else
    echo "❌ config.yaml not found"
    exit 1
fi

echo ""
echo "=================================="
echo "✓ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Start Ollama server: ollama serve"
echo "  2. Run example: python domain_resolver.py example_input.csv"
echo "  3. Check results: cat output/resolved.csv"
echo ""
echo "For more help, see README.md"
echo ""
