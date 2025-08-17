import * as React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "./avatar"
import { cn } from "../../lib/utils"

interface UserProps extends React.HTMLAttributes<HTMLDivElement> {
  name?: string
  description?: string
  avatarProps?: {
    src?: string
    alt?: string
    fallback?: string
  }
}

const User = React.forwardRef<HTMLDivElement, UserProps>(
  ({ className, name, description, avatarProps, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("flex items-center space-x-3", className)}
        {...props}
      >
        <Avatar className="h-8 w-8">
          <AvatarImage src={avatarProps?.src} alt={avatarProps?.alt} />
          <AvatarFallback>{avatarProps?.fallback}</AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          {name && <p className="text-sm font-medium text-gray-900">{name}</p>}
          {description && <p className="text-xs text-gray-500">{description}</p>}
        </div>
      </div>
    )
  }
)
User.displayName = "User"

export { User }