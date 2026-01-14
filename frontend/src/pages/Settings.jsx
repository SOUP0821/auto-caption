import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
    ArrowLeft, Cpu, Zap, RefreshCw, Download,
    Check, X, AlertTriangle, HardDrive, Settings as SettingsIcon,
    Trash2, Monitor, Apple, ChevronDown
} from 'lucide-react'
import './Settings.css'

const API_BASE = 'http://localhost:8000/api'

function Settings() {
    const navigate = useNavigate()
    const [status, setStatus] = useState(null)
    const [hardware, setHardware] = useState(null)
    const [storageInfo, setStorageInfo] = useState(null)
    const [loading, setLoading] = useState(true)
    const [installing, setInstalling] = useState(null)
    const [messages, setMessages] = useState({})
    const [showUninstall, setShowUninstall] = useState(false)

    useEffect(() => {
        loadAllStatus()
    }, [])

    const loadAllStatus = async () => {
        setLoading(true)
        await Promise.all([
            loadStatus(),
            loadHardware(),
            loadStorageInfo()
        ])
        setLoading(false)
    }

    const loadStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/system/status`)
            const data = await res.json()
            setStatus(data)
        } catch (err) {
            console.error('Failed to load status:', err)
        }
    }

    const loadHardware = async () => {
        try {
            const res = await fetch(`${API_BASE}/hardware/status`)
            const data = await res.json()
            setHardware(data)
        } catch (err) {
            console.error('Failed to load hardware:', err)
        }
    }

    const loadStorageInfo = async () => {
        try {
            const res = await fetch(`${API_BASE}/uninstall/info`)
            const data = await res.json()
            setStorageInfo(data)
        } catch (err) {
            console.error('Failed to load storage info:', err)
        }
    }

    const installBackend = async (backend) => {
        setInstalling(backend)
        setMessages(prev => ({ ...prev, [backend]: `Installing ${backend.toUpperCase()}... This may take several minutes.` }))

        try {
            const res = await fetch(`${API_BASE}/hardware/install-backend?backend=${backend}`, { method: 'POST' })
            const data = await res.json()

            if (data.success) {
                setMessages(prev => ({ ...prev, [backend]: `Success: ${data.message}` }))
            } else {
                setMessages(prev => ({ ...prev, [backend]: `Failed: ${data.error}` }))
            }
        } catch (err) {
            setMessages(prev => ({ ...prev, [backend]: `Error: ${err.message}` }))
        }
        setInstalling(null)
    }

    const installFFmpeg = async () => {
        setInstalling('ffmpeg')
        setMessages(prev => ({ ...prev, ffmpeg: 'Downloading FFmpeg...' }))

        try {
            const res = await fetch(`${API_BASE}/system/install-ffmpeg`, { method: 'POST' })
            const data = await res.json()

            if (data.success) {
                setMessages(prev => ({ ...prev, ffmpeg: 'Success: FFmpeg installed!' }))
                loadStatus()
            } else {
                setMessages(prev => ({ ...prev, ffmpeg: `Failed: ${data.error}` }))
            }
        } catch (err) {
            setMessages(prev => ({ ...prev, ffmpeg: `Error: ${err.message}` }))
        }
        setInstalling(null)
    }

    const downloadWhisperModel = async () => {
        setInstalling('whisper')
        setMessages(prev => ({ ...prev, whisper: 'Downloading Whisper Large V3 Turbo (~3GB)...' }))

        try {
            const res = await fetch(`${API_BASE}/system/download-whisper?model_size=large-v3-turbo`, { method: 'POST' })
            const data = await res.json()

            if (data.success) {
                setMessages(prev => ({ ...prev, whisper: 'Success: Model downloaded!' }))
                loadStatus()
            } else {
                setMessages(prev => ({ ...prev, whisper: `Failed: ${data.error}` }))
            }
        } catch (err) {
            setMessages(prev => ({ ...prev, whisper: `Error: ${err.message}` }))
        }
        setInstalling(null)
    }

    const downloadTranslationModel = async () => {
        setInstalling('translation')
        setMessages(prev => ({ ...prev, translation: 'Downloading Hunyuan MT (~4.4GB)...' }))

        try {
            const res = await fetch(`${API_BASE}/system/download-translation`, { method: 'POST' })
            const data = await res.json()

            if (data.success) {
                setMessages(prev => ({ ...prev, translation: 'Success: Model downloaded!' }))
                loadStatus()
            } else {
                setMessages(prev => ({ ...prev, translation: `Failed: ${data.error}` }))
            }
        } catch (err) {
            setMessages(prev => ({ ...prev, translation: `Error: ${err.message}` }))
        }
        setInstalling(null)
    }

    const deleteModels = async () => {
        if (!confirm('Delete all downloaded AI models? You will need to re-download them to use the app.')) return

        setInstalling('delete-models')
        try {
            const res = await fetch(`${API_BASE}/uninstall/models`, { method: 'DELETE' })
            const data = await res.json()
            if (data.success) {
                setMessages(prev => ({ ...prev, uninstall: `Success: Models deleted, freed ${data.freed_mb} MB` }))
                loadStorageInfo()
                loadStatus()
            }
        } catch (err) {
            setMessages(prev => ({ ...prev, uninstall: `Error: ${err.message}` }))
        }
        setInstalling(null)
    }

    const deleteProjects = async () => {
        if (!confirm('Delete ALL projects? This cannot be undone!')) return

        setInstalling('delete-projects')
        try {
            const res = await fetch(`${API_BASE}/uninstall/projects`, { method: 'DELETE' })
            const data = await res.json()
            if (data.success) {
                setMessages(prev => ({ ...prev, uninstall: `Success: ${data.message}` }))
                loadStorageInfo()
            }
        } catch (err) {
            setMessages(prev => ({ ...prev, uninstall: `Error: ${err.message}` }))
        }
        setInstalling(null)
    }

    const startUninstall = async () => {
        if (!confirm('Are you sure you want to uninstall AutoCaption? The app will close and delete itself.')) return

        setInstalling('uninstall')
        try {
            const res = await fetch(`${API_BASE}/uninstall/perform-self-destruct`, { method: 'POST' })
            const data = await res.json()
            if (data.success) {
                setMessages(prev => ({ ...prev, uninstall: 'Uninstalling... App will close in 3 seconds.' }))
            } else {
                setMessages(prev => ({ ...prev, uninstall: `Error: ${data.message || data.error}` }))
            }
        } catch (err) {
            setMessages(prev => ({ ...prev, uninstall: 'Uninstall initiated.' }))
        }
    }

    if (loading) {
        return (
            <div className="settings-page">
                <div className="settings-loading">
                    <div className="spinner"></div>
                    <p>Loading system information...</p>
                </div>
            </div>
        )
    }

    const cuda = status?.cuda || {}
    const ffmpeg = status?.ffmpeg || {}
    const whisper = status?.whisper || {}
    const translation = status?.translation || {}
    const recommended = hardware?.recommended || {}
    const gpus = hardware?.gpus?.gpus || []
    const currentBackend = hardware?.current_backend || 'cpu'

    // Get the platform icon
    const getPlatformIcon = () => {
        const platform = hardware?.system?.platform
        if (platform === 'Darwin') return <Apple size={20} />
        return <Monitor size={20} />
    }

    return (
        <div className="settings-page">
            <header className="settings-header">
                <button className="btn btn-ghost" onClick={() => navigate('/dashboard')}>
                    <ArrowLeft size={18} />
                    Back
                </button>
                <h1>
                    <SettingsIcon size={24} />
                    Settings
                </h1>
                <button className="btn btn-ghost" onClick={loadAllStatus}>
                    <RefreshCw size={18} />
                    Refresh
                </button>
            </header>

            <main className="settings-main">
                {/* Hardware Detection */}
                <section className="settings-section">
                    <h2>
                        <Zap size={20} />
                        Hardware Acceleration
                    </h2>

                    {/* Detected GPUs */}
                    <div className="setting-card">
                        <div className="setting-info">
                            <h4>Detected Hardware</h4>
                            {gpus.length > 0 ? (
                                <div className="gpu-list">
                                    {gpus.map((gpu, i) => (
                                        <div key={i} className="gpu-item">
                                            <span className={`badge badge-${gpu.vendor === 'nvidia' ? 'success' : gpu.vendor === 'apple' ? 'turquoise' : 'warning'}`}>
                                                {gpu.vendor.toUpperCase()}
                                            </span>
                                            <span className="gpu-name">{gpu.name}</span>
                                            <span className="gpu-supports">
                                                Supports: {gpu.supports?.join(', ') || 'CPU'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="muted">No dedicated GPU detected - using CPU</p>
                            )}
                        </div>
                    </div>

                    {/* Current Backend Status */}
                    <div className="setting-card">
                        <div className="setting-info">
                            <div className="setting-status">
                                <span className={`badge badge-${currentBackend !== 'cpu' ? 'success' : 'warning'}`}>
                                    {currentBackend !== 'cpu' ? <Zap size={14} /> : <Cpu size={14} />}
                                    {currentBackend.toUpperCase()} Active
                                </span>
                            </div>

                            {currentBackend === 'cuda' && (
                                <div className="gpu-details">
                                    <h3>{cuda.device_name}</h3>
                                    <div className="gpu-specs">
                                        <span>CUDA {cuda.cuda_version}</span>
                                        <span>PyTorch {cuda.torch_version}</span>
                                    </div>
                                </div>
                            )}

                            {currentBackend === 'mps' && (
                                <div className="gpu-details">
                                    <h3>Apple Silicon GPU</h3>
                                    <p className="muted">Metal Performance Shaders active</p>
                                </div>
                            )}

                            {currentBackend === 'cpu' && (
                                <div className="cpu-info">
                                    <p>{recommended.description}</p>
                                    {recommended.install_command && (
                                        <p className="hint">Recommended: Install {recommended.name} for faster processing</p>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Install Backend Button */}
                        {recommended.install_command && !recommended.ready && (
                            <div className="setting-action">
                                {messages[recommended.backend] && (
                                    <p className="action-message">{messages[recommended.backend]}</p>
                                )}
                                <button
                                    className="btn btn-primary"
                                    onClick={() => installBackend(recommended.backend)}
                                    disabled={installing === recommended.backend}
                                >
                                    {installing === recommended.backend ? (
                                        <>
                                            <RefreshCw size={16} className="spinning" />
                                            Installing...
                                        </>
                                    ) : (
                                        <>
                                            <Download size={16} />
                                            Install {recommended.name}
                                        </>
                                    )}
                                </button>
                                <p className="action-note">
                                    {recommended.backend === 'cuda' && 'Requires NVIDIA GPU with CUDA support. ~2.5GB download.'}
                                    {recommended.backend === 'mps' && 'Uses built-in Apple Metal support.'}
                                    {recommended.backend === 'vulkan' && 'GPU acceleration for AMD/Intel GPUs.'}
                                </p>
                            </div>
                        )}
                    </div>

                    {/* PyTorch Version */}
                    <div className="setting-card compact">
                        <span>PyTorch Version</span>
                        <code>{cuda.torch_version || hardware?.pytorch?.torch_version || 'Not installed'}</code>
                    </div>
                </section>

                {/* FFmpeg Section */}
                <section className="settings-section">
                    <h2>
                        <HardDrive size={20} />
                        FFmpeg
                    </h2>

                    <div className="setting-card">
                        <div className="setting-info">
                            <div className="setting-status">
                                {ffmpeg.installed ? (
                                    <span className="badge badge-success">
                                        <Check size={14} /> Installed
                                    </span>
                                ) : (
                                    <span className="badge badge-error">
                                        <X size={14} /> Not Found
                                    </span>
                                )}
                            </div>

                            {ffmpeg.installed ? (
                                <p className="version-info">{ffmpeg.version}</p>
                            ) : (
                                <p>Required for video and audio processing</p>
                            )}
                        </div>

                        {!ffmpeg.installed && (
                            <div className="setting-action">
                                {messages.ffmpeg && (
                                    <p className="action-message">{messages.ffmpeg}</p>
                                )}
                                <button
                                    className="btn btn-primary"
                                    onClick={installFFmpeg}
                                    disabled={installing === 'ffmpeg'}
                                >
                                    {installing === 'ffmpeg' ? (
                                        <>
                                            <RefreshCw size={16} className="spinning" />
                                            Installing...
                                        </>
                                    ) : (
                                        <>
                                            <Download size={16} />
                                            Install FFmpeg
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>
                </section>

                {/* Models Section */}
                <section className="settings-section">
                    <h2>
                        <Cpu size={20} />
                        AI Models
                    </h2>

                    <div className="setting-card">
                        <div className="setting-info">
                            <h4>Whisper (Transcription)</h4>
                            <div className="setting-status">
                                {whisper.available ? (
                                    <span className="badge badge-success">
                                        <Check size={14} /> Ready
                                    </span>
                                ) : (
                                    <span className="badge badge-default">
                                        Not downloaded
                                    </span>
                                )}
                            </div>
                            <p className="model-note">Large V3 Turbo - Best speed/accuracy balance</p>
                        </div>

                        <div className="setting-action">
                            {messages.whisper && (
                                <p className="action-message">{messages.whisper}</p>
                            )}
                            <button
                                className="btn btn-secondary"
                                onClick={downloadWhisperModel}
                                disabled={installing === 'whisper' || whisper.available}
                            >
                                {installing === 'whisper' ? (
                                    <>
                                        <RefreshCw size={16} className="spinning" />
                                        Downloading...
                                    </>
                                ) : whisper.available ? (
                                    <>
                                        <Check size={16} />
                                        Downloaded
                                    </>
                                ) : (
                                    <>
                                        <Download size={16} />
                                        Pre-download (~3GB)
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    <div className="setting-card">
                        <div className="setting-info">
                            <h4>Hunyuan MT Chimera (Translation)</h4>
                            <div className="setting-status">
                                {translation.available ? (
                                    <span className="badge badge-success">
                                        <Check size={14} /> Ready
                                    </span>
                                ) : (
                                    <span className="badge badge-default">
                                        Not downloaded
                                    </span>
                                )}
                            </div>
                            <p className="model-note">7B parameters, Q4_K_M quantized</p>
                        </div>

                        <div className="setting-action">
                            {messages.translation && (
                                <p className="action-message">{messages.translation}</p>
                            )}
                            <button
                                className="btn btn-secondary"
                                onClick={downloadTranslationModel}
                                disabled={installing === 'translation' || translation.available}
                            >
                                {installing === 'translation' ? (
                                    <>
                                        <RefreshCw size={16} className="spinning" />
                                        Downloading...
                                    </>
                                ) : translation.available ? (
                                    <>
                                        <Check size={16} />
                                        Downloaded ({translation.size_gb}GB)
                                    </>
                                ) : (
                                    <>
                                        <Download size={16} />
                                        Pre-download (~4.4GB)
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </section>

                {/* System Info */}
                <section className="settings-section">
                    <h2>
                        {getPlatformIcon()}
                        System Info
                    </h2>
                    <div className="system-info-grid">
                        <div className="info-item">
                            <span>Platform</span>
                            <code>{hardware?.system?.platform || status?.platform || 'Unknown'}</code>
                        </div>
                        <div className="info-item">
                            <span>Python</span>
                            <code>{hardware?.system?.python_version || status?.python_version?.split(' ')[0] || 'Unknown'}</code>
                        </div>
                        <div className="info-item">
                            <span>Architecture</span>
                            <code>{hardware?.system?.architecture || 'Unknown'}</code>
                        </div>
                    </div>
                </section>

                {/* Storage & Uninstall */}
                <section className="settings-section">
                    <h2
                        className="collapsible"
                        onClick={() => setShowUninstall(!showUninstall)}
                    >
                        <Trash2 size={20} />
                        Storage & Uninstall
                        <ChevronDown size={18} className={`chevron ${showUninstall ? 'open' : ''}`} />
                    </h2>

                    <div className={`collapsible-content ${showUninstall ? 'open' : ''}`}>
                        {/* Storage Usage */}
                        {storageInfo && (
                            <div className="setting-card">
                                <div className="setting-info">
                                    <h4>Storage Usage</h4>
                                    <div className="storage-grid">
                                        <div className="storage-item">
                                            <span>Models</span>
                                            <span>{storageInfo.models?.size_mb || 0} MB</span>
                                        </div>
                                        <div className="storage-item">
                                            <span>Projects ({storageInfo.projects?.count || 0})</span>
                                            <span>{storageInfo.projects?.size_mb || 0} MB</span>
                                        </div>
                                        <div className="storage-item">
                                            <span>Virtual Environment</span>
                                            <span>{storageInfo.venv?.size_mb || 0} MB</span>
                                        </div>
                                        <div className="storage-item total">
                                            <span>Total</span>
                                            <span>{storageInfo.total_size_mb || 0} MB</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Cleanup Actions */}
                        <div className="setting-card danger">
                            <div className="setting-info">
                                <h4>Cleanup Options</h4>
                                <p className="muted">Free up space by removing downloaded content</p>
                            </div>

                            {messages.uninstall && (
                                <p className="action-message">{messages.uninstall}</p>
                            )}

                            <div className="cleanup-buttons">
                                <button
                                    className="btn btn-danger-outline"
                                    onClick={deleteModels}
                                    disabled={installing === 'delete-models'}
                                >
                                    <Trash2 size={14} />
                                    Delete Models
                                </button>
                                <button
                                    className="btn btn-danger-outline"
                                    onClick={deleteProjects}
                                    disabled={installing === 'delete-projects'}
                                >
                                    <Trash2 size={14} />
                                    Delete All Projects
                                </button>
                                <button
                                    className="btn btn-danger"
                                    onClick={startUninstall}
                                >
                                    <Trash2 size={14} />
                                    Uninstall App
                                </button>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    )
}

export default Settings
