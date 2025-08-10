import { ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title?: string; children: ReactNode }) {
  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/30" onClick={onClose} />
          <motion.div
            className="relative w-full max-w-2xl mx-4 rounded-xl bg-white dark:bg-secondary-900 border border-secondary-200/60 dark:border-secondary-800/60 shadow-soft"
            initial={{ y: 12, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 12, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            <div className="px-6 py-4 border-b border-secondary-200/60 dark:border-secondary-800/60 flex items-center justify-between">
              <h3 className="font-medium text-secondary-800 dark:text-secondary-100">{title}</h3>
              <button onClick={onClose} className="h-8 px-3 rounded-md border border-secondary-200 dark:border-secondary-800">✕</button>
            </div>
            <div className="p-6">{children}</div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  )
}





