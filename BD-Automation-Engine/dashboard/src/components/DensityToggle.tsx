import { useState, useEffect, useCallback } from 'react';
import { AlignJustify, AlignCenter, AlignLeft } from 'lucide-react';

export type Density = 'compact' | 'comfortable' | 'spacious';

const DENSITY_KEY = 'bd_density';

const DENSITY_OPTIONS: Array<{ value: Density; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { value: 'compact', label: 'Compact', icon: AlignJustify },
  { value: 'comfortable', label: 'Comfortable', icon: AlignCenter },
  { value: 'spacious', label: 'Spacious', icon: AlignLeft },
];

const CSS_VARS: Record<Density, Record<string, string>> = {
  compact: {
    '--density-spacing': '0.25rem',
    '--density-padding': '0.5rem',
    '--density-text': '0.75rem',
    '--density-gap': '0.375rem',
    '--density-rounded': '0.375rem',
  },
  comfortable: {
    '--density-spacing': '0.5rem',
    '--density-padding': '0.75rem',
    '--density-text': '0.875rem',
    '--density-gap': '0.5rem',
    '--density-rounded': '0.5rem',
  },
  spacious: {
    '--density-spacing': '0.75rem',
    '--density-padding': '1rem',
    '--density-text': '0.875rem',
    '--density-gap': '0.75rem',
    '--density-rounded': '0.75rem',
  },
};

function applyDensity(density: Density) {
  const root = document.documentElement;
  const vars = CSS_VARS[density];
  for (const [key, value] of Object.entries(vars)) {
    root.style.setProperty(key, value);
  }
  root.setAttribute('data-density', density);
}

export function useDensity(): [Density, (d: Density) => void] {
  const [density, setDensityState] = useState<Density>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem(DENSITY_KEY) as Density) || 'comfortable';
    }
    return 'comfortable';
  });

  useEffect(() => {
    applyDensity(density);
  }, [density]);

  const setDensity = useCallback((d: Density) => {
    setDensityState(d);
    localStorage.setItem(DENSITY_KEY, d);
    applyDensity(d);
  }, []);

  return [density, setDensity];
}

interface DensityToggleProps {
  collapsed?: boolean;
}

export function DensityToggle({ collapsed }: DensityToggleProps) {
  const [density, setDensity] = useDensity();

  return (
    <div className="flex items-center gap-1">
      {DENSITY_OPTIONS.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          onClick={() => setDensity(value)}
          className={`p-1.5 rounded-md transition-all ${
            density === value
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-300 hover:bg-slate-700'
          }`}
          title={collapsed ? label : undefined}
        >
          <Icon className="h-3.5 w-3.5" />
        </button>
      ))}
      {!collapsed && (
        <span className="text-[10px] text-slate-500 ml-1 capitalize">{density}</span>
      )}
    </div>
  );
}
