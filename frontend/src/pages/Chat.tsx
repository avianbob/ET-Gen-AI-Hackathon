import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send, Plus, MessageSquare, Trash2, Loader2, Upload,
  PanelLeftClose, PanelLeftOpen,
} from 'lucide-react';
import MessageBubble from '../components/chat/MessageBubble';
import ChatProgress from '../components/chat/ChatProgress';
import SuggestedQueries from '../components/chat/SuggestedQueries';
import FileUploadZone from '../components/chat/FileUploadZone';
import {
  sendChatMessage, getConversations, getConversation,
  deleteConversation, uploadFile,
} from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { generateSessionId } from '../utils/helpers';
import { formatTimeAgo } from '../utils/formatters';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  suggestions?: string[];
}

interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(() => generateSessionId());
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [loadingConversations, setLoadingConversations] = useState(false);

  /** Stable WebSocket session for backend agent progress (same pattern as /search). */
  const [wsSessionId] = useState(() => generateSessionId());
  const { agentProgress, workflowStatus, resetProgress } = useWebSocket(wsSessionId, { autoConnect: true });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setLoadingConversations(true);
    try {
      const data = await getConversations(30);
      const raw = Array.isArray(data) ? data : data.conversations ?? [];
      setConversations(
        raw.map((c: any) => ({
          id: c.id ?? c.conversation_id ?? '',
          title: (c.title ?? c.preview ?? 'Untitled').slice(0, 120),
          updated_at: c.updated_at ?? c.created_at ?? new Date().toISOString(),
          message_count: c.message_count ?? 0,
        }))
      );
    } catch {
      /* silently fail — sidebar will just be empty */
    } finally {
      setLoadingConversations(false);
    }
  };

  const handleLoadConversation = async (id: string) => {
    try {
      const data = await getConversation(id);
      const history: Message[] = (data.messages ?? data.history ?? []).map(
        (m: any) => ({ role: m.role, content: m.content, suggestions: m.suggestions })
      );
      setMessages(history);
      setConversationId(id);
    } catch {
      /* ignore */
    }
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (id === conversationId) handleNewChat();
    } catch {
      /* ignore */
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(generateSessionId());
    setInput('');
    setShowUpload(false);
    setUploadedFiles([]);
    textareaRef.current?.focus();
  };

  const handleSend = async (overrideMessage?: string) => {
    const text = (overrideMessage ?? input).trim();
    if (!text || isLoading) return;

    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    resetProgress();

    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    try {
      if (uploadedFiles.length > 0) {
        await Promise.all(uploadedFiles.map((f) => uploadFile(f)));
        setUploadedFiles([]);
        setShowUpload(false);
      }

      const history = [...messages, userMsg].map(({ role, content }) => ({ role, content }));
      const data = await sendChatMessage(text, conversationId, history, wsSessionId);

      if (data.conversation_id) setConversationId(data.conversation_id);

      const inner = data.message;
      const replyText =
        typeof inner === 'string'
          ? inner
          : inner?.content ?? data.response ?? data.content ?? 'No response received.';
      const replySuggestions =
        typeof inner === 'object' && inner?.suggestions ? inner.suggestions : data.suggestions;

      const assistantMsg: Message = {
        role: 'assistant',
        content: replyText,
        suggestions: replySuggestions,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      loadConversations();
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Sorry, something went wrong: ${err.message || 'Unknown error'}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  const handleFileUpload = (files: File[]) => {
    setUploadedFiles((prev) => [...prev, ...files].slice(0, 5));
  };

  const handleFileRemove = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem-2rem)] lg:h-[calc(100vh-3.5rem-3rem)] -m-4 lg:-m-6 rounded-xl overflow-hidden border border-slate-200/90 bg-white/80 shadow-sm shadow-slate-200/50">
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col border-r border-slate-200 bg-slate-50/90 overflow-hidden"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
              <span className="text-sm font-medium text-slate-700">Conversations</span>
              <button
                type="button"
                onClick={handleNewChat}
                className="p-1.5 rounded-lg text-slate-500 hover:text-cyan-700 hover:bg-white border border-transparent hover:border-slate-200 transition-colors"
                title="New Chat"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-2 space-y-0.5 px-2 scrollbar-thin">
              {loadingConversations ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
                </div>
              ) : conversations.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-8">No conversations yet</p>
              ) : (
                conversations.map((c) => (
                  <div
                    key={c.id}
                    className={`group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-colors ${
                      c.id === conversationId
                        ? 'bg-white border border-cyan-200 text-slate-900 shadow-sm'
                        : 'text-slate-600 hover:bg-white/80 hover:text-slate-900 border border-transparent'
                    }`}
                    onClick={() => handleLoadConversation(c.id)}
                    onKeyDown={(e) => e.key === 'Enter' && handleLoadConversation(c.id)}
                    role="button"
                    tabIndex={0}
                  >
                    <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-cyan-600" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">{c.title || 'Untitled'}</p>
                      <p className="text-[10px] text-slate-400">{formatTimeAgo(c.updated_at)}</p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleDeleteConversation(c.id); }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-600 transition-all"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col min-w-0 bg-gradient-to-b from-white to-slate-50/80">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-200 bg-white/90">
          <button
            type="button"
            onClick={() => setSidebarOpen((prev) => !prev)}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            {sidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
          </button>
          <h1 className="text-sm font-semibold text-slate-800">AI Assistant</h1>
          {messages.length > 0 && (
            <button
              type="button"
              onClick={handleNewChat}
              className="ml-auto text-xs text-slate-500 hover:text-cyan-700 transition-colors flex items-center gap-1"
            >
              <Plus className="w-3.5 h-3.5" />
              New Chat
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin">
          {messages.length === 0 && !isLoading ? (
            <div className="max-w-2xl mx-auto mt-12">
              <SuggestedQueries onSelect={(q) => handleSend(q)} />
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              <AnimatePresence initial={false}>
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25 }}
                  >
                    <MessageBubble
                      message={msg}
                      onSuggestionClick={(s) => handleSend(s)}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>

              {isLoading && (
                <ChatProgress
                  agentProgress={agentProgress}
                  workflowStatus={workflowStatus ?? { message: 'Thinking...' }}
                />
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="border-t border-slate-200 px-4 py-3 bg-white/95">
          <div className="max-w-3xl mx-auto space-y-2">
            <AnimatePresence>
              {showUpload && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <FileUploadZone
                    onUpload={handleFileUpload}
                    files={uploadedFiles}
                    onRemove={handleFileRemove}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex items-end gap-2">
              <button
                type="button"
                onClick={() => setShowUpload((prev) => !prev)}
                className={`p-2.5 rounded-xl transition-colors flex-shrink-0 ${
                  showUpload
                    ? 'bg-cyan-50 text-cyan-700 border border-cyan-200'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100 border border-transparent'
                }`}
                title="Attach files"
              >
                <Upload className="w-4 h-4" />
              </button>

              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleTextareaChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about drug repurposing, market analysis, clinical trials..."
                  rows={1}
                  className="w-full resize-none bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 pr-12 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/15 transition-all"
                />
                <button
                  type="button"
                  onClick={() => handleSend()}
                  disabled={!input.trim() || isLoading}
                  className="absolute right-2 bottom-2 p-2 rounded-lg bg-gradient-to-r from-cyan-600 to-teal-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:from-cyan-500 hover:to-teal-500 shadow-md shadow-cyan-500/20 transition-colors"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            <p className="text-[10px] text-slate-400 text-center">
              PharmAI may produce inaccurate information. Verify critical findings independently.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
