import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import ModerationPanel from './ModerationPanel'
import RouteOptimizer from './RouteOptimizer'
import {
  Users,
  BarChart2,
  Shield,
  UserPlus,
  Edit2,
  Trash2,
  Search,
  CheckCircle,
  XCircle,
  MoreVertical,
  Map as MapIcon,
  ArrowLeft
} from 'lucide-react'
import './DashboardAdmin.css'

function DashboardAdmin() {
  const navigate = useNavigate()
  const [vista, setVista] = useState('usuarios')
  const [usuarios, setUsuarios] = useState([])
  const [estadisticas, setEstadisticas] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showModalUsuario, setShowModalUsuario] = useState(false)
  const [usuarioEditando, setUsuarioEditando] = useState(null)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    tipo: 'ciudadano',
    telefono: ''
  })

  useEffect(() => {
    if (vista === 'usuarios') {
      loadUsuarios()
    } else if (vista === 'estadisticas') {
      loadEstadisticas()
    }
  }, [vista])

  const loadUsuarios = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get(API_ROUTES.ADMIN_USUARIOS)
      setUsuarios(response.data || [])
    } catch (error) {
      console.error('Error al cargar usuarios:', error)
      toast.error('Error al cargar usuarios')
    } finally {
      setLoading(false)
    }
  }

  const loadEstadisticas = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get(API_ROUTES.ADMIN_ESTADISTICAS)
      setEstadisticas(response.data)
    } catch (error) {
      console.error('Error al cargar estadísticas:', error)
      toast.error('Error al cargar estadísticas')
    } finally {
      setLoading(false)
    }
  }

  const handleCrearUsuario = () => {
    setUsuarioEditando(null)
    setFormData({
      username: '',
      password: '',
      email: '',
      tipo: 'ciudadano',
      telefono: ''
    })
    setShowModalUsuario(true)
  }

  const handleEditarUsuario = (usuario) => {
    setUsuarioEditando(usuario)
    setFormData({
      username: usuario.username,
      password: '',
      email: usuario.email || '',
      tipo: usuario.tipo || 'ciudadano',
      telefono: usuario.telefono || ''
    })
    setShowModalUsuario(true)
  }

  const handleGuardarUsuario = async () => {
    try {
      if (usuarioEditando) {
        // Actualizar
        await apiClient.put(`${API_ROUTES.ADMIN_USUARIOS}${usuarioEditando.id}/`, formData)
        toast.success('Usuario actualizado exitosamente')
      } else {
        // Crear
        await apiClient.post(API_ROUTES.ADMIN_USUARIOS, formData)
        toast.success('Usuario creado exitosamente')
      }
      setShowModalUsuario(false)
      loadUsuarios()
    } catch (error) {
      console.error('Error al guardar usuario:', error)
      toast.error(error.response?.data?.error || 'Error al guardar usuario')
    }
  }

  const handleEliminarUsuario = async (id) => {
    if (!window.confirm('¿Estás seguro de desactivar este usuario?')) {
      return
    }

    try {
      await apiClient.delete(`${API_ROUTES.ADMIN_USUARIOS}${id}/`)
      toast.success('Usuario desactivado')
      loadUsuarios()
    } catch (error) {
      console.error('Error al eliminar usuario:', error)
      toast.error('Error al desactivar usuario')
    }
  }

  return (
    <div className="dashboard-admin">
      <div className="admin-header">
        <div className="admin-header-left">
          <button className="btn-volver" onClick={() => navigate('/dashboard')}>
            <ArrowLeft size={20} />
            Volver al Dashboard
          </button>
          <h1>Panel de Administración</h1>
        </div>
      </div>

      <div className="admin-nav">
        <button
          className={vista === 'usuarios' ? 'active' : ''}
          onClick={() => setVista('usuarios')}
        >
          <Users size={18} />
          Usuarios
        </button>
        <button
          className={vista === 'estadisticas' ? 'active' : ''}
          onClick={() => setVista('estadisticas')}
        >
          <BarChart2 size={18} />
          Estadísticas
        </button>
        <button
          className={vista === 'moderacion' ? 'active' : ''}
          onClick={() => setVista('moderacion')}
        >
          <Shield size={18} />
          Moderación
        </button>
        <button
          className={vista === 'rutas' ? 'active' : ''}
          onClick={() => setVista('rutas')}
        >
          <MapIcon size={18} />
          Rutas
        </button>
      </div>

      <div className="admin-content">
        {vista === 'usuarios' && (
          <div className="usuarios-section">
            <div className="section-header">
              <h2>Gestión de Usuarios</h2>
              <button className="btn-primary" onClick={handleCrearUsuario}>
                <UserPlus size={18} />
                Nuevo Usuario
              </button>
            </div>

            {loading ? (
              <div className="loading">Cargando...</div>
            ) : (
              <table className="usuarios-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Usuario</th>
                    <th>Email</th>
                    <th>Tipo</th>
                    <th>Teléfono</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {usuarios.map(usuario => (
                    <tr key={usuario.id}>
                      <td>{usuario.id}</td>
                      <td>{usuario.username}</td>
                      <td>{usuario.email || '-'}</td>
                      <td>
                        <span className={`badge badge-${usuario.tipo}`}>
                          {usuario.tipo}
                        </span>
                      </td>
                      <td>{usuario.telefono || '-'}</td>
                      <td>
                        <div className="action-buttons">
                          <button
                            className="btn-icon btn-edit"
                            onClick={() => handleEditarUsuario(usuario)}
                            title="Editar usuario"
                          >
                            <Edit2 size={16} />
                          </button>
                          <button
                            className="btn-icon btn-delete"
                            onClick={() => handleEliminarUsuario(usuario.id)}
                            title="Desactivar usuario"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {vista === 'estadisticas' && (
          <div className="estadisticas-section">
            <h2>Estadísticas Generales</h2>
            {loading ? (
              <div className="loading">Cargando...</div>
            ) : estadisticas ? (
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Total Usuarios</h3>
                  <p className="stat-value">{estadisticas.total_usuarios || 0}</p>
                </div>
                <div className="stat-card">
                  <h3>Inspectores Activos</h3>
                  <p className="stat-value">{estadisticas.total_inspectores || 0}</p>
                </div>
                <div className="stat-card">
                  <h3>Total Reportes</h3>
                  <p className="stat-value">{estadisticas.total_reportes || 0}</p>
                </div>
                <div className="stat-card">
                  <h3>Reportes (30 días)</h3>
                  <p className="stat-value">{estadisticas.reportes_ultimos_30_dias || 0}</p>
                </div>
                <div className="stat-card">
                  <h3>Tiempo Promedio Resolución</h3>
                  <p className="stat-value">
                    {estadisticas.promedio_resolucion_horas
                      ? `${Math.round(estadisticas.promedio_resolucion_horas)}h`
                      : 'N/A'}
                  </p>
                </div>
                <div className="stat-card stat-card-wide">
                  <h3>Reportes por Estado</h3>
                  <div className="reportes-por-estado">
                    {Object.entries(estadisticas.reportes_por_estado || {}).map(([estado, count]) => (
                      <div key={estado} className="estado-item">
                        <span className="estado-name">{estado}</span>
                        <span className="estado-count">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="no-data">No hay datos disponibles</div>
            )}
          </div>
        )}

        {vista === 'moderacion' && (
          <div className="moderacion-section">
            <ModerationPanel />
          </div>
        )}

        {vista === 'rutas' && (
          <div className="rutas-section">
            <RouteOptimizer />
          </div>
        )}
      </div>

      {showModalUsuario && (
        <div className="modal-overlay" onClick={() => setShowModalUsuario(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>{usuarioEditando ? 'Editar Usuario' : 'Nuevo Usuario'}</h3>
            <div className="form-group">
              <label>Usuario *</label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                disabled={!!usuarioEditando}
              />
            </div>
            {!usuarioEditando && (
              <div className="form-group">
                <label>Contraseña *</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
              </div>
            )}
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Tipo</label>
              <select
                value={formData.tipo}
                onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
              >
                <option value="ciudadano">Ciudadano</option>
                <option value="inspector">Inspector</option>
                <option value="admin">Administrador</option>
              </select>
            </div>
            <div className="form-group">
              <label>Teléfono</label>
              <input
                type="text"
                value={formData.telefono}
                onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowModalUsuario(false)}>
                Cancelar
              </button>
              <button className="btn-save" onClick={handleGuardarUsuario}>
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DashboardAdmin
