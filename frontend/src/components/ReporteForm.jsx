import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './ReporteForm.css'
import logo from '../assets/images/Ecoalerta-logo-min.png'
import { API_ENDPOINTS } from '../config'

// Fix para iconos de Leaflet en React
import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

function MapClickHandler({ onLocationSelect }) {
  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng)
    },
  })
  return null
}

function ReporteForm() {
  const [ubicacion, setUbicacion] = useState(null)
  const navigate = useNavigate()
  const [categoria, setCategoria] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [foto, setFoto] = useState(null)
  const [fotoPreview, setFotoPreview] = useState(null)
  const [email, setEmail] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [codigoSeguimiento, setCodigoSeguimiento] = useState('')
  const [loading, setLoading] = useState(false)
  const [categorias, setCategorias] = useState([])

  const handleLocationSelect = (latlng) => {
    setUbicacion(latlng)
  }

  const handleFotoChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setFoto(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setFotoPreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  // Cargar categorías al montar el componente
  useEffect(() => {
    const fetchCategorias = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.CATEGORIAS)
        const data = await response.json()
        setCategorias(Array.isArray(data) ? data : data.results || [])
      } catch (error) {
        console.error('Error al cargar categorías:', error)
      }
    }
    fetchCategorias()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    if (!ubicacion) {
      alert('Por favor, selecciona una ubicación en el mapa')
      setLoading(false)
      return
    }

    if (!categoria) {
      alert('Por favor, selecciona una categoría')
      setLoading(false)
      return
    }

    try {
      const formData = new FormData()
      formData.append('categoria', categoria)
      formData.append('descripcion', descripcion)
      if (email) formData.append('email', email)
      if (foto) formData.append('foto', foto)
      formData.append('lat', ubicacion.lat)
      formData.append('lng', ubicacion.lng)

      const response = await fetch(API_ENDPOINTS.REPORTES, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (data.codigo_seguimiento) {
        setCodigoSeguimiento(data.codigo_seguimiento)
        setShowModal(true)
      } else {
        alert(data.error || 'Error al enviar el reporte')
      }
    } catch (error) {
      console.error('Error al enviar reporte:', error)
      alert('Error al conectar con el servidor. Verifica que el backend esté corriendo.')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setUbicacion(null)
    setCategoria('')
    setDescripcion('')
    setFoto(null)
    setFotoPreview(null)
    setEmail('')
    setShowModal(false)
  }

  return (
    <>
      <div className="container">
        <div className="header">
          <img src={logo} alt="logo-ecoalerta" />
          <button 
              onClick={() => navigate('/login')}
              className="back-button"
          >
              ← Volver
          </button>
        </div>

        <div className="form-section">
          {/* Mapa */}
          <div className="map-container">
            <MapContainer
              center={[-29.9533, -71.3395]}
              zoom={12}
              style={{ height: '100%', width: '100%', borderRadius: '20px' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; OpenStreetMap contributors'
              />
              <MapClickHandler onLocationSelect={handleLocationSelect} />
              {ubicacion && <Marker position={[ubicacion.lat, ubicacion.lng]} />}
            </MapContainer>
            <input
              type="text"
              value={ubicacion ? `Lat: ${ubicacion.lat.toFixed(6)}, Lng: ${ubicacion.lng.toFixed(6)}` : ''}
              placeholder="Haz clic en el mapa para seleccionar ubicación"
              readOnly
            />
          </div>

          {/* Formulario */}
          <div className="form-container">
            <form onSubmit={handleSubmit}>
              {/* Fotografía */}
              <div className="form-group">
                <label>Fotografía del vertedero *</label>
                <div className="file-input-wrapper">
                  <input
                    type="file"
                    id="foto"
                    accept="image/*"
                    onChange={handleFotoChange}
                    required
                  />
                  <label htmlFor="foto" className="file-input-label">
                    {foto ? foto.name : '📷 Seleccionar fotografía'}
                  </label>
                </div>
                {fotoPreview && (
                  <img src={fotoPreview} alt="Preview" className="preview-image" />
                )}
              </div>

              {/* Categoría */}
              <div className="form-group">
                <label>Tipo de residuos *</label>
                <select
                  value={categoria}
                  onChange={(e) => setCategoria(e.target.value)}
                  required
                >
                  <option value="">Seleccione una opción</option>
                  {categorias.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.nombre}</option>
                  ))}
                </select>
              </div>

              {/* Email */}
              <div className="form-group">
                <label>Correo electrónico (opcional)</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tu@email.com"
                />
                <p className="help-text">Para recibir notificaciones sobre tu reporte</p>
              </div>

              {/* Descripción */}
              <div className="form-group">
                <label>Descripción</label>
                <textarea
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  placeholder="Describe el vertedero (tamaño, tiempo, etc.)"
                />
              </div>

              <button type="submit" className="btn" disabled={loading}>
                {loading ? 'Enviando...' : 'Enviar Reporte'}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Modal de éxito */}
      {showModal && (
        <div className="success-modal">
          <div className="modal-content">
            <div className="success-icon">✅</div>
            <h2>¡Reporte Enviado!</h2>
            <p>Tu reporte ha sido registrado exitosamente</p>
            <div className="tracking-code">{codigoSeguimiento}</div>
            <p style={{ marginBottom: '20px' }}>Guarda este código para hacer seguimiento</p>
            <button className="modal-btn" onClick={resetForm}>Hacer otro reporte</button>
          </div>
        </div>
      )}
    </>
  )
}

export default ReporteForm