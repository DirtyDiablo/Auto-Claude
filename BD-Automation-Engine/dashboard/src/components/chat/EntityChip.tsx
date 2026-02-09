import { User, Building2, Briefcase } from 'lucide-react';

export interface EntityCard {
  type: 'contact' | 'program' | 'job';
  name: string;
  id: string;
  meta: Record<string, string>;
}

interface EntityChipProps {
  entity: EntityCard;
  onNavigate: (type: EntityCard['type'], id: string, name: string) => void;
}

const chipStyles: Record<EntityCard['type'], { icon: typeof User; bg: string; border: string; text: string }> = {
  contact: { icon: User, bg: 'bg-blue-50 dark:bg-blue-900/30', border: 'border-blue-200 dark:border-blue-700', text: 'text-blue-700 dark:text-blue-300' },
  program: { icon: Building2, bg: 'bg-purple-50 dark:bg-purple-900/30', border: 'border-purple-200 dark:border-purple-700', text: 'text-purple-700 dark:text-purple-300' },
  job: { icon: Briefcase, bg: 'bg-amber-50 dark:bg-amber-900/30', border: 'border-amber-200 dark:border-amber-700', text: 'text-amber-700 dark:text-amber-300' },
};

export function EntityChip({ entity, onNavigate }: EntityChipProps) {
  const style = chipStyles[entity.type];
  const Icon = style.icon;
  const subtitle = Object.values(entity.meta).filter(Boolean).slice(0, 2).join(' · ');

  return (
    <button
      onClick={() => onNavigate(entity.type, entity.id, entity.name)}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium
        ${style.bg} ${style.border} ${style.text}
        hover:shadow-sm transition-all cursor-pointer max-w-full`}
      title={`View ${entity.type}: ${entity.name}`}
    >
      <Icon className="h-3 w-3 shrink-0" />
      <span className="truncate">{entity.name}</span>
      {subtitle && <span className="text-[10px] opacity-70 truncate hidden sm:inline">— {subtitle}</span>}
    </button>
  );
}
