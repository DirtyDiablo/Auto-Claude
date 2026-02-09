import { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, Send, Loader2, Trash2, PanelRightClose } from 'lucide-react';
import { ChatMessage, type Message } from './chat/ChatMessage';
import { QuickActions } from './chat/QuickActions';
import type { EntityCard } from './chat/EntityChip';
import type { CopilotContext } from '../hooks/useCopilotContext';

const API_BASE = import.meta.env.VITE_API_BASE || '';

interface CopilotSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  context: CopilotContext;
  onNavigateToContact: (name: string) => void;
  onNavigateToProgram: (name: string) => void;
  onNavigateToJobs: () => void;
}

const WELCOME: Message = {
  role: 'assistant',
  content: 'Hi! I can help you explore contacts, programs, and jobs across the BD database. Ask me anything or try a quick action below.',
  timestamp: new Date(),
};

export function CopilotSidebar({
  isOpen,
  onToggle,
  context,
  onNavigateToContact,
  onNavigateToProgram,
  onNavigateToJobs,
}: CopilotSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-scroll on new content
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when sidebar opens
  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 200);
  }, [isOpen]);

  const handleEntityNavigate = useCallback(
    (type: EntityCard['type'], _id: string, name: string) => {
      if (type === 'contact') onNavigateToContact(name);
      else if (type === 'program') onNavigateToProgram(name);
      else onNavigateToJobs();
    },
    [onNavigateToContact, onNavigateToProgram, onNavigateToJobs],
  );

  const resolveEntities = useCallback(async (text: string): Promise<EntityCard[]> => {
    // Extract proper nouns (capitalized multi-word phrases) and search for matches
    const phrases = text.match(/[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+/g) || [];
    const unique = [...new Set(phrases)].slice(0, 3);
    if (unique.length === 0) return [];

    try {
      const results: EntityCard[] = [];
      for (const phrase of unique) {
        const res = await fetch(`${API_BASE}/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: phrase, limit: 1 }),
        });
        if (!res.ok) continue;
        const data = await res.json();
        const hit = data.results?.[0];
        if (!hit || hit.score < 0.55) continue;

        const collection = hit.collection || '';
        if (collection === 'contacts') {
          const name = hit.payload?.['﻿Contact Name'] || hit.payload?.name || phrase;
          results.push({
            type: 'contact',
            name,
            id: hit.id,
            meta: { tier: `Tier ${hit.payload?.tier || '?'}`, program: hit.payload?.program || '' },
          });
        } else if (collection === 'programs') {
          const name = hit.payload?.['Program Name'] || hit.payload?.name || phrase;
          results.push({
            type: 'program',
            name,
            id: hit.id,
            meta: { prime: hit.payload?.['Prime Contractor'] || '', value: hit.payload?.['Contract Value'] || '' },
          });
        } else if (collection === 'jobs') {
          results.push({
            type: 'job',
            name: hit.payload?.title || phrase,
            id: hit.id,
            meta: { company: hit.payload?.company || '', location: hit.payload?.location || '' },
          });
        }
      }
      return results;
    } catch {
      return [];
    }
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      const userMsg: Message = { role: 'user', content: trimmed, timestamp: new Date() };
      const assistantMsg: Message = { role: 'assistant', content: '', timestamp: new Date() };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setInput('');
      setIsStreaming(true);

      // Build history for API (last 10 messages)
      const history = [...messages, userMsg]
        .filter((m) => m !== WELCOME)
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));

      const abortController = new AbortController();
      abortRef.current = abortController;

      try {
        const res = await fetch(`${API_BASE}/ai/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: trimmed,
            history,
            context: context.contextPrompt,
          }),
          signal: abortController.signal,
        });

        if (!res.ok) {
          const errText = await res.text().catch(() => 'Unknown error');
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: `Sorry, I got an error: ${res.status} — ${errText.slice(0, 200)}`,
            };
            return updated;
          });
          setIsStreaming(false);
          return;
        }

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';

        if (reader) {
          let buffer = '';
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              const payload = line.slice(6).trim();
              if (payload === '[DONE]') continue;
              try {
                const parsed = JSON.parse(payload);
                if (parsed.content) {
                  fullContent += parsed.content;
                  setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                      ...updated[updated.length - 1],
                      content: fullContent,
                    };
                    return updated;
                  });
                }
              } catch {
                // skip malformed SSE frames
              }
            }
          }
        }

        // Resolve entity chips after full response
        if (fullContent) {
          const entities = await resolveEntities(fullContent);
          if (entities.length > 0) {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = { ...updated[updated.length - 1], entities };
              return updated;
            });
          }
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          // User cancelled — leave partial content
        } else {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (!last.content) {
              updated[updated.length - 1] = {
                ...last,
                content: 'Sorry, something went wrong. Please check that the Hub API is running.',
              };
            }
            return updated;
          });
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [isStreaming, messages, context.contextPrompt, resolveEntities],
  );

  const handleSubmit = useCallback(() => {
    sendMessage(input);
  }, [input, sendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  const handleQuickAction = useCallback(
    (query: string) => {
      sendMessage(query);
    },
    [sendMessage],
  );

  const handleClear = useCallback(() => {
    if (isStreaming) abortRef.current?.abort();
    setMessages([WELCOME]);
    setIsStreaming(false);
  }, [isStreaming]);

  return (
    <div
      className={`fixed top-0 right-0 h-full z-40 transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        w-full sm:w-80 flex flex-col
        bg-slate-50 dark:bg-slate-900 border-l border-slate-200 dark:border-slate-700 shadow-xl`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Bot className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">BD Copilot</h3>
            <p className="text-[10px] text-slate-500">{context.contextLabel ? `Context: ${context.contextLabel}` : 'General intelligence'}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={handleClear} className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 dark:hover:text-slate-300 transition-colors" title="Clear chat">
            <Trash2 className="h-3.5 w-3.5" />
          </button>
          <button onClick={onToggle} className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 dark:hover:text-slate-300 transition-colors" title="Close (Ctrl+/)">
            <PanelRightClose className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} onEntityNavigate={handleEntityNavigate} />
        ))}
        {isStreaming && messages[messages.length - 1]?.content === '' && (
          <div className="flex items-center gap-2 text-xs text-slate-500 pl-9">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <QuickActions contextLabel={context.contextLabel} onAction={handleQuickAction} />

      {/* Input */}
      <div className="border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2.5">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about contacts, programs, jobs..."
            rows={1}
            className="flex-1 resize-none rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900
              text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400
              px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              max-h-24 overflow-y-auto"
            onInput={(e) => {
              const t = e.target as HTMLTextAreaElement;
              t.style.height = 'auto';
              t.style.height = Math.min(t.scrollHeight, 96) + 'px';
            }}
            disabled={isStreaming}
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isStreaming}
            className="shrink-0 p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700
              disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
        <p className="text-[10px] text-slate-400 mt-1.5 text-center">
          Enter to send · Shift+Enter for new line · Ctrl+/ to toggle
        </p>
      </div>
    </div>
  );
}
