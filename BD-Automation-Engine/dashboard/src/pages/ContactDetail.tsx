import { useState, useEffect, useCallback } from 'react';
import {
  User, ArrowLeft, Mail, Phone, Linkedin, Building2, Shield, Star,
  FileText, Users, MessageSquare, RefreshCw, Network,
} from 'lucide-react';
import { hubApiClient } from '../services/hubApi';

interface ContactDetailProps {
  contactName: string;
  onBack: () => void;
  onNavigateToProgram?: (programName: string) => void;
}

type DetailTab = 'overview' | 'intelligence' | 'relationships' | 'outreach' | 'documents';

const TABS: Array<{ id: DetailTab; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: 'overview', label: 'Overview', icon: User },
  { id: 'intelligence', label: 'Intelligence', icon: Star },
  { id: 'relationships', label: 'Relationships', icon: Users },
  { id: 'outreach', label: 'Outreach History', icon: MessageSquare },
  { id: 'documents', label: 'Documents', icon: FileText },
];

interface ContactData {
  id: string;
  name: string;
  title?: string;
  company?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  tier?: number;
  bd_priority?: string;
  program?: string;
  programs?: string[];
  clearance?: string;
  location?: string;
  relationship_status?: string;
  notes?: string;
  source_db?: string;
  score?: number;
  [key: string]: unknown;
}

interface IntelResult {
  answer: string;
  sources: Array<{ collection: string; id: string; content: string; score: number }>;
}

interface MemoryContext {
  contact: { name: string; title: string; company: string };
  call_history: Array<{ date: string; notes: string; outcome: string }>;
  interactions: Array<{ type: string; date: string; summary: string }>;
  insights: string[];
}

interface RelatedContact {
  id: string;
  name: string;
  title?: string;
  company?: string;
  score: number;
}

interface RelatedDoc {
  id: string;
  content: string;
  collection: string;
  score: number;
  metadata: Record<string, unknown>;
}

const TIER_LABELS: Record<number, string> = {
  1: 'Executive (C-Suite)',
  2: 'Senior Leadership',
  3: 'Director Level',
  4: 'Manager Level',
  5: 'Senior Individual',
  6: 'Individual Contributor',
};

const TIER_BADGE_COLORS: Record<number, string> = {
  1: 'bg-purple-600 text-white',
  2: 'bg-blue-600 text-white',
  3: 'bg-cyan-600 text-white',
  4: 'bg-emerald-600 text-white',
  5: 'bg-amber-600 text-white',
  6: 'bg-slate-500 text-white',
};

export function ContactDetail({ contactName, onBack, onNavigateToProgram }: ContactDetailProps) {
  const [activeTab, setActiveTab] = useState<DetailTab>('overview');
  const [contact, setContact] = useState<ContactData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tab-specific data
  const [intel, setIntel] = useState<IntelResult | null>(null);
  const [intelLoading, setIntelLoading] = useState(false);
  const [memoryCtx, setMemoryCtx] = useState<MemoryContext | null>(null);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [relatedContacts, setRelatedContacts] = useState<RelatedContact[]>([]);
  const [relatedLoading, setRelatedLoading] = useState(false);
  const [docs, setDocs] = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  // Load contact data
  const fetchContact = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await hubApiClient.filterContacts({ query: contactName, limit: 5 });
      if (res.contacts.length > 0) {
        // Find best match
        const match = res.contacts.find(
          (c) => String(c.name || c.Name || '').toLowerCase() === contactName.toLowerCase()
        ) || res.contacts[0];
        setContact({
          id: String(match.id || ''),
          name: String(match.name || match.Name || contactName),
          title: String(match.title || match.Title || match['Job Title'] || ''),
          company: String(match.company || match.Primes || match.Company || ''),
          email: String(match.email || match.Email || ''),
          phone: String(match.phone || match.Phone || ''),
          linkedin: String(match.linkedin || match.LinkedIn || ''),
          tier: Number(match.tier || match.Tier || 0),
          bd_priority: String(match.bd_priority || match['BD Priority'] || ''),
          program: String(match.program || match.Programs || ''),
          programs: Array.isArray(match.programs || match.Programs)
            ? (match.programs || match.Programs) as string[]
            : String(match.programs || match.Programs || '').split(',').filter(Boolean),
          clearance: String(match.clearance || match.Clearances || ''),
          location: String(match.location || match.Location || ''),
          relationship_status: String(match.relationship_status || match.Status || ''),
          notes: String(match.notes || match.Notes || ''),
          source_db: String(match.source_db || match.Source || ''),
          score: Number(match.score || 0),
        });
      } else {
        setError(`No contact found matching "${contactName}"`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load contact');
    } finally {
      setLoading(false);
    }
  }, [contactName]);

  useEffect(() => { fetchContact(); }, [fetchContact]);

  // Load intelligence on tab switch
  useEffect(() => {
    if (activeTab === 'intelligence' && !intel && !intelLoading) {
      setIntelLoading(true);
      hubApiClient.askSmart(`What do we know about ${contactName}? Include role, programs, and relationship history.`)
        .then(res => setIntel({ answer: res.answer, sources: res.sources }))
        .catch(() => setIntel({ answer: 'Intelligence not available', sources: [] }))
        .finally(() => setIntelLoading(false));
    }
  }, [activeTab, contactName, intel, intelLoading]);

  // Load memory context on outreach tab
  useEffect(() => {
    if (activeTab === 'outreach' && !memoryCtx && !memoryLoading) {
      setMemoryLoading(true);
      hubApiClient.getContactContext(contactName)
        .then(res => setMemoryCtx(res))
        .catch(() => setMemoryCtx({
          contact: { name: contactName, title: '', company: '' },
          call_history: [],
          interactions: [],
          insights: [],
        }))
        .finally(() => setMemoryLoading(false));
    }
  }, [activeTab, contactName, memoryCtx, memoryLoading]);

  // Load relationships
  useEffect(() => {
    if (activeTab === 'relationships' && relatedContacts.length === 0 && !relatedLoading) {
      setRelatedLoading(true);
      const company = contact?.company || '';
      hubApiClient.filterContacts({ company: company || undefined, limit: 20 })
        .then(res => {
          setRelatedContacts(res.contacts
            .filter(c => String(c.name || c.Name || '') !== contactName)
            .slice(0, 15)
            .map(c => ({
              id: String(c.id || ''),
              name: String(c.name || c.Name || ''),
              title: String(c.title || c.Title || c['Job Title'] || ''),
              company: String(c.company || c.Primes || ''),
              score: Number(c.score || 0),
            })));
        })
        .catch(() => setRelatedContacts([]))
        .finally(() => setRelatedLoading(false));
    }
  }, [activeTab, contact?.company, contactName, relatedContacts.length, relatedLoading]);

  // Load documents
  useEffect(() => {
    if (activeTab === 'documents' && docs.length === 0 && !docsLoading) {
      setDocsLoading(true);
      hubApiClient.search(contactName, 'documents', 10)
        .then(res => setDocs(res.map(r => ({
          id: r.id,
          content: r.content,
          collection: r.collection,
          score: r.score,
          metadata: r.metadata,
        }))))
        .catch(() => setDocs([]))
        .finally(() => setDocsLoading(false));
    }
  }, [activeTab, contactName, docs.length, docsLoading]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !contact) {
    return (
      <div className="h-full overflow-auto p-6">
        <button onClick={onBack} className="flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4">
          <ArrowLeft className="w-4 h-4" /> Back to Contacts
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error || 'Contact not found'}
        </div>
      </div>
    );
  }

  const tierNum = contact.tier || 6;
  const tierLabel = TIER_LABELS[tierNum] || `Tier ${tierNum}`;
  const tierBadge = TIER_BADGE_COLORS[tierNum] || TIER_BADGE_COLORS[6];

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      {/* Back Button */}
      <button onClick={onBack} className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Contacts
      </button>

      {/* Header Card */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold">
            {contact.name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{contact.name}</h1>
              <span className={`text-xs font-bold px-2 py-1 rounded ${tierBadge}`}>
                Tier {tierNum}
              </span>
              {contact.bd_priority && contact.bd_priority !== 'undefined' && (
                <span className="text-xs px-2 py-1 rounded bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
                  {contact.bd_priority}
                </span>
              )}
            </div>
            {contact.title && contact.title !== 'undefined' && (
              <p className="text-lg text-slate-600 dark:text-slate-400 mt-1">{contact.title}</p>
            )}
            <div className="flex flex-wrap gap-4 mt-3 text-sm text-slate-500 dark:text-slate-400">
              {contact.company && contact.company !== 'undefined' && (
                <span className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4" /> {contact.company}
                </span>
              )}
              {contact.location && contact.location !== 'undefined' && (
                <span className="flex items-center gap-1.5">
                  <Network className="w-4 h-4" /> {contact.location}
                </span>
              )}
              {contact.clearance && contact.clearance !== 'undefined' && (
                <span className="flex items-center gap-1.5">
                  <Shield className="w-4 h-4" /> {contact.clearance}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-3 mt-3">
              {contact.email && contact.email !== 'undefined' && (
                <a href={`mailto:${contact.email}`} className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5" /> {contact.email}
                </a>
              )}
              {contact.phone && contact.phone !== 'undefined' && (
                <a href={`tel:${contact.phone}`} className="text-sm text-slate-600 hover:text-slate-800 flex items-center gap-1.5">
                  <Phone className="w-3.5 h-3.5" /> {contact.phone}
                </a>
              )}
              {contact.linkedin && contact.linkedin !== 'undefined' && (
                <a href={contact.linkedin} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1.5">
                  <Linkedin className="w-3.5 h-3.5" /> LinkedIn
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700">
        {TABS.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && (
          <OverviewTab contact={contact} tierLabel={tierLabel} onNavigateToProgram={onNavigateToProgram} />
        )}
        {activeTab === 'intelligence' && (
          <IntelligenceTab intel={intel} loading={intelLoading} />
        )}
        {activeTab === 'relationships' && (
          <RelationshipsTab contacts={relatedContacts} loading={relatedLoading} company={contact.company || ''} />
        )}
        {activeTab === 'outreach' && (
          <OutreachTab ctx={memoryCtx} loading={memoryLoading} />
        )}
        {activeTab === 'documents' && (
          <DocumentsTab docs={docs} loading={docsLoading} />
        )}
      </div>
    </div>
  );
}

// =============================================================================
// OVERVIEW TAB
// =============================================================================

function OverviewTab({
  contact, tierLabel, onNavigateToProgram,
}: {
  contact: ContactData;
  tierLabel: string;
  onNavigateToProgram?: (name: string) => void;
}) {
  const fields = [
    { label: 'Tier', value: `${contact.tier} - ${tierLabel}` },
    { label: 'BD Priority', value: contact.bd_priority },
    { label: 'Relationship Status', value: contact.relationship_status },
    { label: 'Clearance', value: contact.clearance },
    { label: 'Location', value: contact.location },
    { label: 'Source', value: contact.source_db },
  ].filter(f => f.value && f.value !== 'undefined' && f.value !== '0');

  const programs = contact.programs?.filter(p => p && p !== 'undefined') || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Details */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Contact Details</h3>
        <dl className="space-y-3">
          {fields.map(f => (
            <div key={f.label} className="flex justify-between">
              <dt className="text-sm text-slate-500 dark:text-slate-400">{f.label}</dt>
              <dd className="text-sm font-medium text-slate-900 dark:text-slate-100">{f.value}</dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Programs */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">Associated Programs</h3>
        {programs.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {programs.map(p => (
              <button
                key={p}
                onClick={() => onNavigateToProgram?.(p.trim())}
                className="px-3 py-1.5 text-sm bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
              >
                {p.trim()}
              </button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500 dark:text-slate-400">No programs linked</p>
        )}

        {contact.notes && contact.notes !== 'undefined' && (
          <div className="mt-6">
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Notes</h4>
            <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">{contact.notes}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// INTELLIGENCE TAB
// =============================================================================

function IntelligenceTab({ intel, loading }: { intel: IntelResult | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
        <span className="text-slate-600 dark:text-slate-400">Querying AI intelligence...</span>
      </div>
    );
  }

  if (!intel) return null;

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
          <Star className="w-5 h-5 text-yellow-500" /> AI Intelligence Summary
        </h3>
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{intel.answer}</p>
        </div>
      </div>

      {intel.sources.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-5">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Sources ({intel.sources.length})</h3>
          <div className="space-y-2">
            {intel.sources.map((s, i) => (
              <div key={i} className="flex items-start gap-3 py-2 border-b border-slate-100 dark:border-slate-700 last:border-0">
                <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 flex-shrink-0">
                  {s.collection}
                </span>
                <p className="text-sm text-slate-600 dark:text-slate-400 truncate">{s.content}</p>
                <span className="text-xs text-slate-400 flex-shrink-0">{(s.score * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// RELATIONSHIPS TAB
// =============================================================================

function RelationshipsTab({
  contacts, loading, company,
}: {
  contacts: RelatedContact[];
  loading: boolean;
  company: string;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
        <span className="text-slate-600 dark:text-slate-400">Loading relationships...</span>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Colleagues at {company || 'Same Organization'}
        </h3>
        <p className="text-sm text-slate-500">{contacts.length} related contacts</p>
      </div>
      {contacts.length === 0 ? (
        <div className="px-5 py-8 text-center text-slate-500">No related contacts found</div>
      ) : (
        <table className="w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Name</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Title</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600 dark:text-slate-400">Company</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {contacts.map(c => (
              <tr key={c.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                <td className="px-4 py-3 text-slate-900 dark:text-slate-100 font-medium">{c.name}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{c.title || '-'}</td>
                <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{c.company || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// =============================================================================
// OUTREACH HISTORY TAB
// =============================================================================

function OutreachTab({ ctx, loading }: { ctx: MemoryContext | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
        <span className="text-slate-600 dark:text-slate-400">Loading outreach history...</span>
      </div>
    );
  }

  if (!ctx) return null;

  const hasHistory = ctx.call_history.length > 0 || ctx.interactions.length > 0;

  return (
    <div className="space-y-6">
      {/* Insights */}
      {ctx.insights.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-5">
          <h3 className="text-sm font-semibold text-yellow-800 dark:text-yellow-400 mb-2">Key Insights</h3>
          <ul className="list-disc list-inside space-y-1">
            {ctx.insights.map((insight, i) => (
              <li key={i} className="text-sm text-yellow-700 dark:text-yellow-500">{insight}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Call History */}
      {ctx.call_history.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Call History</h3>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            {ctx.call_history.map((call, i) => (
              <div key={i} className="px-5 py-3">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">{call.outcome}</span>
                  <span className="text-xs text-slate-500">{call.date}</span>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400">{call.notes}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interactions */}
      {ctx.interactions.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Interactions</h3>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            {ctx.interactions.map((int, i) => (
              <div key={i} className="px-5 py-3 flex items-start gap-3">
                <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 flex-shrink-0">
                  {int.type}
                </span>
                <p className="text-sm text-slate-600 dark:text-slate-400 flex-1">{int.summary}</p>
                <span className="text-xs text-slate-500 flex-shrink-0">{int.date}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!hasHistory && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-8 text-center text-slate-500">
          <MessageSquare className="w-8 h-8 mx-auto mb-3 text-slate-400" />
          <p>No outreach history recorded for this contact</p>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// DOCUMENTS TAB
// =============================================================================

function DocumentsTab({ docs, loading }: { docs: RelatedDoc[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-3" />
        <span className="text-slate-600 dark:text-slate-400">Searching documents...</span>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Related Documents</h3>
        <p className="text-sm text-slate-500">{docs.length} documents found</p>
      </div>
      {docs.length === 0 ? (
        <div className="px-5 py-8 text-center text-slate-500">
          <FileText className="w-8 h-8 mx-auto mb-3 text-slate-400" />
          <p>No related documents found</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-100 dark:divide-slate-700">
          {docs.map(doc => (
            <div key={doc.id} className="px-5 py-4">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-4 h-4 text-slate-400" />
                <span className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400">
                  {doc.collection}
                </span>
                <span className="text-xs text-slate-400 ml-auto">{(doc.score * 100).toFixed(0)}% match</span>
              </div>
              <p className="text-sm text-slate-700 dark:text-slate-300">{doc.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
