import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Installer from './pages/Installer'
import Dashboard from './pages/Dashboard'
import Editor from './pages/Editor'
import Settings from './pages/Settings'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [systemReady, setSystemReady] = useState(null) // null = checking
  const [systemStatus, setSystemStatus] = useState(null)
  const [backendAvailable, setBackendAvailable] = useState(null)

  useEffect(() => {
    checkSystem()
  }, [])

  const checkSystem = async () => {
    try {
      const res = await fetch(`${API_BASE}/system/status`)
      const data = await res.json()
      setSystemStatus(data)
      setSystemReady(data.ready)
      setBackendAvailable(true)
    } catch (err) {
      setSystemStatus({ error: 'Backend not available. Please start the backend server.' })
      setSystemReady(false)
      setBackendAvailable(false)
    }
  }

  const handleRefresh = () => {
    setSystemReady(null)
    checkSystem()
  }

  // Show loading while checking
  if (systemReady === null) {
    return (
      <div className="app-loading">
        <div className="loading-content">
          <div className="logo-loader">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              {/* Animated spinner circle */}
              <circle
                cx="32" cy="32" r="28"
                stroke="var(--color-bg-tertiary)"
                strokeWidth="3"
                fill="none"
              />
              <circle
                cx="32" cy="32" r="28"
                stroke="var(--color-turquoise-400)"
                strokeWidth="3"
                fill="none"
                strokeLinecap="round"
                strokeDasharray="120 60"
                className="spinner-arc"
              />
              {/* Static checkmark */}
              <path
                d="M20 32 L28 40 L44 24"
                stroke="var(--color-turquoise-400)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
            </svg>
          </div>
          <h2>AutoCaption</h2>
          <p className="text-muted">Checking system requirements...</p>
        </div>
        <style>{`
          .app-loading {
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--color-bg-primary);
          }
          .loading-content {
            text-align: center;
          }
          .loading-content h2 {
            margin-top: 20px;
            font-size: 1.5rem;
            background: linear-gradient(135deg, var(--color-turquoise-400), var(--color-turquoise-600));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
          }
          .loading-content p {
            margin-top: 6px;
            color: var(--color-text-muted);
            font-size: 0.9rem;
          }
          .logo-loader {
            display: flex;
            justify-content: center;
          }
          .spinner-arc {
            transform-origin: center;
            animation: rotate-spinner 1.2s linear infinite;
          }
          @keyframes rotate-spinner {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    )
  }

  // If backend is not available, show error
  if (!backendAvailable) {
    return (
      <div className="app-loading">
        <div className="loading-content">
          <div className="error-icon">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="28" stroke="var(--color-error)" strokeWidth="3" fill="none" />
              <path d="M22 22 L42 42 M42 22 L22 42" stroke="var(--color-error)" strokeWidth="3" strokeLinecap="round" />
            </svg>
          </div>
          <h2 style={{ color: 'var(--color-error)', fontSize: '1.25rem', marginTop: '20px' }}>Backend Not Available</h2>
          <p className="text-muted" style={{ fontSize: '0.9rem' }}>Please start the backend server first.</p>
          <div className="instructions">
            <code>cd backend</code>
            <code>venv\Scripts\activate</code>
            <code>python main.py</code>
          </div>
          <button className="btn btn-primary" onClick={handleRefresh} style={{ marginTop: 20 }}>
            Retry Connection
          </button>
        </div>
        <style>{`
          .app-loading {
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--color-bg-primary);
          }
          .loading-content {
            text-align: center;
            max-width: 360px;
          }
          .error-icon {
            display: flex;
            justify-content: center;
          }
          .instructions {
            margin-top: 20px;
            background: var(--color-bg-secondary);
            padding: 14px;
            border-radius: var(--radius-md);
          }
          .instructions code {
            display: block;
            color: var(--color-turquoise-400);
            font-family: var(--font-mono);
            font-size: 0.85rem;
            margin: 3px 0;
          }
        `}</style>
      </div>
    )
  }

  // Protected routes
  const ProtectedRoute = ({ children }) => {
    if (!systemReady) {
      return <Navigate to="/" replace />
    }
    return children
  }

  return (
    <Routes>
      <Route
        path="/"
        element={
          systemReady
            ? <Navigate to="/dashboard" replace />
            : <Installer
              status={systemStatus}
              onComplete={() => setSystemReady(true)}
              onRefresh={handleRefresh}
            />
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/editor/:projectId"
        element={
          <ProtectedRoute>
            <Editor />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
