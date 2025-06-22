#!/bin/bash

# Gmail News Analyzer Setup Script
echo "🛠️ Setting up Gmail News Analyzer..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual credentials!"
    echo "   - Gmail credentials"
    echo "   - OpenAI API key"
    echo "   - Optional: Pushover and Notion credentials"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Set up Gmail App Password (see README for instructions)"
echo "3. Create Google Alerts for energy sector keywords"
echo "4. Run: python news_gpt_analyzer.py"
echo ""
echo "Optional integrations:"
echo "- Set up Pushover for mobile alerts"
echo "- Set up Notion database for logging"
