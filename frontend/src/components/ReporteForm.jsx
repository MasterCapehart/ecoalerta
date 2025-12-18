import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './ReporteForm.css'
import logo from '../assets/images/Ecoalerta-logo-min.png'
import { API_ROUTES } from '../config'
import apiClient from '../services/api'
import { toast } from './ToastContainer'

// Fix para iconos de Leaflet en React
import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

function MapClickHandler({ onLocationSelect, onMapReady }) {
  const map = useMapEvents({
    click(e) {
      onLocationSelect(e.latlng)
    },
  })

  useEffect(() => {
    if (onMapReady && map) {
      onMapReady(map)
    }
  }, [onMapReady, map])

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
  const [errors, setErrors] = useState({})
  const [isDragging, setIsDragging] = useState(false)
  const [mapInstance, setMapInstance] = useState(null)

  const handleLocationSelect = (latlng) => {
    setUbicacion(latlng)
    setErrors(prev => ({ ...prev, ubicacion: '' }))
  }

  const handleFotoChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      // Validar tamaño (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('La imagen es demasiado grande. Máximo 5MB')
        return
      }
      // Validar tipo
      if (!file.type.startsWith('image/')) {
        toast.error('Por favor selecciona una imagen válida')
        return
      }
      setFoto(file)
      setErrors(prev => ({ ...prev, foto: '' }))
      const reader = new FileReader()
      reader.onloadend = () => {
        setFotoPreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('La imagen es demasiado grande. Máximo 5MB')
        return
      }
      if (!file.type.startsWith('image/')) {
        toast.error('Por favor selecciona una imagen válida')
        return
      }
      setFoto(file)
      setErrors(prev => ({ ...prev, foto: '' }))
      const reader = new FileReader()
      reader.onloadend = () => {
        setFotoPreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      toast.error('Tu navegador no soporta geolocalización')
      return
    }

    if (!mapInstance) {
      toast.error('El mapa aún se está cargando, intenta de nuevo en un momento')
      return
    }

    const successHandler = (position) => {
      const { latitude, longitude } = position.coords
      const latlng = { lat: latitude, lng: longitude }

      mapInstance.flyTo([latitude, longitude], 16, {
        duration: 1.5,
      })

      handleLocationSelect(latlng)
      toast.info('Ubicación actual detectada')
    }

    const fallbackLocateByIP = async () => {
      try {
        toast.info('Intentando ubicación aproximada por IP...')
        const response = await fetch('https://ipapi.co/json/')
        if (!response.ok) {
          throw new Error('Respuesta inválida del servicio de geolocalización por IP')
        }
        const data = await response.json()
        const latitude = parseFloat(data.latitude)
        const longitude = parseFloat(data.longitude)

        if (!latitude || !longitude) {
          throw new Error('Sin coordenadas válidas desde IP')
        }

        const latlng = { lat: latitude, lng: longitude }

        mapInstance.flyTo([latitude, longitude], 12, {
          duration: 1.5,
        })

        handleLocationSelect(latlng)
        toast.success('Usando ubicación aproximada por IP')
      } catch (error) {
        console.error('Error al obtener ubicación por IP:', error)
        toast.error('Tu dispositivo no pudo calcular tu ubicación. Verifica que tengas activada la ubicación en Windows y conexión a internet.')
      }
    }

    const errorHandler = (error) => {
      console.error('Error de geolocalización:', error)

      if (error.code === error.PERMISSION_DENIED) {
        toast.error('Permiso de ubicación denegado. Activa los permisos en tu navegador.')
        return
      }

      if (error.code === error.POSITION_UNAVAILABLE || error.code === error.TIMEOUT) {
        // Fallback a ubicación aproximada por IP
        fallbackLocateByIP()
        return
      }

      toast.error('Ocurrió un error al obtener tu ubicación.')
    }

    navigator.geolocation.getCurrentPosition(
      successHandler,
      errorHandler,
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 0,
      }
    )
  }

  const validateEmail = (email) => {
    if (!email) return true // Email es opcional
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return re.test(email)
  }

  // Cargar categorías al montar el componente
  useEffect(() => {
    const fetchCategorias = async () => {
      try {
        const response = await apiClient.get(API_ROUTES.CATEGORIAS)
        const data = response.data
        setCategorias(Array.isArray(data) ? data : data.results || [])
      } catch (error) {
        console.error('Error al cargar categorías:', error)
        toast.error('Error al cargar las categorías')
      }
    }
    fetchCategorias()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    const newErrors = {}
    
    if (!ubicacion) {
      newErrors.ubicacion = 'Por favor, selecciona una ubicación en el mapa'
    }

    if (!categoria) {
      newErrors.categoria = 'Por favor, selecciona una categoría'
    }

    if (!foto) {
      newErrors.foto = 'Por favor, selecciona una fotografía'
    }

    if (email && !validateEmail(email)) {
      newErrors.email = 'Por favor, ingresa un email válido'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      Object.values(newErrors).forEach(error => toast.error(error))
      setLoading(false)
      return
    }

    setErrors({})

    try {
      const formData = new FormData()
      formData.append('categoria', categoria)
      formData.append('descripcion', descripcion)
      if (email) formData.append('email', email)
      if (foto) formData.append('foto', foto)
      formData.append('lat', ubicacion.lat)
      formData.append('lng', ubicacion.lng)

      const response = await apiClient.post(API_ROUTES.REPORTES, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const data = response.data

      if (data.codigo_seguimiento) {
        setCodigoSeguimiento(data.codigo_seguimiento)
        setShowModal(true)
        toast.success('Reporte enviado exitosamente')
      } else {
        toast.error(data.error || 'Error al enviar el reporte')
      }
    } catch (error) {
      console.error('Error al enviar reporte:', error)
      toast.error('Error al conectar con el servidor. Verifica que el backend esté corriendo.')
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
            <div className="map-wrapper">
              <MapContainer
                center={[-29.9533, -71.3395]}
                zoom={12}
                style={{ height: '400px', width: '100%', borderRadius: '20px' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; OpenStreetMap contributors'
                />
                <MapClickHandler 
                  onLocationSelect={handleLocationSelect} 
                  onMapReady={setMapInstance}
                />
                {ubicacion && <Marker position={[ubicacion.lat, ubicacion.lng]} />}
              </MapContainer>
              <button
                type="button"
                className="locate-button"
                onClick={handleLocateMe}
              >
                <span className="locate-icon">📌</span>
                <span className="locate-label">Usar mi ubicación</span>
              </button>
              {ubicacion && (
                <div className="map-accuracy-indicator">
                  <span className="accuracy-icon">📍</span>
                  <span className="accuracy-text">Ubicación seleccionada</span>
                </div>
              )}
            </div>
            <div className={`map-coordinates ${errors.ubicacion ? 'error' : ''} ${ubicacion ? 'has-location' : ''}`}>
              <input
                type="text"
                value={ubicacion ? `Lat: ${ubicacion.lat.toFixed(6)}, Lng: ${ubicacion.lng.toFixed(6)}` : ''}
                placeholder="Haz clic en el mapa para seleccionar ubicación"
                readOnly
              />
              {ubicacion && <span className="location-check">✓</span>}
            </div>
            {errors.ubicacion && <span className="error-message">{errors.ubicacion}</span>}
          </div>

          {/* Formulario */}
          <div className="form-container">
            <form onSubmit={handleSubmit}>
              {/* Fotografía */}
              <div className="form-group">
                <label>Fotografía del vertedero *</label>
                <div 
                  className={`file-input-wrapper ${isDragging ? 'dragging' : ''} ${errors.foto ? 'error' : ''} ${foto ? 'has-file' : ''}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <input
                    type="file"
                    id="foto"
                    accept="image/*"
                    onChange={handleFotoChange}
                    required
                  />
                  <label htmlFor="foto" className="file-input-label">
                    {foto ? (
                      <>
                        <span className="file-icon">✅</span>
                        <span className="file-name">{foto.name}</span>
                        <span className="file-size">({(foto.size / 1024 / 1024).toFixed(2)} MB)</span>
                      </>
                    ) : (
                      <>
                        <span className="file-icon">📷</span>
                        <span>Arrastra una imagen aquí o haz clic para seleccionar</span>
                      </>
                    )}
                  </label>
                </div>
                {errors.foto && <span className="error-message">{errors.foto}</span>}
                {fotoPreview && (
                  <div className="preview-container">
                    <img src={fotoPreview} alt="Preview" className="preview-image" />
                    <button 
                      type="button"
                      className="remove-image-btn"
                      onClick={() => {
                        setFoto(null)
                        setFotoPreview(null)
                        setErrors(prev => ({ ...prev, foto: '' }))
                      }}
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>

              {/* Categoría */}
              <div className="form-group">
                <label>Tipo de residuos *</label>
                <select
                  value={categoria}
                  onChange={(e) => {
                    setCategoria(e.target.value)
                    setErrors(prev => ({ ...prev, categoria: '' }))
                  }}
                  className={errors.categoria ? 'error' : ''}
                  required
                >
                  <option value="">Seleccione una opción</option>
                  {categorias.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.nombre}</option>
                  ))}
                </select>
                {errors.categoria && <span className="error-message">{errors.categoria}</span>}
              </div>

              {/* Email */}
              <div className="form-group">
                <label>Correo electrónico (opcional)</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value)
                    if (e.target.value && !validateEmail(e.target.value)) {
                      setErrors(prev => ({ ...prev, email: 'Email inválido' }))
                    } else {
                      setErrors(prev => ({ ...prev, email: '' }))
                    }
                  }}
                  onBlur={(e) => {
                    if (e.target.value && !validateEmail(e.target.value)) {
                      setErrors(prev => ({ ...prev, email: 'Email inválido' }))
                    }
                  }}
                  placeholder="tu@email.com"
                  className={errors.email ? 'error' : ''}
                />
                {errors.email && <span className="error-message">{errors.email}</span>}
                {!errors.email && email && validateEmail(email) && (
                  <span className="success-message">✓ Email válido</span>
                )}
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