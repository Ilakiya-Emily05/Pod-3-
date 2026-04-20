# PowerUp API Development Environment Setup Script (PowerShell)
# This script sets up a complete development environment for the PowerUp API

Write-Host "🚀 Setting up PowerUp API Development Environment..." -ForegroundColor Green

# Check if .env file exists, if not copy from .env.example
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created with default development settings" -ForegroundColor Green
    Write-Host "⚠️  Please review .env file and update database credentials if needed" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Install Python dependencies using uv
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Blue
try {
    uv sync
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Run database migrations
Write-Host "🗄️  Running database migrations..." -ForegroundColor Blue
try {
    uv run alembic upgrade head
    Write-Host "✅ Database migrations completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to run database migrations" -ForegroundColor Red
    Write-Host "⚠️  Please ensure your database is running and configured in .env" -ForegroundColor Yellow
    exit 1
}

# Seed pre-assessment data
Write-Host "🌱 Seeding pre-assessment data..." -ForegroundColor Blue
if (Test-Path "scripts\seed_assessments.py") {
    try {
        uv run python scripts\seed_assessments.py
        Write-Host "✅ Pre-assessment data seeded successfully" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Warning: Failed to seed pre-assessment data" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Warning: scripts\seed_assessments.py not found - you may need to create this file" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host "🚀 Run '.\run.sh' to start the server" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Review .env file for database configuration"
Write-Host "   2. Run '.\run.sh' to start the development server"
Write-Host "   3. Visit http://localhost:8000/docs for API documentation"
Write-Host ""
