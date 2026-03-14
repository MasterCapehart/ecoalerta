import { openDB } from 'idb'
import { toast } from '../components/ToastContainer'
import apiClient from './api'

const DB_NAME = 'ecoalerta-offline-db'
const STORE_REPORTS = 'offline-reports'
const STORE_ACTIONS = 'offline-actions'

class OfflineService {
    async getDb() {
        return openDB(DB_NAME, 1, {
            upgrade(db) {
                if (!db.objectStoreNames.contains(STORE_REPORTS)) {
                    db.createObjectStore(STORE_REPORTS, { keyPath: 'id', autoIncrement: true })
                }
                if (!db.objectStoreNames.contains(STORE_ACTIONS)) {
                    db.createObjectStore(STORE_ACTIONS, { keyPath: 'id', autoIncrement: true })
                }
            },
        })
    }

    async saveReport(reportData) {
        const db = await this.getDb()
        await db.add(STORE_REPORTS, {
            ...reportData,
            createdAt: new Date().toISOString(),
            retryCount: 0
        })
        this.notifyPendingCountChange()
        toast.info('Sin conexión. Reporte guardado localmente.')
    }

    async getPendingReports() {
        const db = await this.getDb()
        return db.getAll(STORE_REPORTS)
    }

    async deleteReport(id, storeName = STORE_REPORTS) {
        const db = await this.getDb()
        await db.delete(storeName, id)
        this.notifyPendingCountChange()
    }

    async queueInspectorAction(actionData) {
        const db = await this.getDb()
        await db.add(STORE_ACTIONS, {
            ...actionData,
            createdAt: new Date().toISOString(),
            retryCount: 0
        })
        this.notifyPendingCountChange()
        toast.info('Sin conexión. Acción de inspector en cola para sincronizar.')
    }

    async getPendingActions() {
        const db = await this.getDb()
        return db.getAll(STORE_ACTIONS)
    }

    async getPendingCount() {
        const [reports, actions] = await Promise.all([
            this.getPendingReports(),
            this.getPendingActions()
        ])
        return reports.length + actions.length
    }

    async notifyPendingCountChange() {
        const pendingCount = await this.getPendingCount()
        window.dispatchEvent(new CustomEvent('offlinePendingChanged', {
            detail: { pendingCount }
        }))
    }

    async syncPendingReports() {
        if (!navigator.onLine) return

        const reports = await this.getPendingReports()
        const actions = await this.getPendingActions()
        if (reports.length === 0 && actions.length === 0) {
            this.notifyPendingCountChange()
            return
        }

        if (reports.length > 0) {
            toast.info(`Sincronizando ${reports.length} reportes pendientes...`)
        }

        let syncedCount = 0

        for (const report of reports) {
            try {
                // Eliminar campos locales antes de enviar
                const { id, ...payload } = report

                // Reconstruir FormData si había imagen (esto es complejo en IndexedDB, 
                // asumimos por ahora que payload es JSON o Blob serializado)
                // Para simplificar, si es compleja, se envía como JSON

                await apiClient.post('/api/reportes/', payload)

                await this.deleteReport(id)
                syncedCount++
            } catch (error) {
                console.error('Error syncing report:', error)
                // Opcional: incrementar retryCount
            }
        }

        if (syncedCount > 0) {
            toast.success(`${syncedCount} reportes sincronizados exitosamente.`)
        }

        await this.syncPendingActions()
    }

    async syncPendingActions() {
        if (!navigator.onLine) return

        const actions = await this.getPendingActions()
        if (actions.length === 0) {
            this.notifyPendingCountChange()
            return
        }

        toast.info(`Sincronizando ${actions.length} acciones pendientes...`)

        let syncedActions = 0

        for (const action of actions) {
            try {
                const { id, method, url, payload } = action
                await apiClient.request({
                    method: method || 'patch',
                    url,
                    data: payload
                })
                await this.deleteReport(id, STORE_ACTIONS)
                syncedActions++
            } catch (error) {
                console.error('Error syncing offline action:', error)
            }
        }

        if (syncedActions > 0) {
            toast.success(`${syncedActions} acciones de inspector sincronizadas.`)
        }
    }

    // Iniciar listener de conexión
    init() {
        window.addEventListener('online', () => {
            toast.success('Conexión recuperada. Iniciando sincronización...')
            this.syncPendingReports()
        })

        window.addEventListener('offline', () => {
            toast.warning('Modo Offline. Los reportes se guardarán localmente.')
        })

        this.notifyPendingCountChange()
    }
}

export default new OfflineService()
