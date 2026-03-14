import { useState, useEffect, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useWebSocket } from '../context/WebSocketContext'
import { toast } from './ToastContainer'
import './LiveOperationsCenter.css'

// Custom map updater component to center the map when new critical report arrives
function MapUpdater({ center, zoom }) {
    const map = useMap()
    useEffect(() => {
        if (center) {
            map.flyTo(center, zoom, {
                duration: 1.5,
            })
        }
    }, [center, zoom, map])
    return null
}

const customMarkerIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/9356/9356230.png',
    iconSize: [35, 35],
    iconAnchor: [17, 35],
    popupAnchor: [0, -35]
})

const LiveOperationsCenter = ({ initialReports = [] }) => {
    const { lastMessage } = useWebSocket()
    const [liveReports, setLiveReports] = useState(
        initialReports.filter(r => r.estado !== 'resuelto' && !r.es_spam).slice(0, 50)
    )
    const [focusedLocation, setFocusedLocation] = useState(null)
    const [mapZoom, setMapZoom] = useState(13)
    const [isAlerting, setIsAlerting] = useState(false)

    // Handle incoming websocket messages
    const triggerCriticalAlert = useCallback((reporte) => {
        // Set map focus
        setFocusedLocation([reporte.ubicacion_lat, reporte.ubicacion_lng])
        setMapZoom(16)

        // Trigger visual alert
        setIsAlerting(true)
        setTimeout(() => setIsAlerting(false), 5000) // Flash for 5 seconds

        // Play sound (simulated if browser blocks auto-play)
        try {
            const audio = new Audio('/alert.mp3') // Assume we have a generic alert sound or just rely on toast
            audio.volume = 0.5
            audio.play().catch(e => console.log('Audio autoplay blocked', e))
        } catch (e) {
            console.log('Audio playback error', e)
        }

        toast.warning(`¡ALERTA CRÍTICA! Reporte #${reporte.codigo_seguimiento}`)
    }, [])

    // Handle incoming websocket messages
    useEffect(() => {
        if (lastMessage) {
            if (lastMessage.type === 'nuevo_reporte' || lastMessage.type === 'reporte_actualizado') {
                const reporte = lastMessage.data

                // Skip spam or resolved
                if (reporte.es_spam || reporte.estado === 'resuelto') return

                const isCritical =
                    reporte.prioridad === 'alta' ||
                    reporte.prioridad === 'urgente' ||
                    reporte.prediction?.risk_level === 'alto'

                setLiveReports(prev => {
                    // If update, replace it
                    const filtered = prev.filter(r => r.id !== reporte.id)
                    return [reporte, ...filtered].slice(0, 50) // keep latest 50
                })

                if (isCritical && reporte.ubicacion_lat && reporte.ubicacion_lng) {
                    triggerCriticalAlert(reporte)
                }
            }
        }
    }, [lastMessage, triggerCriticalAlert])

    const handleFocusReport = (reporte) => {
        if (reporte.ubicacion_lat && reporte.ubicacion_lng) {
            setFocusedLocation([reporte.ubicacion_lat, reporte.ubicacion_lng])
            setMapZoom(16)
        } else {
            toast.info('Este reporte no tiene ubicación exacta.')
        }
    }

    // Default center to La Serena
    const defaultCenter = [-29.9027, -71.2520]

    return (
        <div className={`live-ops-container ${isAlerting ? 'alerting' : ''}`}>
            <div className="live-ops-header">
                <h2>Centro de Operaciones en Tiempo Real</h2>
                <div className="live-status">
                    <span className="live-indicator"></span>
                    Conexión Activa
                </div>
            </div>

            <div className="live-ops-content">
                <div className="live-ops-sidebar">
                    <h3>Feed de Incidentes Activos</h3>
                    <div className="feed-list">
                        {liveReports.length === 0 ? (
                            <p className="empty-feed">Esperando nuevos reportes...</p>
                        ) : (
                            liveReports.map(reporte => {
                                const isCritical =
                                    reporte.prioridad === 'alta' ||
                                    reporte.prioridad === 'urgente' ||
                                    reporte.prediction?.risk_level === 'alto'

                                return (
                                    <div
                                        key={reporte.id}
                                        className={`feed-item ${isCritical ? 'critical' : ''}`}
                                        onClick={() => handleFocusReport(reporte)}
                                    >
                                        <div className="feed-item-header">
                                            <span className="feed-code">#{reporte.codigo_seguimiento || reporte.id}</span>
                                            <span className={`feed-priority priority-${reporte.prioridad || 'normal'}`}>
                                                {reporte.prioridad?.toUpperCase() || 'NORMAL'}
                                            </span>
                                        </div>
                                        <p className="feed-title">{reporte.categoria_nombre || 'Reporte de Basura'}</p>
                                        <p className="feed-address">{reporte.direccion || 'Ubicación Desconocida'}</p>
                                        <span className="feed-time">
                                            {new Date(reporte.fecha_creacion).toLocaleTimeString()}
                                        </span>
                                    </div>
                                )
                            })
                        )}
                    </div>
                </div>

                <div className="live-ops-map">
                    <MapContainer
                        center={defaultCenter}
                        zoom={12}
                        style={{ height: '100%', width: '100%', borderRadius: '8px' }}
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://carto.com/">Carto</a>'
                            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                        />
                        <MapUpdater center={focusedLocation} zoom={mapZoom} />

                        {liveReports.map(reporte => {
                            if (!reporte.ubicacion_lat || !reporte.ubicacion_lng) return null;

                            const isCritical =
                                reporte.prioridad === 'alta' ||
                                reporte.prioridad === 'urgente' ||
                                reporte.prediction?.risk_level === 'alto'

                            return (
                                <Marker
                                    key={reporte.id}
                                    position={[reporte.ubicacion_lat, reporte.ubicacion_lng]}
                                    icon={customMarkerIcon}
                                >
                                    <Popup>
                                        <div className="live-popup">
                                            <h4>#{reporte.codigo_seguimiento}</h4>
                                            <p><strong>Estado:</strong> {reporte.estado}</p>
                                            {isCritical && <strong className="critical-text">¡CRÍTICO!</strong>}
                                            <p>{reporte.categoria_nombre}</p>
                                        </div>
                                    </Popup>
                                </Marker>
                            )
                        })}
                    </MapContainer>
                </div>
            </div>
        </div>
    )
}

export default LiveOperationsCenter
