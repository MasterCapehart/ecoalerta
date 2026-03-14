import { useEffect, useRef, useState } from 'react'
import * as Cesium from 'cesium'

// Importar estilos de Cesium
import 'cesium/Build/Cesium/Widgets/widgets.css'

// Configurar la ruta base de Cesium para assets estáticos
window.CESIUM_BASE_URL = '/node_modules/cesium/Build/Cesium/'

function MapView3D({ reportes, center, onMarkerClick }) {
  const cesiumContainer = useRef(null)
  const viewerRef = useRef(null)
  const entitiesRef = useRef([])
  const [locating, setLocating] = useState(false)

  useEffect(() => {
    if (!cesiumContainer.current) return

    // Intentar usar terreno real de ArcGIS (gratis y no requiere token)
    // Si falla, usar EllipsoidTerrainProvider
    let terrainProvider = new Cesium.EllipsoidTerrainProvider()
    
    try {
      // Usar ArcGIS World Elevation Service (terreno real gratuito)
      terrainProvider = new Cesium.ArcGisMapServerTerrainProvider({
        url: 'https://elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer'
      })
    } catch (e) {
      console.log('Usando terreno básico, ArcGIS no disponible')
      terrainProvider = new Cesium.EllipsoidTerrainProvider()
    }

    const viewer = new Cesium.Viewer(cesiumContainer.current, {
      terrainProvider: terrainProvider,
      baseLayerPicker: false,
      vrButton: false,
      geocoder: false,
      homeButton: true,
      infoBox: true,
      sceneModePicker: true,
      selectionIndicator: true,
      timeline: false,
      animation: false,
      navigationHelpButton: true,
      fullscreenButton: true,
    })

    // Mejorar controles de navegación - permitir movimiento más fluido
    viewer.scene.screenSpaceCameraController.enableRotate = true
    viewer.scene.screenSpaceCameraController.enableTranslate = true
    viewer.scene.screenSpaceCameraController.enableZoom = true
    viewer.scene.screenSpaceCameraController.enableTilt = true
    viewer.scene.screenSpaceCameraController.enableLook = true
    
    // Configurar velocidad de movimiento
    viewer.scene.screenSpaceCameraController.rotateEventTypes = [
      Cesium.CameraEventType.LEFT_DRAG,
      Cesium.CameraEventType.MIDDLE_DRAG,
      Cesium.CameraEventType.PINCH,
      {
        eventType: Cesium.CameraEventType.RIGHT_DRAG,
        modifier: Cesium.KeyboardEventModifier.CTRL
      }
    ]
    
    // Zoom con rueda del mouse más suave
    viewer.scene.screenSpaceCameraController.wheelZoomFactor = 1.5
    viewer.scene.screenSpaceCameraController.enableCollisionDetection = false

    // Habilitar sombras y iluminación para mayor realismo
    viewer.shadows = true
    viewer.shadowMap.enabled = true
    viewer.scene.globe.enableLighting = true

    // Configurar altura de cámara inicial
    viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(
        center[1], // lng
        center[0], // lat
        3000 // altura inicial en metros
      ),
      orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(-60), // Más inclinado para mejor perspectiva 3D
        roll: 0.0
      }
    })

    viewerRef.current = viewer

    return () => {
      if (viewerRef.current) {
        viewerRef.current.destroy()
      }
    }
  }, [center])

  // Actualizar marcadores cuando cambien los reportes
  useEffect(() => {
    if (!viewerRef.current) return

    // Eliminar entidades anteriores
    entitiesRef.current.forEach(entity => {
      viewerRef.current.entities.remove(entity)
    })
    entitiesRef.current = []

    // Agregar marcadores 3D para cada reporte
    const reportesConUbicacion = reportes.filter(reporte => reporte.lat && reporte.lng)
    
    reportesConUbicacion.forEach(reporte => {
      const color = getColorByEstado(reporte.estado)
      const size = getSizeByPrioridad(reporte.prediction?.risk_level)

      // Crear marcador tipo pin usando punto
      const entity = viewerRef.current.entities.add({
        position: Cesium.Cartesian3.fromDegrees(
          reporte.lng,
          reporte.lat,
          0
        ),
        point: {
          pixelSize: size,
          color: Cesium.Color.fromCssColorString(color),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 2,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        ellipse: {
          semiMajorAxis: 100,
          semiMinorAxis: 100,
          material: Cesium.Color.fromCssColorString(color).withAlpha(0.3),
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
        label: {
          text: reporte.codigo_seguimiento || `Reporte ${reporte.id}`,
          font: '14px sans-serif',
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -size - 25),
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        },
        description: `
          <div style="padding: 0; color: #333; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; max-width: 400px;">
            <!-- Header con código de seguimiento -->
            <div style="background: linear-gradient(135deg, #228B22 0%, #32CD32 100%); color: white; padding: 16px; border-radius: 8px 8px 0 0;">
              <h2 style="margin: 0; font-size: 18px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                📋 ${reporte.codigo_seguimiento || `Reporte ${reporte.id}`}
              </h2>
            </div>
            
            <!-- Contenido principal -->
            <div style="padding: 16px; background: #f8fafc; border-left: 4px solid ${color};">
              <!-- Estado con badge -->
              <div style="margin-bottom: 12px;">
                <span style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Estado</span>
                <div style="margin-top: 4px;">
                  <span style="display: inline-block; padding: 4px 12px; background: ${getEstadoBadgeColor(reporte.estado)}; color: ${getEstadoTextColor(reporte.estado)}; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: capitalize;">
                    ${reporte.estado || 'N/A'}
                  </span>
                </div>
              </div>

              <!-- Categoría -->
              <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e2e8f0;">
                <span style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Categoría</span>
                <p style="margin: 4px 0 0 0; font-size: 14px; color: #0f172a; font-weight: 500;">
                  ${reporte.categoria_nombre || 'Sin categoría'}
                </p>
              </div>

              <!-- Dirección -->
              <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e2e8f0;">
                <span style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">📍 Ubicación</span>
                <p style="margin: 4px 0 0 0; font-size: 13px; color: #475569; line-height: 1.5;">
                  ${reporte.direccion || reporte.direccion_completa || 'Sin dirección especificada'}
                </p>
              </div>

              <!-- Fecha de creación -->
              ${reporte.fecha_creacion ? `
                <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e2e8f0;">
                  <span style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">📅 Fecha</span>
                  <p style="margin: 4px 0 0 0; font-size: 13px; color: #475569;">
                    ${new Date(reporte.fecha_creacion).toLocaleDateString('es-CL', { 
                      day: 'numeric', 
                      month: 'long', 
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              ` : ''}

              <!-- Predicción de Riesgo -->
              ${reporte.prediction ? `
                <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e2e8f0;">
                  <span style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">⚠️ Nivel de Riesgo</span>
                  <div style="margin-top: 6px; display: flex; align-items: center; gap: 8px;">
                    <span style="display: inline-block; padding: 4px 12px; background: ${getRiskBadgeColor(reporte.prediction.risk_level)}; color: white; border-radius: 12px; font-size: 12px; font-weight: 700; text-transform: uppercase;">
                      ${reporte.prediction.risk_level || 'MEDIO'}
                    </span>
                    <span style="font-size: 13px; color: #64748b; font-weight: 500;">
                      ${(reporte.prediction.probability * 100).toFixed(0)}% probabilidad
                    </span>
                  </div>
                </div>
              ` : ''}

              <!-- Descripción si existe -->
              ${reporte.descripcion ? `
                <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e2e8f0;">
                  <span style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">📝 Descripción</span>
                  <p style="margin: 4px 0 0 0; font-size: 13px; color: #475569; line-height: 1.5;">
                    ${reporte.descripcion}
                  </p>
                </div>
              ` : ''}
            </div>

            <!-- Botón de acción -->
            <div style="padding: 12px 16px; background: white; border-radius: 0 0 8px 8px; border-top: 1px solid #e2e8f0;">
              <button onclick="window.viewer3DMarkerClick && window.viewer3DMarkerClick('${reporte.id || reporte.codigo_seguimiento}')" 
                      style="width: 100%; padding: 10px 16px; background: #228B22; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s;"
                      onmouseover="this.style.background='#1d7a1d'"
                      onmouseout="this.style.background='#228B22'">
                🔍 Ver Detalles Completos
              </button>
            </div>
          </div>
        `
      })

      entity.reporteData = reporte
      entitiesRef.current.push(entity)
    })

    // Configurar handler global para clicks desde la descripción
    window.viewer3DMarkerClick = (id) => {
      const reporte = reportes.find(r => (r.id === id || r.codigo_seguimiento === id))
      if (reporte && onMarkerClick) {
        onMarkerClick(reporte)
      }
    }

    // Volar a todos los marcadores si hay reportes
    if (entitiesRef.current.length > 0) {
      viewerRef.current.zoomTo(viewerRef.current.entities)
    }
  }, [reportes, onMarkerClick])

  // Función para ir a mi ubicación
  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      alert('Tu navegador no soporta geolocalización')
      return
    }

    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords
        
        if (viewerRef.current) {
          viewerRef.current.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, 2000),
            orientation: {
              heading: Cesium.Math.toRadians(0),
              pitch: Cesium.Math.toRadians(-60),
              roll: 0.0
            },
            duration: 2.0
          })
        }
        setLocating(false)
      },
      (error) => {
        console.error('Error de geolocalización:', error)
        alert('No se pudo obtener tu ubicación. Verifica que tengas activada la geolocalización en tu navegador.')
        setLocating(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 0
      }
    )
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div 
        ref={cesiumContainer} 
        className="cesium-viewer-container"
        style={{ 
          width: '100%', 
          height: '100%', 
          minHeight: '600px',
          position: 'relative',
          overflow: 'hidden'
        }} 
      />
      {/* Botón "Ir a mi ubicación" */}
      <button
        onClick={handleLocateMe}
        disabled={locating}
        style={{
          position: 'absolute',
          bottom: '20px',
          right: '20px',
          zIndex: 1000,
          padding: '12px 20px',
          background: locating ? '#94a3b8' : '#228B22',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: locating ? 'not-allowed' : 'pointer',
          fontSize: '14px',
          fontWeight: 600,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          transition: 'all 0.2s'
        }}
        onMouseEnter={(e) => {
          if (!locating) {
            e.target.style.background = '#1d7a1d'
            e.target.style.transform = 'translateY(-2px)'
          }
        }}
        onMouseLeave={(e) => {
          if (!locating) {
            e.target.style.background = '#228B22'
            e.target.style.transform = 'translateY(0)'
          }
        }}
      >
        <span>📍</span>
        <span>{locating ? 'Buscando...' : 'Ir a mi ubicación'}</span>
      </button>
    </div>
  )
}

// Helper para colores según estado
function getColorByEstado(estado) {
  const colors = {
    'nuevo': '#22c55e',
    'proceso': '#f59e0b',
    'resuelto': '#64748b',
  }
  return colors[estado] || '#3b82f6'
}

// Helper para color de badge según estado
function getEstadoBadgeColor(estado) {
  const colors = {
    'nuevo': '#dcfce7',
    'proceso': '#fef3c7',
    'resuelto': '#f1f5f9',
  }
  return colors[estado] || '#dbeafe'
}

// Helper para color de texto según estado
function getEstadoTextColor(estado) {
  const colors = {
    'nuevo': '#166534',
    'proceso': '#92400e',
    'resuelto': '#475569',
  }
  return colors[estado] || '#1e40af'
}

// Helper para color de badge de riesgo
function getRiskBadgeColor(riskLevel) {
  const colors = {
    'alto': '#ef4444',
    'medio': '#f59e0b',
    'bajo': '#22c55e',
  }
  return colors[riskLevel] || '#6b7280'
}

// Helper para tamaño de marcador según prioridad
function getSizeByPrioridad(riskLevel) {
  const sizes = {
    'alto': 16,
    'medio': 12,
    'bajo': 8,
  }
  return sizes[riskLevel] || 10
}

export default MapView3D
