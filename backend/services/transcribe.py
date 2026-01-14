"""Transcription service using HuggingFace Transformers Whisper."""
import time
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
from dataclasses import dataclass, asdict
import torch
import config

@dataclass
class SubtitleSegment:
    """Represents a single subtitle segment."""
    id: int
    start: float
    end: float
    text: str
    
    def to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def to_srt(self) -> str:
        """Convert segment to SRT format."""
        return f"{self.id}\n{self.to_srt_time(self.start)} --> {self.to_srt_time(self.end)}\n{self.text}\n"


class TranscriptionService:
    """Handles audio/video transcription using Whisper via Transformers."""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.pipe = None
        self.current_model_id = None
        
        # Auto-detect best device
        if torch.cuda.is_available():
            self.device = "cuda:0"
            self.torch_dtype = torch.float16
            print("Using CUDA (NVIDIA) for transcription")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
            self.torch_dtype = torch.float16
            print("Using MPS (Apple Silicon) for transcription")
        else:
            self.device = "cpu"
            self.torch_dtype = torch.float32
            print("Using CPU for transcription")
    
    def load_model(self, model_size: str = "large-v3-turbo"):
        """Load or switch Whisper model using Transformers."""
        model_id = f"openai/whisper-{model_size}"
        
        if self.pipe is not None and self.current_model_id == model_id:
            return  # Model already loaded
        
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
        
        # Unload previous model
        if self.model is not None:
            del self.model
            del self.processor
            del self.pipe
            self.model = None
            self.processor = None
            self.pipe = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        print(f"Loading Whisper model: {model_id}")
        print(f"Device: {self.device}, dtype: {self.torch_dtype}")
        
        # Load model
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=self.torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        )
        self.model.to(self.device)
        
        # Load processor
        self.processor = AutoProcessor.from_pretrained(model_id)
        
        # Create pipeline with chunking for long audio
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            chunk_length_s=30,
            batch_size=16 if torch.cuda.is_available() else 4,
            torch_dtype=self.torch_dtype,
            device=self.device,
        )
        
        self.current_model_id = model_id
        print(f"Model loaded successfully")
    
    def transcribe(
        self,
        audio_path: str,
        model_size: str = "large-v3-turbo",
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Transcribe audio file and yield progress updates.
        
        Args:
            audio_path: Path to audio/video file
            model_size: Whisper model size to use
            language: Source language code (auto-detect if None)
            task: 'transcribe' or 'translate' (to English)
        
        Yields:
            Progress updates and final segments
        """
        start_time = time.time()
        
        yield {"type": "status", "message": f"Loading Whisper {model_size} model..."}
        
        try:
            self.load_model(model_size)
        except Exception as e:
            yield {"type": "error", "message": f"Failed to load model: {str(e)}"}
            return
        
        yield {"type": "status", "message": "Transcribing audio..."}
        
        try:
            # Prepare generate kwargs
            generate_kwargs = {
                "task": task,
                "return_timestamps": True,
            }
            
            if language:
                generate_kwargs["language"] = language.lower()
            
            # Run transcription with timestamps
            result = self.pipe(
                audio_path,
                return_timestamps=True,
                generate_kwargs=generate_kwargs
            )
            
            # Process chunks into segments
            segments_list: List[SubtitleSegment] = []
            chunks = result.get("chunks", [])
            
            if not chunks:
                # Fallback: create single segment from full text
                chunks = [{"text": result.get("text", ""), "timestamp": (0, 0)}]
            
            for i, chunk in enumerate(chunks):
                timestamp = chunk.get("timestamp", (0, 0))
                start = timestamp[0] if timestamp[0] is not None else 0
                end = timestamp[1] if timestamp[1] is not None else start + 5
                
                text = chunk.get("text", "").strip()
                if not text:
                    continue
                
                subtitle = SubtitleSegment(
                    id=len(segments_list) + 1,
                    start=start,
                    end=end,
                    text=text
                )
                segments_list.append(subtitle)
                
                # Calculate progress
                progress = min((i + 1) / len(chunks) * 100, 100)
                
                yield {
                    "type": "segment",
                    "segment": asdict(subtitle),
                    "progress": progress
                }
            
            elapsed = time.time() - start_time
            
            yield {
                "type": "complete",
                "total_segments": len(segments_list),
                "elapsed_time": elapsed,
                "segments": [asdict(s) for s in segments_list],
                "language": result.get("language", None)
            }
            
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    def transcribe_sync(
        self,
        audio_path: str,
        model_size: str = "large-v3-turbo",
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Synchronous transcription returning all segments at once."""
        segments = []
        for update in self.transcribe(audio_path, model_size, language):
            if update["type"] == "complete":
                return update["segments"]
            elif update["type"] == "error":
                raise Exception(update["message"])
        return segments
    
    def generate_srt(self, segments: List[Dict[str, Any]]) -> str:
        """Generate SRT content from segments."""
        srt_content = ""
        for seg in segments:
            subtitle = SubtitleSegment(**seg)
            srt_content += subtitle.to_srt() + "\n"
        return srt_content
    
    def unload_model(self):
        """Free GPU memory."""
        if self.model is not None:
            del self.model
            del self.processor
            del self.pipe
            self.model = None
            self.processor = None
            self.pipe = None
            self.current_model_id = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


transcription_service = TranscriptionService()
