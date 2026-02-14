/**
 * BD Playbook Hook
 *
 * Loads and enriches job data, then generates the daily playbook
 */

import { useState, useEffect, useCallback } from 'react';
import {
  fetchJobs,
  fetchPrograms,
  fetchAllContacts,
  isNotionConfigured,
} from '../services/notionApi';
import type { NotionJob, NotionProgram, NotionContact } from '../services/notionApi';
import { enrichAllJobs, getEnrichmentStats } from '../services/enrichmentEngine';
import type { EnrichedJob } from '../services/enrichmentEngine';
import { generateDailyPlaybook, fetchBackendPlaybook } from '../services/playbookGenerator';
import type { DailyPlaybook } from '../services/playbookGenerator';

interface UseBDPlaybookReturn {
  // Data
  playbook: DailyPlaybook | null;
  enrichedJobs: EnrichedJob[];
  contacts: NotionContact[];
  programs: NotionProgram[];

  // State
  loading: boolean;
  error: string | null;
  isConfigured: boolean;

  // Stats
  enrichmentStats: ReturnType<typeof getEnrichmentStats> | null;

  // Actions
  refresh: () => Promise<void>;
  setDate: (date: Date) => void;
  toggleTask: (taskId: string) => void;
  currentDate: Date;
}

export function useBDPlaybook(): UseBDPlaybookReturn {
  const [_jobs, setJobs] = useState<NotionJob[]>([]);
  const [programs, setPrograms] = useState<NotionProgram[]>([]);
  const [contacts, setContacts] = useState<NotionContact[]>([]);
  const [enrichedJobs, setEnrichedJobs] = useState<EnrichedJob[]>([]);
  const [playbook, setPlaybook] = useState<DailyPlaybook | null>(null);
  const [enrichmentStats, setEnrichmentStats] = useState<ReturnType<typeof getEnrichmentStats> | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConfigured, setIsConfigured] = useState(false);
  const [currentDate, setCurrentDate] = useState(new Date());

  // Load all data — tries backend API first, falls back to Notion
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Try backend-generated playbook first
      const dateStr = currentDate.toISOString().split('T')[0];
      const backendPlaybook = await fetchBackendPlaybook(dateStr);

      if (backendPlaybook && backendPlaybook.tasks.length > 0) {
        setPlaybook(backendPlaybook);
        setIsConfigured(true);
        setLoading(false);
        return;
      }
    } catch {
      // Backend unavailable, fall through to Notion
    }

    // Fall back to Notion-based generation
    const configured = isNotionConfigured();
    setIsConfigured(configured);

    if (!configured) {
      setLoading(false);
      setError('Backend API and Notion both unavailable. Please check your connections.');
      return;
    }

    try {
      // Fetch all data in parallel
      const [notionJobs, notionPrograms, notionContacts] = await Promise.all([
        fetchJobs(),
        fetchPrograms(),
        fetchAllContacts(),
      ]);

      setJobs(notionJobs);
      setPrograms(notionPrograms);
      setContacts(notionContacts);

      // Enrich jobs with program matching and contacts
      const enriched = enrichAllJobs(notionJobs, notionPrograms, notionContacts);
      setEnrichedJobs(enriched);

      // Generate enrichment stats
      const stats = getEnrichmentStats(enriched);
      setEnrichmentStats(stats);

      // Generate playbook for current date
      const generatedPlaybook = generateDailyPlaybook(
        enriched,
        notionContacts,
        notionPrograms,
        currentDate
      );
      setPlaybook(generatedPlaybook);

    } catch (err) {
      console.error('Error loading BD data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [currentDate]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Regenerate playbook when date changes
  useEffect(() => {
    if (enrichedJobs.length > 0 && contacts.length > 0 && programs.length > 0) {
      const generatedPlaybook = generateDailyPlaybook(
        enrichedJobs,
        contacts,
        programs,
        currentDate
      );
      setPlaybook(generatedPlaybook);
    }
  }, [currentDate, enrichedJobs, contacts, programs]);

  // Toggle task completion
  const toggleTask = useCallback((taskId: string) => {
    setPlaybook(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        tasks: prev.tasks.map(task =>
          task.id === taskId ? { ...task, completed: !task.completed } : task
        ),
      };
    });
  }, []);

  // Set playbook date
  const setDate = useCallback((date: Date) => {
    setCurrentDate(date);
  }, []);

  return {
    playbook,
    enrichedJobs,
    contacts,
    programs,
    loading,
    error,
    isConfigured,
    enrichmentStats,
    refresh: loadData,
    setDate,
    toggleTask,
    currentDate,
  };
}

// Hook for just enriched jobs
export function useEnrichedJobs() {
  const [jobs, setJobs] = useState<NotionJob[]>([]);
  const [programs, setPrograms] = useState<NotionProgram[]>([]);
  const [contacts, setContacts] = useState<NotionContact[]>([]);
  const [enrichedJobs, setEnrichedJobs] = useState<EnrichedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!isNotionConfigured()) {
      setLoading(false);
      setError('Notion not configured');
      return;
    }

    setLoading(true);
    try {
      const [notionJobs, notionPrograms, notionContacts] = await Promise.all([
        fetchJobs(),
        fetchPrograms(),
        fetchAllContacts(),
      ]);

      setJobs(notionJobs);
      setPrograms(notionPrograms);
      setContacts(notionContacts);

      const enriched = enrichAllJobs(notionJobs, notionPrograms, notionContacts);
      setEnrichedJobs(enriched);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return {
    jobs,
    programs,
    contacts,
    enrichedJobs,
    loading,
    error,
    refresh: loadData,
    stats: enrichedJobs.length > 0 ? getEnrichmentStats(enrichedJobs) : null,
  };
}
