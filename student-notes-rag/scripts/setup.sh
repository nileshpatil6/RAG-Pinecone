#!/bin/bash

echo "🚀 Setting up Student Notes RAG..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys"
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'make dev' to start development server"
echo "3. Visit http://localhost:8000/docs for API documentation"