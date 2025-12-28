import { CheckCircle, Circle } from 'lucide-react'

interface ProgressBarProps {
  current: number
  total: number
  hasLeader: boolean
}

export function ProgressBar({ current, total, hasLeader }: ProgressBarProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div className="space-y-3">
      {/* Textual Progress */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {hasLeader ? (
            <CheckCircle className="w-5 h-5 text-emerald-600" />
          ) : (
            <Circle className="w-5 h-5 text-gray-300" />
          )}
          <span className="text-sm font-medium text-gray-900">
            {current} of {total} guests entered
          </span>
        </div>
        <span className="text-sm font-bold text-blue-600">{percentage}%</span>
      </div>

      {/* Visual Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className="bg-gradient-to-r from-blue-600 to-blue-500 h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Status Message */}
      <div className="text-xs text-gray-600">
        {!hasLeader && 'Add group leader to continue'}
        {hasLeader && current < total &&
          `${total - current} more ${total - current === 1 ? 'guest' : 'guests'} to add`}
        {hasLeader && current >= total && 'All guests entered! Ready to complete.'}
      </div>
    </div>
  )
}
