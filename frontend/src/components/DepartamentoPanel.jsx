import { useState, useEffect, useCallback } from 'react'
import apiClient from '../services/api'
import { getDepartamentos, iaResumenDepartamento } from '../services/api'
import './DepartamentoPanel.css'

// ─── Helpers ──────────────────────────────────────────────────────────────────

const TABS = [
  { key: '', label: 'Todos' },
  { key: 'nuevo', label: 'Nuevos' },
  { key: 'proceso', label: 'En Proceso' },
  { key: 'resuelto', label: 'Resueltos' },
  { key: 'urgente', label: 'Urgentes' },
]

const PRIORIDAD_CONFIG = {
  urgente: { label: 'Urgente', cls: 'badge-urgente' },
  alta:    { label: 'Alta',    cls: 'badge-alta' },
  normal:  { label: 'Normal',  cls: 'badge-normal' },
  baja:    { label: 'Baja',    cls: 'badge-baja' },
}

const ESTADO_CONFIG = {
  nuevo:    { label: 'Nuevo',      cls: 'estado-nuevo' },
  proceso:  { label: 'En Proceso', cls: 'estado-proceso' },
  resuelto: { label: 'Resuelto',   cls: 'estado-resuelto' },
  cerrado:  { label: 'Cerrado',    cls: 'estado-cerrado' },
}

/**
 * Calcula las horas restantes de SLA y devuelve la clase de color.
 * Si sla_limite es nulo, devuelve null.
 */
function calcularSLA(reporte) {
  if (!reporte.sla_limite) return null
  const ahora = new Date()
  const limite = new Date(reporte.sla_limite)
  const diffMs = limite - ahora
  const horas = Math.round(diffMs / (1000 * 60 * 60))

  // Calcular porcentaje respecto al SLA total (si viene sla_horas del reporte)
  let cls = 'sla-verde'
  if (diffMs < 0) {
    cls = 'sla-rojo'
  } else if (reporte.sla_horas_total) {
    const porcentaje = (diffMs / (reporte.sla_horas_total * 3600 * 1000)) * 100
    cls = porcentaje > 50 ? 'sla-verde' : 'sla-amarillo'
  } else {
    cls = horas < 24 ? 'sla-amarillo' : 'sla-verde'
  }

  return { horas, cls, vencido: diffMs < 0 }
}

function formatFecha(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function ReporteSkeleton() {
  return (
    <div className="dp-reporte-card dp-skeleton-card" aria-hidden="true">
      <div className="dp-skeleton dp-skeleton-title" />
      <div className="dp-skeleton dp-skeleton-text" />
      <div className="dp-skeleton dp-skeleton-text dp-skeleton-short" />
      <div className="dp-skeleton dp-skeleton-badge" />
    </div>
  )
}

// ─── Tarjeta de reporte ───────────────────────────────────────────────────────

function ReporteCard({ reporte, onVerDetalle }) {
  const sla = calcularSLA(reporte)
  const prioridadCfg = PRIORIDAD_CONFIG[reporte.prioridad] || PRIORIDAD_CONFIG.normal
  const estadoCfg = ESTADO_CONFIG[reporte.estado] || { label: reporte.estado, cls: '' }

  return (
    <article className="dp-reporte-card">
      <div className="dp-reporte-card-header">
        <div className="dp-reporte-codigo-group">
          <span className="dp-reporte-codigo">{reporte.codigo_seguimiento || `#${reporte.id}`}</span>
          <span className={`dp-badge ${prioridadCfg.cls}`}>{prioridadCfg.label}</span>
        </div>
        <span className={`dp-estado-badge ${estadoCfg.cls}`}>{estadoCfg.label}</span>
      </div>

      <div className="dp-reporte-body">
        <h4 className="dp-reporte-subcategoria">
          {reporte.subcategoria_nombre || reporte.subcategoria?.nombre || '—'}
        </h4>
        {(reporte.capa_nombre || reporte.subcategoria?.capa?.nombre) && (
          <p className="dp-reporte-capa">
            <span className="dp-label">Tipo:</span>{' '}
            {reporte.capa_nombre || reporte.subcategoria?.capa?.nombre}
          </p>
        )}
        <p className="dp-reporte-direccion">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          {reporte.direccion || reporte.direccion_completa || 'Sin dirección'}
        </p>
        <p className="dp-reporte-fecha">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="4" width="18" height="18" rx="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          {formatFecha(reporte.fecha_creacion)}
        </p>
      </div>

      <div className="dp-reporte-card-footer">
        {sla ? (
          <span className={`dp-sla-badge ${sla.cls}`}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            {sla.vencido
              ? `Vencido hace ${Math.abs(sla.horas)}h`
              : `SLA: ${sla.horas}h restantes`}
          </span>
        ) : (
          <span className="dp-sla-badge dp-sla-sin">Sin SLA</span>
        )}

        <button
          className="dp-btn-detalle"
          onClick={() => onVerDetalle(reporte)}
          aria-label={`Ver detalle del reporte ${reporte.codigo_seguimiento || reporte.id}`}
        >
          Ver detalle
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
    </article>
  )
}

// ─── Stat mini ────────────────────────────────────────────────────────────────

function StatMini({ label, value, colorCls, loading }) {
  return (
    <div className={`dp-stat-mini ${colorCls}`}>
      {loading ? (
        <div className="dp-skeleton dp-skeleton-stat" />
      ) : (
        <span className="dp-stat-valor">{value ?? 0}</span>
      )}
      <span className="dp-stat-label">{label}</span>
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────────

const DepartamentoPanel = ({ departamentoId = null }) => {
  const [departamentos, setDepartamentos] = useState([])
  const [deptoActual, setDeptoActual] = useState(departamentoId)
  const [tabActual, setTabActual] = useState('')
  const [reportes, setReportes] = useState([])
  const [stats, setStats] = useState({
    activos: 0,
    urgentes: 0,
    vencidos: 0,
    resueltosHoy: 0,
  })
  const [loadingDepts, setLoadingDepts] = useState(true)
  const [loadingReportes, setLoadingReportes] = useState(false)
  const [error, setError] = useState(null)
  const [resumenIA, setResumenIA] = useState(null)
  const [cargandoResumen, setCargandoResumen] = useState(false)

  // ── Cargar lista de departamentos ──────────────────────────────────────────
  useEffect(() => {
    const cargarDepartamentos = async () => {
      setLoadingDepts(true)
      try {
        const res = await getDepartamentos()
        const data = Array.isArray(res.data) ? res.data : res.data?.results ?? []
        setDepartamentos(data)
        // Seleccionar el primero si no viene prop
        if (!departamentoId && data.length > 0) {
          setDeptoActual(data[0].id)
        }
      } catch (err) {
        console.error('Error al cargar departamentos:', err)
        setError('No se pudo cargar la lista de departamentos.')
      } finally {
        setLoadingDepts(false)
      }
    }
    cargarDepartamentos()
  }, [departamentoId])

  // ── Cargar reportes del departamento seleccionado ──────────────────────────
  const cargarReportes = useCallback(async () => {
    if (!deptoActual) return
    setLoadingReportes(true)
    setError(null)
    try {
      const params = {
        subcategoria__capa__departamento: deptoActual,
      }
      // El tab "urgentes" se mapea a prioridad, no a estado
      if (tabActual === 'urgente') {
        params.prioridad = 'urgente'
      } else if (tabActual) {
        params.estado = tabActual
      }

      const res = await apiClient.get('/api/reportes/', { params })
      const data = Array.isArray(res.data) ? res.data : res.data?.results ?? []
      setReportes(data)

      // Calcular estadísticas rápidas desde la respuesta
      const hoy = new Date()
      hoy.setHours(0, 0, 0, 0)

      const resueltosHoy = data.filter((r) => {
        if (r.estado !== 'resuelto') return false
        const fecha = new Date(r.fecha_actualizacion || r.fecha_creacion)
        fecha.setHours(0, 0, 0, 0)
        return fecha.getTime() === hoy.getTime()
      }).length

      const vencidos = data.filter((r) => {
        if (!r.sla_limite) return false
        return new Date(r.sla_limite) < new Date()
      }).length

      setStats({
        activos: data.filter((r) => r.estado !== 'resuelto' && r.estado !== 'cerrado').length,
        urgentes: data.filter((r) => r.prioridad === 'urgente').length,
        vencidos,
        resueltosHoy,
      })
    } catch (err) {
      console.error('Error al cargar reportes del departamento:', err)
      setError('Error al cargar los reportes. Verifica tu conexión e intenta de nuevo.')
    } finally {
      setLoadingReportes(false)
    }
  }, [deptoActual, tabActual])

  useEffect(() => {
    cargarReportes()
  }, [cargarReportes])

  // ── Nombre del departamento activo ─────────────────────────────────────────
  const nombreDepto = departamentos.find((d) => d.id === deptoActual)?.nombre ?? 'Departamento'

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleCambioDepto = (e) => {
    setDeptoActual(Number(e.target.value))
    setTabActual('')
  }

  const handleVerDetalle = (reporte) => {
    // Navegar o emitir evento; aquí abrimos una URL de detalle simple
    // El consumidor puede sobreescribir con su propio manejador via props si lo necesita
    window.location.href = `/dashboard?reporte=${reporte.id}`
  }

  const handleGenerarResumen = async () => {
    if (!deptoActual) return
    setCargandoResumen(true)
    setResumenIA(null)
    try {
      const res = await iaResumenDepartamento(deptoActual)
      setResumenIA(res.data)
    } catch (e) {
      console.error('Error resumen IA:', e)
    } finally {
      setCargandoResumen(false)
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <section className="dp-panel" aria-label="Panel de departamento municipal">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="dp-header">
        <div className="dp-header-top">
          <div className="dp-header-title-group">
            <div className="dp-header-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </div>
            <div>
              <h2 className="dp-header-nombre">
                {loadingDepts ? 'Cargando...' : nombreDepto}
              </h2>
              <p className="dp-header-sub">Reportes ciudadanos asignados</p>
            </div>
          </div>

          {/* Selector de departamento */}
          <div className="dp-depto-selector-wrap">
            <label htmlFor="dp-depto-select" className="dp-depto-label">
              Departamento:
            </label>
            {loadingDepts ? (
              <div className="dp-skeleton dp-skeleton-select" />
            ) : (
              <select
                id="dp-depto-select"
                className="dp-depto-select"
                value={deptoActual ?? ''}
                onChange={handleCambioDepto}
                disabled={departamentos.length === 0}
              >
                {departamentos.length === 0 && (
                  <option value="">Sin departamentos</option>
                )}
                {departamentos.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.nombre}
                  </option>
                ))}
              </select>
            )}
            <button
              className="btn-resumen-ia"
              onClick={handleGenerarResumen}
              disabled={cargandoResumen || !deptoActual}
              type="button"
            >
              {cargandoResumen ? '⏳ Generando...' : '🤖 Resumen IA del día'}
            </button>
          </div>
        </div>

        {/* Stats rápidos */}
        <div className="dp-stats-row">
          <StatMini label="Reportes activos"   value={stats.activos}       colorCls="dp-stat-azul"   loading={loadingReportes} />
          <StatMini label="Urgentes"           value={stats.urgentes}      colorCls="dp-stat-rojo"   loading={loadingReportes} />
          <StatMini label="SLA vencido"        value={stats.vencidos}      colorCls="dp-stat-naranja" loading={loadingReportes} />
          <StatMini label="Resueltos hoy"      value={stats.resueltosHoy}  colorCls="dp-stat-verde"  loading={loadingReportes} />
        </div>
      </header>

      {/* ── Resumen IA ──────────────────────────────────────────────────────── */}
      {resumenIA && (
        <div className="resumen-ia-card">
          <div className="resumen-ia-header">
            <span>🤖 Resumen ejecutivo generado por IA</span>
            <button className="resumen-ia-cerrar" onClick={() => setResumenIA(null)}>✕</button>
          </div>
          <p className="resumen-ia-texto">{resumenIA.resumen}</p>
          <div className="resumen-ia-stats">
            <span>📋 {resumenIA.stats?.total_activos} activos</span>
            <span>🔴 {resumenIA.stats?.urgentes} urgentes</span>
            <span>⏰ {resumenIA.stats?.sla_vencidos} SLA vencidos</span>
            <span>✅ {resumenIA.stats?.resueltos_7dias} resueltos (7 días)</span>
          </div>
        </div>
      )}

      {/* ── Tabs de filtro ──────────────────────────────────────────────────── */}
      <nav className="dp-tabs" role="tablist" aria-label="Filtrar reportes por estado">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={tabActual === tab.key}
            className={`dp-tab${tabActual === tab.key ? ' dp-tab-activo' : ''}`}
            onClick={() => setTabActual(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* ── Contenido principal ─────────────────────────────────────────────── */}
      <div className="dp-content">
        {/* Error */}
        {error && (
          <div className="dp-error" role="alert">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
            <button className="dp-btn-reintentar" onClick={cargarReportes}>
              Reintentar
            </button>
          </div>
        )}

        {/* Loading skeletons */}
        {loadingReportes && !error && (
          <div className="dp-grid">
            {Array.from({ length: 6 }).map((_, i) => (
              <ReporteSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Lista de reportes */}
        {!loadingReportes && !error && (
          <>
            {reportes.length === 0 ? (
              <div className="dp-vacio">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
                <p>No hay reportes para este filtro.</p>
              </div>
            ) : (
              <>
                <p className="dp-conteo">
                  {reportes.length} reporte{reportes.length !== 1 ? 's' : ''} encontrado{reportes.length !== 1 ? 's' : ''}
                </p>
                <div className="dp-grid" role="list">
                  {reportes.map((r) => (
                    <ReporteCard key={r.id} reporte={r} onVerDetalle={handleVerDetalle} />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </section>
  )
}

export default DepartamentoPanel
