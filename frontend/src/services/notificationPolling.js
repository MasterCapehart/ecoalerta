/**
 * Servicio de polling inteligente para notificaciones
 * Se adapta según la actividad del usuario y el estado de la aplicación
 */
class NotificationPollingService {
  constructor() {
    this.intervalId = null
    this.baseInterval = 30000 // 30 segundos base
    this.activeInterval = 10000 // 10 segundos cuando está activo
    this.idleInterval = 60000 // 60 segundos cuando está inactivo
    this.currentInterval = this.baseInterval
    this.isActive = true
    this.lastActivity = Date.now()
    this.idleTimeout = 5 * 60 * 1000 // 5 minutos de inactividad
    this.errorCount = 0
    this.maxErrors = 3
    this.callbacks = []
    
    // Detectar actividad del usuario
    this.setupActivityDetection()
  }

  setupActivityDetection() {
    // Eventos que indican actividad del usuario
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
    
    const updateActivity = () => {
      this.lastActivity = Date.now()
      if (!this.isActive) {
        this.isActive = true
        this.adjustInterval()
      }
    }

    activityEvents.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true })
    })

    // Verificar inactividad periódicamente
    setInterval(() => {
      const timeSinceActivity = Date.now() - this.lastActivity
      if (timeSinceActivity > this.idleTimeout && this.isActive) {
        this.isActive = false
        this.adjustInterval()
      }
    }, 60000) // Verificar cada minuto
  }

  adjustInterval() {
    if (this.isActive) {
      this.currentInterval = this.activeInterval
    } else {
      this.currentInterval = this.idleInterval
    }
    
    // Reiniciar polling con nuevo intervalo si está corriendo
    if (this.intervalId) {
      this.stop()
      this.start()
    }
  }

  start(callback) {
    if (callback) {
      this.callbacks.push(callback)
    }

    if (this.intervalId) {
      return // Ya está corriendo
    }

    // Ejecutar inmediatamente la primera vez
    this.executeCallbacks()

    // Iniciar polling
    this.intervalId = setInterval(() => {
      this.executeCallbacks()
    }, this.currentInterval)
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
  }

  async executeCallbacks() {
    // Si hay muchos errores, aumentar el intervalo
    if (this.errorCount >= this.maxErrors) {
      this.currentInterval = Math.min(this.currentInterval * 2, 300000) // Máximo 5 minutos
      this.errorCount = 0
      if (this.intervalId) {
        this.stop()
        this.start()
      }
      return
    }

    try {
      // Ejecutar todos los callbacks
      await Promise.all(this.callbacks.map(cb => cb().catch(err => {
        console.error('Error en callback de polling:', err)
        this.errorCount++
      })))
      
      // Si fue exitoso, resetear contador de errores
      if (this.errorCount > 0) {
        this.errorCount = Math.max(0, this.errorCount - 1)
      }
    } catch (error) {
      console.error('Error en polling de notificaciones:', error)
      this.errorCount++
    }
  }

  reset() {
    this.errorCount = 0
    this.currentInterval = this.baseInterval
    if (this.intervalId) {
      this.stop()
      this.start()
    }
  }

  setInterval(interval) {
    this.baseInterval = interval
    this.currentInterval = interval
    if (this.intervalId) {
      this.stop()
      this.start()
    }
  }

  removeCallback(callback) {
    this.callbacks = this.callbacks.filter(cb => cb !== callback)
  }
}

// Instancia singleton
const notificationPollingService = new NotificationPollingService()

export default notificationPollingService
