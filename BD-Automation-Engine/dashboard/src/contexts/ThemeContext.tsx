/**
 * Theme Context - Design Intelligence Integration
 *
 * Provides industry-specific theming using the BD Design Intelligence system.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  createBDDesignSystem,
  createDesignSystem,
  generateCSSVariables,
  validateDesign,
  type Industry,
  type DesignSystem
} from '../design_intelligence';

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextValue {
  // Current state
  mode: ThemeMode;
  industry: Industry;
  designSystem: DesignSystem;
  isDark: boolean;

  // Actions
  setMode: (mode: ThemeMode) => void;
  setIndustry: (industry: Industry) => void;

  // Validation
  warnings: string[];
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

// Storage keys
const THEME_MODE_KEY = 'bd-dashboard-theme-mode';
const INDUSTRY_KEY = 'bd-dashboard-industry';

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultIndustry?: Industry;
}

export function ThemeProvider({ children, defaultIndustry = 'defense' }: ThemeProviderProps) {
  // Load saved preferences
  const [mode, setModeState] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem(THEME_MODE_KEY);
    return (saved as ThemeMode) || 'dark';
  });

  const [industry, setIndustryState] = useState<Industry>(() => {
    const saved = localStorage.getItem(INDUSTRY_KEY);
    return (saved as Industry) || defaultIndustry;
  });

  // Compute effective dark mode
  const [isDark, setIsDark] = useState(mode === 'dark');

  useEffect(() => {
    if (mode === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      setIsDark(mediaQuery.matches);

      const handler = (e: MediaQueryListEvent) => setIsDark(e.matches);
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      setIsDark(mode === 'dark');
    }
  }, [mode]);

  // Generate design system based on industry
  const designSystem = industry === 'defense'
    ? createBDDesignSystem('BD Intelligence Dashboard')
    : createDesignSystem(industry, `${industry.charAt(0).toUpperCase() + industry.slice(1)} Dashboard`);

  // Validate design
  const warnings = validateDesign(designSystem);

  // Apply CSS variables to document
  useEffect(() => {
    const css = generateCSSVariables(designSystem);

    // Create or update style element
    let styleEl = document.getElementById('bd-design-system-vars');
    if (!styleEl) {
      styleEl = document.createElement('style');
      styleEl.id = 'bd-design-system-vars';
      document.head.appendChild(styleEl);
    }
    styleEl.textContent = css;

    // Apply dark/light class to html
    document.documentElement.classList.toggle('dark', isDark);
    document.documentElement.setAttribute('data-industry', industry);
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  }, [designSystem, isDark, industry]);

  // Persist preferences
  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode);
    localStorage.setItem(THEME_MODE_KEY, newMode);
  }, []);

  const setIndustry = useCallback((newIndustry: Industry) => {
    setIndustryState(newIndustry);
    localStorage.setItem(INDUSTRY_KEY, newIndustry);
  }, []);

  return (
    <ThemeContext.Provider value={{
      mode,
      industry,
      designSystem,
      isDark,
      setMode,
      setIndustry,
      warnings,
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export type { ThemeMode, Industry, DesignSystem };
