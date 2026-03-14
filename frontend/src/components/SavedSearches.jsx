import { useState, useEffect } from 'react'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './SavedSearches.css'

function SavedSearches({ onLoadSearch, currentParams }) {
  const [busquedas, setBusquedas] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [nombreBusqueda, setNombreBusqueda] = useState('')

  useEffect(() => {
    loadBusquedas()
  }, [])

  const loadBusquedas = async () => {
    try {
      const response = await apiClient.get(API_ROUTES.BUSQUEDAS_GUARDADAS)
      setBusquedas(response.data || [])
    } catch (error) {
      console.error('Error al cargar búsquedas guardadas:', error)
    } finally {
      setLoading(false)
    }
  }

  const guardarBusqueda = async () => {
    if (!nombreBusqueda.trim()) {
      toast.error('El nombre es requerido')
      return
    }

    try {
      await apiClient.post(API_ROUTES.BUSQUEDAS_GUARDADAS, {
        nombre: nombreBusqueda,
        parametros: currentParams
      })
      toast.success('Búsqueda guardada exitosamente')
      setShowModal(false)
      setNombreBusqueda('')
      loadBusquedas()
    } catch (error) {
      console.error('Error al guardar búsqueda:', error)
      toast.error('Error al guardar la búsqueda')
    }
  }

  const eliminarBusqueda = async (id) => {
    if (!window.confirm('¿Estás seguro de eliminar esta búsqueda?')) {
      return
    }

    try {
      await apiClient.delete(`${API_ROUTES.BUSQUEDAS_GUARDADAS}${id}/`)
      toast.success('Búsqueda eliminada')
      loadBusquedas()
    } catch (error) {
      console.error('Error al eliminar búsqueda:', error)
      toast.error('Error al eliminar la búsqueda')
    }
  }

  const cargarBusqueda = (busqueda) => {
    if (onLoadSearch) {
      onLoadSearch(busqueda.parametros)
      toast.success(`Búsqueda "${busqueda.nombre}" cargada`)
    }
  }

  if (loading) {
    return <div className="saved-searches-loading">Cargando búsquedas...</div>
  }

  return (
    <div className="saved-searches">
      <div className="saved-searches-header">
        <h4>Búsquedas Guardadas</h4>
        <button 
          className="btn-save-search"
          onClick={() => setShowModal(true)}
        >
          Guardar búsqueda actual
        </button>
      </div>

      {busquedas.length === 0 ? (
        <p className="no-saved-searches">No hay búsquedas guardadas</p>
      ) : (
        <div className="saved-searches-list">
          {busquedas.map(busqueda => (
            <div key={busqueda.id} className="saved-search-item">
              <div 
                className="saved-search-content"
                onClick={() => cargarBusqueda(busqueda)}
              >
                <span className="saved-search-name">{busqueda.nombre}</span>
                <span className="saved-search-meta">
                  Usada {busqueda.veces_usado} veces
                </span>
              </div>
              <button
                className="btn-delete-search"
                onClick={() => eliminarBusqueda(busqueda.id)}
                title="Eliminar"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Guardar Búsqueda</h3>
            <input
              type="text"
              value={nombreBusqueda}
              onChange={(e) => setNombreBusqueda(e.target.value)}
              placeholder="Nombre de la búsqueda"
              className="modal-input"
              autoFocus
            />
            <div className="modal-actions">
              <button 
                className="btn-cancel"
                onClick={() => {
                  setShowModal(false)
                  setNombreBusqueda('')
                }}
              >
                Cancelar
              </button>
              <button 
                className="btn-save"
                onClick={guardarBusqueda}
              >
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SavedSearches
