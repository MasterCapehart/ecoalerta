import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import apiClient from '../services/api'
import './Login.css'
import logo from '../assets/images/logo-green.png'
import { toast } from './ToastContainer'

function Login() {
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm()

  const onSubmit = async (data) => {
    try {
      const response = await apiClient.post('/api/auth/login/', {
        username: data.username,
        password: data.password,
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
      const errorMessage = error.response?.data?.error || error.message || 'Error al conectar con el servidor'
      toast.error(errorMessage)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <img src={logo} alt="green-logo" />
          <p>Sistema de Monitoreo de Vertederos</p>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)} role="form" aria-label="Formulario de inicio de sesión">
          <div className="form-group">
            <label htmlFor="username">Usuario</label>
            <input
              id="username"
              type="text"
              {...register('username', {
                required: 'El usuario es requerido',
                minLength: {
                  value: 3,
                  message: 'El usuario debe tener al menos 3 caracteres'
                }
              })}
              placeholder="inspector"
              className={errors.username ? 'error' : ''}
              aria-required="true"
              aria-invalid={errors.username ? 'true' : 'false'}
              aria-describedby={errors.username ? 'username-error' : undefined}
            />
            {errors.username && (
              <span id="username-error" className="error-message" role="alert" aria-live="polite" style={{color: '#dc3545', fontSize: '12px', marginTop: '4px', display: 'block'}}>
                {errors.username.message}
              </span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              {...register('password', {
                required: 'La contraseña es requerida',
                minLength: {
                  value: 4,
                  message: 'La contraseña debe tener al menos 4 caracteres'
                }
              })}
              placeholder="****"
              className={errors.password ? 'error' : ''}
              aria-required="true"
              aria-invalid={errors.password ? 'true' : 'false'}
              aria-describedby={errors.password ? 'password-error' : undefined}
            />
            {errors.password && (
              <span id="password-error" className="error-message" role="alert" aria-live="polite" style={{color: '#dc3545', fontSize: '12px', marginTop: '4px', display: 'block'}}>
                {errors.password.message}
              </span>
            )}
          </div>

          <button type="submit" className="btn-login" disabled={isSubmitting} aria-busy={isSubmitting}>
            <span>{isSubmitting ? 'Conectando...' : 'Iniciar Sesión'}</span>
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
