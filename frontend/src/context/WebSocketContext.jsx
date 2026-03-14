import { createContext, useContext, useEffect, useState, useRef } from 'react'
import { API_URL } from '../config'
import { toast } from '../components/ToastContainer'

const WebSocketContext = createContext(null)

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const reconnectTimeoutRef = useRef(null)
  const socketRef = useRef(null)

  const hasActiveSession = () => Boolean(localStorage.getItem('access_token'))

  useEffect(() => {
    if (!hasActiveSession()) {
      setIsConnected(false)
      setSocket(null)
      return undefined
    }

    connect()

    return () => {
      if (socketRef.current) {
        socketRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  /* eslint-disable react-hooks/exhaustive-deps */
  const connect = () => {
    // Convert http/https to ws/wss
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // If running locally with different ports, hardcode port 8000
    // Usar import.meta.env.MODE para Vite en lugar de process.env.NODE_ENV
    const wsUrl = import.meta.env.MODE === 'development'
      ? 'ws://localhost:8000/ws/reportes/'
      : `${wsProtocol}//${window.location.host}/ws/reportes/`

    console.log('Connecting to WebSocket:', wsUrl)

    const ws = new WebSocket(wsUrl)
    socketRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket Connected')
      setIsConnected(true)
      setSocket(ws)
    }

    ws.onclose = () => {
      console.log('WebSocket Disconnected')
      setIsConnected(false)
      setSocket(null)
      // Reintentar solo si sigue habiendo sesión activa
      if (hasActiveSession()) {
        reconnectTimeoutRef.current = setTimeout(connect, 3000)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error)
      ws.close()
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      console.log('WebSocket Message:', message)
      setLastMessage(message)

      // Nunca mostrar toasts globales si no hay sesión
      if (!hasActiveSession()) {
        return
      }

      if (message.type === 'reporte_creado') {
        const reporte = message.data
        const isCritical = reporte.prioridad === 'alta' || reporte.prediction?.risk_level === 'alto'

        if (isCritical) {
          toast.error(`⚠️ NUEVO REPORTE CRÍTICO: ${reporte.categoria_nombre || 'Sin categoría'}`)
        } else {
          toast.info(`Nuevo reporte recibido: ${reporte.categoria_nombre || 'Sin categoría'}`)
        }
      } else if (message.type === 'reporte_actualizado') {
        // Opcional: notificar actualizaciones
        // toast.info(`Reporte ${message.data.codigo_seguimiento} actualizado`)
      }
    }
  }
  /* eslint-enable react-hooks/exhaustive-deps */

  return (
    <WebSocketContext.Provider value={{ socket, isConnected, lastMessage }}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}
