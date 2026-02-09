/**
 * ProgramAnalysisCard - Structured display for program analysis agent results.
 */

import { Building2, Users, MapPin, Shield, TrendingUp, FileText } from 'lucide-react';

interface ProgramAnalysisResult {
  program_name?: string;
  agency?: string;
  prime_contractor?: string;
  contract_value?: string;
  description?: string;
  key_contacts?: Array<{ name: string; title?: string; company?: string }>;
  competitive_landscape?: string[];
  opportunities?: string[];
  risks?: string[];
  recommendation?: string;
  [key: string]: unknown;
}

interface Props {
  result: ProgramAnalysisResult;
  onNavigateToContact?: (name: string) => void;
  onNavigateToProgram?: (name: string) => void;
}

export function ProgramAnalysisCard({ result, onNavigateToContact, onNavigateToProgram }: Props) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 border-b border-slate-100">
        <div className="flex items-center gap-2 mb-1">
          <Building2 className="h-5 w-5 text-blue-600" />
          <h3 className="font-semibold text-slate-900">Program Analysis</h3>
        </div>
        {result.program_name && (
          <button
            onClick={() => onNavigateToProgram?.(result.program_name!)}
            className="text-lg font-bold text-blue-700 hover:text-blue-900 hover:underline"
          >
            {result.program_name}
          </button>
        )}
        {result.agency && (
          <p className="text-sm text-slate-500">{result.agency}</p>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* Key Facts */}
        <div className="grid grid-cols-2 gap-3">
          {result.prime_contractor && (
            <div className="flex items-start gap-2">
              <Shield className="h-4 w-4 text-purple-500 mt-0.5" />
              <div>
                <p className="text-xs text-slate-400 uppercase font-medium">Prime</p>
                <p className="text-sm font-medium text-slate-700">{result.prime_contractor}</p>
              </div>
            </div>
          )}
          {result.contract_value && (
            <div className="flex items-start gap-2">
              <TrendingUp className="h-4 w-4 text-green-500 mt-0.5" />
              <div>
                <p className="text-xs text-slate-400 uppercase font-medium">Value</p>
                <p className="text-sm font-medium text-slate-700">{result.contract_value}</p>
              </div>
            </div>
          )}
        </div>

        {/* Description */}
        {result.description && (
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              <FileText className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-400 uppercase font-medium">Summary</span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">{result.description}</p>
          </div>
        )}

        {/* Key Contacts */}
        {result.key_contacts && result.key_contacts.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Users className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-400 uppercase font-medium">Key Contacts</span>
            </div>
            <div className="space-y-1">
              {result.key_contacts.slice(0, 5).map((c, i) => (
                <button
                  key={i}
                  onClick={() => onNavigateToContact?.(c.name)}
                  className="block w-full text-left px-2 py-1.5 rounded hover:bg-slate-50 transition-colors"
                >
                  <span className="text-sm font-medium text-blue-700 hover:underline">{c.name}</span>
                  {c.title && <span className="text-xs text-slate-400 ml-2">{c.title}</span>}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Competitive Landscape */}
        {result.competitive_landscape && result.competitive_landscape.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <MapPin className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-400 uppercase font-medium">Competitive Landscape</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {result.competitive_landscape.map((c, i) => (
                <span key={i} className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Recommendation */}
        {result.recommendation && (
          <div className="p-3 bg-green-50 rounded-lg border border-green-100">
            <p className="text-xs text-green-600 uppercase font-medium mb-1">Recommendation</p>
            <p className="text-sm text-green-800">{result.recommendation}</p>
          </div>
        )}
      </div>
    </div>
  );
}
