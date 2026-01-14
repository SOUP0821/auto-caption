"""Project management service."""
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
from PIL import Image
import config


class ProjectService:
    """Handles project creation, storage, and retrieval."""
    
    def __init__(self):
        self.projects_file = config.PROJECTS_DIR / "projects.json"
        self._ensure_projects_file()
    
    def _ensure_projects_file(self):
        """Ensure projects.json exists."""
        if not self.projects_file.exists():
            self.projects_file.write_text("[]")
    
    def _load_projects(self) -> List[Dict[str, Any]]:
        """Load all projects from storage."""
        try:
            return json.loads(self.projects_file.read_text())
        except:
            return []
    
    def _save_projects(self, projects: List[Dict[str, Any]]):
        """Save projects to storage."""
        self.projects_file.write_text(json.dumps(projects, indent=2, default=str))
    
    def generate_thumbnail(self, video_path: str, output_path: str, time_position: float = 1.0) -> bool:
        """Generate a thumbnail from video using FFmpeg."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(time_position),
                "-i", video_path,
                "-vframes", "1",
                "-vf", "scale=320:-1",
                output_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
            
            # Verify thumbnail was created
            if Path(output_path).exists():
                return True
            return False
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")
            return False
    
    def generate_project_name(self, filename: str) -> str:
        """Generate a readable project name from filename."""
        # Remove extension and clean up
        name = Path(filename).stem
        # Replace underscores and dashes with spaces
        name = name.replace("_", " ").replace("-", " ")
        # Title case
        name = name.title()
        # Truncate if too long
        if len(name) > 50:
            name = name[:47] + "..."
        return name
    
    def create_project(
        self,
        video_path: str,
        original_filename: str
    ) -> Dict[str, Any]:
        """Create a new project from an uploaded video."""
        project_id = str(uuid.uuid4())
        project_dir = config.PROJECTS_DIR / project_id
        project_dir.mkdir(exist_ok=True)
        
        # Copy video to project directory
        video_ext = Path(original_filename).suffix
        project_video_path = project_dir / f"video{video_ext}"
        shutil.copy2(video_path, project_video_path)
        
        # Generate thumbnail
        thumbnail_path = project_dir / "thumbnail.jpg"
        thumbnail_generated = self.generate_thumbnail(
            str(project_video_path),
            str(thumbnail_path)
        )
        
        # Create project metadata
        project = {
            "id": project_id,
            "name": self.generate_project_name(original_filename),
            "original_filename": original_filename,
            "video_path": str(project_video_path),
            "thumbnail_path": str(thumbnail_path) if thumbnail_generated else None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "segments": [],
            "translated_segments": None,
            "source_language": None,
            "target_language": None,
            "whisper_model": None,
            "status": "created"
        }
        
        # Save project metadata
        (project_dir / "project.json").write_text(json.dumps(project, indent=2))
        
        # Add to projects list
        projects = self._load_projects()
        projects.insert(0, {
            "id": project_id,
            "name": project["name"],
            "thumbnail_path": project["thumbnail_path"],
            "created_at": project["created_at"],
            "status": project["status"]
        })
        self._save_projects(projects)
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a single project by ID."""
        project_file = config.PROJECTS_DIR / project_id / "project.json"
        if project_file.exists():
            return json.loads(project_file.read_text())
        return None
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a project."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        project.update(updates)
        project["updated_at"] = datetime.now().isoformat()
        
        project_file = config.PROJECTS_DIR / project_id / "project.json"
        project_file.write_text(json.dumps(project, indent=2))
        
        # Update projects list
        projects = self._load_projects()
        for i, p in enumerate(projects):
            if p["id"] == project_id:
                projects[i]["name"] = project.get("name", p["name"])
                projects[i]["status"] = project.get("status", p.get("status"))
                break
        self._save_projects(projects)
        
        return project
    
    def list_projects(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent projects."""
        projects = self._load_projects()
        return projects[:limit]
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and its files."""
        project_dir = config.PROJECTS_DIR / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir)
        
        projects = self._load_projects()
        projects = [p for p in projects if p["id"] != project_id]
        self._save_projects(projects)
        
        return True
    
    def save_segments(self, project_id: str, segments: List[Dict[str, Any]], translated: bool = False):
        """Save segments to project."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        if translated:
            project["translated_segments"] = segments
        else:
            project["segments"] = segments
        
        return self.update_project(project_id, project)
    
    def export_srt(self, project_id: str, use_translated: bool = False) -> Optional[str]:
        """Export segments as SRT content."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        segments = project.get("translated_segments") if use_translated else project.get("segments")
        if not segments:
            return None
        
        srt_content = ""
        for seg in segments:
            # Convert times to SRT format
            def to_srt_time(seconds: float) -> str:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
            
            srt_content += f"{seg['id']}\n"
            srt_content += f"{to_srt_time(seg['start'])} --> {to_srt_time(seg['end'])}\n"
            srt_content += f"{seg['text']}\n\n"
        
        return srt_content


    def open_project_folder(self, project_id: str) -> bool:
        """Open the project folder in file explorer."""
        project_dir = config.PROJECTS_DIR / project_id
        if not project_dir.exists():
            return False
            
        import platform
        import os
        import subprocess
        
        try:
            if platform.system() == "Windows":
                os.startfile(str(project_dir))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(project_dir)])
            else:
                subprocess.Popen(["xdg-open", str(project_dir)])
            return True
        except Exception as e:
            print(f"Failed to open folder: {e}")
            return False

    def save_srt_to_file(self, project_id: str, translated: bool = False) -> Optional[str]:
        """Save SRT content to a file in the project directory."""
        content = self.export_srt(project_id, translated)
        if not content:
            return None
            
        project = self.get_project(project_id)
        # Sanitization
        safe_name = "".join([c for c in project['name'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_name = safe_name.replace(" ", "_")
        
        lang_suffix = "_translated" if translated else ""
        if translated and project.get('target_language'):
            lang_suffix = f"_{project['target_language']}"
            
        filename = f"{safe_name}{lang_suffix}.srt"
        
        project_dir = config.PROJECTS_DIR / project_id
        file_path = project_dir / filename
        
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)


project_service = ProjectService()
