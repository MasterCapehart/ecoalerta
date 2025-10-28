import { useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './DashboardMunicipal.css'

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

  // Datos de ejemplo
  const reportes = [
    { 
      codigo: 'ABC-1234', 
      fecha: '15/01/2025', 
      lat: -29.9533, 
      lng: -71.3395, 
      ubicacion: 'Av. Principal 123', 
      categoria: 'Domésticos', 
      estado: 'nuevo',
      descripcion: 'Acumulación de basura doméstica'
    },
    { 
      codigo: 'DEF-5678', 
      fecha: '14/01/2025', 
      lat: -29.9600, 
      lng: -71.3300, 
      ubicacion: 'Calle 2', 
      categoria: 'Escombros', 
      estado: 'proceso',
      descripcion: 'Escombros de construcción'
    },
    { 
      codigo: 'GHI-9012', 
      fecha: '13/01/2025', 
      lat: -29.9450, 
      lng: -71.3450, 
      ubicacion: 'Sector Norte', 
      categoria: 'Electrónicos', 
      estado: 'resuelto',
      descripcion: 'Residuos electrónicos'
    },
  ]

  const handleVerDetalle = (reporte) => {
    setReporteSeleccionado(reporte)
    setShowModal(true)
  }

  const handleGuardarCambios = () => {
    alert('Cambios guardados exitosamente')
    setShowModal(false)
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
          <div className="nav-item">
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
              <div className="number">15</div>
            </div>
            <div className="stat-card stat-proceso">
              <h3>En Proceso</h3>
              <div className="number">8</div>
            </div>
            <div className="stat-card stat-resueltos">
              <h3>Resueltos</h3>
              <div className="number">42</div>
            </div>
            <div className="stat-card stat-total">
              <h3>Total</h3>
              <div className="number">65</div>
            </div>
          </div>

          {/* Filters */}
          <div className="filters-bar">
            <div className="filter-group">
              <label>Estado</label>
              <select>
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
              <MapContainer
                center={[-29.9533, -71.3395]}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; OpenStreetMap contributors'
                />
                {reportes.map(reporte => (
                  <Marker key={reporte.codigo} position={[reporte.lat, reporte.lng]}>
                    <Popup>
                      <b>{reporte.codigo}</b><br/>
                      {reporte.ubicacion}<br/>
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
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
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
                  {reportes.map(reporte => (
                    <tr key={reporte.codigo}>
                      <td>{reporte.codigo}</td>
                      <td>{reporte.fecha}</td>
                      <td>{reporte.ubicacion}</td>
                      <td>{reporte.categoria}</td>
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
                  ))}
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
              <p>{reporteSeleccionado.codigo}</p>
            </div>

            <div className="detail-group">
              <label>Fecha</label>
              <p>{reporteSeleccionado.fecha}</p>
            </div>

            <div className="detail-group">
              <label>Ubicación</label>
              <p>{reporteSeleccionado.ubicacion}</p>
            </div>

            <div className="detail-group">
              <label>Descripción</label>
              <p>{reporteSeleccionado.descripcion}</p>
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