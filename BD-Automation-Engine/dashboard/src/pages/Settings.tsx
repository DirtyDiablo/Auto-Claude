import { useState, useEffect } from 'react';
import {
  Database,
  RefreshCw,
  Bell,
  Shield,
  Globe,
  Check,
  ExternalLink,
  Key,
  AlertCircle,
  Eye,
  EyeOff,
  Loader2,
  Server,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import {
  setNotionToken,
  clearNotionToken,
  isNotionConfigured,
  fetchJobs,
  fetchPrograms,
} from '../services/notionApi';
import { hubApiClient, getHubApiUrl, setHubApiUrl } from '../services/hubApi';

interface SettingsProps {
  onRefresh: () => void;
  isRefreshing: boolean;
  lastUpdated: Date | null;
}

const SECTION_COLORS: Record<string, { gradient: string; iconBg: string; iconText: string }> = {
  Database: { gradient: 'from-blue-500 to-cyan-500', iconBg: 'bg-gradient-to-br from-blue-100 to-cyan-100', iconText: 'text-blue-600' },
  Key: { gradient: 'from-amber-500 to-orange-500', iconBg: 'bg-gradient-to-br from-amber-100 to-orange-100', iconText: 'text-amber-600' },
  Server: { gradient: 'from-purple-500 to-indigo-500', iconBg: 'bg-gradient-to-br from-purple-100 to-indigo-100', iconText: 'text-purple-600' },
  RefreshCw: { gradient: 'from-green-500 to-emerald-500', iconBg: 'bg-gradient-to-br from-green-100 to-emerald-100', iconText: 'text-green-600' },
  Bell: { gradient: 'from-rose-500 to-pink-500', iconBg: 'bg-gradient-to-br from-rose-100 to-pink-100', iconText: 'text-rose-600' },
  Globe: { gradient: 'from-sky-500 to-blue-500', iconBg: 'bg-gradient-to-br from-sky-100 to-blue-100', iconText: 'text-sky-600' },
  Shield: { gradient: 'from-slate-500 to-gray-500', iconBg: 'bg-gradient-to-br from-slate-100 to-gray-100', iconText: 'text-slate-600' },
};

function SettingSection({
  title,
  description,
  icon: Icon,
  children,
}: {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  const iconName = Icon.name || 'Shield';
  const colors = SECTION_COLORS[iconName] || SECTION_COLORS.Shield;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className={`h-1 bg-gradient-to-r ${colors.gradient}`} />
      <div className="p-6">
        <div className="flex items-start gap-4 mb-4">
          <div className={`p-2.5 rounded-xl ${colors.iconBg}`}>
            <Icon className={`h-5 w-5 ${colors.iconText}`} />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">{title}</h3>
            <p className="text-sm text-slate-500">{description}</p>
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}

function Toggle({
  enabled,
  onChange,
  label,
}: {
  enabled: boolean;
  onChange: (value: boolean) => void;
  label: string;
}) {
  return (
    <label className="flex items-center gap-3 cursor-pointer">
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          enabled ? 'bg-blue-600' : 'bg-slate-200'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            enabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
      <span className="text-sm text-slate-700">{label}</span>
    </label>
  );
}

export function Settings({ onRefresh, isRefreshing, lastUpdated }: SettingsProps) {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  // Notion API configuration
  const [notionToken, setNotionTokenState] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; jobCount?: number; programCount?: number } | null>(null);

  // Hub API state
  const [hubUrl, setHubUrl] = useState(getHubApiUrl());
  const [hubConnected, setHubConnected] = useState(false);
  const [hubTesting, setHubTesting] = useState(false);
  const [hubStats, setHubStats] = useState<{ contacts: number; programs: number; total: number } | null>(null);

  // Check if Notion is configured on mount
  useEffect(() => {
    setIsConfigured(isNotionConfigured());
    // Test Hub connection on mount
    testHubConnection();
  }, []);

  // Test Hub API connection
  const testHubConnection = async () => {
    setHubTesting(true);
    try {
      const connected = await hubApiClient.testConnection();
      setHubConnected(connected);
      if (connected) {
        const stats = await hubApiClient.getStats();
        setHubStats({
          contacts: stats.collections.contacts,
          programs: stats.collections.programs,
          total: stats.total_records,
        });
      }
    } catch {
      setHubConnected(false);
      setHubStats(null);
    } finally {
      setHubTesting(false);
    }
  };

  // Save Hub URL
  const handleSaveHubUrl = () => {
    setHubApiUrl(hubUrl);
    testHubConnection();
  };

  // Save Notion token
  const handleSaveToken = () => {
    if (notionToken.trim()) {
      setNotionToken(notionToken.trim());
      setIsConfigured(true);
      setNotionTokenState('');
      setTestResult(null);
    }
  };

  // Clear Notion token
  const handleClearToken = () => {
    clearNotionToken();
    setIsConfigured(false);
    setTestResult(null);
  };

  // Test Notion connection
  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const [jobs, programs] = await Promise.all([fetchJobs(), fetchPrograms()]);
      setTestResult({
        success: true,
        message: `Successfully connected to Notion`,
        jobCount: jobs.length,
        programCount: programs.length,
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to connect to Notion',
      });
    } finally {
      setIsTesting(false);
    }
  };

  // Data source status - dynamic based on Notion configuration
  const dataSources = isConfigured
    ? [
        { name: 'Notion - Insight Global Jobs', status: 'connected', lastSync: lastUpdated },
        { name: 'Notion - Federal Programs', status: 'connected', lastSync: lastUpdated },
      ]
    : [
        { name: 'Notion - Insight Global Jobs', status: 'disconnected', lastSync: null },
        { name: 'Notion - Federal Programs', status: 'disconnected', lastSync: null },
      ];

  return (
    <div className="p-6 h-full overflow-y-auto bg-slate-50">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 shadow-lg">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
            <p className="text-slate-500">Configure your BD Intelligence Dashboard</p>
          </div>
        </div>
      </div>

      <div className="space-y-6 max-w-3xl">
        {/* Data Sources */}
        <SettingSection
          title="Data Sources"
          description="Connected Notion databases and sync status"
          icon={Database}
        >
          <div className="space-y-3">
            {dataSources.map((source, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      source.status === 'connected' ? 'bg-green-500' : 'bg-red-500'
                    }`}
                  />
                  <span className="text-sm text-slate-700">{source.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">
                    {source.lastSync ? `Synced ${source.lastSync.toLocaleTimeString()}` : 'Not configured'}
                  </span>
                  {source.status === 'connected' ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-amber-500" />
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-200 flex items-center justify-between">
            <button
              onClick={onRefresh}
              disabled={isRefreshing || !isConfigured}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                isRefreshing || !isConfigured
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Syncing...' : 'Sync All Data'}
            </button>
            {lastUpdated && (
              <span className="text-sm text-slate-500">
                Last full sync: {lastUpdated.toLocaleString()}
              </span>
            )}
          </div>
        </SettingSection>

        {/* Notion API Configuration */}
        <SettingSection
          title="Notion API Configuration"
          description="Connect to your Notion workspace to fetch live data"
          icon={Key}
        >
          {isConfigured ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                <Check className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-green-800">Notion API configured</p>
                  <p className="text-xs text-green-600">Your token is saved securely in browser storage</p>
                </div>
              </div>

              {testResult && (
                <div
                  className={`p-3 rounded-lg ${
                    testResult.success ? 'bg-blue-50' : 'bg-red-50'
                  }`}
                >
                  <p
                    className={`text-sm font-medium ${
                      testResult.success ? 'text-blue-800' : 'text-red-800'
                    }`}
                  >
                    {testResult.message}
                  </p>
                  {testResult.success && (
                    <p className="text-xs text-blue-600 mt-1">
                      Found {testResult.jobCount} jobs and {testResult.programCount} programs
                    </p>
                  )}
                </div>
              )}

              <div className="flex items-center gap-3">
                <button
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors disabled:opacity-50"
                >
                  {isTesting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  {isTesting ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  onClick={handleClearToken}
                  className="px-4 py-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
                >
                  Remove Token
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <div>
                  <p className="text-sm font-medium text-amber-800">Notion API not configured</p>
                  <p className="text-xs text-amber-600">Add your integration token to fetch live data</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Notion Integration Token
                </label>
                <div className="relative">
                  <input
                    type={showToken ? 'text' : 'password'}
                    value={notionToken}
                    onChange={(e) => setNotionTokenState(e.target.value)}
                    placeholder="secret_..."
                    className="w-full px-4 py-2 pr-10 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowToken(!showToken)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleSaveToken}
                  disabled={!notionToken.trim()}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Key className="h-4 w-4" />
                  Save Token
                </button>
              </div>

              <div className="text-xs text-slate-500 space-y-1">
                <p className="font-medium">To get your Notion integration token:</p>
                <ol className="list-decimal list-inside ml-2 space-y-1">
                  <li>Go to <a href="https://www.notion.so/my-integrations" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">notion.so/my-integrations</a></li>
                  <li>Create a new integration or use an existing one</li>
                  <li>Copy the "Internal Integration Secret"</li>
                  <li>Share your databases with the integration</li>
                </ol>
              </div>
            </div>
          )}
        </SettingSection>

        {/* Hub API Configuration */}
        <SettingSection
          title="Hub API Configuration"
          description="Connect to the BD Intelligence Hub API for AI-powered features"
          icon={Server}
        >
          <div className="space-y-4">
            {/* Connection Status */}
            <div className={`flex items-center gap-3 p-4 rounded-xl border transition-all ${
              hubConnected
                ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200'
                : 'bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200'
            }`}>
              {hubTesting ? (
                <div className="relative">
                  <div className="w-8 h-8 border-2 border-blue-200 rounded-full animate-pulse" />
                  <div className="absolute inset-0 w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : hubConnected ? (
                <div className="relative">
                  <CheckCircle2 className="h-8 w-8 text-green-500" />
                  <span className="absolute -top-0.5 -right-0.5 flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                  </span>
                </div>
              ) : (
                <XCircle className="h-8 w-8 text-amber-500" />
              )}
              <div className="flex-1">
                <p className={`text-sm font-semibold ${hubConnected ? 'text-green-800' : 'text-amber-800'}`}>
                  {hubTesting ? 'Testing Connection...' : hubConnected ? 'Hub API Connected' : 'Hub API Not Connected'}
                </p>
                {hubStats && (
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-green-600 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      {hubStats.contacts.toLocaleString()} contacts
                    </span>
                    <span className="text-xs text-green-600 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      {hubStats.programs.toLocaleString()} programs
                    </span>
                    <span className="text-xs text-green-600 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                      {hubStats.total.toLocaleString()} total
                    </span>
                  </div>
                )}
                {!hubConnected && !hubTesting && (
                  <p className="text-xs text-amber-600">Start the Hub API server to enable AI features</p>
                )}
              </div>
            </div>

            {/* Hub URL Input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Hub API URL
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={hubUrl}
                  onChange={(e) => setHubUrl(e.target.value)}
                  placeholder="http://127.0.0.1:8100"
                  className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  onClick={handleSaveHubUrl}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Save
                </button>
              </div>
            </div>

            {/* Test Connection Button */}
            <div className="flex items-center gap-3">
              <button
                onClick={testHubConnection}
                disabled={hubTesting}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors disabled:opacity-50"
              >
                {hubTesting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {hubTesting ? 'Testing...' : 'Test Connection'}
              </button>
            </div>

            <div className="text-xs text-slate-500 space-y-1">
              <p className="font-medium">To start the Hub API server:</p>
              <ol className="list-decimal list-inside ml-2 space-y-1">
                <li>Navigate to the Engine8_Knowledge directory</li>
                <li>Run: <code className="bg-slate-100 px-1 rounded">python api.py</code></li>
                <li>The API will start on port 8100</li>
              </ol>
            </div>
          </div>
        </SettingSection>

        {/* Auto Refresh */}
        <SettingSection
          title="Data Refresh"
          description="Configure automatic data updates"
          icon={RefreshCw}
        >
          <div className="space-y-4">
            <Toggle
              enabled={autoRefresh}
              onChange={setAutoRefresh}
              label="Enable auto-refresh (every 30 minutes)"
            />
            <p className="text-xs text-slate-500">
              When enabled, the dashboard will automatically fetch new data from Notion every 30 minutes.
            </p>
          </div>
        </SettingSection>

        {/* Notifications */}
        <SettingSection
          title="Notifications"
          description="Configure alert preferences"
          icon={Bell}
        >
          <div className="space-y-4">
            <Toggle
              enabled={notifications}
              onChange={setNotifications}
              label="Enable browser notifications"
            />
            <div className="text-xs text-slate-500 space-y-1">
              <p>Receive notifications for:</p>
              <ul className="list-disc list-inside ml-2">
                <li>New critical-priority jobs</li>
                <li>New executive contacts added</li>
                <li>Daily playbook reminders</li>
              </ul>
            </div>
          </div>
        </SettingSection>

        {/* Display */}
        <SettingSection
          title="Display"
          description="Customize the dashboard appearance"
          icon={Globe}
        >
          <div className="space-y-4">
            <Toggle
              enabled={darkMode}
              onChange={setDarkMode}
              label="Dark mode (coming soon)"
            />
          </div>
        </SettingSection>

        {/* About */}
        <SettingSection
          title="About"
          description="BD Intelligence Dashboard"
          icon={Shield}
        >
          <div className="space-y-3 text-sm text-slate-600">
            <p>
              <strong>Version:</strong> 1.0.0
            </p>
            <p>
              <strong>Data Engine:</strong> BD Correlation Engine v1.0
            </p>
            <p>
              Part of the BD Automation Engine suite for federal business development.
            </p>
            <div className="pt-3">
              <a
                href="https://github.com/your-repo/bd-automation-engine"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
              >
                View Documentation
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        </SettingSection>
      </div>
    </div>
  );
}
