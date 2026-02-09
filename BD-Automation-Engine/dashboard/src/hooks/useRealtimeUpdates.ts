/**
 * useRealtimeUpdates - React hook for WebSocket real-time dashboard updates.
 *
 * - WebSocket connection with exponential backoff auto-reconnect (1s-30s)
 * - Falls back to SSE after 3 failed WebSocket attempts
 * - Event buffer of last 100 events
 * - Notification queue for toast display
 */

import { useState, useEffect, useCallback, useRef } from 'react'

export interface RealtimeEvent {
  type: string
  data: Record<string, unknown>
  timestamp: string
}

export interface RealtimeNotification {
  id: string
  level: string
  title: string
  message: string
  timestamp: string
}

interface RealtimeState {
  events: RealtimeEvent[]
  notifications: RealtimeNotification[]
  isConnected: boolean
  connectionType: 'websocket' | 'sse' | 'none'
  eventsPerMinute: number
}

const MAX_EVENTS = 100
const MAX_NOTIFICATIONS = 20
const WS_MAX_RETRIES = 3
const BACKOFF_BASE = 1000
const BACKOFF_MAX = 30000

export function useRealtimeUpdates(): RealtimeState {
  const [events, setEvents] = useState<RealtimeEvent[]>([])
  const [notifications, setNotifications] = useState<RealtimeNotification[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [connectionType, setConnectionType] = useState<'websocket' | 'sse' | 'none'>('none')
  const [eventsPerMinute, setEventsPerMinute] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const sseRef = useRef<EventSource | null>(null)
  const retriesRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const eventTimestampsRef = useRef<number[]>([])

  // Track events/minute
  const recordEvent = useCallback(() => {
    const now = Date.now()
    eventTimestampsRef.current.push(now)
    // Keep only last 60 seconds
    const cutoff = now - 60000
    eventTimestampsRef.current = eventTimestampsRef.current.filter((t) => t > cutoff)
    setEventsPerMinute(eventTimestampsRef.current.length)
  }, [])

  const handleMessage = useCallback(
    (raw: string) => {
      try {
        const msg = JSON.parse(raw) as RealtimeEvent
        if (msg.type === 'ping' || msg.type === 'welcome') return

        recordEvent()

        setEvents((prev) => {
          const next = [msg, ...prev]
          return next.length > MAX_EVENTS ? next.slice(0, MAX_EVENTS) : next
        })

        if (msg.type === 'notification' && msg.data) {
          const d = msg.data as { level?: string; title?: string; message?: string }
          setNotifications((prev) => {
            const notif: RealtimeNotification = {
              id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
              level: d.level || 'info',
              title: d.title || 'Notification',
              message: d.message || '',
              timestamp: msg.timestamp || new Date().toISOString(),
            }
            const next = [notif, ...prev]
            return next.length > MAX_NOTIFICATIONS ? next.slice(0, MAX_NOTIFICATIONS) : next
          })
        }
      } catch {
        // Ignore parse errors
      }
    },
    [recordEvent],
  )

  // ── WebSocket connection ─────────────────────────────

  const connectWS = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setConnectionType('websocket')
        retriesRef.current = 0
      }

      ws.onmessage = (event) => {
        handleMessage(event.data)
        // Respond to pings
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }))
          }
        } catch { /* ignore */ }
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null

        retriesRef.current += 1
        if (retriesRef.current <= WS_MAX_RETRIES) {
          const delay = Math.min(BACKOFF_BASE * Math.pow(2, retriesRef.current - 1), BACKOFF_MAX)
          reconnectTimerRef.current = setTimeout(connectWS, delay)
        } else {
          // Fall back to SSE
          connectSSE()
        }
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      retriesRef.current += 1
      if (retriesRef.current > WS_MAX_RETRIES) {
        connectSSE()
      }
    }
  }, [handleMessage])

  // ── SSE fallback ─────────────────────────────────────

  const connectSSE = useCallback(() => {
    if (sseRef.current) return

    try {
      const es = new EventSource('/sse/events')
      sseRef.current = es

      es.onopen = () => {
        setIsConnected(true)
        setConnectionType('sse')
      }

      es.onmessage = (event) => {
        handleMessage(event.data)
      }

      // Listen for typed events
      for (const eventType of ['event', 'notification', 'metric_update', 'pipeline_move', 'agent_status']) {
        es.addEventListener(eventType, (event) => {
          handleMessage((event as MessageEvent).data)
        })
      }

      es.onerror = () => {
        setIsConnected(false)
        sseRef.current?.close()
        sseRef.current = null
        // Retry SSE after delay
        reconnectTimerRef.current = setTimeout(connectSSE, 5000)
      }
    } catch {
      setConnectionType('none')
    }
  }, [handleMessage])

  // ── Lifecycle ────────────────────────────────────────

  useEffect(() => {
    connectWS()

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      wsRef.current?.close()
      sseRef.current?.close()
    }
  }, [connectWS])

  return { events, notifications, isConnected, connectionType, eventsPerMinute }
}
