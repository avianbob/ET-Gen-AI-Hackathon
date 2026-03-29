import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Copy, Check } from 'lucide-react';
import { cn } from '../../utils/helpers';
import { copyToClipboard } from '../../utils/helpers';

interface MessageBubbleProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    tables?: any[];
    charts?: any[];
    suggestions?: string[];
    timestamp?: string;
  };
  onSuggestionClick?: (suggestion: string) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onSuggestionClick }) => {
  const [copied, setCopied] = React.useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    await copyToClipboard(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn('flex gap-3 group', isUser ? 'flex-row-reverse' : '')}>
      <div className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        isUser ? 'bg-gradient-to-br from-cyan-500 to-teal-600 shadow-sm shadow-cyan-500/20' : 'bg-slate-100 border border-slate-200'
      )}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-cyan-600" />}
      </div>

      <div className={cn('max-w-[80%] space-y-2', isUser ? 'items-end' : '')}>
        <div className={cn(
          'px-4 py-3 rounded-2xl text-sm',
          isUser
            ? 'bg-gradient-to-r from-cyan-600 to-teal-600 text-white rounded-tr-sm shadow-md shadow-cyan-500/20'
            : 'bg-white text-slate-800 rounded-tl-sm border border-slate-200 shadow-sm'
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-slate prose-sm max-w-none prose-p:my-1 prose-li:my-0 prose-headings:mt-3 prose-headings:mb-1 prose-a:text-cyan-600">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && (
          <button onClick={handleCopy} className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-slate-600 transition-all">
            {copied ? <Check className="w-3.5 h-3.5 text-teal-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        )}

        {message.suggestions && message.suggestions.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {message.suggestions.map((s: string, i: number) => (
              <button
                key={i}
                onClick={() => onSuggestionClick?.(s)}
                className="px-3 py-1.5 text-xs bg-white text-slate-700 border border-slate-200 rounded-full hover:border-cyan-300 hover:text-cyan-800 shadow-sm transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
