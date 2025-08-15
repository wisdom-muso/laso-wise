import { useEffect, useState } from 'react'
import { apiJson } from '@/lib/api'

export function useProfile() {
  const [me, setMe] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    const data = await apiJson('/accounts/api/me/')
    setMe(data)
  }

  useEffect(() => {
    let mounted = true
    setLoading(true)
    refresh()
      .catch((e) => setError(e.message))
      .finally(() => mounted && setLoading(false))
    return () => {
      mounted = false
    }
  }, [])

  async function update(payload: any) {
    await apiJson('/accounts/api/me/update/', { method: 'POST', body: payload })
    await refresh()
  }

  async function deactivate() {
    await apiJson('/accounts/api/me/delete/', { method: 'POST' })
  }

  return { me, loading, error, update, deactivate }
}






