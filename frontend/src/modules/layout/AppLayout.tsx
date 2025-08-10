import { Outlet, Link, NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

export function AppLayout() {
  const [isDark, setIsDark] = useState(false)
  useEffect(() => {
    const root = document.documentElement
    const saved = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const enabled = saved ? saved === 'dark' : prefersDark
    setIsDark(enabled)
    root.classList.toggle('dark', enabled)
  }, [])

  function toggleTheme() {
    const next = !isDark
    setIsDark(next)
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('theme', next ? 'dark' : 'light')
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-40 bg-white/70 dark:bg-secondary-900/70 glass border-b border-secondary-200/60 dark:border-secondary-800/60">
        <div className="container flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full brand-gradient" />
            <span className="text-lg font-semibold text-primary-700">Laso Health</span>
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <NavLink to="/patients/dashboard" className={({isActive}) => isActive ? 'text-primary-600' : 'text-secondary-600 hover:text-primary-600'}>
              Dashboard
            </NavLink>
            <NavLink to="/doctors/dashboard" className={({isActive}) => isActive ? 'text-primary-600' : 'text-secondary-600 hover:text-primary-600'}>
              Doctor
            </NavLink>
            <NavLink to="/login" className={({isActive}) => isActive ? 'text-primary-600' : 'text-secondary-600 hover:text-primary-600'}>
              Login
            </NavLink>
            <NavLink to="/register" className={({isActive}) => isActive ? 'text-primary-600' : 'text-secondary-600 hover:text-primary-600'}>
              Register
            </NavLink>
            <button onClick={toggleTheme} className="ml-4 h-9 px-3 rounded-full border border-secondary-200 text-secondary-700 dark:text-secondary-200">
              {isDark ? 'Light' : 'Dark'}
            </button>
          </nav>
        </div>
      </header>
      <motion.main
        className="flex-1 container py-10"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Outlet />
      </motion.main>
      <footer className="border-t border-secondary-200/60 dark:border-secondary-800/60 py-6">
        <div className="container text-xs text-secondary-500">© {new Date().getFullYear()} Laso</div>
      </footer>
    </div>
  )
}



