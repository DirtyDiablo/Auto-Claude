"""
BD Component Styles Library

Pre-built component styles for BD dashboards that integrate with the design system.
Includes priority badges, contact cards, pipeline charts, and more.
"""

from typing import Optional
from .design_system import DesignSystem, ColorPalette


class BDComponentStyles:
    """
    Static methods for generating BD-specific component styles.

    These styles are designed to work with the DesignSystem class
    and provide consistent styling for common BD dashboard components.
    """

    @staticmethod
    def get_priority_badge_styles() -> str:
        """
        Generate styles for priority badges.

        Priority levels: Critical, High, Medium, Low, Standard
        """
        return """
/* Priority Badge Styles */
.priority-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.priority-badge::before {
  content: '';
  width: 0.5rem;
  height: 0.5rem;
  border-radius: var(--border-radius-full);
}

/* Critical Priority */
.priority-badge--critical {
  background-color: rgba(220, 38, 38, 0.1);
  color: var(--color-priority-critical);
  border: 1px solid rgba(220, 38, 38, 0.2);
}
.priority-badge--critical::before {
  background-color: var(--color-priority-critical);
  animation: pulse-critical 1.5s ease-in-out infinite;
}

/* High Priority */
.priority-badge--high {
  background-color: rgba(234, 88, 12, 0.1);
  color: var(--color-priority-high);
  border: 1px solid rgba(234, 88, 12, 0.2);
}
.priority-badge--high::before {
  background-color: var(--color-priority-high);
}

/* Medium Priority */
.priority-badge--medium {
  background-color: rgba(202, 138, 4, 0.1);
  color: var(--color-priority-medium);
  border: 1px solid rgba(202, 138, 4, 0.2);
}
.priority-badge--medium::before {
  background-color: var(--color-priority-medium);
}

/* Low Priority */
.priority-badge--low {
  background-color: rgba(22, 163, 74, 0.1);
  color: var(--color-priority-low);
  border: 1px solid rgba(22, 163, 74, 0.2);
}
.priority-badge--low::before {
  background-color: var(--color-priority-low);
}

/* Standard Priority */
.priority-badge--standard {
  background-color: rgba(107, 114, 128, 0.1);
  color: var(--color-text-secondary);
  border: 1px solid rgba(107, 114, 128, 0.2);
}
.priority-badge--standard::before {
  background-color: var(--color-text-secondary);
}

@keyframes pulse-critical {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}
"""

    @staticmethod
    def get_tier_badge_styles() -> str:
        """
        Generate styles for contact tier badges.

        Tiers: 1 (Executive) through 6 (IC)
        """
        return """
/* Contact Tier Badge Styles */
.tier-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.375rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  font-weight: 700;
}

/* Tier 1 - Executive/C-Suite */
.tier-badge--1 {
  background: linear-gradient(135deg, #7C3AED, #6D28D9);
  color: white;
  box-shadow: 0 2px 4px rgba(124, 58, 237, 0.3);
}

/* Tier 2 - Director */
.tier-badge--2 {
  background: linear-gradient(135deg, #2563EB, #1D4ED8);
  color: white;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
}

/* Tier 3 - Program Manager */
.tier-badge--3 {
  background: linear-gradient(135deg, #0891B2, #0E7490);
  color: white;
  box-shadow: 0 2px 4px rgba(8, 145, 178, 0.3);
}

/* Tier 4 - Manager */
.tier-badge--4 {
  background: linear-gradient(135deg, #059669, #047857);
  color: white;
  box-shadow: 0 2px 4px rgba(5, 150, 105, 0.3);
}

/* Tier 5 - Senior IC */
.tier-badge--5 {
  background: linear-gradient(135deg, #65A30D, #4D7C0F);
  color: white;
  box-shadow: 0 2px 4px rgba(101, 163, 13, 0.3);
}

/* Tier 6 - IC */
.tier-badge--6 {
  background: linear-gradient(135deg, #6B7280, #4B5563);
  color: white;
  box-shadow: 0 2px 4px rgba(107, 114, 128, 0.3);
}
"""

    @staticmethod
    def get_contact_card_styles() -> str:
        """
        Generate styles for contact cards.

        Includes avatar, info section, and action buttons.
        """
        return """
/* Contact Card Styles */
.contact-card {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-radius: var(--border-radius);
  border: 1px solid rgba(148, 163, 184, 0.1);
  transition: all var(--transition);
}

.contact-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-lg);
  transform: translateY(-1px);
}

/* Avatar */
.contact-card__avatar {
  position: relative;
  flex-shrink: 0;
  width: 3rem;
  height: 3rem;
  border-radius: var(--border-radius-full);
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1rem;
}

.contact-card__avatar--image {
  object-fit: cover;
}

.contact-card__tier {
  position: absolute;
  bottom: -0.25rem;
  right: -0.25rem;
}

/* Info Section */
.contact-card__info {
  flex: 1;
  min-width: 0;
}

.contact-card__name {
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contact-card__title {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contact-card__company {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  opacity: 0.8;
}

/* Meta Tags */
.contact-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.contact-card__tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.125rem 0.5rem;
  background-color: rgba(148, 163, 184, 0.1);
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

/* Actions */
.contact-card__actions {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity var(--transition);
}

.contact-card:hover .contact-card__actions {
  opacity: 1;
}

.contact-card__action {
  padding: 0.5rem;
  border-radius: var(--border-radius);
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.contact-card__action:hover {
  background-color: var(--color-primary);
  color: white;
}
"""

    @staticmethod
    def get_pipeline_chart_styles() -> str:
        """
        Generate styles for pipeline/funnel charts.

        Includes stage indicators and value displays.
        """
        return """
/* Pipeline Chart Styles */
.pipeline-chart {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.pipeline-stage {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.pipeline-stage__label {
  flex: 0 0 120px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.pipeline-stage__bar-container {
  flex: 1;
  height: 2rem;
  background-color: rgba(148, 163, 184, 0.1);
  border-radius: var(--border-radius);
  overflow: hidden;
  position: relative;
}

.pipeline-stage__bar {
  height: 100%;
  border-radius: var(--border-radius);
  transition: width 0.5s ease-out;
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-sm);
}

.pipeline-stage__value {
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.pipeline-stage__count {
  flex: 0 0 60px;
  text-align: right;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Stage Colors */
.pipeline-stage--prospect .pipeline-stage__bar {
  background: linear-gradient(90deg, #3B82F6, #2563EB);
}

.pipeline-stage--qualify .pipeline-stage__bar {
  background: linear-gradient(90deg, #8B5CF6, #7C3AED);
}

.pipeline-stage--pursue .pipeline-stage__bar {
  background: linear-gradient(90deg, #EC4899, #DB2777);
}

.pipeline-stage--capture .pipeline-stage__bar {
  background: linear-gradient(90deg, #F59E0B, #D97706);
}

.pipeline-stage--won .pipeline-stage__bar {
  background: linear-gradient(90deg, #10B981, #059669);
}

/* Pipeline Summary */
.pipeline-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.pipeline-summary__card {
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-radius: var(--border-radius);
  border: 1px solid rgba(148, 163, 184, 0.1);
  text-align: center;
}

.pipeline-summary__value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.pipeline-summary__label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
"""

    @staticmethod
    def get_data_table_styles() -> str:
        """
        Generate styles for data tables.

        Includes sortable headers, row hover states, and pagination.
        """
        return """
/* Data Table Styles */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.data-table thead {
  background-color: rgba(148, 163, 184, 0.05);
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.data-table th {
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  cursor: pointer;
  user-select: none;
  transition: color var(--transition);
}

.data-table th:hover {
  color: var(--color-text-primary);
}

.data-table th--sortable::after {
  content: '↕';
  margin-left: 0.5rem;
  opacity: 0.3;
}

.data-table th--sorted-asc::after {
  content: '↑';
  opacity: 1;
}

.data-table th--sorted-desc::after {
  content: '↓';
  opacity: 1;
}

.data-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid rgba(148, 163, 184, 0.05);
  color: var(--color-text-primary);
  vertical-align: middle;
}

.data-table tbody tr {
  transition: background-color var(--transition);
}

.data-table tbody tr:hover {
  background-color: rgba(148, 163, 184, 0.05);
}

.data-table tbody tr--selected {
  background-color: rgba(37, 99, 235, 0.1);
}

/* Pagination */
.data-table__pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  border-top: 1px solid rgba(148, 163, 184, 0.1);
}

.data-table__pagination-info {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.data-table__pagination-controls {
  display: flex;
  gap: 0.5rem;
}

.data-table__pagination-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--border-radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition);
}

.data-table__pagination-btn:hover:not(:disabled) {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.data-table__pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.data-table__pagination-btn--active {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}
"""

    @staticmethod
    def get_stat_card_styles() -> str:
        """
        Generate styles for statistic cards.

        Includes animated counters, trends, and sparklines.
        """
        return """
/* Stat Card Styles */
.stat-card {
  padding: var(--spacing-lg);
  background-color: var(--color-surface);
  border-radius: var(--border-radius);
  border: 1px solid rgba(148, 163, 184, 0.1);
  transition: all var(--transition);
}

.stat-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-lg);
}

.stat-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.stat-card__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.stat-card__icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-card__icon--primary { background-color: var(--color-primary); }
.stat-card__icon--success { background-color: var(--color-success); }
.stat-card__icon--warning { background-color: var(--color-warning); }
.stat-card__icon--info { background-color: var(--color-info); }

.stat-card__value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
}

.stat-card__trend {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: var(--spacing-sm);
  padding: 0.25rem 0.5rem;
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.stat-card__trend--up {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--color-success);
}

.stat-card__trend--down {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--color-error);
}

.stat-card__sparkline {
  margin-top: var(--spacing-md);
  height: 40px;
}
"""

    @staticmethod
    def get_all_styles(design_system: Optional[DesignSystem] = None) -> str:
        """
        Generate all BD component styles.

        Optionally integrates with a DesignSystem for consistent theming.
        """
        styles = []

        # Include design system CSS if provided
        if design_system:
            styles.append(design_system.to_css())

        # Add all component styles
        styles.extend([
            BDComponentStyles.get_priority_badge_styles(),
            BDComponentStyles.get_tier_badge_styles(),
            BDComponentStyles.get_contact_card_styles(),
            BDComponentStyles.get_pipeline_chart_styles(),
            BDComponentStyles.get_data_table_styles(),
            BDComponentStyles.get_stat_card_styles(),
        ])

        return "\n".join(styles)


# Convenience function
def generate_bd_stylesheet(project_name: str = "BD Intelligence Dashboard") -> str:
    """
    Generate a complete stylesheet for BD dashboards.

    Includes the design system and all component styles.
    """
    from .design_system import DesignSystemGenerator

    design = DesignSystemGenerator.generate_for_bd(project_name)
    return BDComponentStyles.get_all_styles(design)


if __name__ == "__main__":
    # Demo: Generate complete BD stylesheet
    stylesheet = generate_bd_stylesheet()
    print(stylesheet)
