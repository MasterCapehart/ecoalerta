import { useState } from 'react'
import './AdvancedSearch.css'

function AdvancedSearch({ onSearch, onReset, categorias = [], tags = [], inspectores = [] }) {
  const [searchParams, setSearchParams] = useState({
    q: '',
    estado: '',
    categoria: '',
    asignado_a: '',
    prioridad: '',
    tags: [],
    fecha_desde: '',
    fecha_hasta: '',
    lat: '',
    lng: '',
    radio: '',
    ordenar_por: 'fecha_creacion',
    orden: 'desc'
  })

  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleChange = (field, value) => {
    setSearchParams(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleTagToggle = (tagId) => {
    setSearchParams(prev => ({
      ...prev,
      tags: prev.tags.includes(tagId)
        ? prev.tags.filter(id => id !== tagId)
        : [...prev.tags, tagId]
    }))
  }

  const handleSearch = () => {
    // Limpiar parámetros vacíos
    const params = {}
    Object.keys(searchParams).forEach(key => {
      const value = searchParams[key]
      if (value !== '' && value !== null && value !== undefined) {
        if (Array.isArray(value) && value.length > 0) {
          params[key] = value
        } else if (!Array.isArray(value)) {
          params[key] = value
        }
      }
    })

    // Convertir tags array a string separado por comas si es necesario
    if (params.tags && params.tags.length > 0) {
      params.tags = params.tags.join(',')
    }

    onSearch(params)
  }

  const handleReset = () => {
    setSearchParams({
      q: '',
      estado: '',
      categoria: '',
      asignado_a: '',
      prioridad: '',
      tags: [],
      fecha_desde: '',
      fecha_hasta: '',
      lat: '',
      lng: '',
      radio: '',
      ordenar_por: 'fecha_creacion',
      orden: 'desc'
    })
    onReset()
  }

  return (
    <div className="advanced-search">
      <div className="search-header">
        <div className="search-basic">
          <input
            type="text"
            placeholder="Buscar por código, descripción, dirección..."
            value={searchParams.q}
            onChange={(e) => handleChange('q', e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="search-input"
          />
          <button onClick={handleSearch} className="btn-search">
            🔍 Buscar
          </button>
          <button onClick={handleReset} className="btn-reset">
            ↺ Limpiar
          </button>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="btn-advanced"
          >
            {showAdvanced ? '▲' : '▼'} Filtros Avanzados
          </button>
        </div>
      </div>

      {showAdvanced && (
        <div className="search-advanced">
          <div className="filters-grid">
            <div className="filter-group">
              <label>Estado</label>
              <select
                value={searchParams.estado}
                onChange={(e) => handleChange('estado', e.target.value)}
              >
                <option value="">Todos</option>
                <option value="nuevo">Nuevo</option>
                <option value="proceso">En Proceso</option>
                <option value="resuelto">Resuelto</option>
                <option value="cerrado">Cerrado</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Categoría</label>
              <select
                value={searchParams.categoria}
                onChange={(e) => handleChange('categoria', e.target.value)}
              >
                <option value="">Todas</option>
                {categorias.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.nombre}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Prioridad</label>
              <select
                value={searchParams.prioridad}
                onChange={(e) => handleChange('prioridad', e.target.value)}
              >
                <option value="">Todas</option>
                <option value="baja">Baja</option>
                <option value="normal">Normal</option>
                <option value="alta">Alta</option>
                <option value="urgente">Urgente</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Asignado a</label>
              <select
                value={searchParams.asignado_a}
                onChange={(e) => handleChange('asignado_a', e.target.value)}
              >
                <option value="">Todos</option>
                {inspectores.map(ins => (
                  <option key={ins.id} value={ins.id}>{ins.username}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Fecha desde</label>
              <input
                type="date"
                value={searchParams.fecha_desde}
                onChange={(e) => handleChange('fecha_desde', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Fecha hasta</label>
              <input
                type="date"
                value={searchParams.fecha_hasta}
                onChange={(e) => handleChange('fecha_hasta', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Ordenar por</label>
              <select
                value={searchParams.ordenar_por}
                onChange={(e) => handleChange('ordenar_por', e.target.value)}
              >
                <option value="fecha_creacion">Fecha de creación</option>
                <option value="prioridad_calculada">Prioridad</option>
                <option value="estado">Estado</option>
                <option value="codigo_seguimiento">Código</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Orden</label>
              <select
                value={searchParams.orden}
                onChange={(e) => handleChange('orden', e.target.value)}
              >
                <option value="desc">Descendente</option>
                <option value="asc">Ascendente</option>
              </select>
            </div>
          </div>

          {tags.length > 0 && (
            <div className="filter-group tags-filter">
              <label>Tags</label>
              <div className="tags-list">
                {tags.map(tag => (
                  <button
                    key={tag.id}
                    className={`tag-btn ${searchParams.tags.includes(tag.id) ? 'active' : ''}`}
                    onClick={() => handleTagToggle(tag.id)}
                    style={{ backgroundColor: searchParams.tags.includes(tag.id) ? tag.color : '#f0f0f0' }}
                  >
                    {tag.nombre}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="filter-group location-filter">
            <label>Búsqueda por proximidad</label>
            <div className="location-inputs">
              <input
                type="number"
                placeholder="Latitud"
                step="any"
                value={searchParams.lat}
                onChange={(e) => handleChange('lat', e.target.value)}
              />
              <input
                type="number"
                placeholder="Longitud"
                step="any"
                value={searchParams.lng}
                onChange={(e) => handleChange('lng', e.target.value)}
              />
              <input
                type="number"
                placeholder="Radio (km)"
                step="0.1"
                value={searchParams.radio}
                onChange={(e) => handleChange('radio', e.target.value)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdvancedSearch

