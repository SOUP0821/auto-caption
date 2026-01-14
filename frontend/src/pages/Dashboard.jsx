import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FolderOpen, Clock, Trash2, Play, Film, Cpu, Zap, Settings } from 'lucide-react'
import './Dashboard.css'

const API_BASE = 'http://localhost:8000/api'

function Dashboard() {
    const navigate = useNavigate()
    const [projects, setProjects] = useState([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [uploadProgress, setUploadProgress] = useState(0)
    const [deviceInfo, setDeviceInfo] = useState(null)

    useEffect(() => {
        loadProjects()
        loadDeviceInfo()
    }, [])

    const loadProjects = async () => {
        try {
            const res = await fetch(`${API_BASE}/projects`)
            const data = await res.json()
            setProjects(data)
        } catch (err) {
            console.error('Failed to load projects:', err)
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

    const onDrop = useCallback(async (acceptedFiles) => {
        if (acceptedFiles.length === 0) return

        const file = acceptedFiles[0]
        setUploading(true)
        setUploadProgress(0)

        const formData = new FormData()
        formData.append('file', file)

        try {
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => Math.min(prev + 10, 90))
            }, 200)

            const res = await fetch(`${API_BASE}/projects/upload`, {
                method: 'POST',
                body: formData
            })

            clearInterval(progressInterval)
            setUploadProgress(100)

            if (res.ok) {
                const project = await res.json()
                setTimeout(() => {
                    navigate(`/editor/${project.id}`)
                }, 500)
            }
        } catch (err) {
            console.error('Upload failed:', err)
        } finally {
            setUploading(false)
        }
    }, [navigate])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'video/*': ['.mp4', '.mkv', '.avi', '.mov', '.webm']
        },
        multiple: false
    })

    const handleDeleteProject = async (e, projectId) => {
        e.stopPropagation()
        if (!confirm('Delete this project?')) return

        try {
            await fetch(`${API_BASE}/projects/${projectId}`, { method: 'DELETE' })
            setProjects(prev => prev.filter(p => p.id !== projectId))
        } catch (err) {
            console.error('Failed to delete:', err)
        }
    }

    const formatDate = (dateStr) => {
        const date = new Date(dateStr)
        const now = new Date()
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))

        if (diffDays === 0) return 'Today'
        if (diffDays === 1) return 'Yesterday'
        if (diffDays < 7) return `${diffDays} days ago`

        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }

    return (
        <div className="dashboard-page">
            {/* Header */}
            <header className="dashboard-header">
                <div className="header-content">
                    <div className="brand">
                        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                            <rect width="40" height="40" rx="8" fill="rgba(45, 212, 191, 0.1)" />
                            <text x="50%" y="50%" dy=".35em" textAnchor="middle" fill="var(--color-turquoise-400)" fontSize="20" fontWeight="bold" fontFamily="system-ui">AC</text>
                        </svg>
                        <h1>AutoCaption</h1>
                    </div>

                    {/* Device indicator - clickable for settings */}
                    <button
                        className="device-indicator"
                        onClick={() => navigate('/settings')}
                        title="Go to Settings"
                    >
                        {deviceInfo?.available ? (
                            <>
                                <Zap size={16} />
                                <span>{deviceInfo.device_name || 'GPU'}</span>
                            </>
                        ) : (
                            <>
                                <Cpu size={16} />
                                <span>CPU Mode</span>
                            </>
                        )}
                        <Settings size={14} className="settings-icon" />
                    </button>
                </div>
            </header>

            <main className="dashboard-main">
                {/* Upload Area */}
                <section className="upload-section animate-slide-up">
                    <div
                        {...getRootProps()}
                        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
                    >
                        <input {...getInputProps()} />

                        {uploading ? (
                            <div className="upload-progress">
                                <div className="progress-bar" style={{ width: 200 }}>
                                    <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }}></div>
                                </div>
                                <p>Uploading... {uploadProgress}%</p>
                            </div>
                        ) : (
                            <>
                                <div className="dropzone-icon">
                                    <Upload size={32} />
                                </div>
                                <h3>Drop your video here</h3>
                                <p>or click to browse files</p>
                                <span className="file-types">MP4, MKV, AVI, MOV, WebM</span>
                            </>
                        )}
                    </div>
                </section>

                {/* Projects Grid */}
                <section className="projects-section">
                    <div className="section-header">
                        <h2>
                            <FolderOpen size={20} />
                            Recent Projects
                        </h2>
                    </div>

                    {loading ? (
                        <div className="loading-state">
                            <div className="spinner"></div>
                            <p>Loading projects...</p>
                        </div>
                    ) : projects.length === 0 ? (
                        <div className="empty-state">
                            <Film size={48} />
                            <h3>No projects yet</h3>
                            <p>Upload a video to get started</p>
                        </div>
                    ) : (
                        <div className="projects-grid">
                            {projects.map((project, index) => (
                                <div
                                    key={project.id}
                                    className="project-card animate-slide-up"
                                    style={{ animationDelay: `${index * 50}ms` }}
                                    onClick={() => navigate(`/editor/${project.id}`)}
                                >
                                    <div className="project-thumbnail">
                                        {project.thumbnail_path ? (
                                            <img
                                                src={`${API_BASE}/projects/${project.id}/thumbnail`}
                                                alt={project.name}
                                                onError={(e) => {
                                                    e.target.style.display = 'none'
                                                    e.target.nextSibling.style.display = 'flex'
                                                }}
                                            />
                                        ) : null}
                                        <div className="thumbnail-placeholder" style={{ display: project.thumbnail_path ? 'none' : 'flex' }}>
                                            <Film size={28} />
                                        </div>
                                        <div className="play-overlay">
                                            <Play size={28} />
                                        </div>
                                    </div>

                                    <div className="project-info">
                                        <h4>{project.name}</h4>
                                        <div className="project-meta">
                                            <span className="project-date">
                                                <Clock size={12} />
                                                {formatDate(project.created_at)}
                                            </span>
                                            <span className={`badge badge-${project.status === 'translated' ? 'success' : project.status === 'transcribed' ? 'turquoise' : 'default'}`}>
                                                {project.status || 'New'}
                                            </span>
                                        </div>
                                    </div>

                                    <button
                                        className="delete-btn"
                                        onClick={(e) => handleDeleteProject(e, project.id)}
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </main>
        </div>
    )
}

export default Dashboard
