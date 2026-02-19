# Data Architecture Explorer V6 Upgrade Plan

## Context

The Intelligent DB Enhancement Pipeline just transformed the unified federal contracts database with 63K graph entities (was ~2K), 16K relationships, 13 domain tags, 63K quality scores, 53K sentiment scores, and 19.7K program summaries. The current V5 dashboard has 4 separate graph pages with overlapping functionality, none of which surface these new data products. This plan upgrades the visualization layer to expose the intelligent DB capabilities.

**Problem:** 4 graph pages with partial overlap, no domain filtering/coloring, no quality score visualization, no competition network, hardcoded 500-node limit, only 2 node types (contact/program) when the graph now has 4 (+ contractor, job).

---

## Track 1: API Endpoint Upgrades (`Engine8_Knowledge/api.py`)

### 1A. Upgrade `/graph/data` endpoint (~line 3986)
- Add query params: `node_types`, `domain_filter`, `min_quality`, `include_quality`, `include_domain_tags`
- Pull Contractor and Job entities from `bd_graph.db` via `BDKnowledgeGraph`
- Add PRIMES_ON, COMPETES_WITH, HAS_OPENING edges from graph relationships
- Add `type` field to all edges (currently missing)
- Raise default limit from 500 to 800

### 1B. New `/graph/competition` endpoint
- Returns contractor nodes + program nodes with COMPETES_WITH and PRIMES_ON edges
- Contractors sized by `program_count`, edges weighted by `shared_programs`
- Optional `program_filter` param

### 1C. New `/graph/domain-tags` endpoint
- Returns `{"tags": [{"tag": "ISR", "count": 234}, ...]}` from programs table

### 1D. New `/graph/quality-stats` endpoint
- Returns quality score distribution: overall mean/median, per-entity-type breakdown, histogram buckets (0-20, 20-40, 40-60, 60-80, 80-100)

---

## Track 2: TypeScript Type & Service Updates

### 2A. Extend types in `dashboard/src/pages/GraphExplorer.tsx`
```typescript
type NodeType = 'contact' | 'program' | 'contractor' | 'job';  // was 2, now 4
type ColorBy = 'type' | 'priority' | 'tier' | 'program' | 'domain' | 'quality';  // +2 new

// Add to GraphNode:
data_quality_score?: number;   // 0-100
domain_tags?: string[];        // ['ISR', 'Cyber']
headquarters?: string;         // contractor
bd_score?: number;             // job

// Add to GraphEdge:
type?: string;  // 'WORKS_ON' | 'PRIMES_ON' | 'COMPETES_WITH' | etc.
```

### 2B. New interfaces in `dashboard/src/services/hubApi.ts`
- `CompetitionGraphData` — nodes (contractor/program), edges (COMPETES_WITH/PRIMES_ON)
- `DomainTagSummary` — tag name + count array
- `EnrichedGraphData` / `EnrichedGraphNode` / `EnrichedGraphEdge`

### 2C. New methods on `HubApiClient` class
- `getEnrichedGraphData(params)` → `GET /graph/data` with new params
- `getCompetitionGraph(programFilter, limit)` → `GET /graph/competition`
- `getDomainTagSummary()` → `GET /graph/domain-tags`

### 2D. New hooks in `dashboard/src/hooks/useHubApi.ts`
- `useCompetitionGraph(programFilter?)` — query state hook
- `useDomainTags()` — query state hook

---

## Track 3: GraphExplorer.tsx Upgrades (highest impact)

### 3A. New color maps
- `DOMAIN_COLORS` — 13 defense domains mapped to distinct colors
- `getQualityColor(score)` — green(80+) → lime(60+) → amber(40+) → orange(20+) → red

### 3B. Extend `getNodeColor` + `getNodeSize`
- Handle `colorBy === 'domain'` → first domain tag color
- Handle `colorBy === 'quality'` → quality score gradient
- Handle `node.type === 'contractor'` (size 28) and `'job'` (size 14)

### 3C. Upgrade fetch logic
- Replace hardcoded `fetch('/graph/data?limit=500')` with parameterized call
- Include `include_quality=true`, `include_domain_tags=true`
- Pass `node_types` and `domain_filter` from new UI state

### 3D. New toolbar controls
- Node type toggle buttons (contact/program/contractor/job)
- Domain filter dropdown (populated from `/graph/domain-tags`)
- Two new `<option>` in color-by select: "Color: Domain", "Color: Quality Score"

### 3E. Extended NodeDetailPanel
- Quality score progress bar with color-coded fill
- Domain tag chips (colored badges)
- Contractor-specific fields (headquarters, program_count)

### 3F. Dynamic legend
- Updates based on current `colorBy` mode
- Shows domain tag legend, quality score ranges, or node type shapes

---

## Track 4: Competition Network View (new tab in GraphExplorer)

Add as a view mode toggle inside `GraphExplorer.tsx` — no new page.

### 4A. New state
- `viewMode: 'explore' | 'competition'` — toggle at top of toolbar
- `competitionData`, `competitionLoading`, `programFilter`

### 4B. Competition graph rendering (G6)
- Contractor nodes sized by `program_count`
- Program nodes as small diamonds
- COMPETES_WITH edges: orange, width proportional to `shared_programs`
- PRIMES_ON edges: thin grey
- Click contractor → show programs they compete on

### 4C. Competition toolbar
- Program name filter input
- Info text: "Orange edges = competition, Size = program count"

---

## Track 5: GraphAnalytics.tsx Upgrades

### 5A. Replace Graph RAG tab with Smart Query tab
- Swap `tab === 'rag'` with `tab === 'smart'`
- Use existing `useSmartQuery` hook from `useHubApi.ts`
- Show `query_type` badge, `systems_used` array, answer + sources
- Add suggested prompts for graph-specific questions

### 5B. Add Data Quality tab (6th tab)
- Fetch from new `/graph/quality-stats` endpoint
- Render distribution histogram using CSS bars (matching existing `scoreBar` pattern)
- Per-entity-type breakdown cards: Contact/Program/Contractor
- Summary stats: mean, median, p25, p75

---

## Track 6: Consolidation

### 6A. Deprecate `KnowledgeGraph.tsx` → redirect to `RelationshipExplorer.tsx`
- In `App.tsx`, change `case 'knowledgegraph'` to render `<RelationshipExplorer>` instead
- `KnowledgeGraph.tsx` (537 lines) overlaps heavily with `RelationshipExplorer.tsx` — both use react-force-graph-2d for program ecosystem/contact network views
- Keep file for now, just redirect the route — remove in future cleanup

---

## Files to Modify (in order)

| # | File | Change |
|---|------|--------|
| 1 | `Engine8_Knowledge/api.py` | Upgrade `/graph/data`, add 3 new endpoints |
| 2 | `dashboard/src/services/hubApi.ts` | Add interfaces + 3 client methods |
| 3 | `dashboard/src/hooks/useHubApi.ts` | Add 2 hooks |
| 4 | `dashboard/src/pages/GraphExplorer.tsx` | New color modes, 4 node types, domain filter, competition view, extended detail panel |
| 5 | `dashboard/src/pages/GraphAnalytics.tsx` | Replace RAG→Smart Query, add Data Quality tab |
| 6 | `dashboard/src/App.tsx` | Redirect knowledgegraph → RelationshipExplorer |

## Key Files to Reuse
- `Engine8_Knowledge/graph/bd_knowledge_graph.py` — `get_entities_by_type()`, `get_relationships_by_type()` for new API endpoints
- `dashboard/src/hooks/useHubApi.ts` — `useSmartQuery` hook already exists, reuse for Smart Query tab
- `dashboard/src/services/hubApi.ts` — `HubApiClient` class pattern: `buildQueryString()` + `this.fetch<T>()`

## Verification
1. Start API: `python Engine8_Knowledge/api.py` → test new endpoints with curl
2. `curl http://localhost:8100/graph/data?include_quality=true&include_domain_tags=true&limit=50` → should return 4 node types with quality/domain fields
3. `curl http://localhost:8100/graph/competition` → should return contractor competition network
4. `curl http://localhost:8100/graph/domain-tags` → should return 13 domain tags with counts
5. `curl http://localhost:8100/graph/quality-stats` → should return score distribution
6. Start dashboard: `npm run dev` in dashboard/ → navigate to Graph Explorer
7. Verify: node type toggles work, domain filter dropdown populated, "Color: Domain" and "Color: Quality Score" modes render correctly
8. Verify: Competition view tab shows orange COMPETES_WITH edges between contractors
9. Navigate to Graph Analytics → Smart Query tab works, Data Quality tab shows distribution
10. Navigate to Knowledge Graph (sidebar) → renders RelationshipExplorer instead
