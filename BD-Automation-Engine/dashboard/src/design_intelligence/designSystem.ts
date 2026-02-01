/**
 * UI-UX-Pro-Max Design Intelligence System
 *
 * Industry-specific design system generator for creating professional BD dashboards.
 * TypeScript version for React integration.
 */

// Industry types
export type Industry = 'government' | 'defense' | 'enterprise_saas' | 'consulting' | 'financial';

// Color Palette interface
export interface ColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  textPrimary: string;
  textSecondary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  priority: {
    critical: string;
    high: string;
    medium: string;
    low: string;
  };
  tier: {
    1: string;
    2: string;
    3: string;
    4: string;
    5: string;
    6: string;
  };
}

// Typography interface
export interface Typography {
  headingFont: string;
  bodyFont: string;
  monoFont: string;
  headingWeights: number[];
  bodyWeights: number[];
  baseSize: string;
  scaleRatio: number;
}

// Design System interface
export interface DesignSystem {
  name: string;
  industry: Industry;
  style: string;
  colors: ColorPalette;
  typography: Typography;
  spacingUnit: string;
  borderRadius: string;
  shadow: string;
  shadowLg: string;
  transition: string;
  antiPatterns: string[];
  notes: string;
}

// Default BD Colors
export const BD_COLORS: ColorPalette = {
  primary: '#1E40AF',
  secondary: '#7C3AED',
  accent: '#F59E0B',
  background: '#0F172A',
  surface: '#1E293B',
  textPrimary: '#F1F5F9',
  textSecondary: '#94A3B8',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  priority: {
    critical: '#DC2626',
    high: '#EA580C',
    medium: '#CA8A04',
    low: '#16A34A',
  },
  tier: {
    1: '#7C3AED',
    2: '#2563EB',
    3: '#0891B2',
    4: '#059669',
    5: '#65A30D',
    6: '#6B7280',
  },
};

// Default BD Typography
export const BD_TYPOGRAPHY: Typography = {
  headingFont: 'Inter',
  bodyFont: 'Inter',
  monoFont: 'JetBrains Mono',
  headingWeights: [500, 600, 700],
  bodyWeights: [400, 500, 600],
  baseSize: '16px',
  scaleRatio: 1.25,
};

// Industry configurations
export const INDUSTRY_CONFIGS: Record<Industry, Partial<DesignSystem>> = {
  government: {
    style: 'Accessible & Ethical + Swiss Modernism',
    colors: {
      ...BD_COLORS,
      primary: '#003366',
      secondary: '#005A9C',
      accent: '#CC0000',
      background: '#F8FAFC',
      surface: '#FFFFFF',
      textPrimary: '#1E293B',
      textSecondary: '#64748B',
    },
    typography: {
      ...BD_TYPOGRAPHY,
      headingFont: 'Source Sans Pro',
      bodyFont: 'Open Sans',
    },
    borderRadius: '4px',
    antiPatterns: [
      'Dark mode only',
      'Low contrast ratios',
      'Complex animations',
      'AI/tech gradient vibes',
    ],
  },
  defense: {
    style: 'Swiss Modernism 2.0 + Data-Dense Dashboard',
    colors: {
      ...BD_COLORS,
      primary: '#1A365D',
      secondary: '#2B6CB0',
      accent: '#ED8936',
      background: '#1A202C',
      surface: '#2D3748',
      textPrimary: '#F7FAFC',
      textSecondary: '#A0AEC0',
    },
    typography: {
      ...BD_TYPOGRAPHY,
      headingFont: 'Inter',
      bodyFont: 'IBM Plex Sans',
    },
    antiPatterns: [
      'Consumer aesthetics',
      'Playful animations',
      'Bright/saturated colors',
    ],
  },
  enterprise_saas: {
    style: 'Minimalism + Glassmorphism',
    colors: {
      ...BD_COLORS,
      primary: '#4F46E5',
      secondary: '#10B981',
      accent: '#8B5CF6',
      background: '#F9FAFB',
      surface: '#FFFFFF',
      textPrimary: '#111827',
      textSecondary: '#6B7280',
    },
    typography: {
      ...BD_TYPOGRAPHY,
      headingFont: 'Poppins',
      bodyFont: 'Inter',
    },
    borderRadius: '12px',
    antiPatterns: [
      'Dated gradients',
      'Excessive drop shadows',
      'Busy/cluttered layouts',
    ],
  },
  consulting: {
    style: 'Trust & Authority + Editorial Grid',
    colors: {
      ...BD_COLORS,
      primary: '#0F172A',
      secondary: '#1E40AF',
      accent: '#059669',
      background: '#FFFFFF',
      surface: '#F8FAFC',
      textPrimary: '#0F172A',
      textSecondary: '#475569',
    },
    typography: {
      ...BD_TYPOGRAPHY,
      headingFont: 'Merriweather',
      bodyFont: 'Source Sans Pro',
      headingWeights: [400, 700, 900],
    },
    borderRadius: '4px',
    antiPatterns: [
      'Tech startup vibes',
      'Playful illustrations',
      'Casual tone',
    ],
  },
  financial: {
    style: 'Financial Dashboard + Trust & Authority',
    colors: {
      ...BD_COLORS,
      primary: '#0D9488',
      secondary: '#1E3A8A',
      accent: '#F59E0B',
      background: '#FAFAFA',
      surface: '#FFFFFF',
      textPrimary: '#18181B',
      textSecondary: '#71717A',
    },
    typography: {
      ...BD_TYPOGRAPHY,
      headingFont: 'DM Sans',
      bodyFont: 'Inter',
    },
    antiPatterns: [
      'Playful colors',
      'Casual/handwritten fonts',
      'AI purple gradients',
    ],
  },
};

/**
 * Create a design system for a specific industry
 */
export function createDesignSystem(industry: Industry, name: string): DesignSystem {
  const config = INDUSTRY_CONFIGS[industry];

  return {
    name,
    industry,
    style: config.style || 'Default',
    colors: config.colors || BD_COLORS,
    typography: config.typography || BD_TYPOGRAPHY,
    spacingUnit: '4px',
    borderRadius: config.borderRadius || '8px',
    shadow: '0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)',
    shadowLg: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
    transition: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    antiPatterns: config.antiPatterns || [],
    notes: '',
  };
}

/**
 * Create a BD-optimized design system
 */
export function createBDDesignSystem(name: string = 'BD Intelligence Dashboard'): DesignSystem {
  return {
    name,
    industry: 'defense',
    style: 'BD Intelligence + Data-Dense Dashboard',
    colors: BD_COLORS,
    typography: BD_TYPOGRAPHY,
    spacingUnit: '4px',
    borderRadius: '8px',
    shadow: '0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)',
    shadowLg: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
    transition: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    antiPatterns: [
      'Consumer aesthetics',
      'Playful animations',
      'Bright/saturated colors',
      'Marketing-style layouts',
    ],
    notes: 'Optimized for federal BD workflows. High data density, clear hierarchies.',
  };
}

/**
 * Generate CSS custom properties from a design system
 */
export function generateCSSVariables(design: DesignSystem): string {
  return `
:root {
  /* Primary Colors */
  --color-primary: ${design.colors.primary};
  --color-secondary: ${design.colors.secondary};
  --color-accent: ${design.colors.accent};

  /* Background & Surface */
  --color-background: ${design.colors.background};
  --color-surface: ${design.colors.surface};

  /* Text */
  --color-text-primary: ${design.colors.textPrimary};
  --color-text-secondary: ${design.colors.textSecondary};

  /* Semantic */
  --color-success: ${design.colors.success};
  --color-warning: ${design.colors.warning};
  --color-error: ${design.colors.error};
  --color-info: ${design.colors.info};

  /* BD Priority Colors */
  --color-priority-critical: ${design.colors.priority.critical};
  --color-priority-high: ${design.colors.priority.high};
  --color-priority-medium: ${design.colors.priority.medium};
  --color-priority-low: ${design.colors.priority.low};

  /* Contact Tier Colors */
  --color-tier-1: ${design.colors.tier[1]};
  --color-tier-2: ${design.colors.tier[2]};
  --color-tier-3: ${design.colors.tier[3]};
  --color-tier-4: ${design.colors.tier[4]};
  --color-tier-5: ${design.colors.tier[5]};
  --color-tier-6: ${design.colors.tier[6]};

  /* Typography */
  --font-heading: '${design.typography.headingFont}', system-ui, sans-serif;
  --font-body: '${design.typography.bodyFont}', system-ui, sans-serif;
  --font-mono: '${design.typography.monoFont}', 'Consolas', monospace;
  --font-size-base: ${design.typography.baseSize};

  /* Spacing */
  --spacing-unit: ${design.spacingUnit};
  --border-radius: ${design.borderRadius};
  --shadow: ${design.shadow};
  --shadow-lg: ${design.shadowLg};
  --transition: ${design.transition};
}
`;
}

/**
 * Validate a design system for anti-patterns
 */
export function validateDesign(design: DesignSystem): string[] {
  const warnings: string[] = [];

  // Check color contrast
  const getLuminance = (hex: string): number => {
    const color = hex.replace('#', '');
    const r = parseInt(color.substr(0, 2), 16);
    const g = parseInt(color.substr(2, 2), 16);
    const b = parseInt(color.substr(4, 2), 16);
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  };

  const bgLuminance = getLuminance(design.colors.background);
  const textLuminance = getLuminance(design.colors.textPrimary);
  const contrastRatio = Math.abs(bgLuminance - textLuminance);

  if (contrastRatio < 0.5) {
    warnings.push(`Low contrast ratio (${contrastRatio.toFixed(2)}) between background and text`);
  }

  // Check border radius for conservative industries
  if (design.industry === 'government') {
    const radius = parseInt(design.borderRadius.replace('px', ''));
    if (radius > 8) {
      warnings.push('Border radius may be too rounded for government aesthetic');
    }
  }

  return warnings;
}

// Export default BD design system
export const defaultBDDesign = createBDDesignSystem();
