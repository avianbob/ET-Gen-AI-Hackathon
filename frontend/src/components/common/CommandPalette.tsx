import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, MessageSquare, LayoutDashboard, Clock, Bookmark, GitCompareArrows, Settings, Plug, GitBranch } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../../utils/constants';

const commands = [
  { id: 'chat', label: 'AI Assistant', icon: MessageSquare, path: ROUTES.CHAT, group: 'Navigate' },
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: ROUTES.DASHBOARD, group: 'Navigate' },
  { id: 'search', label: 'Drug Search', icon: Search, path: ROUTES.SEARCH, group: 'Navigate' },
  { id: 'history', label: 'History', icon: Clock, path: ROUTES.HISTORY, group: 'Navigate' },
  { id: 'saved', label: 'Saved Opportunities', icon: Bookmark, path: ROUTES.SAVED, group: 'Navigate' },
  { id: 'compare', label: 'Drug Comparison', icon: GitCompareArrows, path: ROUTES.COMPARE, group: 'Navigate' },
  { id: 'architecture', label: 'Architecture', icon: GitBranch, path: ROUTES.ARCHITECTURE, group: 'Navigate' },
  { id: 'integrations', label: 'Integrations', icon: Plug, path: ROUTES.INTEGRATIONS, group: 'Navigate' },
  { id: 'settings', label: 'Settings', icon: Settings, path: ROUTES.SETTINGS, group: 'Navigate' },
];

interface CommandPaletteProps { isOpen: boolean; onClose: () => void; }

const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    if (isOpen) { setQuery(''); setSelectedIndex(0); setTimeout(() => inputRef.current?.focus(), 100); }
  }, [isOpen]);

  const handleSelect = (cmd: typeof commands[0]) => {
    navigate(cmd.path);
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIndex((i) => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && filtered[selectedIndex]) handleSelect(filtered[selectedIndex]);
    if (e.key === 'Escape') onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} className="fixed inset-0 bg-slate-900/30 backdrop-blur-sm z-50" />
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className="fixed left-1/2 top-[20%] -translate-x-1/2 w-full max-w-lg bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-300/50 z-50 overflow-hidden"
          >
            <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-100">
              <Search className="w-5 h-5 text-slate-400" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
                onKeyDown={handleKeyDown}
                placeholder="Type a command or search..."
                className="flex-1 bg-transparent text-slate-900 placeholder-slate-400 focus:outline-none text-sm"
              />
              <kbd className="px-2 py-0.5 text-[10px] text-slate-500 bg-slate-100 border border-slate-200 rounded">ESC</kbd>
            </div>
            <div className="max-h-80 overflow-y-auto p-2">
              {filtered.length === 0 ? (
                <p className="text-center text-sm text-slate-500 py-8">No results found</p>
              ) : (
                filtered.map((cmd, i) => {
                  const Icon = cmd.icon;
                  return (
                    <button
                      key={cmd.id}
                      onClick={() => handleSelect(cmd)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors ${
                        i === selectedIndex ? 'bg-cyan-50 text-cyan-800 border border-cyan-100' : 'text-slate-700 hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="flex-1 text-left">{cmd.label}</span>
                      <span className="text-[10px] text-slate-400">{cmd.group}</span>
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default CommandPalette;
