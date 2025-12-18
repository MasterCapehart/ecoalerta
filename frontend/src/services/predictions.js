import apiClient from './api'
import { API_ROUTES } from '../config'

export async function fetchCategorias() {
  const response = await apiClient.get(API_ROUTES.CATEGORIAS)
  return response.data
}

export async function requestPrediction(payload) {
  const response = await apiClient.post(API_ROUTES.PREDICCIONES, payload)
  return response.data
}

