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
    const healthRes = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) })
    if (healthRes.ok) {
      const [contactsRes, programsRes, jobsRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/contacts?limit=500`).catch(() => null),
        fetch(`${API_BASE}/api/v2/programs?limit=500`).catch(() => null),
        fetch(`${API_BASE}/api/v2/jobs?limit=500`).catch(() => null),
        fetch(`${API_BASE}/stats`).catch(() => null),
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
            jobs: jobsList,
            programs: programsList,
            contacts: groupContactsByTier(contactsList),
            contractors: [],
            summary: buildSummary(contactsList, programsList, jobsList, stats),
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
  _stats: unknown,
) {
  return {
    totalJobs: jobs.length,
    openJobs: jobs.length,
    totalPrograms: programs.length,
    highPriorityPrograms: 0,
    totalContacts: contacts.length,
    tier1Contacts: 0,
    tier2Contacts: 0,
    tier3Contacts: 0,
    jobsBySource: {},
    jobsByLocation: {},
    programsByAgency: {},
    contactsByTier: {},
  }
}

/**
 * Main dashboard data hook using TanStack Query.
 *
 * Returns the same interface as useNotionDashboard for drop-in compatibility.
 */
export function useAppData() {
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-data'],
    queryFn: fetchDashboardData,
    staleTime: STALE_TIME,
    retry: 1,
  })

  return {
    data: data ?? null,
    loading: isLoading,
    error: error ? (error as Error).message : null,
    refresh: async () => {
      await queryClient.invalidateQueries({ queryKey: ['dashboard-data'] })
    },
    lastUpdated: data ? new Date() : null,
    isConfigured: true, // Always true with local fallback
  }
}
