import { useState, useCallback, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { DataFreshness } from './components/DataFreshness';
import { ExecutiveSummary } from './pages/ExecutiveSummary';
import { JobIntelligence } from './pages/JobIntelligence';
import { JobsPipeline } from './pages/JobsPipeline';
import { Programs } from './pages/Programs';
import { Contacts } from './pages/Contacts';
import { Contractors } from './pages/Contractors';
import { Locations } from './pages/Locations';
import { BDEvents } from './pages/BDEvents';
import { Opportunities } from './pages/Opportunities';
import { EnrichmentDashboard } from './pages/EnrichmentDashboard';
import { DailyPlaybook } from './pages/DailyPlaybook';
import { MindMap } from './pages/MindMap';
import { Settings } from './pages/Settings';
import { DataQualityDashboard } from './pages/DataQualityDashboard';
import { PastPerformance } from './pages/PastPerformance';
import { PrimeOrgChart } from './pages/PrimeOrgChart';
import { ContactOrgChartPage } from './pages/ContactOrgChartPage';
import { PlacementsPage } from './pages/PlacementsPage';
import CallIntelligence from './pages/CallIntelligence';
import { AccountTakeover } from './pages/AccountTakeover';
import { OutreachManager } from './pages/OutreachManager';
import { Analytics } from './pages/Analytics';
// Operations Pages
import { QADashboard } from './pages/QADashboard';
import { PipelineStatus } from './pages/PipelineStatus';
// Hub AI Pages
import { SmartQuery } from './pages/SmartQuery';
import { KnowledgeGraph } from './pages/KnowledgeGraph';
import { AgentPanel } from './pages/AgentPanel';
import { MemoryContext } from './pages/MemoryContext';
import { SystemHealth } from './pages/SystemHealth';
// Detail Pages
import { ContactDetail } from './pages/ContactDetail';
import { ProgramDetail } from './pages/ProgramDetail';
import { useAppData } from './hooks/useAppData';
import { CommandPalette } from './components/CommandPalette';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Breadcrumb } from './components/Breadcrumb';
import type { TabId } from './types';
import type { NativeNodeType } from './configs/nativeNodeConfigs';
import './index.css';

// Cross-navigation filter state
interface CrossNavFilter {
  type: 'program' | 'contractor' | 'company' | 'location';
  value: string;
}

// Mind map navigation state
interface MindMapNav {
  entityType: NativeNodeType;
  entityId: string;
  entityLabel: string;
}

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('executive');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => window.innerWidth < 1024);
  const { data, loading, error, refresh, lastUpdated, isConfigured } = useAppData();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [crossNavFilter, setCrossNavFilter] = useState<CrossNavFilter | null>(null);
  const [mindMapNav, setMindMapNav] = useState<MindMapNav | null>(null);
  const [selectedContact, setSelectedContact] = useState<string | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<string | null>(null);

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

  // Navigate to Contact Detail page
  const handleNavigateToContactDetail = useCallback((contactName: string) => {
    setSelectedContact(contactName);
    setActiveTab('contactdetail');
  }, []);

  // Navigate to Program Detail page
  const handleNavigateToProgramDetail = useCallback((programName: string) => {
    setSelectedProgram(programName);
    setActiveTab('programdetail');
  }, []);

  // Navigate to Mind Map with a specific entity
  const handleNavigateToMindMap = useCallback(
    (entityType: NativeNodeType, entityId: string, entityLabel: string) => {
      setMindMapNav({ entityType, entityId, entityLabel });
      setActiveTab('mindmap');
    },
    []
  );

  // Clear filter when manually changing tabs
  const handleTabChange = useCallback((tab: TabId) => {
    setCrossNavFilter(null);
    setMindMapNav(null);
    setSelectedContact(null);
    setSelectedProgram(null);
    setActiveTab(tab);
  }, []);

  // Keyboard shortcuts: Alt+1..9 for quick navigation
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
        return <ExecutiveSummary summary={data?.summary ?? null} loading={loading} />;
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
      case 'analytics':
        return <Analytics loading={loading} />;
      // Operations Pages
      case 'qadashboard':
        return <QADashboard />;
      case 'pipelinestatus':
        return <PipelineStatus />;
      // Hub AI Pages
      case 'smartquery':
        return <SmartQuery loading={loading} />;
      case 'knowledgegraph':
        return <KnowledgeGraph />;
      case 'agents':
        return <AgentPanel />;
      case 'memory':
        return <MemoryContext />;
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
      <main className="flex-1 overflow-hidden">
        <ErrorBoundary key={activeTab}>
          {renderContent()}
        </ErrorBoundary>
      </main>
      <DataFreshness />
      <CommandPalette onNavigate={handleTabChange} />
    </div>
  );
}

export default App;
