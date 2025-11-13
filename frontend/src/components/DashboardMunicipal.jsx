import { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './DashboardMunicipal.css'
import { API_ENDPOINTS } from '../config'
import { getAuthHeaders, logout } from '../services/auth'

// Fix iconos Leaflet
import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Función para cargar leaflet.heat dinámicamente desde CDN
// Esto asegura que el plugin se cargue correctamente en Vite
const loadHeatPlugin = () => {
  return new Promise((resolve, reject) => {
    // Verificar si ya está cargado
    if (typeof L !== 'undefined' && typeof L.heatLayer !== 'undefined') {
      console.log('Heat plugin already loaded')
      resolve()
      return
    }

    // Verificar si el script ya existe
    const existingScript = document.querySelector('script[data-heat-plugin]')
    if (existingScript) {
      existingScript.addEventListener('load', () => {
        if (typeof L.heatLayer !== 'undefined') {
          resolve()
        } else {
          reject(new Error('Plugin loaded but L.heatLayer not available'))
        }
      })
      return
    }

    // Cargar desde CDN (más confiable que node_modules en Vite)
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js'
    script.setAttribute('data-heat-plugin', 'true')
    script.onload = () => {
      // Esperar un momento para que L.heatLayer se registre
      setTimeout(() => {
        if (typeof L.heatLayer !== 'undefined') {
          console.log('Heat plugin loaded successfully from CDN')
          resolve()
        } else {
          console.error('Plugin loaded but L.heatLayer not found')
          reject(new Error('Plugin loaded but L.heatLayer not available'))
        }
      }, 100)
    }
    script.onerror = () => {
      console.error('Failed to load heat plugin from CDN')
      reject(new Error('Could not load leaflet.heat plugin'))
    }
    document.head.appendChild(script)
  })
}

// Componente para la capa de heatmap
function HeatmapLayer({ data, enabled }) {
  const map = useMap()
  const heatmapRef = useRef(null)
  const clickHandlerRef = useRef(null)
  const [pluginLoaded, setPluginLoaded] = useState(false)

  // Cargar el plugin una vez cuando el componente se monta
  useEffect(() => {
    loadHeatPlugin()
      .then(() => {
        setPluginLoaded(true)
      })
      .catch((error) => {
        console.error('Error loading heat plugin:', error)
      })
  }, [])

  useEffect(() => {
    if (!map || !pluginLoaded) {
      return
    }

    // Limpiar capa anterior si existe
    if (heatmapRef.current) {
      map.removeLayer(heatmapRef.current)
      heatmapRef.current = null
    }

    // Remover handler de clic anterior si existe
    if (clickHandlerRef.current) {
      map.off('click', clickHandlerRef.current)
      clickHandlerRef.current = null
    }

    if (!enabled) {
      console.log('HeatmapLayer: Disabled')
      return
    }

    if (!data || data.length === 0) {
      console.log('HeatmapLayer: No data available', { dataLength: data?.length })
      return
    }

    console.log('HeatmapLayer: Creating heatmap with', data.length, 'points')

    // Verificar que L.heatLayer esté disponible
    if (typeof L.heatLayer === 'undefined') {
      console.error('L.heatLayer is not defined after loading plugin')
      return
    }

    // Preparar datos para leaflet.heat
    const heatData = data.map(point => [
      point.lat,
      point.lng,
      point.intensity || point.densidad || 1
    ])

    console.log('HeatmapLayer: Heat data prepared', heatData.slice(0, 3))

    // Calcular máximo para la intensidad
    const maxIntensity = Math.max(...data.map(d => d.intensity || d.densidad || 1), 1)
    console.log('HeatmapLayer: Max intensity', maxIntensity)

    // Crear la capa de heatmap usando L.heatLayer (función factory)
    try {
      // Ajustar parámetros para hacer el heatmap más visible
      // Aumentar radius y blur para que sea más visible con pocos puntos
      const radius = Math.max(50, Math.min(100, 25 * Math.sqrt(data.length)))
      const blur = Math.max(20, Math.min(40, 15 * Math.sqrt(data.length)))
      
      console.log('HeatmapLayer: Creating with params', { radius, blur, maxIntensity, dataPoints: data.length })
      
      heatmapRef.current = L.heatLayer(heatData, {
        radius: radius,
        blur: blur,
        maxZoom: 17,
        minOpacity: 0.3, // Hacer más visible
        gradient: {
          0.0: 'blue',
          0.3: 'cyan',
          0.5: 'lime',
          0.7: 'yellow',
          0.9: 'orange',
          1.0: 'red'
        },
        max: maxIntensity
      })

      heatmapRef.current.addTo(map)
      
      // Asegurar que el heatmap esté por encima de otros elementos y sea visible
      if (heatmapRef.current._canvas) {
        heatmapRef.current._canvas.style.zIndex = '650'
        heatmapRef.current._canvas.style.pointerEvents = 'none'
        // Forzar redraw para asegurar que se renderice
        setTimeout(() => {
          if (heatmapRef.current && heatmapRef.current.redraw) {
            heatmapRef.current.redraw()
            console.log('HeatmapLayer: Forced redraw')
          }
        }, 100)
      }
      
      // También forzar un evento de movimiento del mapa para activar el renderizado
      map.fire('moveend')
      
      console.log('HeatmapLayer: Heatmap layer added to map successfully', {
        layer: heatmapRef.current,
        canvas: heatmapRef.current._canvas,
        canvasStyle: heatmapRef.current._canvas?.style,
        dataPoints: heatData.length,
        heatData: heatData.slice(0, 3)
      })
    } catch (error) {
      console.error('HeatmapLayer: Error creating heatmap layer', error)
      console.error('Error details:', error.message, error.stack)
      // Mostrar mensaje de error más descriptivo
      if (error.message) {
        console.error('Error específico:', error.message)
      }
    }

    // Crear handler de clic para mostrar popup de hotspots
    clickHandlerRef.current = function(e) {
      const clickedPoint = e.latlng
      
      // Buscar el punto más cercano dentro de un radio razonable
      let closestPoint = null
      let minDistance = Infinity
      
      data.forEach(point => {
        const pointLatLng = L.latLng(point.lat, point.lng)
        const distance = clickedPoint.distanceTo(pointLatLng)
        
        // Radio de detección en metros (aproximadamente 500m)
        if (distance < 500 && distance < minDistance) {
          minDistance = distance
          closestPoint = point
        }
      })
      
      if (closestPoint) {
        const popup = L.popup()
          .setLatLng([closestPoint.lat, closestPoint.lng])
          .setContent(`
            <div style="padding: 10px;">
              <h3 style="margin: 0 0 10px 0; font-size: 16px;">🔥 Hotspot de Vertederos</h3>
              <p style="margin: 5px 0;"><strong>Densidad:</strong> ${closestPoint.densidad} reportes</p>
              <p style="margin: 5px 0;"><strong>Intensidad:</strong> ${closestPoint.intensity}</p>
              <p style="margin: 5px 0; font-size: 12px; color: #666;">
                Ubicación: ${closestPoint.lat.toFixed(4)}, ${closestPoint.lng.toFixed(4)}
              </p>
              <p style="margin: 10px 0 0 0; font-size: 11px; color: #999;">
                Esta zona concentra una alta cantidad de reportes de vertederos
              </p>
            </div>
          `)
          .openOn(map)
      }
    }

    // Agregar evento de clic
    map.on('click', clickHandlerRef.current)

    return () => {
      if (heatmapRef.current) {
        map.removeLayer(heatmapRef.current)
        heatmapRef.current = null
      }
      if (clickHandlerRef.current) {
        map.off('click', clickHandlerRef.current)
        clickHandlerRef.current = null
      }
    }
  }, [map, data, enabled, pluginLoaded])

  return null
}

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
  const [heatmapEnabled, setHeatmapEnabled] = useState(false)
  const [heatmapData, setHeatmapData] = useState([])
  const [loadingHeatmap, setLoadingHeatmap] = useState(false)

  // Cargar reportes y estadísticas
  useEffect(() => {
    fetchReportes()
    fetchEstadisticas()
  }, [filtroEstado])

  // Cargar datos del heatmap cuando se activa
  useEffect(() => {
    if (heatmapEnabled && vistaActual === 'mapa') {
      console.log('Heatmap enabled, fetching data...')
      fetchHeatmapData()
    } else if (!heatmapEnabled) {
      // Limpiar datos cuando se desactiva
      setHeatmapData([])
    }
  }, [heatmapEnabled, filtroEstado, vistaActual])

  // Handler para cuando se cambia el checkbox
  const handleHeatmapToggle = (checked) => {
    console.log('Heatmap toggle:', checked)
    setHeatmapEnabled(checked)
    if (checked && vistaActual === 'mapa') {
      // Cargar datos inmediatamente cuando se activa
      fetchHeatmapData()
    }
  }

  const fetchHeatmapData = async () => {
    setLoadingHeatmap(true)
    try {
      const params = new URLSearchParams()
      if (filtroEstado) {
        params.append('estado', filtroEstado)
      }
      
      const url = `${API_ENDPOINTS.HEATMAP}?${params.toString()}`
      console.log('Fetching heatmap data from:', url)
      const response = await fetch(url)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('HTTP error response:', response.status, errorText)
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Heatmap data received:', data)
      
      if (data.data && Array.isArray(data.data)) {
        if (data.data.length > 0) {
          setHeatmapData(data.data)
          console.log('Heatmap data set, points:', data.data.length)
        } else {
          console.warn('Heatmap data is empty array')
          setHeatmapData([])
        }
      } else if (Array.isArray(data)) {
        // Si la respuesta es directamente un array
        if (data.length > 0) {
          setHeatmapData(data)
          console.log('Heatmap data set (direct array), points:', data.length)
        } else {
          console.warn('Heatmap data is empty array')
          setHeatmapData([])
        }
      } else {
        console.warn('No heatmap data found in response:', data)
        setHeatmapData([])
      }
    } catch (error) {
      console.error('Error al cargar datos del heatmap:', error)
      setHeatmapData([])
      // Mostrar mensaje de error al usuario
      alert('Error al cargar el mapa de calor. Por favor, intente nuevamente.')
    } finally {
      setLoadingHeatmap(false)
    }
  }

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
      const response = await fetch(API_ENDPOINTS.ESTADISTICAS, {
        headers: getAuthHeaders()
      })
      
      if (response.status === 401) {
        // Token expirado o inválido
        logout()
        window.location.href = '/login'
        return
      }
      
      const data = await response.json()
      setEstadisticas(data)
    } catch (error) {
      console.error('Error al cargar estadísticas:', error)
    }
  }

  const handleVerDetalle = (reporte) => {
    console.log('handleVerDetalle llamado con:', reporte)
    setReporteSeleccionado(reporte)
    setShowModal(true)
    console.log('Modal debería mostrarse ahora')
  }

  const handleGuardarCambios = async () => {
    if (!reporteSeleccionado) return

    const nuevoEstado = document.querySelector('select').value
    const notasInternas = document.querySelector('textarea').value

    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTES}${reporteSeleccionado.id}/actualizar_estado/`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          estado: nuevoEstado,
          notas_internas: notasInternas
        })
      })

      if (response.status === 401) {
        // Token expirado o inválido
        logout()
        window.location.href = '/login'
        return
      }

      if (response.ok) {
        fetchReportes()
        fetchEstadisticas()
        setShowModal(false)
        alert('Cambios guardados exitosamente')
      } else {
        const errorData = await response.json()
        alert(errorData.error || 'Error al guardar cambios')
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
          <button className="logout-btn" onClick={() => {
            logout()
            window.location.href = '/login'
          }}>
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
            {vistaActual === 'mapa' && (
              <div className="heatmap-control">
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={heatmapEnabled}
                    onChange={(e) => handleHeatmapToggle(e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                  <span style={{ fontWeight: 500 }}>🔥 Mapa de Calor</span>
                  {loadingHeatmap && <span style={{ fontSize: '12px', color: '#666' }}>(Cargando...)</span>}
                  {heatmapEnabled && !loadingHeatmap && heatmapData.length === 0 && (
                    <span style={{ fontSize: '12px', color: '#ff6b6b' }}>(Sin datos - verifique que haya reportes con ubicación)</span>
                  )}
                  {heatmapEnabled && !loadingHeatmap && heatmapData.length > 0 && (
                    <span style={{ fontSize: '12px', color: '#228B22' }}>({heatmapData.length} puntos)</span>
                  )}
                </label>
              </div>
            )}
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
                  {/* Capa de Heatmap */}
                  <HeatmapLayer data={heatmapData} enabled={heatmapEnabled} />
                  {/* Marcadores de reportes - siempre visibles cuando el mapa de calor está desactivado */}
                  {!heatmapEnabled && reportes
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
                            onClick={(e) => {
                              e.preventDefault()
                              e.stopPropagation()
                              console.log('Botón Ver clickeado para reporte:', reporte)
                              handleVerDetalle(reporte)
                            }}
                            type="button"
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
        <div 
          className="modal-overlay" 
          onClick={() => {
            console.log('Clic en overlay, cerrando modal')
            setShowModal(false)
            setReporteSeleccionado(null)
          }}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Detalle de Reporte</h2>
              <span 
                className="close-btn" 
                onClick={() => {
                  console.log('Clic en botón cerrar')
                  setShowModal(false)
                  setReporteSeleccionado(null)
                }}
              >
                &times;
              </span>
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