import { useState } from 'react'
import './Estadisticas.css'

function Estadisticas() {
  const [periodo, setPeriodo] = useState('mes')

  // Datos de ejemplo para gráficos
  const datosReportes = [
    { mes: 'Ene', nuevos: 15, proceso: 8, resueltos: 22 },
    { mes: 'Feb', nuevos: 18, proceso: 12, resueltos: 25 },
    { mes: 'Mar', nuevos: 12, proceso: 6, resueltos: 30 },
    { mes: 'Abr', nuevos: 20, proceso: 10, resueltos: 28 },
  ]

  const datosCategorias = [
    { nombre: 'Domésticos', cantidad: 45, porcentaje: 35 },
    { nombre: 'Escombros', cantidad: 38, porcentaje: 29 },
    { nombre: 'Orgánicos', cantidad: 25, porcentaje: 19 },
    { nombre: 'Electrónicos', cantidad: 15, porcentaje: 12 },
    { nombre: 'Peligrosos', cantidad: 7, porcentaje: 5 },
  ]

  const kpisRendimiento = {
    tiempoPromedioResolucion: '3.2 días',
    tasaResolucion: '85%',
    reportesRecurrentes: 12,
    zonasRiesgo: 5
  }

  return (
    <div className="estadisticas-container">
      <div className="estadisticas-header">
        <h2>📊 Estadísticas y Análisis</h2>
        <div className="periodo-selector">
          <button 
            className={periodo === 'semana' ? 'active' : ''}
            onClick={() => setPeriodo('semana')}
          >
            Semana
          </button>
          <button 
            className={periodo === 'mes' ? 'active' : ''}
            onClick={() => setPeriodo('mes')}
          >
            Mes
          </button>
          <button 
            className={periodo === 'año' ? 'active' : ''}
            onClick={() => setPeriodo('año')}
          >
            Año
          </button>
        </div>
      </div>

      {/* KPIs de Rendimiento */}
      <div className="kpis-section">
        <h3>Indicadores de Rendimiento</h3>
        <div className="kpis-grid">
          <div className="kpi-card">
            <div className="kpi-icon">⏱️</div>
            <div className="kpi-content">
              <div className="kpi-value">{kpisRendimiento.tiempoPromedioResolucion}</div>
              <div className="kpi-label">Tiempo Promedio de Resolución</div>
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-icon">✅</div>
            <div className="kpi-content">
              <div className="kpi-value">{kpisRendimiento.tasaResolucion}</div>
              <div className="kpi-label">Tasa de Resolución</div>
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-icon">🔄</div>
            <div className="kpi-content">
              <div className="kpi-value">{kpisRendimiento.reportesRecurrentes}</div>
              <div className="kpi-label">Reportes Recurrentes</div>
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-icon">⚠️</div>
            <div className="kpi-content">
              <div className="kpi-value">{kpisRendimiento.zonasRiesgo}</div>
              <div className="kpi-label">Zonas de Alto Riesgo</div>
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico de Tendencias */}
      <div className="chart-section">
        <h3>Tendencia de Reportes por Estado</h3>
        <div className="chart-container">
          <div className="chart-bars">
            {datosReportes.map((dato, index) => (
              <div key={index} className="bar-group">
                <div className="bars">
                  <div 
                    className="bar bar-nuevos" 
                    style={{ height: `${dato.nuevos * 5}px` }}
                    data-value={`Nuevos: ${dato.nuevos}`}
                    title={`Nuevos: ${dato.nuevos}`}
                  ></div>
                  <div 
                    className="bar bar-proceso" 
                    style={{ height: `${dato.proceso * 5}px` }}
                    data-value={`En Proceso: ${dato.proceso}`}
                    title={`En Proceso: ${dato.proceso}`}
                  ></div>
                  <div 
                    className="bar bar-resueltos" 
                    style={{ height: `${dato.resueltos * 5}px` }}
                    data-value={`Resueltos: ${dato.resueltos}`}
                    title={`Resueltos: ${dato.resueltos}`}
                  ></div>
                </div>
                <div className="bar-label">{dato.mes}</div>
              </div>
            ))}
          </div>
          <div className="chart-legend">
            <div className="legend-item">
              <span className="legend-color nuevos"></span>
              <span>Nuevos</span>
            </div>
            <div className="legend-item">
              <span className="legend-color proceso"></span>
              <span>En Proceso</span>
            </div>
            <div className="legend-item">
              <span className="legend-color resueltos"></span>
              <span>Resueltos</span>
            </div>
          </div>
        </div>
      </div>

      {/* Distribución por Categoría */}
      <div className="chart-section">
        <h3>Distribución por Tipo de Residuo</h3>
        <div className="category-chart">
          {datosCategorias.map((cat, index) => (
            <div key={index} className="category-row">
              <div className="category-label">{cat.nombre}</div>
              <div className="category-bar-container">
                <div 
                  className="category-bar"
                  style={{ width: `${cat.porcentaje}%` }}
                >
                  <span className="category-value">{cat.cantidad}</span>
                </div>
              </div>
              <div className="category-percentage">{cat.porcentaje}%</div>
            </div>
          ))}
        </div>
      </div>

      {/* Mapa de Calor Semanal */}
      <div className="chart-section">
        <h3>Actividad por Día de la Semana</h3>
        <div className="heatmap-container">
          <div className="heatmap-row">
            <div className="heatmap-label">Lunes</div>
            <div className="heatmap-cell" data-intensity="low">8</div>
            <div className="heatmap-cell" data-intensity="medium">12</div>
            <div className="heatmap-cell" data-intensity="high">18</div>
            <div className="heatmap-cell" data-intensity="medium">10</div>
          </div>
          <div className="heatmap-row">
            <div className="heatmap-label">Martes</div>
            <div className="heatmap-cell" data-intensity="medium">15</div>
            <div className="heatmap-cell" data-intensity="high">20</div>
            <div className="heatmap-cell" data-intensity="medium">14</div>
            <div className="heatmap-cell" data-intensity="low">9</div>
          </div>
          <div className="heatmap-row">
            <div className="heatmap-label">Miércoles</div>
            <div className="heatmap-cell" data-intensity="high">22</div>
            <div className="heatmap-cell" data-intensity="medium">16</div>
            <div className="heatmap-cell" data-intensity="low">7</div>
            <div className="heatmap-cell" data-intensity="medium">11</div>
          </div>
          <div className="heatmap-row">
            <div className="heatmap-label">Jueves</div>
            <div className="heatmap-cell" data-intensity="medium">13</div>
            <div className="heatmap-cell" data-intensity="low">6</div>
            <div className="heatmap-cell" data-intensity="high">19</div>
            <div className="heatmap-cell" data-intensity="medium">15</div>
          </div>
          <div className="heatmap-row">
            <div className="heatmap-label">Viernes</div>
            <div className="heatmap-cell" data-intensity="high">25</div>
            <div className="heatmap-cell" data-intensity="high">23</div>
            <div className="heatmap-cell" data-intensity="medium">17</div>
            <div className="heatmap-cell" data-intensity="low">8</div>
          </div>
          <div className="heatmap-row">
            <div className="heatmap-label">Sábado</div>
            <div className="heatmap-cell" data-intensity="low">5</div>
            <div className="heatmap-cell" data-intensity="low">4</div>
            <div className="heatmap-cell" data-intensity="medium">12</div>
            <div className="heatmap-cell" data-intensity="medium">10</div>
          </div>
          <div className="heatmap-row">
            <div className="heatmap-label">Domingo</div>
            <div className="heatmap-cell" data-intensity="low">3</div>
            <div className="heatmap-cell" data-intensity="low">5</div>
            <div className="heatmap-cell" data-intensity="low">7</div>
            <div className="heatmap-cell" data-intensity="medium">11</div>
          </div>
          <div className="heatmap-row">
            <div className="heatmap-label"></div>
            <div className="heatmap-week">Sem 1</div>
            <div className="heatmap-week">Sem 2</div>
            <div className="heatmap-week">Sem 3</div>
            <div className="heatmap-week">Sem 4</div>
          </div>
        </div>
      </div>

      {/* Botón Exportar */}
      <div className="export-section">
        <button className="btn-export">
          📥 Exportar Informe Completo (PDF)
        </button>
      </div>
    </div>
  )
}

export default Estadisticas