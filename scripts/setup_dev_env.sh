#!/bin/bash

# PowerUp API Development Environment Setup Script
# This script sets up a complete development environment for the PowerUp API

set -e  # Exit on any error

echo "🚀 Setting up PowerUp API Development Environment..."

# Check if .env file exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created with default development settings"
    echo "⚠️  Please review .env file and update database credentials if needed"
else
    echo "✅ .env file already exists"
fi

# Install Python dependencies using uv
echo "📦 Installing Python dependencies..."
uv sync
echo "✅ Dependencies installed successfully"

# Run database migrations
echo "🗄️  Running database migrations..."
uv run alembic upgrade head
echo "✅ Database migrations completed"

# Seed pre-assessment data
echo "🌱 Seeding pre-assessment data..."
if [ -f scripts/seed_assessments.py ]; then
    uv run python scripts/seed_assessments.py
    echo "✅ Pre-assessment data seeded successfully"
else
    echo "⚠️  Warning: scripts/seed_assessments.py not found - you may need to create this file"
fi

echo ""
echo "🎉 Setup complete!"
echo "🚀 Run './run.sh' to start the server"
echo ""
echo "📋 Next steps:"
echo "   1. Review .env file for database configuration"
echo "   2. Run './run.sh' to start the development server"
echo "   3. Visit http://localhost:8000/docs for API documentation"
echo ""
