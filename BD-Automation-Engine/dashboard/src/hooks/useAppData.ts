/**
 * TanStack Query wrapper for dashboard data fetching.
 *
 * Replaces manual useEffect-based fetching with React Query
 * for automatic caching, refetching, and devtools support.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { DashboardData } from '../types'

// Use relative URLs in dev (vite proxy) and allow override via env
const API_BASE = import.meta.env.VITE_API_BASE || ''
const STALE_TIME = 5 * 60 * 1000 // 5 minutes
const REFETCH_INTERVAL = 5 * 60 * 1000 // Auto-refresh every 5 minutes

/** Build fetch headers with optional auth token. */
function getHeaders(): HeadersInit {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const apiKey = localStorage.getItem('bd_api_key')
  const token = localStorage.getItem('bd_jwt_token')
  if (token) headers['Authorization'] = `Bearer ${token}`
  else if (apiKey) headers['X-API-Key'] = apiKey
  return headers
}

/**
 * Fetch local JSON data from public/data/ directory.
 */
async function fetchLocalJson<T>(filename: string): Promise<T> {
  const res = await fetch(`/data/${filename}`)
  if (!res.ok) throw new Error(`Failed to load ${filename}`)
  return res.json()
}

/**
 * Fetch dashboard data from BD Hub API with local JSON fallback.
 */
async function fetchDashboardData(): Promise<DashboardData> {
  // Try Hub API first
  try {
    const headers = getHeaders()
    const healthRes = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) })
    if (healthRes.ok) {
      const [contactsRes, programsRes, jobsRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/contacts?limit=500`, { headers }).catch(() => null),
        fetch(`${API_BASE}/api/v2/programs?limit=500`, { headers }).catch(() => null),
        fetch(`${API_BASE}/api/v2/jobs?limit=500`, { headers }).catch(() => null),
        fetch(`${API_BASE}/stats`, { headers }).catch(() => null),
      ])

      // If Hub API has data, use it
      if (contactsRes?.ok && programsRes?.ok) {
        const contactsData = await contactsRes.json()
        const programsData = await programsRes.json()
        const jobsData = jobsRes?.ok ? await jobsRes.json() : { jobs: [] }
        const stats = statsRes?.ok ? await statsRes.json() : null

        // API returns {contacts: [...]}, {programs: [...]}, {jobs: [...]}
        const contactsList = contactsData?.contacts || contactsData?.results || []
        const programsList = programsData?.programs || programsData?.results || []
        const jobsList = jobsData?.jobs || jobsData?.results || []

        if (contactsList.length || programsList.length) {
          return {
            jobs: jobsList as DashboardData['jobs'],
            programs: programsList as DashboardData['programs'],
            contacts: groupContactsByTier(contactsList) as DashboardData['contacts'],
            contractors: [] as DashboardData['contractors'],
            summary: buildSummary(contactsList, programsList, jobsList, stats),
            _source: 'api' as const,
          }
        }
      }
    }
  } catch {
    // Hub API not available, fall through to local data
  }

  // Fallback: load from local JSON files
  const [jobs, programs, contacts, summary] = await Promise.all([
    fetchLocalJson<unknown[]>('jobs.json'),
    fetchLocalJson<unknown[]>('programs.json'),
    fetchLocalJson<unknown[]>('contacts.json'),
    fetchLocalJson<unknown>('summary.json').catch(() => null),
  ])

  return {
    jobs: jobs as DashboardData['jobs'],
    programs: programs as DashboardData['programs'],
    contacts: (contacts ? groupContactsByTier(contacts as { tier?: number }[]) : {}) as DashboardData['contacts'],
    contractors: [],
    summary: summary as DashboardData['summary'],
    _source: 'local' as const,
  }
}

function groupContactsByTier(contacts: { tier?: number; influence_tier?: number }[]): Record<string, unknown[]> {
  const grouped: Record<string, unknown[]> = {}
  for (const c of contacts) {
    const tier = String((c as Record<string, unknown>).influence_tier || (c as Record<string, unknown>).tier || 6)
    if (!grouped[tier]) grouped[tier] = []
    grouped[tier].push(c)
  }
  return grouped
}

function buildSummary(
  contacts: unknown[],
  programs: unknown[],
  jobs: unknown[],
  stats: Record<string, unknown> | null,
): import('../types').CorrelationSummary {
  // Use Qdrant stats for real counts when available
  const qdrant = (stats as { qdrant?: Record<string, { points_count?: number }> })?.qdrant
  const totalContacts = qdrant?.contacts?.points_count || contacts.length
  const totalPrograms = qdrant?.programs?.points_count || programs.length
  const totalJobs = qdrant?.jobs?.points_count || jobs.length

  // Build contacts_by_tier from the fetched contact data
  const tierCounts: Record<string, number> = {}
  for (const c of contacts) {
    const rec = c as Record<string, unknown>
    const tier = String(rec.influence_tier || rec.tier || rec.Tier || '6')
    tierCounts[tier] = (tierCounts[tier] || 0) + 1
  }

  // Build top_programs_by_jobs from programs data
  const topPrograms = (programs as Record<string, unknown>[])
    .slice(0, 10)
    .map((p) => ({
      name: String(p['Program Name'] || p.name || p.title || 'Unknown'),
      job_count: Number(p.job_count || 0),
      contact_count: Number(p.contact_count || 0),
    }))

  // Build priority distribution from jobs
  const priorityDist: Record<string, number> = { critical: 0, high: 0, medium: 0, low: 0 }
  for (const j of jobs) {
    const rec = j as Record<string, unknown>
    const priority = String(rec.priority || rec.bd_priority || 'medium').toLowerCase()
    if (priority in priorityDist) {
      priorityDist[priority]++
    } else {
      priorityDist['medium']++
    }
  }

  return {
    generated_at: new Date().toISOString(),
    statistics: {
      total_jobs: totalJobs,
      total_programs: totalPrograms,
      total_contacts: totalContacts,
      total_contractors: 0,
      jobs_matched_to_programs: 0,
      jobs_matched_to_contacts: 0,
      contacts_matched_to_programs: 0,
      contacts_with_relevant_jobs: 0,
      match_rates: {
        jobs_to_programs: 0,
        jobs_to_contacts: 0,
        contacts_to_programs: 0,
      },
    },
    priority_distribution: priorityDist,
    contacts_by_tier: tierCounts,
    top_programs_by_jobs: topPrograms,
  }
}

/**
 * Main dashboard data hook using TanStack Query.
 *
 * Returns the same interface as useNotionDashboard for drop-in compatibility.
 */
export function useAppData() {
  const queryClient = useQueryClient()

  const { data, isLoading, error, dataUpdatedAt } = useQuery({
    queryKey: ['dashboard-data'],
    queryFn: fetchDashboardData,
    staleTime: STALE_TIME,
    refetchInterval: REFETCH_INTERVAL,
    refetchIntervalInBackground: false,
    retry: 1,
  })

  return {
    data: data ?? null,
    loading: isLoading,
    error: error ? (error as Error).message : null,
    refresh: async () => {
      await queryClient.invalidateQueries({ queryKey: ['dashboard-data'] })
    },
    lastUpdated: dataUpdatedAt ? new Date(dataUpdatedAt) : null,
    isConfigured: true, // Always true with local fallback
    dataSource: data?._source as 'api' | 'local' | undefined,
  }
}
