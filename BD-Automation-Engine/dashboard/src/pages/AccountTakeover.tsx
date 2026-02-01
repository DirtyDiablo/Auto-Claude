import { useState, useEffect } from 'react';
import {
  DollarSign,
  Users,
  Briefcase,
  Building2,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Target,
  FileText,
  Phone,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Shield,
  UserCheck,
  MapPin,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
  AreaChart,
  Area,
} from 'recharts';

interface TakeoverData {
  metadata: {
    generated: string;
    subject: string;
    totalNotes: number;
    uniqueContacts: number;
  };
  summary: {
    weeklySpreadAtRisk: number;
    activeContractors: number;
    openJobs: number;
    totalContacts: number;
    primeContractors: number;
    programs: number;
  };
  primeContractors: Array<{
    name: string;
    mentions: number;
    contacts: number;
    placements: number;
  }>;
  activeContractors: Array<{
    name: string;
    company: string;
    role: string;
    jobNumber: string;
    startDate: string;
    weeklySpread: number;
  }>;
  openJobs: Array<{
    jobNumber: string;
    role: string;
    company: string;
    submissions: number;
    interviews: number;
    status: string;
    hotCandidate: string | null;
  }>;
  fairGameContacts: Array<{
    contact: string;
    company: string;
    program: string;
    headcount: number;
    status: string;
    priority: string;
  }>;
  programs: Array<{
    name: string;
    mentions: number;
    primes: string[];
    contacts: number;
    status: string;
    growth: string;
  }>;
  keyContacts: Array<{
    name: string;
    company: string;
    program: string;
    notes: number;
    role: string;
    priority: string;
  }>;
  growthTargets: Array<{
    program: string;
    company: string;
    growth: string;
    contact: string;
    timeline: string;
  }>;
  actionItems: {
    day1: Array<{ action: string; type: string; priority: string }>;
    week1: Array<{ action: string; type: string; priority: string }>;
    week2: Array<{ action: string; type: string; priority: string }>;
  };
  revenueByCompany: Array<{
    company: string;
    contractors: number;
    weeklySpread: number;
    percentage: number;
  }>;
}

type TabType = 'overview' | 'contractors' | 'pipeline' | 'fairgame' | 'contacts' | 'programs' | 'actions';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];

const priorityColors: Record<string, string> = {
  CRITICAL: 'bg-red-500',
  IMMEDIATE: 'bg-orange-500',
  URGENT: 'bg-yellow-500',
  HIGH: 'bg-blue-500',
  MEDIUM: 'bg-slate-500',
  'FAIR GAME': 'bg-green-500',
  EXCLUSIVE: 'bg-purple-500',
};

const statusColors: Record<string, string> = {
  HOT: 'bg-red-500 text-white',
  Active: 'bg-green-500 text-white',
  Evergreen: 'bg-blue-500 text-white',
  BROKEN: 'bg-orange-500 text-white',
  Pipeline: 'bg-slate-500 text-white',
};

export function AccountTakeover() {
  const [data, setData] = useState<TakeoverData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [completedActions, setCompletedActions] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch('/data/scurry_takeover.json')
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load takeover data:', err);
        setLoading(false);
      });
  }, []);

  const toggleAction = (action: string) => {
    const newCompleted = new Set(completedActions);
    if (newCompleted.has(action)) {
      newCompleted.delete(action);
    } else {
      newCompleted.add(action);
    }
    setCompletedActions(newCompleted);
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        Failed to load takeover data
      </div>
    );
  }

  const tabs: Array<{ id: TabType; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: 'overview', label: 'Executive Overview', icon: Target },
    { id: 'contractors', label: 'Active Contractors', icon: Users },
    { id: 'pipeline', label: 'Jobs Pipeline', icon: Briefcase },
    { id: 'fairgame', label: 'Fair Game Targets', icon: Zap },
    { id: 'contacts', label: 'Key Contacts', icon: UserCheck },
    { id: 'programs', label: 'Program Intel', icon: Building2 },
    { id: 'actions', label: 'Action Checklist', icon: CheckCircle2 },
  ];

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Hero Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl p-4 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <DollarSign className="h-8 w-8 opacity-80" />
            <ArrowUpRight className="h-5 w-5" />
          </div>
          <p className="text-3xl font-bold mt-2">${(data.summary.weeklySpreadAtRisk / 1000).toFixed(0)}K</p>
          <p className="text-sm opacity-80">Weekly Spread at Risk</p>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl p-4 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <Users className="h-8 w-8 opacity-80" />
            <Shield className="h-5 w-5" />
          </div>
          <p className="text-3xl font-bold mt-2">{data.summary.activeContractors}</p>
          <p className="text-sm opacity-80">Active Contractors</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-violet-600 rounded-xl p-4 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <Briefcase className="h-8 w-8 opacity-80" />
            <TrendingUp className="h-5 w-5" />
          </div>
          <p className="text-3xl font-bold mt-2">{data.summary.openJobs}</p>
          <p className="text-sm opacity-80">Open Jobs</p>
        </div>
        <div className="bg-gradient-to-br from-orange-500 to-red-600 rounded-xl p-4 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <Building2 className="h-8 w-8 opacity-80" />
            <Zap className="h-5 w-5" />
          </div>
          <p className="text-3xl font-bold mt-2">{data.fairGameContacts.length}</p>
          <p className="text-sm opacity-80">Fair Game Targets</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue by Company */}
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Revenue by Company</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data.revenueByCompany}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="weeklySpread"
                nameKey="company"
                label={({ company, percentage }) => `${company} (${percentage.toFixed(0)}%)`}
              >
                {data.revenueByCompany.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}`, 'Weekly']} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Prime Contractor Engagement */}
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Prime Contractor Engagement</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.primeContractors.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="mentions" fill="#3b82f6" name="Mentions" />
              <Bar dataKey="placements" fill="#10b981" name="Placements" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Growth Targets */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-green-500" />
          2026 Growth Targets
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.growthTargets.map((target, idx) => (
            <div key={idx} className="bg-slate-50 dark:bg-slate-700 rounded-lg p-4 border-l-4 border-green-500">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-900 dark:text-white">{target.program}</span>
                <span className="text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded">
                  {target.growth}
                </span>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-300">{target.company}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Contact: {target.contact}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Hot Jobs Alert */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          Hot Jobs - Immediate Action Required
        </h3>
        <div className="space-y-3">
          {data.openJobs
            .filter((j) => j.status === 'HOT')
            .map((job, idx) => (
              <div key={idx} className="flex items-center justify-between bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                <div>
                  <span className="font-semibold text-slate-900 dark:text-white">{job.jobNumber} - {job.role}</span>
                  <p className="text-sm text-slate-600 dark:text-slate-300">{job.company}</p>
                </div>
                <div className="text-right">
                  <span className="text-sm bg-red-500 text-white px-2 py-1 rounded">HOT</span>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{job.hotCandidate}</p>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );

  const renderContractors = () => (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Active Contractors ({data.activeContractors.length})</h3>
          <span className="text-lg font-bold text-green-500">
            ${data.activeContractors.reduce((sum, c) => sum + c.weeklySpread, 0).toLocaleString()}/week
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                <th className="pb-3 font-medium">Contractor</th>
                <th className="pb-3 font-medium">Company</th>
                <th className="pb-3 font-medium">Role</th>
                <th className="pb-3 font-medium">Job #</th>
                <th className="pb-3 font-medium">Start Date</th>
                <th className="pb-3 font-medium text-right">Weekly $</th>
              </tr>
            </thead>
            <tbody>
              {data.activeContractors.map((contractor, idx) => (
                <tr key={idx} className="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/30">
                  <td className="py-3 font-medium text-slate-900 dark:text-white">{contractor.name}</td>
                  <td className="py-3 text-slate-600 dark:text-slate-300">{contractor.company}</td>
                  <td className="py-3 text-slate-600 dark:text-slate-300">{contractor.role}</td>
                  <td className="py-3 text-blue-600 dark:text-blue-400">{contractor.jobNumber}</td>
                  <td className="py-3 text-slate-500 dark:text-slate-400">{contractor.startDate}</td>
                  <td className="py-3 text-right font-medium text-green-600 dark:text-green-400">
                    ${contractor.weeklySpread.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Contractor Distribution Chart */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Contractor Distribution by Company</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data.revenueByCompany}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="company" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="contractors" stackId="1" stroke="#3b82f6" fill="#3b82f6" name="Contractors" />
            <Area type="monotone" dataKey="weeklySpread" stackId="2" stroke="#10b981" fill="#10b981" name="Weekly Spread" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderPipeline = () => (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Open Jobs Pipeline ({data.openJobs.length})</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                <th className="pb-3 font-medium">Job #</th>
                <th className="pb-3 font-medium">Role</th>
                <th className="pb-3 font-medium">Company</th>
                <th className="pb-3 font-medium text-center">Subs</th>
                <th className="pb-3 font-medium text-center">Interviews</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Hot Candidate</th>
              </tr>
            </thead>
            <tbody>
              {data.openJobs.map((job, idx) => (
                <tr key={idx} className="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/30">
                  <td className="py-3 font-medium text-blue-600 dark:text-blue-400">{job.jobNumber}</td>
                  <td className="py-3 text-slate-900 dark:text-white">{job.role}</td>
                  <td className="py-3 text-slate-600 dark:text-slate-300">{job.company}</td>
                  <td className="py-3 text-center text-slate-600 dark:text-slate-300">{job.submissions}</td>
                  <td className="py-3 text-center text-slate-600 dark:text-slate-300">{job.interviews}</td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[job.status] || 'bg-slate-500 text-white'}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="py-3 text-slate-500 dark:text-slate-400">{job.hotCandidate || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pipeline Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg text-center">
          <p className="text-4xl font-bold text-blue-500">{data.openJobs.reduce((sum, j) => sum + j.submissions, 0)}</p>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Total Submissions</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg text-center">
          <p className="text-4xl font-bold text-green-500">{data.openJobs.reduce((sum, j) => sum + j.interviews, 0)}</p>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Active Interviews</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg text-center">
          <p className="text-4xl font-bold text-red-500">{data.openJobs.filter((j) => j.status === 'HOT').length}</p>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Hot Jobs</p>
        </div>
      </div>
    </div>
  );

  const renderFairGame = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-xl p-6 text-white shadow-lg">
        <h2 className="text-2xl font-bold mb-2">Fair Game Targets</h2>
        <p className="opacity-90">Contacts and programs with engagement but NO active placements - ready for immediate pursuit</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {data.fairGameContacts.map((target, idx) => (
          <div key={idx} className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2 py-1 rounded text-xs font-bold text-white ${priorityColors[target.priority] || 'bg-slate-500'}`}>
                    {target.priority}
                  </span>
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{target.contact}</h3>
                </div>
                <p className="text-slate-600 dark:text-slate-300">{target.company} - {target.program}</p>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{target.status}</p>
              </div>
              <div className="text-right">
                {target.headcount > 0 && (
                  <div className="text-2xl font-bold text-blue-500">{target.headcount.toLocaleString()}</div>
                )}
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {target.headcount > 0 ? 'potential positions' : ''}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderContacts = () => (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Key Contacts by Engagement</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                <th className="pb-3 font-medium">Contact</th>
                <th className="pb-3 font-medium">Company</th>
                <th className="pb-3 font-medium">Program</th>
                <th className="pb-3 font-medium">Role</th>
                <th className="pb-3 font-medium text-center">Notes</th>
                <th className="pb-3 font-medium">Priority</th>
              </tr>
            </thead>
            <tbody>
              {data.keyContacts.map((contact, idx) => (
                <tr key={idx} className="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/30">
                  <td className="py-3 font-medium text-slate-900 dark:text-white">{contact.name}</td>
                  <td className="py-3 text-slate-600 dark:text-slate-300">{contact.company}</td>
                  <td className="py-3 text-blue-600 dark:text-blue-400">{contact.program}</td>
                  <td className="py-3 text-slate-600 dark:text-slate-300">{contact.role}</td>
                  <td className="py-3 text-center">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 font-bold">
                      {contact.notes}
                    </span>
                  </td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium text-white ${priorityColors[contact.priority] || 'bg-slate-500'}`}>
                      {contact.priority}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Contact Engagement Chart */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Contact Engagement (Notes Count)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.keyContacts.slice(0, 10)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="notes" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderPrograms = () => (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Program Intelligence</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.programs.map((program, idx) => (
            <div key={idx} className="bg-slate-50 dark:bg-slate-700 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-slate-900 dark:text-white">{program.name}</h4>
                <span className="text-sm text-slate-500 dark:text-slate-400">{program.mentions} mentions</span>
              </div>
              <div className="flex flex-wrap gap-1 mb-2">
                {program.primes.slice(0, 3).map((prime, pidx) => (
                  <span key={pidx} className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                    {prime}
                  </span>
                ))}
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500 dark:text-slate-400">{program.contacts} contacts</span>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  program.status === 'EXCLUSIVE' ? 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300' :
                  program.status === 'Growing' ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' :
                  'bg-slate-100 dark:bg-slate-600 text-slate-700 dark:text-slate-300'
                }`}>
                  {program.status}
                </span>
              </div>
              {program.growth && (
                <p className="text-sm text-green-600 dark:text-green-400 mt-2 font-medium">
                  <TrendingUp className="inline h-4 w-4 mr-1" />
                  {program.growth}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Program Activity Chart */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Program Activity (Mentions)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.programs}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="mentions" fill="#3b82f6" name="Mentions" radius={[4, 4, 0, 0]} />
            <Bar dataKey="contacts" fill="#10b981" name="Contacts" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderActions = () => (
    <div className="space-y-6">
      {/* Day 1 */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white flex items-center gap-2">
          <Clock className="h-5 w-5 text-red-500" />
          Day 1 - Immediate Actions
        </h3>
        <div className="space-y-2">
          {data.actionItems.day1.map((item, idx) => (
            <div
              key={idx}
              onClick={() => toggleAction(`day1-${idx}`)}
              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                completedActions.has(`day1-${idx}`)
                  ? 'bg-green-50 dark:bg-green-900/20 line-through opacity-60'
                  : 'bg-slate-50 dark:bg-slate-700 hover:bg-slate-100 dark:hover:bg-slate-600'
              }`}
            >
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                completedActions.has(`day1-${idx}`) ? 'bg-green-500 border-green-500' : 'border-slate-300 dark:border-slate-500'
              }`}>
                {completedActions.has(`day1-${idx}`) && <CheckCircle2 className="h-4 w-4 text-white" />}
              </div>
              <span className="flex-1 text-slate-900 dark:text-white">{item.action}</span>
              <span className={`px-2 py-1 rounded text-xs font-medium text-white ${priorityColors[item.priority] || 'bg-slate-500'}`}>
                {item.priority}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Week 1 */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white flex items-center gap-2">
          <Calendar className="h-5 w-5 text-blue-500" />
          Week 1 - Stabilization
        </h3>
        <div className="space-y-2">
          {data.actionItems.week1.map((item, idx) => (
            <div
              key={idx}
              onClick={() => toggleAction(`week1-${idx}`)}
              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                completedActions.has(`week1-${idx}`)
                  ? 'bg-green-50 dark:bg-green-900/20 line-through opacity-60'
                  : 'bg-slate-50 dark:bg-slate-700 hover:bg-slate-100 dark:hover:bg-slate-600'
              }`}
            >
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                completedActions.has(`week1-${idx}`) ? 'bg-green-500 border-green-500' : 'border-slate-300 dark:border-slate-500'
              }`}>
                {completedActions.has(`week1-${idx}`) && <CheckCircle2 className="h-4 w-4 text-white" />}
              </div>
              <span className="flex-1 text-slate-900 dark:text-white">{item.action}</span>
              <span className={`px-2 py-1 rounded text-xs font-medium text-white ${priorityColors[item.priority] || 'bg-slate-500'}`}>
                {item.priority}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Week 2 */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white flex items-center gap-2">
          <Target className="h-5 w-5 text-purple-500" />
          Week 2 - Growth
        </h3>
        <div className="space-y-2">
          {data.actionItems.week2.map((item, idx) => (
            <div
              key={idx}
              onClick={() => toggleAction(`week2-${idx}`)}
              className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                completedActions.has(`week2-${idx}`)
                  ? 'bg-green-50 dark:bg-green-900/20 line-through opacity-60'
                  : 'bg-slate-50 dark:bg-slate-700 hover:bg-slate-100 dark:hover:bg-slate-600'
              }`}
            >
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                completedActions.has(`week2-${idx}`) ? 'bg-green-500 border-green-500' : 'border-slate-300 dark:border-slate-500'
              }`}>
                {completedActions.has(`week2-${idx}`) && <CheckCircle2 className="h-4 w-4 text-white" />}
              </div>
              <span className="flex-1 text-slate-900 dark:text-white">{item.action}</span>
              <span className={`px-2 py-1 rounded text-xs font-medium text-white ${priorityColors[item.priority] || 'bg-slate-500'}`}>
                {item.priority}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Progress Tracker */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-slate-900 dark:text-white">Progress</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-4 overflow-hidden">
            <div
              className="bg-gradient-to-r from-green-500 to-emerald-500 h-full transition-all duration-500"
              style={{
                width: `${(completedActions.size / (data.actionItems.day1.length + data.actionItems.week1.length + data.actionItems.week2.length)) * 100}%`
              }}
            />
          </div>
          <span className="text-lg font-bold text-slate-900 dark:text-white">
            {completedActions.size}/{data.actionItems.day1.length + data.actionItems.week1.length + data.actionItems.week2.length}
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full overflow-hidden flex flex-col bg-slate-100 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white p-6">
        <h1 className="text-2xl font-bold">Account Takeover Dashboard</h1>
        <p className="text-slate-400 mt-1">Colton Scurry Portfolio Analysis | Data: {data.metadata.generated}</p>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-4 overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'contractors' && renderContractors()}
        {activeTab === 'pipeline' && renderPipeline()}
        {activeTab === 'fairgame' && renderFairGame()}
        {activeTab === 'contacts' && renderContacts()}
        {activeTab === 'programs' && renderPrograms()}
        {activeTab === 'actions' && renderActions()}
      </div>
    </div>
  );
}

export default AccountTakeover;
