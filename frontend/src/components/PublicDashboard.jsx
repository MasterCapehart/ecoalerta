import { useState, useEffect, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { CheckCircle, AlertTriangle, MapPin, ThumbsUp, Navigation, Locate } from 'lucide-react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './PublicDashboard.css'
import { toast } from 'react-toastify'

// Custom marker icon to avoid broken transparent images
const createCustomIcon = () => {
    return L.divIcon({
        html: `<div style="
      background-color: #ef4444;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    "></div>`,
        className: 'custom-map-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12]
    })
}

// Componente auxiliar para recentrar mapa
function Recenter({ lat, lng }) {
    const map = useMap()
    useEffect(() => {
        if (lat && lng) {
            map.flyTo([lat, lng], 13)
        }
    }, [lat, lng, map])
    return null
}

function PublicDashboard() {
    const [reportes, setReportes] = useState([])
    const [loading, setLoading] = useState(true)
    const [validating, setValidating] = useState(null)
    const [userLocation, setUserLocation] = useState([-29.9027, -71.2520]) // La Serena default

    // Filtros
    const [categorias, setCategorias] = useState([])
    const [filterCat, setFilterCat] = useState('')
    const [filterDays, setFilterDays] = useState('')

    useEffect(() => {
        loadCategories()
        getUserLocation()
    }, [])

    const loadPublicReports = useCallback(async () => {
        setLoading(true)
        try {
            const params = {}
            if (filterCat) params.categoria = filterCat
            if (filterDays) params.dias = filterDays

            const response = await apiClient.get('/api/reportes/public_map/', { params })
            setReportes(response.data)
        } catch (error) {
            console.error('Error cargando mapa público:', error)
        } finally {
            setLoading(false)
        }
    }, [filterCat, filterDays])

    useEffect(() => {
        loadPublicReports()
    }, [loadPublicReports])

    // WebSocket logic
    useEffect(() => {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/ws/reportes/`

        const socket = new WebSocket(wsUrl)

        socket.onopen = () => {
            console.log('🔗 WebSocket Conectado')
        }

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data)

            if (data.type === 'reporte_creado') {
                toast.info('🆕 ¡Nuevo reporte ciudadano recibido!')
                loadPublicReports() // Refresh map
            } else if (data.type === 'reporte_actualizado') {
                // Info: data.data contains details
                toast.success(`✅ Un reporte ha sido actualizado`)
                loadPublicReports()
            }
        }

        socket.onerror = (error) => {
            console.error('WebSocket error:', error)
        }

        return () => {
            socket.close()
        }
    }, [loadPublicReports])

    const loadCategories = async () => {
        try {
            const response = await apiClient.get(API_ROUTES.CATEGORIAS)
            setCategorias(response.data)
        } catch (error) {
            console.error('Error cargando categorias', error)
        }
    }

    const getUserLocation = () => {
        if (!navigator.geolocation) {
            toast.error("Tu navegador no soporta geolocalización")
            return
        }

        toast.info("Obteniendo ubicación...")
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setUserLocation([pos.coords.latitude, pos.coords.longitude])
                toast.success("¡Ubicación encontrada!")
            },
            (err) => {
                console.log("Ubicación no disponible", err)
                if (err.code === 1) {
                    toast.error("Permiso de ubicación denegado. Por favor permítelo en tu navegador.")
                } else if (err.code === 2) {
                    toast.error("Ubicación no disponible.")
                } else {
                    toast.error("Error al obtener ubicación.")
                }
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        )
    }

    const handleValidate = async (id) => {
        setValidating(id)
        try {
            const response = await apiClient.post(`/api/reportes/${id}/validate_report/`)
            // Actualizar contador localmente
            setReportes(prev => prev.map(r =>
                r.id === id ? { ...r, validaciones_ciudadanas: response.data.new_count } : r
            ))
            alert("¡Gracias! Tu confirmación ayuda a priorizar este reporte. 👍")
        } catch (error) {
            console.error("Error validando:", error)
            alert("Error al validar.")
        } finally {
            setValidating(null)
        }
    }

    return (
        <div className="public-dashboard">
            <div className="pd-header">
                <div className="pd-logo">
                    <MapPin color="#228B22" />
                    <h1>UrbanAlert <span className="highlight">Comunidad</span></h1>
                </div>

                <div className="pd-filters">
                    <select
                        value={filterCat}
                        onChange={(e) => setFilterCat(e.target.value)}
                        className="filter-select"
                    >
                        <option value="">Todas las Categorías</option>
                        {categorias.map(cat => (
                            <option key={cat.id} value={cat.id}>{cat.nombre}</option>
                        ))}
                    </select>

                    <select
                        value={filterDays}
                        onChange={(e) => setFilterDays(e.target.value)}
                        className="filter-select"
                    >
                        <option value="">Cualquier Fecha</option>
                        <option value="1">Últimas 24h</option>
                        <option value="7">Última Semana</option>
                        <option value="30">Último Mes</option>
                    </select>
                </div>

                <div className="pd-stats">
                    <button className="btn-location" onClick={getUserLocation} title="Encontrar mi ubicación">
                        <Locate size={18} />
                    </button>
                    <div className="stat-pill">
                        <AlertTriangle size={16} />
                        <span>{reportes.length} Reportes Activos</span>
                    </div>
                    <a href="/nuevo-reporte" className="btn-reportar">
                        📷 Reportar
                    </a>
                </div>
            </div>

            <div className="pd-map-container">
                <MapContainer
                    center={userLocation}
                    zoom={13}
                    style={{ height: '100%', width: '100%' }}
                >
                    {loading && (
                        <div className="map-loading-overlay">
                            <div className="spinner"></div>
                        </div>
                    )}
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; OpenStreetMap'
                    />
                    <Recenter lat={userLocation[0]} lng={userLocation[1]} />

                    {/* User Location Marker */}
                    <Marker position={userLocation} icon={L.divIcon({
                        html: '<div style="background:#2196f3;width:15px;height:15px;border-radius:50%;border:2px solid white;box-shadow:0 0 10px rgba(33,150,243,0.5)"></div>',
                        className: 'user-loc-icon'
                    })} />

                    {reportes.filter(r => r.lat && r.lng).map(reporte => (
                        <Marker
                            key={reporte.id}
                            position={[reporte.lat, reporte.lng]}
                            icon={createCustomIcon()}
                        >
                            <Popup className="custom-popup">
                                <div className="popup-content">
                                    <div className="popup-header">
                                        <span className="cat-badge">{reporte.categoria_nombre || 'Reporte'}</span>
                                        <span className="date-badge">Has hace poco</span>
                                    </div>

                                    {reporte.foto && (
                                        <div className="popup-img">
                                            <img src={reporte.foto} alt="evidencia" />
                                        </div>
                                    )}

                                    <div className="popup-actions">
                                        <button
                                            className="btn-validate"
                                            onClick={() => handleValidate(reporte.id)}
                                            disabled={validating === reporte.id}
                                        >
                                            <ThumbsUp size={14} />
                                            <span>Lo veo ({reporte.validaciones_ciudadanas || 0})</span>
                                        </button>
                                        <a
                                            href={`https://www.google.com/maps/dir/?api=1&destination=${reporte.lat},${reporte.lng}`}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="btn-nav"
                                        >
                                            <Navigation size={14} />
                                        </a>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>

            <div className="pd-legend">
                <p><ThumbsUp size={12} /> <b>Colaboración:</b> Si ves este problema, confirma para subir su prioridad.</p>
            </div>
        </div>
    )
}

export default PublicDashboard
