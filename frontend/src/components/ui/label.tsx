import * as React from 'react'
import { cn } from '../../lib/utils'

export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(({ className, ...props }, ref) => (
  <label
    ref={ref}
    className={cn('text-sm text-secondary-600 dark:text-secondary-300', className)}
    {...props}
  />
))
Label.displayName = 'Label'

export { Label }








