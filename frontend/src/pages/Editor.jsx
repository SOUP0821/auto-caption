import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
    ArrowLeft, Play, Pause, Volume2, VolumeX,
    Languages, Wand2, Download, Edit3, Check, X,
    Clock, Loader, AlertCircle, Cpu, Zap, FolderOpen,
    Maximize, MoreVertical, Save, Palette
} from 'lucide-react'
import './Editor.css'

const API_BASE = 'http://localhost:8000/api'

const WHISPER_MODELS = [
    { id: 'tiny', name: 'Tiny', speed: 'Very Fast', desc: 'Fastest' },
    { id: 'base', name: 'Base', speed: 'Fast', desc: 'Fast' },
    { id: 'small', name: 'Small', speed: 'Medium', desc: 'Balanced' },
    { id: 'medium', name: 'Medium', speed: 'Slow', desc: 'Accurate' },
    { id: 'large-v3-turbo', name: 'Large V3 Turbo', speed: 'Balanced', desc: 'Best' },
    { id: 'large-v3', name: 'Large V3', speed: 'Very Slow', desc: 'Max Accuracy' },
]

const LANGUAGES = [
    'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese',
    'Russian', 'Japanese', 'Korean', 'Chinese', 'Arabic', 'Hindi',
    'Dutch', 'Polish', 'Turkish', 'Vietnamese', 'Thai', 'Indonesian'
]

function Editor() {
    const { projectId } = useParams()
    const navigate = useNavigate()

    // Project state
    const [project, setProject] = useState(null)
    const [loading, setLoading] = useState(true)
    const [deviceInfo, setDeviceInfo] = useState(null)

    // Video state
    const videoRef = useRef(null)
    const [isPlaying, setIsPlaying] = useState(false)
    const [currentTime, setCurrentTime] = useState(0)
    const [duration, setDuration] = useState(0)
    const [isMuted, setIsMuted] = useState(false)
    const [playbackRate, setPlaybackRate] = useState(1.0)
    const [showSpeedMenu, setShowSpeedMenu] = useState(false)

    // Player UI state
    const [showControls, setShowControls] = useState(true)
    const [isDragging, setIsDragging] = useState(false)
    const controlsTimeoutRef = useRef(null)
    const playerRef = useRef(null)
    const timelineRef = useRef(null)

    // Caption Style
    const [showStyleMenu, setShowStyleMenu] = useState(false)
    const [captionStyle, setCaptionStyle] = useState({
        fontSize: 18,
        color: '#ffffff',
        backgroundColor: 'rgba(0,0,0,0.85)',
        bottom: 10
    })

    // Segments state
    const [segments, setSegments] = useState([])
    const [translatedSegments, setTranslatedSegments] = useState(null)
    const [showTranslated, setShowTranslated] = useState(false)
    const [activeSegmentId, setActiveSegmentId] = useState(null)
    const [editingSegmentId, setEditingSegmentId] = useState(null)
    const [editText, setEditText] = useState('')

    // Transcription/Translation state
    const [transcribing, setTranscribing] = useState(false)
    const [transcribeProgress, setTranscribeProgress] = useState(0)
    const [transcribeStatus, setTranscribeStatus] = useState('')
    const [translating, setTranslating] = useState(false)
    const [translateProgress, setTranslateProgress] = useState(0)
    const [translateStatus, setTranslateStatus] = useState('')
    const [translateCurrent, setTranslateCurrent] = useState(0)
    const [translateTotal, setTranslateTotal] = useState(0)
    const [translateRemaining, setTranslateRemaining] = useState(null)

    // Settings
    const [selectedModel, setSelectedModel] = useState('large-v3-turbo')
    const [targetLang, setTargetLang] = useState('Spanish')

    // Load project and device info
    useEffect(() => {
        loadProject()
        loadDeviceInfo()
    }, [projectId])

    const loadProject = async () => {
        try {
            const res = await fetch(`${API_BASE}/projects/${projectId}`)
            if (!res.ok) {
                navigate('/dashboard')
                return
            }
            const data = await res.json()
            setProject(data)
            setSegments(data.segments || [])
            setTranslatedSegments(data.translated_segments || null)
            if (data.whisper_model) setSelectedModel(data.whisper_model)
        } catch (err) {
            console.error('Failed to load project:', err)
            navigate('/dashboard')
        } finally {
            setLoading(false)
        }
    }

    const loadDeviceInfo = async () => {
        try {
            const res = await fetch(`${API_BASE}/system/status`)
            const data = await res.json()
            setDeviceInfo(data.cuda)
        } catch (err) {
            console.error('Failed to load device info:', err)
        }
    }

    // Video time update
    useEffect(() => {
        const video = videoRef.current
        if (!video) return

        const handleTimeUpdate = () => {
            setCurrentTime(video.currentTime)

            const currentSegments = showTranslated && translatedSegments ? translatedSegments : segments
            const active = currentSegments.find(
                seg => video.currentTime >= seg.start && video.currentTime <= seg.end
            )
            setActiveSegmentId(active?.id || null)
        }

        const handleLoadedMetadata = () => {
            setDuration(video.duration)
        }

        const handlePlay = () => setIsPlaying(true)
        const handlePause = () => setIsPlaying(false)

        video.addEventListener('timeupdate', handleTimeUpdate)
        video.addEventListener('loadedmetadata', handleLoadedMetadata)
        video.addEventListener('play', handlePlay)
        video.addEventListener('pause', handlePause)

        return () => {
            video.removeEventListener('timeupdate', handleTimeUpdate)
            video.removeEventListener('loadedmetadata', handleLoadedMetadata)
            video.removeEventListener('play', handlePlay)
            video.removeEventListener('pause', handlePause)
        }
    }, [segments, translatedSegments, showTranslated])

    // Transcription
    const startTranscription = async () => {
        setTranscribing(true)
        setTranscribeProgress(0)
        setTranscribeStatus('Starting...')

        try {
            await fetch(`${API_BASE}/transcribe`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    model_size: selectedModel,
                    language: null  // Auto-detect
                })
            })

            // Poll for progress
            const pollInterval = setInterval(async () => {
                try {
                    const res = await fetch(`${API_BASE}/transcribe/${projectId}/progress`)
                    const data = await res.json()

                    setTranscribeProgress(data.progress || 0)
                    setTranscribeStatus(data.status || '')

                    if (data.status === 'complete') {
                        clearInterval(pollInterval)
                        setSegments(data.segments || [])
                        setTranscribing(false)
                        loadProject()
                    } else if (data.status?.startsWith('error')) {
                        clearInterval(pollInterval)
                        setTranscribing(false)
                        alert('Transcription failed: ' + data.status)
                    }
                } catch (err) {
                    // Continue polling
                }
            }, 500)
        } catch (err) {
            setTranscribing(false)
            alert('Failed to start transcription')
        }
    }

    // Translation
    const startTranslation = async () => {
        if (segments.length === 0) {
            alert('No segments to translate. Run transcription first.')
            return
        }

        setTranslating(true)
        setTranslateProgress(0)
        setTranslateStatus('Starting...')
        setTranslateCurrent(0)
        setTranslateTotal(segments.length)

        // Detect source language from project or default
        const sourceLang = project?.source_language || 'Auto'

        try {
            await fetch(`${API_BASE}/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    source_lang: sourceLang,
                    target_lang: targetLang
                })
            })

            const pollInterval = setInterval(async () => {
                try {
                    const res = await fetch(`${API_BASE}/translate/${projectId}/progress`)
                    const data = await res.json()

                    setTranslateProgress(data.progress || 0)
                    setTranslateStatus(data.status || '')
                    setTranslateCurrent(data.current || 0)
                    setTranslateTotal(data.total || segments.length)
                    setTranslateRemaining(data.remaining)

                    if (data.status === 'complete') {
                        clearInterval(pollInterval)
                        setTranslatedSegments(data.segments || [])
                        setShowTranslated(true)
                        setTranslating(false)
                        loadProject()
                    } else if (data.status?.startsWith('error')) {
                        clearInterval(pollInterval)
                        setTranslating(false)
                        alert('Translation failed: ' + data.status)
                    }
                } catch (err) {
                    // Continue polling
                }
            }, 500)
        } catch (err) {
            setTranslating(false)
            alert('Failed to start translation')
        }
    }

    // Segment editing
    const startEditing = (segment) => {
        setEditingSegmentId(segment.id)
        setEditText(segment.text)
    }

    const saveEdit = async () => {
        try {
            await fetch(`${API_BASE}/segments`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    segment_id: editingSegmentId,
                    text: editText,
                    is_translated: showTranslated
                })
            })

            if (showTranslated && translatedSegments) {
                setTranslatedSegments(prev =>
                    prev.map(s => s.id === editingSegmentId ? { ...s, text: editText } : s)
                )
            } else {
                setSegments(prev =>
                    prev.map(s => s.id === editingSegmentId ? { ...s, text: editText } : s)
                )
            }
        } catch (err) {
            console.error('Failed to save:', err)
        }
        setEditingSegmentId(null)
    }

    const cancelEdit = () => {
        setEditingSegmentId(null)
        setEditText('')
    }

    // Jump to segment
    const jumpToSegment = (segment) => {
        if (videoRef.current) {
            videoRef.current.currentTime = segment.start
        }
    }

    // Export SRT
    const exportSRT = async () => {
        if (segments.length === 0) {
            alert('No segments to export')
            return
        }

        try {
            const url = `${API_BASE}/projects/${projectId}/export/srt?translated=${showTranslated}`
            const res = await fetch(url)

            if (!res.ok) {
                const errorText = await res.text()
                throw new Error(errorText || 'Export failed')
            }

            const srtContent = await res.text()

            // Ensure we got actual SRT content
            if (!srtContent || srtContent.length < 10) {
                throw new Error('Empty or invalid SRT content received')
            }

            // Create proper filename
            const filename = `${(project?.name || 'subtitles').replace(/[^a-z0-9]/gi, '_')}${showTranslated ? '_translated' : ''}.srt`

            // Create blob and download using modern approach
            const blob = new Blob([srtContent], { type: 'application/x-subrip' })
            const downloadUrl = window.URL.createObjectURL(blob)

            // Create and trigger download
            const link = document.createElement('a')
            link.href = downloadUrl
            link.setAttribute('download', filename)
            link.style.display = 'none'
            document.body.appendChild(link)
            link.click()

            // Cleanup
            setTimeout(() => {
                document.body.removeChild(link)
                window.URL.revokeObjectURL(downloadUrl)
            }, 100)

        } catch (err) {
            console.error('Export failed:', err)
            alert('Failed to export SRT file: ' + err.message)
        }
    }

    // Save and Open Folder
    const openFolder = async () => {
        try {
            await fetch(`${API_BASE}/projects/${projectId}/open-folder`, { method: 'POST' })
        } catch (err) {
            console.error('Failed to open folder:', err)
        }
    }

    const saveToDisk = async () => {
        try {
            const res = await fetch(`${API_BASE}/projects/${projectId}/save-srt?translated=${showTranslated}`, { method: 'POST' })
            const data = await res.json()
            if (data.success) {
                alert(`Saved to: ${data.path}`)
                openFolder()
            } else {
                alert('Failed to save file')
            }
        } catch (err) {
            alert('Error saving file')
        }
    }

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return

            switch (e.code) {
                case 'Space':
                    e.preventDefault()
                    togglePlay()
                    break
                case 'ArrowLeft':
                    e.preventDefault()
                    if (videoRef.current) videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime - 5)
                    break
                case 'ArrowRight':
                    e.preventDefault()
                    if (videoRef.current) videoRef.current.currentTime = Math.min(duration, videoRef.current.currentTime + 5)
                    break
            }
        }
        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [isPlaying, duration])

    // Video controls
    const togglePlay = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause()
            } else {
                videoRef.current.play()
            }
        }
    }

    const toggleFullscreen = () => {
        if (document.fullscreenElement) {
            document.exitFullscreen()
        } else if (playerRef.current) {
            playerRef.current.requestFullscreen()
        }
    }

    const changeSpeed = (speed) => {
        if (videoRef.current) {
            videoRef.current.playbackRate = speed
            setPlaybackRate(speed)
            setShowSpeedMenu(false)
        }
    }

    // Player Visibility
    const handlePlayerMouseMove = () => {
        setShowControls(true)
        if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current)
        controlsTimeoutRef.current = setTimeout(() => {
            if (isPlaying) setShowControls(false)
        }, 2000)
    }

    // Seek Logic
    const calculateTime = (e) => {
        if (!timelineRef.current) return 0
        const rect = timelineRef.current.getBoundingClientRect()
        const percent = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1)
        return percent * duration
    }

    const handleTimelineMouseDown = (e) => {
        setIsDragging(true)
        if (videoRef.current) {
            const time = calculateTime(e)
            videoRef.current.currentTime = time
            setCurrentTime(time) // Instant UI update
        }

        const handleDrag = (moveEvent) => {
            if (videoRef.current) {
                const time = calculateTime(moveEvent)
                videoRef.current.currentTime = time
                setCurrentTime(time)
            }
        }

        const handleDragEnd = () => {
            setIsDragging(false)
            document.removeEventListener('mousemove', handleDrag)
            document.removeEventListener('mouseup', handleDragEnd)
        }

        document.addEventListener('mousemove', handleDrag)
        document.addEventListener('mouseup', handleDragEnd)
    }



    const toggleMute = () => {
        if (videoRef.current) {
            videoRef.current.muted = !isMuted
            setIsMuted(!isMuted)
        }
    }

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const formatRemaining = (seconds) => {
        if (!seconds || seconds <= 0) return ''
        if (seconds < 60) return `~${Math.round(seconds)}s left`
        return `~${Math.round(seconds / 60)}m left`
    }

    const getCurrentCaption = () => {
        const currentSegments = showTranslated && translatedSegments ? translatedSegments : segments
        const active = currentSegments.find(
            seg => currentTime >= seg.start && currentTime <= seg.end
        )
        return active?.text || ''
    }

    const displaySegments = showTranslated && translatedSegments ? translatedSegments : segments

    if (loading) {
        return (
            <div className="editor-loading">
                <div className="spinner"></div>
                <p>Loading project...</p>
            </div>
        )
    }

    return (
        <div className="editor-page">
            {/* Header */}
            <header className="editor-header">
                <button className="btn btn-ghost" onClick={() => navigate('/dashboard')}>
                    <ArrowLeft size={18} />
                    Back
                </button>
                <h2>{project?.name || 'Untitled Project'}</h2>
                <div className="header-right">
                    {/* Device indicator */}
                    <div className="device-badge">
                        {deviceInfo?.available ? (
                            <>
                                <Zap size={14} />
                                <span>{deviceInfo.device_name?.split(' ')[0] || 'GPU'}</span>
                            </>
                        ) : (
                            <>
                                <Cpu size={14} />
                                <span>CPU</span>
                            </>
                        )}
                    </div>

                    <button
                        className="btn btn-secondary"
                        onClick={openFolder}
                        title="Open Output Folder"
                    >
                        <FolderOpen size={16} />
                    </button>

                    <button
                        className="btn btn-secondary"
                        onClick={saveToDisk}
                        disabled={segments.length === 0}
                        title="Save SRT to Disk"
                    >
                        <Save size={16} />
                    </button>

                    <button
                        className="btn btn-primary"
                        onClick={exportSRT}
                        disabled={segments.length === 0}
                    >
                        <Download size={16} />
                        Export
                    </button>
                </div>
            </header>

            <div className="editor-layout">
                {/* Content Area - Video on left, Captions on right */}
                <div className="content-area">
                    {/* Video Panel */}
                    <div className="video-panel">
                        <div
                            className="player-wrapper"
                            ref={playerRef}
                            onMouseMove={handlePlayerMouseMove}
                            onMouseLeave={() => setShowControls(false)}
                        >
                            <video
                                ref={videoRef}
                                src={`${API_BASE}/projects/${projectId}/video`}
                                onClick={togglePlay}
                            />

                            {/* Caption Overlay */}
                            {getCurrentCaption() && (
                                <div
                                    className="caption-overlay"
                                    style={{
                                        fontSize: `${captionStyle.fontSize}px`,
                                        color: captionStyle.color,
                                        bottom: `${captionStyle.bottom}%`,
                                        transform: 'translateX(-50%)'
                                    }}
                                >
                                    <span style={{ backgroundColor: captionStyle.backgroundColor }}>
                                        {getCurrentCaption()}
                                    </span>
                                </div>
                            )}

                            {/* Video Controls (Overlay) */}
                            <div className={`video-controls ${!showControls ? 'hidden' : ''}`}>
                                <button className="btn btn-icon btn-ghost" onClick={togglePlay}>
                                    {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                                </button>

                                <div
                                    className="timeline"
                                    ref={timelineRef}
                                    onMouseDown={handleTimelineMouseDown}
                                >
                                    <div className="timeline-progress" style={{ width: `${(currentTime / duration) * 100}%` }} />
                                    {displaySegments.map(seg => (
                                        <div
                                            key={seg.id}
                                            className="timeline-marker"
                                            style={{
                                                left: `${(seg.start / duration) * 100}%`,
                                                width: `${((seg.end - seg.start) / duration) * 100}%`
                                            }}
                                        />
                                    ))}
                                </div>

                                <span className="time-display">
                                    {formatTime(currentTime)} / {formatTime(duration)}
                                </span>

                                <div className="video-controls-right">
                                    {/* Style Editor */}
                                    <div className="speed-control">
                                        <button
                                            className="btn btn-icon btn-ghost"
                                            onClick={() => setShowStyleMenu(!showStyleMenu)}
                                            title="Caption Style"
                                        >
                                            <Palette size={18} />
                                        </button>
                                        {showStyleMenu && (
                                            <div className="style-menu" onClick={e => e.stopPropagation()}>
                                                <div className="style-control-group">
                                                    <label>Font Size ({captionStyle.fontSize}px)</label>
                                                    <input
                                                        type="range"
                                                        min="12" max="48"
                                                        value={captionStyle.fontSize}
                                                        onChange={e => setCaptionStyle({ ...captionStyle, fontSize: parseInt(e.target.value) })}
                                                        className="slider-input"
                                                    />
                                                </div>
                                                <div className="style-control-group">
                                                    <label>Vertical Position</label>
                                                    <input
                                                        type="range"
                                                        min="5" max="90"
                                                        value={captionStyle.bottom}
                                                        onChange={e => setCaptionStyle({ ...captionStyle, bottom: parseInt(e.target.value) })}
                                                        className="slider-input"
                                                    />
                                                </div>
                                                <div className="style-control-group">
                                                    <label>Colors</label>
                                                    <div className="color-picker-row">
                                                        <input
                                                            type="color"
                                                            value={captionStyle.color}
                                                            onChange={e => setCaptionStyle({ ...captionStyle, color: e.target.value })}
                                                            className="color-input"
                                                            title="Text Color"
                                                        />
                                                        <input
                                                            type="color"
                                                            value={captionStyle.backgroundColor.startsWith('#') ? captionStyle.backgroundColor : '#000000'}
                                                            onChange={e => setCaptionStyle({ ...captionStyle, backgroundColor: e.target.value })}
                                                            className="color-input"
                                                            title="Background Color"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Speed Control */}
                                    <div className="speed-control">
                                        <button
                                            className="btn btn-icon btn-ghost speed-btn"
                                            onClick={() => setShowSpeedMenu(!showSpeedMenu)}
                                        >
                                            {playbackRate}x
                                        </button>
                                        {showSpeedMenu && (
                                            <div className="speed-menu">
                                                {[0.5, 1.0, 1.25, 1.5, 2.0].map(speed => (
                                                    <button
                                                        key={speed}
                                                        className={playbackRate === speed ? 'active' : ''}
                                                        onClick={() => changeSpeed(speed)}
                                                    >
                                                        {speed}x
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    <button className="btn btn-icon btn-ghost" onClick={toggleMute}>
                                        {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
                                    </button>

                                    <button className="btn btn-icon btn-ghost" onClick={toggleFullscreen}>
                                        <Maximize size={18} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Segments Panel - Right sidebar */}
                    <div className="segments-panel">
                        <div className="segments-header">
                            <h3>Captions ({displaySegments.length})</h3>
                            {translatedSegments && (
                                <div className="segment-toggle">
                                    <button
                                        className={`toggle-btn ${!showTranslated ? 'active' : ''}`}
                                        onClick={() => setShowTranslated(false)}
                                    >
                                        Original
                                    </button>
                                    <button
                                        className={`toggle-btn ${showTranslated ? 'active' : ''}`}
                                        onClick={() => setShowTranslated(true)}
                                    >
                                        Translated
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="segments-list">
                            {displaySegments.length === 0 ? (
                                <div className="empty-segments">
                                    <AlertCircle size={40} />
                                    <p>No captions yet</p>
                                    <span>Click "Transcribe" to generate captions</span>
                                </div>
                            ) : (
                                displaySegments.map(segment => (
                                    <div
                                        key={segment.id}
                                        className={`segment-item ${activeSegmentId === segment.id ? 'active' : ''}`}
                                        onClick={() => jumpToSegment(segment)}
                                    >
                                        <div className="segment-time">
                                            <Clock size={12} />
                                            {formatTime(segment.start)} - {formatTime(segment.end)}
                                        </div>

                                        {editingSegmentId === segment.id ? (
                                            <div className="segment-edit">
                                                <textarea
                                                    value={editText}
                                                    onChange={(e) => setEditText(e.target.value)}
                                                    autoFocus
                                                    onKeyDown={(e) => {
                                                        if (e.key === 'Enter' && !e.shiftKey) {
                                                            e.preventDefault()
                                                            saveEdit()
                                                        }
                                                        if (e.key === 'Escape') cancelEdit()
                                                    }}
                                                />
                                                <div className="edit-actions">
                                                    <button className="btn btn-icon btn-ghost" onClick={saveEdit}>
                                                        <Check size={14} />
                                                    </button>
                                                    <button className="btn btn-icon btn-ghost" onClick={cancelEdit}>
                                                        <X size={14} />
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="segment-text">
                                                <p>{segment.text}</p>
                                                <button
                                                    className="edit-btn"
                                                    onClick={(e) => {
                                                        e.stopPropagation()
                                                        startEditing(segment)
                                                    }}
                                                >
                                                    <Edit3 size={12} />
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Progress bars */}
                {transcribing && (
                    <div className="progress-section">
                        <div className="progress-header">
                            <span className="progress-label">{transcribeStatus}</span>
                            <span className="progress-value">{Math.round(transcribeProgress)}%</span>
                        </div>
                        <div className="progress-bar">
                            <div className="progress-bar-fill" style={{ width: `${transcribeProgress}%` }} />
                        </div>
                    </div>
                )}

                {translating && (
                    <div className="progress-section">
                        <div className="progress-header">
                            <span className="progress-label">
                                {translateStatus} ({translateCurrent}/{translateTotal})
                            </span>
                            <span className="progress-value">
                                {Math.round(translateProgress)}% {formatRemaining(translateRemaining)}
                            </span>
                        </div>
                        <div className="progress-bar">
                            <div className="progress-bar-fill" style={{ width: `${translateProgress}%` }} />
                        </div>
                    </div>
                )}

                {/* Actions Bar - Bottom */}
                <div className="actions-bar">
                    {/* Transcription controls */}
                    <div className="action-group">
                        <select
                            className="input select"
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            disabled={transcribing}
                        >
                            {WHISPER_MODELS.map(m => (
                                <option key={m.id} value={m.id}>
                                    {m.name} ({m.speed})
                                </option>
                            ))}
                        </select>

                        <button
                            className="btn btn-primary"
                            onClick={startTranscription}
                            disabled={transcribing}
                        >
                            {transcribing ? (
                                <Loader size={16} className="spinning" />
                            ) : (
                                <Wand2 size={16} />
                            )}
                            {transcribing ? 'Transcribing...' : segments.length > 0 ? 'Re-Transcribe' : 'Transcribe'}
                        </button>
                    </div>

                    <div className="action-divider" />

                    {/* Translation controls */}
                    <div className="action-group">
                        <span className="lang-label">Auto-detect →</span>
                        <select
                            className="input select"
                            value={targetLang}
                            onChange={(e) => setTargetLang(e.target.value)}
                            disabled={translating}
                        >
                            {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
                        </select>

                        <button
                            className="btn btn-secondary"
                            onClick={startTranslation}
                            disabled={translating || segments.length === 0}
                        >
                            {translating ? (
                                <Loader size={16} className="spinning" />
                            ) : (
                                <Languages size={16} />
                            )}
                            {translating ? 'Translating...' : 'Translate'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Editor
