/**
 * KPI Charts Components
 *
 * Reusable chart components for Executive Summary, Data Quality,
 * and Job Intelligence pages using Recharts.
 */

import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Activity, Database, TrendingUp, Users, AlertTriangle, CheckCircle2 } from 'lucide-react'

const TIER_COLORS = ['#7c3aed', '#2563eb', '#0891b2', '#059669', '#ca8a04', '#6b7280']

interface CollectionHealth {
  name: string
  vectors: number
  status: string
}

// =========================================
// Contact Tier Distribution Chart
// =========================================

interface TierDistributionProps {
  contacts: Record<string, unknown[]>
}

export function TierDistributionChart({ contacts }: TierDistributionProps) {
  const data = Object.entries(contacts).map(([tier, list]) => ({
    tier: `Tier ${tier}`,
    count: list.length,
  })).sort((a, b) => a.tier.localeCompare(b.tier))

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Users className="h-4 w-4" />
          Contact Tier Distribution
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="tier" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map((_, idx) => (
                <Cell key={idx} fill={TIER_COLORS[idx] || '#6b7280'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

// =========================================
// Pipeline Metrics Chart
// =========================================

interface PipelineMetricsProps {
  totalJobs: number
  totalPrograms: number
  totalContacts: number
  highPriorityPrograms: number
}

export function PipelineMetricsChart({ totalJobs, totalPrograms, totalContacts, highPriorityPrograms }: PipelineMetricsProps) {
  const data = [
    { name: 'Jobs', value: totalJobs, fill: '#3b82f6' },
    { name: 'Programs', value: totalPrograms, fill: '#8b5cf6' },
    { name: 'Contacts', value: totalContacts, fill: '#06b6d4' },
    { name: 'High Priority', value: highPriorityPrograms, fill: '#ef4444' },
  ]

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          Pipeline Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              outerRadius={80}
              label={({ name, value }) => `${name}: ${value}`}
              dataKey="value"
            >
              {data.map((entry, idx) => (
                <Cell key={idx} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

// =========================================
// Collection Health Chart (from BD Hub API)
// =========================================

export function CollectionHealthChart() {
  const [collections, setCollections] = useState<CollectionHealth[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchHealth() {
      try {
        const res = await fetch('http://localhost:8100/collections/stats', {
          signal: AbortSignal.timeout(5000),
        })
        if (res.ok) {
          const data = await res.json()
          const items = (data.collections || []).map((c: Record<string, unknown>) => ({
            name: String(c.name || c.collection || ''),
            vectors: Number(c.points_count || c.vectors || 0),
            status: String(c.status || 'green'),
          }))
          setCollections(items)
        }
      } catch {
        // API not available
      } finally {
        setLoading(false)
      }
    }
    fetchHealth()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Database className="h-4 w-4" />
            Collection Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
            Loading collection data...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (collections.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Database className="h-4 w-4" />
            Collection Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-sm text-muted-foreground">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Knowledge API not available (port 8100)
          </div>
        </CardContent>
      </Card>
    )
  }

  const totalVectors = collections.reduce((sum, c) => sum + c.vectors, 0)

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Database className="h-4 w-4" />
          Collection Health
          <Badge variant="secondary" className="ml-auto">
            {totalVectors.toLocaleString()} vectors
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={collections} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={120} />
            <Tooltip formatter={(value: number) => value.toLocaleString()} />
            <Bar dataKey="vectors" fill="#6366f1" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

// =========================================
// Weekly Outreach Activity Chart
// =========================================

export function WeeklyOutreachChart() {
  // Simulated weekly data — in production, this comes from the API
  const data = [
    { week: 'W1', emails: 12, calls: 8, meetings: 3 },
    { week: 'W2', emails: 18, calls: 12, meetings: 5 },
    { week: 'W3', emails: 15, calls: 10, meetings: 4 },
    { week: 'W4', emails: 22, calls: 15, meetings: 7 },
  ]

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Weekly Outreach Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="week" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="emails" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
            <Area type="monotone" dataKey="calls" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
            <Area type="monotone" dataKey="meetings" stackId="1" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.6} />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

// =========================================
// System Health Status
// =========================================

export function SystemHealthCards() {
  const [health, setHealth] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function checkHealth() {
      const services: Record<string, string> = {}

      // Check Knowledge API
      try {
        const res = await fetch('http://localhost:8100/health', { signal: AbortSignal.timeout(3000) })
        services['Knowledge API'] = res.ok ? 'healthy' : 'unhealthy'
      } catch {
        services['Knowledge API'] = 'offline'
      }

      // Check Qdrant
      try {
        const res = await fetch('http://localhost:6333', { signal: AbortSignal.timeout(3000) })
        services['Qdrant DB'] = res.ok ? 'healthy' : 'unhealthy'
      } catch {
        services['Qdrant DB'] = 'offline'
      }

      // Check Neo4j
      try {
        const res = await fetch('http://localhost:7474', { signal: AbortSignal.timeout(3000) })
        services['Neo4j Graph'] = res.ok ? 'healthy' : 'unhealthy'
      } catch {
        services['Neo4j Graph'] = 'offline'
      }

      setHealth(services)
      setLoading(false)
    }
    checkHealth()
  }, [])

  if (loading) return null

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">System Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {Object.entries(health).map(([service, status]) => (
            <div key={service} className="flex items-center justify-between py-1">
              <span className="text-sm">{service}</span>
              <Badge variant={status === 'healthy' ? 'default' : 'destructive'}>
                {status === 'healthy' ? (
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                ) : (
                  <AlertTriangle className="h-3 w-3 mr-1" />
                )}
                {status}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
