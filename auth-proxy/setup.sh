#!/bin/bash
# Auth Proxy Setup Script

set -e

echo "🚀 Setting up Authentication Proxy..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
else
    echo "✓ .env file already exists"
fi

# Check for service account file
if [ ! -f "service-account.json" ]; then
    echo ""
    echo "⚠️  WARNING: service-account.json not found"
    echo ""
    echo "To create a service account:"
    echo "  1. Go to Google Cloud Console"
    echo "  2. IAM & Admin > Service Accounts"
    echo "  3. Create new service account"
    echo "  4. Download JSON key as 'service-account.json'"
    echo ""
    echo "Or use gcloud:"
    echo "  gcloud iam service-accounts create a2a-proxy --project=YOUR_PROJECT_ID"
    echo "  gcloud iam service-accounts keys create service-account.json \\"
    echo "    --iam-account=a2a-proxy@YOUR_PROJECT_ID.iam.gserviceaccount.com"
    echo ""
else
    echo "✓ service-account.json found"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Ensure service-account.json is in this directory"
echo "  3. Run: python server.py"
echo ""
