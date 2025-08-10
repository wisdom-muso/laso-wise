import { ReactNode, useState } from 'react'
import { cn } from '@/lib/utils'

export type Tab = { id: string; label: string; content: ReactNode }

export function Tabs({ tabs, initialId }: { tabs: Tab[]; initialId?: string }) {
  const [active, setActive] = useState(initialId ?? tabs[0]?.id)
  return (
    <div>
      <div className="flex gap-2 border-b border-secondary-200/60 dark:border-secondary-800/60 mb-4">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={cn(
              'h-10 px-4 rounded-t-md',
              active === t.id
                ? 'bg-white dark:bg-secondary-900 text-primary-700 border-x border-t border-secondary-200/60 dark:border-secondary-800/60'
                : 'text-secondary-600 hover:text-primary-700',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div>
        {tabs.map((t) => (
          <div key={t.id} className={active === t.id ? 'block' : 'hidden'}>
            {t.content}
          </div>
        ))}
      </div>
    </div>
  )
}





