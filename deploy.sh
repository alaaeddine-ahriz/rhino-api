#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting deployment process..."

# Update system packages
echo "📦 Updating system packages..."
brew update

# Install Python if not already installed
if ! command -v python3 &> /dev/null; then
    echo "🐍 Installing Python..."
    brew install python@3.11
fi

# Create and activate virtual environment
echo "🔧 Setting up virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories if they don't exist
echo "📁 Creating necessary directories..."
mkdir -p logs outputs static

# Set up environment variables
echo "⚙️ Setting up environment variables..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
PINECONE_API_KEY = pcsk_7XdePS_SLdpRTXFHGoMv7UxJq8v5rnugAv4PHYhSQqkAp3sLkLmTTG8yp4mSud2kxhASkJ
OPENAI_API_KEY = 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
EOL
    echo "⚠️ Please edit the .env file with your actual API keys and configuration"
fi

# Start the application
echo "🚀 Starting the application..."
uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload

# Note: The application will keep running until you stop it with Ctrl+C 