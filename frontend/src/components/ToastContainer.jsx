import { useState, useCallback, useEffect } from 'react'
import Toast from './Toast'
import './Toast.css'

let toastId = 0
let toastListeners = []

export const toast = {
  success: (message, duration = 3000) => {
    const id = toastId++
    toastListeners.forEach(listener => listener({ id, message, type: 'success', duration }))
    return id
  },
  error: (message, duration = 4000) => {
    const id = toastId++
    toastListeners.forEach(listener => listener({ id, message, type: 'error', duration }))
    return id
  },
  warning: (message, duration = 3000) => {
    const id = toastId++
    toastListeners.forEach(listener => listener({ id, message, type: 'warning', duration }))
    return id
  },
  info: (message, duration = 3000) => {
    const id = toastId++
    toastListeners.forEach(listener => listener({ id, message, type: 'info', duration }))
    return id
  }
}

function ToastContainer() {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((toastData) => {
    setToasts(prev => [...prev, toastData])
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  useEffect(() => {
    toastListeners.push(addToast)
    return () => {
      toastListeners = toastListeners.filter(l => l !== addToast)
    }
  }, [addToast])

  return (
    <div className="toast-container" role="region" aria-live="polite" aria-atomic="true" aria-label="Notificaciones del sistema">
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  )
}

export default ToastContainer

