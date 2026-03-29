import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Search, Clock, TrendingUp, Zap, ArrowRight, Loader2, Globe, FileText, Stethoscope,
  Database, BookOpen, Cog, Calculator, MapPin, FileStack,
} from 'lucide-react';
import { useSearch } from '../hooks/useSearch';
import useAppStore from '../store';
import { useSearchParams } from 'react-router-dom';
import { ET_AGENT_GROUPS, AGENTS } from '../utils/constants';
import { formatDuration } from '../utils/formatters';
import Card from '../components/common/Card';

const AGENT_GROUP_ENTRIES = Object.entries(ET_AGENT_GROUPS) as [string, typeof ET_AGENT_GROUPS[string]][];

const GROUP_ICONS: Record<string, typeof TrendingUp> = {
  TrendingUp, Globe, FileText, Stethoscope, Database, BookOpen, Cog, Calculator, MapPin, FileStack,
};

const STATUS_DOT: Record<string, string> = {
  pending: 'bg-slate-400',
  running: 'bg-cyan-500 animate-pulse',
  success: 'bg-teal-500',
  error: 'bg-red-500',
};

const SearchPage: React.FC = () => {
  const [drugName, setDrugName] = useState('');
  const [searchParams] = useSearchParams();
  const hasAutoSearched = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { searchHistory } = useAppStore();

  const {
    isSearching, error, elapsedTime, agentProgress,
    workflowStatus, search,
  } = useSearch({ autoNavigate: true });

  useEffect(() => {
    const drug = searchParams.get('drug') || searchParams.get('q');
    if (drug && !hasAutoSearched.current) {
      hasAutoSearched.current = true;
      setDrugName(drug);
      search(drug);
    }
  }, [searchParams, search]);

  useEffect(() => {
    if (!isSearching) inputRef.current?.focus();
  }, [isSearching]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (drugName.trim()) search(drugName.trim());
  };

  const handleRecentClick = (name: string) => {
    setDrugName(name);
    search(name);
  };

  const recentSearches = searchHistory.slice(0, 6);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-16 max-w-4xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-10 w-full"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-50 border border-cyan-200 text-cyan-800 text-xs font-medium mb-6">
            <Zap className="w-3.5 h-3.5" />
            {AGENTS.length} specialized AI agents
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Drug Repurposing Search
          </h1>
          <p className="text-slate-600 text-lg max-w-2xl mx-auto">
            Enter a drug name to run one unified report: evidence, scoring, market intelligence,
            process design, techno-economics, demographics & plant siting, plus exports.
          </p>
        </motion.div>

        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="w-full max-w-2xl mb-8"
        >
          <div className="relative">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              ref={inputRef}
              type="text"
              value={drugName}
              onChange={(e) => setDrugName(e.target.value)}
              placeholder="Enter drug name — e.g. Metformin, Aspirin, Sildenafil"
              disabled={isSearching}
              className="w-full pl-14 pr-36 py-4 bg-white border border-slate-200 rounded-2xl text-slate-900 text-lg placeholder-slate-400 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/15 disabled:opacity-60 transition-all shadow-sm"
            />
            <button
              type="submit"
              disabled={!drugName.trim() || isSearching}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 text-white font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:from-cyan-500 hover:to-teal-500 shadow-md shadow-cyan-500/20 transition-colors flex items-center gap-2"
            >
              {isSearching ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Searching
                </>
              ) : (
                <>
                  Search
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {error && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-3 text-sm text-red-600 text-center"
            >
              {error}
            </motion.p>
          )}
        </motion.form>

        {isSearching && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-2xl mb-10"
          >
            <Card className="!bg-slate-50/95 !border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 text-cyan-600 animate-spin" />
                  <span className="text-sm text-slate-700">
                    {workflowStatus?.message || 'Initializing agents...'}
                  </span>
                </div>
                <span className="text-xs text-slate-500 tabular-nums">
                  <Clock className="w-3 h-3 inline mr-1" />
                  {formatDuration(elapsedTime)}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {AGENT_GROUP_ENTRIES.map(([key, group]) => {
                  const groupAgentIds: string[] = group.agents || [];
                  const statuses = groupAgentIds.map(
                    (id: string) => agentProgress[id]?.status || 'pending'
                  );
                  const overallStatus = statuses.includes('running')
                    ? 'running'
                    : statuses.every((s: string) => s === 'success')
                      ? 'success'
                      : statuses.includes('error')
                        ? 'error'
                        : 'pending';

                  return (
                    <div
                      key={key}
                      className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white border border-slate-200/80 shadow-sm"
                    >
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${STATUS_DOT[overallStatus]}`} />
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-800 truncate">{group.name}</p>
                        <p className="text-[10px] text-slate-500">
                          {groupAgentIds.length} agent{groupAgentIds.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          </motion.div>
        )}

        {!isSearching && recentSearches.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
            className="w-full max-w-2xl mb-12"
          >
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Recent Searches</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {recentSearches.map((item, i) => (
                <button
                  key={`${item.drugName}-${item.timestamp}-${i}`}
                  type="button"
                  onClick={() => handleRecentClick(item.drugName)}
                  className="px-4 py-2 rounded-xl text-sm bg-white border border-slate-200 text-slate-700 hover:border-cyan-300 hover:text-cyan-800 shadow-sm transition-all"
                >
                  {item.drugName}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {!isSearching && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45 }}
            className="w-full max-w-4xl"
          >
            <div className="text-center mb-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-1">Multi-Agent Intelligence Pipeline</h2>
              <p className="text-sm text-slate-500">
                {AGENT_GROUP_ENTRIES.length} ET agent groups orchestrating {AGENTS.length} specialized agents
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {AGENT_GROUP_ENTRIES.map(([key, group], idx) => {
                const GIcon = GROUP_ICONS[group.icon] || TrendingUp;
                return (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + idx * 0.06 }}
                >
                  <Card hover className="h-full">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-cyan-50 border border-cyan-100 flex items-center justify-center flex-shrink-0">
                        <GIcon className="w-4 h-4 text-cyan-600" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-900 mb-1">{group.name}</p>
                        <p className="text-xs text-slate-500 leading-relaxed mb-2">{group.description}</p>
                        <div className="flex flex-wrap gap-1">
                          {(group.agents as string[]).map((agentId: string) => {
                            const agent = AGENTS.find((a) => a.id === agentId);
                            return (
                              <span
                                key={agentId}
                                className="px-2 py-0.5 rounded-md text-[10px] bg-slate-100 text-slate-600 border border-slate-200"
                              >
                                {agent?.name || agentId}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
