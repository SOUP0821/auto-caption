@echo off
setlocal enabledelayedexpansion
title AutoCaption Setup

echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                   AutoCaption Setup                       ║
echo  ║           Video Captioning ^& Translation App              ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

:: Check if we're in the right directory
if not exist "backend\main.py" (
    if not exist "backend" (
        echo [INFO] Creating project structure...
    ) else (
        echo [ERROR] Invalid directory. Please run from the AutoCaption folder.
        pause
        exit /b 1
    )
)

:: ============================================
:: Check Python
:: ============================================
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ┌─────────────────────────────────────────────────────────┐
    echo  │  Python is NOT installed!                               │
    echo  │                                                         │
    echo  │  Please install Python 3.10 or later from:              │
    echo  │  https://www.python.org/downloads/                      │
    echo  │                                                         │
    echo  │  Make sure to check "Add Python to PATH" during install │
    echo  └─────────────────────────────────────────────────────────┘
    echo.
    set /p OPEN_PYTHON="Open Python download page? (Y/N): "
    if /i "!OPEN_PYTHON!"=="Y" (
        start https://www.python.org/downloads/
    )
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo     Found Python %PYTHON_VER%

:: ============================================
:: Check Node.js
:: ============================================
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ┌─────────────────────────────────────────────────────────┐
    echo  │  Node.js is NOT installed!                              │
    echo  │                                                         │
    echo  │  Please install Node.js 18 or later from:               │
    echo  │  https://nodejs.org/                                    │
    echo  └─────────────────────────────────────────────────────────┘
    echo.
    set /p OPEN_NODE="Open Node.js download page? (Y/N): "
    if /i "!OPEN_NODE!"=="Y" (
        start https://nodejs.org/
    )
    pause
    exit /b 1
)
for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODE_VER=%%i
echo     Found Node.js %NODE_VER%

:: ============================================
:: Setup Backend
:: ============================================
echo [3/6] Setting up Backend...

if not exist "backend\venv" (
    echo     Creating Python virtual environment...
    cd backend
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    cd ..
)

:: Activate and install dependencies
echo     Installing Python dependencies...
cd backend
call venv\Scripts\activate.bat

:: Check if requirements are already installed
pip show fastapi >nul 2>&1
if errorlevel 1 (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies
        pause
        exit /b 1
    )
)
cd ..
echo     Backend dependencies ready

:: ============================================
:: Check for CUDA and offer GPU setup
:: ============================================
echo [4/6] Checking GPU Support...
cd backend
call venv\Scripts\activate.bat

:: Check if CUDA PyTorch is installed
python -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>nul > "%TEMP%\cuda_check.txt"
set /p CUDA_STATUS=<"%TEMP%\cuda_check.txt"
del "%TEMP%\cuda_check.txt" 2>nul

if "%CUDA_STATUS%"=="CUDA" (
    echo     GPU acceleration available!
) else (
    echo.
    echo  ┌─────────────────────────────────────────────────────────┐
    echo  │  GPU Acceleration NOT available                         │
    echo  │                                                         │
    echo  │  You have CPU-only PyTorch installed.                   │
    echo  │  For faster processing, install CUDA-enabled PyTorch.   │
    echo  │                                                         │
    echo  │  This requires an NVIDIA GPU with CUDA support.         │
    echo  └─────────────────────────────────────────────────────────┘
    echo.
    set /p INSTALL_CUDA="Install PyTorch with CUDA support? (Y/N): "
    if /i "!INSTALL_CUDA!"=="Y" (
        echo     Installing PyTorch with CUDA 12.1 support...
        echo     This may take several minutes...
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        if errorlevel 1 (
            echo [WARNING] CUDA installation failed. Continuing with CPU...
        ) else (
            echo     CUDA PyTorch installed successfully!
        )
    ) else (
        echo     Skipping CUDA installation. Using CPU mode.
    )
)
cd ..

:: ============================================
:: Setup Frontend
:: ============================================
echo [5/6] Setting up Frontend...

if not exist "frontend\node_modules" (
    echo     Installing Node.js dependencies...
    cd frontend
    npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies
        pause
        exit /b 1
    )
    cd ..
) else (
    echo     Frontend dependencies already installed
)

:: ============================================
:: Check FFmpeg
:: ============================================
echo [6/6] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    :: Check our local install
    if exist "backend\ffmpeg\bin\ffmpeg.exe" (
        echo     Found local FFmpeg installation
        set "PATH=%CD%\backend\ffmpeg\bin;%PATH%"
    ) else (
        echo.
        echo  ┌─────────────────────────────────────────────────────────┐
        echo  │  FFmpeg is NOT installed!                               │
        echo  │                                                         │
        echo  │  FFmpeg is required for video processing.               │
        echo  │                                                         │
        echo  │  You can install it now, or install it later via        │
        echo  │  the application's Installer page.                      │
        echo  └─────────────────────────────────────────────────────────┘
        echo.
        set /p INSTALL_FFMPEG="Download and install FFmpeg now? (Y/N): "
        if /i "!INSTALL_FFMPEG!"=="Y" (
            echo     Downloading FFmpeg...
            powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip' -OutFile 'backend\ffmpeg.zip'}"
            if exist "backend\ffmpeg.zip" (
                echo     Extracting FFmpeg...
                powershell -Command "& {Expand-Archive -Path 'backend\ffmpeg.zip' -DestinationPath 'backend\ffmpeg_temp' -Force}"
                mkdir "backend\ffmpeg\bin" 2>nul
                for /d %%D in (backend\ffmpeg_temp\ffmpeg*) do (
                    copy "%%D\bin\*.exe" "backend\ffmpeg\bin\" >nul
                )
                rmdir /s /q "backend\ffmpeg_temp" 2>nul
                del "backend\ffmpeg.zip" 2>nul
                set "PATH=%CD%\backend\ffmpeg\bin;%PATH%"
                echo     FFmpeg installed successfully!
            ) else (
                echo [WARNING] FFmpeg download failed. Install manually or via app.
            )
        ) else (
            echo     Skipping FFmpeg. You can install it via the app later.
        )
    )
) else (
    echo     FFmpeg found in system PATH
)

:: ============================================
:: All Done - Start Servers
:: ============================================
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                    Setup Complete!                        ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.
echo  Starting AutoCaption...
echo.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo.
echo  Press Ctrl+C to stop both servers.
echo.
echo ──────────────────────────────────────────────────────────────
echo.

:: Start backend in a new window
start "AutoCaption Backend" cmd /c "cd backend && call venv\Scripts\activate.bat && python main.py"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend in this window
cd frontend
npm run dev

endlocal
