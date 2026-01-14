"""Hardware detection and acceleration management for cross-platform support."""
import subprocess
import platform
import sys
import os
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path


class GPUVendor(Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"


class AccelerationBackend(Enum):
    CUDA = "cuda"           # NVIDIA on all platforms
    MPS = "mps"             # Apple Metal Performance Shaders
    ROCM = "rocm"           # AMD on Linux
    VULKAN = "vulkan"       # AMD/Intel on Windows/Linux (llama-cpp)
    DIRECTML = "directml"   # Windows universal (experimental)
    CPU = "cpu"             # Fallback



class HardwareService:
    """Cross-platform hardware detection and acceleration setup."""
    
    def __init__(self):
        self._cached_gpu_info = None
        self._cache_time = 0
        self._cache_ttl = 300  # 5 minutes cache
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get basic system information."""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "is_arm": platform.machine().lower() in ["arm64", "aarch64"],
        }
    
    def detect_gpu(self) -> Dict[str, Any]:
        """Detect available GPUs and their vendors (Cached)."""
        import time
        # Return cached if valid
        if self._cached_gpu_info and (time.time() - self._cache_time < self._cache_ttl):
            return self._cached_gpu_info

        system = platform.system()
        gpus = []
        primary_vendor = GPUVendor.UNKNOWN
        
        # macOS - Check for Apple Silicon
        if system == "Darwin":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True, text=True, timeout=10
                )
                output = result.stdout.lower()
                
                if "apple" in output or platform.machine() == "arm64":
                    gpus.append({
                        "name": "Apple Silicon GPU",
                        "vendor": GPUVendor.APPLE.value,
                        "supports": [AccelerationBackend.MPS.value]
                    })
                    primary_vendor = GPUVendor.APPLE
                elif "amd" in output or "radeon" in output:
                    gpus.append({
                        "name": "AMD GPU",
                        "vendor": GPUVendor.AMD.value,
                        "supports": [AccelerationBackend.CPU.value]  # No good acceleration on Intel Mac AMD
                    })
                    primary_vendor = GPUVendor.AMD
            except Exception:
                pass
        
        # Windows - Check with PowerShell (WMIC is deprecated/missing)
        elif system == "Windows":
            try:
                # Try PowerShell first as it's more reliable continuously
                ps_command = "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode != 0:
                    # Fallback to WMIC if PowerShell fails
                    result = subprocess.run(
                        ["wmic", "path", "win32_VideoController", "get", "name"],
                        capture_output=True, text=True, timeout=10
                    )
                
                output_lines = result.stdout.split('\n')
                
                for line in output_lines:
                    gpu_name = line.strip()
                    if not gpu_name or gpu_name.lower() == "name":
                        continue
                        
                    gpu_lower = gpu_name.lower()
                    if "nvidia" in gpu_lower or "geforce" in gpu_lower or "rtx" in gpu_lower or "gtx" in gpu_lower:
                        gpus.append({
                            "name": gpu_name,
                            "vendor": GPUVendor.NVIDIA.value,
                            "supports": [AccelerationBackend.CUDA.value, AccelerationBackend.VULKAN.value]
                        })
                        # Always prioritize NVIDIA as primary if found
                        primary_vendor = GPUVendor.NVIDIA
                    elif "amd" in gpu_lower or "radeon" in gpu_lower:
                        gpus.append({
                            "name": gpu_name,
                            "vendor": GPUVendor.AMD.value,
                            "supports": [AccelerationBackend.VULKAN.value, AccelerationBackend.DIRECTML.value]
                        })
                        if primary_vendor == GPUVendor.UNKNOWN:
                            primary_vendor = GPUVendor.AMD
                    elif "intel" in gpu_lower:
                        gpus.append({
                            "name": gpu_name,
                            "vendor": GPUVendor.INTEL.value,
                            "supports": [AccelerationBackend.VULKAN.value, AccelerationBackend.DIRECTML.value]
                        })
                        # Don't set as primary if we found NVIDIA/AMD already
                        if primary_vendor == GPUVendor.UNKNOWN:
                            primary_vendor = GPUVendor.INTEL
            except Exception as e:
                print(f"GPU detection error: {e}")
                pass
        
        # Linux - Check with lspci
        elif system == "Linux":
            try:
                result = subprocess.run(
                    ["lspci", "-v"],
                    capture_output=True, text=True, timeout=10
                )
                output = result.stdout.lower()
                
                if "nvidia" in output:
                    gpus.append({
                        "name": "NVIDIA GPU",
                        "vendor": GPUVendor.NVIDIA.value,
                        "supports": [AccelerationBackend.CUDA.value, AccelerationBackend.VULKAN.value]
                    })
                    primary_vendor = GPUVendor.NVIDIA
                if "amd" in output or "radeon" in output:
                    gpus.append({
                        "name": "AMD GPU",
                        "vendor": GPUVendor.AMD.value,
                        "supports": [AccelerationBackend.ROCM.value, AccelerationBackend.VULKAN.value]
                    })
                    if primary_vendor == GPUVendor.UNKNOWN:
                        primary_vendor = GPUVendor.AMD
            except Exception:
                pass
        
        result = {
            "gpus": gpus,
            "primary_vendor": primary_vendor.value,
            "has_dedicated_gpu": len(gpus) > 0
        }
        
        # Cache result
        self._cached_gpu_info = result
        self._cache_time = time.time()
        return result
    
    @staticmethod
    def check_pytorch_backends() -> Dict[str, Any]:
        """Check which PyTorch backends are available."""
        backends = {
            "cuda": False,
            "cuda_version": None,
            "mps": False,
            "cpu": True,
            "device_name": None,
            "torch_version": None
        }
        
        try:
            import torch
            backends["torch_version"] = torch.__version__
            
            # Check CUDA
            if torch.cuda.is_available():
                backends["cuda"] = True
                backends["cuda_version"] = torch.version.cuda
                backends["device_name"] = torch.cuda.get_device_name(0)
            
            # Check MPS (Apple Silicon)
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                backends["mps"] = True
                backends["device_name"] = "Apple Silicon GPU"
                
        except ImportError:
            backends["error"] = "PyTorch not installed"
        except Exception as e:
            backends["error"] = str(e)
        
        return backends
    
    @staticmethod
    def check_llama_cpp_backends() -> Dict[str, Any]:
        """Check llama-cpp-python backend capabilities."""
        backends = {
            "installed": False,
            "cuda": False,
            "metal": False,
            "vulkan": False,
            "version": None
        }
        
        try:
            import llama_cpp
            backends["installed"] = True
            backends["version"] = getattr(llama_cpp, "__version__", "unknown")
            
            # Check build info if available
            if hasattr(llama_cpp, 'llama_print_system_info'):
                # This would show build flags but is complex to parse
                pass
            
            # On Mac, Metal is usually enabled by default
            if platform.system() == "Darwin":
                backends["metal"] = True
                
        except ImportError:
            pass
        except Exception as e:
            backends["error"] = str(e)
        
        return backends
    
    def get_recommended_backend(self) -> Dict[str, Any]:
        """Get the recommended acceleration backend for this system."""
        system = platform.system()
        # Use instance method for detection (cached)
        gpu_info = self.detect_gpu()
        pytorch = HardwareService.check_pytorch_backends()
        
        # Determine best backend
        if system == "Darwin" and (pytorch.get("mps") or platform.machine() == "arm64"):
            return {
                "backend": AccelerationBackend.MPS.value,
                "name": "Metal (Apple Silicon)",
                "ready": pytorch.get("mps", False),
                "install_command": None,  # MPS is built into PyTorch for Mac
                "description": "Native Apple Silicon acceleration"
            }
        
        if pytorch.get("cuda"):
            return {
                "backend": AccelerationBackend.CUDA.value,
                "name": "CUDA (NVIDIA)",
                "ready": True,
                "install_command": None,
                "description": f"NVIDIA {pytorch.get('device_name', 'GPU')} with CUDA {pytorch.get('cuda_version')}"
            }
        
        # Check if NVIDIA GPU exists but CUDA not installed
        if gpu_info["primary_vendor"] == "nvidia":
            return {
                "backend": AccelerationBackend.CUDA.value,
                "name": "CUDA (NVIDIA)",
                "ready": False,
                "install_command": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",
                "description": "NVIDIA GPU detected - install CUDA PyTorch for acceleration"
            }
        
        # AMD GPU
        if gpu_info["primary_vendor"] == "amd":
            return {
                "backend": AccelerationBackend.VULKAN.value,
                "name": "Vulkan (AMD)",
                "ready": False,  # Need to check llama-cpp-python Vulkan build
                "install_command": "pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/vulkan",
                "description": "AMD GPU - Vulkan acceleration available for translation"
            }
        
        # Intel GPU
        if gpu_info["primary_vendor"] == "intel":
            return {
                "backend": AccelerationBackend.VULKAN.value,
                "name": "Vulkan (Intel)",
                "ready": False,
                "install_command": "pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/vulkan",
                "description": "Intel GPU - Vulkan acceleration available for translation"
            }
        
        # Fallback to CPU
        return {
            "backend": AccelerationBackend.CPU.value,
            "name": "CPU",
            "ready": True,
            "install_command": None,
            "description": "CPU processing (no GPU acceleration)"
        }
    
    def get_full_hardware_status(self) -> Dict[str, Any]:
        """Get complete hardware and acceleration status."""
        system_info = HardwareService.get_system_info()
        gpu_info = self.detect_gpu()
        pytorch = HardwareService.check_pytorch_backends()
        llama = HardwareService.check_llama_cpp_backends()
        recommended = self.get_recommended_backend()
        
        # Determine current active backend
        current_backend = AccelerationBackend.CPU.value
        if pytorch.get("cuda"):
            current_backend = AccelerationBackend.CUDA.value
        elif pytorch.get("mps"):
            current_backend = AccelerationBackend.MPS.value
        
        return {
            "system": system_info,
            "gpus": gpu_info,
            "pytorch": pytorch,
            "llama_cpp": llama,
            "recommended": recommended,
            "current_backend": current_backend,
            "available_backends": self._get_available_backends(system_info, gpu_info)
        }
    
    def _get_available_backends(self, system_info: Dict, gpu_info: Dict) -> List[Dict]:
        """List all available backend options for the current system."""
        platform_name = system_info["platform"]
        backends = []
        
        # Always available
        backends.append({
            "id": "cpu",
            "name": "CPU Only",
            "description": "Works on all systems, slowest option",
            "install_command": None
        })
        
        # Platform-specific
        if platform_name == "Darwin" and system_info.get("is_arm"):
            backends.append({
                "id": "mps",
                "name": "Metal (Apple Silicon)",
                "description": "Native Apple Silicon acceleration, very fast",
                "install_command": "pip install torch torchvision torchaudio"
            })
        
        if gpu_info["primary_vendor"] == "nvidia":
            backends.append({
                "id": "cuda",
                "name": "CUDA (NVIDIA)",
                "description": "Best performance for NVIDIA GPUs",
                "install_command": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
            })
        
        if gpu_info["primary_vendor"] in ["amd", "intel"]:
            backends.append({
                "id": "vulkan",
                "name": "Vulkan",
                "description": "GPU acceleration for AMD/Intel (translation only)",
                "install_command": "pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/vulkan"
            })
        
        return backends


# Singleton instance
hardware_service = HardwareService()
