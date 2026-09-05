import { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import apiClient from '../services/api'
import { toast } from './ToastContainer'
import './PanelCiudadano.css'

// Iconos del mapa
const iconReporte = L.divIcon({
  html: `<div style="background:#ef4444;width:20px;height:20px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>`,
  className: '',
  iconSize: [20, 20],
  iconAnchor: [10, 10],
  popupAnchor: [0, -10],
})
const iconNuevo = L.divIcon({
  html: `<div style="background:#3b82f6;width:22px;height:22px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>`,
  className: '',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -11],
})

function SeleccionarUbicacion({ onSelect }) {
  useMapEvents({
    click(e) {
      onSelect(e.latlng)
    },
  })
  return null
}

const ESTADOS_LABEL = { nuevo: 'Nuevo', proceso: 'En Proceso', resuelto: 'Resuelto', cerrado: 'Cerrado' }
const ESTADOS_COLOR = { nuevo: '#3b82f6', proceso: '#f59e0b', resuelto: '#22c55e', cerrado: '#9ca3af' }

export default function PanelCiudadano() {
  const [tab, setTab] = useState('mapa') // mapa | reportar | seguimiento
  const [municipio, setMunicipio] = useState(null)
  const [mapCenter, setMapCenter] = useState([-29.9027, -71.252])
  const [mapZoom] = useState(13)

  // Mapa público
  const [reportesPublicos, setReportesPublicos] = useState([])

  // Formulario reporte
  const [capas, setCapas] = useState([])
  const [subcategorias, setSubcategorias] = useState([])
  const [capaSeleccionada, setCapaSeleccionada] = useState('')
  const [form, setForm] = useState({
    subcategoria_id: '',
    descripcion: '',
    direccion: '',
    lat: '',
    lng: '',
    nombre_reportante: '',
    email_reportante: '',
    telefono_reportante: '',
  })
  const [marcadorNuevo, setMarcadorNuevo] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [codigoGenerado, setCodigoGenerado] = useState(null)

  // Seguimiento
  const [codigoBusqueda, setCodigoBusqueda] = useState('')
  const [reporteSeguimiento, setReporteSeguimiento] = useState(null)
  const [buscando, setBuscando] = useState(false)

  // Cargar config municipio
  useEffect(() => {
    apiClient.get('/api/municipio/').then(r => {
      setMunicipio(r.data)
      if (r.data.mapa_lat && r.data.mapa_lng) {
        setMapCenter([r.data.mapa_lat, r.data.mapa_lng])
      }
    }).catch(() => {})
  }, [])

  // Cargar reportes públicos
  useEffect(() => {
    if (tab === 'mapa') {
      apiClient.get('/api/reportes/public_map/').then(r => setReportesPublicos(r.data)).catch(() => {})
    }
  }, [tab])

  // Cargar capas
  useEffect(() => {
    if (tab === 'reportar') {
      apiClient.get('/api/capas/').then(r => setCapas(r.data)).catch(() => {})
    }
  }, [tab])

  // Cargar subcategorías al cambiar capa
  useEffect(() => {
    if (capaSeleccionada) {
      apiClient.get(`/api/capas/${capaSeleccionada}/subcategorias/`).then(r => {
        setSubcategorias(r.data)
        setForm(f => ({ ...f, subcategoria_id: '' }))
      }).catch(() => {})
    } else {
      setSubcategorias([])
    }
  }, [capaSeleccionada])

  // Seleccionar ubicación en el mapa del formulario
  const handleMapClick = (latlng) => {
    setMarcadorNuevo(latlng)
    setForm(f => ({ ...f, lat: latlng.lat.toFixed(6), lng: latlng.lng.toFixed(6) }))
    // Geocodificación inversa simple
    fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latlng.lat}&lon=${latlng.lng}&format=json`)
      .then(r => r.json())
      .then(d => {
        const dir = d.display_name?.split(',').slice(0, 3).join(', ') || ''
        setForm(f => ({ ...f, direccion: dir }))
      }).catch(() => {})
  }

  const handleEnviarReporte = async (e) => {
    e.preventDefault()
    if (!form.subcategoria_id) { toast.error('Selecciona el tipo de problema'); return }
    if (!form.descripcion.trim()) { toast.error('Describe el problema'); return }
    if (!form.lat || !form.lng) { toast.error('Haz clic en el mapa para indicar la ubicación'); return }

    setEnviando(true)
    try {
      const payload = {
        subcategoria_id: form.subcategoria_id,
        descripcion: form.descripcion,
        direccion: form.direccion,
        latitud: parseFloat(form.lat),
        longitud: parseFloat(form.lng),
        nombre_reportante: form.nombre_reportante,
        email_reportante: form.email_reportante,
        telefono_reportante: form.telefono_reportante,
      }
      const res = await apiClient.post('/api/reportes/', payload)
      setCodigoGenerado(res.data.codigo_seguimiento)
      toast.success('Reporte enviado correctamente')
      // Limpiar formulario
      setForm({ subcategoria_id:'', descripcion:'', direccion:'', lat:'', lng:'', nombre_reportante:'', email_reportante:'', telefono_reportante:'' })
      setMarcadorNuevo(null)
      setCapaSeleccionada('')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error al enviar el reporte')
    } finally {
      setEnviando(false)
    }
  }

  const handleBuscarSeguimiento = async () => {
    if (!codigoBusqueda.trim()) { toast.error('Ingresa el código de seguimiento'); return }
    setBuscando(true)
    setReporteSeguimiento(null)
    try {
      const res = await apiClient.get(`/api/seguimiento/${codigoBusqueda.trim().toUpperCase()}/`)
      setReporteSeguimiento(res.data.reporte)
    } catch {
      toast.error('No se encontró un reporte con ese código')
    } finally {
      setBuscando(false)
    }
  }

  const nombreMunicipio = municipio?.nombre || 'Mi Municipio'

  return (
    <div className="pc-container">
      {/* Header */}
      <header className="pc-header">
        <div className="pc-header-inner">
          {municipio?.logo_url
            ? <img src={municipio.logo_url} alt={nombreMunicipio} className="pc-logo" />
            : <div className="pc-logo-placeholder">🏛️</div>
          }
          <div>
            <h1>{nombreMunicipio}</h1>
            <p>Portal Ciudadano de Reportes Urbanos</p>
          </div>
        </div>
        <nav className="pc-tabs">
          <button className={tab === 'mapa' ? 'active' : ''} onClick={() => setTab('mapa')}>
            Mapa de Reportes
          </button>
          <button className={tab === 'reportar' ? 'active' : ''} onClick={() => setTab('reportar')}>
            Reportar Problema
          </button>
          <button className={tab === 'seguimiento' ? 'active' : ''} onClick={() => setTab('seguimiento')}>
            Seguimiento
          </button>
        </nav>
      </header>

      <main className="pc-main">

        {/* ── TAB: MAPA ── */}
        {tab === 'mapa' && (
          <div className="pc-mapa">
            <div className="pc-mapa-info">
              <strong>{reportesPublicos.length}</strong> reportes activos en tu municipio
            </div>
            <MapContainer center={mapCenter} zoom={mapZoom} className="pc-map">
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution="© OpenStreetMap"
              />
              {reportesPublicos.map(r => (
                <Marker
                  key={r.id}
                  position={[r.latitud, r.longitud]}
                  icon={iconReporte}
                >
                  <Popup>
                    <div className="pc-popup">
                      <strong>{r.subcategoria || r.categoria || 'Reporte'}</strong>
                      <span
                        className="pc-popup-estado"
                        style={{ background: ESTADOS_COLOR[r.estado] }}
                      >
                        {ESTADOS_LABEL[r.estado]}
                      </span>
                      <p>{r.descripcion?.slice(0, 100)}{r.descripcion?.length > 100 ? '…' : ''}</p>
                      <small>{r.direccion}</small>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        )}

        {/* ── TAB: REPORTAR ── */}
        {tab === 'reportar' && (
          <div className="pc-reportar">
            {codigoGenerado ? (
              <div className="pc-exito">
                <div className="pc-exito-icon">✅</div>
                <h2>Reporte enviado</h2>
                <p>Tu código de seguimiento es:</p>
                <div className="pc-codigo">{codigoGenerado}</div>
                <p className="pc-codigo-hint">Guarda este código para consultar el estado de tu reporte</p>
                <button className="pc-btn-primary" onClick={() => { setCodigoGenerado(null); setTab('seguimiento'); setCodigoBusqueda(codigoGenerado) }}>
                  Ver estado del reporte
                </button>
                <button className="pc-btn-secondary" onClick={() => setCodigoGenerado(null)}>
                  Enviar otro reporte
                </button>
              </div>
            ) : (
              <div className="pc-form-layout">
                {/* Formulario */}
                <form className="pc-form" onSubmit={handleEnviarReporte}>
                  <h2>Reportar un problema</h2>
                  <p className="pc-form-hint">Haz clic en el mapa para indicar la ubicación exacta del problema.</p>

                  <div className="pc-field">
                    <label>Tipo de problema</label>
                    <select value={capaSeleccionada} onChange={e => setCapaSeleccionada(e.target.value)} required>
                      <option value="">-- Selecciona categoría --</option>
                      {capas.map(c => (
                        <option key={c.id} value={c.id}>{c.nombre}</option>
                      ))}
                    </select>
                  </div>

                  {subcategorias.length > 0 && (
                    <div className="pc-field">
                      <label>Problema específico</label>
                      <select
                        value={form.subcategoria_id}
                        onChange={e => setForm(f => ({ ...f, subcategoria_id: e.target.value }))}
                        required
                      >
                        <option value="">-- Selecciona el problema --</option>
                        {subcategorias.map(s => (
                          <option key={s.id} value={s.id}>{s.nombre}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div className="pc-field">
                    <label>Descripción</label>
                    <textarea
                      value={form.descripcion}
                      onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
                      placeholder="Describe el problema con detalle..."
                      rows={3}
                      required
                    />
                  </div>

                  <div className="pc-field">
                    <label>Dirección (opcional)</label>
                    <input
                      type="text"
                      value={form.direccion}
                      onChange={e => setForm(f => ({ ...f, direccion: e.target.value }))}
                      placeholder="Se completa automáticamente al hacer clic en el mapa"
                    />
                  </div>

                  {form.lat && (
                    <div className="pc-ubicacion-ok">
                      Ubicación seleccionada: {parseFloat(form.lat).toFixed(4)}, {parseFloat(form.lng).toFixed(4)}
                    </div>
                  )}

                  <hr className="pc-sep" />
                  <p className="pc-form-hint">Datos de contacto (opcionales, para notificarte del avance)</p>

                  <div className="pc-field-row">
                    <div className="pc-field">
                      <label>Tu nombre</label>
                      <input
                        type="text"
                        value={form.nombre_reportante}
                        onChange={e => setForm(f => ({ ...f, nombre_reportante: e.target.value }))}
                        placeholder="Nombre (opcional)"
                      />
                    </div>
                    <div className="pc-field">
                      <label>Email</label>
                      <input
                        type="email"
                        value={form.email_reportante}
                        onChange={e => setForm(f => ({ ...f, email_reportante: e.target.value }))}
                        placeholder="tu@email.cl (opcional)"
                      />
                    </div>
                  </div>

                  <button type="submit" className="pc-btn-primary" disabled={enviando}>
                    {enviando ? 'Enviando...' : 'Enviar Reporte'}
                  </button>
                </form>

                {/* Mapa de selección */}
                <div className="pc-form-map-wrap">
                  <MapContainer center={mapCenter} zoom={mapZoom} className="pc-form-map">
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution="© OpenStreetMap"
                    />
                    <SeleccionarUbicacion onSelect={handleMapClick} />
                    {marcadorNuevo && (
                      <Marker position={marcadorNuevo} icon={iconNuevo}>
                        <Popup>Ubicación seleccionada</Popup>
                      </Marker>
                    )}
                  </MapContainer>
                  <p className="pc-map-hint">Haz clic en el mapa para marcar la ubicación del problema</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB: SEGUIMIENTO ── */}
        {tab === 'seguimiento' && (
          <div className="pc-seguimiento">
            <h2>Consultar estado de tu reporte</h2>
            <p>Ingresa el código de seguimiento que recibiste al reportar el problema.</p>

            <div className="pc-seguimiento-search">
              <input
                type="text"
                value={codigoBusqueda}
                onChange={e => setCodigoBusqueda(e.target.value.toUpperCase())}
                placeholder="Ej: ABC-1234"
                onKeyDown={e => e.key === 'Enter' && handleBuscarSeguimiento()}
                maxLength={10}
              />
              <button
                className="pc-btn-primary"
                onClick={handleBuscarSeguimiento}
                disabled={buscando}
              >
                {buscando ? 'Buscando...' : 'Consultar'}
              </button>
            </div>

            {reporteSeguimiento && (
              <div className="pc-resultado">
                <div className="pc-resultado-header">
                  <div>
                    <span className="pc-codigo-tag">{reporteSeguimiento.codigo_seguimiento}</span>
                    <h3>{reporteSeguimiento.subcategoria?.nombre || reporteSeguimiento.categoria?.nombre || 'Reporte'}</h3>
                  </div>
                  <span
                    className="pc-estado-badge"
                    style={{ background: ESTADOS_COLOR[reporteSeguimiento.estado] }}
                  >
                    {ESTADOS_LABEL[reporteSeguimiento.estado]}
                  </span>
                </div>

                <div className="pc-resultado-body">
                  <div className="pc-resultado-row">
                    <span>Descripción</span>
                    <p>{reporteSeguimiento.descripcion}</p>
                  </div>
                  {reporteSeguimiento.direccion && (
                    <div className="pc-resultado-row">
                      <span>Dirección</span>
                      <p>{reporteSeguimiento.direccion}</p>
                    </div>
                  )}
                  <div className="pc-resultado-row">
                    <span>Fecha de reporte</span>
                    <p>{new Date(reporteSeguimiento.fecha_creacion).toLocaleDateString('es-CL', {
                      year: 'numeric', month: 'long', day: 'numeric'
                    })}</p>
                  </div>
                  {reporteSeguimiento.prioridad && (
                    <div className="pc-resultado-row">
                      <span>Prioridad</span>
                      <p style={{ textTransform: 'capitalize' }}>{reporteSeguimiento.prioridad}</p>
                    </div>
                  )}
                </div>

                <div className="pc-progreso">
                  {['nuevo', 'proceso', 'resuelto'].map((est, i) => (
                    <div
                      key={est}
                      className={`pc-progreso-paso ${
                        ['nuevo','proceso','resuelto','cerrado'].indexOf(reporteSeguimiento.estado) >= i ? 'activo' : ''
                      }`}
                    >
                      <div className="pc-progreso-circulo">{i + 1}</div>
                      <span>{ESTADOS_LABEL[est]}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="pc-footer">
        <p>{nombreMunicipio} · Portal Ciudadano</p>
        {municipio?.email_contacto && <p><a href={`mailto:${municipio.email_contacto}`}>{municipio.email_contacto}</a></p>}
      </footer>
    </div>
  )
}
