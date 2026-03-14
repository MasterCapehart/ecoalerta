import { useState } from 'react'
import { useParams } from 'react-router-dom'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './PublicTracking.css'
import HistoryTimeline from './HistoryTimeline'

function PublicTracking() {
  const { codigo } = useParams()
  const [codigoSeguimiento, setCodigoSeguimiento] = useState(codigo || '')
  const [reporte, setReporte] = useState(null)
  const [comentarios, setComentarios] = useState([])
  const [loading, setLoading] = useState(false)
  const [nuevoComentario, setNuevoComentario] = useState({
    nombre: '',
    email: '',
    comentario: ''
  })

  const handleSearch = async () => {
    if (!codigoSeguimiento.trim()) {
      toast.error('Por favor ingresa un código de seguimiento')
      return
    }

    setLoading(true)
    try {
      const response = await apiClient.get(`${API_ROUTES.SEGUIMIENTO_PUBLICO}${codigoSeguimiento}/`)
      setReporte(response.data.reporte)
      setComentarios(response.data.comentarios || [])
    } catch (error) {
      console.error('Error al buscar reporte:', error)
      toast.error('No se encontró el reporte con ese código')
      setReporte(null)
      setComentarios([])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitComment = async (e) => {
    e.preventDefault()
    if (!reporte) return

    if (!nuevoComentario.nombre.trim() || !nuevoComentario.comentario.trim()) {
      toast.error('Por favor completa todos los campos requeridos')
      return
    }

    try {
      await apiClient.post(`${API_ROUTES.COMENTARIOS_PUBLICOS}${reporte.id}/comentarios/`, nuevoComentario)
      toast.success('Comentario enviado. Será moderado antes de publicarse.')
      setNuevoComentario({ nombre: '', email: '', comentario: '' })
      // Recargar comentarios
      const response = await apiClient.get(`${API_ROUTES.COMENTARIOS_PUBLICOS}${reporte.id}/comentarios/`)
      setComentarios(response.data || [])
    } catch (error) {
      console.error('Error al enviar comentario:', error)
      toast.error('Error al enviar el comentario')
    }
  }

  const getEstadoColor = (estado) => {
    const colors = {
      nuevo: '#2196F3',
      proceso: '#FF9800',
      resuelto: '#4CAF50',
      cerrado: '#9e9e9e'
    }
    return colors[estado] || '#666'
  }

  const getEstadoLabel = (estado) => {
    const labels = {
      nuevo: 'Nuevo',
      proceso: 'En Proceso',
      resuelto: 'Resuelto',
      cerrado: 'Cerrado'
    }
    return labels[estado] || estado
  }

  return (
    <div className="public-tracking">
      <div className="tracking-header">
        <h1>🔍 Seguimiento de Reporte</h1>
        <p>Ingresa tu código de seguimiento para ver el estado de tu reporte</p>
      </div>

      <div className="search-section">
        <div className="search-box">
          <input
            type="text"
            placeholder="Ej: ABC-1234"
            value={codigoSeguimiento}
            onChange={(e) => setCodigoSeguimiento(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="search-input"
          />
          <button onClick={handleSearch} className="btn-search" disabled={loading}>
            {loading ? 'Buscando...' : '🔍 Buscar'}
          </button>
        </div>
      </div>

      {reporte && (
        <div className="reporte-details">
          <div className="reporte-header">
            <div className="reporte-title">
              <h2>Reporte: {reporte.codigo_seguimiento}</h2>
              <span
                className="estado-badge"
                style={{ backgroundColor: getEstadoColor(reporte.estado) }}
              >
                {getEstadoLabel(reporte.estado)}
              </span>
            </div>
            <div className="reporte-meta">
              <p><strong>Fecha de creación:</strong> {new Date(reporte.fecha_creacion).toLocaleDateString('es-ES')}</p>
              {reporte.categoria_nombre && (
                <p><strong>Categoría:</strong> {reporte.categoria_nombre}</p>
              )}
            </div>
          </div>

          {reporte.descripcion && (
            <div className="reporte-section">
              <h3>Descripción</h3>
              <p>{reporte.descripcion}</p>
            </div>
          )}

          {reporte.direccion && (
            <div className="reporte-section">
              <h3>Ubicación</h3>
              <p>{reporte.direccion}</p>
            </div>
          )}

          {reporte.foto && (
            <div className="reporte-section">
              <h3>Fotografía</h3>
              <img src={reporte.foto} alt="Reporte" className="reporte-foto" />
            </div>
          )}

          <div className="reporte-section">
            <h3>Historial</h3>
            <HistoryTimeline reporteId={reporte.id} />
          </div>

          <div className="reporte-section">
            <h3>Comentarios</h3>
            {comentarios.length > 0 ? (
              <div className="comentarios-list">
                {comentarios.map(comentario => (
                  <div key={comentario.id} className="comentario-item">
                    <div className="comentario-header">
                      <strong>{comentario.nombre}</strong>
                      <span className="comentario-date">
                        {new Date(comentario.fecha_creacion).toLocaleDateString('es-ES')}
                      </span>
                    </div>
                    <p>{comentario.comentario}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-comentarios">No hay comentarios públicos aún</p>
            )}

            <form onSubmit={handleSubmitComment} className="comentario-form">
              <h4>Agregar Comentario</h4>
              <input
                type="text"
                placeholder="Tu nombre *"
                value={nuevoComentario.nombre}
                onChange={(e) => setNuevoComentario({ ...nuevoComentario, nombre: e.target.value })}
                required
              />
              <input
                type="email"
                placeholder="Tu email (opcional)"
                value={nuevoComentario.email}
                onChange={(e) => setNuevoComentario({ ...nuevoComentario, email: e.target.value })}
              />
              <textarea
                placeholder="Tu comentario *"
                value={nuevoComentario.comentario}
                onChange={(e) => setNuevoComentario({ ...nuevoComentario, comentario: e.target.value })}
                required
                rows="4"
              />
              <button type="submit" className="btn-submit">
                Enviar Comentario
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default PublicTracking

