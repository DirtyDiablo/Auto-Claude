import { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import { Sidebar } from './components/Sidebar';
import { DataFreshness } from './components/DataFreshness';
import { useAppData } from './hooks/useAppData';
import { CommandPalette } from './components/CommandPalette';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Breadcrumb } from './components/Breadcrumb';
import { CopilotSidebar } from './components/CopilotSidebar';
import { useCopilotContext } from './hooks/useCopilotContext';
import type { TabId } from './types';
import type { NativeNodeType } from './configs/nativeNodeConfigs';
import './index.css';

// =============================================================================
// LAZY-LOADED PAGES (Code Splitting)
// =============================================================================

const ExecutiveSummary = lazy(() => import('./pages/ExecutiveSummary').then(m => ({ default: m.ExecutiveSummary })));
const JobIntelligence = lazy(() => import('./pages/JobIntelligence').then(m => ({ default: m.JobIntelligence })));
const JobsPipeline = lazy(() => import('./pages/JobsPipeline').then(m => ({ default: m.JobsPipeline })));
const Programs = lazy(() => import('./pages/Programs').then(m => ({ default: m.Programs })));
const Contacts = lazy(() => import('./pages/Contacts').then(m => ({ default: m.Contacts })));
const Contractors = lazy(() => import('./pages/Contractors').then(m => ({ default: m.Contractors })));
const Locations = lazy(() => import('./pages/Locations').then(m => ({ default: m.Locations })));
const BDEvents = lazy(() => import('./pages/BDEvents').then(m => ({ default: m.BDEvents })));
const Opportunities = lazy(() => import('./pages/Opportunities').then(m => ({ default: m.Opportunities })));
const EnrichmentDashboard = lazy(() => import('./pages/EnrichmentDashboard').then(m => ({ default: m.EnrichmentDashboard })));
const DailyPlaybook = lazy(() => import('./pages/DailyPlaybook').then(m => ({ default: m.DailyPlaybook })));
const MindMap = lazy(() => import('./pages/MindMap').then(m => ({ default: m.MindMap })));
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));
const DataQualityDashboard = lazy(() => import('./pages/DataQualityDashboard').then(m => ({ default: m.DataQualityDashboard })));
const PastPerformance = lazy(() => import('./pages/PastPerformance').then(m => ({ default: m.PastPerformance })));
const PrimeOrgChart = lazy(() => import('./pages/PrimeOrgChart').then(m => ({ default: m.PrimeOrgChart })));
const ContactOrgChartPage = lazy(() => import('./pages/ContactOrgChartPage').then(m => ({ default: m.ContactOrgChartPage })));
const PlacementsPage = lazy(() => import('./pages/PlacementsPage').then(m => ({ default: m.PlacementsPage })));
const CallIntelligence = lazy(() => import('./pages/CallIntelligence'));
const AccountTakeover = lazy(() => import('./pages/AccountTakeover').then(m => ({ default: m.AccountTakeover })));
const OutreachManager = lazy(() => import('./pages/OutreachManager').then(m => ({ default: m.OutreachManager })));
const MeetingCalendar = lazy(() => import('./pages/MeetingCalendar').then(m => ({ default: m.MeetingCalendar })));
const GraphExplorer = lazy(() => import('./pages/GraphExplorer').then(m => ({ default: m.GraphExplorer })));
const Analytics = lazy(() => import('./pages/Analytics').then(m => ({ default: m.Analytics })));
const QADashboard = lazy(() => import('./pages/QADashboard').then(m => ({ default: m.QADashboard })));
const PipelineStatus = lazy(() => import('./pages/PipelineStatus').then(m => ({ default: m.PipelineStatus })));
const SmartQuery = lazy(() => import('./pages/SmartQuery').then(m => ({ default: m.SmartQuery })));
const KnowledgeGraph = lazy(() => import('./pages/KnowledgeGraph').then(m => ({ default: m.KnowledgeGraph })));
const AgentPanel = lazy(() => import('./pages/AgentPanel').then(m => ({ default: m.AgentPanel })));
const MemoryContext = lazy(() => import('./pages/MemoryContext').then(m => ({ default: m.MemoryContext })));
const SystemHealth = lazy(() => import('./pages/SystemHealth').then(m => ({ default: m.SystemHealth })));
const CompetitiveLandscape = lazy(() => import('./pages/CompetitiveLandscape').then(m => ({ default: m.CompetitiveLandscape })));
const AlertHistory = lazy(() => import('./pages/AlertHistory').then(m => ({ default: m.AlertHistory })));
const RevenuePipeline = lazy(() => import('./pages/RevenuePipeline').then(m => ({ default: m.RevenuePipeline })));
const ContactDetail = lazy(() => import('./pages/ContactDetail').then(m => ({ default: m.ContactDetail })));
const ProgramDetail = lazy(() => import('./pages/ProgramDetail').then(m => ({ default: m.ProgramDetail })));
const GeographicDashboard = lazy(() => import('./pages/GeographicDashboard').then(m => ({ default: m.GeographicDashboard })));
const RelationshipExplorer = lazy(() => import('./pages/RelationshipExplorer').then(m => ({ default: m.RelationshipExplorer })));

// =============================================================================
// LOADING SPINNER
// =============================================================================

function PageLoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="flex flex-col items-center gap-3">
        <div className="relative">
          <div className="w-10 h-10 border-3 border-slate-200 dark:border-slate-700 rounded-full" />
          <div className="absolute inset-0 w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
        <p className="text-sm text-slate-400 dark:text-slate-500">Loading...</p>
      </div>
    </div>
  );
}

// =============================================================================
// APP STATE TYPES
// =============================================================================

interface CrossNavFilter {
  type: 'program' | 'contractor' | 'company' | 'location';
  value: string;
}

interface MindMapNav {
  entityType: NativeNodeType;
  entityId: string;
  entityLabel: string;
}

// =============================================================================
// APP COMPONENT
// =============================================================================

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('executive');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => window.innerWidth < 1024);
  const { data, loading, error, refresh, lastUpdated, isConfigured } = useAppData();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [crossNavFilter, setCrossNavFilter] = useState<CrossNavFilter | null>(null);
  const [mindMapNav, setMindMapNav] = useState<MindMapNav | null>(null);
  const [selectedContact, setSelectedContact] = useState<string | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<string | null>(null);
  const [copilotOpen, setCopilotOpen] = useState(false);

  const copilotContext = useCopilotContext(activeTab, selectedContact, selectedProgram);

  // Responsive: auto-collapse sidebar under 1024px
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 1024px)');
    const handler = (e: MediaQueryListEvent) => setSidebarCollapsed(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  // Cross-navigation handlers
  const handleNavigateToProgram = useCallback((programName: string) => {
    setCrossNavFilter({ type: 'program', value: programName });
    setActiveTab('programs');
  }, []);

  const handleNavigateToContractor = useCallback((contractorName: string) => {
    setCrossNavFilter({ type: 'contractor', value: contractorName });
    setActiveTab('contractors');
  }, []);

  const handleNavigateToLocation = useCallback((location: string) => {
    setCrossNavFilter({ type: 'location', value: location });
    setActiveTab('locations');
  }, []);

  const handleNavigateToContactDetail = useCallback((contactName: string) => {
    setSelectedContact(contactName);
    setActiveTab('contactdetail');
  }, []);

  const handleNavigateToProgramDetail = useCallback((programName: string) => {
    setSelectedProgram(programName);
    setActiveTab('programdetail');
  }, []);

  const handleNavigateToMindMap = useCallback(
    (entityType: NativeNodeType, entityId: string, entityLabel: string) => {
      setMindMapNav({ entityType, entityId, entityLabel });
      setActiveTab('mindmap');
    },
    []
  );

  const handleTabChange = useCallback((tab: TabId) => {
    setCrossNavFilter(null);
    setMindMapNav(null);
    setSelectedContact(null);
    setSelectedProgram(null);
    setActiveTab(tab);
  }, []);

  // Keyboard shortcuts: Alt+1..9 for quick navigation, Ctrl+/ for copilot
  useEffect(() => {
    const shortcuts: Record<string, TabId> = {
      '1': 'executive',
      '2': 'jobs',
      '3': 'contacts',
      '4': 'programs',
      '5': 'outreach',
      '6': 'analytics',
      '7': 'smartquery',
      '8': 'agents',
      '9': 'settings',
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && !e.ctrlKey && !e.metaKey && shortcuts[e.key]) {
        e.preventDefault();
        handleTabChange(shortcuts[e.key]);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setCopilotOpen((prev) => !prev);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleTabChange]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await refresh();
    setIsRefreshing(false);
  }, [refresh]);

  const renderContent = () => {
    if (error) {
      const isNotConfiguredError = !isConfigured;
      return (
        <div className="flex flex-col items-center justify-center h-full text-slate-500">
          <p className="text-xl font-semibold text-red-600 mb-2">
            {isNotConfiguredError ? 'Notion Not Configured' : 'Error Loading Data'}
          </p>
          <p className="mb-4">{error}</p>
          {isNotConfiguredError ? (
            <>
              <p className="text-sm mb-4 text-center max-w-md">
                To use the dashboard, you need to configure your Notion API token in Settings.
                This allows the dashboard to fetch live data from your Notion databases.
              </p>
              <button
                onClick={() => handleTabChange('settings')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Go to Settings
              </button>
            </>
          ) : (
            <button
              onClick={handleRefresh}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      );
    }

    switch (activeTab) {
      case 'executive':
        return <ExecutiveSummary summary={data?.summary ?? null} loading={loading} onTabChange={setActiveTab} />;
      case 'intelligence':
        return (
          <JobIntelligence
            jobs={data?.jobs ?? []}
            programs={data?.programs ?? []}
            contacts={data?.contacts ?? {}}
            loading={loading}
          />
        );
      case 'jobs':
        return (
          <JobsPipeline
            jobs={data?.jobs ?? []}
            loading={loading}
            onNavigateToProgram={handleNavigateToProgram}
            onNavigateToLocation={handleNavigateToLocation}
            onNavigateToMindMap={handleNavigateToMindMap}
            onNavigateToContact={handleNavigateToContactDetail}
          />
        );
      case 'programs':
        return (
          <Programs
            programs={data?.programs ?? []}
            loading={loading}
            initialFilter={crossNavFilter?.type === 'program' ? crossNavFilter.value : undefined}
            onNavigateToContractor={handleNavigateToContractor}
            onNavigateToLocation={handleNavigateToLocation}
            onNavigateToMindMap={handleNavigateToMindMap}
            onNavigateToProgramDetail={handleNavigateToProgramDetail}
          />
        );
      case 'contacts':
        return (
          <Contacts
            contacts={data?.contacts ?? {}}
            loading={loading}
            initialCompanyFilter={crossNavFilter?.type === 'company' ? crossNavFilter.value : undefined}
            onNavigateToProgram={handleNavigateToProgram}
            onNavigateToMindMap={handleNavigateToMindMap}
            onNavigateToContact={handleNavigateToContactDetail}
          />
        );
      case 'contactdetail':
        return selectedContact ? (
          <div className="h-full overflow-auto">
            <div className="px-6 pt-4">
              <Breadcrumb
                items={[
                  { label: 'Contacts', tabId: 'contacts' },
                  { label: selectedContact },
                ]}
                onNavigate={handleTabChange}
              />
            </div>
            <ContactDetail
              contactName={selectedContact}
              onBack={() => handleTabChange('contacts')}
              onNavigateToProgram={handleNavigateToProgramDetail}
            />
          </div>
        ) : null;
      case 'programdetail':
        return selectedProgram ? (
          <div className="h-full overflow-auto">
            <div className="px-6 pt-4">
              <Breadcrumb
                items={[
                  { label: 'Programs', tabId: 'programs' },
                  { label: selectedProgram },
                ]}
                onNavigate={handleTabChange}
              />
            </div>
            <ProgramDetail
              programName={selectedProgram}
              onBack={() => handleTabChange('programs')}
              onNavigateToContact={handleNavigateToContactDetail}
            />
          </div>
        ) : null;
      case 'contractors':
        return (
          <Contractors
            contractors={data?.contractors ?? []}
            loading={loading}
            initialFilter={crossNavFilter?.type === 'contractor' ? crossNavFilter.value : undefined}
          />
        );
      case 'locations':
        return (
          <Locations
            jobs={data?.jobs ?? []}
            programs={data?.programs ?? []}
            contacts={data?.contacts ?? {}}
            loading={loading}
            initialFilter={crossNavFilter?.type === 'location' ? crossNavFilter.value : undefined}
          />
        );
      case 'events':
        return (
          <BDEvents
            programs={data?.programs ?? []}
            contacts={data?.contacts ?? {}}
            loading={loading}
            onNavigateToProgram={handleNavigateToProgram}
          />
        );
      case 'opportunities':
        return (
          <Opportunities
            jobs={data?.jobs ?? []}
            programs={data?.programs ?? []}
            contacts={data?.contacts ?? {}}
            summary={data?.summary ?? null}
            loading={loading}
          />
        );
      case 'enrichment':
        return <EnrichmentDashboard loading={loading} />;
      case 'playbook':
        return <DailyPlaybook loading={loading} />;
      case 'mindmap':
        return (
          <MindMap
            initialEntityType={mindMapNav?.entityType}
            initialEntityId={mindMapNav?.entityId}
            initialEntityLabel={mindMapNav?.entityLabel}
          />
        );
      case 'dataquality':
        return (
          <DataQualityDashboard
            jobs={data?.jobs ?? []}
            programs={data?.programs ?? []}
            contacts={data?.contacts ?? {}}
            loading={loading}
          />
        );
      case 'pastperformance':
        return <PastPerformance loading={loading} />;
      case 'primeorgchart':
        return <PrimeOrgChart loading={loading} />;
      case 'contactorgchart':
        return <ContactOrgChartPage loading={loading} />;
      case 'placements':
        return <PlacementsPage loading={loading} />;
      case 'callintelligence':
        return <CallIntelligence />;
      case 'accounttakeover':
        return <AccountTakeover />;
      case 'outreach':
        return <OutreachManager loading={loading} />;
      case 'meetingcalendar':
        return <MeetingCalendar onNavigateToContact={handleNavigateToContactDetail} />;
      case 'graphexplorer':
        return (
          <GraphExplorer
            onNavigateToContact={handleNavigateToContactDetail}
            onNavigateToProgram={handleNavigateToProgramDetail}
            onNavigateToOutreach={() => handleTabChange('outreach')}
          />
        );
      case 'analytics':
        return <Analytics loading={loading} />;
      case 'qadashboard':
        return <QADashboard />;
      case 'pipelinestatus':
        return <PipelineStatus />;
      case 'competitive':
        return <CompetitiveLandscape />;
      case 'alerthistory':
        return <AlertHistory />;
      case 'revenue':
        return <RevenuePipeline />;
      case 'smartquery':
        return <SmartQuery loading={loading} />;
      case 'knowledgegraph':
        return <KnowledgeGraph />;
      case 'agents':
        return <AgentPanel />;
      case 'memory':
        return <MemoryContext />;
      case 'geographic':
        return (
          <GeographicDashboard
            contacts={data?.contacts ?? {}}
            programs={data?.programs ?? []}
            loading={loading}
          />
        );
      case 'relationships':
        return (
          <RelationshipExplorer
            onNavigateToContact={handleNavigateToContactDetail}
            onNavigateToProgram={handleNavigateToProgramDetail}
          />
        );
      case 'systemhealth':
        return <SystemHealth />;
      case 'settings':
        return (
          <Settings
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
            lastUpdated={lastUpdated}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="h-screen flex overflow-hidden bg-slate-100 dark:bg-slate-900 transition-colors">
      <Sidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing || loading}
        lastUpdated={lastUpdated}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <main className={`flex-1 overflow-hidden transition-[margin] duration-300 ${copilotOpen ? 'sm:mr-80' : ''}`}>
        <ErrorBoundary key={activeTab}>
          <Suspense fallback={<PageLoadingSpinner />}>
            {renderContent()}
          </Suspense>
        </ErrorBoundary>
      </main>

      {/* Copilot toggle button */}
      {!copilotOpen && (
        <button
          onClick={() => setCopilotOpen(true)}
          className="fixed bottom-6 right-6 z-30 w-12 h-12 rounded-full
            bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg
            hover:shadow-xl hover:scale-105 transition-all
            flex items-center justify-center"
          title="Open BD Copilot (Ctrl+/)"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      )}

      <CopilotSidebar
        isOpen={copilotOpen}
        onToggle={() => setCopilotOpen(false)}
        context={copilotContext}
        onNavigateToContact={handleNavigateToContactDetail}
        onNavigateToProgram={handleNavigateToProgramDetail}
        onNavigateToJobs={() => handleTabChange('jobs')}
      />
      <DataFreshness />
      <CommandPalette onNavigate={handleTabChange} />
    </div>
  );
}

export default App;
