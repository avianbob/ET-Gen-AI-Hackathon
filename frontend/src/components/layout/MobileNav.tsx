import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LayoutDashboard, Search, Clock, Bookmark, Settings, MessageSquare } from 'lucide-react';
import { cn } from '../../utils/helpers';
import { ROUTES } from '../../utils/constants';

const navItems = [
  { path: ROUTES.CHAT, label: 'Chat', icon: MessageSquare },
  { path: ROUTES.DASHBOARD, label: 'Home', icon: LayoutDashboard },
  { path: ROUTES.SEARCH, label: 'Search', icon: Search },
  { path: ROUTES.HISTORY, label: 'History', icon: Clock },
  { path: ROUTES.SETTINGS, label: 'Settings', icon: Settings },
];

const MobileNav: React.FC = () => {
  const location = useLocation();

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-md border-t border-slate-200 z-50 shadow-[0_-4px_24px_-4px_rgba(15,23,42,0.08)]">
      <div className="flex items-center justify-around py-2">
        {navItems.map((item) => {
          const active = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <NavLink key={item.path} to={item.path} className="relative flex flex-col items-center py-2 px-4 min-w-[60px]">
              {active && <motion.div layoutId="mobile-nav-indicator" className="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-1 rounded-full bg-gradient-to-r from-cyan-500 to-teal-600" />}
              <Icon className={cn('w-5 h-5 mb-1 transition-colors', active ? 'text-cyan-600' : 'text-slate-400')} />
              <span className={cn('text-xs transition-colors', active ? 'text-cyan-700 font-semibold' : 'text-slate-500')}>{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNav;
