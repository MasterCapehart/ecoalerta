import { useState, useEffect } from 'react'
import './DarkModeToggle.css'

function DarkModeToggle() {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved ? JSON.parse(saved) : false
  })

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark-mode')
    } else {
      document.documentElement.classList.remove('dark-mode')
    }
    localStorage.setItem('darkMode', JSON.stringify(isDark))
  }, [isDark])

  return (
    <button 
      className={`dark-mode-toggle ${isDark ? 'active' : ''}`}
      onClick={() => setIsDark(!isDark)}
      aria-label="Toggle dark mode"
    >
      <span className="toggle-icon">{isDark ? '🌙' : '☀️'}</span>
      <span className="toggle-label">{isDark ? 'Modo Oscuro' : 'Modo Claro'}</span>
    </button>
  )
}

export default DarkModeToggle

