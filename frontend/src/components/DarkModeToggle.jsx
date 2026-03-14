import { useState, useEffect } from 'react'
import './DarkModeToggle.css'

function DarkModeToggle() {
  const applyTheme = (enabled) => {
    document.documentElement.classList.toggle('dark-mode', enabled)
    document.body.classList.toggle('dark-mode', enabled)
  }

  const [isDark, setIsDark] = useState(() => {
    try {
      const saved = localStorage.getItem('darkMode')
      return saved ? JSON.parse(saved) : false
    } catch {
      return false
    }
  })

  useEffect(() => {
    applyTheme(isDark)
    localStorage.setItem('darkMode', JSON.stringify(isDark))
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { darkMode: isDark } }))
  }, [isDark])

  return (
    <button 
      className={`dark-mode-toggle ${isDark ? 'active' : ''}`}
      onClick={() => setIsDark(!isDark)}
      aria-pressed={isDark}
      aria-label="Toggle dark mode"
    >
      <span className="toggle-icon">{isDark ? '🌙' : '☀️'}</span>
      <span className="toggle-label">{isDark ? 'Modo Oscuro' : 'Modo Claro'}</span>
    </button>
  )
}

export default DarkModeToggle

