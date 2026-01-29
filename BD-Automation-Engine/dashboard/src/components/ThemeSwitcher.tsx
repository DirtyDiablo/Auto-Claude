/**
 * Theme Switcher Component
 *
 * Allows users to switch between light/dark/system modes and industry themes.
 */

import { Sun, Moon, Monitor, Building2, Shield, Briefcase, Users, DollarSign, AlertCircle } from 'lucide-react';
import { useTheme, type ThemeMode, type Industry } from '../contexts/ThemeContext';

const THEME_MODES: { value: ThemeMode; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
];

const INDUSTRIES: { value: Industry; label: string; icon: typeof Building2; description: string }[] = [
  { value: 'defense', label: 'Defense / BD', icon: Shield, description: 'Dark theme optimized for federal BD workflows' },
  { value: 'government', label: 'Government', icon: Building2, description: 'Accessible, high-contrast, ethical design' },
  { value: 'enterprise_saas', label: 'Enterprise SaaS', icon: Briefcase, description: 'Modern glassmorphism with rounded corners' },
  { value: 'consulting', label: 'Consulting', icon: Users, description: 'Trust & authority with editorial aesthetics' },
  { value: 'financial', label: 'Financial', icon: DollarSign, description: 'Data-dense dashboard with precise styling' },
];

export function ThemeSwitcher() {
  const { mode, industry, isDark, setMode, setIndustry, warnings, designSystem } = useTheme();

  return (
    <div className="space-y-6">
      {/* Theme Mode Selection */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
          Appearance
        </h3>
        <div className="flex gap-2">
          {THEME_MODES.map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => setMode(value)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
                transition-all duration-200
                ${mode === value
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600'
                }
              `}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Current: {isDark ? 'Dark' : 'Light'} mode
        </p>
      </div>

      {/* Industry Theme Selection */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
          Industry Theme
        </h3>
        <div className="grid grid-cols-1 gap-2">
          {INDUSTRIES.map(({ value, label, icon: Icon, description }) => (
            <button
              key={value}
              onClick={() => setIndustry(value)}
              className={`
                flex items-start gap-3 p-3 rounded-lg text-left
                transition-all duration-200 border-2
                ${industry === value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-transparent bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700'
                }
              `}
            >
              <div className={`
                p-2 rounded-lg
                ${industry === value
                  ? 'bg-blue-500 text-white'
                  : 'bg-slate-200 text-slate-600 dark:bg-slate-600 dark:text-slate-300'
                }
              `}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <div className={`font-medium text-sm ${industry === value ? 'text-blue-700 dark:text-blue-300' : 'text-slate-700 dark:text-slate-300'}`}>
                  {label}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {description}
                </div>
              </div>
              {industry === value && (
                <div className="text-blue-500 dark:text-blue-400">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Current Design System Info */}
      <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
          Active Design System
        </h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-500 dark:text-slate-400">Name:</span>
            <span className="font-medium text-slate-700 dark:text-slate-300">{designSystem.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500 dark:text-slate-400">Style:</span>
            <span className="font-medium text-slate-700 dark:text-slate-300">{designSystem.style}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500 dark:text-slate-400">Heading Font:</span>
            <span className="font-medium text-slate-700 dark:text-slate-300">{designSystem.typography.headingFont}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500 dark:text-slate-400">Body Font:</span>
            <span className="font-medium text-slate-700 dark:text-slate-300">{designSystem.typography.bodyFont}</span>
          </div>
        </div>

        {/* Color Preview */}
        <div className="mt-4">
          <span className="text-xs text-slate-500 dark:text-slate-400 block mb-2">Color Palette:</span>
          <div className="flex gap-1">
            <div className="w-8 h-8 rounded" style={{ backgroundColor: designSystem.colors.primary }} title="Primary" />
            <div className="w-8 h-8 rounded" style={{ backgroundColor: designSystem.colors.secondary }} title="Secondary" />
            <div className="w-8 h-8 rounded" style={{ backgroundColor: designSystem.colors.accent }} title="Accent" />
            <div className="w-8 h-8 rounded" style={{ backgroundColor: designSystem.colors.success }} title="Success" />
            <div className="w-8 h-8 rounded" style={{ backgroundColor: designSystem.colors.warning }} title="Warning" />
            <div className="w-8 h-8 rounded" style={{ backgroundColor: designSystem.colors.error }} title="Error" />
          </div>
        </div>

        {/* Tier Colors */}
        <div className="mt-3">
          <span className="text-xs text-slate-500 dark:text-slate-400 block mb-2">Contact Tiers:</span>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5, 6].map(tier => (
              <div
                key={tier}
                className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold"
                style={{ backgroundColor: designSystem.colors.tier[tier as keyof typeof designSystem.colors.tier] }}
              >
                {tier}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Validation Warnings */}
      {warnings.length > 0 && (
        <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-amber-800 dark:text-amber-300">Design Warnings</h4>
              <ul className="mt-1 text-xs text-amber-700 dark:text-amber-400 space-y-0.5">
                {warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Anti-patterns */}
      {designSystem.antiPatterns.length > 0 && (
        <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
          <h4 className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-2">
            Avoid These Anti-Patterns:
          </h4>
          <div className="flex flex-wrap gap-1">
            {designSystem.antiPatterns.map((pattern, i) => (
              <span
                key={i}
                className="px-2 py-0.5 text-xs rounded bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
              >
                {pattern}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
