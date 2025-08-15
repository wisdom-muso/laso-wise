import { useEffect, useState } from 'react'
import { apiJson } from '@/lib/api'

export type DayKey = 'sunday'|'monday'|'tuesday'|'wednesday'|'thursday'|'friday'|'saturday'
export type TimeBlock = { start: string; end: string; slots_per_hour?: number }

export function useDoctorSchedule() {
  const [schedule, setSchedule] = useState<Record<DayKey, TimeBlock[]>>({
    sunday: [], monday: [], tuesday: [], wednesday: [], thursday: [], friday: [], saturday: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    const data = await apiJson<Record<DayKey, TimeBlock[]>>('/doctors/api/schedule/')
    setSchedule(data)
  }

  useEffect(() => {
    setLoading(true)
    refresh().catch((e)=>setError(e.message)).finally(()=>setLoading(false))
  }, [])

  async function save() {
    await apiJson('/doctors/api/schedule/', { method: 'POST', body: schedule })
  }

  function addBlock(day: DayKey) {
    setSchedule((s) => ({ ...s, [day]: [...s[day], { start: '09:00', end: '17:00', slots_per_hour: 4 }] }))
  }

  function updateBlock(day: DayKey, idx: number, block: Partial<TimeBlock>) {
    setSchedule((s) => {
      const copy = { ...s }
      copy[day] = copy[day].map((b, i) => (i === idx ? { ...b, ...block } : b))
      return copy
    })
  }

  function removeBlock(day: DayKey, idx: number) {
    setSchedule((s) => {
      const copy = { ...s }
      copy[day] = copy[day].filter((_, i) => i !== idx)
      return copy
    })
  }

  return { schedule, setSchedule, loading, error, addBlock, updateBlock, removeBlock, save }
}






