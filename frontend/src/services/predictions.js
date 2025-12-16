import { API_ENDPOINTS } from '../config'

export async function fetchCategorias() {
  const response = await fetch(API_ENDPOINTS.CATEGORIAS)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || 'No fue posible cargar las categorías')
  }
  return response.json()
}

export async function requestPrediction(payload) {
  const response = await fetch(API_ENDPOINTS.PREDICCIONES, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const text = await response.text()
    const error = new Error(text || `Error ${response.status}`)
    error.status = response.status
    throw error
  }

  return response.json()
}

