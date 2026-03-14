import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts'
import 'leaflet/dist/leaflet.css'
import './DashboardMunicipal.css'
import { API_ROUTES } from '../config'
import { API_URL } from '../config'
import apiClient from '../services/api'
import { fetchCategorias as fetchCategoriasService } from '../services/predictions'
import { toast } from './ToastContainer'
import OfflineService from '../services/OfflineService'
import Skeleton from './Skeleton'
import AnimatedNumber from './AnimatedNumber'
import DarkModeToggle from './DarkModeToggle'
import AdvancedSearch from './AdvancedSearch'
import HistoryTimeline from './HistoryTimeline'
import PriorityTagsManager from './PriorityTagsManager'
import AdvancedStatistics from './AdvancedStatistics'
import RouteOptimizer from './RouteOptimizer'
import StatCardEnterprise from './StatCardEnterprise'
import NotificationsPanel from './NotificationsPanel'
import SavedSearches from './SavedSearches'
import LocationUpdater from './LocationUpdater'
import EmployeeManager from './EmployeeManager'
import ValidationPanel from './ValidationPanel'
import { useWebSocket } from '../context/WebSocketContext'
import SLADashboard from './SLADashboard'
import MapView3D from './MapView3D'
import LiveOperationsCenter from './LiveOperationsCenter'
import DashboardTour from './DashboardTour'
import EcoInteligenciaTab from './EcoInteligenciaTab'

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
    clickHandlerRef.current = function (e) {
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
        L.popup()
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

// Iconos SVG simples para el diseño enterprise
const LayoutDashboardIcon = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="3" width="7" height="7" rx="1" />
    <rect x="3" y="14" width="7" height="7" rx="1" />
    <rect x="14" y="14" width="7" height="7" rx="1" />
  </svg>
)

const MapIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4z" />
    <path d="M8 2v16M16 6v16" />
  </svg>
)

const AlertTriangleIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
)

const FileTextIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
  </svg>
)

const UsersIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
)

const ActivityIconSVG = ({ size = 20 }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
  </svg>
)

const CalendarIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </svg>
)

const SettingsIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="3" />
    <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24" />
  </svg>
)

const LogOutIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </svg>
)

const SearchIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8" />
    <path d="m21 21-4.35-4.35" />
  </svg>
)

const BellIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
)

const MenuIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="6" x2="21" y2="6" />
    <line x1="3" y1="18" x2="21" y2="18" />
  </svg>
)

const ChevronRightIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="9 18 15 12 9 6" />
  </svg>
)

const ChevronDownIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 12 15 18 9" />
  </svg>
)

const PlusIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
)

const FilterIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </svg>
)

const DownloadIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
)

const MoreVerticalIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="1" />
    <circle cx="12" cy="5" r="1" />
    <circle cx="12" cy="19" r="1" />
  </svg>
)

const LeafIconSVG = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.77 10-10 10Z" />
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
  </svg>
)

const BrainIconSVG = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04z" />
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04z" />
  </svg>
)


function DashboardMunicipal() {
  const navigate = useNavigate()
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [vistaActual, setVistaActual] = useState('dashboard')
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
  const [userInfo, setUserInfo] = useState(null)
  const [filtroEstado, setFiltroEstado] = useState('')
  // States para mapas
  const [heatmapEnabled, setHeatmapEnabled] = useState(false)

  const [heatmapData, setHeatmapData] = useState([])
  const [loadingHeatmap, setLoadingHeatmap] = useState(false)
  const [mapView3D, setMapView3D] = useState(false)
  const [categorias, setCategorias] = useState([])
  const [tags, setTags] = useState([])
  const [inspectores, setInspectores] = useState([])
  const [searchParams, setSearchParams] = useState({})

  // Nuevos estados para mejoras del dashboard
  const [filtroRapidoEstado, setFiltroRapidoEstado] = useState('')
  const [filtroRapidoPrioridad, setFiltroRapidoPrioridad] = useState('')
  const [filtroRapidoCategoria, setFiltroRapidoCategoria] = useState('')
  const [periodoSeleccionado, setPeriodoSeleccionado] = useState('30d')
  const [estadisticasAnteriores, setEstadisticasAnteriores] = useState(null)
  const [actividadHoy, setActividadHoy] = useState({ nuevos: 0, resueltos: 0, en_proceso: 0 })
  const [zonasRiesgo, setZonasRiesgo] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const searchInputRef = useRef(null)
  const selectAllReportesRef = useRef(null)

  // Estados para nuevas mejoras
  const [busquedasGuardadas, setBusquedasGuardadas] = useState([])
  const [mostrarFiltrosAvanzados, setMostrarFiltrosAvanzados] = useState(false)
  const [filtrosAvanzados, setFiltrosAvanzados] = useState({
    fechaDesde: '',
    fechaHasta: '',
    inspector: '',
    prioridadMinima: '',
    tieneFoto: '',
    validado: ''
  })
  const [ordenamientoTabla, setOrdenamientoTabla] = useState({ campo: null, direccion: 'asc' })
  const [vistaCalendario, setVistaCalendario] = useState(false)
  const [mesCalendario, setMesCalendario] = useState(new Date())
  const [notificaciones, setNotificaciones] = useState([])
  const [mostrarNotificaciones, setMostrarNotificaciones] = useState(false)
  const [widgetsVisibles] = useState({
    categorias: true,
    alertas: true,
    actividad: true,
    zonas: true,
    comparacion: true,
    tendencia: true,
    inspectores: true
  })
  const [vistaTendencia, setVistaTendencia] = useState('area') // 'area', 'line', 'bar'
  const [estadisticasInspectores, setEstadisticasInspectores] = useState({})
  const [loadingInspectores, setLoadingInspectores] = useState(false)
  const [showLocationUpdater, setShowLocationUpdater] = useState(false)
  const [showValidationPanel, setShowValidationPanel] = useState(false)
  const [offlinePendingCount, setOfflinePendingCount] = useState(0)
  const [executiveStats, setExecutiveStats] = useState(null)
  const [loadingExecutiveStats, setLoadingExecutiveStats] = useState(false)
  const [modalEstado, setModalEstado] = useState('nuevo')
  const [modalNotas, setModalNotas] = useState('')
  const [modalEvidenciaCierre, setModalEvidenciaCierre] = useState('')
  const [modalFotoCierre, setModalFotoCierre] = useState(null)
  const [selectedReporteIds, setSelectedReporteIds] = useState([])
  const [bulkInspectorId, setBulkInspectorId] = useState('')
  const [bulkEstado, setBulkEstado] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [totalReportes, setTotalReportes] = useState(0)

  // Estado para el Tour (Onboarding)
  const [runTour, setRunTour] = useState(false)

  const { lastMessage } = useWebSocket()

  // Efecto para procesar mensajes en tiempo real
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'reporte_creado') {
      const nuevoReporte = lastMessage.data

      // Actualizar lista de reportes
      setReportes(prev => [nuevoReporte, ...prev])

      // Actualizar estadísticas simples
      setEstadisticas(prev => ({
        ...prev,
        total: (prev.total || 0) + 1,
        nuevos: (prev.nuevos || 0) + 1
      }))

      // Actualizar actividad de hoy
      setActividadHoy(prev => ({
        ...prev,
        nuevos: (prev.nuevos || 0) + 1
      }))

      // Si el heatmap está activo, recargarlo
      if (heatmapEnabled) {
        fetchHeatmapData()
      }

    } else if (lastMessage && lastMessage.type === 'reporte_actualizado') {
      const reporteActualizado = lastMessage.data

      setReportes(prev => prev.map(r =>
        r.id === reporteActualizado.id ? reporteActualizado : r
      ))

      // Actualizar estadísticas si es necesario (simplificado: recargar si es crítico)
      if (reporteActualizado.prioridad === 'alta' || reporteActualizado.estado === 'resuelto') {
        fetchEstadisticas()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastMessage, heatmapEnabled])

  const predictedReportes = useMemo(
    () => reportes.filter((reporte) => Boolean(reporte.prediction)),
    [reportes]
  )
  const highRiskReportes = useMemo(() => {
    return predictedReportes
      .filter((reporte) => reporte.prediction?.risk_level === 'alto')
      .sort((a, b) => (b.prediction?.probability || 0) - (a.prediction?.probability || 0))
      .slice(0, 5)
  }, [predictedReportes])
  const predictionSummary = useMemo(() => {
    const summary = { alto: 0, medio: 0, bajo: 0 }
    predictedReportes.forEach((reporte) => {
      if (reporte.prediction?.risk_level && summary[reporte.prediction.risk_level] !== undefined) {
        summary[reporte.prediction.risk_level] += 1
      }
    })
    return summary
  }, [predictedReportes])
  const predictionsAvailable = predictedReportes.length > 0

  // Desencadenar el Tour si el usuario es nuevo y nunca lo ha hecho
  useEffect(() => {
    if (userInfo && userInfo.tour_completado === false) {
      // Pequeño delay para que la interfaz cargue primero
      const timer = setTimeout(() => {
        setRunTour(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [userInfo]);

  // Función para cerrar sesión
  const handleLogout = (e) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }

    try {
      console.log('Iniciando cierre de sesión...')

      // Limpiar tokens y datos del usuario
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')

      console.log('Tokens eliminados del localStorage')

      // Mostrar mensaje de éxito
      toast.success('Sesión cerrada exitosamente')

      // Redirigir al login - usar window.location como fallback si navigate no funciona
      try {
        navigate('/login', { replace: true })
        console.log('Navegación con navigate ejecutada')
      } catch (navError) {
        console.error('Error con navigate, usando window.location:', navError)
        window.location.href = '/login'
      }
    } catch (error) {
      console.error('Error al cerrar sesión:', error)
      toast.error('Error al cerrar sesión')
      // Fallback: redirigir directamente
      window.location.href = '/login'
    }
  }

  // Cargar información del usuario
  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (userData) {
      try {
        setUserInfo(JSON.parse(userData))
      } catch (e) {
        console.error('Error al parsear datos del usuario:', e)
      }
    }
  }, [])

  // Cargar reportes y estadísticas
  useEffect(() => {
    fetchReportes()
    fetchEstadisticas()
    fetchExecutiveStats()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtroEstado, currentPage])

  // Efecto separado para cuando cambian los parámetros de búsqueda
  useEffect(() => {
    if (searchParams && Object.keys(searchParams).length > 0) {
      setCurrentPage(1)
      fetchReportes()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  useEffect(() => {
    const loadCategorias = async () => {
      try {
        const data = await fetchCategoriasService()
        setCategorias(Array.isArray(data) ? data : [])
      } catch (error) {
        console.error('Error al cargar categorías:', error)
      }
    }
    loadCategorias()
  }, [])

  useEffect(() => {
    const loadTags = async () => {
      try {
        const response = await apiClient.get(API_ROUTES.TAGS)
        setTags(response.data || [])
      } catch (error) {
        console.error('Error al cargar tags:', error)
      }
    }
    loadTags()
  }, [])

  useEffect(() => {
    const loadInspectores = async () => {
      try {
        // Intentar obtener usuarios/inspectores desde una API específica
        try {
          const response = await apiClient.get('/api/admin/usuarios/')
          const data = response.data
          const usuariosList = Array.isArray(data) ? data : data.results || []
          setInspectores(usuariosList.map(u => ({
            id: u.id,
            username: u.username,
            email: u.email || '',
            first_name: u.first_name || '',
            last_name: u.last_name || '',
            is_staff: u.is_staff || false
          })))
        } catch {
          // Si no existe la API de usuarios, obtener desde reportes asignados
          console.log('API de usuarios no disponible, obteniendo desde reportes...')
          const response = await apiClient.get(API_ROUTES.REPORTES)
          const data = response.data
          const reportesList = Array.isArray(data) ? data : data.results || []
          const inspectoresMap = new Map()

          reportesList.forEach(r => {
            if (r.asignado_a) {
              const inspectorId = typeof r.asignado_a === 'object' ? r.asignado_a.id : r.asignado_a
              const inspectorUsername = typeof r.asignado_a === 'object' ? r.asignado_a.username : r.asignado_a

              if (!inspectoresMap.has(inspectorId)) {
                inspectoresMap.set(inspectorId, {
                  id: inspectorId,
                  username: inspectorUsername,
                  email: '',
                  first_name: '',
                  last_name: '',
                  is_staff: false
                })
              }
            }
          })

          // También agregar el usuario actual si existe
          if (userInfo) {
            const userId = userInfo.id || userInfo.username
            inspectoresMap.set(userId, {
              id: userId,
              username: userInfo.username,
              email: userInfo.email || '',
              first_name: userInfo.first_name || '',
              last_name: userInfo.last_name || '',
              is_staff: userInfo.is_staff || false
            })
          }

          const inspectoresList = Array.from(inspectoresMap.values())

          // Si no hay inspectores, agregar al menos el usuario actual
          if (inspectoresList.length === 0 && userInfo) {
            inspectoresList.push({
              id: userInfo.id || userInfo.username,
              username: userInfo.username,
              email: userInfo.email || '',
              first_name: userInfo.first_name || '',
              last_name: userInfo.last_name || '',
              is_staff: userInfo.is_staff || false
            })
          }

          setInspectores(inspectoresList)
        }
      } catch (error) {
        console.error('Error al cargar inspectores:', error)
        // Fallback: usar solo el usuario actual
        if (userInfo) {
          setInspectores([{
            id: userInfo.id || userInfo.username,
            username: userInfo.username,
            email: userInfo.email || '',
            first_name: userInfo.first_name || '',
            last_name: userInfo.last_name || '',
            is_staff: userInfo.is_staff || false
          }])
        }
      }
    }
    loadInspectores()
  }, [userInfo])

  useEffect(() => {
    const handlePendingChange = (event) => {
      setOfflinePendingCount(event.detail?.pendingCount || 0)
    }

    const loadPendingCount = async () => {
      const count = await OfflineService.getPendingCount()
      setOfflinePendingCount(count)
    }

    loadPendingCount()
    window.addEventListener('offlinePendingChanged', handlePendingChange)

    return () => {
      window.removeEventListener('offlinePendingChanged', handlePendingChange)
    }
  }, [])

  // Cargar datos del heatmap cuando se activa
  useEffect(() => {
    if (heatmapEnabled && vistaActual === 'mapa') {
      console.log('Heatmap enabled, fetching data...')
      fetchHeatmapData()
    } else if (!heatmapEnabled) {
      // Limpiar datos cuando se desactiva
      setHeatmapData([])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const handleExportGerencial = async () => {
    try {
      toast.info('Iniciando generación de reporte gerencial asíncrono...')
      await apiClient.post('/api/analytics/gerencial/')
      toast.success('¡Generación iniciada! Se enviará por correo a los administradores.')
    } catch (error) {
      console.error('Error al generar reporte gerencial:', error)
      toast.error('Error al iniciar la generación del reporte')
    }
  }

  const fetchHeatmapData = async () => {
    setLoadingHeatmap(true)
    try {
      const params = {}
      if (filtroEstado) {
        params.estado = filtroEstado
      }

      const response = await apiClient.get(API_ROUTES.HEATMAP, { params })
      const data = response.data

      if (data.data && Array.isArray(data.data)) {
        if (data.data.length > 0) {
          setHeatmapData(data.data)
        } else {
          setHeatmapData([])
        }
      } else if (Array.isArray(data)) {
        if (data.length > 0) {
          setHeatmapData(data)
        } else {
          setHeatmapData([])
        }
      } else {
        setHeatmapData([])
      }
    } catch (error) {
      console.error('Error al cargar datos del heatmap:', error)
      setHeatmapData([])
      toast.error('Error al cargar el mapa de calor. Por favor, intente nuevamente.')
    } finally {
      setLoadingHeatmap(false)
    }
  }

  const fetchReportes = async () => {
    setLoading(true)
    try {
      const params = searchParams ? { ...searchParams } : {}
      if (filtroEstado) {
        params.estado = filtroEstado
      }
      params.page = currentPage
      const response = await apiClient.get(API_ROUTES.REPORTES, { params })
      const data = response.data
      if (Array.isArray(data)) {
        setReportes(data)
        setTotalReportes(data.length)
        setPageSize(data.length || 20)
      } else {
        const results = data.results || []
        setReportes(results)
        setTotalReportes(typeof data.count === 'number' ? data.count : results.length)
        setPageSize(results.length || 20)
      }
    } catch (error) {
      console.error('Error al cargar reportes:', error)
      toast.error('Error al cargar los reportes')
    } finally {
      setLoading(false)
    }
  }

  // Funciones de exportación
  const handleExportCSV = async () => {
    try {
      const params = searchParams ? { ...searchParams } : {}
      if (filtroEstado) {
        params.estado = filtroEstado
      }
      const response = await apiClient.get(`${API_ROUTES.REPORTES}exportar/`, {
        params,
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'reportes.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      toast.success('CSV descargado exitosamente')
    } catch (error) {
      console.error('Error al exportar CSV:', error)
      toast.error('Error al exportar CSV')
    }
  }

  const handleExportPDF = async () => {
    try {
      const params = {}
      const response = await apiClient.get(API_ROUTES.EXPORTAR_PDF, {
        params,
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'reporte_estadistico.pdf')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      toast.success('PDF descargado exitosamente')
    } catch (error) {
      console.error('Error al exportar PDF:', error)
      toast.error('Error al exportar PDF')
    }
  }

  const handleExportExcel = async () => {
    try {
      const params = {}
      const response = await apiClient.get(API_ROUTES.EXPORTAR_EXCEL, {
        params,
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'reporte_estadistico.xlsx')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      toast.success('Excel descargado exitosamente')
    } catch (error) {
      console.error('Error al exportar Excel:', error)
      toast.error('Error al exportar Excel')
    }
  }

  const handleSearch = (params) => {
    setCurrentPage(1)
    setSearchParams(params)
  }

  const handleResetSearch = () => {
    setCurrentPage(1)
    setSearchParams({})
  }

  const fetchEstadisticas = async () => {
    try {
      const response = await apiClient.get(API_ROUTES.ESTADISTICAS)
      setEstadisticas(response.data)
    } catch (error) {
      console.error('Error al cargar estadísticas:', error)
      toast.error('Error al cargar las estadísticas')
    }
  }

  const fetchExecutiveStats = async () => {
    setLoadingExecutiveStats(true)
    try {
      const response = await apiClient.get(API_ROUTES.ANALYTICS_EJECUTIVO)
      setExecutiveStats(response.data)
    } catch (error) {
      console.error('Error al cargar KPIs ejecutivos:', error)
      setExecutiveStats(null)
    } finally {
      setLoadingExecutiveStats(false)
    }
  }

  const handleVerDetalle = async (reporte) => {
    let reporteDetalle = reporte
    // Siempre obtener el detalle completo del reporte para asegurar que tenemos todos los datos
    if (reporte.id) {
      try {
        const response = await apiClient.get(`${API_ROUTES.REPORTES}${reporte.id}/`)
        reporteDetalle = response.data
        setReporteSeleccionado(reporteDetalle)
      } catch (error) {
        console.error('Error al obtener detalle del reporte:', error)
        // Si falla, usar el reporte de la lista
        reporteDetalle = reporte
        setReporteSeleccionado(reporteDetalle)
        toast.error('Error al cargar el detalle del reporte')
      }
    } else {
      reporteDetalle = reporte
      setReporteSeleccionado(reporteDetalle)
    }

    const estadoInicial = reporteDetalle.estado || 'nuevo'
    setModalEstado(estadoInicial)
    setModalNotas(reporteDetalle.notas_internas || '')
    setModalEvidenciaCierre(reporteDetalle.cierre?.evidencia_texto || '')
    setModalFotoCierre(null)

    setShowModal(true)
  }

  const handleGuardarCambios = async () => {
    if (!reporteSeleccionado) return

    const nuevoEstado = modalEstado
    const notasInternas = modalNotas
    const evidenciaCierre = modalEvidenciaCierre.trim()
    const requiereEvidencia = nuevoEstado === 'resuelto' || nuevoEstado === 'cerrado'
    if (requiereEvidencia && !evidenciaCierre && !modalFotoCierre && !reporteSeleccionado?.cierre?.foto_cierre) {
      toast.error('Debes adjuntar evidencia de cierre (texto o foto).')
      return
    }

    try {
      if (modalFotoCierre) {
        const formData = new FormData()
        formData.append('estado', nuevoEstado)
        formData.append('notas_internas', notasInternas)
        if (evidenciaCierre) {
          formData.append('evidencia_cierre', evidenciaCierre)
        }
        formData.append('foto_cierre', modalFotoCierre)
        await apiClient.patch(
          `${API_ROUTES.REPORTES}${reporteSeleccionado.id}/actualizar_estado/`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        )
      } else {
        await apiClient.patch(`${API_ROUTES.REPORTES}${reporteSeleccionado.id}/actualizar_estado/`, {
          estado: nuevoEstado,
          notas_internas: notasInternas,
          evidencia_cierre: evidenciaCierre
        })
      }

      fetchReportes()
      fetchEstadisticas()
      setShowModal(false)
      toast.success('Cambios guardados exitosamente')
    } catch (error) {
      if (!navigator.onLine) {
        if (modalFotoCierre) {
          toast.error('No se puede encolar una foto de cierre estando offline.')
          return
        }
        await OfflineService.queueInspectorAction({
          method: 'patch',
          url: `${API_ROUTES.REPORTES}${reporteSeleccionado.id}/actualizar_estado/`,
          payload: {
            estado: nuevoEstado,
            notas_internas: notasInternas,
            evidencia_cierre: evidenciaCierre
          },
          type: 'actualizar_estado_reporte',
          reporteId: reporteSeleccionado.id
        })
        setReportes((prev) => prev.map((reporte) => (
          reporte.id === reporteSeleccionado.id
            ? { ...reporte, estado: nuevoEstado, notas_internas: notasInternas, cierre: { evidencia_texto: evidenciaCierre } }
            : reporte
        )))
        setShowModal(false)
        toast.info('Sin conexión. Cambio guardado en cola para sincronizar.')
        return
      }
      console.error('Error al actualizar:', error)
      toast.error('Error al guardar cambios')
    }
  }

  const handleBulkUpdate = async (payload) => {
    if (selectedReporteIds.length === 0) {
      toast.warning('Selecciona al menos un reporte.')
      return
    }

    try {
      const response = await apiClient.post(API_ROUTES.REPORTES_BULK_UPDATE, {
        report_ids: selectedReporteIds,
        ...payload
      })
      toast.success(`${response.data.updated || 0} reportes actualizados`)
      setSelectedReporteIds([])
      setBulkEstado('')
      setBulkInspectorId('')
      fetchReportes()
      fetchEstadisticas()
    } catch (error) {
      console.error('Error en actualización masiva:', error)
      toast.error('No se pudo aplicar la actualización masiva')
    }
  }

  // Datos para sparklines
  const sparkData1 = [{ value: 10 }, { value: 15 }, { value: 12 }, { value: 20 }, { value: 18 }, { value: 25 }, { value: 22 }]
  const sparkData2 = [{ value: 20 }, { value: 22 }, { value: 25 }, { value: 24 }, { value: 28 }, { value: 30 }, { value: 35 }]
  const sparkData3 = [{ value: 30 }, { value: 28 }, { value: 25 }, { value: 22 }, { value: 20 }, { value: 18 }, { value: 15 }]
  const sparkData4 = [{ value: 12 }, { value: 14 }, { value: 13 }, { value: 15 }, { value: 14 }, { value: 14 }, { value: 14 }]

  // Datos para gráfico de área
  const dataDenuncias = [
    { name: '1 Oct', denuncias: estadisticas.nuevos || 12, resueltos: estadisticas.resueltos || 8 },
    { name: '5 Oct', denuncias: (estadisticas.nuevos || 12) + 7, resueltos: (estadisticas.resueltos || 8) + 7 },
    { name: '10 Oct', denuncias: (estadisticas.nuevos || 12) + 3, resueltos: (estadisticas.resueltos || 8) + 4 },
    { name: '15 Oct', denuncias: (estadisticas.nuevos || 12) + 13, resueltos: (estadisticas.resueltos || 8) + 12 },
    { name: '20 Oct', denuncias: (estadisticas.nuevos || 12) + 20, resueltos: (estadisticas.resueltos || 8) + 20 },
    { name: '25 Oct', denuncias: (estadisticas.nuevos || 12) + 16, resueltos: (estadisticas.resueltos || 8) + 17 },
    { name: '30 Oct', denuncias: (estadisticas.nuevos || 12) + 23, resueltos: (estadisticas.resueltos || 8) + 22 },
  ]

  // Funciones para mejoras del dashboard

  // Calcular datos de categorías para gráfico de pastel
  const datosCategorias = useMemo(() => {
    const categoriasMap = {}
    reportes.forEach(reporte => {
      const catNombre = reporte.categoria_nombre || 'Sin categoría'
      categoriasMap[catNombre] = (categoriasMap[catNombre] || 0) + 1
    })
    return Object.entries(categoriasMap).map(([name, value]) => ({ name, value }))
  }, [reportes])

  // Colores para gráfico de pastel
  const COLORS_PIE = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658']

  // Calcular actividad del día
  useEffect(() => {
    const hoy = new Date()
    hoy.setHours(0, 0, 0, 0)
    const actividad = {
      nuevos: 0,
      resueltos: 0,
      en_proceso: 0
    }
    reportes.forEach(reporte => {
      const fechaReporte = new Date(reporte.fecha_creacion)
      fechaReporte.setHours(0, 0, 0, 0)
      if (fechaReporte.getTime() === hoy.getTime()) {
        if (reporte.estado === 'nuevo') actividad.nuevos++
        else if (reporte.estado === 'resuelto') actividad.resueltos++
        else if (reporte.estado === 'proceso') actividad.en_proceso++
      }
    })
    setActividadHoy(actividad)
  }, [reportes])

  // Calcular zonas de riesgo (Top 5 por cantidad de reportes)
  useEffect(() => {
    const zonasMap = {}
    reportes.forEach(reporte => {
      const direccion = reporte.direccion || reporte.direccion_completa || 'Sin dirección'
      // Extraer zona/barrio aproximado (primeras palabras de la dirección)
      const zona = direccion.split(',').slice(0, 2).join(',').trim() || 'Sin ubicación'
      zonasMap[zona] = (zonasMap[zona] || 0) + 1
    })
    const zonasArray = Object.entries(zonasMap)
      .map(([zona, cantidad]) => ({ zona, cantidad }))
      .sort((a, b) => b.cantidad - a.cantidad)
      .slice(0, 5)
    setZonasRiesgo(zonasArray)
  }, [reportes])

  // Calcular tiempo promedio de resolución
  const tiempoPromedioResolucion = useMemo(() => {
    const resueltos = reportes.filter(r => r.estado === 'resuelto' && r.fecha_creacion)
    if (resueltos.length === 0) return 0

    // Usar tiempo_resolucion_horas si está disponible, sino calcular desde fecha_creacion hasta fecha_actualizacion
    const tiempos = resueltos.map(r => {
      if (r.tiempo_resolucion_horas) {
        return r.tiempo_resolucion_horas / 24 // convertir horas a días
      } else if (r.fecha_actualizacion) {
        const inicio = new Date(r.fecha_creacion)
        const fin = new Date(r.fecha_actualizacion)
        return (fin - inicio) / (1000 * 60 * 60 * 24) // días
      }
      return 0
    }).filter(t => t > 0)

    if (tiempos.length === 0) return 0
    const promedio = tiempos.reduce((a, b) => a + b, 0) / tiempos.length
    return promedio
  }, [reportes])

  // Calcular comparativa de períodos
  useEffect(() => {
    const calcularComparativa = () => {
      const hoy = new Date()
      let fechaInicioActual, fechaInicioAnterior, fechaFinAnterior

      switch (periodoSeleccionado) {
        case 'hoy':
          fechaInicioActual = new Date(hoy.setHours(0, 0, 0, 0))
          fechaInicioAnterior = new Date(hoy)
          fechaInicioAnterior.setDate(fechaInicioAnterior.getDate() - 1)
          fechaFinAnterior = new Date(fechaInicioAnterior)
          fechaFinAnterior.setHours(23, 59, 59, 999)
          break
        case '7d':
          fechaInicioActual = new Date()
          fechaInicioActual.setDate(fechaInicioActual.getDate() - 7)
          fechaFinAnterior = new Date(fechaInicioActual)
          fechaInicioAnterior = new Date(fechaFinAnterior)
          fechaInicioAnterior.setDate(fechaInicioAnterior.getDate() - 7)
          break
        case '30d':
          fechaInicioActual = new Date()
          fechaInicioActual.setDate(fechaInicioActual.getDate() - 30)
          fechaFinAnterior = new Date(fechaInicioActual)
          fechaInicioAnterior = new Date(fechaFinAnterior)
          fechaInicioAnterior.setDate(fechaInicioAnterior.getDate() - 30)
          break
        default:
          return
      }

      const anteriores = reportes.filter(r => {
        const fecha = new Date(r.fecha_creacion)
        return fecha >= fechaInicioAnterior && fecha <= fechaFinAnterior
      })

      setEstadisticasAnteriores({
        total: anteriores.length,
        nuevos: anteriores.filter(r => r.estado === 'nuevo').length,
        resueltos: anteriores.filter(r => r.estado === 'resuelto').length,
        en_proceso: anteriores.filter(r => r.estado === 'proceso').length
      })
    }

    calcularComparativa()
  }, [periodoSeleccionado, reportes])

  // Reportes críticos (alta prioridad)
  const reportesCriticos = useMemo(() => {
    return reportes
      .filter(r => r.prediction?.risk_level === 'alto' || r.prioridad === 'alta')
      .sort((a, b) => {
        const probA = a.prediction?.probability || 0
        const probB = b.prediction?.probability || 0
        return probB - probA
      })
      .slice(0, 5)
  }, [reportes])

  // Manejar filtros rápidos
  const handleFiltroRapido = (tipo, valor) => {
    if (tipo === 'estado') {
      setCurrentPage(1)
      setFiltroRapidoEstado(valor === filtroRapidoEstado ? '' : valor)
      setFiltroEstado(valor === filtroRapidoEstado ? '' : valor)
    } else if (tipo === 'prioridad') {
      setFiltroRapidoPrioridad(valor === filtroRapidoPrioridad ? '' : valor)
    } else if (tipo === 'categoria') {
      setFiltroRapidoCategoria(valor === filtroRapidoCategoria ? '' : valor)
    }
  }

  // Aplicar filtros combinados (incluyendo avanzados)
  const reportesFiltrados = useMemo(() => {
    let filtrados = [...reportes]

    if (filtroRapidoEstado) {
      filtrados = filtrados.filter(r => r.estado === filtroRapidoEstado)
    }

    if (filtroRapidoPrioridad) {
      filtrados = filtrados.filter(r => {
        const riskLevel = r.prediction?.risk_level || 'medio'
        return (filtroRapidoPrioridad === 'alto' && riskLevel === 'alto') ||
          (filtroRapidoPrioridad === 'medio' && riskLevel === 'medio') ||
          (filtroRapidoPrioridad === 'bajo' && riskLevel === 'bajo')
      })
    }

    if (filtroRapidoCategoria) {
      filtrados = filtrados.filter(r => r.categoria_nombre === filtroRapidoCategoria)
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtrados = filtrados.filter(r =>
        (r.codigo_seguimiento && r.codigo_seguimiento.toLowerCase().includes(query)) ||
        (r.direccion && r.direccion.toLowerCase().includes(query)) ||
        (r.direccion_completa && r.direccion_completa.toLowerCase().includes(query)) ||
        (r.categoria_nombre && r.categoria_nombre.toLowerCase().includes(query))
      )
    }

    // Filtros avanzados
    if (filtrosAvanzados.fechaDesde) {
      const fechaDesde = new Date(filtrosAvanzados.fechaDesde)
      filtrados = filtrados.filter(r => new Date(r.fecha_creacion) >= fechaDesde)
    }

    if (filtrosAvanzados.fechaHasta) {
      const fechaHasta = new Date(filtrosAvanzados.fechaHasta)
      fechaHasta.setHours(23, 59, 59, 999)
      filtrados = filtrados.filter(r => new Date(r.fecha_creacion) <= fechaHasta)
    }

    if (filtrosAvanzados.inspector) {
      filtrados = filtrados.filter(r => r.asignado_a === filtrosAvanzados.inspector)
    }

    if (filtrosAvanzados.tieneFoto === 'si') {
      filtrados = filtrados.filter(r => r.foto)
    } else if (filtrosAvanzados.tieneFoto === 'no') {
      filtrados = filtrados.filter(r => !r.foto)
    }

    if (filtrosAvanzados.validado === 'si') {
      filtrados = filtrados.filter(r => r.validado)
    } else if (filtrosAvanzados.validado === 'no') {
      filtrados = filtrados.filter(r => !r.validado)
    }

    // Ordenamiento
    if (ordenamientoTabla.campo) {
      filtrados.sort((a, b) => {
        let aVal = a[ordenamientoTabla.campo]
        let bVal = b[ordenamientoTabla.campo]

        if (ordenamientoTabla.campo === 'fecha_creacion') {
          aVal = new Date(aVal)
          bVal = new Date(bVal)
        }

        if (typeof aVal === 'string') {
          aVal = aVal.toLowerCase()
          bVal = bVal.toLowerCase()
        }

        if (ordenamientoTabla.direccion === 'asc') {
          return aVal > bVal ? 1 : -1
        } else {
          return aVal < bVal ? 1 : -1
        }
      })
    }

    return filtrados
  }, [reportes, filtroRapidoEstado, filtroRapidoPrioridad, filtroRapidoCategoria, searchQuery, filtrosAvanzados, ordenamientoTabla])

  const totalPaginas = Math.max(1, Math.ceil((totalReportes || 0) / Math.max(pageSize || 1, 1)))
  const fromRegistro = totalReportes === 0 ? 0 : ((currentPage - 1) * pageSize) + 1
  const toRegistro = totalReportes === 0 ? 0 : Math.min(((currentPage - 1) * pageSize) + reportesFiltrados.length, totalReportes)

  const visibleReporteIds = useMemo(
    () => reportesFiltrados.map((r) => r.id).filter(Boolean),
    [reportesFiltrados]
  )

  const allVisibleSelected = useMemo(
    () => visibleReporteIds.length > 0 && visibleReporteIds.every((id) => selectedReporteIds.includes(id)),
    [visibleReporteIds, selectedReporteIds]
  )

  const someVisibleSelected = useMemo(
    () => visibleReporteIds.some((id) => selectedReporteIds.includes(id)),
    [visibleReporteIds, selectedReporteIds]
  )

  useEffect(() => {
    // Limpia ids seleccionados que ya no existen en la lista cargada
    const reportesIds = new Set(reportes.map((r) => r.id).filter(Boolean))
    setSelectedReporteIds((prev) => prev.filter((id) => reportesIds.has(id)))
  }, [reportes])

  useEffect(() => {
    if (selectAllReportesRef.current) {
      selectAllReportesRef.current.indeterminate = !allVisibleSelected && someVisibleSelected
    }
  }, [allVisibleSelected, someVisibleSelected])

  const handleToggleSelectAllReportes = (checked) => {
    if (checked) {
      setSelectedReporteIds((prev) => {
        const merged = new Set([...prev, ...visibleReporteIds])
        return Array.from(merged)
      })
      return
    }
    setSelectedReporteIds((prev) => prev.filter((id) => !visibleReporteIds.includes(id)))
  }

  const handleToggleReporte = (reporteId, checked) => {
    if (!reporteId) return
    if (checked) {
      setSelectedReporteIds((prev) => (prev.includes(reporteId) ? prev : [...prev, reporteId]))
      return
    }
    setSelectedReporteIds((prev) => prev.filter((id) => id !== reporteId))
  }

  // Función para ordenar tabla
  const handleOrdenarTabla = (campo) => {
    setOrdenamientoTabla(prev => ({
      campo,
      direccion: prev.campo === campo && prev.direccion === 'asc' ? 'desc' : 'asc'
    }))
  }

  // Datos para gráfico de tendencia temporal
  const datosTendencia = useMemo(() => {
    const dias = periodoSeleccionado === '7d' ? 7 : periodoSeleccionado === '30d' ? 30 : 90
    const hoy = new Date()
    const datos = []

    for (let i = dias - 1; i >= 0; i--) {
      const fecha = new Date(hoy)
      fecha.setDate(fecha.getDate() - i)
      fecha.setHours(0, 0, 0, 0)

      const siguienteDia = new Date(fecha)
      siguienteDia.setDate(siguienteDia.getDate() + 1)

      const reportesDia = reportes.filter(r => {
        const fechaReporte = new Date(r.fecha_creacion)
        fechaReporte.setHours(0, 0, 0, 0)
        return fechaReporte >= fecha && fechaReporte < siguienteDia
      })

      datos.push({
        fecha: fecha.toLocaleDateString('es-CL', { day: 'numeric', month: 'short' }),
        nuevos: reportesDia.filter(r => r.estado === 'nuevo').length,
        en_proceso: reportesDia.filter(r => r.estado === 'proceso').length,
        resueltos: reportesDia.filter(r => r.estado === 'resuelto').length,
        total: reportesDia.length
      })
    }

    return datos
  }, [reportes, periodoSeleccionado])

  // Datos para gráfico de inspectores
  const datosInspectores = useMemo(() => {
    const inspectoresMap = {}
    reportes.forEach(r => {
      const inspector = r.asignado_a || 'Sin asignar'
      if (!inspectoresMap[inspector]) {
        inspectoresMap[inspector] = { asignados: 0, resueltos: 0 }
      }
      inspectoresMap[inspector].asignados++
      if (r.estado === 'resuelto') {
        inspectoresMap[inspector].resueltos++
      }
    })

    return Object.entries(inspectoresMap)
      .map(([nombre, datos]) => ({
        nombre: nombre.length > 15 ? nombre.substring(0, 15) + '...' : nombre,
        asignados: datos.asignados,
        resueltos: datos.resueltos,
        eficiencia: datos.asignados > 0 ? ((datos.resueltos / datos.asignados) * 100).toFixed(1) : 0
      }))
      .sort((a, b) => b.asignados - a.asignados)
      .slice(0, 10)
  }, [reportes])

  // Función para exportar gráfico
  const exportarGrafico = (tipo, nombre) => {
    const canvas = document.querySelector(`.chart-container canvas`) ||
      document.querySelector(`.widget-card canvas`)
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.href = url
      link.download = `${nombre}_${new Date().toISOString().split('T')[0]}.png`
      link.click()
      toast.success('Gráfico exportado exitosamente')
    } else {
      toast.error('No se pudo exportar el gráfico')
    }
  }

  // Simular notificaciones (en producción vendrían del backend)
  useEffect(() => {
    const interval = setInterval(() => {
      if (reportesCriticos.length > 0 && Math.random() > 0.7) {
        const nuevoCritico = reportesCriticos[0]
        const nuevaNotif = {
          id: Date.now(),
          tipo: 'critico',
          titulo: 'Nuevo reporte crítico',
          mensaje: `Reporte ${nuevoCritico.codigo_seguimiento || nuevoCritico.id} requiere atención inmediata`,
          tiempo: 'Hace unos momentos'
        }
        setNotificaciones(prev => [nuevaNotif, ...prev].slice(0, 10))
        toast.warning('Nuevo reporte crítico detectado')
      }
    }, 30000) // Cada 30 segundos

    return () => clearInterval(interval)
  }, [reportesCriticos])

  // Cargar estadísticas de inspectores
  useEffect(() => {
    const loadEstadisticasInspectores = async () => {
      if (vistaActual !== 'cuadrillas' || inspectores.length === 0) return

      setLoadingInspectores(true)
      const stats = {}

      try {
        for (const inspector of inspectores) {
          try {
            const response = await apiClient.get(`${API_ROUTES.ESTADISTICAS_INSPECTOR}${inspector.id}/`)
            stats[inspector.id] = response.data
          } catch {
            // Si no hay API específica, calcular desde reportes
            const reportesInspector = reportes.filter(r => {
              const asignadoA = typeof r.asignado_a === 'object' ? r.asignado_a.id : r.asignado_a
              return asignadoA === inspector.id || asignadoA === inspector.username
            })

            stats[inspector.id] = {
              total_asignados: reportesInspector.length,
              resueltos: reportesInspector.filter(r => r.estado === 'resuelto').length,
              en_proceso: reportesInspector.filter(r => r.estado === 'proceso').length,
              nuevos: reportesInspector.filter(r => r.estado === 'nuevo').length,
              tiempo_promedio_resolucion: 0,
              eficiencia: reportesInspector.length > 0
                ? ((reportesInspector.filter(r => r.estado === 'resuelto').length / reportesInspector.length) * 100).toFixed(1)
                : 0
            }
          }
        }
        setEstadisticasInspectores(stats)
      } catch (error) {
        console.error('Error al cargar estadísticas de inspectores:', error)
      } finally {
        setLoadingInspectores(false)
      }
    }

    loadEstadisticasInspectores()
  }, [vistaActual, inspectores, reportes])

  // Atajo de teclado para búsqueda (Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        searchInputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Cargar búsquedas guardadas desde localStorage
  useEffect(() => {
    const guardadas = localStorage.getItem('busquedasGuardadas')
    if (guardadas) {
      try {
        setBusquedasGuardadas(JSON.parse(guardadas))
      } catch (e) {
        console.error('Error al cargar búsquedas guardadas:', e)
      }
    }
  }, [])

  // Guardar búsqueda actual
  const guardarBusqueda = () => {
    const nuevaBusqueda = {
      id: Date.now(),
      nombre: `Búsqueda ${busquedasGuardadas.length + 1}`,
      filtros: {
        estado: filtroRapidoEstado,
        prioridad: filtroRapidoPrioridad,
        categoria: filtroRapidoCategoria,
        ...filtrosAvanzados,
        query: searchQuery
      },
      fecha: new Date().toISOString()
    }
    const actualizadas = [...busquedasGuardadas, nuevaBusqueda]
    setBusquedasGuardadas(actualizadas)
    localStorage.setItem('busquedasGuardadas', JSON.stringify(actualizadas))
    toast.success('Búsqueda guardada exitosamente')
  }

  // Aplicar búsqueda guardada
  const aplicarBusquedaGuardada = (busqueda) => {
    setFiltroRapidoEstado(busqueda.filtros.estado || '')
    setFiltroRapidoPrioridad(busqueda.filtros.prioridad || '')
    setFiltroRapidoCategoria(busqueda.filtros.categoria || '')
    setSearchQuery(busqueda.filtros.query || '')
    setFiltrosAvanzados(busqueda.filtros)
    toast.success(`Búsqueda "${busqueda.nombre}" aplicada`)
  }

  // Eliminar búsqueda guardada
  const eliminarBusquedaGuardada = (id) => {
    const actualizadas = busquedasGuardadas.filter(b => b.id !== id)
    setBusquedasGuardadas(actualizadas)
    localStorage.setItem('busquedasGuardadas', JSON.stringify(actualizadas))
    toast.success('Búsqueda eliminada')
  }

  // Función de exportación rápida del dashboard
  const handleExportDashboard = async (formato) => {
    try {
      const hoy = new Date()
      const fechaDesde = new Date()
      fechaDesde.setDate(fechaDesde.getDate() - 30)

      if (formato === 'pdf') {
        const response = await apiClient.get(API_ROUTES.EXPORTAR_PDF, {
          params: {
            fecha_desde: fechaDesde.toISOString().split('T')[0],
            fecha_hasta: hoy.toISOString().split('T')[0]
          },
          responseType: 'blob'
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `dashboard_${hoy.toISOString().split('T')[0]}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        toast.success('Dashboard exportado a PDF exitosamente')
      } else if (formato === 'excel') {
        const response = await apiClient.get(API_ROUTES.EXPORTAR_EXCEL, {
          params: {
            fecha_desde: fechaDesde.toISOString().split('T')[0],
            fecha_hasta: hoy.toISOString().split('T')[0]
          },
          responseType: 'blob'
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `dashboard_${hoy.toISOString().split('T')[0]}.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        toast.success('Dashboard exportado a Excel exitosamente')
      }
    } catch (error) {
      console.error('Error al exportar dashboard:', error)
      toast.error('Error al exportar el dashboard')
    }
  }

  return (
    <div className="dashboard-enterprise">
      {/* Sidebar Enterprise */}
      <aside className={`sidebar-enterprise ${isSidebarOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}>
        {/* Logo Area */}
        <div className="sidebar-logo">
          <div className="logo-container">
            <div className="logo-icon">
              <LeafIconSVG />
            </div>
            {isSidebarOpen && (
              <span className="logo-text">Eco<span className="logo-text-accent">Alerta</span></span>
            )}
          </div>
        </div>

        {/* User Profile */}
        <div className={`sidebar-user ${!isSidebarOpen ? 'sidebar-user-collapsed' : ''}`}>
          <div className="user-avatar">
            {userInfo?.username ? (
              <span className="user-avatar-initial">
                {userInfo.username.charAt(0).toUpperCase()}
              </span>
            ) : (
              <span className="user-avatar-initial">I</span>
            )}
          </div>
          {isSidebarOpen && (
            <div className="user-info-text">
              <p className="user-name">{userInfo?.username || 'Inspector'}</p>
              <p className="user-role">Inspector Municipal</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <div className="nav-section">
            {isSidebarOpen && <p className="nav-section-label">Plataforma</p>}
            <div
              className={`nav-item-enterprise ${vistaActual === 'dashboard' ? 'active' : ''}`}
              onClick={() => setVistaActual('dashboard')}
            >
              <LayoutDashboardIcon size={18} />
              {isSidebarOpen && <span>Dashboard General</span>}
              {vistaActual === 'dashboard' && isSidebarOpen && <div className="nav-dot"></div>}
            </div>
            <div
              className={`nav-item-enterprise ${vistaActual === 'mapa' ? 'active' : ''}`}
              onClick={() => setVistaActual('mapa')}
            >
              <MapIconSVG size={18} />
              {isSidebarOpen && <span>Mapa Geo-Referencial</span>}
            </div>
            <div
              className={`nav-item-enterprise ${vistaActual === 'estadisticas' ? 'active' : ''}`}
              onClick={() => setVistaActual('estadisticas')}
            >
              <AlertTriangleIconSVG size={18} />
              {isSidebarOpen && <span>Centro de Alertas</span>}
            </div>
            <div
              className={`nav-item-enterprise ${vistaActual === 'live' ? 'active' : ''}`}
              onClick={() => setVistaActual('live')}
            >
              <ActivityIconSVG size={18} />
              {isSidebarOpen && <span>Live Operations</span>}
            </div>
            <div
              className={`nav-item-enterprise ${vistaActual === 'reportes' ? 'active' : ''}`}
              onClick={() => setVistaActual('reportes')}
            >
              <FileTextIconSVG size={18} />
              {isSidebarOpen && <span>Reportes</span>}
            </div>
          </div>

          <div className="nav-section">
            {isSidebarOpen && <p className="nav-section-label">Gestión</p>}
            <div
              className={`nav-item-enterprise ${vistaActual === 'exportar' ? 'active' : ''}`}
              onClick={() => setVistaActual('exportar')}
            >
              <FileTextIconSVG size={18} />
              {isSidebarOpen && <span>Reportes & Informes</span>}
            </div>
            <div
              className={`nav-item-enterprise ${vistaActual === 'cuadrillas' ? 'active' : ''}`}
              onClick={() => setVistaActual('cuadrillas')}
            >
              <UsersIconSVG size={18} />
              {isSidebarOpen && <span>Cuadrillas Terreno</span>}
            </div>
            <div
              className={`nav-item-enterprise ${vistaActual === 'sla' ? 'active' : ''}`}
              onClick={() => setVistaActual('sla')}
            >
              <AlertTriangleIconSVG size={18} />
              {isSidebarOpen && <span>SLA y Alertas</span>}
            </div>
            <div
              className={`nav-item-enterprise ${vistaActual === 'planificacion' ? 'active' : ''}`}
              onClick={() => setVistaActual('planificacion')}
            >
              <CalendarIconSVG size={18} />
              {isSidebarOpen && <span>Planificación</span>}
            </div>
            <div
              className={`nav-item-enterprise ${vistaActual === 'inteligencia' ? 'active' : ''}`}
              onClick={() => setVistaActual('inteligencia')}
            >
              <BrainIconSVG size={18} /> {/* Assuming BrainIconSVG for 'Eco-Inteligencia' */}
              {isSidebarOpen && <span>Eco-Inteligencia</span>}
            </div>
          </div>

          {userInfo?.tipo === 'admin' && (
            <div className="nav-section">
              {isSidebarOpen && <p className="nav-section-label">Administración</p>}
              <div
                className="nav-item-enterprise"
                onClick={() => navigate('/admin')}
              >
                <SettingsIconSVG size={18} />
                {isSidebarOpen && <span>Panel Admin</span>}
              </div>
            </div>
          )}
        </nav>

        {/* Footer Sidebar */}
        <div className="sidebar-footer">
          {userInfo?.tipo === 'inspector' && (
            <div
              className="nav-item-enterprise"
              onClick={() => setShowLocationUpdater(true)}
              title="Actualizar mi ubicación"
            >
              <MapIconSVG size={18} />
              {isSidebarOpen && <span>Mi Ubicación</span>}
            </div>
          )}
          <div className="nav-item-enterprise">
            <SettingsIconSVG size={18} />
            {isSidebarOpen && <span>Configuración</span>}
          </div>
          <div style={{ marginTop: 'auto', paddingTop: '2rem', display: 'flex', justifyContent: 'center' }}>
            <button
              onClick={() => setRunTour(true)}
              className="btn btn-outline-secondary"
              style={{
                padding: '0.5rem 1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.875rem',
                color: '#64748b',
                background: 'transparent',
                border: '1px solid #cbd5e1',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => { e.currentTarget.style.color = '#3b82f6'; e.currentTarget.style.borderColor = '#3b82f6'; }}
              onMouseOut={(e) => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.borderColor = '#cbd5e1'; }}
            >
              <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>?</span> Repetir Tutorial
            </button>
          </div>
        </div>
      </aside>

      <DashboardTour run={runTour} setRun={setRunTour} usuario={userInfo} onTourComplete={() => { const u = { ...userInfo, tour_completado: true }; setUserInfo(u); localStorage.setItem('user', JSON.stringify(u)); }} />

      {/* Main Content */}
      <div className="main-content-enterprise">
        {/* Topbar Enterprise */}
        <header className="topbar-enterprise">
          <div className="topbar-left">
            <button
              className="menu-toggle"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            >
              <MenuIconSVG size={20} />
            </button>

            {/* Breadcrumbs */}
            <nav className="breadcrumbs">
              <span className="breadcrumb-item">Inicio</span>
              <ChevronRightIconSVG size={14} />
              <span className="breadcrumb-item active">Dashboard Operativo</span>
            </nav>
          </div>

          <div className="topbar-right">
            {offlinePendingCount > 0 && (
              <div className="offline-pending-indicator" title="Cambios pendientes por sincronizar">
                {offlinePendingCount} pendiente{offlinePendingCount > 1 ? 's' : ''} offline
              </div>
            )}
            {/* Search Global */}
            <div className="search-global">
              <SearchIconSVG size={16} />
              <input
                type="text"
                placeholder=""
                className="search-input"
              />
            </div>

            <div className="topbar-divider"></div>

            {/* Notificaciones */}
            <div className="notification-wrapper">
              <button
                className="notification-btn"
                onClick={() => setMostrarNotificaciones(!mostrarNotificaciones)}
                aria-label={`Notificaciones${notificaciones.length > 0 ? `: ${notificaciones.length} no leídas` : ''}`}
                aria-expanded={mostrarNotificaciones}
                aria-haspopup="true"
              >
                <BellIconSVG size={20} aria-hidden="true" />
                {notificaciones.length > 0 && (
                  <span className="notification-badge" aria-label={`${notificaciones.length} notificaciones no leídas`}>
                    {notificaciones.length}
                  </span>
                )}
              </button>
              {mostrarNotificaciones && (
                <NotificationsPanel
                  onClose={() => setMostrarNotificaciones(false)}
                />
              )}
            </div>

            <div className="topbar-divider"></div>

            {/* Modo Oscuro/Claro */}
            <DarkModeToggle />

            <div className="topbar-divider"></div>

            {/* Botón Cerrar Sesión */}
            <button
              className="logout-btn-topbar"
              onClick={handleLogout}
              title="Cerrar Sesión"
            >
              <LogOutIconSVG size={18} />
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="dashboard-content-enterprise">
          <div className="dashboard-container">

            {/* Page Header */}
            <div className="page-header-enterprise">
              <div className="page-header-left">
                <h1 className="page-title">Resumen Operativo</h1>
                <p className="page-subtitle">Región de Coquimbo • Última sincronización: {new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' })}</p>
              </div>
              <div className="page-header-right">
                {/* Selector de Período */}
                <select
                  className="period-selector"
                  value={periodoSeleccionado}
                  onChange={(e) => setPeriodoSeleccionado(e.target.value)}
                >
                  <option value="hoy">Hoy</option>
                  <option value="7d">Últimos 7 días</option>
                  <option value="30d">Últimos 30 días</option>
                  <option value="mes">Este mes</option>
                  <option value="mes-anterior">Mes anterior</option>
                </select>
                <button className="btn-new-report">
                  <PlusIconSVG size={16} />
                  Nuevo Reporte
                </button>
                {/* Botón de Exportación Rápida */}
                <div className="export-dropdown">
                  <button className="btn-export-quick">
                    <DownloadIconSVG size={16} />
                    Exportar
                  </button>
                  <div className="export-dropdown-menu">
                    <button onClick={() => handleExportDashboard('pdf')}>Exportar a PDF</button>
                    <button onClick={() => handleExportDashboard('excel')}>Exportar a Excel</button>
                  </div>
                </div>
              </div>
            </div>

            {/* Búsqueda Rápida Mejorada */}
            {vistaActual === 'dashboard' && (
              <div className="quick-search-section">
                <div className="search-input-wrapper">
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Buscar reportes (Ctrl+K)..."
                    className="quick-search-input"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <span className="search-shortcut-hint">Ctrl+K</span>
                </div>
              </div>
            )}

            {/* Filtros Rápidos con Chips */}
            {vistaActual === 'dashboard' && (
              <>
                <div className="quick-filters-section">
                  <div className="filters-group">
                    <span className="filters-label">Estado:</span>
                    <div className="filter-chips">
                      {['nuevo', 'proceso', 'resuelto'].map(estado => (
                        <button
                          key={estado}
                          className={`filter-chip ${filtroRapidoEstado === estado ? 'active' : ''}`}
                          onClick={() => handleFiltroRapido('estado', estado)}
                        >
                          {estado.charAt(0).toUpperCase() + estado.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="filters-group">
                    <span className="filters-label">Prioridad:</span>
                    <div className="filter-chips">
                      {['alto', 'medio', 'bajo'].map(prioridad => (
                        <button
                          key={prioridad}
                          className={`filter-chip priority-${prioridad} ${filtroRapidoPrioridad === prioridad ? 'active' : ''}`}
                          onClick={() => handleFiltroRapido('prioridad', prioridad)}
                        >
                          {prioridad.charAt(0).toUpperCase() + prioridad.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="filters-group">
                    <span className="filters-label">Categoría:</span>
                    <div className="filter-chips">
                      {categorias.slice(0, 5).map(cat => (
                        <button
                          key={cat.id}
                          className={`filter-chip ${filtroRapidoCategoria === cat.nombre ? 'active' : ''}`}
                          onClick={() => handleFiltroRapido('categoria', cat.nombre)}
                        >
                          {cat.nombre}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="filters-actions">
                    <button
                      className="btn-filters-advanced"
                      onClick={() => setMostrarFiltrosAvanzados(!mostrarFiltrosAvanzados)}
                    >
                      {mostrarFiltrosAvanzados ? 'Ocultar' : 'Mostrar'} Filtros Avanzados
                    </button>
                    <button
                      className="btn-save-search"
                      onClick={guardarBusqueda}
                      disabled={!filtroRapidoEstado && !filtroRapidoPrioridad && !filtroRapidoCategoria && !searchQuery}
                    >
                      Guardar Búsqueda
                    </button>
                  </div>
                </div>

                {/* Panel de Búsquedas Guardadas */}
                {busquedasGuardadas.length > 0 && (
                  <div className="saved-searches-section">
                    <span className="saved-searches-label">Búsquedas guardadas:</span>
                    <div className="saved-searches-list">
                      {busquedasGuardadas.map(busqueda => (
                        <div key={busqueda.id} className="saved-search-item">
                          <button
                            className="saved-search-btn"
                            onClick={() => aplicarBusquedaGuardada(busqueda)}
                          >
                            {busqueda.nombre}
                          </button>
                          <button
                            className="saved-search-delete"
                            onClick={() => eliminarBusquedaGuardada(busqueda.id)}
                            title="Eliminar"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Filtros Avanzados */}
                {mostrarFiltrosAvanzados && (
                  <div className="advanced-filters-panel">
                    <div className="advanced-filters-grid">
                      <div className="filter-field">
                        <label>Fecha Desde</label>
                        <input
                          type="date"
                          value={filtrosAvanzados.fechaDesde}
                          onChange={(e) => setFiltrosAvanzados(prev => ({ ...prev, fechaDesde: e.target.value }))}
                        />
                      </div>
                      <div className="filter-field">
                        <label>Fecha Hasta</label>
                        <input
                          type="date"
                          value={filtrosAvanzados.fechaHasta}
                          onChange={(e) => setFiltrosAvanzados(prev => ({ ...prev, fechaHasta: e.target.value }))}
                        />
                      </div>
                      <div className="filter-field">
                        <label>Inspector</label>
                        <select
                          value={filtrosAvanzados.inspector}
                          onChange={(e) => setFiltrosAvanzados(prev => ({ ...prev, inspector: e.target.value }))}
                        >
                          <option value="">Todos</option>
                          {inspectores.map(ins => (
                            <option key={ins.id} value={ins.id}>{ins.username}</option>
                          ))}
                        </select>
                      </div>
                      <div className="filter-field">
                        <label>Tiene Foto</label>
                        <select
                          value={filtrosAvanzados.tieneFoto}
                          onChange={(e) => setFiltrosAvanzados(prev => ({ ...prev, tieneFoto: e.target.value }))}
                        >
                          <option value="">Todos</option>
                          <option value="si">Sí</option>
                          <option value="no">No</option>
                        </select>
                      </div>
                      <div className="filter-field">
                        <label>Validado</label>
                        <select
                          value={filtrosAvanzados.validado}
                          onChange={(e) => setFiltrosAvanzados(prev => ({ ...prev, validado: e.target.value }))}
                        >
                          <option value="">Todos</option>
                          <option value="si">Sí</option>
                          <option value="no">No</option>
                        </select>
                      </div>
                      <div className="filter-field">
                        <button
                          className="btn-clear-filters"
                          onClick={() => setFiltrosAvanzados({
                            fechaDesde: '',
                            fechaHasta: '',
                            inspector: '',
                            prioridadMinima: '',
                            tieneFoto: '',
                            validado: ''
                          })}
                        >
                          Limpiar Filtros
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* KPI Cards Grid */}
            <div className="stats-grid-enterprise">
              {loading ? (
                <>
                  <div className="stat-card-enterprise skeleton">
                    <Skeleton height="60px" width="100%" />
                  </div>
                  <div className="stat-card-enterprise skeleton">
                    <Skeleton height="60px" width="100%" />
                  </div>
                  <div className="stat-card-enterprise skeleton">
                    <Skeleton height="60px" width="100%" />
                  </div>
                  <div className="stat-card-enterprise skeleton">
                    <Skeleton height="60px" width="100%" />
                  </div>
                </>
              ) : (
                <>
                  <StatCardEnterprise
                    title="Denuncias Totales"
                    value={estadisticas.total.toLocaleString()}
                    subtext="En los últimos 30 días"
                    trend={12.5}
                    trendLabel="Crecimiento"
                    icon={AlertTriangleIconSVG}
                    colorClass="text-amber-600"
                    bgIconClass="bg-amber-100"
                    sparkColor="#d97706"
                    sparkData={sparkData1}
                  />
                  <StatCardEnterprise
                    title="Tasa de Resolución"
                    value={`${estadisticas.resueltos > 0 && estadisticas.total > 0 ? ((estadisticas.resueltos / estadisticas.total) * 100).toFixed(1) : 0}%`}
                    subtext="Objetivo mensual: 85%"
                    trend={5.4}
                    trendLabel="Eficiencia"
                    icon={() => <span>✓</span>}
                    colorClass="text-emerald-600"
                    bgIconClass="bg-emerald-100"
                    sparkColor="#059669"
                    sparkData={sparkData2}
                  />
                  <StatCardEnterprise
                    title="Tiempo Promedio"
                    value={tiempoPromedioResolucion > 0 ? `${tiempoPromedioResolucion.toFixed(1)} Días` : 'N/A'}
                    subtext="Desde reporte hasta cierre"
                    trend={estadisticasAnteriores ?
                      ((tiempoPromedioResolucion - 1.2) / 1.2 * 100).toFixed(1) : -15.3}
                    trendLabel="Mejora"
                    icon={() => <span>⏱</span>}
                    colorClass="text-blue-600"
                    bgIconClass="bg-blue-100"
                    sparkColor="#2563eb"
                    sparkData={sparkData3}
                  />
                  <StatCardEnterprise
                    title="Cuadrillas Activas"
                    value="14"
                    subtext="Operando actualmente"
                    trend={0}
                    trendLabel="Capacidad"
                    icon={UsersIconSVG}
                    colorClass="text-indigo-600"
                    bgIconClass="bg-indigo-100"
                    sparkColor="#4f46e5"
                    sparkData={sparkData4}
                  />
                </>
              )}
            </div>

            {/* Main Visual Section - Chart (solo en dashboard y estadisticas) */}
            {vistaActual === 'dashboard' && (
              <div className="visual-section-enterprise">
                {/* Chart Component */}
                <div className="chart-card-enterprise">
                  <div className="chart-header">
                    <div>
                      <h3 className="chart-title">Dinámica de Incidencias</h3>
                      <p className="chart-subtitle">Comparativa de ingresos vs. resoluciones</p>
                    </div>
                    <div className="chart-actions">
                      <button className="chart-action-btn">
                        <FilterIconSVG size={16} />
                      </button>
                      <button className="chart-action-btn">
                        <DownloadIconSVG size={16} />
                      </button>
                    </div>
                  </div>

                  <div className="chart-container">
                    <div className="chart-view-toggle">
                      <button
                        className={vistaTendencia === 'area' ? 'active' : ''}
                        onClick={() => setVistaTendencia('area')}
                      >
                        Área
                      </button>
                      <button
                        className={vistaTendencia === 'line' ? 'active' : ''}
                        onClick={() => setVistaTendencia('line')}
                      >
                        Línea
                      </button>
                      <button
                        className={vistaTendencia === 'bar' ? 'active' : ''}
                        onClick={() => setVistaTendencia('bar')}
                      >
                        Barras
                      </button>
                      <button
                        className="btn-export-chart"
                        onClick={() => exportarGrafico('png', 'tendencia')}
                        title="Exportar gráfico"
                      >
                        <DownloadIconSVG size={16} />
                      </button>
                    </div>
                    <ResponsiveContainer width="100%" height="100%">
                      {vistaTendencia === 'area' ? (
                        <AreaChart data={datosTendencia} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <defs>
                            <linearGradient id="colorNuevos" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1} />
                              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorResueltos" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.1} />
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="fecha" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
                            itemStyle={{ color: '#fff', fontSize: '13px' }}
                            labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                          />
                          <Area type="monotone" dataKey="nuevos" stroke="#6366f1" strokeWidth={2} fill="url(#colorNuevos)" name="Nuevos" />
                          <Area type="monotone" dataKey="resueltos" stroke="#10b981" strokeWidth={2} fill="url(#colorResueltos)" name="Resueltos" />
                        </AreaChart>
                      ) : vistaTendencia === 'line' ? (
                        <AreaChart data={datosTendencia} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="fecha" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
                            itemStyle={{ color: '#fff', fontSize: '13px' }}
                            labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                          />
                          <Area type="monotone" dataKey="nuevos" stroke="#6366f1" strokeWidth={2} fill="none" name="Nuevos" />
                          <Area type="monotone" dataKey="resueltos" stroke="#10b981" strokeWidth={2} fill="none" name="Resueltos" />
                        </AreaChart>
                      ) : (
                        <BarChart data={datosTendencia} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="fecha" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
                            itemStyle={{ color: '#fff', fontSize: '13px' }}
                            labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                          />
                          <Legend />
                          <Bar dataKey="nuevos" fill="#6366f1" name="Nuevos" />
                          <Bar dataKey="resueltos" fill="#10b981" name="Resueltos" />
                        </BarChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Gráfico de Inspectores */}
                {widgetsVisibles.inspectores && datosInspectores.length > 0 && (
                  <div className="widget-card widget-inspectores">
                    <div className="widget-header">
                      <h3 className="widget-title">Rendimiento por Inspector</h3>
                      <button
                        className="btn-export-widget"
                        onClick={() => exportarGrafico('png', 'inspectores')}
                        title="Exportar gráfico"
                      >
                        <DownloadIconSVG size={16} />
                      </button>
                    </div>
                    <div className="widget-content">
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={datosInspectores} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" />
                          <YAxis dataKey="nombre" type="category" width={120} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="asignados" fill="#6366f1" name="Asignados" />
                          <Bar dataKey="resueltos" fill="#10b981" name="Resueltos" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Widgets Adicionales - Grid de 2 columnas */}
                <div className="dashboard-widgets-grid">
                  {/* Widget: Gráfico de Categorías (Pie Chart) */}
                  <div className="widget-card">
                    <div className="widget-header">
                      <h3 className="widget-title">Distribución por Categoría</h3>
                    </div>
                    <div className="widget-content">
                      {datosCategorias.length > 0 ? (
                        <ResponsiveContainer width="100%" height={250}>
                          <PieChart>
                            <Pie
                              data={datosCategorias}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {datosCategorias.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS_PIE[index % COLORS_PIE.length]} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="widget-empty">No hay datos disponibles</div>
                      )}
                    </div>
                  </div>

                  {/* Widget: Alertas Críticas */}
                  <div className="widget-card widget-alerts">
                    <div className="widget-header">
                      <h3 className="widget-title">🚨 Alertas Críticas</h3>
                      <span className="alert-count">{reportesCriticos.length}</span>
                    </div>
                    <div className="widget-content">
                      {reportesCriticos.length > 0 ? (
                        <div className="alerts-list">
                          {reportesCriticos.map((reporte) => (
                            <div
                              key={reporte.id || reporte.codigo_seguimiento}
                              className="alert-item"
                              onClick={() => handleVerDetalle(reporte)}
                            >
                              <div className="alert-main">
                                <span className="alert-code">{reporte.codigo_seguimiento || reporte.id}</span>
                                <p className="alert-location">{reporte.direccion || reporte.direccion_completa || 'Sin dirección'}</p>
                              </div>
                              <div className="alert-meta">
                                <span className="alert-risk">Riesgo: {reporte.prediction?.risk_level?.toUpperCase() || 'ALTO'}</span>
                                {(reporte.prediction?.probability * 100).toFixed(0)}%
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="widget-empty">No hay alertas críticas</div>
                      )}
                    </div>
                  </div>

                  {/* Widget: Actividad del Día */}
                  <div className="widget-card widget-activity">
                    <div className="widget-header">
                      <h3 className="widget-title">📊 Actividad de Hoy</h3>
                    </div>
                    <div className="widget-content">
                      <div className="activity-stats">
                        <div className="activity-item">
                          <span className="activity-label">Nuevos</span>
                          <span className="activity-value new">{actividadHoy.nuevos}</span>
                        </div>
                        <div className="activity-item">
                          <span className="activity-label">En Proceso</span>
                          <span className="activity-value process">{actividadHoy.en_proceso}</span>
                        </div>
                        <div className="activity-item">
                          <span className="activity-label">Resueltos</span>
                          <span className="activity-value resolved">{actividadHoy.resueltos}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Widget: Zonas de Riesgo */}
                  <div className="widget-card widget-zones">
                    <div className="widget-header">
                      <h3 className="widget-title">📍 Zonas de Mayor Riesgo</h3>
                      <button
                        className="view-map-btn"
                        onClick={() => setVistaActual('mapa')}
                      >
                        Ver Mapa
                      </button>
                    </div>
                    <div className="widget-content">
                      {zonasRiesgo.length > 0 ? (
                        <div className="zones-list">
                          {zonasRiesgo.map((zona, index) => (
                            <div key={index} className="zone-item">
                              <span className="zone-rank">#{index + 1}</span>
                              <div className="zone-info">
                                <p className="zone-name">{zona.zona}</p>
                                <p className="zone-count">{zona.cantidad} reportes</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="widget-empty">No hay datos de zonas</div>
                      )}
                    </div>
                  </div>

                  {/* Widget: Comparativa de Períodos */}
                  {estadisticasAnteriores && (
                    <div className="widget-card widget-comparison">
                      <div className="widget-header">
                        <h3 className="widget-title">📈 Comparativa de Períodos</h3>
                      </div>
                      <div className="widget-content">
                        <div className="comparison-stats">
                          <div className="comparison-item">
                            <span className="comparison-label">Total</span>
                            <div className="comparison-values">
                              <span className="comparison-current">{estadisticas.total}</span>
                              <span className={`comparison-trend ${estadisticas.total >= estadisticasAnteriores.total ? 'trend-up' : 'trend-down'}`}>
                                {estadisticas.total >= estadisticasAnteriores.total ? '↑' : '↓'} {Math.abs(((estadisticas.total - estadisticasAnteriores.total) / estadisticasAnteriores.total * 100).toFixed(1))}%
                              </span>
                            </div>
                            <span className="comparison-previous">Anterior: {estadisticasAnteriores.total}</span>
                          </div>
                          <div className="comparison-item">
                            <span className="comparison-label">Resueltos</span>
                            <div className="comparison-values">
                              <span className="comparison-current">{estadisticas.resueltos}</span>
                              <span className={`comparison-trend ${estadisticas.resueltos >= estadisticasAnteriores.resueltos ? 'trend-up' : 'trend-down'}`}>
                                {estadisticas.resueltos >= estadisticasAnteriores.resueltos ? '↑' : '↓'} {Math.abs(((estadisticas.resueltos - estadisticasAnteriores.resueltos) / (estadisticasAnteriores.resueltos || 1) * 100).toFixed(1))}%
                              </span>
                            </div>
                            <span className="comparison-previous">Anterior: {estadisticasAnteriores.resueltos}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Reportes Recientes */}
                <div className="recent-reports-card">
                  <div className="recent-reports-header">
                    <h3 className="recent-reports-title">Reportes Más Recientes</h3>
                    <button
                      className="view-all-btn"
                      onClick={() => setVistaActual('reportes')}
                    >
                      Ver todos
                    </button>
                  </div>
                  <div className="recent-reports-list">
                    {loading ? (
                      <div className="recent-reports-loading">
                        <Skeleton height="60px" width="100%" />
                        <Skeleton height="60px" width="100%" />
                        <Skeleton height="60px" width="100%" />
                      </div>
                    ) : reportesFiltrados.length === 0 ? (
                      <div className="recent-reports-empty">
                        <p>No hay reportes disponibles</p>
                      </div>
                    ) : (
                      reportesFiltrados
                        .sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion))
                        .slice(0, 5)
                        .map((reporte) => (
                          <div
                            key={reporte.id || reporte.codigo_seguimiento}
                            className="recent-report-item"
                            onClick={() => handleVerDetalle(reporte)}
                          >
                            <div className="recent-report-main">
                              <div className="recent-report-id">{reporte.codigo_seguimiento || reporte.id}</div>
                              <div className="recent-report-info">
                                <p className="recent-report-location">{reporte.direccion || reporte.direccion_completa || 'Sin dirección'}</p>
                                <p className="recent-report-category">{reporte.categoria_nombre || 'Sin categoría'}</p>
                              </div>
                            </div>
                            <div className="recent-report-meta">
                              <span className={`status-badge status-${reporte.estado}`}>
                                {reporte.estado.charAt(0).toUpperCase() + reporte.estado.slice(1)}
                              </span>
                              <span className="recent-report-date">
                                {new Date(reporte.fecha_creacion).toLocaleDateString('es-CL', {
                                  day: 'numeric',
                                  month: 'short',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                            </div>
                          </div>
                        ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Vista Estadísticas - Chart */}
            {vistaActual === 'estadisticas' && (
              <div className="visual-section-enterprise">
                <div className="chart-card-enterprise">
                  <div className="chart-header">
                    <div>
                      <h3 className="chart-title">Dinámica de Incidencias</h3>
                      <p className="chart-subtitle">Comparativa de ingresos vs. resoluciones</p>
                    </div>
                    <div className="chart-actions">
                      <button className="chart-action-btn">
                        <FilterIconSVG size={16} />
                      </button>
                      <button className="chart-action-btn">
                        <DownloadIconSVG size={16} />
                      </button>
                    </div>
                  </div>

                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={dataDenuncias} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorIncidencias2" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1} />
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="colorResueltos2" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.1} />
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#fff' }}
                          itemStyle={{ color: '#fff', fontSize: '13px' }}
                          labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                        />
                        <Area type="monotone" dataKey="denuncias" stroke="#6366f1" strokeWidth={2} fill="url(#colorIncidencias2)" name="Nuevos Casos" activeDot={{ r: 6 }} />
                        <Area type="monotone" dataKey="resueltos" stroke="#10b981" strokeWidth={2} fill="url(#colorResueltos2)" name="Resueltos" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {/* Vista Mapa Geo-Referencial */}
            {vistaActual === 'mapa' && (
              <>
                {/* Búsqueda Avanzada */}
                <div className="search-section-enterprise">
                  <AdvancedSearch
                    onSearch={handleSearch}
                    onReset={handleResetSearch}
                    categorias={categorias}
                    tags={tags}
                    inspectores={inspectores}
                  />
                </div>

                {/* Filters para mapa */}
                <div className="filters-bar-enterprise">
                  <div className="filter-group">
                    <label>Estado</label>
                    <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
                      <option value="">Todos</option>
                      <option value="nuevo">Nuevo</option>
                      <option value="proceso">En Proceso</option>
                      <option value="resuelto">Resuelto</option>
                    </select>
                  </div>
                  <div className="heatmap-control">


                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={heatmapEnabled}
                        onChange={(e) => {
                          handleHeatmapToggle(e.target.checked)
                        }}
                        disabled={mapView3D}
                      />
                      <span style={{ fontWeight: 500, opacity: mapView3D ? 0.5 : 1 }}>🔥 Mapa de Calor</span>
                      {loadingHeatmap && <span style={{ fontSize: '12px', color: '#666' }}>(Cargando...)</span>}
                      {heatmapEnabled && !loadingHeatmap && heatmapData.length === 0 && (
                        <span style={{ fontSize: '12px', color: '#ff6b6b' }}>(Sin datos - verifique que haya reportes con ubicación)</span>
                      )}
                      {heatmapEnabled && !loadingHeatmap && heatmapData.length > 0 && (
                        <span style={{ fontSize: '12px', color: '#228B22' }}>({heatmapData.length} puntos)</span>
                      )}
                    </label>
                  </div>
                </div>

                {/* Toggle Vista 2D/3D */}
                <div className="map-view-toggle-container" style={{
                  marginBottom: '1rem',
                  display: 'flex',
                  gap: '0.5rem',
                  alignItems: 'center',
                  padding: '0.75rem',
                  background: 'white',
                  borderRadius: '0.5rem',
                  border: '1px solid #e2e8f0'
                }}>
                  <button
                    onClick={() => setMapView3D(false)}
                    className={`map-view-btn ${!mapView3D ? 'active' : ''}`}
                    style={{
                      padding: '0.5rem 1rem',
                      border: '1px solid #e2e8f0',
                      borderRadius: '0.375rem',
                      background: !mapView3D ? '#228B22' : 'white',
                      color: !mapView3D ? 'white' : '#475569',
                      cursor: 'pointer',
                      fontWeight: 500,
                      transition: 'all 0.2s',
                      fontSize: '0.875rem'
                    }}
                  >
                    📍 Vista 2D
                  </button>
                  <button
                    onClick={() => setMapView3D(true)}
                    className={`map-view-btn ${mapView3D ? 'active' : ''}`}
                    style={{
                      padding: '0.5rem 1rem',
                      border: '1px solid #e2e8f0',
                      borderRadius: '0.375rem',
                      background: mapView3D ? '#228B22' : 'white',
                      color: mapView3D ? 'white' : '#475569',
                      cursor: 'pointer',
                      fontWeight: 500,
                      transition: 'all 0.2s',
                      fontSize: '0.875rem'
                    }}
                  >
                    🌍 Vista 3D
                  </button>
                </div>

                {/* Mapa completo con Leaflet o Cesium 3D */}
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
                  ) : mapView3D ? (
                    // Vista 3D con Cesium
                    <MapView3D
                      reportes={reportes.filter(r => r.lat && r.lng)}
                      center={[-29.9533, -71.3395]}
                      onMarkerClick={handleVerDetalle}
                    />
                  ) : (
                    // Vista 2D con Leaflet
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

                      {/* Marcadores normales (solo si no hay Clustering ni Heatmap) */}
                      {!heatmapEnabled && reportes
                        .filter(reporte => reporte.lat && reporte.lng)
                        .map(reporte => (
                          <Marker
                            key={reporte.id || reporte.codigo_seguimiento}
                            position={[reporte.lat, reporte.lng]}
                          >
                            <Popup>
                              <div>
                                <b>{reporte.codigo_seguimiento}</b><br />
                                {reporte.categoria_nombre}<br />
                                <small>{reporte.direccion || reporte.direccion_completa || 'Sin dirección'}</small><br />
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
              </>
            )}

            {/* Vista Reportes - Todos los reportes */}
            {vistaActual === 'reportes' && (
              <div className="table-section-enterprise">
                <div className="table-header-enterprise">
                  <div className="table-header-left">
                    <h3 className="table-title">Todos los Reportes</h3>
                    <span className="table-badge">{totalReportes}</span>
                    {selectedReporteIds.length > 0 && (
                      <span className="table-badge">{selectedReporteIds.length} seleccionados</span>
                    )}
                  </div>
                  <div className="table-header-right">
                    <div className="bulk-actions">
                      <select
                        value={bulkInspectorId}
                        onChange={(e) => setBulkInspectorId(e.target.value)}
                        className="bulk-select"
                      >
                        <option value="">Asignar inspector...</option>
                        {inspectores.map((ins) => (
                          <option key={ins.id} value={ins.id}>{ins.username}</option>
                        ))}
                      </select>
                      <button
                        className="table-action-btn"
                        onClick={() => bulkInspectorId && handleBulkUpdate({ asignado_a: bulkInspectorId })}
                        disabled={!bulkInspectorId || selectedReporteIds.length === 0}
                      >
                        Asignar
                      </button>
                      <select
                        value={bulkEstado}
                        onChange={(e) => setBulkEstado(e.target.value)}
                        className="bulk-select"
                      >
                        <option value="">Cambiar estado...</option>
                        <option value="nuevo">Nuevo</option>
                        <option value="proceso">Proceso</option>
                        <option value="resuelto">Resuelto</option>
                        <option value="cerrado">Cerrado</option>
                      </select>
                      <button
                        className="table-action-btn"
                        onClick={() => bulkEstado && handleBulkUpdate({ estado: bulkEstado })}
                        disabled={!bulkEstado || selectedReporteIds.length === 0}
                      >
                        Aplicar
                      </button>
                    </div>
                    <button
                      className={`table-view-toggle ${!vistaCalendario ? 'active' : ''}`}
                      onClick={() => setVistaCalendario(false)}
                    >
                      Tabla
                    </button>
                    <button
                      className={`table-view-toggle ${vistaCalendario ? 'active' : ''}`}
                      onClick={() => setVistaCalendario(true)}
                    >
                      Calendario
                    </button>
                    <div className="table-search">
                      <SearchIconSVG size={14} />
                      <input
                        type="text"
                        placeholder="Filtrar tabla..."
                        className="table-search-input"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>
                    <button className="table-action-btn" onClick={handleExportCSV}>
                      <DownloadIconSVG size={14} />
                      Exportar
                    </button>
                  </div>
                </div>

                {vistaCalendario ? (
                  <div className="calendar-view">
                    <div className="calendar-header">
                      <button onClick={() => {
                        const nuevoMes = new Date(mesCalendario)
                        nuevoMes.setMonth(nuevoMes.getMonth() - 1)
                        setMesCalendario(nuevoMes)
                      }}>
                        ←
                      </button>
                      <h3>{mesCalendario.toLocaleDateString('es-CL', { month: 'long', year: 'numeric' })}</h3>
                      <button onClick={() => {
                        const nuevoMes = new Date(mesCalendario)
                        nuevoMes.setMonth(nuevoMes.getMonth() + 1)
                        setMesCalendario(nuevoMes)
                      }}>
                        →
                      </button>
                    </div>
                    <div className="calendar-grid">
                      {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map(dia => (
                        <div key={dia} className="calendar-day-header">{dia}</div>
                      ))}
                      {Array.from({ length: new Date(mesCalendario.getFullYear(), mesCalendario.getMonth() + 1, 0).getDate() }, (_, i) => {
                        const fecha = new Date(mesCalendario.getFullYear(), mesCalendario.getMonth(), i + 1)
                        const reportesDia = reportesFiltrados.filter(r => {
                          const fechaReporte = new Date(r.fecha_creacion)
                          return fechaReporte.toDateString() === fecha.toDateString()
                        })
                        const diaSemana = fecha.getDay()
                        const esHoy = fecha.toDateString() === new Date().toDateString()

                        return (
                          <div
                            key={i}
                            className={`calendar-day ${diaSemana === 0 || diaSemana === 6 ? 'weekend' : ''} ${esHoy ? 'today' : ''}`}
                            style={{ gridColumnStart: i === 0 ? diaSemana + 1 : 'auto' }}
                          >
                            <div className="calendar-day-number">{i + 1}</div>
                            {reportesDia.length > 0 && (
                              <div className="calendar-day-reports">
                                {reportesDia.slice(0, 3).map(r => (
                                  <div
                                    key={r.id}
                                    className={`calendar-report-item status-${r.estado}`}
                                    onClick={() => handleVerDetalle(r)}
                                  >
                                    {r.codigo_seguimiento || r.id}
                                  </div>
                                ))}
                                {reportesDia.length > 3 && (
                                  <div className="calendar-more-reports">+{reportesDia.length - 3}</div>
                                )}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="table-wrapper-enterprise">
                    <table className="table-enterprise">
                      <thead>
                        <tr>
                          <th className="table-checkbox-col">
                            <input
                              ref={selectAllReportesRef}
                              type="checkbox"
                              className="table-checkbox"
                              checked={allVisibleSelected}
                              onChange={(e) => handleToggleSelectAllReportes(e.target.checked)}
                            />
                          </th>
                          <th
                            className="sortable"
                            onClick={() => handleOrdenarTabla('codigo_seguimiento')}
                          >
                            ID Caso
                            {ordenamientoTabla.campo === 'codigo_seguimiento' && (
                              <span>{ordenamientoTabla.direccion === 'asc' ? '↑' : '↓'}</span>
                            )}
                          </th>
                          <th
                            className="sortable"
                            onClick={() => handleOrdenarTabla('direccion')}
                          >
                            Ubicación / Sector
                            {ordenamientoTabla.campo === 'direccion' && (
                              <span>{ordenamientoTabla.direccion === 'asc' ? '↑' : '↓'}</span>
                            )}
                          </th>
                          <th>Prioridad</th>
                          <th
                            className="sortable"
                            onClick={() => handleOrdenarTabla('estado')}
                          >
                            Estado
                            {ordenamientoTabla.campo === 'estado' && (
                              <span>{ordenamientoTabla.direccion === 'asc' ? '↑' : '↓'}</span>
                            )}
                          </th>
                          <th>Asignado a</th>
                          <th
                            className="sortable"
                            onClick={() => handleOrdenarTabla('fecha_creacion')}
                          >
                            Fecha
                            {ordenamientoTabla.campo === 'fecha_creacion' && (
                              <span>{ordenamientoTabla.direccion === 'asc' ? '↑' : '↓'}</span>
                            )}
                          </th>
                          <th className="table-actions-col">Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {loading ? (
                          <tr>
                            <td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>
                              <Skeleton height="20px" width="100%" />
                            </td>
                          </tr>
                        ) : reportesFiltrados.length === 0 ? (
                          <tr>
                            <td colSpan="8" style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                              No hay reportes disponibles
                            </td>
                          </tr>
                        ) : (
                          reportesFiltrados.map((reporte) => (
                            <tr key={reporte.id || reporte.codigo_seguimiento} className="table-row-enterprise">
                              <td className="table-checkbox-col">
                                <input
                                  type="checkbox"
                                  className="table-checkbox"
                                  checked={selectedReporteIds.includes(reporte.id)}
                                  onChange={(e) => handleToggleReporte(reporte.id, e.target.checked)}
                                />
                              </td>
                              <td className="table-id-col">{reporte.codigo_seguimiento || reporte.id}</td>
                              <td>
                                <p className="table-location-main">{reporte.direccion || reporte.direccion_completa || 'Sin dirección'}</p>
                                <p className="table-location-sub">{reporte.categoria_nombre || 'Sin categoría'}</p>
                              </td>
                              <td>
                                <span className={`priority-badge priority-${reporte.prediction?.risk_level || 'medio'}`}>
                                  {reporte.prediction?.risk_level === 'alto' ? 'Alta' :
                                    reporte.prediction?.risk_level === 'medio' ? 'Media' :
                                      reporte.prediction?.risk_level === 'bajo' ? 'Baja' : 'Media'}
                                </span>
                              </td>
                              <td>
                                <div className="status-indicator">
                                  <div className={`status-dot status-${reporte.estado}`}></div>
                                  <span>{reporte.estado.charAt(0).toUpperCase() + reporte.estado.slice(1)}</span>
                                </div>
                              </td>
                              <td>
                                {reporte.asignado_a ? (
                                  (() => {
                                    const nombre = typeof reporte.asignado_a === 'object' ? reporte.asignado_a.username : reporte.asignado_a
                                    return (
                                      <div className="assigned-user">
                                        <div className="user-avatar-small">
                                          {nombre ? String(nombre).charAt(0).toUpperCase() : '?'}
                                        </div>
                                        <span>{nombre}</span>
                                      </div>
                                    )
                                  })()
                                ) : (
                                  <span className="not-assigned">Sin asignar</span>
                                )}
                              </td>
                              <td className="table-date-col">
                                {new Date(reporte.fecha_creacion).toLocaleDateString('es-CL', {
                                  day: 'numeric',
                                  month: 'short',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </td>
                              <td className="table-actions-col">
                                <button
                                  className="table-action-icon"
                                  onClick={(e) => {
                                    e.preventDefault()
                                    e.stopPropagation()
                                    handleVerDetalle(reporte)
                                  }}
                                  type="button"
                                >
                                  <MoreVerticalIconSVG size={16} />
                                </button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Pagination Footer */}
                {!vistaCalendario && (
                  <div className="table-pagination">
                    <span className="pagination-info">
                      Mostrando <span className="pagination-bold">{fromRegistro}-{toRegistro}</span> de <span className="pagination-bold">{totalReportes}</span> resultados
                    </span>
                    <div className="pagination-controls">
                      <button
                        className="pagination-btn"
                        disabled={currentPage <= 1}
                        onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                      >
                        Anterior
                      </button>
                      <span className="pagination-info">
                        Página <span className="pagination-bold">{currentPage}</span> de <span className="pagination-bold">{totalPaginas}</span>
                      </span>
                      <button
                        className="pagination-btn"
                        disabled={currentPage >= totalPaginas}
                        onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPaginas))}
                      >
                        Siguiente
                      </button>
                    </div>
                  </div>
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
                      <th>Riesgo</th>
                      <th>Estado</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <>
                        {[...Array(5)].map((_, i) => (
                          <tr key={i} className="skeleton-table-row">
                            <td><Skeleton height="16px" /></td>
                            <td><Skeleton height="16px" /></td>
                            <td><Skeleton height="16px" /></td>
                            <td><Skeleton height="16px" /></td>
                            <td><Skeleton height="16px" width="80px" /></td>
                            <td><Skeleton height="16px" width="100px" /></td>
                            <td><Skeleton height="24px" width="60px" /></td>
                          </tr>
                        ))}
                      </>
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
                          <td>{reporte.direccion || reporte.direccion_completa || 'Sin dirección'}</td>
                          <td>{reporte.categoria_nombre || 'Sin categoría'}</td>
                          <td>
                            {reporte.prediction ? (
                              <span className={`risk-badge risk-${reporte.prediction.risk_level}`}>
                                {(reporte.prediction.probability * 100).toFixed(0)}% ·{' '}
                                {reporte.prediction.risk_level.toUpperCase()}
                              </span>
                            ) : (
                              <span className="risk-badge risk-empty">Sin datos</span>
                            )}
                          </td>
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
                              <span>Ver</span>
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {/* Vista Estadísticas + Predicciones */}
            {vistaActual === 'estadisticas' && (
              <div className="prediction-panel">
                <div className="prediction-card prediction-card--auto">
                  <div className="prediction-card__header">
                    <div>
                      <h3>📊 KPI Ejecutivo (30 días)</h3>
                      <p>Indicadores para seguimiento de operación y cumplimiento.</p>
                    </div>
                    <button
                      className="btn-export-csv"
                      type="button"
                      onClick={fetchExecutiveStats}
                      style={{ width: 'auto', minWidth: '120px' }}
                    >
                      Actualizar
                    </button>
                  </div>
                  {loadingExecutiveStats ? (
                    <div className="prediction-placeholder">
                      <p>Cargando indicadores ejecutivos...</p>
                    </div>
                  ) : executiveStats ? (
                    <>
                      <div className="prediction-metrics">
                        <div className="metric-card">
                          <span>Total reportes</span>
                          <strong>{executiveStats.resumen?.total_reportes || 0}</strong>
                        </div>
                        <div className="metric-card">
                          <span>Tasa resolución</span>
                          <strong>{executiveStats.tasas?.resolucion_pct || 0}%</strong>
                        </div>
                        <div className="metric-card">
                          <span>Alta prioridad</span>
                          <strong>{executiveStats.tasas?.alta_prioridad_pct || 0}%</strong>
                        </div>
                        <div className="metric-card">
                          <span>Variación volumen</span>
                          <strong>{executiveStats.tendencia?.variacion_pct || 0}%</strong>
                        </div>
                      </div>
                      <div className="prediction-meta">
                        <p>
                          Promedio resolución: {executiveStats.eficiencia?.tiempo_promedio_resolucion_horas ?? 'N/D'} horas
                        </p>
                        <p>
                          Validación: {executiveStats.tasas?.validacion_pct || 0}% · Spam detectado: {executiveStats.tasas?.spam_pct || 0}%
                        </p>
                      </div>
                    </>
                  ) : (
                    <div className="prediction-placeholder">
                      <p>No se pudieron cargar los KPI ejecutivos.</p>
                    </div>
                  )}
                </div>

                <div className="prediction-card prediction-card--auto">
                  <div className="prediction-card__header">
                    <div>
                      <h3>🔎 Puntos críticos automáticos</h3>
                      <p>El modelo analiza todos los reportes y resalta los de mayor prioridad.</p>
                    </div>
                    <span className={`prediction-badge ${predictionsAvailable ? 'success' : 'warning'}`}>
                      {predictionsAvailable ? 'Modelo activo' : 'Sin datos predictivos'}
                    </span>
                  </div>

                  {predictionsAvailable ? (
                    <>
                      <div className="prediction-metrics">
                        <div className="metric-card risk-alto">
                          <span>Riesgo alto</span>
                          <strong>{predictionSummary.alto}</strong>
                        </div>
                        <div className="metric-card risk-medio">
                          <span>Riesgo medio</span>
                          <strong>{predictionSummary.medio}</strong>
                        </div>
                        <div className="metric-card risk-bajo">
                          <span>Riesgo bajo</span>
                          <strong>{predictionSummary.bajo}</strong>
                        </div>
                      </div>
                      <div className="prediction-meta">
                        <p>Top 5 reportes que conviene revisar primero:</p>
                      </div>
                      <ul className="prediction-list">
                        {highRiskReportes.length === 0 && (
                          <li className="prediction-list__item muted">
                            No hay reportes críticos en este momento. Revisa los de riesgo medio.
                          </li>
                        )}
                        {highRiskReportes.map((reporte) => (
                          <li key={reporte.id} className="prediction-list__item">
                            <div>
                              <strong>{reporte.codigo_seguimiento}</strong>
                              <p>
                                {reporte.categoria_nombre} ·{' '}
                                {(reporte.prediction.probability * 100).toFixed(0)}% de resolución ·{' '}
                                {reporte.prediction.estimated_resolution_days} días estimados
                              </p>
                            </div>
                            <span className={`risk-badge risk-${reporte.prediction.risk_level}`}>
                              {reporte.prediction.risk_level.toUpperCase()}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </>
                  ) : (
                    <div className="prediction-placeholder">
                      <p>Aún no hay predicciones calculadas automáticamente.</p>
                      <ul>
                        <li>Ejecuta `python manage.py train_prediction_model` para activar el modelo.</li>
                        <li>Asegúrate de tener reportes con coordenadas y categorías.</li>
                      </ul>
                    </div>
                  )}
                </div>

              </div>
            )}

            {/* Vista Exportación */}
            {/* Vista Cuadrillas Terreno */}
            {vistaActual === 'cuadrillas' && (
              userInfo?.tipo === 'admin' ? (
                <EmployeeManager
                  onEmployeeUpdated={() => {
                    // Recargar inspectores cuando se actualiza un empleado
                    const loadInspectores = async () => {
                      try {
                        const response = await apiClient.get(API_ROUTES.ADMIN_USUARIOS)
                        const usuariosList = response.data || []
                        const empleadosList = usuariosList.filter(u => u.tipo === 'inspector' || u.tipo === 'admin')
                        setInspectores(empleadosList.map(u => ({
                          id: u.id,
                          username: u.username,
                          email: u.email || '',
                          first_name: u.first_name || '',
                          last_name: u.last_name || '',
                          is_staff: u.is_staff || false
                        })))
                      } catch (error) {
                        console.error('Error al recargar inspectores:', error)
                      }
                    }
                    loadInspectores()
                  }}
                  userInfo={userInfo}
                />
              ) : (
                <div className="cuadrillas-section">
                  <div className="cuadrillas-header">
                    <div className="cuadrillas-header-left">
                      <h2 className="cuadrillas-title">Cuadrillas Terreno</h2>
                      <p className="cuadrillas-subtitle">Inspectores Municipales y Funcionarios</p>
                    </div>
                    <div className="cuadrillas-header-right">
                      <span className="cuadrillas-count">{inspectores.length} Inspector{inspectores.length !== 1 ? 'es' : ''}</span>
                    </div>
                  </div>

                  {loadingInspectores ? (
                    <div className="cuadrillas-loading">
                      <Skeleton height="200px" width="100%" />
                      <Skeleton height="200px" width="100%" />
                    </div>
                  ) : inspectores.length === 0 ? (
                    <div className="cuadrillas-empty">
                      <p>No hay inspectores registrados</p>
                    </div>
                  ) : (
                    <div className="cuadrillas-grid">
                      {inspectores.map((inspector) => {
                        const stats = estadisticasInspectores[inspector.id] || {
                          total_asignados: 0,
                          resueltos: 0,
                          en_proceso: 0,
                          nuevos: 0,
                          tiempo_promedio_resolucion: 0,
                          eficiencia: 0
                        }

                        const nombreCompleto = inspector.first_name && inspector.last_name
                          ? `${inspector.first_name} ${inspector.last_name}`
                          : inspector.username

                        return (
                          <div key={inspector.id} className="inspector-card">
                            <div className="inspector-card-header">
                              <div className="inspector-avatar-large">
                                {nombreCompleto.charAt(0).toUpperCase()}
                              </div>
                              <div className="inspector-info">
                                <h3 className="inspector-name">{nombreCompleto}</h3>
                                <p className="inspector-username">@{inspector.username}</p>
                                {inspector.email && (
                                  <p className="inspector-email">{inspector.email}</p>
                                )}
                                {inspector.is_staff && (
                                  <span className="inspector-badge">Administrador</span>
                                )}
                              </div>
                            </div>

                            <div className="inspector-stats">
                              <div className="inspector-stat-item">
                                <div className="stat-label">Total Asignados</div>
                                <div className="stat-value">{stats.total_asignados || 0}</div>
                              </div>
                              <div className="inspector-stat-item">
                                <div className="stat-label">Resueltos</div>
                                <div className="stat-value success">{stats.resueltos || 0}</div>
                              </div>
                              <div className="inspector-stat-item">
                                <div className="stat-label">En Proceso</div>
                                <div className="stat-value warning">{stats.en_proceso || 0}</div>
                              </div>
                              <div className="inspector-stat-item">
                                <div className="stat-label">Nuevos</div>
                                <div className="stat-value info">{stats.nuevos || 0}</div>
                              </div>
                            </div>

                            <div className="inspector-metrics">
                              <div className="inspector-metric">
                                <span className="metric-label">Eficiencia</span>
                                <div className="metric-bar">
                                  <div
                                    className="metric-bar-fill"
                                    style={{ width: `${Math.min(stats.eficiencia || 0, 100)}%` }}
                                  ></div>
                                </div>
                                <span className="metric-value">{stats.eficiencia || 0}%</span>
                              </div>
                              {stats.tiempo_promedio_resolucion > 0 && (
                                <div className="inspector-metric">
                                  <span className="metric-label">Tiempo Promedio</span>
                                  <span className="metric-value">{stats.tiempo_promedio_resolucion.toFixed(1)} días</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            )}

            {vistaActual === 'sla' && (
              <div className="sla-section">
                <SLADashboard />
              </div>
            )}

            {vistaActual === 'live' && (
              <div className="live-section" style={{ padding: '20px', height: '100%' }}>
                <LiveOperationsCenter initialReports={reportes} />
              </div>
            )}

            {vistaActual === 'planificacion' && (
              <div className="planning-section" style={{ padding: '20px' }}>
                <RouteOptimizer />
              </div>
            )}

            {vistaActual === 'inteligencia' && (
              <div className="inteligencia-section" style={{ padding: '20px' }}>
                <EcoInteligenciaTab />
              </div>
            )}

            {vistaActual === 'exportar' && (
              <div className="export-panel">
                <div className="export-card">
                  <h2>📥 Exportar Datos</h2>
                  <p className="export-info">
                    Exporta los reportes filtrados o estadísticas generales en diferentes formatos.
                    {reportes.length > 0 && (
                      <span className="export-count">
                        Total de reportes a exportar: <strong>{reportes.length}</strong>
                      </span>
                    )}
                  </p>
                  <div className="export-options">
                    <div className="export-option">
                      <div className="export-icon">📄</div>
                      <h3>Exportar a CSV</h3>
                      <p>Descarga los reportes filtrados en formato CSV</p>
                      <button className="btn-export-csv" onClick={handleExportCSV}>
                        Descargar CSV
                      </button>
                    </div>
                    <div className="export-option">
                      <div className="export-icon">📊</div>
                      <h3>Exportar Estadísticas (PDF)</h3>
                      <p>Genera un reporte estadístico completo en PDF</p>
                      <button className="btn-export-pdf" onClick={handleExportPDF}>
                        Descargar PDF
                      </button>
                    </div>
                    <div className="export-option">
                      <div className="export-icon">📈</div>
                      <h3>Exportar Estadísticas (Excel)</h3>
                      <p>Genera un reporte estadístico completo en Excel</p>
                      <button className="btn-export-excel" onClick={handleExportExcel}>
                        Descargar Excel
                      </button>
                    </div>
                    {localStorage.getItem('userType') === 'admin' && (
                      <div className="export-option" style={{ gridColumn: '1 / -1', background: '#f8fafc', border: '1px dashed #cbd5e1' }}>
                        <div className="export-icon">📩</div>
                        <h3>Reporte Gerencial Automatizado</h3>
                        <p>Genera y envía de inmediato el PDF gerencial semanal a todos los administradores (Asíncrono).</p>
                        <button
                          className="btn-export-pdf"
                          style={{ background: '#475569' }}
                          onClick={handleExportGerencial}
                        >
                          Generar y Enviar Ahora
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

          </div>
        </main>
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

            {/* Agregar visualización de imagen */}
            {reporteSeleccionado.foto ? (
              <div className="detail-group">
                <label>Fotografía</label>
                <div className="reporte-imagen-container">
                  {(() => {
                    let imagenUrl = reporteSeleccionado.foto;

                    // Si no es una URL completa, construirla
                    if (!imagenUrl.startsWith('http://') && !imagenUrl.startsWith('https://')) {
                      // Si empieza con /media/, usar directamente con API_URL
                      if (imagenUrl.startsWith('/media/')) {
                        imagenUrl = `${API_URL}${imagenUrl}`;
                      }
                      // Si es una ruta relativa como "reportes/image.jpg"
                      else if (!imagenUrl.startsWith('/')) {
                        imagenUrl = `${API_URL}/media/${imagenUrl}`;
                      }
                      // Si empieza con / pero no con /media/
                      else {
                        imagenUrl = `${API_URL}${imagenUrl}`;
                      }
                    }

                    console.log('URL de imagen construida:', imagenUrl);

                    return (
                      <div>
                        <img
                          src={imagenUrl}
                          alt={`Reporte ${reporteSeleccionado.codigo_seguimiento}`}
                          className="reporte-imagen"
                          onError={(e) => {
                            console.error('Error al cargar imagen:', e.target.src);
                            console.error('Reporte completo:', reporteSeleccionado);
                            e.target.style.display = 'none';
                            const errorMsg = document.getElementById(`error-${reporteSeleccionado.id}`);
                            if (errorMsg) {
                              errorMsg.style.display = 'block';
                            }
                          }}
                          onLoad={() => {
                            console.log('Imagen cargada exitosamente:', imagenUrl);
                            const errorMsg = document.getElementById(`error-${reporteSeleccionado.id}`);
                            if (errorMsg) {
                              errorMsg.style.display = 'none';
                            }
                          }}
                        />
                        <p
                          id={`error-${reporteSeleccionado.id}`}
                          className="imagen-error"
                          style={{
                            display: 'none',
                            color: '#d32f2f',
                            fontSize: '14px',
                            padding: '10px',
                            textAlign: 'center',
                            backgroundColor: '#ffebee',
                            borderRadius: '4px',
                            marginTop: '10px'
                          }}
                        >
                          ⚠️ No se pudo cargar la imagen.<br />
                          <small>URL: {imagenUrl}</small><br />
                          <small>Verifica que el archivo exista en el servidor.</small>
                        </p>
                      </div>
                    );
                  })()}
                </div>
              </div>
            ) : (
              <div className="detail-group">
                <label>Fotografía</label>
                <p style={{ color: '#999', fontStyle: 'italic' }}>No hay imagen disponible para este reporte</p>
              </div>
            )}

            <div className="form-group">
              <label>Cambiar Estado</label>
              <select value={modalEstado} onChange={(e) => setModalEstado(e.target.value)}>
                <option value="nuevo">Nuevo</option>
                <option value="proceso">En Proceso</option>
                <option value="resuelto">Resuelto</option>
                <option value="cerrado">Cerrado</option>
              </select>
            </div>

            <div className="form-group">
              <label>Notas Internas</label>
              <textarea
                placeholder="Agregar notas..."
                value={modalNotas}
                onChange={(e) => setModalNotas(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Evidencia de Cierre (obligatoria para Resuelto/Cerrado)</label>
              <textarea
                placeholder="Describe acciones ejecutadas, limpieza, validación en terreno, etc."
                value={modalEvidenciaCierre}
                onChange={(e) => setModalEvidenciaCierre(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Foto de Cierre (opcional)</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setModalFotoCierre(e.target.files?.[0] || null)}
              />
            </div>

            {/* Panel de Validación */}
            <div className="validation-section">
              <div className="section-header">
                <h3>Validación de Reporte</h3>
                <button
                  className="btn-toggle-validation"
                  onClick={() => setShowValidationPanel(!showValidationPanel)}
                >
                  {showValidationPanel ? 'Ocultar' : 'Mostrar'} Validación
                </button>
              </div>
              {showValidationPanel && (
                <ValidationPanel
                  reporteId={reporteSeleccionado.id}
                  onValidated={() => {
                    fetchReportes()
                    setShowValidationPanel(false)
                  }}
                />
              )}
            </div>

            <button className="btn-save" onClick={handleGuardarCambios}>
              Guardar Cambios
            </button>
          </div>
        </div>
      )}

      {/* Modal de Actualizar Ubicación */}
      {showLocationUpdater && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }} onClick={() => setShowLocationUpdater(false)}>
          <div onClick={(e) => e.stopPropagation()}>
            <LocationUpdater onClose={() => setShowLocationUpdater(false)} />
          </div>
        </div>
      )}
    </div>
  )
}

export default DashboardMunicipal
