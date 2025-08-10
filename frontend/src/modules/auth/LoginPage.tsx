import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ensureCsrfToken, getCookie } from '@/lib/csrf'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      // ensure csrftoken
      await ensureCsrfToken('/accounts/login/')
      const csrftoken = getCookie('csrftoken')
      const form = new URLSearchParams()
      form.append('username', username)
      form.append('password', password)
      const res = await fetch('/accounts/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrftoken || '' },
        body: form.toString(),
        credentials: 'include',
      })
      if (res.redirected || res.ok) {
        window.location.href = '/patients/dashboard'
      } else {
        setError('Invalid credentials')
      }
    } catch (err) {
      setError('Something went wrong')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="grid md:grid-cols-2 gap-10 items-center">
      <div className="hidden md:block">
        <motion.div
          className="rounded-2xl p-10 brand-gradient text-white"
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl font-semibold mb-2">Welcome back</h2>
          <p className="text-white/90">Access your medical dashboard securely.</p>
        </motion.div>
      </div>
      <motion.form
        onSubmit={handleSubmit}
        className="bg-white dark:bg-secondary-900 rounded-xl p-8 border border-secondary-200/60 dark:border-secondary-800/60 shadow-soft"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl font-semibold text-primary-700 mb-6">Login</h1>
        <div className="space-y-4">
          <div>
            <Label className="mb-1 block">Username</Label>
            <Input value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div>
            <Label className="mb-1 block">Password</Label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" disabled={isLoading} className="w-full h-11 text-white">
            {isLoading ? 'Signing in…' : 'Sign in'}
          </Button>
        </div>
      </motion.form>
    </div>
  )
}


