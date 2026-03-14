import { useState, useEffect } from 'react'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './ValidationPanel.css'

function ValidationPanel({ reporteId, onValidated }) {
  const [reporte, setReporte] = useState(null)
  const [loading, setLoading] = useState(true)
  const [validando, setValidando] = useState(false)
  const [formData, setFormData] = useState({
    validado: true,
    notas: ''
  })

  useEffect(() => {
    if (reporteId) {
      loadReporte()
    }
  }, [reporteId])

  const loadReporte = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get(`${API_ROUTES.REPORTES}${reporteId}/`)
      setReporte(response.data)
    } catch (error) {
      console.error('Error al cargar reporte:', error)
      toast.error('Error al cargar reporte')
    } finally {
      setLoading(false)
    }
  }

  const handleValidar = async () => {
    if (!reporteId) return

    setValidando(true)
    try {
      await apiClient.post(
        `${API_ROUTES.VALIDAR_REPORTE}${reporteId}/validar/`,
        formData
      )
      toast.success(`Reporte ${formData.validado ? 'validado' : 'rechazado'} exitosamente`)
      if (onValidated) {
        onValidated()
      }
      loadReporte()
    } catch (error) {
      console.error('Error al validar reporte:', error)
      toast.error(error.response?.data?.error || 'Error al validar reporte')
    } finally {
      setValidando(false)
    }
  }

  if (loading) {
    return <div className="validation-panel-loading">Cargando reporte...</div>
  }

  if (!reporte) {
    return <div className="validation-panel-error">Reporte no encontrado</div>
  }

  return (
    <div className="validation-panel">
      <div className="validation-header">
        <h3>Validar Reporte</h3>
        <span className="reporte-code">Código: {reporte.codigo_seguimiento}</span>
      </div>

      <div className="validation-info">
        <div className="info-item">
          <label>Categoría:</label>
          <span>{reporte.categoria?.nombre || 'N/A'}</span>
        </div>
        <div className="info-item">
          <label>Estado:</label>
          <span className={`estado-badge estado-${reporte.estado}`}>
            {reporte.estado}
          </span>
        </div>
        <div className="info-item">
          <label>Validado:</label>
          <span className={reporte.validado ? 'validado' : 'no-validado'}>
            {reporte.validado ? '✓ Sí' : '✗ No'}
          </span>
        </div>
        {reporte.validado_por && (
          <div className="info-item">
            <label>Validado por:</label>
            <span>{reporte.validado_por?.username || 'N/A'}</span>
          </div>
        )}
      </div>

      <div className="validation-form">
        <div className="form-group">
          <label>
            <input
              type="radio"
              checked={formData.validado === true}
              onChange={() => setFormData({ ...formData, validado: true })}
            />
            <span>Validar</span>
          </label>
          <label>
            <input
              type="radio"
              checked={formData.validado === false}
              onChange={() => setFormData({ ...formData, validado: false })}
            />
            <span>Rechazar</span>
          </label>
        </div>

        <div className="form-group">
          <label htmlFor="notas">Notas (opcional):</label>
          <textarea
            id="notas"
            value={formData.notas}
            onChange={(e) => setFormData({ ...formData, notas: e.target.value })}
            placeholder="Agregar notas sobre la validación..."
            rows={4}
          />
        </div>

        <button
          onClick={handleValidar}
          disabled={validando}
          className={`btn-validate ${formData.validado ? 'btn-approve' : 'btn-reject'}`}
        >
          {validando ? 'Validando...' : (formData.validado ? 'Validar Reporte' : 'Rechazar Reporte')}
        </button>
      </div>
    </div>
  )
}

export default ValidationPanel
