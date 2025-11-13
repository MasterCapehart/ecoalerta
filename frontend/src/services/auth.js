/**
 * Servicio de autenticación con JWT
 */

const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'

/**
 * Guardar tokens y datos del usuario
 */
export const saveAuthData = (accessToken, refreshToken, user) => {
  localStorage.setItem(TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

/**
 * Obtener token de acceso
 */
export const getAccessToken = () => {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * Obtener refresh token
 */
export const getRefreshToken = () => {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

/**
 * Obtener datos del usuario
 */
export const getUser = () => {
  const userStr = localStorage.getItem(USER_KEY)
  return userStr ? JSON.parse(userStr) : null
}

/**
 * Verificar si el usuario está autenticado
 */
export const isAuthenticated = () => {
  return !!getAccessToken()
}

/**
 * Cerrar sesión
 */
export const logout = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * Obtener headers con autenticación
 */
export const getAuthHeaders = () => {
  const token = getAccessToken()
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  }
}

/**
 * Refrescar token
 */
export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('No refresh token available')
  }

  try {
    const API_URL = import.meta.env.VITE_API_URL || 
      (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
        ? 'https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net'
        : 'http://localhost:8000')
    
    const response = await fetch(`${API_URL}/api/auth/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
    })

    if (!response.ok) {
      throw new Error('Failed to refresh token')
    }

    const data = await response.json()
    localStorage.setItem(TOKEN_KEY, data.access)
    return data.access
  } catch (error) {
    console.error('Error refreshing token:', error)
    logout()
    throw error
  }
}

