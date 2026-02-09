/**
 * LiveActivityFeed - Scrolling feed of real-time events (newest at top).
 *
 * Features:
 * - Event cards with icon by type, timestamp, summary
 * - Filter chips: All, Pipeline, Agents, Alerts, Outreach
 * - Auto-scroll toggle (pauses when user scrolls up)
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Activity, ArrowUpRight, Bot, Bell, BarChart3,
  Send, Zap, ChevronDown,
} from 'lucide-react'
import type { RealtimeEvent } from '../hooks/useRealtimeUpdates'

interface LiveActivityFeedProps {
  events: RealtimeEvent[]
  maxHeight?: string
}

type FilterKey = 'all' | 'pipeline' | 'agents' | 'alerts' | 'outreach' | 'metrics'

const FILTERS: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'pipeline', label: 'Pipeline' },
  { key: 'agents', label: 'Agents' },
  { key: 'alerts', label: 'Alerts' },
  { key: 'metrics', label: 'Metrics' },
]

const EVENT_ICONS: Record<string, typeof Activity> = {
  event: Zap,
  notification: Bell,
  metric_update: BarChart3,
  pipeline_move: ArrowUpRight,
  agent_status: Bot,
}

const EVENT_COLORS: Record<string, string> = {
  event: 'text-blue-500 bg-blue-50 dark:bg-blue-900/30',
  notification: 'text-amber-500 bg-amber-50 dark:bg-amber-900/30',
  metric_update: 'text-green-500 bg-green-50 dark:bg-green-900/30',
  pipeline_move: 'text-purple-500 bg-purple-50 dark:bg-purple-900/30',
  agent_status: 'text-cyan-500 bg-cyan-50 dark:bg-cyan-900/30',
}

function matchesFilter(event: RealtimeEvent, filter: FilterKey): boolean {
  if (filter === 'all') return true
  if (filter === 'pipeline') return event.type === 'pipeline_move'
  if (filter === 'agents') return event.type === 'agent_status'
  if (filter === 'alerts') return event.type === 'notification'
  if (filter === 'metrics') return event.type === 'metric_update'
  return true
}

function formatEventSummary(event: RealtimeEvent): string {
  const d = event.data || {}
  switch (event.type) {
    case 'notification':
      return `[${d.level || 'info'}] ${d.title || ''}: ${d.message || ''}`
    case 'metric_update':
      return `${d.metric_name}: ${d.value}${d.delta ? ` (${Number(d.delta) > 0 ? '+' : ''}${d.delta})` : ''}`
    case 'pipeline_move':
      return `Deal ${d.deal_id}: ${d.from_stage} → ${d.to_stage}`
    case 'agent_status':
      return `${d.agent_name}: ${d.status}${d.last_output ? ` — ${String(d.last_output).slice(0, 80)}` : ''}`
    case 'event':
      return `${d.event_type || 'event'}: ${d.payload ? JSON.stringify(d.payload).slice(0, 100) : ''}`
    default:
      return JSON.stringify(d).slice(0, 120)
  }
}

function formatTime(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}

export function LiveActivityFeed({ events, maxHeight = '500px' }: LiveActivityFeedProps) {
  const [filter, setFilter] = useState<FilterKey>('all')
  const [autoScroll, setAutoScroll] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  const filtered = events.filter((e) => matchesFilter(e, filter))

  // Auto-scroll to top when new events arrive (if enabled)
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = 0
    }
  }, [events.length, autoScroll])

  // Detect manual scroll (pause auto-scroll)
  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return
    setAutoScroll(scrollRef.current.scrollTop < 10)
  }, [])

  return (
    <div className="flex flex-col">
      {/* Filter bar */}
      <div className="flex items-center gap-1.5 mb-3">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
              filter === f.key
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
            }`}
          >
            {f.label}
          </button>
        ))}

        {!autoScroll && (
          <button
            onClick={() => {
              setAutoScroll(true)
              if (scrollRef.current) scrollRef.current.scrollTop = 0
            }}
            className="ml-auto flex items-center gap-1 px-2 py-1 rounded text-xs text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30"
          >
            <ChevronDown className="h-3 w-3" />
            Resume auto-scroll
          </button>
        )}
      </div>

      {/* Event list */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="overflow-y-auto space-y-1.5"
        style={{ maxHeight }}
      >
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-sm text-slate-400">
            No events yet. Events will appear here in real time.
          </div>
        ) : (
          filtered.map((event, i) => {
            const Icon = EVENT_ICONS[event.type] || Activity
            const colorClass = EVENT_COLORS[event.type] || 'text-slate-500 bg-slate-50 dark:bg-slate-800'

            return (
              <div
                key={`${event.timestamp}-${i}`}
                className="flex items-start gap-2.5 px-3 py-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700/50 hover:border-slate-200 dark:hover:border-slate-600 transition-colors"
              >
                <div className={`p-1.5 rounded-md ${colorClass}`}>
                  <Icon className="h-3.5 w-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-slate-700 dark:text-slate-300 truncate">
                    {formatEventSummary(event)}
                  </p>
                </div>
                <span className="text-[10px] text-slate-400 whitespace-nowrap flex-shrink-0">
                  {formatTime(event.timestamp)}
                </span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
