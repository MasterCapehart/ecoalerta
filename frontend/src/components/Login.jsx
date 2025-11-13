import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_ENDPOINTS } from '../config'
import { saveAuthData } from '../services/auth'
import './Login.css'
import logo from '../assets/images/logo-green.png'

function Login() {
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const response = await fetch(API_ENDPOINTS.JWT_LOGIN, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: usuario, password: password }),
      })

      const data = await response.json()

      if (response.ok && data.access && data.user) {
        // Verificar que el usuario sea inspector o admin
        if (data.user.tipo === 'inspector' || data.user.tipo === 'admin') {
          // Guardar tokens y datos del usuario
          saveAuthData(data.access, data.refresh, data.user)
          navigate('/dashboard')
        } else {
          setError('No tienes permisos para acceder. Solo inspectores y administradores pueden acceder.')
        }
      } else {
        setError(data.detail || data.error || 'Credenciales incorrectas')
      }
    } catch (error) {
      console.error('Error al conectar con el servidor:', error)
      setError('Error al conectar con el servidor. Verifica que el backend esté corriendo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <img src= {logo} alt="green-logo" />
          <p>Sistema de Monitoreo de Vertederos</p>
        </div>
        
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Usuario</label>
            <input
              type="text"
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              placeholder="inspector"
              required
            />
          </div>

          <div className="form-group">
            <label>Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="****"
              required
            />
          </div>

          {error && (
            <div style={{
              color: '#ff6b6b',
              fontSize: '14px',
              marginBottom: '10px',
              padding: '10px',
              backgroundColor: '#ffe0e0',
              borderRadius: '4px'
            }}>
              {error}
            </div>
          )}
          <button type="submit" className="btn-login" disabled={loading}>
            {loading ? 'Conectando...' : 'Iniciar Sesión'}
          </button>
        </form>

        <div className="login-footer">
          <p>¿Eres ciudadano?</p>
          <button 
            className="btn-ciudadano"
            onClick={() => navigate('/reporte')}
          >
            Reportar Vertedero
          </button>
        </div>
      </div>
    </div>
  )
}

export default Login