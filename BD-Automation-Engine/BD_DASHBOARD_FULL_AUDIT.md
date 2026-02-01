# BD Intelligence Dashboard - Comprehensive Audit Report

**Audit Date:** 2026-02-01
**Auditor:** Claude Opus 4.5
**Scope:** Full architectural, code quality, and strategic assessment
**Purpose:** Pre-rebuild analysis for QA review and strategic planning

---

## EXECUTIVE SUMMARY

The BD Intelligence Dashboard is a React 19 + Vite 7 application with **significant architectural debt** that has accumulated through iterative development. While the dashboard has good foundational components, it suffers from:

1. **Fragmented data architecture** - Multiple competing patterns (3 data adapters, 2 hooks systems, static JSON)
2. **No routing infrastructure** - 25+ pages managed via switch statement
3. **Type inconsistencies** - Same entities typed differently across components
4. **Missing production essentials** - No error boundaries, no testing, no performance optimization
5. **File clutter** - 50+ temp files in root, dead code, duplicate logic

**Recommendation:** A structured refactoring rather than complete rewrite. The core components are sound.

---

## SECTION 1: ARCHITECTURE ANALYSIS

### 1.1 Directory Structure

```
dashboard/
├── src/
│   ├── components/          # 20 components
│   │   ├── hub/             # Hub API components (3)
│   │   ├── mindmap/         # Mind map components (8)
│   │   └── ui/              # UI primitives (4)
│   ├── configs/             # Node configurations (1)
│   ├── contexts/            # React contexts (2)
│   ├── data/                # Data providers & adapters
│   │   └── adapters/        # 3 adapters: local, notion, hub
│   ├── design_intelligence/ # Design system (2)
│   ├── hooks/               # 9 custom hooks
│   ├── pages/               # 25 page components
│   ├── services/            # 6 service modules
│   ├── stores/              # Zustand stores (1)
│   ├── tests/               # 1 test file
│   └── types/               # Type definitions (2)
├── public/
│   └── data/                # 27 static JSON files
└── dist/                    # Build output
```

### 1.2 Technology Stack

| Layer | Technology | Version | Assessment |
|-------|-----------|---------|------------|
| Framework | React | 19.2.0 | Current |
| Build Tool | Vite | 7.2.4 | Current |
| Language | TypeScript | 5.9.3 | Current |
| Styling | TailwindCSS | 4.1.18 | Current |
| State Mgmt | Zustand | 5.0.10 | Current |
| Charts | Recharts | 3.6.0 | Current |
| Visualization | react-force-graph-2d | 1.29.0 | Current |
| Icons | lucide-react | 0.562.0 | Current |
| Date | date-fns | 4.1.0 | Current |

**Verdict:** Modern stack with latest versions. No version debt.

---

## SECTION 2: CRITICAL ISSUES (Must Fix)

### 2.1 CRITICAL: No Error Boundaries

**Location:** Entire application
**Impact:** Any component error crashes entire app
**Risk Level:** HIGH

```tsx
// Current: App.tsx has no error boundary
function App() {
  // If any child throws, entire app crashes
  return (
    <div className="h-screen flex overflow-hidden">
      <Sidebar ... />
      <main>{renderContent()}</main>  {/* No protection */}
    </div>
  );
}
```

**Fix Required:**
- Add root ErrorBoundary component
- Add per-page error boundaries
- Implement error reporting

---

### 2.2 CRITICAL: Fragmented Data Architecture

**Problem:** Three different data-loading paradigms compete:

| Pattern | Location | Used By |
|---------|----------|---------|
| `useNotionDashboard()` | hooks/useNotionData.ts | App.tsx (primary) |
| `DataProvider` context | data/DataProvider.tsx | Not integrated |
| Direct adapter calls | services/*.ts | Some pages |

**Conflicts:**
1. `useNotionDashboard()` loads static JSON despite its name
2. `DataProvider` exists but isn't wrapped around app
3. Hub adapter duplicates logic from `hubApi.ts` service

**Evidence:**
```tsx
// App.tsx uses useNotionDashboard (static JSON)
const { data, loading, error, refresh, lastUpdated, isConfigured } = useNotionDashboard();

// But DataProvider.tsx defines useData() which is never used
export function useData(): DataContextValue { ... }

// And pages sometimes call hubApiClient directly
const { data: hubStats } = useHubStats(60000);
```

---

### 2.3 CRITICAL: Type Inconsistencies

**Problem:** Same entity typed differently across codebase

```typescript
// App.tsx expects contacts as Record<string, Contact[]>
contacts: Record<string, Contact[]>

// But DataProvider returns contacts as Contact[]
interface DashboardDataState {
  contacts: Contact[];
  contactsByTier: Record<number, Contact[]>;  // Separate field
}

// And DashboardData type has yet another pattern
interface DashboardData {
  contacts: Record<string, Contact[]>;  // Different from DataState
}
```

**Result:** Runtime errors when components receive wrong shape.

---

### 2.4 CRITICAL: No Routing Library

**Problem:** 25+ pages managed via switch statement

```tsx
// App.tsx:128-262 - Giant switch statement
const renderContent = () => {
  switch (activeTab) {
    case 'executive': return <ExecutiveSummary ... />;
    case 'intelligence': return <JobIntelligence ... />;
    case 'jobs': return <JobsPipeline ... />;
    // ... 22 more cases
    default: return null;
  }
};
```

**Issues:**
1. No URL-based navigation (can't share links)
2. No browser back/forward support
3. No code splitting (all pages loaded upfront)
4. No nested routes support
5. Tab state lost on refresh

---

### 2.5 CRITICAL: Static Data Dependency

**Location:** `public/data/` - 27 JSON files
**Problem:** Dashboard relies on pre-generated static files

| File | Size | Records | Source |
|------|------|---------|--------|
| contacts_classified.json | 9.6MB | ~2,000 | Manual copy |
| contact_org_chart.json | 1.2MB | ~500 | Manual generation |
| jobs.json | 500KB | ~200 | Static copy |
| programs.json | 300KB | ~400 | Static copy |
| call_notes_*.json (7 files) | 2MB total | Various | Manual export |

**Issues:**
1. Data goes stale immediately
2. No refresh mechanism
3. Manual sync required (`npm run sync-data`)
4. Inconsistent with Hub API integration

---

## SECTION 3: HIGH-PRIORITY ISSUES

### 3.1 No Testing Infrastructure

**Current State:**
- 1 test file: `src/tests/enrichmentEngine.test.ts`
- No test runner configured
- No component tests
- No integration tests
- No E2E tests

**Missing:**
```json
// No test dependencies in package.json
{
  "devDependencies": {
    // Missing: vitest, @testing-library/react, etc.
  }
}
```

---

### 3.2 Temp File Clutter

**Location:** `dashboard/` root
**Count:** 50+ files matching `tmpclaude-*-cwd`

```
tmpclaude-012f-cwd  tmpclaude-5d95-cwd  tmpclaude-b54e-cwd
tmpclaude-01fa-cwd  tmpclaude-6036-cwd  tmpclaude-b6b6-cwd
... (48 more files)
```

**Impact:** Development friction, git noise, disk space

---

### 3.3 Duplicate Hook Logic

**Pattern:** Multiple hooks fetch same data differently

```typescript
// hooks/useNotionData.ts
export function useNotionDashboard() { ... }  // Fetches static JSON

// hooks/useHubApi.ts
export function useHubStats() { ... }  // Fetches from API

// hooks/useData.ts
export function useData() { ... }  // Context-based (unused)

// data/adapters/hubAdapter.ts
export class HubAdapter { ... }  // Another fetch pattern
```

**Result:** Multiple sources of truth, inconsistent caching, duplicated error handling.

---

### 3.4 Missing Loading/Error States

**Pattern:** Many pages don't handle loading/error properly

```tsx
// Some pages have proper handling
if (loading) return <LoadingSpinner />;
if (error) return <ErrorMessage />;

// Others just return null or crash
if (!data) return null;  // No explanation to user
```

**Affected Pages:**
- `CallIntelligence.tsx` - No loading state
- `AccountTakeover.tsx` - Minimal error handling
- `KnowledgeGraph.tsx` - No skeleton states

---

### 3.5 Large Bundle Size (No Code Splitting)

**Problem:** All 25 pages loaded upfront

```tsx
// App.tsx imports all pages at top level
import { ExecutiveSummary } from './pages/ExecutiveSummary';
import { JobIntelligence } from './pages/JobIntelligence';
import { JobsPipeline } from './pages/JobsPipeline';
// ... 22 more imports
```

**Impact:**
- Initial load time increased
- Memory usage higher than needed
- No lazy loading benefits

**Fix:** React.lazy() + Suspense with route-based code splitting

---

## SECTION 4: COMPONENT ANALYSIS

### 4.1 Page Component Inventory (25 pages)

| Page | Lines | Complexity | Data Source | Issues |
|------|-------|------------|-------------|--------|
| ExecutiveSummary.tsx | 370 | Medium | Summary + Hub Stats | Good structure |
| JobIntelligence.tsx | ~400 | High | Jobs, Programs, Contacts | Large, needs splitting |
| JobsPipeline.tsx | ~350 | Medium | Jobs | Reasonable |
| Programs.tsx | ~400 | Medium | Programs | Good |
| Contacts.tsx | ~450 | High | Contacts by tier | Complex filtering |
| Contractors.tsx | ~250 | Low | Contractors | Simple |
| Locations.tsx | ~350 | Medium | Jobs, Programs, Contacts | Good |
| BDEvents.tsx | ~300 | Medium | Programs, Contacts | Good |
| Opportunities.tsx | ~350 | Medium | All data | Good |
| EnrichmentDashboard.tsx | ~400 | High | Custom hooks | Complex |
| DailyPlaybook.tsx | ~350 | Medium | Custom service | Good |
| MindMap.tsx | ~500 | Very High | Zustand store | Most complex |
| Settings.tsx | ~300 | Medium | Config | Good |
| DataQualityDashboard.tsx | ~350 | Medium | Jobs, Programs, Contacts | Good |
| PastPerformance.tsx | ~300 | Medium | Static JSON | Good |
| PrimeOrgChart.tsx | ~350 | Medium | Static JSON | Good |
| ContactOrgChartPage.tsx | ~300 | Medium | Static JSON | Good |
| PlacementsPage.tsx | ~250 | Low | Static JSON | Simple |
| CallIntelligence.tsx | ~400 | High | Static JSON | Complex |
| AccountTakeover.tsx | ~300 | Medium | Static JSON | New |
| SmartQuery.tsx | ~400 | High | Hub API | AI integration |
| KnowledgeGraph.tsx | ~350 | High | Hub API | Graph viz |
| AgentPanel.tsx | ~300 | Medium | Hub API | AI agents |
| MemoryContext.tsx | ~250 | Medium | Hub API | Memory system |
| SystemHealth.tsx | ~300 | Medium | Hub API | Metrics |

**Observations:**
- 6 pages are "Very High" or "High" complexity - candidates for splitting
- 8 pages use static JSON - candidates for Hub API migration
- Inconsistent data fetching patterns across pages

---

### 4.2 Component Hierarchy

```
App.tsx
├── ThemeProvider (context)
│   └── App
│       ├── Sidebar
│       │   └── Tab buttons (25)
│       ├── Main content (switch-based)
│       │   ├── ExecutiveSummary
│       │   │   ├── StatCard (4x)
│       │   │   ├── MatchRateCard (3x)
│       │   │   ├── PieChart (2x)
│       │   │   └── BarChart
│       │   ├── MindMap
│       │   │   ├── MindMapCanvas
│       │   │   │   ├── ForceGraph2D
│       │   │   │   └── MindMapNode (per node)
│       │   │   ├── ControlBar
│       │   │   ├── NativeNodeTabs
│       │   │   ├── NotePanel
│       │   │   ├── AttachmentPanel
│       │   │   ├── ContextMenu
│       │   │   └── AIMapGenerator
│       │   └── [23 other pages...]
│       └── DataFreshness (footer component)
```

---

### 4.3 Hook Inventory

| Hook | Purpose | Used By | Status |
|------|---------|---------|--------|
| useNotionData | Fetch static JSON | Multiple pages | Active but misnamed |
| useNotionDashboard | Main data hook | App.tsx | Primary hook |
| useHubApi | Hub API hooks (12) | Hub pages | Active |
| useMindMapData | Mind map data loading | MindMap.tsx | Active |
| useMindMapExport | Export mind map | MindMap.tsx | Active |
| useForceLayout | D3 force simulation | MindMapCanvas | Active |
| useData | Context-based data | None | Orphaned |
| useCorrelation | Correlation logic | EnrichmentDashboard | Active |
| useAutoEnrichment | Auto-enrich data | EnrichmentDashboard | Active |
| useBDPlaybook | Playbook generation | DailyPlaybook | Active |

---

## SECTION 5: DATA FLOW ANALYSIS

### 5.1 Current Data Flow (Confused)

```
                    ┌─────────────────────────────────────────┐
                    │           Multiple Entry Points          │
                    └─────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
┌───────────────┐             ┌─────────────────┐             ┌─────────────────┐
│ useNotionData │             │   DataProvider  │             │   hubApiClient  │
│   (Hook)      │             │   (Context)     │             │   (Service)     │
│               │             │   NOT USED!     │             │                 │
└───────────────┘             └─────────────────┘             └─────────────────┘
        │                               │                               │
        ▼                               ▼                               ▼
┌───────────────┐             ┌─────────────────┐             ┌─────────────────┐
│ public/data/  │             │  localAdapter   │             │ localhost:8100  │
│ Static JSON   │             │  notionAdapter  │             │ Hub API         │
│ (27 files)    │             │  hubAdapter     │             │                 │
└───────────────┘             └─────────────────┘             └─────────────────┘
        │                                                              │
        └──────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │   25 Pages      │
                              │   (Different    │
                              │    patterns)    │
                              └─────────────────┘
```

### 5.2 Recommended Data Flow (Clean)

```
                    ┌─────────────────────────────────────────┐
                    │           DataProvider (Context)         │
                    │   - Single source of truth               │
                    │   - Auto-detects Hub vs Local            │
                    │   - Unified caching                      │
                    └─────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
            ┌───────────┐       ┌───────────┐       ┌───────────┐
            │ Hub API   │       │ Notion API│       │ Local JSON│
            │ Adapter   │       │ Adapter   │       │ Adapter   │
            │ (Primary) │       │ (Future)  │       │ (Fallback)│
            └───────────┘       └───────────┘       └───────────┘
                    │
                    ▼
            ┌─────────────────────────────────────────┐
            │           Unified Hooks                  │
            │   useJobs() useProgramsss() useContacts()   │
            │   All from DataProvider context          │
            └─────────────────────────────────────────┘
                                        │
                                        ▼
            ┌─────────────────────────────────────────┐
            │           React Router                   │
            │   Lazy-loaded pages with code splitting  │
            └─────────────────────────────────────────┘
```

---

## SECTION 6: SERVICE LAYER ANALYSIS

### 6.1 Service Inventory

| Service | Purpose | API Calls | Issues |
|---------|---------|-----------|--------|
| hubApi.ts | Hub API client | 25+ methods | Well-structured, singleton |
| notionApi.ts | Notion API | 5 methods | Token in localStorage |
| mapifyApi.ts | Mapify MCP | 3 methods | Minimal |
| playbookGenerator.ts | BD playbook | 2 methods | Works |
| correlationEngine.ts | Data correlation | 4 methods | Complex |
| autoEnrichment.ts | Auto-enrich | 3 methods | Works |
| enrichmentEngine.ts | Enrichment | 5 methods | Works |

### 6.2 hubApi.ts Analysis (Primary Service)

**Strengths:**
- Well-typed interfaces
- Proper error handling
- Singleton pattern
- URL persistence in localStorage
- 30-second timeout with AbortController

**Weaknesses:**
- No retry logic
- No request queue
- No rate limiting
- No offline detection
- Hardcoded `127.0.0.1:8100` default

---

## SECTION 7: STATE MANAGEMENT

### 7.1 Zustand Store (mindMapStore.ts)

**Location:** `src/stores/mindMapStore.ts`
**Lines:** 406
**Quality:** HIGH

**Structure:**
```typescript
interface MindMapState {
  // Core data
  nodes: Map<string, MindMapNode>;
  edges: MindMapEdge[];

  // UI State
  selectedNodeId: string | null;
  hoveredNodeId: string | null;

  // Expansion
  expansion: ExpansionState;

  // Viewport
  viewport: ViewportState;

  // Actions (20+)
  setGraphData, addNodes, removeChildNodes,
  setNativeNode, setSelectedNode, ...
}
```

**Assessment:** Best-structured code in the dashboard. Good separation of concerns.

### 7.2 Other State

| State Type | Location | Scope |
|------------|----------|-------|
| Theme state | ThemeContext | Global |
| Tab state | App.tsx useState | App-level |
| Page filters | Individual pages | Page-level |
| Cross-nav state | App.tsx useState | App-level |

**Missing:**
- URL state synchronization
- Persistent filter state
- Undo/redo capability

---

## SECTION 8: DESIGN SYSTEM ANALYSIS

### 8.1 Design Intelligence System

**Location:** `src/design_intelligence/`
**Quality:** GOOD

**Features:**
- Industry-specific color palettes (5 industries)
- Typography system with scale
- CSS variable generation
- Validation warnings

**Implemented:**
```typescript
export type Industry = 'government' | 'defense' | 'enterprise_saas' | 'consulting' | 'financial';

export interface DesignSystem {
  name: string;
  industry: Industry;
  colors: ColorPalette;
  typography: Typography;
  spacingUnit: string;
  borderRadius: string;
  ...
}
```

**Integration:**
- ThemeContext generates CSS variables
- Applied to :root on load
- Dark mode toggle works
- Industry switching works

### 8.2 Theme Implementation

**ThemeContext.tsx:**
- LocalStorage persistence
- System preference detection
- Dark/light/system modes
- Industry switching

**Issues:**
- CSS variables not consistently used (hardcoded colors in many components)
- Tailwind dark: classes mixed with CSS variables
- No runtime theme switching animation

---

## SECTION 9: PERFORMANCE ANALYSIS

### 9.1 Bundle Analysis (Estimated)

| Factor | Current | Target |
|--------|---------|--------|
| Initial JS | ~2MB (all pages) | ~500KB (lazy loaded) |
| Initial CSS | ~150KB | ~50KB (purged) |
| Static JSON | ~15MB loaded | 0 (API-based) |
| Code Splitting | None | Per-route |

### 9.2 Runtime Performance Issues

1. **All pages imported upfront** - No lazy loading
2. **Large JSON files fetched** - Even for unused pages
3. **No virtualization** - Contact lists (7k+ items)
4. **D3 force simulation** - CPU intensive on large graphs
5. **No memoization** - Many computed values recalculate

### 9.3 Recommended Optimizations

```tsx
// 1. Route-based code splitting
const ExecutiveSummary = React.lazy(() => import('./pages/ExecutiveSummary'));
const JobIntelligence = React.lazy(() => import('./pages/JobIntelligence'));

// 2. Virtualized lists for contacts
import { useVirtualizer } from '@tanstack/react-virtual';

// 3. Memoized computations
const sortedContacts = useMemo(() =>
  contacts.sort((a, b) => a.tier - b.tier),
  [contacts]
);

// 4. Debounced search
const debouncedSearch = useDebouncedCallback(setSearchTerm, 300);
```

---

## SECTION 10: SECURITY CONSIDERATIONS

### 10.1 Token Storage

| Token | Storage | Risk |
|-------|---------|------|
| Notion API Token | localStorage | Medium |
| Hub API URL | localStorage | Low |
| Theme preference | localStorage | None |

**Issue:** Notion token in localStorage is XSS-vulnerable
**Fix:** Consider httpOnly cookie or session-based auth

### 10.2 API Communication

- All APIs called over HTTP (localhost)
- No HTTPS enforcement
- No request signing
- No CORS configuration visible

### 10.3 Data Exposure

- Static JSON files publicly accessible
- No authentication on Hub API
- Contact PII in public/data/

---

## SECTION 11: TECHNICAL DEBT INVENTORY

### 11.1 Code Debt

| Item | Severity | Effort to Fix | Location |
|------|----------|---------------|----------|
| 50+ temp files | Low | 1 hour | dashboard/ |
| Unused DataProvider | Medium | 4 hours | data/DataProvider.tsx |
| Type inconsistencies | High | 8 hours | Throughout |
| No error boundaries | Critical | 4 hours | App.tsx |
| No routing | Critical | 16 hours | App.tsx |
| No tests | High | 40 hours | N/A |
| No code splitting | High | 8 hours | App.tsx |
| Hardcoded colors | Low | 4 hours | Multiple pages |

### 11.2 Architecture Debt

| Item | Severity | Effort | Description |
|------|----------|--------|-------------|
| Static JSON dependency | High | 24 hours | Migrate to Hub API |
| Multiple data patterns | High | 16 hours | Unify under DataProvider |
| No state persistence | Medium | 8 hours | Add URL state |
| No offline support | Low | 16 hours | Add service worker |

---

## SECTION 12: RECOMMENDATIONS

### 12.1 Phase 1: Stabilization (1-2 days)

1. **Clean up temp files**
   ```bash
   rm dashboard/tmpclaude-*
   ```

2. **Add error boundaries**
   ```tsx
   <ErrorBoundary fallback={<ErrorPage />}>
     <App />
   </ErrorBoundary>
   ```

3. **Fix type inconsistencies**
   - Standardize Contact type usage
   - Update all components to match

### 12.2 Phase 2: Architecture (3-5 days)

1. **Add React Router**
   - Replace switch statement with routes
   - Add URL-based navigation
   - Enable browser history

2. **Unify data layer**
   - Integrate DataProvider at root
   - Remove useNotionDashboard
   - Make Hub API primary source

3. **Add code splitting**
   - Lazy load pages
   - Add Suspense boundaries
   - Implement loading skeletons

### 12.3 Phase 3: Quality (5-7 days)

1. **Add testing**
   - Configure Vitest
   - Add component tests
   - Add integration tests

2. **Migrate static JSON to Hub API**
   - Remove public/data dependency
   - Add API endpoints for all data
   - Implement real-time refresh

3. **Performance optimization**
   - Add virtualization for long lists
   - Memoize computed values
   - Optimize D3 force simulation

### 12.4 Phase 4: Enhancement (Ongoing)

1. **Add offline support**
2. **Add real-time updates (WebSocket)**
3. **Add collaborative features**
4. **Add analytics/telemetry**

---

## SECTION 13: FILE-BY-FILE ISSUES

### Critical Files to Review

| File | Issues | Priority |
|------|--------|----------|
| App.tsx | Giant switch, no routing, no error boundary | Critical |
| hooks/useNotionData.ts | Misnamed, duplicates logic | High |
| data/DataProvider.tsx | Good code but unused | High |
| types/index.ts | Contact type inconsistent | High |
| pages/MindMap.tsx | 500 lines, needs splitting | Medium |
| services/hubApi.ts | No retry logic | Medium |

---

## SECTION 14: SUMMARY METRICS

| Metric | Value |
|--------|-------|
| Total Source Files | 77 |
| Total Lines of Code | ~15,000 |
| React Components | 45 |
| Custom Hooks | 9 |
| Service Modules | 6 |
| Pages | 25 |
| Type Definitions | 120+ |
| Static Data Files | 27 |
| Test Files | 1 |
| Test Coverage | ~0% |
| Technical Debt Score | 3.5/10 (needs work) |
| Architecture Score | 4/10 (fragmented) |
| Code Quality Score | 6/10 (decent) |
| UI/UX Quality | 7/10 (good visuals) |

---

## SECTION 15: DECISION MATRIX

### Rebuild vs Refactor

| Factor | Rebuild | Refactor |
|--------|---------|----------|
| Time to MVP | 3-4 weeks | 1-2 weeks |
| Risk | High (feature parity) | Low |
| Cost | High | Medium |
| Learning | Good architecture | Fix existing |
| Recommendation | | **REFACTOR** |

**Verdict:** The codebase has good bones. The components work, the design system is solid, and the Hub API integration is well-built. The issues are architectural (routing, data flow) rather than fundamental. A structured refactoring will be faster and safer than a rebuild.

---

## APPENDIX A: Quick Wins (< 1 hour each)

1. Delete temp files: `rm dashboard/tmpclaude-*`
2. Add `.gitignore` entry for temp files
3. Fix eslint warnings
4. Update README with setup instructions
5. Add loading spinners to pages missing them

## APPENDIX B: Commands for Analysis

```bash
# Count lines of code
find dashboard/src -name "*.tsx" -o -name "*.ts" | xargs wc -l

# Find unused exports
npx ts-prune dashboard/src

# Check bundle size
npm run build && du -sh dashboard/dist

# Find duplicate code
npx jscpd dashboard/src
```

---

*Report generated: 2026-02-01*
*Auditor: Claude Opus 4.5*
