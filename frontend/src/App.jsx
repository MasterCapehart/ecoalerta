import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/Login'
import ReporteForm from './components/ReporteForm'
import DashboardMunicipal from './components/DashboardMunicipal'
import ToastContainer from './components/ToastContainer'

function App() {
  return (
    <BrowserRouter>
      <ToastContainer />
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/login" element={<Login />} />
        <Route path="/reporte" element={<ReporteForm />} />
        <Route path="/dashboard" element={<DashboardMunicipal />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App