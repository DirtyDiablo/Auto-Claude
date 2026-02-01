import React, { useState, useEffect } from 'react';
import {
  Phone,
  TrendingUp,
  Users,
  Building2,
  MapPin,
  AlertTriangle,
  CheckCircle,
  Target,
  BarChart3,
  Activity,
  Clock
} from 'lucide-react';
import type {
  CallNotesPrime,
  CallNotesProgram,
  CallNotesContact,
  CallNotesLocation,
  CallNotesGapAnalysis,
  CallNotesStats,
  CallNotesSummary
} from '../types';

const CallIntelligence: React.FC = () => {
  const [primes, setPrimes] = useState<CallNotesPrime[]>([]);
  const [programs, setPrograms] = useState<CallNotesProgram[]>([]);
  const [contacts, setContacts] = useState<CallNotesContact[]>([]);
  const [locations, setLocations] = useState<CallNotesLocation[]>([]);
  const [gaps, setGaps] = useState<CallNotesGapAnalysis | null>(null);
  const [stats, setStats] = useState<CallNotesStats | null>(null);
  const [summary, setSummary] = useState<CallNotesSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'primes' | 'programs' | 'contacts' | 'locations' | 'gaps'>('overview');

  useEffect(() => {
    const loadData = async () => {
      try {
        const [primesRes, programsRes, contactsRes, locationsRes, gapsRes, statsRes, summaryRes] = await Promise.all([
          fetch('/data/call_notes_primes.json'),
          fetch('/data/call_notes_programs.json'),
          fetch('/data/call_notes_contacts.json'),
          fetch('/data/call_notes_locations.json'),
          fetch('/data/call_notes_gaps.json'),
          fetch('/data/call_notes_stats.json'),
          fetch('/data/call_notes_summary.json')
        ]);

        if (primesRes.ok) setPrimes(await primesRes.json());
        if (programsRes.ok) setPrograms(await programsRes.json());
        if (contactsRes.ok) setContacts(await contactsRes.json());
        if (locationsRes.ok) setLocations(await locationsRes.json());
        if (gapsRes.ok) setGaps(await gapsRes.json());
        if (statsRes.ok) setStats(await statsRes.json());
        if (summaryRes.ok) setSummary(await summaryRes.json());
      } catch (error) {
        console.error('Error loading call intelligence data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'A': return 'bg-green-500';
      case 'B': return 'bg-blue-500';
      case 'C': return 'bg-yellow-500';
      case 'D': return 'bg-orange-500';
      case 'E': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getActivityColor = (level: string) => {
    switch (level) {
      case 'High': return 'text-green-400';
      case 'Medium': return 'text-yellow-400';
      case 'Low': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Phone className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Total Call Notes</p>
              <p className="text-2xl font-bold text-white">{summary?.totalCallNotes?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <Users className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Unique Contacts</p>
              <p className="text-2xl font-bold text-white">{summary?.uniqueContacts?.toLocaleString() || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Building2 className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Primes Tracked</p>
              <p className="text-2xl font-bold text-white">{summary?.totalPrimes || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-sm text-slate-400">Gap Programs</p>
              <p className="text-2xl font-bold text-white">{summary?.gapPrograms || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Action Distribution */}
      {stats && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            Action Distribution
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(stats.actionDistribution).slice(0, 5).map(([action, count]) => (
              <div key={action} className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-sm text-slate-400">{action}</p>
                <p className="text-xl font-bold text-white">{count.toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Primes and Programs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Primes */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-purple-400" />
            Top Primes by Mentions
          </h3>
          <div className="space-y-3">
            {primes.slice(0, 8).map((prime, idx) => (
              <div key={prime.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-slate-500 w-6">{idx + 1}.</span>
                  <span className="text-white">{prime.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-sm ${getActivityColor(prime.activityLevel)}`}>
                    {prime.activityLevel}
                  </span>
                  <span className="text-slate-400">{prime.mentionCount.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Locations */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-green-400" />
            Top Locations
          </h3>
          <div className="space-y-3">
            {locations.slice(0, 8).map((location, idx) => (
              <div key={location.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-slate-500 w-6">{idx + 1}.</span>
                  <span className="text-white">{location.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-400">
                    {location.category}
                  </span>
                </div>
                <span className="text-slate-400">{location.mentionCount.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Gap Analysis Summary */}
      {gaps && (
        <div className="bg-slate-800 rounded-lg p-6 border border-red-500/30">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            Gap Analysis - Needs Attention
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-slate-400 mb-3">Gap Programs (Low Traction)</h4>
              <div className="space-y-2">
                {gaps.gapPrograms.map((gap) => (
                  <div key={gap.name} className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                    <p className="text-white font-medium">{gap.name}</p>
                    <p className="text-sm text-slate-400">{gap.reason}</p>
                    <p className="text-xs text-yellow-400 mt-1">{gap.recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-slate-400 mb-3">Gap Contacts by Status</h4>
              <div className="space-y-2">
                {Object.entries(gaps.gapContactsByStatus).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between bg-slate-700/50 rounded p-2">
                    <span className="text-slate-300">{status}</span>
                    <span className="text-red-400 font-medium">{count}</span>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-sm text-red-400">
                Total Gap Contacts: {gaps.totalGapContacts}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderPrimes = () => (
    <div className="bg-slate-800 rounded-lg border border-slate-700">
      <div className="p-4 border-b border-slate-700">
        <h3 className="text-lg font-semibold text-white">Prime Contractor Activity</h3>
        <p className="text-sm text-slate-400">Call note mentions and activity levels</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-700/50">
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Prime</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Mentions</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Activity</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Sample Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {primes.map((prime) => (
              <tr key={prime.name} className="hover:bg-slate-700/30">
                <td className="px-4 py-3">
                  <span className="font-medium text-white">{prime.name}</span>
                </td>
                <td className="px-4 py-3 text-slate-300">{prime.mentionCount.toLocaleString()}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-sm ${
                    prime.activityLevel === 'High' ? 'bg-green-500/20 text-green-400' :
                    prime.activityLevel === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-red-500/20 text-red-400'
                  }`}>
                    {prime.activityLevel}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-slate-400 max-w-md truncate">
                  {prime.sampleNotes?.[0]?.note || 'No notes available'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderPrograms = () => (
    <div className="bg-slate-800 rounded-lg border border-slate-700">
      <div className="p-4 border-b border-slate-700">
        <h3 className="text-lg font-semibold text-white">Program/Agency Mentions</h3>
        <p className="text-sm text-slate-400">Programs and agencies mentioned in call notes</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-700/50">
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Program</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Mentions</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Sample Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {programs.map((program) => (
              <tr key={program.name} className={`hover:bg-slate-700/30 ${program.isGapProgram ? 'bg-red-500/5' : ''}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{program.name}</span>
                    {program.isGapProgram && (
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-300">{program.mentionCount.toLocaleString()}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-sm ${
                    program.isGapProgram ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                  }`}>
                    {program.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-slate-400 max-w-md truncate">
                  {program.sampleNotes?.[0]?.note || 'No notes available'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderContacts = () => (
    <div className="bg-slate-800 rounded-lg border border-slate-700">
      <div className="p-4 border-b border-slate-700">
        <h3 className="text-lg font-semibold text-white">Contact Engagement Analysis</h3>
        <p className="text-sm text-slate-400">Contact activity and engagement scores from call notes</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-700/50">
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Contact</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Tier</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Engagement</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Interactions</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Primes</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {contacts.slice(0, 100).map((contact) => (
              <tr key={contact.name} className={`hover:bg-slate-700/30 ${contact.isGapContact ? 'bg-red-500/5' : ''}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{contact.name}</span>
                    {contact.isGapContact && (
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold text-white ${getTierColor(contact.tier)}`}>
                    {contact.tier}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          contact.engagementScore >= 60 ? 'bg-green-500' :
                          contact.engagementScore >= 30 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${contact.engagementScore}%` }}
                      />
                    </div>
                    <span className="text-sm text-slate-400">{contact.engagementScore}%</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-400">{contact.positiveInteractions}</span>
                    <span className="text-slate-500">/</span>
                    <span className="text-red-400">{contact.negativeInteractions}</span>
                    <span className="text-slate-500">/</span>
                    <span className="text-slate-400">{contact.totalInteractions} total</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-slate-400">
                  {contact.primesAssociated?.slice(0, 2).join(', ') || '-'}
                </td>
                <td className="px-4 py-3 text-sm text-slate-400">
                  {contact.lastStatus || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderLocations = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Locations by Category */}
      {['Military Installation', 'Intel Community', 'DC Metro', 'OCONUS', 'SOCOM/CENTCOM', 'Space Command'].map(category => {
        const categoryLocations = locations.filter(l => l.category === category);
        if (categoryLocations.length === 0) return null;

        return (
          <div key={category} className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4">{category}</h3>
            <div className="space-y-2">
              {categoryLocations.map((location) => (
                <div key={location.name} className="flex items-center justify-between bg-slate-700/30 rounded p-2">
                  <span className="text-slate-300">{location.name}</span>
                  <span className="text-slate-400">{location.mentionCount.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );

  const renderGaps = () => (
    <div className="space-y-6">
      {/* Gap Programs */}
      <div className="bg-slate-800 rounded-lg p-6 border border-red-500/30">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-red-400" />
          Gap Programs - Low Traction
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {gaps?.gapPrograms.map((gap) => (
            <div key={gap.name} className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <h4 className="text-xl font-bold text-white mb-2">{gap.name}</h4>
              <p className="text-sm text-slate-400 mb-3">{gap.reason}</p>
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-2">
                <p className="text-xs text-yellow-400">{gap.recommendation}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Gap Contacts */}
      <div className="bg-slate-800 rounded-lg p-6 border border-orange-500/30">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Users className="w-5 h-5 text-orange-400" />
          Gap Contacts - Need Re-engagement
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {gaps && Object.entries(gaps.gapContactsByStatus).map(([status, count]) => (
            <div key={status} className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-orange-400">{count}</p>
              <p className="text-sm text-slate-400">{status}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-center text-slate-400">
          Total contacts needing attention: <span className="text-orange-400 font-bold">{gaps?.totalGapContacts}</span>
        </p>
      </div>

      {/* Recommendations */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Recommendations</h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-blue-500/10 rounded-lg">
            <CheckCircle className="w-5 h-5 text-blue-400 mt-0.5" />
            <div>
              <p className="text-white font-medium">Review DCGS, NSA, CENTCOM targeting</p>
              <p className="text-sm text-slate-400">These programs show high mention count but low positive traction. Consider different contact approach.</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-green-500/10 rounded-lg">
            <TrendingUp className="w-5 h-5 text-green-400 mt-0.5" />
            <div>
              <p className="text-white font-medium">Focus on CACI and GDIT contacts</p>
              <p className="text-sm text-slate-400">Highest activity primes with strong engagement. Prioritize these relationships.</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-yellow-500/10 rounded-lg">
            <Clock className="w-5 h-5 text-yellow-400 mt-0.5" />
            <div>
              <p className="text-white font-medium">Re-engage gap contacts</p>
              <p className="text-sm text-slate-400">{gaps?.totalGapContacts} contacts have multiple negative interactions. Schedule re-engagement campaign.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Phone className="w-7 h-7 text-blue-400" />
          Call Notes Intelligence
        </h1>
        <p className="text-slate-400 mt-1">
          Analysis of 50,710 outbound call notes • Primes, Programs, Contacts, and Gaps
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'overview', label: 'Overview', icon: BarChart3 },
          { id: 'primes', label: 'Primes', icon: Building2 },
          { id: 'programs', label: 'Programs', icon: Target },
          { id: 'contacts', label: 'Contacts', icon: Users },
          { id: 'locations', label: 'Locations', icon: MapPin },
          { id: 'gaps', label: 'Gap Analysis', icon: AlertTriangle },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
              activeTab === id
                ? 'bg-blue-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'overview' && renderOverview()}
      {activeTab === 'primes' && renderPrimes()}
      {activeTab === 'programs' && renderPrograms()}
      {activeTab === 'contacts' && renderContacts()}
      {activeTab === 'locations' && renderLocations()}
      {activeTab === 'gaps' && renderGaps()}
    </div>
  );
};

export default CallIntelligence;
