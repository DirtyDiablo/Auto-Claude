/**
 * AgentResultRenderer - Dispatches to the correct structured result card
 * based on task type. Falls back to raw JSON for unknown types.
 */

import type { AgentTaskResult, AgentTaskType } from '../../hooks/useAgentTask';
import { ProgramAnalysisCard } from './ProgramAnalysisCard';
import { ContactEnrichmentCard } from './ContactEnrichmentCard';
import { CompetitiveReportCard } from './CompetitiveReportCard';
import { FileText } from 'lucide-react';

interface Props {
  task: AgentTaskResult;
  onNavigateToContact?: (name: string) => void;
  onNavigateToProgram?: (name: string) => void;
}

const CARD_MAP: Record<AgentTaskType, React.FC<{ result: Record<string, unknown>; onNavigateToContact?: (name: string) => void; onNavigateToProgram?: (name: string) => void }>> = {
  program_analysis: ProgramAnalysisCard as React.FC<{ result: Record<string, unknown>; onNavigateToContact?: (name: string) => void; onNavigateToProgram?: (name: string) => void }>,
  contact_enrichment: ContactEnrichmentCard as React.FC<{ result: Record<string, unknown>; onNavigateToContact?: (name: string) => void; onNavigateToProgram?: (name: string) => void }>,
  competitive_report: CompetitiveReportCard as React.FC<{ result: Record<string, unknown>; onNavigateToContact?: (name: string) => void; onNavigateToProgram?: (name: string) => void }>,
  outreach_draft: GenericResultCard,
  strategy_brief: GenericResultCard,
  humint_analysis: GenericResultCard,
};

function GenericResultCard({ result }: { result: Record<string, unknown> }) {
  // Try to extract common patterns from the result
  const title = (result.title || result.name || result.summary || '') as string;
  const content = (result.content || result.answer || result.analysis || result.report || '') as string;
  const items = (result.items || result.findings || result.recommendations || []) as string[];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-4 bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-slate-600" />
          <h3 className="font-semibold text-slate-900">
            {title || 'Agent Result'}
          </h3>
        </div>
      </div>
      <div className="p-4">
        {content && (
          <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap mb-3">{content}</p>
        )}
        {Array.isArray(items) && items.length > 0 && (
          <ul className="space-y-1">
            {items.map((item, i) => (
              <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
              </li>
            ))}
          </ul>
        )}
        {!content && (!Array.isArray(items) || items.length === 0) && (
          <pre className="text-xs text-slate-500 bg-slate-50 rounded-lg p-3 overflow-auto max-h-48 font-mono">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

export function AgentResultRenderer({ task, onNavigateToContact, onNavigateToProgram }: Props) {
  if (!task.result || task.status !== 'completed') return null;

  const Card = CARD_MAP[task.type] || GenericResultCard;

  return (
    <Card
      result={task.result}
      onNavigateToContact={onNavigateToContact}
      onNavigateToProgram={onNavigateToProgram}
    />
  );
}
