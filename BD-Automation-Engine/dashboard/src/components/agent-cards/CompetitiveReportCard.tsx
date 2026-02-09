/**
 * CompetitiveReportCard - Structured display for competitive analysis agent results.
 */

import { Swords, Building2, TrendingUp, AlertTriangle, Target, ArrowRight } from 'lucide-react';

interface CompetitiveReportResult {
  target_program?: string;
  competitors?: Array<{
    name: string;
    strengths?: string[];
    weaknesses?: string[];
    win_probability?: string;
  }>;
  market_position?: string;
  key_differentiators?: string[];
  threats?: string[];
  win_themes?: string[];
  recommendation?: string;
  [key: string]: unknown;
}

interface Props {
  result: CompetitiveReportResult;
}

export function CompetitiveReportCard({ result }: Props) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-red-50 to-orange-50 border-b border-slate-100">
        <div className="flex items-center gap-2 mb-1">
          <Swords className="h-5 w-5 text-red-600" />
          <h3 className="font-semibold text-slate-900">Competitive Analysis</h3>
        </div>
        {result.target_program && (
          <p className="text-lg font-bold text-red-700">{result.target_program}</p>
        )}
        {result.market_position && (
          <p className="text-sm text-slate-500 mt-1">{result.market_position}</p>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* Competitors */}
        {result.competitors && result.competitors.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Building2 className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-400 uppercase font-medium">Competitors</span>
            </div>
            <div className="space-y-2">
              {result.competitors.map((comp, i) => (
                <div key={i} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm text-slate-800">{comp.name}</span>
                    {comp.win_probability && (
                      <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full">
                        Win: {comp.win_probability}
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {comp.strengths && comp.strengths.length > 0 && (
                      <div>
                        <p className="text-xs text-green-600 font-medium mb-0.5">Strengths</p>
                        {comp.strengths.map((s, j) => (
                          <p key={j} className="text-xs text-slate-500">• {s}</p>
                        ))}
                      </div>
                    )}
                    {comp.weaknesses && comp.weaknesses.length > 0 && (
                      <div>
                        <p className="text-xs text-red-600 font-medium mb-0.5">Weaknesses</p>
                        {comp.weaknesses.map((w, j) => (
                          <p key={j} className="text-xs text-slate-500">• {w}</p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Differentiators */}
        {result.key_differentiators && result.key_differentiators.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-400 uppercase font-medium">Our Differentiators</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {result.key_differentiators.map((d, i) => (
                <span key={i} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                  {d}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Threats */}
        {result.threats && result.threats.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
              <span className="text-xs text-amber-500 uppercase font-medium">Threats</span>
            </div>
            <ul className="space-y-1">
              {result.threats.map((t, i) => (
                <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                  <AlertTriangle className="h-3 w-3 text-amber-400 mt-1 flex-shrink-0" />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Win Themes */}
        {result.win_themes && result.win_themes.length > 0 && (
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
            <div className="flex items-center gap-1.5 mb-2">
              <Target className="h-3.5 w-3.5 text-blue-600" />
              <span className="text-xs text-blue-600 uppercase font-medium">Win Themes</span>
            </div>
            {result.win_themes.map((theme, i) => (
              <p key={i} className="text-sm text-blue-800 flex items-start gap-2">
                <ArrowRight className="h-3 w-3 mt-1 text-blue-400 flex-shrink-0" />
                <span>{theme}</span>
              </p>
            ))}
          </div>
        )}

        {/* Recommendation */}
        {result.recommendation && (
          <div className="p-3 bg-green-50 rounded-lg border border-green-100">
            <p className="text-xs text-green-600 uppercase font-medium mb-1">Strategy Recommendation</p>
            <p className="text-sm text-green-800">{result.recommendation}</p>
          </div>
        )}
      </div>
    </div>
  );
}
