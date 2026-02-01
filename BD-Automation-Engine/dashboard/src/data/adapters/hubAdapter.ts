/**
 * Hub Data Adapter
 *
 * Implements the DataAdapter interface for the Hub API (localhost:8100).
 * Provides access to 8,447+ records across contacts, programs, documents, activities, and jobs.
 */

import type { Job, Program, Contact, Contractor } from '../../types';
import type { DataAdapter, DataSourceStatus, SyncResult } from '../types';
import {
  hubApiClient,
  getHubApiUrl,
  setHubApiUrl,
  type HubSearchResult,
  type HubStats,
} from '../../services/hubApi';

// =============================================================================
// TRANSFORM FUNCTIONS
// =============================================================================

function transformHubJob(result: HubSearchResult): Job {
  const meta = result.metadata as Record<string, unknown>;
  return {
    id: result.id,
    title: (meta.title as string) || result.content?.slice(0, 100) || '',
    program: (meta.program as string) || '',
    agency: (meta.agency as string) || '',
    bd_priority: (meta.bd_priority as number) ?? (meta.bd_score as number) ?? null,
    clearance: (meta.clearance as string) || '',
    functional_area: (meta.functional_area as string) || '',
    status: (meta.status as string) || 'Open',
    location: (meta.location as string) || '',
    city: (meta.city as string) || '',
    company: (meta.company as string) || '',
    task_order: (meta.task_order as string) || '',
    source_url: (meta.source_url as string) || '',
    scraped_at: (meta.scraped_at as string) || (meta.created_at as string) || '',
    dcgs_relevance: (meta.dcgs_relevance as boolean) || false,
    source: 'hub',
    program_name: (meta.program_name as string) || (meta.program as string) || '',
    bd_score: (meta.bd_score as number) || (meta.bd_priority as number) || undefined,
    matched_programs: (meta.matched_programs as string[]) || [],
    matched_contacts: (meta.matched_contacts as string[]) || [],
  };
}

function transformHubProgram(result: HubSearchResult): Program {
  const meta = result.metadata as Record<string, unknown>;
  return {
    id: result.id,
    name: (meta.name as string) || result.content?.slice(0, 100) || '',
    acronym: (meta.acronym as string) || '',
    agency: (meta.agency as string) || (meta.agency_owner as string) || '',
    prime_contractor: (meta.prime_contractor as string) || '',
    prime_contractor_ids: (meta.prime_contractor_ids as string[]) || [],
    bd_priority: (meta.bd_priority as string) || 'Medium',
    program_type: (meta.program_type as string) || '',
    contract_vehicle: (meta.contract_vehicle as string) || '',
    contract_value: (meta.contract_value as string) || '',
    location: (meta.location as string) || (meta.key_locations as string) || '',
    clearance_requirements: (meta.clearance_requirements as string[]) || [],
    period_of_performance: (meta.period_of_performance as string) || '',
    recompete_date: (meta.recompete_date as string) || '',
    hiring_velocity: (meta.hiring_velocity as string) || '',
    pts_involvement: (meta.pts_involvement as string) || '',
    notes: (meta.notes as string) || '',
    description: (meta.description as string) || result.content || '',
    status: (meta.status as string) || '',
    priority: (meta.priority as string) || (meta.bd_priority as string) || '',
    job_count: (meta.job_count as number) || 0,
    contact_count: (meta.contact_count as number) || 0,
  };
}

function transformHubContact(result: HubSearchResult): Contact {
  const meta = result.metadata as Record<string, unknown>;
  const fullName = (meta.name as string) || result.content?.slice(0, 100) || '';
  const nameParts = fullName.split(' ');

  return {
    id: result.id,
    name: fullName,
    first_name: (meta.first_name as string) || nameParts[0] || '',
    title: (meta.title as string) || '',
    email: (meta.email as string) || '',
    phone: (meta.phone as string) || '',
    linkedin: (meta.linkedin as string) || (meta.linkedin_url as string) || '',
    company: (meta.company as string) || (meta.employer as string) || '',
    program: (meta.program as string) || '',
    tier: (meta.tier as number) || (meta.influence_tier as number) || 6,
    bd_priority: (meta.bd_priority as string) || '',
    relationship_status: (meta.relationship_status as string) || (meta.relationship_strength as string) || '',
    notes: (meta.notes as string) || '',
    source_db: (meta.source_db as string) || 'Hub',
    matched_programs: (meta.matched_programs as string[]) || (meta.programs as string[]) || [],
    last_name: nameParts.slice(1).join(' ') || '',
    linkedin_url: (meta.linkedin_url as string) || (meta.linkedin as string) || '',
    influence_tier: (meta.tier as number) || (meta.influence_tier as number) || undefined,
    location: (meta.location as string) || '',
    programs: (meta.programs as string[]) || (meta.matched_programs as string[]) || [],
  };
}

// Derive contractors from programs and contacts
function deriveContractors(programs: Program[], contacts: Contact[]): Contractor[] {
  const contractorMap = new Map<string, Contractor>();

  // Extract from prime contractors in programs
  for (const program of programs) {
    if (program.prime_contractor && !contractorMap.has(program.prime_contractor)) {
      contractorMap.set(program.prime_contractor, {
        id: `contractor-${program.prime_contractor.toLowerCase().replace(/\s+/g, '-')}`,
        name: program.prime_contractor,
        description: '',
        website: '',
        programs: [],
        contract_vehicles: [],
        locations: [],
        capabilities: [],
        job_count: 0,
        contact_count: 0,
      });
    }
    // Add program to contractor
    const contractor = contractorMap.get(program.prime_contractor);
    if (contractor && !contractor.programs.includes(program.name)) {
      contractor.programs.push(program.name);
    }
  }

  // Extract from contact companies
  for (const contact of contacts) {
    if (contact.company && !contractorMap.has(contact.company)) {
      contractorMap.set(contact.company, {
        id: `contractor-${contact.company.toLowerCase().replace(/\s+/g, '-')}`,
        name: contact.company,
        description: '',
        website: '',
        programs: [],
        contract_vehicles: [],
        locations: [],
        capabilities: [],
        job_count: 0,
        contact_count: 0,
      });
    }
    // Increment contact count
    const contractor = contractorMap.get(contact.company);
    if (contractor) {
      contractor.contact_count++;
    }
  }

  return Array.from(contractorMap.values());
}

// =============================================================================
// HUB ADAPTER IMPLEMENTATION
// =============================================================================

export class HubAdapter implements DataAdapter {
  type: 'hub' = 'hub';
  private lastFetchTime: Date | null = null;
  private cachedJobs: Job[] | null = null;
  private cachedPrograms: Program[] | null = null;
  private cachedContacts: Contact[] | null = null;
  private cachedContractors: Contractor[] | null = null;
  private cachedStats: HubStats | null = null;
  private error: string | null = null;
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes
  private connected = false;

  isConfigured(): boolean {
    // Hub is configured if we have a URL set
    return !!getHubApiUrl();
  }

  async testConnection(): Promise<boolean> {
    try {
      this.connected = await hubApiClient.testConnection();
      this.error = this.connected ? null : 'Hub API not responding';
      return this.connected;
    } catch (err) {
      this.connected = false;
      this.error = err instanceof Error ? err.message : 'Connection test failed';
      return false;
    }
  }

  async fetchStats(): Promise<HubStats | null> {
    try {
      this.cachedStats = await hubApiClient.getStats();
      return this.cachedStats;
    } catch (err) {
      console.warn('Failed to fetch Hub stats:', err);
      return null;
    }
  }

  async fetchJobs(): Promise<Job[]> {
    try {
      if (this.cachedJobs && this.isCacheValid()) {
        return this.cachedJobs;
      }

      const results = await hubApiClient.getJobs();
      this.cachedJobs = results.map(transformHubJob);
      this.lastFetchTime = new Date();
      this.connected = true;
      this.error = null;
      return this.cachedJobs;
    } catch (err) {
      this.error = err instanceof Error ? err.message : 'Failed to fetch jobs from Hub';
      this.connected = false;
      throw err;
    }
  }

  async fetchPrograms(): Promise<Program[]> {
    try {
      if (this.cachedPrograms && this.isCacheValid()) {
        return this.cachedPrograms;
      }

      const results = await hubApiClient.getPrograms();
      this.cachedPrograms = results.map(transformHubProgram);
      this.lastFetchTime = new Date();
      this.connected = true;
      this.error = null;
      return this.cachedPrograms;
    } catch (err) {
      this.error = err instanceof Error ? err.message : 'Failed to fetch programs from Hub';
      this.connected = false;
      throw err;
    }
  }

  async fetchContacts(): Promise<Contact[]> {
    try {
      if (this.cachedContacts && this.isCacheValid()) {
        return this.cachedContacts;
      }

      const results = await hubApiClient.getContacts();
      this.cachedContacts = results.map(transformHubContact);
      this.lastFetchTime = new Date();
      this.connected = true;
      this.error = null;
      return this.cachedContacts;
    } catch (err) {
      this.error = err instanceof Error ? err.message : 'Failed to fetch contacts from Hub';
      this.connected = false;
      throw err;
    }
  }

  async fetchContactsByTier(): Promise<Record<number, Contact[]>> {
    const contacts = await this.fetchContacts();
    const byTier: Record<number, Contact[]> = {};

    for (const contact of contacts) {
      const tier = contact.tier || 6;
      if (!byTier[tier]) {
        byTier[tier] = [];
      }
      byTier[tier].push(contact);
    }

    return byTier;
  }

  async fetchContractors(): Promise<Contractor[]> {
    try {
      if (this.cachedContractors && this.isCacheValid()) {
        return this.cachedContractors;
      }

      // Derive contractors from programs and contacts
      const [programs, contacts] = await Promise.all([
        this.fetchPrograms(),
        this.fetchContacts(),
      ]);

      this.cachedContractors = deriveContractors(programs, contacts);
      return this.cachedContractors;
    } catch (err) {
      this.error = err instanceof Error ? err.message : 'Failed to derive contractors';
      throw err;
    }
  }

  async sync(): Promise<SyncResult> {
    this.clearCache();

    const errors: string[] = [];
    let recordsUpdated = 0;

    // Test connection first
    const isConnected = await this.testConnection();
    if (!isConnected) {
      return {
        success: false,
        recordsUpdated: 0,
        errors: ['Hub API not responding. Is the server running on ' + getHubApiUrl() + '?'],
        timestamp: new Date(),
      };
    }

    try {
      const jobs = await this.fetchJobs();
      recordsUpdated += jobs.length;
    } catch (err) {
      errors.push(`Jobs: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }

    try {
      const programs = await this.fetchPrograms();
      recordsUpdated += programs.length;
    } catch (err) {
      errors.push(`Programs: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }

    try {
      const contacts = await this.fetchContacts();
      recordsUpdated += contacts.length;
    } catch (err) {
      errors.push(`Contacts: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }

    try {
      const contractors = await this.fetchContractors();
      recordsUpdated += contractors.length;
    } catch (err) {
      errors.push(`Contractors: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }

    return {
      success: errors.length === 0,
      recordsUpdated,
      errors,
      timestamp: new Date(),
    };
  }

  getStatus(): DataSourceStatus {
    return {
      type: 'hub',
      configured: this.isConfigured(),
      connected: this.connected,
      lastSync: this.lastFetchTime,
      error: this.error,
    };
  }

  getCachedStats(): HubStats | null {
    return this.cachedStats;
  }

  // URL management
  setUrl(url: string): void {
    setHubApiUrl(url);
    this.clearCache();
  }

  getUrl(): string {
    return getHubApiUrl();
  }

  private isCacheValid(): boolean {
    if (!this.lastFetchTime) return false;
    return Date.now() - this.lastFetchTime.getTime() < this.cacheTimeout;
  }

  private clearCache(): void {
    this.cachedJobs = null;
    this.cachedPrograms = null;
    this.cachedContacts = null;
    this.cachedContractors = null;
    this.cachedStats = null;
    this.lastFetchTime = null;
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

export const hubAdapter = new HubAdapter();

export default hubAdapter;
