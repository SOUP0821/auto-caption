"""
Build Script for AutoCaption Release
------------------------------------
This script automates the process of building the frontend and packaging the backend
into a standalone executable for Windows.

Requirements:
- Node.js & npm
- Python & pip
- PyInstaller (will be installed if missing)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
import time

# Configuration
BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"
BACKEND_DIR = BASE_DIR / "backend"
DIST_DIR = BASE_DIR / "dist_release"
BUILD_NAME = "AutoCaption"

def print_step(message):
    print(f"\n{'='*50}")
    print(f" {message}")
    print(f"{'='*50}\n")

def get_venv_python():
    venv_python = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        return sys.executable
    return str(venv_python)

def check_requirements():
    print_step("Checking Requirements")
    
    # Check Node
    try:
        subprocess.run(["node", "-v"], check=True, capture_output=True)
        print("[OK] Node.js detected")
    except:
        print("[ERROR] Node.js not found! Please install Node.js.")
        sys.exit(1)
        
    # Check PyInstaller in VENV
    python_exe = get_venv_python()
    print(f"Using Python: {python_exe}")
    
    try:
        subprocess.run([python_exe, "-m", "PyInstaller", "--version"], check=True, capture_output=True)
        print("[OK] PyInstaller detected in venv")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[WARN] PyInstaller not found in venv. Installing...")
        subprocess.run([python_exe, "-m", "pip", "install", "pyinstaller"], check=True)
        print("[OK] PyInstaller installed in venv")

def build_frontend():
    print_step("Building Frontend (React)")
    
    os.chdir(FRONTEND_DIR)
    
    # Install dependencies
    if not (FRONTEND_DIR / "node_modules").exists():
        print("Installing npm dependencies...")
        subprocess.run(["npm", "install"], check=True, shell=True)
    
    # Build
    print("Running npm build...")
    subprocess.run(["npm", "run", "build"], check=True, shell=True)
    
    # Verify build
    dist = FRONTEND_DIR / "dist"
    if not dist.exists():
        print("[ERROR] Frontend build failed: dist folder not found")
        sys.exit(1)
        
    print("[OK] Frontend built successfully")
    return dist

def clean_backend_static():
    static_dir = BACKEND_DIR / "static"
    if static_dir.exists():
        shutil.rmtree(static_dir)
    static_dir.mkdir()
    return static_dir

def copy_frontend_to_backend(frontend_dist, backend_static):
    print_step("Copying Frontend to Backend")
    
    # Copy all files from frontend/dist to backend/static
    for item in frontend_dist.iterdir():
        if item.is_dir():
            shutil.copytree(item, backend_static / item.name)
        else:
            shutil.copy2(item, backend_static / item.name)
            
    print(f"[OK] Copied frontend assets to {backend_static}")

def build_executable():
    print_step("Packaging Backend (PyInstaller)")
    
    os.chdir(BACKEND_DIR)
    
    # Clean previous builds
    shutil.rmtree(BACKEND_DIR / "build", ignore_errors=True)
    shutil.rmtree(BACKEND_DIR / "dist", ignore_errors=True)
    
    # Determine Python path
    python_exe = get_venv_python()
    print(f"[OK] Using python: {python_exe}")

    # PyInstaller arguments
    # We use --onedir data because --onefile is too slow to launch
    args = [
        python_exe, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", BUILD_NAME,
        "--onedir",            # Directory based bundle (faster startup)
        "--windowed",          # No console window (optional, use --console for debug)
        "--icon=NONE",         # TODO: Add an icon
        
        # Include static files (frontend)
        "--add-data", f"static{os.pathsep}static",
        
        # Include FFmpeg (if locally installed)
        "--add-data", f"ffmpeg{os.pathsep}ffmpeg",
        
        # Hidden imports often needed for uvicorn/fastapi/torch
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "engineio.async_drivers.aiohttp",
        
        # Main entry point
        "main.py"
    ]
    
    # Note on FFmpeg:
    # If ffmpeg is strictly local in backend/ffmpeg, verify it exists first
    if not (BACKEND_DIR / "ffmpeg").exists():
        print("[WARN] Warning: local 'ffmpeg' folder not found in backend. App might need system FFmpeg.")
        # Remove the add-data arg for ffmpeg if not present
        args = [a for a in args if "ffmpeg" not in a]
    
    print(f"Running: {' '.join(args)}")
    subprocess.run(args, check=True)
    
    # Verify Output
    dist_exe = BACKEND_DIR / "dist" / BUILD_NAME / f"{BUILD_NAME}.exe"
    if not dist_exe.exists():
        print("[ERROR] PyInstaller failed to create executable")
        sys.exit(1)
        
    print(f"[OK] Build successful: {dist_exe}")
    return BACKEND_DIR / "dist" / BUILD_NAME

def finalize_release(build_dir):
    print_step("Finalizing Release")
    
    # Move to root dist_release
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    
    shutil.copytree(build_dir, DIST_DIR)
    
    # Create a launcher batch file that sets env vars
    launcher_path = DIST_DIR / "Launch_AutoCaption.bat"
    with open(launcher_path, "w") as f:
        f.write('@echo off\n')
        f.write('set LAUNCH_BROWSER=1\n')
        f.write(f'start "" "{BUILD_NAME}.exe"\n')
    
    print(f"[OK] Release created at: {DIST_DIR}")
    print("You can zip this folder and share it!")

def main():
    check_requirements()
    
    frontend_dist = build_frontend()
    backend_static = clean_backend_static()
    
    copy_frontend_to_backend(frontend_dist, backend_static)
    
    build_dir = build_executable()
    
    finalize_release(build_dir)
    print_step("DONE!")

if __name__ == "__main__":
    main()
