import {
  LayoutDashboard,
  Briefcase,
  Building2,
  Users,
  Factory,
  MapPin,
  Calendar,
  Target,
  Zap,
  CalendarCheck,
  Network,
  Settings,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  BarChart3,
  Trophy,
  GitBranch,
  UserCheck,
  FileSpreadsheet,
  Phone,
  Search,
  Bot,
  Brain,
  Activity,
} from 'lucide-react';
import type { TabId } from '../types';

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  lastUpdated: Date | null;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

const tabs: Array<{ id: TabId; label: string; icon: React.ComponentType<{ className?: string }>; section?: string }> = [
  { id: 'executive', label: 'Executive Summary', icon: LayoutDashboard },
  // Hub AI Section
  { id: 'smartquery', label: 'Smart Query', icon: Search, section: 'Hub AI' },
  { id: 'knowledgegraph', label: 'Knowledge Graph', icon: GitBranch, section: 'Hub AI' },
  { id: 'agents', label: 'BD Agents', icon: Bot, section: 'Hub AI' },
  { id: 'memory', label: 'Memory Context', icon: Brain, section: 'Hub AI' },
  // Intelligence Section
  { id: 'intelligence', label: 'Job Intelligence', icon: Sparkles },
  { id: 'jobs', label: 'Jobs Pipeline', icon: Briefcase },
  { id: 'programs', label: 'Programs/Contracts', icon: Building2 },
  { id: 'contacts', label: 'Contact Intelligence', icon: Users },
  { id: 'contractors', label: 'Contractors', icon: Factory },
  { id: 'locations', label: 'Locations', icon: MapPin },
  { id: 'events', label: 'BD Events', icon: Calendar },
  { id: 'opportunities', label: 'BD Opportunities', icon: Target },
  { id: 'pastperformance', label: 'Past Performance', icon: Trophy },
  { id: 'primeorgchart', label: 'Prime Org Chart', icon: Network },
  { id: 'contactorgchart', label: 'Contact Org Chart', icon: UserCheck },
  { id: 'placements', label: 'Placements', icon: FileSpreadsheet },
  { id: 'callintelligence', label: 'Call Intelligence', icon: Phone },
  { id: 'enrichment', label: 'Auto-Enrichment', icon: Zap },
  { id: 'playbook', label: 'Daily Playbook', icon: CalendarCheck },
  { id: 'mindmap', label: 'Mind Map', icon: Network },
  { id: 'dataquality', label: 'Data Quality', icon: BarChart3 },
  // System Section
  { id: 'systemhealth', label: 'System Health', icon: Activity, section: 'System' },
  { id: 'settings', label: 'Settings', icon: Settings, section: 'System' },
];

export function Sidebar({
  activeTab,
  onTabChange,
  onRefresh,
  isRefreshing,
  lastUpdated,
  collapsed,
  onToggleCollapse,
}: SidebarProps) {
  return (
    <aside
      className={`bg-slate-900 text-white flex flex-col transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-700/50 flex items-center justify-between bg-gradient-to-r from-slate-900 to-slate-800">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                BD Intelligence
              </h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Dashboard v2.0</p>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center mx-auto shadow-lg shadow-blue-500/30">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          className={`p-1.5 rounded-lg hover:bg-slate-700 transition-all duration-200 group ${collapsed ? 'mt-2' : ''}`}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4 text-slate-500 group-hover:text-white transition-colors" />
          ) : (
            <ChevronLeft className="h-4 w-4 text-slate-500 group-hover:text-white transition-colors" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-0.5 px-2">
          {tabs.map((tab, index) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            const prevTab = tabs[index - 1];
            const showSectionHeader = tab.section && (!prevTab || prevTab.section !== tab.section);

            return (
              <li key={tab.id}>
                {/* Section Header */}
                {showSectionHeader && !collapsed && (
                  <div className="mt-4 mb-2 px-3 first:mt-0">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                      {tab.section}
                    </span>
                  </div>
                )}
                {showSectionHeader && collapsed && <div className="mt-3 mb-1 border-t border-slate-700 mx-2" />}

                <button
                  onClick={() => onTabChange(tab.id)}
                  className={`group w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/25'
                      : 'text-slate-400 hover:bg-slate-800/80 hover:text-white'
                  }`}
                  title={collapsed ? tab.label : undefined}
                >
                  <div className={`p-1 rounded-md transition-colors ${
                    isActive ? 'bg-white/20' : 'group-hover:bg-slate-700'
                  }`}>
                    <Icon className={`h-4 w-4 flex-shrink-0 transition-transform ${
                      isActive ? '' : 'group-hover:scale-110'
                    }`} />
                  </div>
                  {!collapsed && (
                    <span className={`text-sm transition-colors ${
                      isActive ? 'font-semibold' : 'font-medium'
                    }`}>
                      {tab.label}
                    </span>
                  )}
                  {isActive && !collapsed && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-slate-700/50 bg-slate-900/50">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className={`w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg transition-all duration-200 ${
            isRefreshing
              ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed'
              : 'bg-slate-800 text-slate-300 hover:bg-gradient-to-r hover:from-blue-600 hover:to-cyan-600 hover:text-white hover:shadow-lg hover:shadow-blue-500/20'
          }`}
          title={collapsed ? 'Refresh Data' : undefined}
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          {!collapsed && <span className="text-sm font-medium">{isRefreshing ? 'Refreshing...' : 'Refresh Data'}</span>}
        </button>
        {!collapsed && lastUpdated && (
          <p className="mt-2 text-[10px] text-slate-500 text-center">
            Updated: {lastUpdated.toLocaleTimeString()}
          </p>
        )}
      </div>
    </aside>
  );
}
