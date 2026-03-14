import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './LocationUpdater.css'

// Fix iconos Leaflet
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

function LocationUpdater({ onClose }) {
  const [ubicacion, setUbicacion] = useState(null)
  const [loading, setLoading] = useState(false)
  const [mapInstance, setMapInstance] = useState(null)

  useEffect(() => {
    // Intentar obtener ubicación actual del usuario
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const latlng = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          }
          setUbicacion(latlng)
          if (mapInstance) {
            mapInstance.flyTo([latlng.lat, latlng.lng], 15)
          }
        },
        () => {
          // Si falla, usar ubicación por defecto (Santiago, Chile)
          const defaultLoc = { lat: -33.4489, lng: -70.6693 }
          setUbicacion(defaultLoc)
        }
      )
    } else {
      // Fallback a ubicación por defecto
      setUbicacion({ lat: -33.4489, lng: -70.6693 })
    }
  }, [mapInstance])

  const handleLocationSelect = (latlng) => {
    setUbicacion(latlng)
  }

  const handleActualizar = async () => {
    if (!ubicacion) {
      toast.error('Por favor selecciona una ubicación en el mapa')
      return
    }

    setLoading(true)
    try {
      await apiClient.post(API_ROUTES.ACTUALIZAR_UBICACION, {
        lat: ubicacion.lat,
        lng: ubicacion.lng
      })
      toast.success('Ubicación actualizada exitosamente')
      if (onClose) {
        onClose()
      }
    } catch (error) {
      console.error('Error al actualizar ubicación:', error)
      toast.error(error.response?.data?.error || 'Error al actualizar ubicación')
    } finally {
      setLoading(false)
    }
  }

  const handleLocalizar = () => {
    if (!navigator.geolocation) {
      toast.error('Tu navegador no soporta geolocalización')
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latlng = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        }
        setUbicacion(latlng)
        if (mapInstance) {
          mapInstance.flyTo([latlng.lat, latlng.lng], 16)
        }
        toast.success('Ubicación detectada')
      },
      (error) => {
        console.error('Error de geolocalización:', error)
        toast.error('No se pudo obtener tu ubicación')
      },
      {
        enableHighAccuracy: true,
        timeout: 8000
      }
    )
  }

  return (
    <div className="location-updater">
      <div className="location-updater-header">
        <h3>Actualizar Mi Ubicación</h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      <div className="location-updater-content">
        <p className="location-help">
          Haz clic en el mapa para seleccionar tu ubicación actual. Esto ayudará a optimizar
          la asignación de reportes y rutas.
        </p>

        <div className="location-map-container">
          <MapContainer
            center={ubicacion || [-33.4489, -70.6693]}
            zoom={13}
            style={{ height: '400px', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />
            {ubicacion && (
              <Marker position={[ubicacion.lat, ubicacion.lng]} />
            )}
            <MapClickHandler
              onLocationSelect={handleLocationSelect}
              onMapReady={setMapInstance}
            />
          </MapContainer>
        </div>

        {ubicacion && (
          <div className="location-info">
            <p>
              <strong>Coordenadas:</strong> {ubicacion.lat.toFixed(6)}, {ubicacion.lng.toFixed(6)}
            </p>
          </div>
        )}

        <div className="location-actions">
          <button className="btn-locate" onClick={handleLocalizar}>
            📍 Usar Mi Ubicación
          </button>
          <button
            className="btn-update"
            onClick={handleActualizar}
            disabled={!ubicacion || loading}
          >
            {loading ? 'Actualizando...' : 'Actualizar Ubicación'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default LocationUpdater
