/**
 * RealtimeIndicator - Connection status dot in the dashboard header.
 *
 * Green dot + "Live" when connected
 * Yellow dot + "Reconnecting..." during backoff
 * Red dot + "Offline" when disconnected
 * Shows event throughput: "12 events/min"
 */

interface RealtimeIndicatorProps {
  isConnected: boolean
  connectionType: 'websocket' | 'sse' | 'none'
  eventsPerMinute: number
}

export function RealtimeIndicator({
  isConnected,
  connectionType,
  eventsPerMinute,
}: RealtimeIndicatorProps) {
  const dotColor = isConnected
    ? 'bg-emerald-500'
    : connectionType === 'none'
      ? 'bg-red-500'
      : 'bg-yellow-500'

  const label = isConnected
    ? 'Live'
    : connectionType === 'none'
      ? 'Offline'
      : 'Reconnecting...'

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs">
      <span className="relative flex h-2.5 w-2.5">
        {isConnected && (
          <span className={`absolute inline-flex h-full w-full rounded-full ${dotColor} opacity-75 animate-ping`} />
        )}
        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${dotColor}`} />
      </span>
      <span className="font-medium text-slate-700 dark:text-slate-300">{label}</span>
      {isConnected && (
        <>
          <span className="text-slate-400 dark:text-slate-500">|</span>
          <span className="text-slate-500 dark:text-slate-400">
            {eventsPerMinute} evt/min
          </span>
          {connectionType === 'sse' && (
            <span className="text-amber-500 text-[10px]">(SSE)</span>
          )}
        </>
      )}
    </div>
  )
}
