/**
 * ContactEnrichmentCard - Structured display for contact enrichment agent results.
 */

import { User, Building2, Phone, Mail, Linkedin, Star, Briefcase } from 'lucide-react';

interface ContactEnrichmentResult {
  name?: string;
  title?: string;
  company?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  tier?: number;
  programs?: string[];
  enrichment_sources?: string[];
  key_insights?: string[];
  outreach_angles?: string[];
  relationship_strength?: string;
  [key: string]: unknown;
}

interface Props {
  result: ContactEnrichmentResult;
  onNavigateToContact?: (name: string) => void;
  onNavigateToProgram?: (name: string) => void;
}

const TIER_COLORS: Record<number, string> = {
  1: 'bg-purple-100 text-purple-700',
  2: 'bg-blue-100 text-blue-700',
  3: 'bg-cyan-100 text-cyan-700',
  4: 'bg-emerald-100 text-emerald-700',
  5: 'bg-amber-100 text-amber-700',
  6: 'bg-slate-100 text-slate-700',
};

export function ContactEnrichmentCard({ result, onNavigateToContact, onNavigateToProgram }: Props) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 border-b border-slate-100">
        <div className="flex items-center gap-2 mb-1">
          <User className="h-5 w-5 text-purple-600" />
          <h3 className="font-semibold text-slate-900">Contact Enrichment</h3>
        </div>
        {result.name && (
          <button
            onClick={() => onNavigateToContact?.(result.name!)}
            className="text-lg font-bold text-purple-700 hover:text-purple-900 hover:underline"
          >
            {result.name}
          </button>
        )}
        <div className="flex items-center gap-2 mt-1">
          {result.title && <span className="text-sm text-slate-500">{result.title}</span>}
          {result.tier && (
            <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${TIER_COLORS[result.tier] || TIER_COLORS[6]}`}>
              Tier {result.tier}
            </span>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Contact Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {result.company && (
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-slate-400" />
              <span className="text-sm text-slate-700">{result.company}</span>
            </div>
          )}
          {result.email && (
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-slate-400" />
              <span className="text-sm text-slate-700">{result.email}</span>
            </div>
          )}
          {result.phone && (
            <div className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-slate-400" />
              <span className="text-sm text-slate-700">{result.phone}</span>
            </div>
          )}
          {result.linkedin && (
            <div className="flex items-center gap-2">
              <Linkedin className="h-4 w-4 text-slate-400" />
              <a href={result.linkedin} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline truncate">
                LinkedIn Profile
              </a>
            </div>
          )}
        </div>

        {/* Programs */}
        {result.programs && result.programs.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Briefcase className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-400 uppercase font-medium">Programs</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {result.programs.map((p, i) => (
                <button
                  key={i}
                  onClick={() => onNavigateToProgram?.(p)}
                  className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full hover:bg-blue-200 transition-colors"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Key Insights */}
        {result.key_insights && result.key_insights.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Star className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-400 uppercase font-medium">Key Insights</span>
            </div>
            <ul className="space-y-1">
              {result.key_insights.map((insight, i) => (
                <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                  <span className="text-blue-400 mt-1">•</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Outreach Angles */}
        {result.outreach_angles && result.outreach_angles.length > 0 && (
          <div className="p-3 bg-amber-50 rounded-lg border border-amber-100">
            <p className="text-xs text-amber-600 uppercase font-medium mb-1">Outreach Angles</p>
            <ul className="space-y-1">
              {result.outreach_angles.map((angle, i) => (
                <li key={i} className="text-sm text-amber-800">• {angle}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
