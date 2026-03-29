import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Search, Clock, Bookmark, TrendingUp, GitCompareArrows,
  Plug, Settings, ChevronLeft, ChevronRight, Dna, MessageSquare, GitBranch, FlaskConical,
} from 'lucide-react';
import { cn } from '../../utils/helpers';
import { NAV_ITEMS, ROUTES } from '../../utils/constants';
import Badge from '../common/Badge';
import Tooltip from '../common/Tooltip';
import useAppStore from '../../store';

const icons: Record<string, any> = {
  LayoutDashboard, Search, Clock, Bookmark, TrendingUp, GitCompareArrows,
  Plug, Settings, MessageSquare, GitBranch, FlaskConical,
};

const Sidebar: React.FC = () => {
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar, savedOpportunities } = useAppStore();

  const navSections = [
    { title: 'MAIN', items: NAV_ITEMS.main },
    { title: 'INTELLIGENCE', items: NAV_ITEMS.intelligence },
    { title: 'CONFIGURATION', items: NAV_ITEMS.configuration },
  ];

  const isActive = (path: string) => {
    if (path === ROUTES.RESULTS) return location.pathname.startsWith('/results');
    return location.pathname === path;
  };

  const NavItem = ({ item }: { item: any }) => {
    const Icon = icons[item.icon] || LayoutDashboard;
    const active = isActive(item.path);
    const savedCount = item.path === ROUTES.SAVED ? savedOpportunities?.length : null;

    const content = (
      <NavLink
        to={item.path}
        className={cn(
          'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 relative group',
          active
            ? 'bg-cyan-50 text-slate-900 border border-cyan-200/80 shadow-sm shadow-cyan-500/10'
            : 'text-slate-600 hover:text-slate-900 hover:bg-white/80 border border-transparent'
        )}
      >
        {active && (
          <motion.div layoutId="sidebar-indicator" className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-7 bg-gradient-to-b from-cyan-500 to-teal-600 rounded-r" transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }} />
        )}
        <Icon className={cn('w-5 h-5 flex-shrink-0', active && 'text-cyan-600')} />
        <AnimatePresence>
          {!sidebarCollapsed && (
            <motion.span initial={{ opacity: 0, width: 0 }} animate={{ opacity: 1, width: 'auto' }} exit={{ opacity: 0, width: 0 }} transition={{ duration: 0.2 }} className="font-medium whitespace-nowrap overflow-hidden">
              {item.label}
            </motion.span>
          )}
        </AnimatePresence>
        {!sidebarCollapsed && item.badge && <Badge variant={item.badge === 'NEW' ? 'teal' : 'yellow'} size="sm" className="ml-auto">{item.badge}</Badge>}
        {!sidebarCollapsed && savedCount > 0 && <Badge variant="teal" size="sm" className="ml-auto">{savedCount}</Badge>}
      </NavLink>
    );

    return sidebarCollapsed ? <Tooltip content={item.label} position="right">{content}</Tooltip> : content;
  };

  return (
    <motion.aside initial={false} animate={{ width: sidebarCollapsed ? 72 : 280 }} transition={{ duration: 0.2, ease: 'easeInOut' }} className="h-screen bg-white/90 backdrop-blur-md border-r border-slate-200/90 flex flex-col flex-shrink-0 shadow-sm shadow-slate-200/30">
      <div className="p-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md shadow-cyan-500/25">
            <Dna className="w-6 h-6 text-white" />
          </div>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div initial={{ opacity: 0, width: 0 }} animate={{ opacity: 1, width: 'auto' }} exit={{ opacity: 0, width: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
                <h1 className="text-lg font-bold text-slate-900 whitespace-nowrap">Pharm<span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-teal-600">AI</span></h1>
                <p className="text-xs text-slate-500 whitespace-nowrap">Drug Intelligence Platform</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        {!sidebarCollapsed && <div className="mt-3 h-0.5 bg-gradient-to-r from-cyan-500 via-teal-500 to-transparent rounded-full opacity-80" />}
      </div>

      <nav className="flex-1 p-3 space-y-6 overflow-y-auto scrollbar-thin">
        {navSections.map((section) => (
          <div key={section.title}>
            <AnimatePresence>
              {!sidebarCollapsed && (
                <motion.h2 initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="px-4 mb-2 text-xs font-semibold text-slate-400 tracking-wider">
                  {section.title}
                </motion.h2>
              )}
            </AnimatePresence>
            <div className="space-y-1">
              {section.items.map((item: any) => <NavItem key={item.path} item={item} />)}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-3 border-t border-slate-100">
        <button onClick={toggleSidebar} className="w-full flex items-center gap-3 px-4 py-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-all duration-200">
          {sidebarCollapsed ? <ChevronRight className="w-5 h-5 mx-auto" /> : <><ChevronLeft className="w-5 h-5" /><span className="font-medium">Collapse</span></>}
        </button>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
