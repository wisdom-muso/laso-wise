import { useState } from 'react'
import { motion } from 'framer-motion'
import { ensureCsrfToken, getCookie } from '@/lib/csrf'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export function RegisterPage() {
  const [isDoctor, setIsDoctor] = useState(false)
  const [form, setForm] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function update(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      await ensureCsrfToken('/accounts/login/')
      const csrftoken = getCookie('csrftoken')
      const fd = new URLSearchParams()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v))
      const endpoint = isDoctor ? '/accounts/doctor/register/' : '/accounts/patient/register/'
      const res = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrftoken || '' }, body: fd.toString(), credentials: 'include' })
      if (res.redirected || res.ok) {
        window.location.href = '/login'
      } else {
        setError('Please check the form and try again.')
      }
    } catch (e) {
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
          <h2 className="text-3xl font-semibold mb-2">Create an account</h2>
          <p className="text-white/90">Join our care network with a few details.</p>
        </motion.div>
      </div>

      <motion.form
        onSubmit={handleSubmit}
        className="bg-white dark:bg-secondary-900 rounded-xl p-8 border border-secondary-200/60 dark:border-secondary-800/60 shadow-soft"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center gap-3 mb-6">
          <button type="button" onClick={() => setIsDoctor(false)} className={`h-10 px-4 rounded-full border ${!isDoctor ? 'bg-primary-600 text-white' : 'bg-white text-secondary-700'} border-secondary-200`}>Patient</button>
          <button type="button" onClick={() => setIsDoctor(true)} className={`h-10 px-4 rounded-full border ${isDoctor ? 'bg-primary-600 text-white' : 'bg-white text-secondary-700'} border-secondary-200`}>Doctor</button>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <Label className="block mb-1">First name</Label>
            <Input onChange={(e)=>update('first_name', e.target.value)} />
          </div>
          <div>
            <Label className="block mb-1">Last name</Label>
            <Input onChange={(e)=>update('last_name', e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <Label className="block mb-1">Email</Label>
            <Input type="email" onChange={(e)=>update('email', e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <Label className="block mb-1">Password</Label>
            <Input type="password" onChange={(e)=>update('password1', e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <Label className="block mb-1">Confirm Password</Label>
            <Input type="password" onChange={(e)=>update('password2', e.target.value)} />
          </div>
          {isDoctor && (
            <div className="sm:col-span-2">
              <Label className="block mb-1">Username (optional)</Label>
              <Input onChange={(e)=>update('username', e.target.value)} />
            </div>
          )}
        </div>
        {error && <p className="text-sm text-red-600 mt-3">{error}</p>}
        <Button type="submit" disabled={isLoading} className="mt-6 w-full h-11">
          {isLoading ? 'Creating…' : 'Create account'}
        </Button>
      </motion.form>
    </div>
  )
}


