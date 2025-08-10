import { useEffect, useState } from 'react'
import { apiJson } from '@/lib/api'

type DoctorStats = {
  totalPatients: number
  todayPatients: number
  totalAppointments: number
}

export function useDoctorDashboard() {
  const [stats, setStats] = useState<DoctorStats | null>(null)
  const [upcoming, setUpcoming] = useState<any[]>([])
  const [recentRx, setRecentRx] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    apiJson<{ stats: DoctorStats; upcomingAppointments: any[]; recentPrescriptions: any[] }>(`/doctors/api/dashboard/`)
      .then((data) => {
        if (!mounted) return
        setStats(data.stats)
        setUpcoming(data.upcomingAppointments)
        setRecentRx(data.recentPrescriptions)
      })
      .catch((e) => mounted && setError(e.message))
      .finally(() => mounted && setLoading(false))
    return () => {
      mounted = false
    }
  }, [])

  async function actOnAppointment(id: number, action: 'accept' | 'cancel' | 'completed') {
    await apiJson(`/doctors/api/appointments/${id}/${action}/`, { method: 'POST' })
    setUpcoming((prev) => prev.map((a) => (a.id === id ? { ...a, status: action === 'accept' ? 'confirmed' : action } : a)))
  }

  return { stats, upcoming, recentRx, loading, error, actOnAppointment }
}




