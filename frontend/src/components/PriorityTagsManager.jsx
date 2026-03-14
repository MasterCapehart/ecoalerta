import { useState, useEffect } from 'react'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './PriorityTagsManager.css'

function PriorityTagsManager({ reporte, onUpdate }) {
  const [prioridad, setPrioridad] = useState(reporte?.prioridad || 'normal')
  const [tags, setTags] = useState(reporte?.tags || [])
  const [availableTags, setAvailableTags] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchTags()
  }, [])

  useEffect(() => {
    if (reporte) {
      setPrioridad(reporte.prioridad || 'normal')
      setTags(reporte.tags || [])
    }
  }, [reporte])

  const fetchTags = async () => {
    try {
      const response = await apiClient.get(API_ROUTES.TAGS)
      setAvailableTags(response.data || [])
    } catch (error) {
      console.error('Error al cargar tags:', error)
    }
  }

  const handlePrioridadChange = async (newPrioridad) => {
    setPrioridad(newPrioridad)
    if (reporte?.id) {
      await updateReporte({ prioridad: newPrioridad })
    }
  }

  const handleTagToggle = async (tagId) => {
    const newTags = tags.some(t => t.id === tagId)
      ? tags.filter(t => t.id !== tagId)
      : [...tags, availableTags.find(t => t.id === tagId)]
    
    setTags(newTags)
    if (reporte?.id) {
      await updateReporte({ tags: newTags.map(t => t.id) })
    }
  }

  const updateReporte = async (data) => {
    setLoading(true)
    try {
      await apiClient.patch(`${API_ROUTES.REPORTES}${reporte.id}/actualizar_estado/`, data)
      toast.success('Cambios guardados')
      if (onUpdate) {
        onUpdate()
      }
    } catch (error) {
      console.error('Error al actualizar:', error)
      toast.error('Error al guardar cambios')
    } finally {
      setLoading(false)
    }
  }

  const getPrioridadColor = (p) => {
    const colors = {
      baja: '#9e9e9e',
      normal: '#2196F3',
      alta: '#ff9800',
      urgente: '#f44336'
    }
    return colors[p] || colors.normal
  }

  const getPrioridadLabel = (p) => {
    const labels = {
      baja: 'Baja',
      normal: 'Normal',
      alta: 'Alta',
      urgente: 'Urgente'
    }
    return labels[p] || 'Normal'
  }

  return (
    <div className="priority-tags-manager">
      <div className="priority-section">
        <label>Prioridad</label>
        <div className="priority-buttons">
          {['baja', 'normal', 'alta', 'urgente'].map(p => (
            <button
              key={p}
              className={`priority-btn ${prioridad === p ? 'active' : ''}`}
              onClick={() => handlePrioridadChange(p)}
              style={{
                backgroundColor: prioridad === p ? getPrioridadColor(p) : '#f0f0f0',
                color: prioridad === p ? 'white' : '#333',
                border: `2px solid ${getPrioridadColor(p)}`
              }}
              disabled={loading}
            >
              {getPrioridadLabel(p)}
            </button>
          ))}
        </div>
        {reporte?.prioridad_calculada !== undefined && (
          <div className="priority-score">
            Score calculado: <strong>{reporte.prioridad_calculada.toFixed(1)}</strong>
          </div>
        )}
      </div>

      <div className="tags-section">
        <label>Tags</label>
        <div className="tags-list">
          {availableTags.map(tag => {
            const isSelected = tags.some(t => t.id === tag.id)
            return (
              <button
                key={tag.id}
                className={`tag-btn ${isSelected ? 'active' : ''}`}
                onClick={() => handleTagToggle(tag.id)}
                style={{
                  backgroundColor: isSelected ? tag.color : '#f0f0f0',
                  color: isSelected ? 'white' : '#333',
                  border: `1px solid ${tag.color}`
                }}
                disabled={loading}
              >
                {tag.nombre}
              </button>
            )
          })}
        </div>
        {availableTags.length === 0 && (
          <p className="no-tags">No hay tags disponibles</p>
        )}
      </div>
    </div>
  )
}

export default PriorityTagsManager

