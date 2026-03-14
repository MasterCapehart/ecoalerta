import { useState, useEffect, useRef } from 'react'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import notificationPollingService from '../services/notificationPolling'
import './NotificationsPanel.css'

function NotificationsPanel({ onClose }) {
  const [notificaciones, setNotificaciones] = useState([])
  const [noLeidas, setNoLeidas] = useState(0)
  const [loading, setLoading] = useState(true)
  const pollingCallbackRef = useRef(null)

  const loadNotificaciones = async () => {
    try {
      const response = await apiClient.get(API_ROUTES.NOTIFICACIONES)
      const nuevasNotificaciones = response.data.notificaciones || []
      const nuevasNoLeidas = response.data.no_leidas || 0
      
      // Detectar nuevas notificaciones
      const prevNoLeidas = noLeidas
      if (nuevasNoLeidas > prevNoLeidas) {
        const nuevas = nuevasNotificaciones.filter(n => !n.leido).length
        if (nuevas > 0) {
          // No mostrar toast si el panel está abierto (ya se ve)
          if (!document.querySelector('.notifications-panel')) {
            toast.info(`Tienes ${nuevas} nueva(s) notificación(es)`)
          }
        }
      }
      
      setNotificaciones(nuevasNotificaciones)
      setNoLeidas(nuevasNoLeidas)
      return true
    } catch (error) {
      // No mostrar error en cada polling, solo loguear
      if (error.response?.status !== 429) {
        console.error('Error al cargar notificaciones:', error)
      }
      return false
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Cargar inicialmente
    loadNotificaciones()
    
    // Configurar polling inteligente
    pollingCallbackRef.current = loadNotificaciones
    notificationPollingService.start(pollingCallbackRef.current)
    
    // Limpiar al desmontar
    return () => {
      if (pollingCallbackRef.current) {
        notificationPollingService.removeCallback(pollingCallbackRef.current)
      }
    }
  }, [])

  const marcarLeida = async (id) => {
    try {
      await apiClient.patch(`${API_ROUTES.MARCAR_NOTIFICACION_LEIDA}${id}/marcar-leida/`)
      setNotificaciones(prev => prev.map(n => 
        n.id === id ? { ...n, leido: true } : n
      ))
      setNoLeidas(prev => Math.max(0, prev - 1))
    } catch (error) {
      console.error('Error al marcar como leída:', error)
      toast.error('Error al actualizar notificación')
    }
  }

  const marcarTodasLeidas = async () => {
    try {
      const noLeidasList = notificaciones.filter(n => !n.leido)
      await Promise.all(
        noLeidasList.map(n => 
          apiClient.patch(`${API_ROUTES.MARCAR_NOTIFICACION_LEIDA}${n.id}/marcar-leida/`)
        )
      )
      setNotificaciones(prev => prev.map(n => ({ ...n, leido: true })))
      setNoLeidas(0)
      toast.success('Todas las notificaciones marcadas como leídas')
    } catch (error) {
      console.error('Error al marcar todas como leídas:', error)
      toast.error('Error al actualizar notificaciones')
    }
  }

  if (loading) {
    return (
      <div className="notifications-panel">
        <div className="notifications-header">
          <h3>Notificaciones</h3>
          <button onClick={onClose} className="close-btn">×</button>
        </div>
        <div className="notifications-loading">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="notifications-panel" role="dialog" aria-labelledby="notifications-title" aria-modal="true">
      <div className="notifications-header">
        <h3 id="notifications-title">
          Notificaciones {noLeidas > 0 && <span className="badge" aria-label={`${noLeidas} no leídas`}>{noLeidas}</span>}
        </h3>
        <div className="header-actions">
          {noLeidas > 0 && (
            <button 
              onClick={marcarTodasLeidas} 
              className="btn-mark-all"
              aria-label="Marcar todas las notificaciones como leídas"
            >
              Marcar todas como leídas
            </button>
          )}
          <button 
            onClick={onClose} 
            className="close-btn"
            aria-label="Cerrar panel de notificaciones"
          >
            ×
          </button>
        </div>
      </div>
      <div className="notifications-list" role="list" aria-label="Lista de notificaciones">
        {notificaciones.length === 0 ? (
          <div className="no-notifications" role="status" aria-live="polite">
            <p>No hay notificaciones</p>
          </div>
        ) : (
          notificaciones.map(notif => (
            <div
              key={notif.id}
              role="listitem"
              className={`notification-item ${notif.leido ? 'leida' : 'no-leida'}`}
              onClick={() => !notif.leido && marcarLeida(notif.id)}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ') && !notif.leido) {
                  e.preventDefault()
                  marcarLeida(notif.id)
                }
              }}
              tabIndex={!notif.leido ? 0 : -1}
              aria-label={`${notif.leido ? 'Leída' : 'No leída'}: ${notif.titulo}`}
            >
              <div className="notification-content">
                <h4>{notif.titulo}</h4>
                <p>{notif.mensaje}</p>
                {notif.reporte_codigo && (
                  <span className="reporte-code">Código: {notif.reporte_codigo}</span>
                )}
                <span className="notification-date">
                  {new Date(notif.fecha_creacion).toLocaleString('es-ES')}
                </span>
              </div>
              {!notif.leido && <div className="unread-indicator"></div>}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default NotificationsPanel
