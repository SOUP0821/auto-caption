# AutoCaption Setup Script
# Run with: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"

# Colors
function Write-Title { Write-Host "`n$args`n" -ForegroundColor Cyan }
function Write-Step { Write-Host "[*] $args" -ForegroundColor Yellow }
function Write-Success { Write-Host "[✓] $args" -ForegroundColor Green }
function Write-Error { Write-Host "[✗] $args" -ForegroundColor Red }
function Write-Info { Write-Host "    $args" -ForegroundColor Gray }

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║                   AutoCaption Setup                       ║" -ForegroundColor Cyan
Write-Host "  ║           Video Captioning & Translation App              ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# ============================================
# Check Python
# ============================================
Write-Step "Checking Python..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Found $pythonVersion"
} catch {
    Write-Error "Python is NOT installed!"
    Write-Host ""
    Write-Host "  Please install Python 3.10 or later from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
    Write-Host ""
    $response = Read-Host "Open Python download page? (Y/N)"
    if ($response -eq "Y") {
        Start-Process "https://www.python.org/downloads/"
    }
    exit 1
}

# ============================================
# Check Node.js
# ============================================
Write-Step "Checking Node.js..."
try {
    $nodeVersion = node --version 2>&1
    Write-Success "Found Node.js $nodeVersion"
} catch {
    Write-Error "Node.js is NOT installed!"
    Write-Host ""
    Write-Host "  Please install Node.js 18 or later from:" -ForegroundColor Yellow
    Write-Host "  https://nodejs.org/" -ForegroundColor White
    Write-Host ""
    $response = Read-Host "Open Node.js download page? (Y/N)"
    if ($response -eq "Y") {
        Start-Process "https://nodejs.org/"
    }
    exit 1
}

# ============================================
# Setup Backend
# ============================================
Write-Step "Setting up Backend..."

if (-not (Test-Path "backend\venv")) {
    Write-Info "Creating Python virtual environment..."
    Push-Location backend
    python -m venv venv
    Pop-Location
}

# Install dependencies
Write-Info "Installing Python dependencies..."
Push-Location backend
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt --quiet
Pop-Location
Write-Success "Backend dependencies installed"

# ============================================
# Check for CUDA
# ============================================
Write-Step "Checking GPU Support..."
Push-Location backend
& .\venv\Scripts\Activate.ps1

$cudaCheck = python -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>$null
Pop-Location

if ($cudaCheck -eq "CUDA") {
    Write-Success "GPU acceleration available!"
} else {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host "  │  GPU Acceleration NOT available                         │" -ForegroundColor Yellow
    Write-Host "  │                                                         │" -ForegroundColor Yellow
    Write-Host "  │  You have CPU-only PyTorch installed.                   │" -ForegroundColor Yellow
    Write-Host "  │  For faster processing, install CUDA-enabled PyTorch.   │" -ForegroundColor Yellow
    Write-Host "  │                                                         │" -ForegroundColor Yellow
    Write-Host "  │  This requires an NVIDIA GPU with CUDA support.         │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Install PyTorch with CUDA support? (Y/N)"
    if ($response -eq "Y") {
        Write-Info "Installing PyTorch with CUDA 12.1 support..."
        Write-Info "This may take several minutes..."
        Push-Location backend
        & .\venv\Scripts\Activate.ps1
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        Pop-Location
        Write-Success "CUDA PyTorch installed!"
    } else {
        Write-Info "Skipping CUDA installation. Using CPU mode."
    }
}

# ============================================
# Setup Frontend
# ============================================
Write-Step "Setting up Frontend..."

if (-not (Test-Path "frontend\node_modules")) {
    Write-Info "Installing Node.js dependencies..."
    Push-Location frontend
    npm install
    Pop-Location
}
Write-Success "Frontend dependencies installed"

# ============================================
# Check FFmpeg
# ============================================
Write-Step "Checking FFmpeg..."

$ffmpegFound = $false
try {
    ffmpeg -version 2>&1 | Out-Null
    $ffmpegFound = $true
    Write-Success "FFmpeg found in system PATH"
} catch {
    if (Test-Path "backend\ffmpeg\bin\ffmpeg.exe") {
        $ffmpegFound = $true
        $env:PATH = "$scriptDir\backend\ffmpeg\bin;$env:PATH"
        Write-Success "Found local FFmpeg installation"
    }
}

if (-not $ffmpegFound) {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host "  │  FFmpeg is NOT installed!                               │" -ForegroundColor Yellow
    Write-Host "  │                                                         │" -ForegroundColor Yellow
    Write-Host "  │  FFmpeg is required for video processing.               │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Download and install FFmpeg now? (Y/N)"
    if ($response -eq "Y") {
        Write-Info "Downloading FFmpeg (~85MB)..."
        $ffmpegUrl = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
        $zipPath = "backend\ffmpeg.zip"
        
        Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipPath -UseBasicParsing
        
        Write-Info "Extracting FFmpeg..."
        Expand-Archive -Path $zipPath -DestinationPath "backend\ffmpeg_temp" -Force
        
        New-Item -ItemType Directory -Path "backend\ffmpeg\bin" -Force | Out-Null
        Get-ChildItem "backend\ffmpeg_temp\ffmpeg*\bin\*.exe" | Copy-Item -Destination "backend\ffmpeg\bin\"
        
        Remove-Item "backend\ffmpeg_temp" -Recurse -Force
        Remove-Item $zipPath -Force
        
        $env:PATH = "$scriptDir\backend\ffmpeg\bin;$env:PATH"
        Write-Success "FFmpeg installed successfully!"
    } else {
        Write-Info "Skipping FFmpeg. You can install it via the app later."
    }
}

# ============================================
# All Done
# ============================================
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║                    Setup Complete!                        ║" -ForegroundColor Green
Write-Host "  ╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  To start AutoCaption, run: " -NoNewline
Write-Host ".\start.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Or start manually:" -ForegroundColor Gray
Write-Host "    Terminal 1: cd backend && venv\Scripts\activate && python main.py" -ForegroundColor Gray
Write-Host "    Terminal 2: cd frontend && npm run dev" -ForegroundColor Gray
Write-Host ""

$response = Read-Host "Start AutoCaption now? (Y/N)"
if ($response -eq "Y") {
    # Start backend
    Start-Process cmd -ArgumentList "/c cd backend && call venv\Scripts\activate.bat && python main.py" -WindowStyle Normal
    
    Start-Sleep -Seconds 3
    
    # Start frontend
    Push-Location frontend
    npm run dev
}
