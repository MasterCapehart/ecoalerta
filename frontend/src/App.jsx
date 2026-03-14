import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import Login from './components/Login'
import ReporteForm from './components/ReporteForm'
import DashboardMunicipal from './components/DashboardMunicipal'
import DashboardAdmin from './components/DashboardAdmin'
import PublicTracking from './components/PublicTracking'
import PublicDashboard from './components/PublicDashboard'
import ToastContainer from './components/ToastContainer'
import { toast } from './components/ToastContainer'
import { WebSocketProvider } from './context/WebSocketContext'
import OfflineService from './services/OfflineService'

function App() {
  useEffect(() => {
    const applySavedTheme = () => {
      let isDark = false
      try {
        isDark = JSON.parse(localStorage.getItem('darkMode') || 'false')
      } catch {
        isDark = false
      }
      document.documentElement.classList.toggle('dark-mode', isDark)
      document.body.classList.toggle('dark-mode', isDark)
    }

    const handleThemeChanged = () => applySavedTheme()
    const handleStorageChanged = (event) => {
      if (event.key === 'darkMode') {
        applySavedTheme()
      }
    }

    applySavedTheme()
    window.addEventListener('themeChanged', handleThemeChanged)
    window.addEventListener('storage', handleStorageChanged)

    return () => {
      window.removeEventListener('themeChanged', handleThemeChanged)
      window.removeEventListener('storage', handleStorageChanged)
    }
  }, [])

  // Inicializar OfflineService y listener de rate limiting
  useEffect(() => {
    OfflineService.init()

    const handleRateLimit = (event) => {
      const { waitTime, message } = event.detail
      toast.warning(message || `Demasiadas solicitudes. Espera ${waitTime} segundos.`)
    }

    window.addEventListener('rateLimitExceeded', handleRateLimit)

    return () => {
      window.removeEventListener('rateLimitExceeded', handleRateLimit)
    }
  }, [])

  return (
    <BrowserRouter>
      <WebSocketProvider>
        <ToastContainer />
        <Routes>
          <Route path="/" element={<Navigate to="/login" />} />
          <Route path="/login" element={<Login />} />
          <Route path="/reporte" element={<ReporteForm />} />
          <Route path="/dashboard" element={<DashboardMunicipal />} />
          <Route path="/admin" element={<DashboardAdmin />} />
          <Route path="/seguimiento/:codigo" element={<PublicTracking />} />
          <Route path="/seguimiento" element={<PublicTracking />} />
          <Route path="/public-dashboard" element={<PublicDashboard />} />
        </Routes>
      </WebSocketProvider>
    </BrowserRouter>
  )
}

export default App
