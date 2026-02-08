/**
 * Breadcrumb navigation component
 *
 * Shows current page location with navigation back links.
 */

import { ChevronRight, Home } from 'lucide-react';
import type { TabId } from '../types';

interface BreadcrumbItem {
  label: string;
  tabId?: TabId;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  onNavigate: (tab: TabId) => void;
}

const PAGE_LABELS: Partial<Record<TabId, string>> = {
  executive: 'Executive Summary',
  intelligence: 'Job Intelligence',
  jobs: 'Jobs Pipeline',
  programs: 'Programs',
  contacts: 'Contacts',
  contactdetail: 'Contact Detail',
  programdetail: 'Program Detail',
  contractors: 'Contractors',
  locations: 'Locations',
  events: 'BD Events',
  opportunities: 'Opportunities',
  enrichment: 'Enrichment',
  playbook: 'Playbook',
  mindmap: 'Mind Map',
  dataquality: 'Data Quality',
  pastperformance: 'Past Performance',
  primeorgchart: 'Prime Org Chart',
  contactorgchart: 'Contact Org Chart',
  placements: 'Placements',
  callintelligence: 'Call Intelligence',
  accounttakeover: 'Account Takeover',
  outreach: 'Outreach Manager',
  analytics: 'Analytics',
  smartquery: 'Smart Query',
  knowledgegraph: 'Knowledge Graph',
  agents: 'BD Agents',
  memory: 'Memory Context',
  qadashboard: 'QA Dashboard',
  pipelinestatus: 'Pipeline Status',
  systemhealth: 'System Health',
  settings: 'Settings',
};

export function getPageLabel(tabId: TabId): string {
  return PAGE_LABELS[tabId] || tabId;
}

export function Breadcrumb({ items, onNavigate }: BreadcrumbProps) {
  return (
    <nav className="flex items-center gap-1.5 text-sm mb-4">
      <button
        onClick={() => onNavigate('executive')}
        className="flex items-center gap-1 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors"
      >
        <Home className="h-3.5 w-3.5" />
      </button>
      {items.map((item, idx) => (
        <span key={idx} className="flex items-center gap-1.5">
          <ChevronRight className="h-3 w-3 text-slate-300 dark:text-slate-600" />
          {item.tabId && idx < items.length - 1 ? (
            <button
              onClick={() => onNavigate(item.tabId!)}
              className="text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors"
            >
              {item.label}
            </button>
          ) : (
            <span className="text-slate-700 dark:text-slate-200 font-medium">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

export default Breadcrumb;
