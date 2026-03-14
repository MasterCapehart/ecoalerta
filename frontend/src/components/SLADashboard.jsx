import { useState, useEffect } from 'react'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './SLADashboard.css'

function SLADashboard() {
  const [estadisticas, setEstadisticas] = useState(null)
  const [reportesRiesgo, setReportesRiesgo] = useState([])
  const [reportesExcedidos, setReportesExcedidos] = useState([])
  const [loading, setLoading] = useState(true)
  const [vista, setVista] = useState('estadisticas')

  useEffect(() => {
    loadData()
  }, [vista])

  const loadData = async () => {
    setLoading(true)
    try {
      if (vista === 'estadisticas') {
        const [statsRes, riesgoRes, excedidosRes] = await Promise.all([
          apiClient.get(API_ROUTES.SLA_ESTADISTICAS),
          apiClient.get(API_ROUTES.SLA_RIESGO),
          apiClient.get(API_ROUTES.SLA_EXCEDIDOS)
        ])
        setEstadisticas(statsRes.data)
        setReportesRiesgo(riesgoRes.data.reportes || [])
        setReportesExcedidos(excedidosRes.data.reportes || [])
      } else if (vista === 'riesgo') {
        const response = await apiClient.get(API_ROUTES.SLA_RIESGO)
        setReportesRiesgo(response.data.reportes || [])
      } else if (vista === 'excedidos') {
        const response = await apiClient.get(API_ROUTES.SLA_EXCEDIDOS)
        setReportesExcedidos(response.data.reportes || [])
      }
    } catch (error) {
      console.error('Error al cargar datos SLA:', error)
      toast.error('Error al cargar datos de SLA')
    } finally {
      setLoading(false)
    }
  }

  const calcularTiempoRestante = (fechaLimite) => {
    if (!fechaLimite) return null
    const ahora = new Date()
    const limite = new Date(fechaLimite)
    const diff = limite - ahora
    const horas = Math.floor(diff / (1000 * 60 * 60))
    const dias = Math.floor(horas / 24)
    
    if (diff < 0) return { excedido: true, horas: Math.abs(horas) }
    if (dias > 0) return { dias, horas: horas % 24 }
    return { horas }
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

  if (loading && vista === 'estadisticas') {
    return <div className="sla-loading">Cargando estadísticas...</div>
  }

  return (
    <div className="sla-dashboard">
      <div className="sla-header">
        <h2>Dashboard de SLA</h2>
        <div className="sla-tabs">
          <button
            className={vista === 'estadisticas' ? 'active' : ''}
            onClick={() => setVista('estadisticas')}
          >
            Estadísticas
          </button>
          <button
            className={vista === 'riesgo' ? 'active' : ''}
            onClick={() => setVista('riesgo')}
          >
            En Riesgo ({reportesRiesgo.length})
          </button>
          <button
            className={vista === 'excedidos' ? 'active' : ''}
            onClick={() => setVista('excedidos')}
          >
            Excedidos ({reportesExcedidos.length})
          </button>
        </div>
      </div>

      {vista === 'estadisticas' && estadisticas && (
        <div className="sla-stats">
          <div className="stat-card">
            <div className="stat-value">{estadisticas.total_con_sla || 0}</div>
            <div className="stat-label">Total con SLA</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-value">{estadisticas.en_riesgo || 0}</div>
            <div className="stat-label">En Riesgo</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-value">{estadisticas.excedidos || 0}</div>
            <div className="stat-label">Excedidos</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{estadisticas.cumplidos || 0}</div>
            <div className="stat-label">Cumplidos</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {estadisticas.tasa_cumplimiento?.toFixed(1) || 0}%
            </div>
            <div className="stat-label">Tasa de Cumplimiento</div>
          </div>
        </div>
      )}

      {vista === 'riesgo' && (
        <div className="sla-reportes">
          {loading ? (
            <div className="sla-loading">Cargando reportes...</div>
          ) : reportesRiesgo.length === 0 ? (
            <div className="no-reportes">No hay reportes en riesgo</div>
          ) : (
            <div className="reportes-list">
              {reportesRiesgo.map(reporte => {
                const tiempo = calcularTiempoRestante(reporte.fecha_limite_resolucion)
                return (
                  <div key={reporte.id} className="reporte-item warning">
                    <div className="reporte-header">
                      <span className="reporte-code">{reporte.codigo_seguimiento}</span>
                      <span className="reporte-estado">{reporte.estado}</span>
                    </div>
                    <div className="reporte-info">
                      <div>{reporte.categoria?.nombre || 'N/A'}</div>
                      <div className="tiempo-restante">
                        {tiempo && !tiempo.excedido && (
                          <>
                            {tiempo.dias && `${tiempo.dias}d `}
                            {tiempo.horas}h restantes
                          </>
                        )}
                      </div>
                    </div>
                    <div className="reporte-fecha">
                      Límite: {formatDate(reporte.fecha_limite_resolucion)}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {vista === 'excedidos' && (
        <div className="sla-reportes">
          {loading ? (
            <div className="sla-loading">Cargando reportes...</div>
          ) : reportesExcedidos.length === 0 ? (
            <div className="no-reportes">No hay reportes excedidos</div>
          ) : (
            <div className="reportes-list">
              {reportesExcedidos.map(reporte => {
                const tiempo = calcularTiempoRestante(reporte.fecha_limite_resolucion)
                return (
                  <div key={reporte.id} className="reporte-item danger">
                    <div className="reporte-header">
                      <span className="reporte-code">{reporte.codigo_seguimiento}</span>
                      <span className="reporte-estado">{reporte.estado}</span>
                    </div>
                    <div className="reporte-info">
                      <div>{reporte.categoria?.nombre || 'N/A'}</div>
                      <div className="tiempo-excedido">
                        {tiempo?.excedido && `Excedido por ${tiempo.horas}h`}
                      </div>
                    </div>
                    <div className="reporte-fecha">
                      Límite: {formatDate(reporte.fecha_limite_resolucion)}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SLADashboard
