import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './AdvancedStatistics.css'
// Funciones de fecha (fallback si date-fns no está disponible)
const formatDate = (date) => {
  const d = new Date(date)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
}

const subDays = (date, days) => {
  const d = new Date(date)
  d.setDate(d.getDate() - days)
  return d
}

const formatShortDate = (dateStr) => {
  try {
    const d = new Date(dateStr)
    return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}`
  } catch {
    return dateStr
  }
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8']

function AdvancedStatistics() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fechaDesde, setFechaDesde] = useState(formatDate(subDays(new Date(), 30)))
  const [fechaHasta, setFechaHasta] = useState(formatDate(new Date()))

  useEffect(() => {
    fetchStatistics()
  }, [fechaDesde, fechaHasta])

  const fetchStatistics = async () => {
    setLoading(true)
    try {
      const params = {
        fecha_desde: fechaDesde,
        fecha_hasta: fechaHasta
      }
      const response = await apiClient.get(API_ROUTES.ESTADISTICAS_AVANZADAS, { params })
      setStats(response.data)
    } catch (error) {
      console.error('Error al cargar estadísticas:', error)
      toast.error('Error al cargar las estadísticas')
    } finally {
      setLoading(false)
    }
  }

  const handleExportPDF = async () => {
    try {
      const params = {
        fecha_desde: fechaDesde,
        fecha_hasta: fechaHasta
      }
      const response = await apiClient.get(API_ROUTES.EXPORTAR_PDF, { 
        params,
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'reporte_estadistico.pdf')
      document.body.appendChild(link)
      link.click()
      link.remove()
      
      toast.success('PDF descargado exitosamente')
    } catch (error) {
      console.error('Error al exportar PDF:', error)
      toast.error('Error al exportar PDF')
    }
  }

  const handleExportExcel = async () => {
    try {
      const params = {
        fecha_desde: fechaDesde,
        fecha_hasta: fechaHasta
      }
      const response = await apiClient.get(API_ROUTES.EXPORTAR_EXCEL, { 
        params,
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'reporte_estadistico.xlsx')
      document.body.appendChild(link)
      link.click()
      link.remove()
      
      toast.success('Excel descargado exitosamente')
    } catch (error) {
      console.error('Error al exportar Excel:', error)
      toast.error('Error al exportar Excel')
    }
  }

  if (loading) {
    return (
      <div className="advanced-statistics loading">
        <p>Cargando estadísticas...</p>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="advanced-statistics error">
        <p>No se pudieron cargar las estadísticas</p>
      </div>
    )
  }

  const estadoData = [
    { name: 'Nuevos', value: stats.totales.nuevos },
    { name: 'En Proceso', value: stats.totales.en_proceso },
    { name: 'Resueltos', value: stats.totales.resueltos },
    { name: 'Cerrados', value: stats.totales.cerrados }
  ]

  const categoriaData = stats.por_categoria?.map(item => ({
    name: item.categoria__nombre || 'Sin categoría',
    value: item.total
  })) || []

  const prioridadData = stats.por_prioridad?.map(item => ({
    name: item.prioridad.charAt(0).toUpperCase() + item.prioridad.slice(1),
    value: item.total
  })) || []

  const diaData = stats.por_dia?.map(item => ({
    fecha: formatShortDate(item.dia),
    cantidad: item.total
  })) || []

  return (
    <div className="advanced-statistics">
      <div className="stats-header">
        <h2>📊 Estadísticas Avanzadas</h2>
        <div className="stats-controls">
          <div className="date-filters">
            <label>
              Desde:
              <input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
              />
            </label>
            <label>
              Hasta:
              <input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
              />
            </label>
          </div>
          <div className="export-buttons">
            <button onClick={handleExportPDF} className="btn-export">
              📄 Exportar PDF
            </button>
            <button onClick={handleExportExcel} className="btn-export">
              📊 Exportar Excel
            </button>
          </div>
        </div>
      </div>

      <div className="stats-summary">
        <div className="summary-card">
          <h3>Total Reportes</h3>
          <p className="summary-value">{stats.totales.total}</p>
        </div>
        <div className="summary-card">
          <h3>Tasa de Resolución</h3>
          <p className="summary-value">{stats.tasa_resolucion?.toFixed(1) || 0}%</p>
        </div>
        <div className="summary-card">
          <h3>Tiempo Promedio</h3>
          <p className="summary-value">
            {stats.tiempo_promedio_resolucion 
              ? `${stats.tiempo_promedio_resolucion.toFixed(1)}h`
              : 'N/A'}
          </p>
        </div>
      </div>

      <div className="stats-charts">
        <div className="chart-container">
          <h3>Reportes por Estado</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={estadoData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#4CAF50" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Reportes por Categoría</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoriaData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {categoriaData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Reportes por Prioridad</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={prioridadData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#FF9800" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {diaData.length > 0 && (
          <div className="chart-container full-width">
            <h3>Tendencia Diaria</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={diaData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fecha" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="cantidad" stroke="#2196F3" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {stats.top_inspectores && stats.top_inspectores.length > 0 && (
          <div className="chart-container">
            <h3>Top Inspectores</h3>
            <div className="inspectors-list">
              {stats.top_inspectores.map((inspector, index) => (
                <div key={index} className="inspector-item">
                  <span className="inspector-rank">#{index + 1}</span>
                  <span className="inspector-name">{inspector.asignado_a__username}</span>
                  <span className="inspector-stats">
                    {inspector.total_resueltos} resueltos
                    {inspector.tiempo_promedio && ` • ${inspector.tiempo_promedio.toFixed(1)}h promedio`}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdvancedStatistics

