import { useEffect, useState } from 'react'
import { apiJson } from '@/lib/api'

type PatientStats = {
  upcomingAppointments: number
  prescriptions: number
  doctorsConsulted: number
  healthScore: number
}

export function usePatientDashboard() {
  const [stats, setStats] = useState<PatientStats | null>(null)
  const [appointments, setAppointments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    apiJson<{ stats: PatientStats; appointments: any[] }>(`/patients/api/dashboard/`)
      .then((data) => {
        if (!mounted) return
        setStats(data.stats)
        setAppointments(data.appointments)
      })
      .catch((e) => mounted && setError(e.message))
      .finally(() => mounted && setLoading(false))
    return () => {
      mounted = false
    }
  }, [])

  async function cancelAppointment(id: number) {
    await apiJson(`/patients/api/appointments/${id}/cancel/`, { method: 'POST' })
    setAppointments((prev) => prev.map((a) => (a.id === id ? { ...a, status: 'cancelled' } : a)))
  }

  return { stats, appointments, loading, error, cancelAppointment }
}






