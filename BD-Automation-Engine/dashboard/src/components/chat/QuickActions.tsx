import { BarChart3, Search, Mail, Factory } from 'lucide-react';

interface QuickActionsProps {
  contextLabel?: string;
  onAction: (query: string) => void;
}

export function QuickActions({ contextLabel, onAction }: QuickActionsProps) {
  const actions = [
    { icon: BarChart3, label: 'Weekly Brief', query: 'Generate a weekly BD intelligence brief covering top programs, new jobs, and key contacts to engage.' },
    { icon: Search, label: contextLabel ? `Contacts for ${contextLabel}` : 'Find contacts', query: contextLabel ? `Find key contacts for the ${contextLabel} program` : 'Find top tier contacts for DCGS programs' },
    { icon: Mail, label: 'Draft outreach', query: contextLabel ? `Draft a BD outreach message for contacts on ${contextLabel}` : 'Draft an introductory outreach message for a Tier 2 defense contact' },
    { icon: Factory, label: 'Competitive landscape', query: 'Analyze the competitive landscape — which primes are hiring the most and where are the gaps?' },
  ];

  return (
    <div className="flex flex-wrap gap-1.5 px-3 pb-2">
      {actions.map((action) => (
        <button
          key={action.label}
          onClick={() => onAction(action.query)}
          className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium
            bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400
            rounded-md border border-slate-200 dark:border-slate-700
            hover:bg-blue-50 hover:text-blue-700 hover:border-blue-300
            dark:hover:bg-blue-900/30 dark:hover:text-blue-300 dark:hover:border-blue-700
            transition-colors"
        >
          <action.icon className="h-3 w-3" />
          {action.label}
        </button>
      ))}
    </div>
  );
}
