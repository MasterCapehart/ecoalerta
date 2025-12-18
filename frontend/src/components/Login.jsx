import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../services/api'
import './Login.css'
import logo from '../assets/images/logo-green.png'
import { toast } from './ToastContainer'

function Login() {
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const response = await apiClient.post('/api/auth/login/', {
        username: usuario,
        password: password,
      })

      if (response.data.success) {
        // Guardar tokens JWT
        if (response.data.access) {
          localStorage.setItem('access_token', response.data.access)
        }
        if (response.data.refresh) {
          localStorage.setItem('refresh_token', response.data.refresh)
        }
        
        // Guardar datos del usuario
        localStorage.setItem('user', JSON.stringify(response.data.user))
        
        toast.success('Inicio de sesión exitoso')
        navigate('/dashboard')
      } else {
        toast.error(response.data.error || 'Credenciales incorrectas')
      }
    } catch (error) {
      toast.error(error.message || 'Error al conectar con el servidor')
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

          <button type="submit" className="btn-login" disabled={loading}>
            <span>{loading ? 'Conectando...' : 'Iniciar Sesión'}</span>
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
