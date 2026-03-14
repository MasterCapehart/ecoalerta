import { useState, useEffect } from 'react'
import apiClient from '../services/api'
import { API_ROUTES } from '../config'
import { toast } from './ToastContainer'
import './EmployeeManager.css'

function EmployeeManager({ onEmployeeUpdated, userInfo }) {
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingEmployee, setEditingEmployee] = useState(null)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    tipo: 'inspector',
    telefono: '',
    first_name: '',
    last_name: '',
    is_staff: false,
    is_active: true
  })

  useEffect(() => {
    loadEmployees()
  }, [])

  const loadEmployees = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get(API_ROUTES.ADMIN_USUARIOS)
      // Filtrar solo inspectores y admins para esta vista
      const empleados = (response.data || []).filter(u => u.tipo === 'inspector' || u.tipo === 'admin')
      setEmployees(empleados)
    } catch (error) {
      console.error('Error al cargar empleados:', error)
      toast.error('Error al cargar empleados')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingEmployee(null)
    setFormData({
      username: '',
      password: '',
      email: '',
      tipo: 'inspector',
      telefono: '',
      first_name: '',
      last_name: '',
      is_staff: false,
      is_active: true
    })
    setShowModal(true)
  }

  const handleEdit = (employee) => {
    setEditingEmployee(employee)
    setFormData({
      username: employee.username,
      password: '', // No mostrar password
      email: employee.email || '',
      tipo: employee.tipo || 'inspector',
      telefono: employee.telefono || '',
      first_name: employee.first_name || '',
      last_name: employee.last_name || '',
      is_staff: employee.is_staff || false,
      is_active: employee.is_active !== undefined ? employee.is_active : true
    })
    setShowModal(true)
  }

  const handleSave = async () => {
    try {
      const dataToSend = { ...formData }
      
      // Si estamos editando y no hay password, no enviarlo
      if (editingEmployee && !dataToSend.password) {
        delete dataToSend.password
      }

      if (editingEmployee) {
        // Actualizar
        await apiClient.put(`${API_ROUTES.ADMIN_USUARIOS}${editingEmployee.id}/`, dataToSend)
        toast.success('Empleado actualizado exitosamente')
      } else {
        // Crear nuevo
        if (!dataToSend.password) {
          toast.error('La contraseña es requerida para nuevos empleados')
          return
        }
        await apiClient.post(API_ROUTES.ADMIN_USUARIOS, dataToSend)
        toast.success('Empleado creado exitosamente')
      }
      
      setShowModal(false)
      loadEmployees()
      if (onEmployeeUpdated) {
        onEmployeeUpdated()
      }
    } catch (error) {
      console.error('Error al guardar empleado:', error)
      const errorMsg = error.response?.data?.error || error.response?.data?.username?.[0] || 'Error al guardar empleado'
      toast.error(errorMsg)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('¿Estás seguro de desactivar este empleado?')) {
      return
    }

    try {
      await apiClient.delete(`${API_ROUTES.ADMIN_USUARIOS}${id}/`)
      toast.success('Empleado desactivado')
      loadEmployees()
      if (onEmployeeUpdated) {
        onEmployeeUpdated()
      }
    } catch (error) {
      console.error('Error al desactivar empleado:', error)
      toast.error('Error al desactivar empleado')
    }
  }

  if (loading) {
    return <div className="employee-manager-loading">Cargando empleados...</div>
  }

  return (
    <div className="employee-manager">
      <div className="employee-manager-header">
        <div>
          <h2>Gestión de Empleados</h2>
          <p>Administra inspectores y funcionarios municipales</p>
        </div>
        <button className="btn-create-employee" onClick={handleCreate}>
          + Nuevo Empleado
        </button>
      </div>

      <div className="employee-list">
        {employees.length === 0 ? (
          <div className="employee-empty">
            <p>No hay empleados registrados</p>
          </div>
        ) : (
          employees.map(employee => (
            <div key={employee.id} className="employee-card">
              <div className="employee-card-header">
                <div className="employee-avatar">
                  {employee.first_name || employee.username ? 
                    (employee.first_name?.[0] || employee.username[0]).toUpperCase() : 
                    'E'}
                </div>
                <div className="employee-info">
                  <h3>{employee.first_name && employee.last_name 
                    ? `${employee.first_name} ${employee.last_name}` 
                    : employee.username}</h3>
                  <p>@{employee.username}</p>
                  {employee.email && <p className="employee-email">{employee.email}</p>}
                </div>
                <div className="employee-badges">
                  <span className={`badge badge-${employee.tipo}`}>{employee.tipo}</span>
                  {employee.is_staff && <span className="badge badge-staff">Staff</span>}
                  {!employee.is_active && <span className="badge badge-inactive">Inactivo</span>}
                </div>
              </div>
              
              <div className="employee-actions">
                <button 
                  className="btn-edit-employee"
                  onClick={() => handleEdit(employee)}
                >
                  Editar
                </button>
                <button 
                  className="btn-delete-employee"
                  onClick={() => handleDelete(employee.id)}
                >
                  Desactivar
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content employee-modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editingEmployee ? 'Editar Empleado' : 'Nuevo Empleado'}</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>Usuario *</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  disabled={!!editingEmployee}
                  placeholder="usuario"
                />
              </div>
              
              <div className="form-group">
                <label>Contraseña {!editingEmployee && '*'}</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  placeholder={editingEmployee ? "Dejar vacío para mantener" : "contraseña"}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Nombre</label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                  placeholder="Nombre"
                />
              </div>
              
              <div className="form-group">
                <label>Apellido</label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                  placeholder="Apellido"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="email@ejemplo.com"
                />
              </div>
              
              <div className="form-group">
                <label>Teléfono</label>
                <input
                  type="text"
                  value={formData.telefono}
                  onChange={(e) => setFormData({...formData, telefono: e.target.value})}
                  placeholder="+56 9 1234 5678"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Tipo de Usuario *</label>
                <select
                  value={formData.tipo}
                  onChange={(e) => setFormData({...formData, tipo: e.target.value})}
                >
                  <option value="inspector">Inspector Municipal</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Estado</label>
                <select
                  value={formData.is_active ? 'active' : 'inactive'}
                  onChange={(e) => setFormData({...formData, is_active: e.target.value === 'active'})}
                >
                  <option value="active">Activo</option>
                  <option value="inactive">Inactivo</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_staff}
                  onChange={(e) => setFormData({...formData, is_staff: e.target.checked})}
                />
                <span>Permisos de Staff (acceso al panel de administración de Django)</span>
              </label>
            </div>

            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowModal(false)}>
                Cancelar
              </button>
              <button className="btn-save" onClick={handleSave}>
                {editingEmployee ? 'Actualizar' : 'Crear'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default EmployeeManager
