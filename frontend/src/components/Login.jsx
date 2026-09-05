import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import apiClient from '../services/api'
import './Login.css'
import logo from '../assets/images/logo-green.png'
import { toast } from './ToastContainer'

function Login() {
  const navigate = useNavigate()
  const [bloqueado, setBloqueado] = useState(false)
  const [minutosEspera, setMinutosEspera] = useState(30)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm()

  const onSubmit = async (data) => {
    if (bloqueado) return

    try {
      const response = await apiClient.post('/api/auth/login/', {
        username: data.username,
        password: data.password,
      })

      if (response.data.success) {
        if (response.data.access) {
          localStorage.setItem('access_token', response.data.access)
        }
        if (response.data.refresh) {
          localStorage.setItem('refresh_token', response.data.refresh)
        }
        localStorage.setItem('user', JSON.stringify(response.data.user))
        toast.success('Inicio de sesión exitoso')
        navigate('/dashboard')
      } else {
        toast.error(response.data.error || 'Credenciales incorrectas')
      }
    } catch (error) {
      const status = error.response?.status
      const data = error.response?.data

      if (status === 429) {
        // Cuenta bloqueada por Axes
        setBloqueado(true)
        const espera = data?.espera_minutos || 30
        setMinutosEspera(espera)
        toast.error(`Cuenta bloqueada. Intenta de nuevo en ${espera} minutos.`)
        // Desbloquear en el frontend después del tiempo indicado
        setTimeout(() => setBloqueado(false), espera * 60 * 1000)
      } else if (status === 401) {
        toast.error('Usuario o contraseña incorrectos')
      } else if (status === 403) {
        toast.error('No tienes permisos para acceder al sistema')
      } else {
        const msg = data?.error || error.message || 'Error al conectar con el servidor'
        toast.error(msg)
      }
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <img src={logo} alt="EcoAlerta" />
          <p>Sistema de Reportes Ciudadanos Urbanos</p>
        </div>

        {bloqueado && (
          <div className="login-bloqueado">
            <span>Cuenta bloqueada temporalmente ({minutosEspera} min)</span>
            <p>Demasiados intentos fallidos. Contacta al administrador si necesitas acceso inmediato.</p>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} role="form" aria-label="Formulario de inicio de sesión">
          <div className="form-group">
            <label htmlFor="username">Usuario</label>
            <input
              id="username"
              type="text"
              {...register('username', {
                required: 'El usuario es requerido',
                minLength: { value: 3, message: 'Mínimo 3 caracteres' }
              })}
              placeholder="inspector"
              className={errors.username ? 'error' : ''}
              disabled={bloqueado}
              autoComplete="username"
            />
            {errors.username && (
              <span className="error-message" role="alert">{errors.username.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              {...register('password', {
                required: 'La contraseña es requerida',
                minLength: { value: 4, message: 'Mínimo 4 caracteres' }
              })}
              placeholder="••••••••"
              className={errors.password ? 'error' : ''}
              disabled={bloqueado}
              autoComplete="current-password"
            />
            {errors.password && (
              <span className="error-message" role="alert">{errors.password.message}</span>
            )}
          </div>

          <button
            type="submit"
            className="btn-login"
            disabled={isSubmitting || bloqueado}
            aria-busy={isSubmitting}
          >
            <span>{isSubmitting ? 'Conectando...' : 'Iniciar Sesión'}</span>
          </button>
        </form>

        <div className="login-footer">
          <p>¿Eres ciudadano?</p>
          <button
            className="btn-ciudadano"
            onClick={() => navigate('/ciudadano')}
          >
            Reportar un problema
          </button>
        </div>
      </div>
    </div>
  )
}

export default Login
