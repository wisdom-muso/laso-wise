import { useDoctorSchedule, DayKey } from '@/hooks/useDoctorSchedule'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function SchedulePage() {
  const { schedule, addBlock, updateBlock, removeBlock, save, loading } = useDoctorSchedule()
  const days: DayKey[] = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']
  if (loading) return <div>Loading…</div>
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-primary-700">Schedule</h1>
      <div className="grid lg:grid-cols-2 gap-6">
        {days.map((d) => (
          <div key={d} className="rounded-xl p-6 bg-white dark:bg-secondary-900 border border-secondary-200/60 dark:border-secondary-800/60">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium capitalize">{d}</h3>
              <Button variant="secondary" onClick={() => addBlock(d)}>Add block</Button>
            </div>
            <div className="space-y-3">
              {schedule[d].map((b, i) => (
                <div key={i} className="grid grid-cols-3 gap-3 items-center">
                  <Input value={b.start} onChange={(e)=>updateBlock(d, i, { start: e.target.value })} />
                  <Input value={b.end} onChange={(e)=>updateBlock(d, i, { end: e.target.value })} />
                  <Input value={String(b.slots_per_hour ?? 4)} onChange={(e)=>updateBlock(d, i, { slots_per_hour: Number(e.target.value)||4 })} />
                  <div className="col-span-3 flex justify-end">
                    <Button variant="secondary" onClick={()=>removeBlock(d, i)}>Remove</Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="flex justify-end">
        <Button onClick={save}>Save schedule</Button>
      </div>
    </div>
  )
}




