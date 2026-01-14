"""Uninstall service for cleaning up the application."""
import shutil
import os
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional
import config


class UninstallService:
    """Handles application cleanup and uninstallation."""
    
    @staticmethod
    def get_storage_info() -> Dict[str, Any]:
        """Get information about what's installed and how much space it uses."""
        info = {
            "models": {"exists": False, "size_mb": 0, "path": str(config.MODELS_DIR)},
            "projects": {"exists": False, "size_mb": 0, "count": 0, "path": str(config.PROJECTS_DIR)},
            "venv": {"exists": False, "size_mb": 0, "path": str(config.BASE_DIR / "venv")},
            "cache": {"exists": False, "size_mb": 0, "paths": []},
            "total_size_mb": 0
        }
        
        # Check models directory
        if config.MODELS_DIR.exists():
            info["models"]["exists"] = True
            info["models"]["size_mb"] = UninstallService._get_dir_size_mb(config.MODELS_DIR)
        
        # Check projects directory
        if config.PROJECTS_DIR.exists():
            info["projects"]["exists"] = True
            info["projects"]["size_mb"] = UninstallService._get_dir_size_mb(config.PROJECTS_DIR)
            info["projects"]["count"] = len(list(config.PROJECTS_DIR.iterdir()))
        
        # Check virtual environment
        venv_path = config.BASE_DIR / "venv"
        if venv_path.exists():
            info["venv"]["exists"] = True
            info["venv"]["size_mb"] = UninstallService._get_dir_size_mb(venv_path)
        
        # Check HuggingFace cache
        hf_cache = Path.home() / ".cache" / "huggingface"
        if hf_cache.exists():
            info["cache"]["exists"] = True
            info["cache"]["paths"].append(str(hf_cache))
            # Only estimate, don't scan the whole cache
            info["cache"]["size_mb"] = "varies"
        
        # Total
        total = 0
        for key in ["models", "projects", "venv"]:
            if isinstance(info[key]["size_mb"], (int, float)):
                total += info[key]["size_mb"]
        info["total_size_mb"] = round(total, 2)
        
        return info
    
    @staticmethod
    def _get_dir_size_mb(path: Path) -> float:
        """Calculate directory size in MB."""
        total = 0
        try:
            for entry in path.rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return round(total / (1024 * 1024), 2)
    
    @staticmethod
    def delete_models() -> Dict[str, Any]:
        """Delete all downloaded AI models."""
        try:
            if config.MODELS_DIR.exists():
                size = UninstallService._get_dir_size_mb(config.MODELS_DIR)
                shutil.rmtree(config.MODELS_DIR)
                config.MODELS_DIR.mkdir(exist_ok=True)
                return {"success": True, "freed_mb": size, "message": "Models deleted"}
            return {"success": True, "freed_mb": 0, "message": "No models to delete"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_projects(keep_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """Delete all projects or specific ones."""
        try:
            if not config.PROJECTS_DIR.exists():
                return {"success": True, "deleted": 0, "message": "No projects to delete"}
            
            deleted = 0
            freed = 0
            
            for project_dir in config.PROJECTS_DIR.iterdir():
                if project_dir.is_dir():
                    if keep_list and project_dir.name in keep_list:
                        continue
                    freed += UninstallService._get_dir_size_mb(project_dir)
                    shutil.rmtree(project_dir)
                    deleted += 1
            
            return {
                "success": True, 
                "deleted": deleted, 
                "freed_mb": freed,
                "message": f"Deleted {deleted} projects, freed {freed:.1f} MB"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_venv() -> Dict[str, Any]:
        """Delete the Python virtual environment."""
        try:
            venv_path = config.BASE_DIR / "venv"
            if venv_path.exists():
                size = UninstallService._get_dir_size_mb(venv_path)
                shutil.rmtree(venv_path)
                return {
                    "success": True, 
                    "freed_mb": size,
                    "message": "Virtual environment deleted. You will need to reinstall to use the app."
                }
            return {"success": True, "freed_mb": 0, "message": "No virtual environment found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def clear_huggingface_cache() -> Dict[str, Any]:
        """Clear HuggingFace model cache."""
        try:
            hf_cache = Path.home() / ".cache" / "huggingface"
            
            # Only delete specific model folders
            whisper_cache = hf_cache / "hub" / "models--openai--whisper-large-v3-turbo"
            
            deleted = []
            freed = 0
            
            if whisper_cache.exists():
                freed += UninstallService._get_dir_size_mb(whisper_cache)
                shutil.rmtree(whisper_cache)
                deleted.append("whisper-large-v3-turbo")
            
            return {
                "success": True,
                "deleted": deleted,
                "freed_mb": freed,
                "message": f"Cleared {len(deleted)} cached models"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def full_uninstall(keep_projects: bool = False) -> Dict[str, Any]:
        """Perform full uninstallation."""
        results = {
            "models": None,
            "projects": None,
            "cache": None,
            "total_freed_mb": 0
        }
        
        # Delete models
        results["models"] = UninstallService.delete_models()
        if results["models"].get("freed_mb"):
            results["total_freed_mb"] += results["models"]["freed_mb"]
        
        # Delete projects (optional)
        if not keep_projects:
            results["projects"] = UninstallService.delete_projects()
            if results["projects"].get("freed_mb"):
                results["total_freed_mb"] += results["projects"]["freed_mb"]
        
        # Clear cache
        results["cache"] = UninstallService.clear_huggingface_cache()
        if results["cache"].get("freed_mb"):
            results["total_freed_mb"] += results["cache"]["freed_mb"]
        
        # Note: We don't delete venv automatically as the server is running from it
        results["note"] = "Virtual environment not deleted (app is running). Delete the 'venv' folder manually after closing the app."
        
        return results
    
    @staticmethod
    def generate_uninstall_script() -> Dict[str, Any]:
        """Generate platform-specific uninstall scripts."""
        base_dir = config.BASE_DIR
        
        if platform.system() == "Windows":
            script_content = f'''@echo off
echo AutoCaption Uninstaller
echo ========================
echo.
echo This will delete:
echo   - Virtual environment (venv)
echo   - Downloaded models
echo   - All projects and their data
echo.
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" exit /b

echo.
echo Stopping any running instances...
taskkill /f /im python.exe 2>nul

echo Deleting virtual environment...
rmdir /s /q "{base_dir}\\venv" 2>nul

echo Deleting models...
rmdir /s /q "{base_dir}\\models" 2>nul

echo Deleting projects...
rmdir /s /q "{base_dir}\\projects" 2>nul

echo Deleting FFmpeg...
rmdir /s /q "{base_dir}\\ffmpeg" 2>nul

echo.
echo Uninstall complete!
echo You can now delete the AutoCaption folder.
pause
'''
            script_path = base_dir / "uninstall.bat"
            
        else:  # macOS/Linux
            script_content = f'''#!/bin/bash
echo "AutoCaption Uninstaller"
echo "========================"
echo ""
echo "This will delete:"
echo "  - Virtual environment (venv)"
echo "  - Downloaded models"
echo "  - All projects and their data"
echo ""
read -p "Are you sure? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo "Stopping any running instances..."
pkill -f "python.*main.py" 2>/dev/null

echo "Deleting virtual environment..."
rm -rf "{base_dir}/venv"

echo "Deleting models..."
rm -rf "{base_dir}/models"

echo "Deleting projects..."
rm -rf "{base_dir}/projects"

echo ""
echo "Uninstall complete!"
echo "You can now delete the AutoCaption folder."
'''
            script_path = base_dir / "uninstall.sh"
        
        try:
            with open(script_path, 'w', newline='\n' if platform.system() != "Windows" else None) as f:
                f.write(script_content)
            
            # Make executable on Unix
            if platform.system() != "Windows":
                os.chmod(script_path, 0o755)
            
            return {
                "success": True,
                "path": str(script_path),
                "message": f"Uninstall script created: {script_path.name}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


    @staticmethod
    def perform_self_destruct() -> Dict[str, Any]:
        """Creates a temporary cleanup script and executes it to remove the app."""
        import tempfile
        import subprocess
        
        # Determine App Root (Parent of backend)
        app_root = config.BASE_DIR.parent
        
        if platform.system() == "Windows":
            try:
                # Create a bat file in temp
                temp_dir = Path(tempfile.gettempdir())
                script_path = temp_dir / "autocaption_nuke.bat"
                
                # Get current PID to kill specifically this process
                pid = os.getpid()
                
                # Script: Wait, Kill PID, Delete App Dir, Delete Self
                content = f'''@echo off
timeout /t 2 /nobreak >nul
taskkill /PID {pid} /F >nul
timeout /t 1 /nobreak >nul
rmdir /s /q "{app_root}"
del "%~f0"
'''
                with open(script_path, "w") as f:
                    f.write(content)
                    
                # Launch separate detached process
                subprocess.Popen(
                    ["cmd.exe", "/c", str(script_path)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                
                return {"success": True, "message": "Uninstall starting. App will close."}
            except Exception as e:
                return {"success": False, "error": str(e)}
            
        else:
            return {"success": False, "message": "One-click uninstall only supported on Windows."}


# Singleton instance
uninstall_service = UninstallService()
