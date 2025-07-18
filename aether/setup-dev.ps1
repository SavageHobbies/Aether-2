# Aether AI Companion - Windows Development Setup Script

Write-Host "Setting up Aether AI Companion development environment..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.9+ first." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies (Windows-compatible)
Write-Host "Installing dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements-windows.txt") {
    pip install -r requirements-windows.txt
} else {
    pip install -r requirements.txt
}

# Install development dependencies
Write-Host "Installing development dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Copy environment file
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
} else {
    Write-Host ".env file already exists, skipping..." -ForegroundColor Yellow
}

# Create data directory
$dataDir = "$env:USERPROFILE\.aether"
if (-not (Test-Path $dataDir)) {
    Write-Host "Creating data directory: $dataDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $dataDir -Force
    New-Item -ItemType Directory -Path "$dataDir\logs" -Force
}

Write-Host "Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Activate the virtual environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Configure your .env file with your settings" -ForegroundColor White
Write-Host "3. Run the application: python -m aether.main" -ForegroundColor White
Write-Host ""
Write-Host "Or use the run-dev.ps1 script to start the development server" -ForegroundColor White