"""Video processing service using FFmpeg."""
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
import config


class VideoService:
    """Handles video processing operations."""
    
    @staticmethod
    def get_video_info(video_path: str) -> Optional[Dict[str, Any]]:
        """Get video metadata using FFprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extract relevant info
                video_stream = None
                audio_stream = None
                
                for stream in data.get("streams", []):
                    if stream.get("codec_type") == "video" and not video_stream:
                        video_stream = stream
                    elif stream.get("codec_type") == "audio" and not audio_stream:
                        audio_stream = stream
                
                format_info = data.get("format", {})
                
                return {
                    "duration": float(format_info.get("duration", 0)),
                    "size": int(format_info.get("size", 0)),
                    "bit_rate": int(format_info.get("bit_rate", 0)),
                    "format_name": format_info.get("format_name"),
                    "video": {
                        "codec": video_stream.get("codec_name") if video_stream else None,
                        "width": video_stream.get("width") if video_stream else None,
                        "height": video_stream.get("height") if video_stream else None,
                        "fps": eval(video_stream.get("r_frame_rate", "0/1")) if video_stream else None,
                    } if video_stream else None,
                    "audio": {
                        "codec": audio_stream.get("codec_name") if audio_stream else None,
                        "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else None,
                        "channels": audio_stream.get("channels") if audio_stream else None,
                    } if audio_stream else None
                }
            return None
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    @staticmethod
    def extract_audio(video_path: str, output_path: str, format: str = "wav") -> bool:
        """Extract audio from video file."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
                "-ar", "16000",  # 16kHz for Whisper
                "-ac", "1",  # Mono
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0 and Path(output_path).exists()
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return False
    
    @staticmethod
    def burn_subtitles(
        video_path: str,
        srt_path: str,
        output_path: str,
        font_size: int = 24,
        font_color: str = "white",
        outline_color: str = "black"
    ) -> bool:
        """Burn subtitles into video."""
        try:
            # Escape path for FFmpeg filter
            srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
            
            subtitle_filter = (
                f"subtitles='{srt_escaped}':"
                f"force_style='FontSize={font_size},"
                f"PrimaryColour=&H00FFFFFF,"
                f"OutlineColour=&H00000000,"
                f"BorderStyle=3,"
                f"Outline=2'"
            )
            
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", subtitle_filter,
                "-c:a", "copy",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=3600)
            return result.returncode == 0 and Path(output_path).exists()
        except Exception as e:
            print(f"Error burning subtitles: {e}")
            return False


video_service = VideoService()
