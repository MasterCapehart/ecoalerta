
import React, { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents, ZoomControl } from 'react-leaflet'
import { MapPin, Check, AlertTriangle, Trash2, Info, Upload, Lock, ChevronLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useForm, Controller } from 'react-hook-form'
import apiClient, { API_ROUTES, getCapasUrbanas, getSubcategoriasPorCapa, iaClasificarReporte } from '../services/api'
import { toast } from './ToastContainer'
import OfflineService from '../services/OfflineService'
import AIService from '../services/AIService'
import './ReporteForm.css'

// Mapa de emojis por nombre de capa
const CAPA_EMOJIS = {
  'agua': '💧',
  'vialidad': '🛣️',
  'señalización': '🚦',
  'señalizacion': '🚦',
  'alumbrado': '💡',
  'áreas verdes': '🌳',
  'areas verdes': '🌳',
  'infraestructura': '🔧',
  'seguridad ciudadana': '🛡️',
  'seguridad': '🛡️',
  'emergencias': '🚨',
  'edificación': '🏗️',
  'edificacion': '🏗️',
  'aseo': '🗑️',
  'medio ambiente': '♻️',
}

// Mapa de colores por nombre de capa
const CAPA_COLORES = {
  'agua': '#3182ce',
  'vialidad': '#d69e2e',
  'señalización': '#dd6b20',
  'señalizacion': '#dd6b20',
  'alumbrado': '#ecc94b',
  'áreas verdes': '#38a169',
  'areas verdes': '#38a169',
  'infraestructura': '#718096',
  'seguridad ciudadana': '#553c9a',
  'seguridad': '#553c9a',
  'emergencias': '#e53e3e',
  'edificación': '#744210',
  'edificacion': '#744210',
  'aseo': '#2d3748',
  'medio ambiente': '#276749',
}

const getCapaEmoji = (nombre) => {
  const key = nombre?.toLowerCase().trim()
  return CAPA_EMOJIS[key] || '📋'
}

const getCapaColor = (nombre) => {
  const key = nombre?.toLowerCase().trim()
  return CAPA_COLORES[key] || '#4a5568'
}

// Capas de fallback si la API no responde
const CAPAS_FALLBACK = [
  { id: 1, nombre: 'Agua' },
  { id: 2, nombre: 'Vialidad' },
  { id: 3, nombre: 'Señalización' },
  { id: 4, nombre: 'Alumbrado' },
  { id: 5, nombre: 'Áreas Verdes' },
  { id: 6, nombre: 'Infraestructura' },
  { id: 7, nombre: 'Seguridad Ciudadana' },
  { id: 8, nombre: 'Emergencias' },
  { id: 9, nombre: 'Aseo' },
  { id: 10, nombre: 'Medio Ambiente' },
]

// Custom Icon for Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Helper component to move map
const MapUpdater = ({ center }) => {
  const map = useMapEvents({})
  useEffect(() => {
    if (center) map.flyTo(center, 15)
  }, [center, map])
  return null
}

const ReporteForm = () => {
  const navigate = useNavigate()
  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm({
    defaultValues: {
      categoria: '',
      subcategoria: '',
      ubicacion: null,
      direccion: '',
      fotos: [],
      descripcion: '',
      email: ''
    }
  })

  // State local para UI no relacionada con el formulario en sí o datos externos
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading] = useState(false)
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [codigoSeguimiento, setCodigoSeguimiento] = useState(null)
  const [mapCenter, setMapCenter] = useState([-29.9027, -71.252])
  const [aiSuggestion, setAiSuggestion] = useState(null)
  const [duplicateCheck, setDuplicateCheck] = useState({
    loading: false,
    found: false,
    count: 0,
    duplicates: [],
    radius: 50
  })
  const [confirmDuplicate, setConfirmDuplicate] = useState(false)

  // Estado para el flujo de selección capa → subcategoría
  const [capas, setCapas] = useState([])
  const [capaSeleccionada, setCapaSeleccionada] = useState(null)
  const [subcategorias, setSubcategorias] = useState([])
  const [subcategoriaSeleccionada, setSubcategoriaSeleccionada] = useState(null)
  const [loadingSubcategorias, setLoadingSubcategorias] = useState(false)

  // Mantenemos previews separado porque no se envía al backend, es solo visual
  const [fotoPreviews, setFotoPreviews] = useState([])

  // Estados IA — clasificación por descripción
  const [iaClasificando, setIaClasificando] = useState(false)
  const [iaSugerencia, setIaSugerencia] = useState(null)
  const [iaDuplicado, setIaDuplicado] = useState(null)

  // Watch values for conditional rendering/logic
  const ubicacion = watch('ubicacion')
  const fotos = watch('fotos')
  const direccion = watch('direccion')

  const checkPotentialDuplicates = async (lat, lng) => {
    if (!lat || !lng) return
    setDuplicateCheck(prev => ({ ...prev, loading: true }))
    try {
      const response = await apiClient.get(API_ROUTES.REPORTES_VERIFICAR_DUPLICADOS, {
        params: { lat, lng, radio: 60 }
      })
      const data = response.data || {}
      setDuplicateCheck({
        loading: false,
        found: Boolean(data.found),
        count: data.count || 0,
        duplicates: Array.isArray(data.duplicates) ? data.duplicates : [],
        radius: data.radius_meters || 60
      })
      if (data.found) {
        toast.warning(`Detectamos ${data.count} reporte(s) cercano(s). Revisa antes de enviar.`)
      }
    } catch (error) {
      console.error('Error verificando duplicados:', error)
      setDuplicateCheck({
        loading: false,
        found: false,
        count: 0,
        duplicates: [],
        radius: 60
      })
    }
  }

  useEffect(() => {
    const fetchCategorias = async () => {
      try {
        const response = await apiClient.get(API_ROUTES.CATEGORIAS)
        const data = response.data
        setCategorias(Array.isArray(data) ? data : (data.results || []))
      } catch {
        setCategorias([
          { id: 1, nombre: 'Residuos Domésticos' },
          { id: 2, nombre: 'Escombros' },
          { id: 3, nombre: 'Voluminosos' },
          { id: 4, nombre: 'Peligrosos' },
          { id: 6, nombre: 'Residuos Orgánicos' }
        ])
      }
    }

    const fetchCapas = async () => {
      try {
        const response = await getCapasUrbanas()
        const data = response.data
        const lista = Array.isArray(data) ? data : (data.results || [])
        setCapas(lista.length > 0 ? lista : CAPAS_FALLBACK)
      } catch {
        setCapas(CAPAS_FALLBACK)
      }
    }

    fetchCategorias()
    fetchCapas()

    // Geolocate on load
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords
          setMapCenter([latitude, longitude])
        },
        () => { }
      )
    }
  }, [])

  const handleSeleccionarCapa = async (capa) => {
    setCapaSeleccionada(capa)
    setSubcategoriaSeleccionada(null)
    setSubcategorias([])
    setValue('subcategoria', '', { shouldValidate: false })
    setValue('categoria', '', { shouldValidate: false })
    setLoadingSubcategorias(true)
    try {
      const response = await getSubcategoriasPorCapa(capa.id)
      const data = response.data
      setSubcategorias(Array.isArray(data) ? data : (data.results || []))
    } catch {
      // Si la API no devuelve subcategorías, usar la capa como categoría directa
      setSubcategorias([])
      setValue('categoria', capa.id, { shouldValidate: true })
    } finally {
      setLoadingSubcategorias(false)
    }
  }

  const handleSeleccionarSubcategoria = (sub) => {
    setSubcategoriaSeleccionada(sub)
    // Mantener compatibilidad: categoria = id de la subcategoría (o capa si no hay sub)
    setValue('subcategoria', sub.id, { shouldValidate: true })
    setValue('categoria', sub.categoria || capaSeleccionada?.id, { shouldValidate: true })
  }

  const handleVolverACapas = () => {
    setCapaSeleccionada(null)
    setSubcategorias([])
    setSubcategoriaSeleccionada(null)
    setValue('subcategoria', '', { shouldValidate: false })
    setValue('categoria', '', { shouldValidate: false })
  }

  const handleDescripcionIA = async (texto) => {
    if (texto.length < 15) return // Esperar mínimo 15 chars
    clearTimeout(window._iaTimer)
    window._iaTimer = setTimeout(async () => {
      setIaClasificando(true)
      setIaSugerencia(null)
      try {
        const res = await iaClasificarReporte(texto)
        if (res.data && res.data.capa) {
          setIaSugerencia(res.data)
        }
      } catch (e) {
        // silencioso - IA es opcional
      } finally {
        setIaClasificando(false)
      }
    }, 1000) // debounce 1 segundo
  }

  const MapClickHandler = () => {
    useMapEvents({
      click: async (e) => {
        const { lat, lng } = e.latlng
        setValue('ubicacion', { lat, lng }, { shouldValidate: true })
        setConfirmDuplicate(false)
        checkPotentialDuplicates(lat, lng)

        try {
          const resp = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
          const data = await resp.json()
          if (data.display_name) setValue('direccion', data.display_name)
        } catch { /* ignore */ }
      }
    })
    return null
  }

  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Geolocalización no soportada')
      return
    }
    if (!window.isSecureContext) {
      toast.error('La geolocalización requiere un contexto seguro (https o localhost).')
      return
    }

    toast.info('Obteniendo ubicación actual...')
    setLoading(true)
    const options = { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords
        setMapCenter([latitude, longitude])
        setValue('ubicacion', { lat: latitude, lng: longitude }, { shouldValidate: true })
        setConfirmDuplicate(false)
        checkPotentialDuplicates(latitude, longitude)
        toast.info('Ubicación actualizada')
        setLoading(false)
      },
      (err) => {
        console.warn(err)
        if (err?.code === 1) {
          toast.error('Permiso de ubicación denegado. Habilítalo en el navegador.')
        } else if (err?.code === 2) {
          toast.error('No se pudo determinar tu ubicación actual.')
        } else if (err?.code === 3) {
          toast.error('Tiempo de espera agotado al obtener ubicación.')
        } else {
          toast.error('Error al obtener ubicación. Revisa permisos.')
        }
        setLoading(false)
      },
      options
    )
  }

  const handlePhotoUpload = async (files) => {
    if (!files || files.length === 0) return
    const fileList = Array.from(files)
    const validFiles = []

    // Current photos from state
    const currentFotos = fotos || []
    const newPreviews = [...fotoPreviews]

    if (currentFotos.length + fileList.length > 5) {
      toast.warning('Máximo 5 fotos permitidas')
      return
    }

    fileList.forEach(file => {
      if (!file.type.startsWith('image/')) return
      validFiles.push(file)
      newPreviews.push(URL.createObjectURL(file))
    })

    if (validFiles.length > 0) {
      const updatedFotos = [...currentFotos, ...validFiles]
      setValue('fotos', updatedFotos, { shouldValidate: true })
      setFotoPreviews(newPreviews)

      // AI Classification Logic
      try {
        const img = document.createElement('img')
        img.src = URL.createObjectURL(validFiles[0])
        img.onload = async () => {
          const suggestion = await AIService.classifyImage(img)
          if (suggestion) {
            setAiSuggestion(suggestion)
            toast.info(`💡 Sugerencia IA: Parece ser ${suggestion.categoryName}`)
          }
        }
      } catch (error) {
        console.error("AI Error:", error)
      }
    }
  }

  const removePhoto = (index) => {
    const currentFotos = [...(fotos || [])]
    const currentPreviews = [...fotoPreviews]

    currentFotos.splice(index, 1)
    currentPreviews.splice(index, 1)

    setValue('fotos', currentFotos, { shouldValidate: true })
    setFotoPreviews(currentPreviews)
  }

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('categoria', data.categoria)
      if (data.subcategoria) formData.append('subcategoria', data.subcategoria)
      formData.append('lat', data.ubicacion.lat)
      formData.append('lng', data.ubicacion.lng)
      if (data.descripcion) formData.append('descripcion', data.descripcion)
      if (data.email) formData.append('email', data.email)
      if (data.direccion) formData.append('direccion', data.direccion)

      // Enviar metadatos de IA si existen (Fase 12-C)
      if (aiSuggestion) {
        formData.append('ai_metadata', JSON.stringify({
          category: aiSuggestion.categoryName,
          product: aiSuggestion.detectedProduct,
          confidence: aiSuggestion.score
        }))
      }

      if (data.fotos.length > 0) {
        formData.append('foto', data.fotos[0])
        for (let i = 1; i < data.fotos.length; i++) {
          formData.append('fotos_adicionales', data.fotos[i])
        }
      }

      if (duplicateCheck.found && !confirmDuplicate) {
        toast.warning('Hay posibles duplicados. Marca la confirmación para continuar.')
        setLoading(false)
        return
      }
      if (confirmDuplicate) {
        formData.append('permitir_duplicado', 'true')
      }

      const response = await apiClient.post(API_ROUTES.REPORTES, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setCodigoSeguimiento(response.data.codigo_seguimiento)
      setShowSuccessModal(true)

    } catch (error) {
      if (!navigator.onLine) {
        await OfflineService.saveReport({
          categoria: data.categoria,
          lat: data.ubicacion.lat,
          lng: data.ubicacion.lng,
          descripcion: data.descripcion,
          email: data.email,
          direccion: data.direccion,
        })
        setCodigoSeguimiento('PENDIENTE-SYNC')
        setShowSuccessModal(true)
      } else {
        toast.error('Error al enviar reporte')
        console.error(error)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    reset()
    setFotoPreviews([])
    setAiSuggestion(null)
    setShowSuccessModal(false)
    setCodigoSeguimiento(null)
    setCapaSeleccionada(null)
    setSubcategorias([])
    setSubcategoriaSeleccionada(null)
  }

  // Extraer onChange de register para descripcion (evita sobreescritura con spread)
  const { onChange: onDescripcionChange, ...descripcionRegisterProps } = register('descripcion')

  return (
    <div className="report-page">
      {/* Header Banner */}
      <div className="header-banner">
        <div className="logo-section">
          <div className="logo-icon">
            <MapPin size={24} fill="currentColor" />
          </div>
          <div className="brand-text">
            <div className="brand-title">
              ECO <span className="highlight">ALERTA</span>
            </div>
            <div className="brand-slogan">
              RADAR INTELIGENTE, CIUDAD SOSTENIBLE
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => navigate('/login')}
          style={{
            marginLeft: 'auto',
            background: 'rgba(255, 255, 255, 0.2)',
            border: '1px solid rgba(255, 255, 255, 0.5)',
            color: '#fff',
            borderRadius: '8px',
            padding: '8px 14px',
            cursor: 'pointer',
            fontWeight: 600
          }}
        >
          Iniciar sesión
        </button>
      </div>

      <div className="report-content">
        {/* Left: Map */}
        <div className="map-container">
          <div className={`map-view ${errors.ubicacion ? 'has-error' : ''}`}>
            <MapContainer 
              center={mapCenter} 
              zoom={13} 
              style={{ height: '100%', width: '100%' }} 
              zoomControl={false}
              dragging={!L.Browser.mobile}
              tap={!L.Browser.mobile}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; OpenStreetMap'
              />
              <ZoomControl position="topleft" />
              <MapUpdater center={mapCenter} />
              <MapClickHandler />
              {ubicacion && (
                <Marker position={[ubicacion.lat, ubicacion.lng]} />
              )}
            </MapContainer>

            {ubicacion && (
              <div className="map-controls-overlay">
                <div className="location-badge">
                  <Check size={14} /> Ubicación seleccionada
                </div>
              </div>
            )}

            <button className="btn-use-location" onClick={handleGetCurrentLocation} type="button">
              <MapPin size={16} color="#d32f2f" fill="#d32f2f" />
              Usar mi ubicación
            </button>
          </div>
          {errors.ubicacion && <span className="error-text">Debes seleccionar una ubicación en el mapa</span>}

          {ubicacion && (
            <div className="coords-bar">
              <span>Lat: {ubicacion.lat.toFixed(6)}, Lng: {ubicacion.lng.toFixed(6)}</span>
              <Check size={16} />
            </div>
          )}

          {duplicateCheck.loading && (
            <div className="duplicate-warning duplicate-warning--loading">
              Verificando reportes cercanos...
            </div>
          )}

          {!duplicateCheck.loading && duplicateCheck.found && (
            <div className="duplicate-warning">
              <div className="duplicate-warning__title">
                <AlertTriangle size={16} />
                Posible duplicado detectado ({duplicateCheck.count})
              </div>
              <p className="duplicate-warning__text">
                Encontramos reportes activos en un radio aproximado de {duplicateCheck.radius}m.
              </p>
              <ul className="duplicate-warning__list">
                {duplicateCheck.duplicates.slice(0, 3).map((rep) => (
                  <li key={rep.id || rep.codigo_seguimiento}>
                    <strong>{rep.codigo_seguimiento || `#${rep.id}`}</strong> · {rep.categoria_nombre || 'Sin categoría'} · {rep.estado}
                  </li>
                ))}
              </ul>
              <label className="duplicate-warning__confirm">
                <input
                  type="checkbox"
                  checked={confirmDuplicate}
                  onChange={(e) => setConfirmDuplicate(e.target.checked)}
                />
                Confirmo que deseo enviar este reporte de todas formas.
              </label>
            </div>
          )}

          <div className="address-bar">
            <MapPin size={16} color="#d32f2f" />
            <span>{direccion || "La Serena, Región de Coquimbo, Chile"}</span>
          </div>
        </div>

        {/* Right: Form */}
        <div className="form-container">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="form-group">
              <label className="form-label">
                <span className="text-gray-600">Fotografía del vertedero *</span>
              </label>

              <label className={`upload-box ${errors.fotos ? 'error-border' : ''}`}>
                <div className="upload-placeholder">
                  <div className="upload-icon-circle">
                    <Upload size={16} strokeWidth={3} />
                  </div>
                  <span>Arrastra una imagen aquí o haz clic para seleccionar</span>
                </div>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(e) => handlePhotoUpload(e.target.files)}
                  hidden
                />
              </label>
              {errors.fotos && <span className="error-text">Al menos una foto es obligatoria</span>}

              <div className="preview-row">
                {fotoPreviews.map((preview, idx) => (
                  <div key={idx} style={{ position: 'relative' }}>
                    <img src={preview} className="preview-thumb" alt="preview" />
                    <button
                      type="button"
                      onClick={() => removePhoto(idx)}
                      style={{
                        position: 'absolute', top: -5, right: -5,
                        background: 'red', color: 'white',
                        borderRadius: '50%', border: 'none',
                        width: 18, height: 18, cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                      }}
                    >
                      &times;
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Suggestion Chip */}
            {aiSuggestion && (
              <div
                className="ai-suggestion-chip"
                onClick={() => {
                  setValue('categoria', aiSuggestion.categoryId, { shouldValidate: true })
                  setAiSuggestion(null)
                  toast.success('Categoría aplicada automáticamente')
                }}
                style={{
                  background: '#e3f2fd',
                  border: '1px solid #2196f3',
                  borderRadius: '8px',
                  padding: '10px',
                  marginBottom: '15px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  animation: 'fadeIn 0.5s ease-in'
                }}
              >
                <div style={{ fontSize: '28px', filter: 'drop-shadow(0 0 5px rgba(33, 150, 243, 0.3))' }}>🤖</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 'bold', color: '#1565c0', fontSize: '14px', marginBottom: '2px' }}>
                    IA Detectó: {aiSuggestion.categoryName}
                  </div>
                  {aiSuggestion.detectedProduct && (
                    <div style={{ fontSize: '12px', color: '#0277bd', fontStyle: 'italic', marginBottom: '4px' }}>
                      Producto específico: <strong>{aiSuggestion.detectedProduct}</strong>
                    </div>
                  )}
                  <div style={{ fontSize: '11px', color: '#546e7a', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Check size={12} /> Pulsa aquí para clasificar automáticamente
                  </div>
                </div>
                <div style={{ background: '#2196f3', color: 'white', fontSize: '10px', padding: '2px 6px', borderRadius: '10px', fontWeight: 'bold' }}>
                  {Math.round(aiSuggestion.score * 100)}%
                </div>
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Categoría del problema *</label>

              {/* Paso 1: Selector visual de Capa Urbana */}
              {!capaSeleccionada && (
                <>
                  <div className="step-label">Paso 1 — Selecciona un área</div>
                  <div className="capa-selector">
                    {capas.map(capa => {
                      const color = getCapaColor(capa.nombre)
                      return (
                        <button
                          key={capa.id}
                          type="button"
                          className="capa-card"
                          style={{ '--capa-color': color }}
                          onClick={() => handleSeleccionarCapa(capa)}
                        >
                          <div className="capa-icon">{getCapaEmoji(capa.nombre)}</div>
                          <div className="capa-nombre">{capa.nombre}</div>
                        </button>
                      )
                    })}
                  </div>
                  {errors.categoria && (
                    <span className="error-text">Debes seleccionar una categoría</span>
                  )}
                </>
              )}

              {/* Paso 2: Selector de Subcategoría */}
              {capaSeleccionada && (
                <>
                  <button
                    type="button"
                    className="capa-back-btn"
                    onClick={handleVolverACapas}
                  >
                    <ChevronLeft size={14} /> Volver a áreas
                  </button>

                  <div
                    className="capa-card selected"
                    style={{
                      '--capa-color': getCapaColor(capaSeleccionada.nombre),
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      marginBottom: 12,
                      cursor: 'default',
                      textAlign: 'left'
                    }}
                  >
                    <span style={{ fontSize: 22 }}>{getCapaEmoji(capaSeleccionada.nombre)}</span>
                    <strong className="capa-nombre" style={{ fontSize: 14 }}>{capaSeleccionada.nombre}</strong>
                  </div>

                  {loadingSubcategorias ? (
                    <div className="helper-text">Cargando subcategorías...</div>
                  ) : subcategorias.length > 0 ? (
                    <>
                      <div className="step-label">Paso 2 — Tipo específico</div>
                      <div className="subcategoria-selector">
                        {subcategorias.map(sub => {
                          const prioridadKey = (sub.prioridad || 'normal').toLowerCase()
                          const slaHoras = sub.sla_horas || sub.tiempo_respuesta_horas
                          return (
                            <div
                              key={sub.id}
                              className={`subcategoria-item ${subcategoriaSeleccionada?.id === sub.id ? 'selected' : ''}`}
                              onClick={() => handleSeleccionarSubcategoria(sub)}
                            >
                              <div>
                                <div className="subcategoria-nombre">{sub.nombre}</div>
                                <div className="subcategoria-badges">
                                  {slaHoras && (
                                    <span className="sla-badge">
                                      ⏱ Respuesta: {slaHoras}h
                                    </span>
                                  )}
                                  <span className={`prioridad-badge ${prioridadKey}`}>
                                    {sub.prioridad || 'Normal'}
                                  </span>
                                </div>
                              </div>
                              {subcategoriaSeleccionada?.id === sub.id && (
                                <Check size={16} color="#4299e1" />
                              )}
                            </div>
                          )
                        })}
                      </div>
                      {errors.subcategoria && (
                        <span className="error-text">Debes seleccionar un tipo específico</span>
                      )}
                    </>
                  ) : (
                    // Sin subcategorías: la capa funciona directamente como categoría
                    <div className="helper-text" style={{ color: '#38a169' }}>
                      <Check size={13} /> Área seleccionada correctamente
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Correo electrónico (opcional)</label>
              <input
                type="email"
                className="form-control"
                placeholder="tu@email.com"
                {...register('email', {
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: "Dirección de email inválida"
                  }
                })}
              />
              {errors.email && <span className="error-text">{errors.email.message}</span>}
              <div className="helper-text">Para recibir notificaciones sobre tu reporte</div>
            </div>

            <div className="form-group">
              <label className="form-label">
                <Lock size={14} color="#9e9e9e" />
                Descripción
              </label>
              <textarea
                className="form-control"
                placeholder="Describe el vertedero (tamaño, tiempo, etc.)"
                {...descripcionRegisterProps}
                onChange={(e) => {
                  onDescripcionChange(e)
                  handleDescripcionIA(e.target.value)
                }}
              />

              {/* Sugerencia IA */}
              {iaClasificando && (
                <div className="ia-clasificando">
                  <span className="ia-spinner">🤖</span> Analizando con IA...
                </div>
              )}
              {iaSugerencia && !iaClasificando && (
                <div className="ia-sugerencia">
                  <div className="ia-sugerencia-header">
                    <span>🤖 IA sugiere:</span>
                    <span className="ia-confianza">{Math.round(iaSugerencia.confianza * 100)}% confianza</span>
                  </div>
                  <div className="ia-sugerencia-body">
                    <strong>{iaSugerencia.capa}</strong> → {iaSugerencia.subcategoria}
                    <span className={`ia-prioridad ia-prioridad-${iaSugerencia.prioridad}`}>
                      {iaSugerencia.prioridad}
                    </span>
                  </div>
                  <div className="ia-sugerencia-razon">{iaSugerencia.razon}</div>
                  <button
                    type="button"
                    className="ia-aplicar-btn"
                    onClick={() => {
                      const capaEncontrada = capas.find(c => c.id === iaSugerencia.capa_id)
                      if (capaEncontrada) {
                        handleSeleccionarCapa(capaEncontrada)
                        setTimeout(() => {
                          const sub = { id: iaSugerencia.subcategoria_id, nombre: iaSugerencia.subcategoria, prioridad_base: iaSugerencia.prioridad }
                          handleSeleccionarSubcategoria(sub)
                        }, 100)
                      }
                      setIaSugerencia(null)
                    }}
                  >
                    ✓ Aplicar sugerencia
                  </button>
                </div>
              )}
            </div>

            <button
              type="submit"
              className="btn-submit"
              disabled={loading}
            >
              {loading ? 'Enviando...' : 'Enviar Reporte'}
            </button>
          </form>
        </div>
      </div>

      {/* Success Modal */}
      {showSuccessModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{
              width: 60, height: 60, borderRadius: '50%', background: '#e8f5e9',
              display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 15px'
            }}>
              <Check size={30} color="#2e7d32" />
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 10, color: '#1b5e20' }}>¡Reporte Enviado!</h2>
            <p style={{ color: '#616161', marginBottom: 20 }}>
              Gracias por tu colaboración.<br />
              Tu código: <strong style={{ background: '#f5f5f5', padding: '2px 6px' }}>{codigoSeguimiento}</strong>
            </p>
            <button
              onClick={handleReset}
              className="btn-submit"
            >
              Nuevo Reporte
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReporteForm
