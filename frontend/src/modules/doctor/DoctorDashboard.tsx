import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { useDoctorDashboard } from '@/hooks/useDoctorDashboard'

export function DoctorDashboard() {
  const { stats, upcoming, recentRx, loading, actOnAppointment } = useDoctorDashboard()
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-primary-700">Practice overview</h1>
        <p className="text-secondary-600">Welcome back, doctor.</p>
      </div>

      <div className="grid sm:grid-cols-4 gap-6">
        {(
          stats
            ? [
                { label: 'Total Patients', value: stats.totalPatients },
                { label: "Today's Patients", value: stats.todayPatients },
                { label: 'Total Appointments', value: stats.totalAppointments },
                { label: 'Average Rating', value: 4.8 },
              ]
            : [
                { label: 'Total Patients', value: 0 },
                { label: "Today's Patients", value: 0 },
                { label: 'Total Appointments', value: 0 },
                { label: 'Average Rating', value: 0 },
              ]
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

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="mb-2 -mt-2 flex flex-wrap gap-3 lg:col-span-2">
          <a href="/doctors/appointments/" className="h-10 px-4 rounded-lg bg-primary-600 text-white">View appointments</a>
          <a href="/doctors/my-patients/" className="h-10 px-4 rounded-lg border border-secondary-200">My patients</a>
          <a href="/doctors/profile-settings/" className="h-10 px-4 rounded-lg border border-secondary-200">Update profile</a>
          <a href="#" className="h-10 px-4 rounded-lg bg-success-500 text-white">New prescription</a>
        </div>
        <motion.div
          className="rounded-xl p-6 bg-white dark:bg-secondary-900 border border-secondary-200/60 dark:border-secondary-800/60"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3 className="font-medium mb-4 text-secondary-700">Upcoming appointments</h3>
          <div className="space-y-3">
            {(upcoming || []).map((u) => (
              <div key={u.id} className="p-4 rounded-lg border border-secondary-200 flex items-center justify-between">
                <div>
                  <div className="font-medium">{u.patient?.name}</div>
                  <div className="text-sm text-secondary-600">
                    {new Date(u.appointment_date).toLocaleDateString()} • {u.appointment_time}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button className="h-9 bg-success-500 hover:bg-success-600" onClick={()=>actOnAppointment(u.id, 'accept')}>Accept</Button>
                  <Button className="h-9 bg-warning-500 hover:bg-warning-600" onClick={()=>actOnAppointment(u.id, 'cancel')}>Cancel</Button>
                </div>
              </div>
            ))}
            {loading && <div className="text-sm text-secondary-500">Loading…</div>}
          </div>
        </motion.div>
        <motion.div
          className="rounded-xl p-6 bg-white dark:bg-secondary-900 border border-secondary-200/60 dark:border-secondary-800/60"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3 className="font-medium mb-4 text-secondary-700">Recent prescriptions</h3>
          <div className="space-y-3">
            {(recentRx || []).map((r) => (
              <div key={r.id} className="p-4 rounded-lg border border-secondary-200 flex items-center justify-between">
                <div>
                  <div className="font-medium">{r.patient?.name}</div>
                  <div className="text-sm text-secondary-600">Diagnosis: {r.diagnosis}</div>
                </div>
                <a href={`/doctors/prescription/${r.id}/`} className="h-9 px-3 rounded-lg bg-primary-600 text-white">View</a>
              </div>
            ))}
            {loading && <div className="text-sm text-secondary-500">Loading…</div>}
          </div>
        </motion.div>
      </div>
    </div>
  )
}


