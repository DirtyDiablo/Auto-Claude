"""
UI-UX-Pro-Max Design Intelligence System

Industry-specific design system generator for creating professional BD dashboards,
proposals, and marketing materials with appropriate styling.

Based on UI-UX-Pro-Max design principles with 100+ industry-specific reasoning rules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Industry(Enum):
    """Target industry for design system generation."""
    GOVERNMENT = "government"
    DEFENSE = "defense"
    ENTERPRISE_SAAS = "enterprise_saas"
    CONSULTING = "consulting"
    FINANCIAL = "financial"


@dataclass
class ColorPalette:
    """Complete color palette for a design system."""
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    success: str = "#10B981"
    warning: str = "#F59E0B"
    error: str = "#EF4444"
    info: str = "#3B82F6"

    # BD-specific priority colors
    priority_critical: str = "#DC2626"
    priority_high: str = "#EA580C"
    priority_medium: str = "#CA8A04"
    priority_low: str = "#16A34A"

    # Tier colors for contacts
    tier_1: str = "#7C3AED"  # Executive - Purple
    tier_2: str = "#2563EB"  # Director - Blue
    tier_3: str = "#0891B2"  # Program Manager - Cyan
    tier_4: str = "#059669"  # Manager - Emerald
    tier_5: str = "#65A30D"  # Senior IC - Lime
    tier_6: str = "#6B7280"  # IC - Gray

    def to_css_vars(self) -> str:
        """Generate CSS custom properties."""
        return f"""
:root {{
  /* Primary Colors */
  --color-primary: {self.primary};
  --color-secondary: {self.secondary};
  --color-accent: {self.accent};

  /* Background & Surface */
  --color-background: {self.background};
  --color-surface: {self.surface};

  /* Text */
  --color-text-primary: {self.text_primary};
  --color-text-secondary: {self.text_secondary};

  /* Semantic */
  --color-success: {self.success};
  --color-warning: {self.warning};
  --color-error: {self.error};
  --color-info: {self.info};

  /* BD Priority Colors */
  --color-priority-critical: {self.priority_critical};
  --color-priority-high: {self.priority_high};
  --color-priority-medium: {self.priority_medium};
  --color-priority-low: {self.priority_low};

  /* Contact Tier Colors */
  --color-tier-1: {self.tier_1};
  --color-tier-2: {self.tier_2};
  --color-tier-3: {self.tier_3};
  --color-tier-4: {self.tier_4};
  --color-tier-5: {self.tier_5};
  --color-tier-6: {self.tier_6};
}}
"""

    def to_tailwind_config(self) -> Dict:
        """Generate Tailwind CSS color configuration."""
        return {
            "colors": {
                "primary": {
                    "DEFAULT": self.primary,
                    "light": self._lighten(self.primary, 0.2),
                    "dark": self._darken(self.primary, 0.2),
                },
                "secondary": {
                    "DEFAULT": self.secondary,
                    "light": self._lighten(self.secondary, 0.2),
                    "dark": self._darken(self.secondary, 0.2),
                },
                "accent": self.accent,
                "background": self.background,
                "surface": self.surface,
                "success": self.success,
                "warning": self.warning,
                "error": self.error,
                "info": self.info,
                "priority": {
                    "critical": self.priority_critical,
                    "high": self.priority_high,
                    "medium": self.priority_medium,
                    "low": self.priority_low,
                },
                "tier": {
                    "1": self.tier_1,
                    "2": self.tier_2,
                    "3": self.tier_3,
                    "4": self.tier_4,
                    "5": self.tier_5,
                    "6": self.tier_6,
                }
            }
        }

    def _lighten(self, hex_color: str, amount: float) -> str:
        """Lighten a hex color by a percentage."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _darken(self, hex_color: str, amount: float) -> str:
        """Darken a hex color by a percentage."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, int(r * (1 - amount)))
        g = max(0, int(g * (1 - amount)))
        b = max(0, int(b * (1 - amount)))
        return f"#{r:02x}{g:02x}{b:02x}"


@dataclass
class Typography:
    """Typography system configuration."""
    heading_font: str
    body_font: str
    mono_font: str = "JetBrains Mono"
    heading_weights: List[int] = field(default_factory=lambda: [600, 700, 800])
    body_weights: List[int] = field(default_factory=lambda: [400, 500, 600])
    base_size: str = "16px"
    scale_ratio: float = 1.25  # Major third scale

    def get_google_fonts_url(self) -> str:
        """Generate Google Fonts import URL."""
        fonts = []

        # Heading font
        heading_weights = ";".join(str(w) for w in self.heading_weights)
        heading_encoded = self.heading_font.replace(" ", "+")
        fonts.append(f"{heading_encoded}:wght@{heading_weights}")

        # Body font (if different)
        if self.body_font != self.heading_font:
            body_weights = ";".join(str(w) for w in self.body_weights)
            body_encoded = self.body_font.replace(" ", "+")
            fonts.append(f"{body_encoded}:wght@{body_weights}")

        # Mono font
        mono_encoded = self.mono_font.replace(" ", "+")
        fonts.append(f"{mono_encoded}:wght@400;500")

        return f"https://fonts.googleapis.com/css2?family={'&family='.join(fonts)}&display=swap"

    def to_css(self) -> str:
        """Generate typography CSS."""
        return f"""
/* Typography */
:root {{
  --font-heading: '{self.heading_font}', system-ui, sans-serif;
  --font-body: '{self.body_font}', system-ui, sans-serif;
  --font-mono: '{self.mono_font}', 'Consolas', monospace;
  --font-size-base: {self.base_size};
  --font-scale: {self.scale_ratio};
}}

/* Type Scale */
.text-xs {{ font-size: calc(var(--font-size-base) / var(--font-scale) / var(--font-scale)); }}
.text-sm {{ font-size: calc(var(--font-size-base) / var(--font-scale)); }}
.text-base {{ font-size: var(--font-size-base); }}
.text-lg {{ font-size: calc(var(--font-size-base) * var(--font-scale)); }}
.text-xl {{ font-size: calc(var(--font-size-base) * var(--font-scale) * var(--font-scale)); }}
.text-2xl {{ font-size: calc(var(--font-size-base) * var(--font-scale) * var(--font-scale) * var(--font-scale)); }}
.text-3xl {{ font-size: calc(var(--font-size-base) * var(--font-scale) * var(--font-scale) * var(--font-scale) * var(--font-scale)); }}

h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-heading);
  font-weight: 700;
  line-height: 1.2;
}}

body {{
  font-family: var(--font-body);
  font-weight: 400;
  line-height: 1.6;
}}

code, pre {{
  font-family: var(--font-mono);
}}
"""


@dataclass
class DesignSystem:
    """Complete design system configuration."""
    name: str
    industry: Industry
    style: str
    colors: ColorPalette
    typography: Typography
    spacing_unit: str = "4px"
    border_radius: str = "8px"
    shadow: str = "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)"
    shadow_lg: str = "0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)"
    transition: str = "150ms cubic-bezier(0.4, 0, 0.2, 1)"
    anti_patterns: List[str] = field(default_factory=list)
    notes: str = ""

    def to_css(self) -> str:
        """Generate complete CSS output."""
        return f"""
/* =============================================================================
   {self.name.upper()} DESIGN SYSTEM
   Industry: {self.industry.value.title()}
   Style: {self.style}
   ============================================================================= */

@import url('{self.typography.get_google_fonts_url()}');

{self.colors.to_css_vars()}

{self.typography.to_css()}

/* Spacing & Layout */
:root {{
  --spacing-unit: {self.spacing_unit};
  --spacing-xs: calc(var(--spacing-unit) * 1);
  --spacing-sm: calc(var(--spacing-unit) * 2);
  --spacing-md: calc(var(--spacing-unit) * 4);
  --spacing-lg: calc(var(--spacing-unit) * 6);
  --spacing-xl: calc(var(--spacing-unit) * 8);
  --spacing-2xl: calc(var(--spacing-unit) * 12);

  --border-radius: {self.border_radius};
  --border-radius-sm: calc({self.border_radius} / 2);
  --border-radius-lg: calc({self.border_radius} * 2);
  --border-radius-full: 9999px;

  --shadow: {self.shadow};
  --shadow-lg: {self.shadow_lg};

  --transition: {self.transition};
}}

/* Base Styles */
* {{
  transition: background-color var(--transition),
              border-color var(--transition),
              box-shadow var(--transition);
}}

body {{
  background-color: var(--color-background);
  color: var(--color-text-primary);
}}

/* Card Component */
.card {{
  background-color: var(--color-surface);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow);
  padding: var(--spacing-md);
}}

.card:hover {{
  box-shadow: var(--shadow-lg);
}}

/* Button Base */
.btn {{
  font-family: var(--font-body);
  font-weight: 500;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  transition: all var(--transition);
}}

.btn-primary {{
  background-color: var(--color-primary);
  color: white;
}}

.btn-primary:hover {{
  filter: brightness(1.1);
}}

/* Notes: {self.notes} */
/* Anti-patterns to avoid: {', '.join(self.anti_patterns)} */
"""


class DesignSystemGenerator:
    """Generator for industry-specific design systems."""

    INDUSTRY_RULES: Dict[Industry, Dict] = {
        Industry.GOVERNMENT: {
            "style": "Accessible & Ethical + Swiss Modernism",
            "colors": ColorPalette(
                primary="#003366",      # Navy blue - trust, authority
                secondary="#005A9C",    # Lighter blue
                accent="#CC0000",       # Red accent - government
                background="#F8FAFC",   # Light gray
                surface="#FFFFFF",
                text_primary="#1E293B",
                text_secondary="#64748B",
            ),
            "typography": Typography(
                heading_font="Source Sans Pro",
                body_font="Open Sans",
            ),
            "border_radius": "4px",     # More conservative
            "anti_patterns": [
                "Dark mode only",
                "Low contrast ratios",
                "Complex animations",
                "AI/tech gradient vibes",
                "Playful illustrations",
                "Non-accessible colors",
            ],
            "notes": "WCAG AAA compliance required. Conservative, trustworthy aesthetic.",
        },

        Industry.DEFENSE: {
            "style": "Swiss Modernism 2.0 + Data-Dense Dashboard",
            "colors": ColorPalette(
                primary="#1A365D",      # Deep navy
                secondary="#2B6CB0",    # Steel blue
                accent="#ED8936",       # Alert orange
                background="#1A202C",   # Dark background
                surface="#2D3748",      # Dark surface
                text_primary="#F7FAFC",
                text_secondary="#A0AEC0",
            ),
            "typography": Typography(
                heading_font="Inter",
                body_font="IBM Plex Sans",
            ),
            "border_radius": "6px",
            "anti_patterns": [
                "Consumer aesthetics",
                "Playful animations",
                "Bright/saturated colors",
                "Casual typography",
                "Marketing-style layouts",
                "Social media patterns",
            ],
            "notes": "High information density. Dark mode default for operational contexts.",
        },

        Industry.ENTERPRISE_SAAS: {
            "style": "Minimalism + Glassmorphism",
            "colors": ColorPalette(
                primary="#4F46E5",      # Indigo
                secondary="#10B981",    # Emerald
                accent="#8B5CF6",       # Violet
                background="#F9FAFB",
                surface="#FFFFFF",
                text_primary="#111827",
                text_secondary="#6B7280",
            ),
            "typography": Typography(
                heading_font="Poppins",
                body_font="Inter",
            ),
            "border_radius": "12px",
            "shadow": "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)",
            "anti_patterns": [
                "Dated gradients",
                "Excessive drop shadows",
                "Busy/cluttered layouts",
                "Skeuomorphic elements",
                "Too many colors",
            ],
            "notes": "Modern, clean aesthetic. Focus on usability and white space.",
        },

        Industry.CONSULTING: {
            "style": "Trust & Authority + Editorial Grid",
            "colors": ColorPalette(
                primary="#0F172A",      # Slate 900
                secondary="#1E40AF",    # Blue 800
                accent="#059669",       # Emerald 600
                background="#FFFFFF",
                surface="#F8FAFC",
                text_primary="#0F172A",
                text_secondary="#475569",
            ),
            "typography": Typography(
                heading_font="Merriweather",  # Serif for authority
                body_font="Source Sans Pro",
                heading_weights=[400, 700, 900],
            ),
            "border_radius": "4px",
            "anti_patterns": [
                "Tech startup vibes",
                "Playful illustrations",
                "Casual tone",
                "Bright neon colors",
                "Trendy animations",
                "Informal typography",
            ],
            "notes": "Professional, authoritative. Serif headings convey expertise and trust.",
        },

        Industry.FINANCIAL: {
            "style": "Financial Dashboard + Trust & Authority",
            "colors": ColorPalette(
                primary="#0D9488",      # Teal
                secondary="#1E3A8A",    # Deep blue
                accent="#F59E0B",       # Amber
                background="#FAFAFA",
                surface="#FFFFFF",
                text_primary="#18181B",
                text_secondary="#71717A",
            ),
            "typography": Typography(
                heading_font="DM Sans",
                body_font="Inter",
            ),
            "border_radius": "8px",
            "anti_patterns": [
                "Playful colors",
                "Casual/handwritten fonts",
                "AI purple gradients",
                "Crypto/Web3 aesthetics",
                "Excessive animations",
            ],
            "notes": "Trust and stability. Data visualization focused. Conservative color usage.",
        },
    }

    @classmethod
    def generate(cls, industry: Industry, project_name: str) -> DesignSystem:
        """Generate a design system for a specific industry."""
        rules = cls.INDUSTRY_RULES[industry]

        return DesignSystem(
            name=project_name,
            industry=industry,
            style=rules["style"],
            colors=rules["colors"],
            typography=rules["typography"],
            border_radius=rules.get("border_radius", "8px"),
            shadow=rules.get("shadow", "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)"),
            anti_patterns=rules["anti_patterns"],
            notes=rules["notes"],
        )

    @classmethod
    def generate_for_bd(cls, project_name: str = "BD Intelligence Dashboard") -> DesignSystem:
        """
        Generate an optimized design system for BD dashboards.

        Combines Defense industry rules with BD-specific enhancements:
        - High information density
        - Clear priority indicators
        - Professional/authoritative aesthetic
        - Accessible but sophisticated
        """
        base = cls.generate(Industry.DEFENSE, project_name)

        # Override with BD-optimized settings
        base.colors = ColorPalette(
            primary="#1E40AF",       # Professional blue
            secondary="#7C3AED",     # Purple for AI features
            accent="#F59E0B",        # Amber for highlights
            background="#0F172A",    # Dark slate background
            surface="#1E293B",       # Slate surface
            text_primary="#F1F5F9",
            text_secondary="#94A3B8",
            # Enhanced priority colors for BD
            priority_critical="#DC2626",
            priority_high="#EA580C",
            priority_medium="#CA8A04",
            priority_low="#16A34A",
        )

        base.typography = Typography(
            heading_font="Inter",
            body_font="Inter",
            mono_font="JetBrains Mono",
            heading_weights=[500, 600, 700],
            body_weights=[400, 500, 600],
        )

        base.style = "BD Intelligence + Data-Dense Dashboard"
        base.notes = "Optimized for federal BD workflows. High data density, clear hierarchies."

        return base

    @classmethod
    def validate_design(cls, design: DesignSystem) -> List[str]:
        """
        Validate a design system against anti-patterns.

        Returns a list of warnings if any anti-patterns are detected.
        """
        warnings = []

        # Check color contrast (simplified check)
        def get_luminance(hex_color: str) -> float:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255

        bg_luminance = get_luminance(design.colors.background)
        text_luminance = get_luminance(design.colors.text_primary)

        contrast_ratio = abs(bg_luminance - text_luminance)
        if contrast_ratio < 0.5:
            warnings.append(f"Low contrast ratio ({contrast_ratio:.2f}) between background and text")

        # Check for overly saturated colors in government/consulting contexts
        if design.industry in [Industry.GOVERNMENT, Industry.CONSULTING]:
            # Simple saturation check
            primary_hex = design.colors.primary.lstrip('#')
            r, g, b = int(primary_hex[:2], 16), int(primary_hex[2:4], 16), int(primary_hex[4:6], 16)
            max_c, min_c = max(r, g, b), min(r, g, b)
            saturation = (max_c - min_c) / max_c if max_c > 0 else 0
            if saturation > 0.9:
                warnings.append("Primary color may be too saturated for professional context")

        # Check border radius for conservative industries
        if design.industry == Industry.GOVERNMENT:
            radius_value = int(design.border_radius.replace("px", ""))
            if radius_value > 8:
                warnings.append("Border radius may be too rounded for government aesthetic")

        return warnings


# Export convenience function
def create_bd_design_system(name: str = "BD Intelligence Dashboard") -> DesignSystem:
    """Create a BD-optimized design system."""
    return DesignSystemGenerator.generate_for_bd(name)


if __name__ == "__main__":
    # Demo: Generate and print a BD design system
    design = create_bd_design_system()
    print(design.to_css())

    # Validate
    warnings = DesignSystemGenerator.validate_design(design)
    if warnings:
        print("\nValidation Warnings:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\nDesign system validated successfully!")
