import { useState, useEffect, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './RouteOptimizer.css'
import L from 'leaflet'

function RouteOptimizer() {
  const [routeData, setRouteData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [estado, setEstado] = useState('nuevo')
  const [includePreventive, setIncludePreventive] = useState(false) // Nuevo

  // Admin Features
  const [inspectores, setInspectores] = useState([])
  const [selectedInspector, setSelectedInspector] = useState('')

  useEffect(() => {
    loadInspectores()
  }, [])

  const loadInspectores = async () => {
    try {
      // Solo funcionará si es admin
      const response = await apiClient.get(API_ROUTES.ADMIN_USUARIOS)
      // Filtrar solo inspectores
      const inspectors = response.data.filter(u => u.tipo === 'inspector')
      setInspectores(inspectors)
    } catch (error) {
      // Ignorar error de permisos (usuario normal)
      console.log("No es admin o error cargando inspectores", error)
    }
  }

  const fetchRoute = useCallback(async () => {
    setLoading(true)
    try {
      const params = { 
        estado, 
        include_preventive: includePreventive 
      }

      let url = API_ROUTES.RUTA_OPTIMIZADA
      if (selectedInspector) {
        url = `${API_ROUTES.RUTA_OPTIMIZADA}${selectedInspector}/`
      }

      const response = await apiClient.get(url, { params })
      setRouteData(response.data)
    } catch (error) {
      console.error('Error al cargar ruta:', error)
      toast.error('Error al cargar la ruta optimizada')
    } finally {
      setLoading(false)
    }
  }, [estado, selectedInspector, includePreventive])

  useEffect(() => {
    fetchRoute()
  }, [fetchRoute])

  // Assignment Result Modal State
  const [assignmentResult, setAssignmentResult] = useState(null)

  const handleAssignAutomatic = async () => {
    setLoading(true)
    try {
      const response = await apiClient.post(API_ROUTES.ASIGNACION_AUTOMATICA)
      setAssignmentResult(response.data)
      toast.success(`Asignación completada: ${response.data.asignados} reportes`)
      fetchRoute()
    } catch (error) {
      console.error('Error en asignación automática:', error)
      toast.error('Error en asignación automática')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !routeData) {
    return (
      <div className="route-optimizer loading">
        <p>Cargando ruta optimizada...</p>
      </div>
    )
  }

  if (!routeData || !routeData.reportes || routeData.reportes.length === 0) {
    return (
      <div className="route-optimizer empty">
        <p>No hay reportes para optimizar ruta</p>
        <button onClick={handleAssignAutomatic} className="btn-assign">
          Asignar Reportes Automáticamente
        </button>
      </div>
    )
  }

  // Obtener coordenadas de los reportes
  const reportesCoords = routeData?.route_coords || []

  // Calcular centro del mapa basado en los puntos
  const center = reportesCoords.length > 0
    ? [reportesCoords[0].lat, reportesCoords[0].lng]
    : [-33.4489, -70.6693]

  return (
    <div className="route-optimizer">
      <div className="route-header">
        <h2>🗺️ Ruta Optimizada</h2>
        <div className="route-controls">
          {inspectores.length > 0 && (
            <select
              value={selectedInspector}
              onChange={(e) => setSelectedInspector(e.target.value)}
              className="inspector-select"
            >
              <option value="">Mi Ruta</option>
              {inspectores.map(insp => (
                <option key={insp.id} value={insp.id}>
                  👮 {insp.username}
                </option>
              ))}
            </select>
          )}

          <select value={estado} onChange={(e) => setEstado(e.target.value)}>
            <option value="nuevo">Nuevos</option>
            <option value="proceso">En Proceso</option>
          </select>

          <label className="toggle-preventive" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px', background: includePreventive ? '#eef2ff' : 'transparent', padding: '4px 10px', borderRadius: '15px', border: '1px solid #c7d2fe' }}>
            <input 
              type="checkbox" 
              checked={includePreventive} 
              onChange={(e) => setIncludePreventive(e.target.checked)} 
            />
            <span style={{ fontWeight: includePreventive ? 'bold' : 'normal', color: includePreventive ? '#4f46e5' : '#666' }}>
              🧠 Inteligencia AI
            </span>
          </label>
          <button onClick={fetchRoute} className="btn-refresh">
            🔄 Actualizar
          </button>
          <button onClick={handleAssignAutomatic} className="btn-assign">
            ⚡ Asignar Automáticamente
          </button>
        </div>
      </div>

      <div className="route-info">
        <div className="info-card">
          <h3>Reportes en Ruta</h3>
          <p className="info-value">{routeData.cantidad_reportes}</p>
        </div>
        <div className="info-card">
          <h3>Distancia Total</h3>
          <p className="info-value">{routeData.distancia_km?.toFixed(2) || 0} km</p>
        </div>
        <div className="info-card">
          <h3>Tiempo Estimado</h3>
          <p className="info-value">{routeData.tiempo_estimado_horas?.toFixed(1) || 0} horas</p>
        </div>
      </div>

      <div className="route-map-container">
        <MapContainer
          center={center}
          zoom={13}
          style={{ height: '500px', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          {reportesCoords.map((coord) => (
            <Marker 
              key={coord.id} 
              position={[coord.lat, coord.lng]}
              icon={coord.tipo === 'preventivo' ? L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="background-color: #4f46e5; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; border: 2px solid white; box-shadow: 0 0 10px rgba(79, 70, 229, 0.5)">🧠</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
              }) : undefined}
            >
              <Popup>
                <div className="route-popup">
                  <b style={{ color: coord.tipo === 'preventivo' ? '#4f46e5' : 'inherit' }}>
                    {coord.tipo === 'preventivo' ? '💡 Punto Preventivo' : `Parada #\${index + 1}`}
                  </b><br />
                  Codigo: {coord.codigo}<br />
                  Cat: {coord.categoria}
                  {coord.tipo === 'preventivo' && <p style={{ fontSize: '11px', color: '#666', marginTop: '5px' }}>Zona con alta probabilidad de acumulación según IA.</p>}
                </div>
              </Popup>
            </Marker>
          ))}
          {reportesCoords.length > 1 && (
            <Polyline
              positions={reportesCoords.map(c => [c.lat, c.lng])}
              color="#2563eb"
              weight={4}
              dashArray="10, 10"
            />
          )}
        </MapContainer>
      </div>

      <div className="route-list">
        <h3>Orden de Visita</h3>
        <div className="timeline">
          {reportesCoords.map((item, index) => (
            <div key={item.id} className="timeline-item">
              <div className="timeline-number">{index + 1}</div>
              <div className="timeline-content">
                <strong>{item.codigo}</strong>
                <span>{item.categoria}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {assignmentResult && (
        <div className="modal-overlay" onClick={() => setAssignmentResult(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>✅ Asignación Completada</h2>
              <span className="close-btn" onClick={() => setAssignmentResult(null)}>&times;</span>
            </div>
            <div className="modal-body" style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <p className="summary-text">
                Se han asignado <strong>{assignmentResult.asignados}</strong> reportes automáticamente.
              </p>

              {assignmentResult.detalles && assignmentResult.detalles.length > 0 && (
                <table className="result-table">
                  <thead>
                    <tr>
                      <th>Reporte</th>
                      <th>Inspector</th>
                      <th>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignmentResult.detalles.map((item, idx) => (
                      <tr key={idx}>
                        <td>{item.reporte}</td>
                        <td>{item.inspector}</td>
                        <td>{Math.round(item.score)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {assignmentResult.asignados === 0 && (
                <p className="empty-message">No se encontraron reportes nuevos pendientes de asignación.</p>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-save" onClick={() => setAssignmentResult(null)}>Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RouteOptimizer

