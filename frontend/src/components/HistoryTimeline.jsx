import { useState, useEffect } from 'react'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './HistoryTimeline.css'
// Usar formato de fecha nativo si date-fns no está disponible
const formatDate = (date) => {
  try {
    // Intentar usar date-fns si está disponible
    if (typeof require !== 'undefined') {
      const { format } = require('date-fns')
      return format(new Date(date), "dd/MM/yyyy HH:mm")
    }
  } catch (e) {
    // Fallback a formato nativo
  }
  const d = new Date(date)
  return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getFullYear()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

function HistoryTimeline({ reporteId }) {
  const [historial, setHistorial] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (reporteId) {
      fetchHistorial()
    }
  }, [reporteId])

  const fetchHistorial = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get(`${API_ROUTES.HISTORIAL}${reporteId}/historial/`)
      setHistorial(response.data || [])
    } catch (error) {
      console.error('Error al cargar historial:', error)
      toast.error('Error al cargar el historial')
    } finally {
      setLoading(false)
    }
  }

  const getTipoIcon = (tipo) => {
    const icons = {
      estado: '🔄',
      asignacion: '👤',
      notas: '📝',
      prioridad: '⭐',
      tags: '🏷️',
      ubicacion: '📍',
      categoria: '📂',
      descripcion: '📄'
    }
    return icons[tipo] || '📌'
  }

  const getTipoLabel = (tipo) => {
    const labels = {
      estado: 'Cambio de Estado',
      asignacion: 'Asignación',
      notas: 'Notas Internas',
      prioridad: 'Prioridad',
      tags: 'Tags',
      ubicacion: 'Ubicación',
      categoria: 'Categoría',
      descripcion: 'Descripción'
    }
    return labels[tipo] || tipo
  }

  if (loading) {
    return (
      <div className="history-timeline loading">
        <p>Cargando historial...</p>
      </div>
    )
  }

  if (historial.length === 0) {
    return (
      <div className="history-timeline empty">
        <p>No hay historial disponible</p>
      </div>
    )
  }

  return (
    <div className="history-timeline">
      <h3>Historial de Cambios</h3>
      <div className="timeline-container">
        {historial.map((item, index) => (
          <div key={item.id} className="timeline-item">
            <div className="timeline-marker">
              <span className="timeline-icon">{getTipoIcon(item.tipo_cambio)}</span>
            </div>
            <div className="timeline-content">
              <div className="timeline-header">
                <span className="timeline-type">{getTipoLabel(item.tipo_cambio)}</span>
                <span className="timeline-date">
                  {formatDate(item.fecha_cambio)}
                </span>
              </div>
              <div className="timeline-body">
                {item.valor_anterior && (
                  <div className="timeline-change">
                    <span className="change-label">Anterior:</span>
                    <span className="change-value old">{item.valor_anterior}</span>
                  </div>
                )}
                {item.valor_nuevo && (
                  <div className="timeline-change">
                    <span className="change-label">Nuevo:</span>
                    <span className="change-value new">{item.valor_nuevo}</span>
                  </div>
                )}
                {item.usuario_username && (
                  <div className="timeline-user">
                    Por: <strong>{item.usuario_username}</strong>
                  </div>
                )}
                {item.notas && (
                  <div className="timeline-notes">
                    <em>{item.notas}</em>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default HistoryTimeline

