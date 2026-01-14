"""Translation service using Hunyuan MT Chimera GGUF via llama-cpp-python."""
import os
import time
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
import config


class TranslationService:
    """Handles text translation using Hunyuan MT Chimera GGUF model."""
    
    def __init__(self):
        self.llm = None
        self.loaded = False
        self.model_path = config.MODELS_DIR / "hunyuan-mt-chimera-7b-q4_k_m.gguf"
    
    def load_model(self):
        """Load the GGUF translation model."""
        if self.loaded:
            return
        
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Translation model not found at {self.model_path}. "
                "Please download it first using the installer."
            )
        
        from llama_cpp import Llama
        
        # Determine GPU layers based on availability
        import torch
        n_gpu_layers = -1 if torch.cuda.is_available() else 0  # -1 = all layers on GPU
        
        print(f"Loading translation model from {self.model_path}")
        print(f"GPU layers: {n_gpu_layers}")
        
        self.llm = Llama(
            model_path=str(self.model_path),
            n_ctx=4096,
            n_threads=config.HALF_CPU_COUNT,
            n_gpu_layers=n_gpu_layers,
            verbose=False
        )
        
        self.loaded = True
        print("Translation model loaded successfully")
    
    def translate_text(
        self,
        text: str,
        source_lang: str = "Auto",
        target_lang: str = "Spanish",
        max_tokens: int = 512
    ) -> str:
        """Translate a single piece of text."""
        self.load_model()
        
        # Clean the input text
        text = text.strip()
        if not text:
            return text
        
        # Use a simpler, more direct prompt format
        if source_lang.lower() == "auto" or not source_lang:
            prompt = f"""<|im_start|>system
You are a professional translator. Translate the following text into {target_lang}. 
Rules:
- Output ONLY the translation, nothing else
- Preserve the original meaning and tone
- Keep proper nouns as-is unless they have a standard translation
- If unsure, make your best effort<|im_end|>
<|im_start|>user
{text}<|im_end|>
<|im_start|>assistant
"""
        else:
            prompt = f"""<|im_start|>system
You are a professional translator. Translate the following {source_lang} text into {target_lang}.
Rules:
- Output ONLY the translation, nothing else
- Preserve the original meaning and tone
- Keep proper nouns as-is unless they have a standard translation
- If unsure, make your best effort<|im_end|>
<|im_start|>user
{text}<|im_end|>
<|im_start|>assistant
"""
        
        try:
            output = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for more consistent translations
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                stop=["<|im_end|>", "<|im_start|>", "\n\n"]
            )
            
            translated_text = output["choices"][0]["text"].strip()
            
            # Fallback: if translation is empty or seems like an error, return original
            if not translated_text or len(translated_text) < 2:
                return text
                
            # Check for common error patterns
            error_patterns = ["i don't understand", "i cannot", "i'm sorry", "sorry,"]
            if any(pattern in translated_text.lower() for pattern in error_patterns):
                # Model failed to translate, try a simpler approach
                simple_prompt = f"Translate to {target_lang}: {text}\n\nTranslation:"
                output = self.llm(
                    simple_prompt,
                    max_tokens=max_tokens,
                    temperature=0.2,
                    stop=["\n", "<|im_end|>"]
                )
                translated_text = output["choices"][0]["text"].strip()
                
                # If still failing, return original
                if not translated_text or any(pattern in translated_text.lower() for pattern in error_patterns):
                    print(f"Translation failed for: {text[:50]}...")
                    return text
            
            return translated_text
            
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def translate_segments(
        self,
        segments: List[Dict[str, Any]],
        source_lang: str = "English",
        target_lang: str = "Spanish"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Translate subtitle segments with progress updates.
        
        Yields:
            Progress updates with translated segments
        """
        yield {"type": "status", "message": "Loading translation model..."}
        
        try:
            self.load_model()
        except FileNotFoundError as e:
            yield {"type": "error", "message": str(e)}
            return
        except Exception as e:
            yield {"type": "error", "message": f"Failed to load model: {str(e)}"}
            return
        
        yield {"type": "status", "message": "Starting translation..."}
        
        total = len(segments)
        translated_segments = []
        start_time = time.time()
        
        for i, segment in enumerate(segments):
            try:
                segment_start = time.time()
                
                translated_text = self.translate_text(
                    segment["text"],
                    source_lang,
                    target_lang
                )
                
                segment_time = time.time() - segment_start
                
                translated_segment = {
                    **segment,
                    "original_text": segment["text"],
                    "text": translated_text
                }
                translated_segments.append(translated_segment)
                
                progress = ((i + 1) / total) * 100
                elapsed = time.time() - start_time
                avg_time_per_segment = elapsed / (i + 1)
                remaining = avg_time_per_segment * (total - i - 1)
                
                yield {
                    "type": "segment",
                    "segment": translated_segment,
                    "progress": progress,
                    "current": i + 1,
                    "total": total,
                    "elapsed": elapsed,
                    "remaining": remaining,
                    "segment_time": segment_time
                }
                
            except Exception as e:
                yield {
                    "type": "warning",
                    "message": f"Failed to translate segment {i + 1}: {str(e)}",
                    "segment_id": segment.get("id")
                }
                # Keep original text on failure
                translated_segments.append(segment)
        
        yield {
            "type": "complete",
            "segments": translated_segments,
            "elapsed_time": time.time() - start_time
        }
    
    def unload_model(self):
        """Unload model to free memory."""
        if self.llm is not None:
            del self.llm
            self.llm = None
            self.loaded = False


translation_service = TranslationService()
