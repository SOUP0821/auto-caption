"""Installer service - checks and installs dependencies."""
import subprocess
import shutil
import sys
import os
import platform
import zipfile
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from huggingface_hub import hf_hub_download, snapshot_download
import config

class InstallerService:
    """Handles dependency checking and model downloads."""
    
    @staticmethod
    def check_ffmpeg() -> Dict[str, Any]:
        """Check if FFmpeg is installed and accessible."""
        ffmpeg_path = shutil.which("ffmpeg")
        ffprobe_path = shutil.which("ffprobe")
        
        # Also check our local install
        local_ffmpeg = config.BASE_DIR / "ffmpeg" / "bin" / "ffmpeg.exe"
        if local_ffmpeg.exists():
            ffmpeg_path = str(local_ffmpeg)
            # Add to PATH for this session
            os.environ["PATH"] = str(local_ffmpeg.parent) + os.pathsep + os.environ.get("PATH", "")
        
        if ffmpeg_path:
            try:
                result = subprocess.run(
                    [ffmpeg_path, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown"
                return {
                    "installed": True,
                    "path": ffmpeg_path,
                    "version": version_line
                }
            except Exception as e:
                return {"installed": False, "error": str(e)}
        
        return {"installed": False, "error": "FFmpeg not found in PATH"}
    
    @staticmethod
    def check_cuda() -> Dict[str, Any]:
        """Check if CUDA is available with detailed info."""
        try:
            import torch
            
            # Force CUDA check
            cuda_available = torch.cuda.is_available()
            
            if cuda_available:
                device_count = torch.cuda.device_count()
                devices = []
                for i in range(device_count):
                    props = torch.cuda.get_device_properties(i)
                    devices.append({
                        "index": i,
                        "name": props.name,
                        "total_memory_gb": round(props.total_memory / (1024**3), 2),
                        "compute_capability": f"{props.major}.{props.minor}"
                    })
                
                return {
                    "available": True,
                    "device_count": device_count,
                    "devices": devices,
                    "device_name": devices[0]["name"] if devices else None,
                    "cuda_version": torch.version.cuda,
                    "cudnn_version": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
                    "torch_version": torch.__version__
                }
            else:
                # Check why CUDA isn't available
                reason = "Unknown reason"
                if not hasattr(torch, 'cuda'):
                    reason = "PyTorch installed without CUDA support"
                elif hasattr(torch.cuda, '_is_compiled') and not torch.cuda._is_compiled():
                    reason = "PyTorch not compiled with CUDA"
                else:
                    reason = "CUDA drivers not found or incompatible"
                
                return {
                    "available": False, 
                    "message": f"CUDA not available: {reason}",
                    "torch_version": torch.__version__,
                    "suggestion": "Install PyTorch with CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
                }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    @staticmethod
    def check_whisper_model() -> Dict[str, Any]:
        """Check if Whisper model is downloaded."""
        try:
            from huggingface_hub import model_info
            model_id = "openai/whisper-large-v3-turbo"
            info = model_info(model_id)
            return {
                "available": True,
                "model_id": model_id,
                "message": "Whisper Large V3 Turbo accessible"
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    @staticmethod
    def check_translation_model() -> Dict[str, Any]:
        """Check if GGUF translation model exists locally."""
        gguf_path = config.MODELS_DIR / "hunyuan-mt-chimera-7b-q4_k_m.gguf"
        if gguf_path.exists():
            size_gb = gguf_path.stat().st_size / (1024**3)
            return {
                "available": True,
                "path": str(gguf_path),
                "size_gb": round(size_gb, 2),
                "message": "Hunyuan MT Chimera GGUF ready"
            }
        
        # Check if model is accessible on HuggingFace
        try:
            from huggingface_hub import model_info
            info = model_info("mradermacher/Huihui-Hunyuan-MT-Chimera-7B-abliterated-GGUF")
            return {
                "available": False,
                "downloadable": True,
                "message": "Model available for download (~4.4GB)"
            }
        except:
            return {"available": False, "downloadable": False, "error": "Model not accessible"}
    
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """Get complete system status."""
        ffmpeg_status = InstallerService.check_ffmpeg()
        cuda_status = InstallerService.check_cuda()
        whisper_status = InstallerService.check_whisper_model()
        translation_status = InstallerService.check_translation_model()
        
        # System is ready if FFmpeg is installed (GPU optional, models download on first use)
        ready = ffmpeg_status["installed"]
        
        return {
            "ffmpeg": ffmpeg_status,
            "cuda": cuda_status,
            "whisper": whisper_status,
            "translation": translation_status,
            "python_version": sys.version,
            "platform": platform.system(),
            "ready": ready
        }
    
    @staticmethod
    async def install_ffmpeg(progress_callback=None) -> Dict[str, Any]:
        """Download and install FFmpeg locally."""
        try:
            if platform.system() != "Windows":
                return {
                    "success": False, 
                    "error": "Auto-install only supported on Windows. Please install FFmpeg manually."
                }
            
            ffmpeg_dir = config.BASE_DIR / "ffmpeg"
            ffmpeg_dir.mkdir(exist_ok=True)
            
            # Download FFmpeg from GitHub releases (gyan.dev builds)
            url = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
            zip_path = ffmpeg_dir / "ffmpeg.zip"
            
            if progress_callback:
                progress_callback({"status": "Downloading FFmpeg...", "progress": 0})
            
            # Download with progress
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size:
                        progress_callback({
                            "status": "Downloading FFmpeg...",
                            "progress": int(downloaded / total_size * 50)
                        })
            
            if progress_callback:
                progress_callback({"status": "Extracting FFmpeg...", "progress": 50})
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(ffmpeg_dir)
            
            # Find the bin folder
            for item in ffmpeg_dir.iterdir():
                if item.is_dir() and "ffmpeg" in item.name.lower():
                    bin_dir = item / "bin"
                    if bin_dir.exists():
                        # Move bin contents to ffmpeg/bin
                        target_bin = ffmpeg_dir / "bin"
                        target_bin.mkdir(exist_ok=True)
                        for exe in bin_dir.glob("*.exe"):
                            shutil.copy2(exe, target_bin / exe.name)
                        break
            
            # Clean up
            zip_path.unlink(missing_ok=True)
            
            # Add to PATH for this session
            bin_path = ffmpeg_dir / "bin"
            os.environ["PATH"] = str(bin_path) + os.pathsep + os.environ.get("PATH", "")
            
            if progress_callback:
                progress_callback({"status": "FFmpeg installed!", "progress": 100})
            
            return {
                "success": True,
                "message": "FFmpeg installed successfully",
                "path": str(bin_path)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def install_cuda_pytorch(progress_callback=None) -> Dict[str, Any]:
        """Install PyTorch with CUDA support."""
        try:
            if progress_callback:
                progress_callback({"status": "Installing PyTorch with CUDA...", "progress": 0})
            
            # Run pip install in subprocess
            cmd = [
                sys.executable, "-m", "pip", "install", 
                "torch", "torchvision", "torchaudio",
                "--index-url", "https://download.pytorch.org/whl/cu121",
                "--upgrade"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            output_lines = []
            for line in process.stdout:
                output_lines.append(line.strip())
                if progress_callback:
                    # Estimate progress from output
                    if "Downloading" in line:
                        progress_callback({"status": "Downloading PyTorch...", "progress": 30})
                    elif "Installing" in line:
                        progress_callback({"status": "Installing PyTorch...", "progress": 70})
            
            process.wait()
            
            if process.returncode == 0:
                if progress_callback:
                    progress_callback({"status": "PyTorch with CUDA installed!", "progress": 100})
                return {
                    "success": True,
                    "message": "PyTorch with CUDA installed. Please restart the application."
                }
            else:
                return {
                    "success": False,
                    "error": "Installation failed",
                    "output": "\n".join(output_lines[-10:])
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def download_whisper_model(model_size: str = "large-v3-turbo", progress_callback=None) -> Dict[str, Any]:
        """Pre-download Whisper model."""
        try:
            if progress_callback:
                progress_callback({"status": "Downloading Whisper model...", "progress": 0})
            
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
            
            model_id = f"openai/whisper-{model_size}"
            
            if progress_callback:
                progress_callback({"status": "Loading model files...", "progress": 30})
            
            # This downloads the model to cache
            processor = AutoProcessor.from_pretrained(model_id)
            
            if progress_callback:
                progress_callback({"status": "Downloading model weights...", "progress": 50})
            
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id,
                low_cpu_mem_usage=True,
                use_safetensors=True
            )
            
            del model
            del processor
            
            if progress_callback:
                progress_callback({"status": "Whisper model ready!", "progress": 100})
            
            return {"success": True, "message": f"Whisper {model_size} downloaded"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def download_translation_model(progress_callback=None) -> Dict[str, Any]:
        """Download the GGUF translation model."""
        try:
            config.MODELS_DIR.mkdir(exist_ok=True)
            gguf_path = config.MODELS_DIR / "hunyuan-mt-chimera-7b-q4_k_m.gguf"
            
            if gguf_path.exists():
                return {"success": True, "message": "Model already downloaded"}
            
            if progress_callback:
                progress_callback({"status": "Downloading translation model (~4.4GB)...", "progress": 0})
            
            # Download from HuggingFace
            downloaded_path = hf_hub_download(
                repo_id="mradermacher/Huihui-Hunyuan-MT-Chimera-7B-abliterated-GGUF",
                filename="Huihui-Hunyuan-MT-Chimera-7B-abliterated.Q4_K_M.gguf",
                local_dir=config.MODELS_DIR,
                local_dir_use_symlinks=False
            )
            
            # Rename for consistency
            Path(downloaded_path).rename(gguf_path)
            
            if progress_callback:
                progress_callback({"status": "Translation model ready!", "progress": 100})
            
            return {"success": True, "message": "Translation model downloaded", "path": str(gguf_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}


installer_service = InstallerService()
