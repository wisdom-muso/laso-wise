import { motion } from 'framer-motion'
import { Tabs } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { ensureCsrfToken, getCookie } from '@/lib/csrf'
import { useState } from 'react'
import { Modal } from '@/components/ui/modal'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { usePatientDashboard } from '@/hooks/usePatientDashboard'

const stats = [
  { label: 'Upcoming Appointments', value: 2 },
  { label: 'Prescriptions', value: 5 },
  { label: 'Messages', value: 1 },
]

export function PatientDashboard() {
  const [vitalsOpen, setVitalsOpen] = useState(false)
  const [vitals, setVitals] = useState({
    value: '',
    category: '1',
    value_diastolic: '',
    category_diastolic: '2',
    heart_rate: '',
    category_heart_rate: '3',
    temperature: '',
    weight: '',
    height: '',
    notes: '',
  })
  function setField(field: string, value: string) {
    setVitals((p) => ({ ...p, [field]: value }))
  }
  async function submitVitals() {
    await ensureCsrfToken('/accounts/login/')
    const csrftoken = getCookie('csrftoken')
    const fd = new URLSearchParams(vitals as any)
    const res = await fetch('/vitals/add/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrftoken || '' },
      body: fd.toString(),
      credentials: 'include',
    })
    if (res.ok) {
      setVitalsOpen(false)
      alert('Vitals recorded successfully')
    } else {
      alert('Failed to record vitals')
    }
  }
  const { stats: liveStats, appointments: appts, loading } = usePatientDashboard()
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-primary-700">Your health at a glance</h1>
          <p className="text-secondary-600">Welcome back. Wishing you a peaceful day.</p>
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-6">
        {(liveStats
          ? [
              { label: 'Upcoming Appointments', value: liveStats.upcomingAppointments },
              { label: 'Prescriptions', value: liveStats.prescriptions },
              { label: 'Doctors Consulted', value: liveStats.doctorsConsulted },
            ]
          : stats
        ).map((s, i) => (
          <motion.div
            key={s.label}
            className="rounded-xl p-6 bg-white dark:bg-secondary-900 border border-secondary-200/60 dark:border-secondary-800/60 shadow-soft"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <div className="text-3xl font-semibold text-primary-600">{s.value}</div>
            <div className="text-sm text-secondary-600">{s.label}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <motion.div
          className="rounded-xl p-6 bg-white dark:bg-secondary-900 border border-secondary-200/60 dark:border-secondary-800/60 lg:col-span-2"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="mb-6 -mt-2 flex flex-wrap gap-3">
            <a href="/doctors/" className="h-10 px-4 rounded-lg bg-primary-600 text-white">Find doctors</a>
            <a href="/patients/profile-settings/" className="h-10 px-4 rounded-lg border border-secondary-200">Update profile</a>
            <Button variant="secondary" onClick={() => setVitalsOpen(true)}>Record vitals</Button>
            <a href="/patients/medical-records/" className="h-10 px-4 rounded-lg border border-secondary-200">View records</a>
          </div>
          <Tabs
            tabs={[
              {
                id: 'appointments',
                label: 'Appointments',
                content: (
                  <div className="space-y-3">
                    {(appts || []).map((a) => (
                      <div key={a.id} className="p-4 rounded-lg border border-secondary-200 flex items-center justify-between">
                        <div>
                          <div className="font-medium">Dr. {a.doctor?.name}</div>
                          <div className="text-sm text-secondary-600">
                            {new Date(a.appointment_date).toLocaleDateString()} • {a.appointment_time}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <a href={`/patients/appointments/${a.id}/`} className="h-10 px-3 rounded-lg border border-secondary-200">Details</a>
                          <a href={`/patients/appointments/${a.id}/print/`} target="_blank" className="h-10 px-3 rounded-lg bg-primary-600 text-white">Print</a>
                        </div>
                      </div>
                    ))}
                    {loading && <div className="text-sm text-secondary-500">Loading…</div>}
                  </div>
                ),
              },
              {
                id: 'prescriptions',
                label: 'Prescriptions',
                content: (
                  <div className="text-sm text-secondary-700">
                    Your prescriptions are securely stored and accessible only to you and your authorized healthcare providers.
                  </div>
                ),
              },
              {
                id: 'medical-records',
                label: 'Medical Records',
                content: (
                  <div className="text-sm text-secondary-700">Your medical records will appear here once uploaded.</div>
                ),
              },
              {
                id: 'billing',
                label: 'Billing',
                content: <div className="text-sm text-secondary-700">Billing info coming soon.</div>,
              },
            ]}
            initialId="appointments"
          />
        </motion.div>

        <motion.div
          className="rounded-xl p-6 bg-white dark:bg-secondary-900 border border-secondary-200/60 dark:border-secondary-800/60"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3 className="font-medium mb-4 text-secondary-700">Wellness tips</h3>
          <ul className="list-disc pl-5 text-sm text-secondary-700 space-y-2">
            <li>Stay hydrated; aim for 6–8 glasses of water daily.</li>
            <li>Take a 10-minute mindful walk today.</li>
            <li>Keep a consistent sleep routine for better recovery.</li>
          </ul>
          <div className="mt-6 text-sm text-secondary-600">Stay well. Your health matters.</div>
        </motion.div>
      </div>

      <Modal open={vitalsOpen} onClose={() => setVitalsOpen(false)} title="Record Vitals">
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <Label className="mb-1 block">Blood Pressure (Systolic)</Label>
            <Input value={vitals.value} onChange={(e)=>setField('value', e.target.value)} placeholder="120" />
            <input type="hidden" value={vitals.category} readOnly />
          </div>
          <div>
            <Label className="mb-1 block">Blood Pressure (Diastolic)</Label>
            <Input value={vitals.value_diastolic} onChange={(e)=>setField('value_diastolic', e.target.value)} placeholder="80" />
            <input type="hidden" value={vitals.category_diastolic} readOnly />
          </div>
          <div>
            <Label className="mb-1 block">Heart Rate (BPM)</Label>
            <Input value={vitals.heart_rate} onChange={(e)=>setField('heart_rate', e.target.value)} placeholder="72" />
            <input type="hidden" value={vitals.category_heart_rate} readOnly />
          </div>
          <div>
            <Label className="mb-1 block">Temperature (°F)</Label>
            <Input value={vitals.temperature} onChange={(e)=>setField('temperature', e.target.value)} placeholder="98.6" />
          </div>
          <div>
            <Label className="mb-1 block">Weight (kg)</Label>
            <Input value={vitals.weight} onChange={(e)=>setField('weight', e.target.value)} placeholder="70" />
          </div>
          <div>
            <Label className="mb-1 block">Height (cm)</Label>
            <Input value={vitals.height} onChange={(e)=>setField('height', e.target.value)} placeholder="170" />
          </div>
          <div className="sm:col-span-2">
            <Label className="mb-1 block">Notes</Label>
            <textarea className="w-full min-h-[96px] rounded-lg border border-secondary-200 px-3 py-2 text-sm" value={vitals.notes} onChange={(e)=>setField('notes', e.target.value)} />
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={()=>setVitalsOpen(false)}>Cancel</Button>
          <Button onClick={submitVitals}>Save</Button>
        </div>
      </Modal>
    </div>
  )
}



