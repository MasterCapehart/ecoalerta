import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_ENDPOINTS } from '../config'
import './Login.css'
import logo from '../assets/images/logo-green.png'

function Login() {
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const response = await fetch(API_ENDPOINTS.LOGIN, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: usuario, password: password }),
      })

      const data = await response.json()

      if (data.success) {
        // Guardar datos del usuario en localStorage
        localStorage.setItem('user', JSON.stringify(data.user))
        navigate('/dashboard')
      } else {
        alert(data.error || 'Credenciales incorrectas')
      }
    } catch (error) {
      console.error('Error al conectar con el servidor:', error)
      alert('Error al conectar con el servidor. Verifica que el backend esté corriendo.')
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
