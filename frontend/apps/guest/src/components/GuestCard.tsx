import { User, Crown } from 'lucide-react'
import { Badge } from '@smartbook/ui'
import { format, parseISO } from 'date-fns'
import type { Guest } from '@smartbook/types'

interface GuestCardProps {
  guest: Guest
}

export function GuestCard({ guest }: GuestCardProps) {
  const isLeader = guest.role === 'leader'
  const age = Math.floor(
    (Date.now() - new Date(guest.date_of_birth).getTime()) / (1000 * 60 * 60 * 24 * 365.25)
  )

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
            {isLeader ? (
              <Crown className="w-5 h-5 text-blue-700" />
            ) : (
              <User className="w-5 h-5 text-blue-700" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-gray-900 truncate">
                {guest.first_name} {guest.last_name}
              </h3>
              {isLeader && <Badge variant="info">Leader</Badge>}
            </div>
            <div className="space-y-1">
              <p className="text-sm text-gray-600">
                {guest.sex === 'M' ? 'Male' : 'Female'}, {age} years old
              </p>
              <p className="text-xs text-gray-500">
                Born: {format(parseISO(guest.date_of_birth), 'dd/MM/yyyy')}
              </p>
              {guest.document_number && (
                <p className="text-xs text-gray-500">
                  Doc: {guest.document_type?.toUpperCase()} - {guest.document_number}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
