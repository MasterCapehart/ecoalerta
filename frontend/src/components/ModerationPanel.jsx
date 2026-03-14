import { useState, useEffect } from 'react'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './ModerationPanel.css'

function ModerationPanel() {
  const [comentarios, setComentarios] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadComentarios()
  }, [])

  const loadComentarios = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get(API_ROUTES.COMENTARIOS_PENDIENTES)
      setComentarios(response.data || [])
    } catch (error) {
      console.error('Error al cargar comentarios:', error)
      toast.error('Error al cargar comentarios pendientes')
    } finally {
      setLoading(false)
    }
  }

  const handleModerar = async (comentarioId, accion) => {
    try {
      await apiClient.post(
        `${API_ROUTES.MODERAR_COMENTARIO}${comentarioId}/moderar/`,
        { accion }
      )
      toast.success(`Comentario ${accion === 'aprobar' ? 'aprobado' : 'rechazado'}`)
      loadComentarios()
    } catch (error) {
      console.error('Error al moderar comentario:', error)
      toast.error('Error al moderar comentario')
    }
  }

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateString
    }
  }

  if (loading) {
    return (
      <div className="moderation-panel">
        <div className="moderation-header">
          <h2>Moderación de Comentarios</h2>
        </div>
        <div className="moderation-loading">Cargando comentarios...</div>
      </div>
    )
  }

  return (
    <div className="moderation-panel">
      <div className="moderation-header">
        <h2>Moderación de Comentarios</h2>
        <button onClick={loadComentarios} className="btn-refresh">
          Actualizar
        </button>
      </div>

      {comentarios.length === 0 ? (
        <div className="no-comments">
          <p>No hay comentarios pendientes de moderación</p>
        </div>
      ) : (
        <div className="comments-list">
          {comentarios.map(comentario => (
            <div key={comentario.id} className="comment-item">
              <div className="comment-header">
                <div className="comment-author">
                  <strong>{comentario.nombre}</strong>
                  {comentario.email && (
                    <span className="comment-email">{comentario.email}</span>
                  )}
                </div>
                <div className="comment-date">
                  {formatDate(comentario.fecha_creacion)}
                </div>
              </div>
              
              <div className="comment-content">
                <p>{comentario.comentario}</p>
              </div>
              
              <div className="comment-meta">
                <span className="reporte-code">
                  Reporte: {comentario.reporte_codigo || comentario.reporte}
                </span>
              </div>
              
              <div className="comment-actions">
                <button
                  onClick={() => handleModerar(comentario.id, 'aprobar')}
                  className="btn-approve"
                >
                  ✓ Aprobar
                </button>
                <button
                  onClick={() => handleModerar(comentario.id, 'rechazar')}
                  className="btn-reject"
                >
                  ✗ Rechazar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ModerationPanel
