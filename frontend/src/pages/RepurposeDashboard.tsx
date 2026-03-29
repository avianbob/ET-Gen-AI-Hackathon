import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Search, Clock, Bookmark, TrendingUp,
  GitCompareArrows, ArrowRight, Zap,
} from 'lucide-react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import useAppStore from '../store';
import { ET_AGENT_GROUPS, ROUTES } from '../utils/constants';
import { formatTimeAgo } from '../utils/formatters';

const ICON_MAP: Record<string, React.ReactNode> = {
  TrendingUp: <TrendingUp className="w-5 h-5" />,
  Globe: <Search className="w-5 h-5" />,
  FileText: <Bookmark className="w-5 h-5" />,
  Stethoscope: <Clock className="w-5 h-5" />,
  Database: <LayoutDashboard className="w-5 h-5" />,
  BookOpen: <Search className="w-5 h-5" />,
};

const QUICK_ACTIONS = [
  { label: 'New Search', icon: <Search className="w-4 h-4" />, route: ROUTES.SEARCH, color: 'text-sky-700 bg-sky-100' },
  { label: 'Compare Drugs', icon: <GitCompareArrows className="w-4 h-4" />, route: ROUTES.COMPARE, color: 'text-violet-700 bg-violet-100' },
  { label: 'View History', icon: <Clock className="w-4 h-4" />, route: ROUTES.HISTORY, color: 'text-amber-700 bg-amber-100' },
  { label: 'Saved Items', icon: <Bookmark className="w-4 h-4" />, route: ROUTES.SAVED, color: 'text-teal-700 bg-teal-100' },
  { label: 'AI Assistant', icon: <Zap className="w-4 h-4" />, route: ROUTES.CHAT, color: 'text-cyan-700 bg-cyan-100' },
  { label: 'Architecture', icon: <LayoutDashboard className="w-4 h-4" />, route: ROUTES.ARCHITECTURE, color: 'text-slate-700 bg-slate-100' },
];

const stagger = { animate: { transition: { staggerChildren: 0.06 } } } as const;
const fadeUp = { initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 } } as const;

const RepurposeDashboard: React.FC = () => {
  const navigate = useNavigate();
  const user = useAppStore((s) => s.user);
  const searchHistory = useAppStore((s) => s.searchHistory);
  const savedOpportunities = useAppStore((s) => s.savedOpportunities);
  const integrations = useAppStore((s) => s.integrations);

  const [quickSearch, setQuickSearch] = useState('');

  const handleQuickSearch = () => {
    const q = quickSearch.trim();
    if (!q) return;
    navigate(`${ROUTES.SEARCH}?q=${encodeURIComponent(q)}`);
  };

  const activeDataSources = integrations.filter((i: any) => i.enabled).length || 22;
  const recentSearches = searchHistory.slice(0, 5);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900">
            Welcome back{user?.name ? `, ${user.name}` : ''}
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            PharmAI Drug Repurposing Intelligence Platform
          </p>
        </div>
        <Badge variant="teal" size="lg">
          <Zap className="w-3 h-3 mr-1" />
          Online
        </Badge>
      </div>

      <motion.div
        variants={stagger}
        initial="initial"
        animate="animate"
        className="grid grid-cols-1 sm:grid-cols-3 gap-4"
      >
        {[
          { label: 'Searches', value: searchHistory.length, icon: <Search className="w-5 h-5 text-sky-600" />, color: 'border-sky-300' },
          { label: 'Saved Opportunities', value: savedOpportunities.length, icon: <Bookmark className="w-5 h-5 text-cyan-600" />, color: 'border-cyan-300' },
          { label: 'Data Sources', value: activeDataSources, icon: <TrendingUp className="w-5 h-5 text-teal-600" />, color: 'border-teal-300' },
        ].map((stat) => (
          <motion.div key={stat.label} variants={fadeUp}>
            <Card className={`border-l-2 ${stat.color}`}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
                  {stat.icon}
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{stat.value}</p>
                  <p className="text-xs text-slate-500">{stat.label}</p>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      <Card>
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Quick search — enter a drug name or disease..."
              value={quickSearch}
              onChange={(e) => setQuickSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuickSearch()}
              className="w-full pl-9 pr-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/15"
            />
          </div>
          <Button
            variant="primary"
            size="md"
            icon={<ArrowRight className="w-4 h-4" />}
            disabled={!quickSearch.trim()}
            onClick={handleQuickSearch}
          >
            Search
          </Button>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              Recent Searches
            </h2>
            {searchHistory.length > 0 && (
              <button
                type="button"
                onClick={() => navigate(ROUTES.HISTORY)}
                className="text-xs text-cyan-600 hover:text-teal-600 font-medium transition-colors"
              >
                View all
              </button>
            )}
          </div>
          {recentSearches.length > 0 ? (
            <div className="space-y-2">
              {recentSearches.map((search: any, idx: number) => (
                <div
                  key={`${search.drugName}-${idx}`}
                  className="flex items-center justify-between py-2 px-3 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer group border border-transparent hover:border-slate-100"
                  onClick={() => {
                    navigate(`${ROUTES.SEARCH}?q=${encodeURIComponent(search.drugName)}`);
                  }}
                  onKeyDown={(e) => e.key === 'Enter' && navigate(`${ROUTES.SEARCH}?q=${encodeURIComponent(search.drugName)}`)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="text-sm text-slate-800 truncate">{search.drugName}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-slate-500">{formatTimeAgo(search.timestamp)}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Search className="w-6 h-6 text-slate-300 mx-auto mb-2" />
              <p className="text-xs text-slate-500">No searches yet. Start exploring above.</p>
            </div>
          )}
        </Card>

        <Card>
          <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4 text-slate-400" />
            Quick Actions
          </h2>
          <div className="grid grid-cols-2 gap-2">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.label}
                type="button"
                onClick={() => navigate(action.route)}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 border border-slate-100 hover:border-cyan-200/80 transition-all text-left group"
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${action.color}`}>
                  {action.icon}
                </div>
                <span className="text-sm text-slate-700 group-hover:text-slate-900 transition-colors">
                  {action.label}
                </span>
              </button>
            ))}
          </div>
        </Card>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <LayoutDashboard className="w-4 h-4 text-slate-400" />
          Pipeline Agent Groups
        </h2>
        <motion.div
          variants={stagger}
          initial="initial"
          animate="animate"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3"
        >
          {Object.entries(ET_AGENT_GROUPS).map(([key, group]) => (
            <motion.div key={key} variants={fadeUp}>
              <Card hover className="h-full">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-cyan-50 flex items-center justify-center text-cyan-700 border border-cyan-100">
                    {ICON_MAP[group.icon] || <Zap className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-xs font-semibold text-slate-900 truncate">{group.name}</h3>
                  </div>
                  <Badge variant="blue">{group.agents.length}</Badge>
                </div>
                <p className="text-[11px] text-slate-500 line-clamp-2">{group.description}</p>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default RepurposeDashboard;
