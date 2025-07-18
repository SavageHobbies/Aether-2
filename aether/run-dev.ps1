# Aether AI Companion - Development Server Script

Write-Host "Starting Aether AI Companion development server..." -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Please run setup-dev.ps1 first." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please configure your .env file before running the server." -ForegroundColor Yellow
}

# Start the development server
Write-Host "Starting development server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python -m aether.main
} catch {
    Write-Host "Failed to start server. Make sure all dependencies are installed." -ForegroundColor Red
    Write-Host "Run setup-dev.ps1 to install dependencies." -ForegroundColor Yellow
}