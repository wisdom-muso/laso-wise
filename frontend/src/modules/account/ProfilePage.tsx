import { useProfile } from '@/hooks/useProfile'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { useState } from 'react'

export function ProfilePage() {
  const { me, loading, update, deactivate } = useProfile()
  const [form, setForm] = useState<any>({})
  if (loading) return <div>Loading…</div>
  if (!me) return <div>Not authenticated</div>

  function setField(field: string, value: string) {
    setForm((f: any) => ({ ...f, [field]: value }))
  }

  async function submit() {
    await update(form)
    alert('Profile updated')
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold text-primary-700 mb-6">Profile settings</h1>
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <Label className="block mb-1">First name</Label>
          <Input defaultValue={me.first_name} onChange={(e)=>setField('first_name', e.target.value)} />
        </div>
        <div>
          <Label className="block mb-1">Last name</Label>
          <Input defaultValue={me.last_name} onChange={(e)=>setField('last_name', e.target.value)} />
        </div>
        <div className="sm:col-span-2">
          <Label className="block mb-1">Email</Label>
          <Input defaultValue={me.email} onChange={(e)=>setField('email', e.target.value)} />
        </div>
        <div>
          <Label className="block mb-1">Phone</Label>
          <Input defaultValue={me.profile?.phone} onChange={(e)=>setField('phone', e.target.value)} />
        </div>
        <div>
          <Label className="block mb-1">City</Label>
          <Input defaultValue={me.profile?.city} onChange={(e)=>setField('city', e.target.value)} />
        </div>
        <div className="sm:col-span-2 mt-4">
          <Button onClick={submit}>Save changes</Button>
        </div>
      </div>

      <div className="mt-12">
        <Button variant="secondary" onClick={deactivate}>Deactivate account</Button>
      </div>
    </div>
  )
}




