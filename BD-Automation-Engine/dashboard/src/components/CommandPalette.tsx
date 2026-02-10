/**
 * Command Palette - Ctrl+K / Cmd+K global search
 *
 * Searches across contacts, programs, jobs, opportunities,
 * and all dashboard pages. Uses BD Hub /ask/smart for AI search.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Users, Building2, Briefcase, Search,
  BarChart3, MapPin, Shield, Brain, Sparkles, FileText,
  Network, Target, Phone, Bot, Database, Activity,
  Settings, Loader2,
} from 'lucide-react'
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
} from '@/components/ui/command'
import type { TabId } from '../types'

interface CommandPaletteProps {
  onNavigate: (tab: TabId) => void
  onSearch?: (query: string) => void
}

interface AIResult {
  answer: string
  sources: { collection: string; text: string }[]
}

const PAGES: { id: TabId; label: string; icon: typeof Users; keywords: string[] }[] = [
  { id: 'executive', label: 'Executive Summary', icon: BarChart3, keywords: ['dashboard', 'overview', 'kpi', 'summary'] },
  { id: 'contacts', label: 'Contacts', icon: Users, keywords: ['people', 'contacts', 'tier', 'name'] },
  { id: 'programs', label: 'Programs', icon: Shield, keywords: ['programs', 'contracts', 'federal', 'dcgs'] },
  { id: 'jobs', label: 'Jobs Pipeline', icon: Briefcase, keywords: ['jobs', 'postings', 'hiring', 'openings'] },
  { id: 'intelligence', label: 'Job Intelligence', icon: Brain, keywords: ['analysis', 'intelligence', 'trends'] },
  { id: 'contractors', label: 'Contractors', icon: Building2, keywords: ['companies', 'primes', 'gdit', 'leidos'] },
  { id: 'locations', label: 'Locations', icon: MapPin, keywords: ['sites', 'bases', 'locations'] },
  { id: 'opportunities', label: 'Opportunities', icon: Target, keywords: ['pipeline', 'deals', 'bd'] },
  { id: 'contactorgchart', label: 'Contact Org Chart', icon: Network, keywords: ['hierarchy', 'org', 'chart', 'tiers'] },
  { id: 'primeorgchart', label: 'Prime Org Chart', icon: Network, keywords: ['prime', 'org', 'relationships'] },
  { id: 'callintelligence', label: 'Call Intelligence', icon: Phone, keywords: ['calls', 'notes', 'humint'] },
  { id: 'playbook', label: 'BD Playbook', icon: FileText, keywords: ['playbook', 'strategy', 'outreach'] },
  { id: 'enrichment', label: 'Enrichment', icon: Sparkles, keywords: ['enrich', 'enhance', 'data'] },
  { id: 'mindmap', label: 'Mind Map', icon: Network, keywords: ['mind', 'map', 'visual', 'graph'] },
  { id: 'smartquery', label: 'Smart Query', icon: Brain, keywords: ['ai', 'search', 'rag', 'ask'] },
  { id: 'knowledgegraph', label: 'Knowledge Graph', icon: Database, keywords: ['graph', 'knowledge', 'vectors'] },
  { id: 'agents', label: 'AI Agents', icon: Bot, keywords: ['agents', 'crew', 'ai', 'automation'] },
  { id: 'memory', label: 'Memory Context', icon: Brain, keywords: ['memory', 'mem0', 'context'] },
  { id: 'outreach', label: 'Outreach Manager', icon: Target, keywords: ['outreach', 'sequence', 'email', 'cadence'] },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, keywords: ['analytics', 'charts', 'metrics', 'trends'] },
  { id: 'qadashboard', label: 'QA Dashboard', icon: Activity, keywords: ['quality', 'qa', 'alerts'] },
  { id: 'pipelinestatus', label: 'Pipeline Status', icon: Activity, keywords: ['pipeline', 'status', 'engines'] },
  { id: 'dataquality', label: 'Data Quality', icon: BarChart3, keywords: ['quality', 'vectors', 'collections'] },
  { id: 'geographic', label: 'Geographic Map', icon: MapPin, keywords: ['map', 'geographic', 'location', 'leaflet'] },
  { id: 'predictions', label: 'Predictive Insights', icon: Brain, keywords: ['ml', 'predict', 'response', 'hiring', 'signals'] },
  { id: 'relationships', label: 'Relationships', icon: Network, keywords: ['relationships', 'network', 'introduction', 'path'] },
  { id: 'autonomousagents', label: 'Autonomous Agents', icon: Bot, keywords: ['autonomous', 'scheduler', 'briefing', 'enrichment'] },
  { id: 'integrations', label: 'Integrations', icon: Database, keywords: ['slack', 'crm', 'bullhorn', 'integrations', 'sync'] },
  { id: 'graphanalytics', label: 'Graph Analytics', icon: BarChart3, keywords: ['pagerank', 'influence', 'community', 'centrality', 'graph', 'rag'] },
  { id: 'realtime', label: 'Real-Time Ops', icon: Activity, keywords: ['realtime', 'websocket', 'live', 'events', 'streaming'] },
  { id: 'searchquality', label: 'Search Quality', icon: Search, keywords: ['embeddings', 'benchmark', 'acronym', 'domain', 'search', 'quality'] },
  { id: 'automation', label: 'Automation Center', icon: Activity, keywords: ['automation', 'scheduler', 'cron', 'workflow', 'claude', 'tasks'] },
  { id: 'systemoverview', label: 'System Overview', icon: BarChart3, keywords: ['system', 'overview', 'health', 'status', 'platform', 'mission', 'control'] },
  { id: 'settings', label: 'Settings', icon: Settings, keywords: ['settings', 'config', 'api'] },
]

export function CommandPalette({ onNavigate }: CommandPaletteProps) {
  const [open, setOpen] = useState(false)
  const [aiQuery, setAiQuery] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [aiResult, setAiResult] = useState<AIResult | null>(null)

  // Ctrl+K / Cmd+K or / handler
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
      // '/' to open search (unless typing in an input)
      if (e.key === '/' && !e.metaKey && !e.ctrlKey && !e.altKey) {
        const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
        if (tag !== 'input' && tag !== 'textarea' && !(e.target as HTMLElement)?.isContentEditable) {
          e.preventDefault()
          setOpen(true)
        }
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const handleSelect = useCallback(
    (tab: TabId) => {
      setOpen(false)
      setAiResult(null)
      onNavigate(tab)
    },
    [onNavigate]
  )

  const handleAiSearch = useCallback(async () => {
    if (!aiQuery.trim()) return
    setAiLoading(true)
    setAiResult(null)

    try {
      const res = await fetch('/ask/smart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: aiQuery, limit: 5 }),
        signal: AbortSignal.timeout(15000),
      })
      if (res.ok) {
        const data = await res.json()
        setAiResult({
          answer: data.answer || data.response || 'No answer found.',
          sources: data.sources || [],
        })
      }
    } catch {
      setAiResult({ answer: 'AI search unavailable. Start the Knowledge API on port 8100.', sources: [] })
    } finally {
      setAiLoading(false)
    }
  }, [aiQuery])

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput
        placeholder="Search pages, contacts, programs... (Ctrl+K)"
        value={aiQuery}
        onValueChange={setAiQuery}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && aiQuery.length > 3) {
            e.preventDefault()
            handleAiSearch()
          }
        }}
      />
      <CommandList>
        <CommandEmpty>
          <div className="flex flex-col items-center gap-2 py-4">
            <Search className="h-8 w-8 text-muted-foreground" />
            <p>No results found. Press Enter to search with AI.</p>
          </div>
        </CommandEmpty>

        {aiResult && (
          <CommandGroup heading="AI Answer">
            <div className="px-3 py-2 text-sm">
              <p className="text-foreground">{aiResult.answer}</p>
              {aiResult.sources.length > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  {aiResult.sources.length} source(s) from{' '}
                  {[...new Set(aiResult.sources.map((s) => s.collection))].join(', ')}
                </p>
              )}
            </div>
          </CommandGroup>
        )}

        {aiLoading && (
          <CommandGroup heading="Searching...">
            <div className="flex items-center gap-2 px-3 py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">Searching knowledge base...</span>
            </div>
          </CommandGroup>
        )}

        <CommandSeparator />

        <CommandGroup heading="Pages">
          {PAGES.map((page) => (
            <CommandItem
              key={page.id}
              value={`${page.label} ${page.keywords.join(' ')}`}
              onSelect={() => handleSelect(page.id)}
            >
              <page.icon className="mr-2 h-4 w-4" />
              <span>{page.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Quick Actions">
          <CommandItem value="search ai smart query" onSelect={() => handleSelect('smartquery')}>
            <Sparkles className="mr-2 h-4 w-4" />
            <span>AI Search (Smart Query)</span>
          </CommandItem>
          <CommandItem value="launch agent crew" onSelect={() => handleSelect('agents')}>
            <Bot className="mr-2 h-4 w-4" />
            <span>Launch AI Agent</span>
          </CommandItem>
          <CommandItem value="explore mind map" onSelect={() => handleSelect('mindmap')}>
            <Network className="mr-2 h-4 w-4" />
            <span>Explore Mind Map</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
