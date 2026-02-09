import { useMemo } from 'react';
import type { TabId } from '../types';

export interface CopilotContext {
  page: TabId;
  entityType?: 'contact' | 'program' | 'job';
  entityName?: string;
  contextLabel?: string;
  contextPrompt: string;
}

export function useCopilotContext(
  activeTab: TabId,
  selectedContact: string | null,
  selectedProgram: string | null,
): CopilotContext {
  return useMemo(() => {
    if (activeTab === 'contactdetail' && selectedContact) {
      return {
        page: activeTab,
        entityType: 'contact' as const,
        entityName: selectedContact,
        contextLabel: selectedContact,
        contextPrompt: `The user is viewing the contact detail page for "${selectedContact}". Prioritize information about this contact, their program associations, tier, and outreach history. If they ask general questions, relate back to this contact when relevant.`,
      };
    }

    if (activeTab === 'programdetail' && selectedProgram) {
      return {
        page: activeTab,
        entityType: 'program' as const,
        entityName: selectedProgram,
        contextLabel: selectedProgram,
        contextPrompt: `The user is viewing the program detail page for "${selectedProgram}". Prioritize information about this program, its prime contractors, key contacts, job postings, and competitive landscape. Relate answers to this program when relevant.`,
      };
    }

    const pageContexts: Partial<Record<TabId, string>> = {
      jobs: 'The user is on the Jobs Pipeline page viewing BD job postings in a Kanban board. Help with job analysis, pipeline stats, and program matching.',
      contacts: 'The user is on the Contacts page browsing CRM contacts. Help find contacts by tier, program, or company.',
      programs: 'The user is on the Programs page viewing federal defense programs. Help with program analysis, prime contractors, and contract details.',
      outreach: 'The user is on the Outreach Manager page managing BD outreach sequences. Help draft messages, plan sequences, and track engagement.',
      analytics: 'The user is on the Analytics page viewing BD intelligence charts. Help interpret data trends and provide strategic insights.',
      executive: 'The user is on the Executive Summary dashboard. Provide high-level BD intelligence and strategic recommendations.',
      smartquery: 'The user is on the Smart Query page for semantic search. Help refine search queries and interpret results.',
      agents: 'The user is on the Agent Panel page managing AI agents. Help with task orchestration and agent status.',
    };

    return {
      page: activeTab,
      contextLabel: undefined,
      contextPrompt: pageContexts[activeTab] || 'The user is browsing the BD Intelligence Dashboard. Help with contacts, programs, jobs, and business development strategy for federal defense programs.',
    };
  }, [activeTab, selectedContact, selectedProgram]);
}
