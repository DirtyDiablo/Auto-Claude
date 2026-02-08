import { useState, useMemo, useEffect, useCallback } from 'react';
import {
  Search, Mail, Phone, Linkedin, Building2, User, ChevronDown, ChevronRight,
  Network, LayoutGrid, Table2, Filter, X, ChevronUp, RefreshCw,
} from 'lucide-react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import type { Contact } from '../types';
import { TIER_LABELS, type ContactTier } from '../types';
import type { NativeNodeType } from '../configs/nativeNodeConfigs';
import { hubApiClient } from '../services/hubApi';

interface ContactsProps {
  contacts: Record<string, Contact[]>;
  loading: boolean;
  initialCompanyFilter?: string;
  onNavigateToProgram?: (programName: string) => void;
  onNavigateToMindMap?: (entityType: NativeNodeType, entityId: string, entityLabel: string) => void;
  onNavigateToContact?: (contactName: string) => void;
}

const TIER_COLORS: Record<number, string> = {
  1: 'border-purple-500 bg-purple-50',
  2: 'border-blue-500 bg-blue-50',
  3: 'border-cyan-500 bg-cyan-50',
  4: 'border-emerald-500 bg-emerald-50',
  5: 'border-amber-500 bg-amber-50',
  6: 'border-slate-400 bg-slate-50',
};

const TIER_BADGE_COLORS: Record<number, string> = {
  1: 'bg-purple-600 text-white',
  2: 'bg-blue-600 text-white',
  3: 'bg-cyan-600 text-white',
  4: 'bg-emerald-600 text-white',
  5: 'bg-amber-600 text-white',
  6: 'bg-slate-500 text-white',
};

// =============================================================================
// CONTACT CARD (for card view)
// =============================================================================

function ContactCard({
  contact,
  onNavigateToProgram,
  onNavigateToMindMap,
  onNavigateToContact,
}: {
  contact: Contact;
  onNavigateToProgram?: (programName: string) => void;
  onNavigateToMindMap?: (entityType: NativeNodeType, entityId: string, entityLabel: string) => void;
  onNavigateToContact?: (contactName: string) => void;
}) {
  const tierColor = TIER_COLORS[contact.tier] || TIER_COLORS[6];

  return (
    <div className={`bg-white rounded-lg shadow-sm border-l-4 ${tierColor} p-4 hover:shadow-md transition-shadow`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center">
          <User className="h-5 w-5 text-slate-500" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900 truncate">
            {onNavigateToContact ? (
              <button
                onClick={() => onNavigateToContact(contact.name || contact.first_name || '')}
                className="text-left hover:text-blue-600 transition-colors"
              >
                {contact.name || `${contact.first_name || ''} (No Name)`.trim()}
              </button>
            ) : (
              contact.name || `${contact.first_name || ''} (No Name)`.trim()
            )}
          </h3>
          {contact.title && <p className="text-sm text-slate-600 truncate">{contact.title}</p>}
          {contact.company && (
            <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
              <Building2 className="h-3.5 w-3.5" />
              <span className="truncate">{contact.company}</span>
            </p>
          )}
        </div>
        {onNavigateToMindMap && (
          <button
            onClick={() => onNavigateToMindMap('CONTACT', contact.id, contact.name || contact.first_name || 'Contact')}
            className="flex-shrink-0 p-1.5 text-slate-400 hover:text-purple-600 transition-colors rounded hover:bg-purple-50"
            title="Explore in Mind Map"
          >
            <Network className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className="mt-3 space-y-1.5">
        {contact.email && (
          <a href={`mailto:${contact.email}`} className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-2 truncate">
            <Mail className="h-3.5 w-3.5 flex-shrink-0" /> <span className="truncate">{contact.email}</span>
          </a>
        )}
        {contact.phone && (
          <a href={`tel:${contact.phone}`} className="text-sm text-slate-600 hover:text-slate-800 flex items-center gap-2">
            <Phone className="h-3.5 w-3.5 flex-shrink-0" /> <span>{contact.phone}</span>
          </a>
        )}
        {contact.linkedin && (
          <a href={contact.linkedin} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-2">
            <Linkedin className="h-3.5 w-3.5 flex-shrink-0" /> <span>LinkedIn Profile</span>
          </a>
        )}
      </div>
      {(contact.program || contact.relationship_status) && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
          {contact.program && (
            <button
              onClick={() => onNavigateToProgram?.(contact.program)}
              className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
            >
              {contact.program}
            </button>
          )}
          {contact.relationship_status && (
            <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">
              {contact.relationship_status}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// TIER SECTION (for card view)
// =============================================================================

function TierSection({
  tier, contacts, searchQuery, defaultExpanded = false,
  onNavigateToProgram, onNavigateToMindMap, onNavigateToContact,
}: {
  tier: number;
  contacts: Contact[];
  searchQuery: string;
  defaultExpanded?: boolean;
  onNavigateToProgram?: (programName: string) => void;
  onNavigateToMindMap?: (entityType: NativeNodeType, entityId: string, entityLabel: string) => void;
  onNavigateToContact?: (contactName: string) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const filteredContacts = useMemo(() => {
    if (!searchQuery) return contacts;
    const query = searchQuery.toLowerCase();
    return contacts.filter(
      (c) =>
        c.name?.toLowerCase().includes(query) ||
        c.first_name?.toLowerCase().includes(query) ||
        c.title?.toLowerCase().includes(query) ||
        c.company?.toLowerCase().includes(query) ||
        c.email?.toLowerCase().includes(query) ||
        c.program?.toLowerCase().includes(query)
    );
  }, [contacts, searchQuery]);

  if (filteredContacts.length === 0) return null;

  const tierLabel = TIER_LABELS[tier as ContactTier] || `Tier ${tier}`;
  const badgeColor = TIER_BADGE_COLORS[tier] || TIER_BADGE_COLORS[6];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? <ChevronDown className="h-5 w-5 text-slate-400" /> : <ChevronRight className="h-5 w-5 text-slate-400" />}
          <span className={`text-xs font-bold px-2 py-1 rounded ${badgeColor}`}>Tier {tier}</span>
          <span className="font-semibold text-slate-900">{tierLabel}</span>
        </div>
        <span className="text-sm text-slate-500">{filteredContacts.length} contacts</span>
      </button>
      {isExpanded && (
        <div className="px-4 pb-4">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {filteredContacts.slice(0, 50).map((contact) => (
              <ContactCard
                key={contact.id}
                contact={contact}
                onNavigateToProgram={onNavigateToProgram}
                onNavigateToMindMap={onNavigateToMindMap}
                onNavigateToContact={onNavigateToContact}
              />
            ))}
          </div>
          {filteredContacts.length > 50 && (
            <p className="mt-4 text-center text-sm text-slate-500">
              Showing 50 of {filteredContacts.length} contacts
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// QDRANT FILTER BAR
// =============================================================================

interface QdrantFilters {
  company: string;
  program: string;
  clearance: string;
  status: string;
}

function FilterBar({
  filters, onChange, onSearch, searching,
}: {
  filters: QdrantFilters;
  onChange: (filters: QdrantFilters) => void;
  onSearch: () => void;
  searching: boolean;
}) {
  const hasFilters = Object.values(filters).some(v => v !== '');

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <Filter className="w-4 h-4" /> Qdrant Payload Filters
        </div>
        {hasFilters && (
          <button
            onClick={() => onChange({ company: '', program: '', clearance: '', status: '' })}
            className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1"
          >
            <X className="w-3 h-3" /> Clear
          </button>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <input
          type="text"
          placeholder="Company / Prime..."
          value={filters.company}
          onChange={(e) => onChange({ ...filters, company: e.target.value })}
          className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <input
          type="text"
          placeholder="Program..."
          value={filters.program}
          onChange={(e) => onChange({ ...filters, program: e.target.value })}
          className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <input
          type="text"
          placeholder="Clearance..."
          value={filters.clearance}
          onChange={(e) => onChange({ ...filters, clearance: e.target.value })}
          className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <input
          type="text"
          placeholder="Status..."
          value={filters.status}
          onChange={(e) => onChange({ ...filters, status: e.target.value })}
          className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <button
        onClick={onSearch}
        disabled={searching || !hasFilters}
        className="flex items-center gap-2 px-4 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {searching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
        Search Qdrant
      </button>
    </div>
  );
}

// =============================================================================
// TANSTACK TABLE VIEW
// =============================================================================

interface FlatContact {
  id: string;
  name: string;
  title: string;
  company: string;
  email: string;
  phone: string;
  tier: number;
  program: string;
  bd_priority: string;
  relationship_status: string;
}

function ContactsTable({
  data, onNavigateToContact,
}: {
  data: FlatContact[];
  onNavigateToContact?: (name: string) => void;
}) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns = useMemo<ColumnDef<FlatContact>[]>(() => [
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => (
        onNavigateToContact ? (
          <button
            onClick={() => onNavigateToContact(row.original.name)}
            className="text-blue-600 hover:text-blue-800 font-medium text-left"
          >
            {row.original.name}
          </button>
        ) : (
          <span className="font-medium text-slate-900">{row.original.name}</span>
        )
      ),
    },
    { accessorKey: 'title', header: 'Title' },
    { accessorKey: 'company', header: 'Company' },
    {
      accessorKey: 'tier',
      header: 'Tier',
      cell: ({ row }) => {
        const t = row.original.tier;
        const badge = TIER_BADGE_COLORS[t] || TIER_BADGE_COLORS[6];
        return t > 0 ? <span className={`text-xs font-bold px-2 py-0.5 rounded ${badge}`}>T{t}</span> : '-';
      },
    },
    { accessorKey: 'program', header: 'Program' },
    { accessorKey: 'bd_priority', header: 'BD Priority' },
    { accessorKey: 'relationship_status', header: 'Status' },
    {
      accessorKey: 'email',
      header: 'Email',
      cell: ({ row }) => row.original.email ? (
        <a href={`mailto:${row.original.email}`} className="text-blue-600 hover:text-blue-800 truncate block max-w-[200px]">
          {row.original.email}
        </a>
      ) : '-',
    },
  ], [onNavigateToContact]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 50 } },
  });

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(header => (
                  <th
                    key={header.id}
                    className="text-left px-4 py-3 font-medium text-slate-600 cursor-pointer select-none hover:bg-slate-100"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === 'asc' && <ChevronUp className="w-3 h-3" />}
                      {header.column.getIsSorted() === 'desc' && <ChevronDown className="w-3 h-3" />}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-100">
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-500">
                  No contacts match the current filters
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map(row => (
                <tr key={row.id} className="hover:bg-slate-50">
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-4 py-2.5 text-slate-700">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 text-sm text-slate-600">
        <span>
          Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}-
          {Math.min(
            (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
            data.length
          )} of {data.length}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="px-3 py-1 rounded bg-slate-100 hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="px-3 py-1 rounded bg-slate-100 hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// MAIN CONTACTS COMPONENT
// =============================================================================

export function Contacts({
  contacts,
  loading,
  initialCompanyFilter,
  onNavigateToProgram,
  onNavigateToMindMap,
  onNavigateToContact,
}: ContactsProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [qdrantFilters, setQdrantFilters] = useState<QdrantFilters>({
    company: '', program: '', clearance: '', status: '',
  });
  const [qdrantResults, setQdrantResults] = useState<FlatContact[] | null>(null);
  const [qdrantSearching, setQdrantSearching] = useState(false);

  // Apply initial filter from cross-navigation
  useEffect(() => {
    if (initialCompanyFilter) {
      setSearchQuery(initialCompanyFilter);
    }
  }, [initialCompanyFilter]);

  // Flatten contacts for table view
  const flatContacts = useMemo<FlatContact[]>(() => {
    const all: FlatContact[] = [];
    for (const tier of Object.keys(contacts)) {
      for (const c of contacts[Number(tier)] || []) {
        all.push({
          id: c.id,
          name: c.name || c.first_name || '',
          title: c.title || '',
          company: c.company || '',
          email: c.email || '',
          phone: c.phone || '',
          tier: c.tier || Number(tier),
          program: c.program || '',
          bd_priority: c.bd_priority || '',
          relationship_status: c.relationship_status || '',
        });
      }
    }
    return all;
  }, [contacts]);

  // Filter flat contacts by search query for table view
  const filteredFlat = useMemo(() => {
    if (qdrantResults) return qdrantResults;
    if (!searchQuery) return flatContacts;
    const q = searchQuery.toLowerCase();
    return flatContacts.filter(c =>
      c.name.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      c.company.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q) ||
      c.program.toLowerCase().includes(q)
    );
  }, [flatContacts, searchQuery, qdrantResults]);

  // Get total contact count
  const totalContacts = useMemo(() => {
    return Object.values(contacts).reduce((sum, arr) => sum + arr.length, 0);
  }, [contacts]);

  // Get sorted tiers
  const sortedTiers = useMemo(() => {
    return Object.keys(contacts).map(Number).sort((a, b) => a - b);
  }, [contacts]);

  // Qdrant filter search
  const handleQdrantSearch = useCallback(async () => {
    setQdrantSearching(true);
    try {
      const params: Record<string, string | undefined> = {};
      if (qdrantFilters.company) params.company = qdrantFilters.company;
      if (qdrantFilters.program) params.program = qdrantFilters.program;
      if (qdrantFilters.clearance) params.clearance = qdrantFilters.clearance;
      if (qdrantFilters.status) params.status = qdrantFilters.status;
      if (searchQuery) params.query = searchQuery;

      const res = await hubApiClient.filterContacts({ ...params, limit: 100 });
      setQdrantResults(res.contacts.map(c => ({
        id: String(c.id || ''),
        name: String(c.name || c.Name || ''),
        title: String(c.title || c.Title || c['Job Title'] || ''),
        company: String(c.company || c.Primes || c.Company || ''),
        email: String(c.email || c.Email || ''),
        phone: String(c.phone || c.Phone || ''),
        tier: Number(c.tier || c.Tier || 0),
        program: String(c.program || c.Programs || ''),
        bd_priority: String(c.bd_priority || c['BD Priority'] || ''),
        relationship_status: String(c.relationship_status || c.Status || ''),
      })));
    } catch {
      setQdrantResults(null);
    } finally {
      setQdrantSearching(false);
    }
  }, [qdrantFilters, searchQuery]);

  // Clear Qdrant results when filters are cleared
  useEffect(() => {
    const hasFilters = Object.values(qdrantFilters).some(v => v !== '');
    if (!hasFilters) setQdrantResults(null);
  }, [qdrantFilters]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Contact Intelligence</h1>
          <p className="text-slate-500">
            {qdrantResults ? `${qdrantResults.length} filtered results` : `${totalContacts} total contacts`}
            {' '} organized by hierarchy tier
          </p>
        </div>
        <div className="flex gap-1 bg-slate-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('cards')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'cards' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <LayoutGrid className="h-4 w-4" /> Cards
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'table' ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <Table2 className="h-4 w-4" /> Table
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search contacts by name, title, company..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Qdrant Filters (table view only) */}
      {viewMode === 'table' && (
        <div className="mb-4">
          <FilterBar
            filters={qdrantFilters}
            onChange={setQdrantFilters}
            onSearch={handleQdrantSearch}
            searching={qdrantSearching}
          />
        </div>
      )}

      {/* Tier Legend */}
      <div className="mb-4 flex flex-wrap gap-2">
        {sortedTiers.map((tier) => {
          const count = contacts[tier]?.length || 0;
          const badgeColor = TIER_BADGE_COLORS[tier] || TIER_BADGE_COLORS[6];
          return (
            <span key={tier} className={`text-xs font-medium px-2 py-1 rounded ${badgeColor}`}>
              Tier {tier}: {count}
            </span>
          );
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {viewMode === 'cards' ? (
          <div className="space-y-4">
            {sortedTiers.map((tier) => (
              <TierSection
                key={tier}
                tier={tier}
                contacts={contacts[tier] || []}
                searchQuery={searchQuery}
                defaultExpanded={tier === 1}
                onNavigateToProgram={onNavigateToProgram}
                onNavigateToMindMap={onNavigateToMindMap}
                onNavigateToContact={onNavigateToContact}
              />
            ))}
          </div>
        ) : (
          <ContactsTable
            data={filteredFlat}
            onNavigateToContact={onNavigateToContact}
          />
        )}
      </div>
    </div>
  );
}
