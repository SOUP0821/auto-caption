"""AutoCaption Backend - FastAPI Application."""
import os
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import aiofiles
import json

import config
from services.installer import installer_service
from services.projects import project_service
from services.transcribe import transcription_service
from services.translate import translation_service
from services.video import video_service
from services.hardware import hardware_service
from services.uninstall import uninstall_service

app = FastAPI(
    title="AutoCaption API",
    description="Video captioning and translation service",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve project thumbnails
app.mount("/thumbnails", StaticFiles(directory=str(config.PROJECTS_DIR)), name="thumbnails")


# ============== Models ==============

class TranscribeRequest(BaseModel):
    project_id: str
    model_size: str = "large-v3-turbo"
    language: Optional[str] = None

class TranslateRequest(BaseModel):
    project_id: str
    source_lang: str = "English"
    target_lang: str = "Spanish"

class UpdateSegmentRequest(BaseModel):
    project_id: str
    segment_id: int
    text: str
    is_translated: bool = False

class UpdateSegmentsRequest(BaseModel):
    project_id: str
    segments: List[dict]
    is_translated: bool = False


# ============== System Endpoints ==============

@app.get("/api/system/status")
async def get_system_status():
    """Check system dependencies and readiness."""
    status = installer_service.get_system_status()
    # Determine if system is ready
    status["ready"] = (
        status["ffmpeg"]["installed"] and
        (status["cuda"]["available"] or True)  # CPU is always available
    )
    return status

@app.post("/api/system/install-ffmpeg")
async def install_ffmpeg():
    """Download and install FFmpeg locally."""
    result = await installer_service.install_ffmpeg()
    return result

@app.post("/api/system/install-cuda")
async def install_cuda_pytorch():
    """Install PyTorch with CUDA support."""
    result = await installer_service.install_cuda_pytorch()
    return result

@app.post("/api/system/download-whisper")
async def download_whisper(model_size: str = "large-v3-turbo"):
    """Download Whisper model."""
    result = await installer_service.download_whisper_model(model_size)
    return result

@app.post("/api/system/download-translation")
async def download_translation():
    """Download translation model."""
    result = await installer_service.download_translation_model()
    return result


# ============== Hardware Detection ==============

@app.get("/api/hardware/status")
async def get_hardware_status():
    """Get comprehensive hardware status for cross-platform support."""
    return hardware_service.get_full_hardware_status()

@app.get("/api/hardware/gpus")
async def detect_gpus():
    """Detect available GPUs."""
    return hardware_service.detect_gpu()

@app.get("/api/hardware/recommended")
async def get_recommended_backend():
    """Get the recommended acceleration backend for this system."""
    return hardware_service.get_recommended_backend()

@app.post("/api/hardware/install-backend")
async def install_backend(backend: str):
    """Install a specific acceleration backend."""
    system = hardware_service.get_system_info()
    gpu_info = hardware_service.detect_gpu()
    
    commands = {
        "cuda": ["pip", "install", "torch", "torchvision", "torchaudio", 
                 "--index-url", "https://download.pytorch.org/whl/cu121", "--upgrade"],
        "mps": ["pip", "install", "torch", "torchvision", "torchaudio", "--upgrade"],
        "vulkan": ["pip", "install", "llama-cpp-python", 
                   "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/vulkan", "--upgrade"],
        "cpu": ["pip", "install", "torch", "torchvision", "torchaudio", "--upgrade"]
    }
    
    if backend not in commands:
        raise HTTPException(status_code=400, detail=f"Unknown backend: {backend}")
    
    try:
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m"] + commands[backend],
            capture_output=True, text=True, timeout=600
        )
        
        if result.returncode == 0:
            return {
                "success": True, 
                "backend": backend,
                "message": f"{backend.upper()} backend installed. Please restart the application."
            }
        else:
            return {
                "success": False, 
                "error": result.stderr[-500:] if result.stderr else "Unknown error"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============== Uninstall ==============

@app.get("/api/uninstall/info")
async def get_storage_info():
    """Get information about installed components and storage usage."""
    return uninstall_service.get_storage_info()

@app.delete("/api/uninstall/models")
async def delete_models():
    """Delete all downloaded AI models."""
    return uninstall_service.delete_models()

@app.delete("/api/uninstall/projects")
async def delete_all_projects():
    """Delete all projects."""
    return uninstall_service.delete_projects()

@app.delete("/api/uninstall/cache")
async def clear_cache():
    """Clear HuggingFace model cache."""
    return uninstall_service.clear_huggingface_cache()

@app.post("/api/uninstall/generate-script")
async def generate_uninstall_script():
    """Generate platform-specific uninstall script."""
    return uninstall_service.generate_uninstall_script()

@app.post("/api/uninstall/full")
async def full_uninstall(keep_projects: bool = False):
    """Perform full uninstallation (except venv which is running)."""
    return uninstall_service.full_uninstall(keep_projects=keep_projects)

@app.post("/api/uninstall/perform-self-destruct")
async def perform_self_destruct():
    """Immediately uninstall the application."""
    return uninstall_service.perform_self_destruct()

@app.get("/api/projects")
async def list_projects(limit: int = 20):
    """List recent projects."""
    return project_service.list_projects(limit)

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get a single project."""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    project_service.delete_project(project_id)
    return {"success": True}

@app.post("/api/projects/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file and create a new project."""
    # Save to temp
    temp_path = config.TEMP_DIR / file.filename
    
    async with aiofiles.open(temp_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Create project
    project = project_service.create_project(str(temp_path), file.filename)
    
    # Clean up temp
    temp_path.unlink(missing_ok=True)
    
    return project

@app.get("/api/projects/{project_id}/video")
async def get_project_video(project_id: str):
    """Serve project video file."""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    video_path = Path(project["video_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=project["original_filename"]
    )

@app.get("/api/projects/{project_id}/thumbnail")
async def get_project_thumbnail(project_id: str):
    """Serve project thumbnail."""
    project = project_service.get_project(project_id)
    if not project or not project.get("thumbnail_path"):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    thumbnail_path = Path(project["thumbnail_path"])
    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found")
    
    return FileResponse(thumbnail_path, media_type="image/jpeg")

@app.post("/api/projects/{project_id}/open-folder")
async def open_project_folder(project_id: str):
    """Open the project folder in file explorer."""
    success = project_service.open_project_folder(project_id)
    return {"success": success}

@app.post("/api/projects/{project_id}/save-srt")
async def save_project_srt(project_id: str, translated: bool = False):
    """Save SRT to disk in project folder."""
    path = project_service.save_srt_to_file(project_id, translated)
    if not path:
        return {"success": False, "error": "No processing data or invalid project"}
    return {"success": True, "path": path}


# ============== Transcription Endpoints ==============

# Store for SSE progress
transcription_progress = {}

@app.post("/api/transcribe")
async def start_transcription(request: TranscribeRequest, background_tasks: BackgroundTasks):
    """Start transcription job."""
    project = project_service.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Initialize progress
    transcription_progress[request.project_id] = {
        "status": "starting",
        "progress": 0,
        "segments": []
    }
    
    # Run transcription in background
    async def run_transcription():
        try:
            video_path = project["video_path"]
            
            for update in transcription_service.transcribe(
                video_path,
                model_size=request.model_size,
                language=request.language
            ):
                if update["type"] == "status":
                    transcription_progress[request.project_id]["status"] = update["message"]
                elif update["type"] == "segment":
                    transcription_progress[request.project_id]["progress"] = update["progress"]
                    transcription_progress[request.project_id]["segments"].append(update["segment"])
                elif update["type"] == "complete":
                    transcription_progress[request.project_id]["status"] = "complete"
                    transcription_progress[request.project_id]["progress"] = 100
                    # Save to project
                    project_service.update_project(request.project_id, {
                        "segments": update["segments"],
                        "whisper_model": request.model_size,
                        "status": "transcribed"
                    })
                    # Auto-save SRT to disk
                    project_service.save_srt_to_file(request.project_id, translated=False)
                elif update["type"] == "error":
                    transcription_progress[request.project_id]["status"] = f"error: {update['message']}"
        except Exception as e:
            transcription_progress[request.project_id]["status"] = f"error: {str(e)}"
    
    background_tasks.add_task(run_transcription)
    
    return {"message": "Transcription started", "project_id": request.project_id}

@app.get("/api/transcribe/{project_id}/progress")
async def get_transcription_progress(project_id: str):
    """Get transcription progress."""
    if project_id not in transcription_progress:
        # Check if project already has segments
        project = project_service.get_project(project_id)
        if project and project.get("segments"):
            return {
                "status": "complete",
                "progress": 100,
                "segments": project["segments"]
            }
        return {"status": "not_started", "progress": 0, "segments": []}
    
    return transcription_progress[project_id]


# ============== Translation Endpoints ==============

translation_progress = {}

@app.post("/api/translate")
async def start_translation(request: TranslateRequest, background_tasks: BackgroundTasks):
    """Start translation job."""
    project = project_service.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.get("segments"):
        raise HTTPException(status_code=400, detail="No segments to translate. Run transcription first.")
    
    # Initialize progress
    translation_progress[request.project_id] = {
        "status": "starting",
        "progress": 0,
        "current": 0,
        "total": len(project["segments"]),
        "segments": [],
        "remaining": None
    }
    
    async def run_translation():
        try:
            for update in translation_service.translate_segments(
                project["segments"],
                source_lang=request.source_lang,
                target_lang=request.target_lang
            ):
                if update["type"] == "status":
                    translation_progress[request.project_id]["status"] = update["message"]
                elif update["type"] == "segment":
                    translation_progress[request.project_id].update({
                        "progress": update["progress"],
                        "current": update["current"],
                        "remaining": update.get("remaining")
                    })
                    translation_progress[request.project_id]["segments"].append(update["segment"])
                elif update["type"] == "complete":
                    translation_progress[request.project_id]["status"] = "complete"
                    translation_progress[request.project_id]["progress"] = 100
                    # Save to project
                    project_service.update_project(request.project_id, {
                        "translated_segments": update["segments"],
                        "source_language": request.source_lang,
                        "target_language": request.target_lang,
                        "status": "translated"
                    })
                    # Auto-save SRT to disk
                    project_service.save_srt_to_file(request.project_id, translated=True)
                elif update["type"] == "error":
                    translation_progress[request.project_id]["status"] = f"error: {update['message']}"
        except Exception as e:
            translation_progress[request.project_id]["status"] = f"error: {str(e)}"
    
    background_tasks.add_task(run_translation)
    
    return {"message": "Translation started", "project_id": request.project_id}

@app.get("/api/translate/{project_id}/progress")
async def get_translation_progress(project_id: str):
    """Get translation progress."""
    if project_id not in translation_progress:
        project = project_service.get_project(project_id)
        if project and project.get("translated_segments"):
            return {
                "status": "complete",
                "progress": 100,
                "segments": project["translated_segments"]
            }
        return {"status": "not_started", "progress": 0, "segments": []}
    
    return translation_progress[project_id]


# ============== Segment Editing ==============

@app.put("/api/segments")
async def update_segment(request: UpdateSegmentRequest):
    """Update a single segment."""
    project = project_service.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    segments_key = "translated_segments" if request.is_translated else "segments"
    segments = project.get(segments_key, [])
    
    for seg in segments:
        if seg["id"] == request.segment_id:
            seg["text"] = request.text
            break
    
    project_service.update_project(request.project_id, {segments_key: segments})
    
    return {"success": True}

@app.put("/api/segments/bulk")
async def update_segments_bulk(request: UpdateSegmentsRequest):
    """Update all segments at once."""
    project = project_service.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    segments_key = "translated_segments" if request.is_translated else "segments"
    project_service.update_project(request.project_id, {segments_key: request.segments})
    
    return {"success": True}


# ============== Export ==============

@app.get("/api/projects/{project_id}/export/srt")
async def export_srt(project_id: str, translated: bool = False):
    """Export segments as SRT file."""
    srt_content = project_service.export_srt(project_id, use_translated=translated)
    if not srt_content:
        raise HTTPException(status_code=404, detail="No segments to export")
    
    return StreamingResponse(
        iter([srt_content]),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=subtitles{'_translated' if translated else ''}.srt"
        }
    )


# ============== Video Info ==============

@app.get("/api/projects/{project_id}/video-info")
async def get_video_info(project_id: str):
    """Get video metadata."""
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    info = video_service.get_video_info(project["video_path"])
    if not info:
        raise HTTPException(status_code=500, detail="Could not read video info")
    
    return info


# ============== Static Files (Frontend) ==============

# Serve React App in Production
# This must be after all API routes
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # In production/exe, we want to launch the browser automatically
    import webbrowser
    import threading
    
    def open_browser():
        webbrowser.open("http://localhost:8000")
        
    # Only open browser if not in reloader mode (proxied dev)
    # env var can be set by the exe launcher
    if os.environ.get("LAUNCH_BROWSER") == "1":
        threading.Timer(1.5, open_browser).start()
        
    uvicorn.run(app, host="0.0.0.0", port=8000)
