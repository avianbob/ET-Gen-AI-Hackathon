import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Settings, LogOut, Menu, Command } from 'lucide-react';
import { ROUTES } from '../../utils/constants';
import SearchInput from '../common/SearchInput';
import NotificationCenter from '../common/NotificationCenter';
import Breadcrumbs from './Breadcrumbs';
import useAppStore from '../../store';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/search': 'Drug Search',
  '/results': 'Analysis Results',
  '/history': 'History',
  '/saved': 'Saved Opportunities',
  '/integrations': 'Integrations',
  '/settings': 'Settings',
  '/chat': 'AI Assistant',
  '/compare': 'Drug Comparison',
  '/architecture': 'Architecture',
};

interface HeaderProps { onMenuClick: () => void; }

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [quickSearch, setQuickSearch] = useState('');
  const { user } = useAppStore();

  const currentPath = location.pathname.startsWith('/results') ? '/results' : location.pathname;
  const pageTitle = pageTitles[currentPath] || 'PharmAI';

  const handleQuickSearch = (value: string) => {
    if (value.trim()) { navigate(`${ROUTES.SEARCH}?drug=${encodeURIComponent(value.trim())}`); setQuickSearch(''); }
  };

  return (
    <header className="h-14 bg-white/85 backdrop-blur-md border-b border-slate-200/90 px-6 flex items-center justify-between sticky top-0 z-40 shadow-sm shadow-slate-200/40">
      <div className="flex items-center gap-4">
        <button onClick={onMenuClick} className="lg:hidden p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors">
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex flex-col">
          <Breadcrumbs />
          <h1 className="text-sm font-semibold text-slate-900 leading-tight">{pageTitle}</h1>
        </div>
      </div>

      <div className="hidden md:flex flex-1 max-w-sm mx-8">
        <SearchInput value={quickSearch} onChange={(e) => setQuickSearch(e.target.value)} onSubmit={handleQuickSearch} placeholder="Quick search... (Ctrl+K)" size="sm" />
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }))}
          className="hidden lg:flex items-center gap-1 px-2 py-1 text-[10px] text-slate-500 bg-slate-100 border border-slate-200 rounded-lg hover:border-cyan-400/40 transition-colors"
        >
          <Command className="w-3 h-3" /> K
        </button>

        <NotificationCenter />

        <div className="relative">
          <button onClick={() => setShowUserMenu(!showUserMenu)} className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-100 transition-colors">
            <div className="w-7 h-7 bg-gradient-to-br from-cyan-500 to-teal-600 rounded-full flex items-center justify-center shadow-sm shadow-cyan-500/25">
              <User className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="hidden sm:block text-xs font-medium text-slate-700">{user?.username || 'User'}</span>
          </button>

          <AnimatePresence>
            {showUserMenu && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }} className="absolute right-0 mt-2 w-52 bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/50 z-50 overflow-hidden">
                  <div className="p-3 border-b border-slate-100">
                    <p className="font-medium text-sm text-slate-900">{user?.full_name || 'Guest User'}</p>
                    <p className="text-xs text-slate-500">{user?.email || 'Sign in for full access'}</p>
                  </div>
                  <div className="p-1.5">
                    <button onClick={() => { navigate(ROUTES.SETTINGS); setShowUserMenu(false); }} className="w-full flex items-center gap-3 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors">
                      <Settings className="w-4 h-4" /> Settings
                    </button>
                    <button onClick={() => setShowUserMenu(false)} className="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                      <LogOut className="w-4 h-4" /> Sign out
                    </button>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
};

export default Header;
