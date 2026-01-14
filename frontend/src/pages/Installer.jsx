import { useState } from 'react'
import {
    CheckCircle, XCircle, Download, Loader, AlertTriangle,
    Cpu, HardDrive, Zap, RefreshCw, ExternalLink
} from 'lucide-react'
import './Installer.css'

const API_BASE = 'http://localhost:8000/api'

function Installer({ status, onComplete, onRefresh }) {
    const [installing, setInstalling] = useState(null)
    const [installProgress, setInstallProgress] = useState({})
    const [installMessages, setInstallMessages] = useState({})

    const handleInstallFFmpeg = async () => {
        setInstalling('ffmpeg')
        setInstallMessages(prev => ({ ...prev, ffmpeg: 'Starting FFmpeg download...' }))

        try {
            const res = await fetch(`${API_BASE}/system/install-ffmpeg`, {
                method: 'POST'
            })
            const data = await res.json()

            if (data.success) {
                setInstallProgress(prev => ({ ...prev, ffmpeg: 'complete' }))
                setInstallMessages(prev => ({ ...prev, ffmpeg: 'FFmpeg installed! Refreshing...' }))
                // Refresh status after a moment
                setTimeout(() => {
                    window.location.reload()
                }, 1500)
            } else {
                setInstallProgress(prev => ({ ...prev, ffmpeg: 'error' }))
                setInstallMessages(prev => ({ ...prev, ffmpeg: data.error || 'Installation failed' }))
            }
        } catch (err) {
            setInstallProgress(prev => ({ ...prev, ffmpeg: 'error' }))
            setInstallMessages(prev => ({ ...prev, ffmpeg: 'Network error' }))
        }
        setInstalling(null)
    }

    const handleInstallCuda = async () => {
        setInstalling('cuda')
        setInstallMessages(prev => ({ ...prev, cuda: 'Installing PyTorch with CUDA (this may take several minutes)...' }))

        try {
            const res = await fetch(`${API_BASE}/system/install-cuda`, {
                method: 'POST'
            })
            const data = await res.json()

            if (data.success) {
                setInstallProgress(prev => ({ ...prev, cuda: 'complete' }))
                setInstallMessages(prev => ({ ...prev, cuda: 'PyTorch with CUDA installed! Please restart the application.' }))
            } else {
                setInstallProgress(prev => ({ ...prev, cuda: 'error' }))
                setInstallMessages(prev => ({ ...prev, cuda: data.error || 'Installation failed' }))
            }
        } catch (err) {
            setInstallProgress(prev => ({ ...prev, cuda: 'error' }))
            setInstallMessages(prev => ({ ...prev, cuda: 'Network error' }))
        }
        setInstalling(null)
    }

    const handleInstallWhisper = async () => {
        setInstalling('whisper')
        setInstallMessages(prev => ({ ...prev, whisper: 'Downloading Whisper model (~3GB)...' }))

        try {
            const res = await fetch(`${API_BASE}/system/download-whisper?model_size=large-v3-turbo`, {
                method: 'POST'
            })
            const data = await res.json()

            if (data.success) {
                setInstallProgress(prev => ({ ...prev, whisper: 'complete' }))
                setInstallMessages(prev => ({ ...prev, whisper: 'Whisper model ready!' }))
            } else {
                setInstallProgress(prev => ({ ...prev, whisper: 'error' }))
                setInstallMessages(prev => ({ ...prev, whisper: data.error || 'Download failed' }))
            }
        } catch (err) {
            setInstallProgress(prev => ({ ...prev, whisper: 'error' }))
            setInstallMessages(prev => ({ ...prev, whisper: 'Network error' }))
        }
        setInstalling(null)
    }

    const handleInstallTranslation = async () => {
        setInstalling('translation')
        setInstallMessages(prev => ({ ...prev, translation: 'Downloading translation model (~4.4GB)...' }))

        try {
            const res = await fetch(`${API_BASE}/system/download-translation`, {
                method: 'POST'
            })
            const data = await res.json()

            if (data.success) {
                setInstallProgress(prev => ({ ...prev, translation: 'complete' }))
                setInstallMessages(prev => ({ ...prev, translation: 'Translation model ready!' }))
            } else {
                setInstallProgress(prev => ({ ...prev, translation: 'error' }))
                setInstallMessages(prev => ({ ...prev, translation: data.error || 'Download failed' }))
            }
        } catch (err) {
            setInstallProgress(prev => ({ ...prev, translation: 'error' }))
            setInstallMessages(prev => ({ ...prev, translation: 'Network error' }))
        }
        setInstalling(null)
    }

    const StatusIcon = ({ ok, loading, warning }) => {
        if (loading) return <Loader className="status-icon loading" size={20} />
        if (ok) return <CheckCircle className="status-icon success" size={20} />
        if (warning) return <AlertTriangle className="status-icon warning" size={20} />
        return <XCircle className="status-icon error" size={20} />
    }

    const isFFmpegReady = status?.ffmpeg?.installed || installProgress.ffmpeg === 'complete'
    const isCudaAvailable = status?.cuda?.available
    const isWhisperReady = status?.whisper?.available || installProgress.whisper === 'complete'
    const isTranslationReady = status?.translation?.available || installProgress.translation === 'complete'

    return (
        <div className="installer-page">
            <div className="installer-container animate-slide-up">
                {/* Header */}
                <div className="installer-header">
                    <div className="logo">
                        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                            <circle cx="24" cy="24" r="20" stroke="var(--color-turquoise-400)" strokeWidth="2.5" />
                            <path d="M15 24 L21 30 L33 18" stroke="var(--color-turquoise-400)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <h1>AutoCaption Setup</h1>
                    <p className="text-secondary">Let's make sure everything is ready</p>
                </div>

                {/* Status Checks */}
                <div className="status-grid">
                    {/* FFmpeg */}
                    <div className={`status-card ${isFFmpegReady ? 'ok' : 'error'}`}>
                        <div className="status-header">
                            <HardDrive size={24} />
                            <span>FFmpeg</span>
                            <StatusIcon ok={isFFmpegReady} loading={installing === 'ffmpeg'} />
                        </div>
                        <p className="status-detail">
                            {isFFmpegReady
                                ? status?.ffmpeg?.version || 'Installed'
                                : 'Required for video processing'}
                        </p>
                        {installMessages.ffmpeg && (
                            <p className={`install-message ${installProgress.ffmpeg}`}>{installMessages.ffmpeg}</p>
                        )}
                        {!isFFmpegReady && (
                            <div className="action-buttons">
                                <button
                                    className="btn btn-primary btn-sm"
                                    onClick={handleInstallFFmpeg}
                                    disabled={installing === 'ffmpeg'}
                                >
                                    {installing === 'ffmpeg' ? (
                                        <>
                                            <Loader size={16} className="spinning" />
                                            Installing...
                                        </>
                                    ) : (
                                        <>
                                            <Download size={16} />
                                            Install FFmpeg
                                        </>
                                    )}
                                </button>
                                <a
                                    href="https://ffmpeg.org/download.html"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn btn-ghost btn-sm"
                                >
                                    <ExternalLink size={14} />
                                    Manual
                                </a>
                            </div>
                        )}
                    </div>

                    {/* CUDA/GPU */}
                    <div className={`status-card ${isCudaAvailable ? 'ok' : 'warning'}`}>
                        <div className="status-header">
                            <Zap size={24} />
                            <span>GPU Acceleration</span>
                            <StatusIcon ok={isCudaAvailable} warning={!isCudaAvailable} />
                        </div>
                        <p className="status-detail">
                            {isCudaAvailable
                                ? (
                                    <>
                                        {status.cuda.device_name}
                                        <br />
                                        <small>CUDA {status.cuda.cuda_version} • {status.cuda.devices?.[0]?.total_memory_gb}GB VRAM</small>
                                    </>
                                )
                                : status?.cuda?.message || 'No GPU detected. Will use CPU (slower).'}
                        </p>
                        {installMessages.cuda && (
                            <p className={`install-message ${installProgress.cuda}`}>{installMessages.cuda}</p>
                        )}
                        {!isCudaAvailable && status?.cuda?.suggestion && (
                            <div className="action-buttons">
                                <button
                                    className="btn btn-secondary btn-sm"
                                    onClick={handleInstallCuda}
                                    disabled={installing === 'cuda'}
                                >
                                    {installing === 'cuda' ? (
                                        <>
                                            <Loader size={16} className="spinning" />
                                            Installing...
                                        </>
                                    ) : (
                                        <>
                                            <Download size={16} />
                                            Install CUDA PyTorch
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                        {!isCudaAvailable && (
                            <p className="hint-text">
                                Requires NVIDIA GPU with CUDA support
                            </p>
                        )}
                    </div>

                    {/* Whisper Model */}
                    <div className={`status-card ${isWhisperReady ? 'ok' : ''}`}>
                        <div className="status-header">
                            <Cpu size={24} />
                            <span>Whisper Model</span>
                            <StatusIcon
                                ok={isWhisperReady}
                                loading={installing === 'whisper'}
                            />
                        </div>
                        <p className="status-detail">
                            {isWhisperReady
                                ? 'Whisper Large V3 Turbo ready'
                                : 'Speech recognition (~3GB download)'}
                        </p>
                        {installMessages.whisper && (
                            <p className={`install-message ${installProgress.whisper}`}>{installMessages.whisper}</p>
                        )}
                        {!isWhisperReady && (
                            <button
                                className="btn btn-secondary btn-sm"
                                onClick={handleInstallWhisper}
                                disabled={installing === 'whisper'}
                            >
                                {installing === 'whisper' ? (
                                    <>
                                        <Loader size={16} className="spinning" />
                                        Downloading...
                                    </>
                                ) : (
                                    <>
                                        <Download size={16} />
                                        Pre-download Model
                                    </>
                                )}
                            </button>
                        )}
                    </div>

                    {/* Translation Model */}
                    <div className={`status-card ${isTranslationReady ? 'ok' : ''}`}>
                        <div className="status-header">
                            <Cpu size={24} />
                            <span>Translation Model</span>
                            <StatusIcon
                                ok={isTranslationReady}
                                loading={installing === 'translation'}
                            />
                        </div>
                        <p className="status-detail">
                            {isTranslationReady
                                ? 'Hunyuan MT Chimera GGUF ready'
                                : 'Translation model (~4.4GB download)'}
                        </p>
                        {installMessages.translation && (
                            <p className={`install-message ${installProgress.translation}`}>{installMessages.translation}</p>
                        )}
                        {!isTranslationReady && (
                            <button
                                className="btn btn-secondary btn-sm"
                                onClick={handleInstallTranslation}
                                disabled={installing === 'translation'}
                            >
                                {installing === 'translation' ? (
                                    <>
                                        <Loader size={16} className="spinning" />
                                        Downloading...
                                    </>
                                ) : (
                                    <>
                                        <Download size={16} />
                                        Pre-download Model
                                    </>
                                )}
                            </button>
                        )}
                    </div>
                </div>

                {/* System Info */}
                {status?.cuda?.torch_version && (
                    <div className="system-info">
                        <span>PyTorch {status.cuda.torch_version}</span>
                        {status.cuda.cudnn_version && <span>cuDNN {status.cuda.cudnn_version}</span>}
                    </div>
                )}

                {/* Action */}
                <div className="installer-actions">
                    {!isFFmpegReady ? (
                        <div className="warning-box">
                            <AlertTriangle size={20} />
                            <span>FFmpeg is required to process videos. Click "Install FFmpeg" above.</span>
                        </div>
                    ) : (
                        <button className="btn btn-primary btn-lg" onClick={onComplete}>
                            <CheckCircle size={20} />
                            Continue to Dashboard
                        </button>
                    )}
                </div>

                {/* Info */}
                <p className="installer-note">
                    Models will download automatically on first use if not pre-downloaded.
                    <br />
                    <small>GPU acceleration is optional but recommended for faster processing.</small>
                </p>
            </div>
        </div>
    )
}

export default Installer
