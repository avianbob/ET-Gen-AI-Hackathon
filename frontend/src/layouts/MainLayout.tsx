import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import Sidebar from '../components/layout/Sidebar';
import Header from '../components/layout/Header';
import MobileNav from '../components/layout/MobileNav';
import CommandPalette from '../components/common/CommandPalette';
import ShortcutsModal from '../components/common/ShortcutsModal';
import { ToastContainer } from '../components/common/NotificationCenter';
import OnboardingTour from '../components/common/OnboardingTour';
import { ROUTES } from '../utils/constants';

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const location = useLocation();
  const mainRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (mainRef.current) mainRef.current.scrollTo(0, 0);
  }, [location.pathname]);

  const handleGlobalKeyDown = useCallback((e: KeyboardEvent) => {
    const tag = (e.target as HTMLElement).tagName.toLowerCase();
    const isInput = tag === 'input' || tag === 'textarea' || (e.target as HTMLElement).isContentEditable;

    if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); setCommandPaletteOpen((prev) => !prev); return; }
    if ((e.ctrlKey || e.metaKey) && e.key === '/') { e.preventDefault(); navigate(ROUTES.CHAT); return; }
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'N') { e.preventDefault(); navigate(ROUTES.SEARCH); return; }
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') { e.preventDefault(); navigate(ROUTES.DASHBOARD); return; }
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'H') { e.preventDefault(); navigate(ROUTES.HISTORY); return; }
    if (!isInput && e.key === '?' && !e.ctrlKey && !e.metaKey) { e.preventDefault(); setShortcutsOpen((prev) => !prev); return; }
    if (e.key === 'Escape') { setCommandPaletteOpen(false); setShortcutsOpen(false); }
  }, [navigate]);

  useEffect(() => {
    document.addEventListener('keydown', handleGlobalKeyDown);
    return () => document.removeEventListener('keydown', handleGlobalKeyDown);
  }, [handleGlobalKeyDown]);

  return (
    <div className="flex h-screen bg-gradient-to-b from-slate-100/90 via-slate-50 to-slate-100/80 text-slate-800 overflow-hidden">
      <div className="hidden lg:block"><Sidebar /></div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setMobileMenuOpen(false)} className="lg:hidden fixed inset-0 bg-slate-900/25 z-40" />
            <motion.div initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }} transition={{ type: 'spring', bounce: 0, duration: 0.3 }} className="lg:hidden fixed left-0 top-0 bottom-0 z-50">
              <div className="relative">
                <Sidebar />
                <button onClick={() => setMobileMenuOpen(false)} className="absolute top-4 right-4 p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onMenuClick={() => setMobileMenuOpen(true)} />
        <main ref={mainRef} className="flex-1 overflow-auto pb-20 lg:pb-0 min-h-0">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }} className="p-4 lg:p-6 min-h-full">
            <Outlet />
          </motion.div>
        </main>
        <MobileNav />
      </div>

      <CommandPalette isOpen={commandPaletteOpen} onClose={() => setCommandPaletteOpen(false)} />
      <ShortcutsModal isOpen={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
      <ToastContainer />
      <OnboardingTour />
    </div>
  );
};

export default MainLayout;
