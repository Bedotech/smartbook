import React from 'react'
import { cn } from '@smartbook/utils'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn('bg-white rounded-lg shadow p-6', className)}
      {...props}
    >
      {children}
    </div>
  )
}
