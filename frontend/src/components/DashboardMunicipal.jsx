import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './DashboardMunicipal.css'
import { API_ENDPOINTS } from '../config'

// Fix iconos Leaflet
import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

function DashboardMunicipal() {
  const [vistaActual, setVistaActual] = useState('mapa')
  const [reporteSeleccionado, setReporteSeleccionado] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [reportes, setReportes] = useState([])
  const [estadisticas, setEstadisticas] = useState({
    total: 0,
    nuevos: 0,
    en_proceso: 0,
    resueltos: 0
  })
  const [loading, setLoading] = useState(true)
  const [filtroEstado, setFiltroEstado] = useState('')

  // Cargar reportes y estadísticas
  useEffect(() => {
    fetchReportes()
    fetchEstadisticas()
  }, [filtroEstado])

  const fetchReportes = async () => {
    setLoading(true)
    try {
      const url = filtroEstado ? `${API_ENDPOINTS.REPORTES}?estado=${filtroEstado}` : API_ENDPOINTS.REPORTES
      const response = await fetch(url)
      const data = await response.json()
      setReportes(Array.isArray(data) ? data : data.results || [])
    } catch (error) {
      console.error('Error al cargar reportes:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchEstadisticas = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.ESTADISTICAS)
      const data = await response.json()
      setEstadisticas(data)
    } catch (error) {
      console.error('Error al cargar estadísticas:', error)
    }
  }

  const handleVerDetalle = (reporte) => {
    setReporteSeleccionado(reporte)
    setShowModal(true)
  }

  const handleGuardarCambios = async () => {
    if (!reporteSeleccionado) return

    const nuevoEstado = document.querySelector('select').value
    const notasInternas = document.querySelector('textarea').value

    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTES}${reporteSeleccionado.id}/actualizar_estado/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          estado: nuevoEstado,
          notas_internas: notasInternas
        })
      })

      if (response.ok) {
        fetchReportes()
        fetchEstadisticas()
        setShowModal(false)
        alert('Cambios guardados exitosamente')
      }
    } catch (error) {
      console.error('Error al actualizar:', error)
      alert('Error al guardar cambios')
    }
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h1>🌱 EcoAlerta - Dashboard Municipal</h1>
        <div className="user-info">
          <span>👤 Inspector Municipal</span>
          <button className="logout-btn" onClick={() => window.location.href = '/login'}>
            Cerrar Sesión
            </button>
        </div>
      </div>

      <div className="dashboard-main">
        {/* Sidebar */}
        <div className="sidebar">
          <div 
            className={`nav-item ${vistaActual === 'mapa' ? 'active' : ''}`}
            onClick={() => setVistaActual('mapa')}
          >
            🗺️ Vista de Mapa
          </div>
          <div 
            className={`nav-item ${vistaActual === 'tabla' ? 'active' : ''}`}
            onClick={() => setVistaActual('tabla')}
          >
            📋 Vista de Tabla
          </div>
          <div 
            className={`nav-item ${vistaActual === 'estadisticas' ? 'active' : ''}`}
            onClick={() => setVistaActual('estadisticas')}
          >
            📊 Estadísticas
          </div>
          <div className="nav-item">
            📥 Exportar Datos
          </div>
        </div>

        {/* Content */}
        <div className="content">
          {/* Stats Cards */}
          <div className="stats-container">
            <div className="stat-card stat-nuevos">
              <h3>Nuevos</h3>
              <div className="number">{estadisticas.nuevos}</div>
            </div>
            <div className="stat-card stat-proceso">
              <h3>En Proceso</h3>
              <div className="number">{estadisticas.en_proceso}</div>
            </div>
            <div className="stat-card stat-resueltos">
              <h3>Resueltos</h3>
              <div className="number">{estadisticas.resueltos}</div>
            </div>
            <div className="stat-card stat-total">
              <h3>Total</h3>
              <div className="number">{estadisticas.total}</div>
            </div>
          </div>

          {/* Filters */}
          <div className="filters-bar">
            <div className="filter-group">
              <label>Estado</label>
              <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
                <option value="">Todos</option>
                <option value="nuevo">Nuevo</option>
                <option value="proceso">En Proceso</option>
                <option value="resuelto">Resuelto</option>
              </select>
            </div>
            <div className="filter-group">
              <label>Categoría</label>
              <select>
                <option value="">Todas</option>
                <option value="domesticos">Domésticos</option>
                <option value="escombros">Escombros</option>
              </select>
            </div>
            <div className="search-box">
              <input type="text" placeholder="Buscar por código..." />
              <button className="btn-filter">Filtrar</button>
            </div>
          </div>

          {/* Vista Mapa */}
          {vistaActual === 'mapa' && (
            <div className="map-view">
              {loading ? (
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center', 
                  height: '100%',
                  fontSize: '16px',
                  color: '#666'
                }}>
                  Cargando mapa...
                </div>
              ) : (
                <MapContainer
                  center={[-29.9533, -71.3395]}
                  zoom={12}
                  style={{ height: '100%', width: '100%', minHeight: '500px' }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; OpenStreetMap contributors'
                  />
                  {reportes
                    .filter(reporte => reporte.lat && reporte.lng)
                    .map(reporte => (
                    <Marker 
                      key={reporte.id || reporte.codigo_seguimiento} 
                      position={[reporte.lat, reporte.lng]}
                    >
                      <Popup>
                        <div>
                          <b>{reporte.codigo_seguimiento}</b><br/>
                          {reporte.categoria_nombre}<br/>
                          <small>{reporte.direccion || 'Sin dirección'}</small><br/>
                          <button 
                            onClick={() => handleVerDetalle(reporte)}
                            style={{
                              marginTop: '5px',
                              padding: '5px 10px',
                              background: '#228B22',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer'
                            }}
                          >
                            Ver Detalle
                          </button>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </MapContainer>
              )}
            </div>
          )}

          {/* Vista Tabla */}
          {vistaActual === 'tabla' && (
            <div className="table-view">
              <table>
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Fecha</th>
                    <th>Ubicación</th>
                    <th>Categoría</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>
                        Cargando reportes...
                      </td>
                    </tr>
                  ) : reportes.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>
                        No hay reportes disponibles
                      </td>
                    </tr>
                  ) : (
                    reportes.map(reporte => (
                      <tr key={reporte.id || reporte.codigo_seguimiento}>
                        <td>{reporte.codigo_seguimiento}</td>
                        <td>{new Date(reporte.fecha_creacion).toLocaleDateString()}</td>
                        <td>{reporte.direccion || 'Sin dirección'}</td>
                        <td>{reporte.categoria_nombre || 'Sin categoría'}</td>
                        <td>
                          <span className={`status-badge status-${reporte.estado}`}>
                            {reporte.estado.toUpperCase()}
                          </span>
                        </td>
                        <td>
                          <button 
                            className="btn-action"
                            onClick={() => handleVerDetalle(reporte)}
                          >
                            Ver
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
          
        </div>
      </div>

      {/* Modal Detalle */}
      {showModal && reporteSeleccionado && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Detalle de Reporte</h2>
              <span className="close-btn" onClick={() => setShowModal(false)}>&times;</span>
            </div>
            
            <div className="detail-group">
              <label>Código</label>
              <p>{reporteSeleccionado.codigo_seguimiento}</p>
            </div>

            <div className="detail-group">
              <label>Fecha</label>
              <p>{new Date(reporteSeleccionado.fecha_creacion).toLocaleString()}</p>
            </div>

            <div className="detail-group">
              <label>Categoría</label>
              <p>{reporteSeleccionado.categoria_nombre}</p>
            </div>

            <div className="detail-group">
              <label>Descripción</label>
              <p>{reporteSeleccionado.descripcion || 'Sin descripción'}</p>
            </div>

            <div className="form-group">
              <label>Cambiar Estado</label>
              <select defaultValue={reporteSeleccionado.estado}>
                <option value="nuevo">Nuevo</option>
                <option value="proceso">En Proceso</option>
                <option value="resuelto">Resuelto</option>
              </select>
            </div>

            <div className="form-group">
              <label>Notas Internas</label>
              <textarea placeholder="Agregar notas..."></textarea>
            </div>

            <button className="btn-save" onClick={handleGuardarCambios}>
              Guardar Cambios
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default DashboardMunicipal