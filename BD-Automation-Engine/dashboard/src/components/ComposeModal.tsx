/**
 * ComposeModal — Outreach message compose/preview/send modal
 *
 * Opened from OutreachManager timeline view to compose a message
 * for the current outreach step. Supports edit/preview modes,
 * channel selection, clipboard copy, and mark-as-sent.
 */

import { useState, useCallback } from 'react';
import {
  X, Eye, Edit3, Copy, CheckCircle2, Mail, Phone, Linkedin, Send,
} from 'lucide-react';

// ─── Types (shared with OutreachManager) ─────────────────────────────────────

interface OutreachStep {
  step_number: number;
  type: 'email' | 'call' | 'linkedin' | 'case_study' | 'breakup';
  label: string;
  day: number;
  status: 'pending' | 'sent' | 'completed' | 'skipped' | 'bounced';
  sent_at?: string;
  content?: string;
}

interface OutreachSequence {
  id: string;
  contact_name: string;
  contact_email?: string;
  contact_phone?: string;
  program: string;
  tier: number;
  status: string;
  current_step: number;
  steps: OutreachStep[];
  created_at: string;
}

interface ComposeModalProps {
  sequence: OutreachSequence;
  stepIndex: number;
  onClose: () => void;
  onSent: (seqId: string) => void;
  generatedContent?: string;
}

// ─── Channel Config ──────────────────────────────────────────────────────────

type Channel = 'email' | 'linkedin' | 'phone';

const CHANNEL_CONFIG: Record<Channel, { icon: typeof Mail; label: string; color: string }> = {
  email: { icon: Mail, label: 'Email', color: 'text-blue-600' },
  linkedin: { icon: Linkedin, label: 'LinkedIn', color: 'text-[#0077b5]' },
  phone: { icon: Phone, label: 'Phone', color: 'text-green-600' },
};

// Map step type to default channel
function defaultChannel(stepType: string): Channel {
  if (stepType === 'linkedin') return 'linkedin';
  if (stepType === 'call') return 'phone';
  return 'email';
}

// ─── Template Generator ──────────────────────────────────────────────────────

function generateTemplate(seq: OutreachSequence, step: OutreachStep): { subject: string; body: string } {
  const firstName = seq.contact_name.split(' ').pop() || seq.contact_name;

  const templates: Record<string, { subject: string; body: string }> = {
    email: {
      subject: `${seq.program} — Partnership Opportunity`,
      body: `Hi ${firstName},\n\nI noticed ${seq.program} is a priority area for your team. We have deep experience supporting DCGS portfolio programs and would love to explore how we might complement your capabilities.\n\nWould you be open to a brief call this week to discuss potential collaboration?\n\nBest regards,\n[Your Name]`,
    },
    call: {
      subject: `Call: ${seq.contact_name} — ${seq.program}`,
      body: `Call Script for ${seq.contact_name}:\n\n1. Introduction & rapport building\n2. Reference previous email about ${seq.program}\n3. Ask about current staffing needs and timeline\n4. Share relevant past performance / case studies\n5. Propose next steps (technical deep-dive / meeting)\n\nKey talking points:\n- DCGS portfolio expertise\n- Cleared talent pipeline\n- Quick ramp capability`,
    },
    linkedin: {
      subject: `LinkedIn: ${seq.contact_name}`,
      body: `Hi ${firstName},\n\nI came across your work on ${seq.program} and was impressed by the program's trajectory. We specialize in supporting DCGS-family programs with cleared technical talent.\n\nI'd welcome the chance to connect and share some ideas that might be relevant to your team's mission.\n\nLooking forward to connecting!`,
    },
    case_study: {
      subject: `${seq.program} — Relevant Case Study`,
      body: `Hi ${firstName},\n\nFollowing up on our earlier conversation — I wanted to share a case study that's directly relevant to ${seq.program}.\n\n[Attach: DCGS Support Case Study]\n\nKey results:\n• 40% faster onboarding for cleared analysts\n• 98% retention rate across 12-month engagement\n• Full TS/SCI pipeline maintained throughout\n\nWould any of these outcomes be valuable for your current needs?\n\nBest,\n[Your Name]`,
    },
    breakup: {
      subject: `Final note — ${seq.program}`,
      body: `Hi ${firstName},\n\nI've reached out a few times about potential support for ${seq.program} and understand you may have other priorities right now.\n\nIf the timing isn't right, no worries at all. I'll keep your contact information on file and reach out if we see relevant opportunities.\n\nWishing you continued success with the program.\n\nBest regards,\n[Your Name]`,
    },
  };

  return templates[step.type] || templates.email;
}

// ─── Component ───────────────────────────────────────────────────────────────

export function ComposeModal({ sequence, stepIndex, onClose, onSent, generatedContent }: ComposeModalProps) {
  const step = sequence.steps[stepIndex];
  const template = generateTemplate(sequence, step);

  const [mode, setMode] = useState<'edit' | 'preview'>('edit');
  const [channel, setChannel] = useState<Channel>(defaultChannel(step.type));
  const [subject, setSubject] = useState(template.subject);
  const [body, setBody] = useState(generatedContent || template.body);
  const [copied, setCopied] = useState(false);
  const [sent, setSent] = useState(false);

  const handleCopy = useCallback(async () => {
    const text = channel === 'phone'
      ? body
      : `Subject: ${subject}\n\n${body}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [channel, subject, body]);

  const handleSend = useCallback(() => {
    setSent(true);
    setTimeout(() => {
      onSent(sequence.id);
      onClose();
    }, 800);
  }, [sequence.id, onSent, onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Compose: {step.label}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {sequence.contact_name} &middot; {sequence.program} &middot; Tier {sequence.tier}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Mode toggle */}
            <div className="flex bg-slate-100 dark:bg-slate-700 rounded-lg p-0.5">
              <button onClick={() => setMode('edit')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${mode === 'edit' ? 'bg-white dark:bg-slate-600 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500'}`}>
                <Edit3 className="h-3 w-3" /> Edit
              </button>
              <button onClick={() => setMode('preview')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${mode === 'preview' ? 'bg-white dark:bg-slate-600 shadow text-slate-800 dark:text-slate-100' : 'text-slate-500'}`}>
                <Eye className="h-3 w-3" /> Preview
              </button>
            </div>
            <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {/* Channel selector */}
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1.5 block">Channel</label>
            <div className="flex gap-2">
              {(Object.entries(CHANNEL_CONFIG) as [Channel, typeof CHANNEL_CONFIG.email][]).map(([ch, cfg]) => {
                const Icon = cfg.icon;
                return (
                  <button key={ch} onClick={() => setChannel(ch)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      channel === ch
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300'
                        : 'bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:bg-slate-100'
                    }`}>
                    <Icon className="h-3.5 w-3.5" /> {cfg.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* To field */}
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">To</label>
            <div className="px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-sm text-slate-700 dark:text-slate-300">
              {sequence.contact_name}
              {channel === 'email' && sequence.contact_email && (
                <span className="text-slate-400 ml-2">&lt;{sequence.contact_email}&gt;</span>
              )}
              {channel === 'phone' && sequence.contact_phone && (
                <span className="text-slate-400 ml-2">{sequence.contact_phone}</span>
              )}
            </div>
          </div>

          {/* Subject (not for phone) */}
          {channel !== 'phone' && (
            <div>
              <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">Subject</label>
              {mode === 'edit' ? (
                <input value={subject} onChange={e => setSubject(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm text-slate-900 dark:text-slate-100" />
              ) : (
                <div className="px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-sm font-medium text-slate-800 dark:text-slate-200">
                  {subject}
                </div>
              )}
            </div>
          )}

          {/* Body */}
          <div>
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-1 block">
              {channel === 'phone' ? 'Call Script' : 'Message'}
            </label>
            {mode === 'edit' ? (
              <textarea value={body} onChange={e => setBody(e.target.value)} rows={12}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm text-slate-900 dark:text-slate-100 font-mono resize-y" />
            ) : (
              <div className="px-4 py-3 rounded-lg bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap min-h-[200px]">
                {body}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={handleCopy}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              copied
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
            }`}>
            {copied ? <CheckCircle2 className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? 'Copied!' : 'Copy to Clipboard'}
          </button>
          <div className="flex gap-2">
            <button onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600">
              Cancel
            </button>
            <button onClick={handleSend} disabled={sent}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                sent
                  ? 'bg-green-600 text-white'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              } disabled:opacity-70`}>
              {sent ? <CheckCircle2 className="h-4 w-4" /> : <Send className="h-4 w-4" />}
              {sent ? 'Sent!' : 'Mark as Sent'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
