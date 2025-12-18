// Servicio de API con manejo de tokens JWT y errores
import axios from 'axios'
import { API_URL } from '../config'

// Crear instancia de axios
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para agregar token a las peticiones
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para manejar respuestas y errores
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Si el error es 401 y no hemos intentado refrescar el token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/api/auth/refresh/`, {
            refresh: refreshToken,
          })

          const { access } = response.data
          localStorage.setItem('access_token', access)

          // Reintentar la petición original con el nuevo token
          originalRequest.headers.Authorization = `Bearer ${access}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Si el refresh falla, limpiar tokens y redirigir a login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Manejo de otros errores
    if (error.response) {
      // El servidor respondió con un código de estado fuera del rango 2xx
      const errorMessage =
        error.response.data?.message ||
        error.response.data?.error ||
        error.response.data?.details ||
        `Error ${error.response.status}: ${error.response.statusText}`

      return Promise.reject(new Error(errorMessage))
    } else if (error.request) {
      // La petición fue hecha pero no se recibió respuesta
      return Promise.reject(
        new Error('No se pudo conectar con el servidor. Verifica tu conexión.')
      )
    } else {
      // Algo más causó el error
      return Promise.reject(new Error(error.message || 'Error desconocido'))
    }
  }
)

export default apiClient

