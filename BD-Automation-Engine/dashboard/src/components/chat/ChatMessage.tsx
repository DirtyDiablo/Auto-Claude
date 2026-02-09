import { Bot, User } from 'lucide-react';
import { EntityChip, type EntityCard } from './EntityChip';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  entities?: EntityCard[];
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
  onEntityNavigate: (type: EntityCard['type'], id: string, name: string) => void;
}

export function ChatMessage({ message, onEntityNavigate }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-0.5
        ${isUser ? 'bg-blue-600 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300'}`}>
        {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>
      <div className={`flex-1 min-w-0 ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block text-sm leading-relaxed rounded-xl px-3.5 py-2.5 max-w-[90%] text-left
          ${isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-bl-sm'
          }`}>
          <MessageContent content={message.content} />
        </div>
        {message.entities && message.entities.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {message.entities.map((entity, i) => (
              <EntityChip key={`${entity.type}-${entity.id}-${i}`} entity={entity} onNavigate={onEntityNavigate} />
            ))}
          </div>
        )}
        <p className={`text-[10px] text-slate-400 mt-1 ${isUser ? 'text-right' : ''}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}

function MessageContent({ content }: { content: string }) {
  // Simple markdown-ish rendering: bold, line breaks
  const parts = content.split(/(\*\*[^*]+\*\*|\n)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part === '\n') return <br key={i} />;
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}
