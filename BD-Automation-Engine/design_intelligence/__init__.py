"""
UI-UX-Pro-Max Design Intelligence System

Industry-specific design system generator for creating professional BD dashboards,
proposals, and marketing materials with appropriate styling.

Usage:
    from design_intelligence import (
        DesignSystemGenerator,
        create_bd_design_system,
        generate_bd_stylesheet,
        Industry,
    )

    # Generate a BD-optimized design system
    design = create_bd_design_system("My Dashboard")

    # Get CSS output
    css = design.to_css()

    # Or generate complete stylesheet with components
    full_css = generate_bd_stylesheet("My Dashboard")
"""

from .design_system import (
    Industry,
    ColorPalette,
    Typography,
    DesignSystem,
    DesignSystemGenerator,
    create_bd_design_system,
)

from .component_library import (
    BDComponentStyles,
    generate_bd_stylesheet,
)

__all__ = [
    # Enums
    "Industry",

    # Data Classes
    "ColorPalette",
    "Typography",
    "DesignSystem",

    # Generators
    "DesignSystemGenerator",
    "BDComponentStyles",

    # Convenience Functions
    "create_bd_design_system",
    "generate_bd_stylesheet",
]

__version__ = "1.0.0"
