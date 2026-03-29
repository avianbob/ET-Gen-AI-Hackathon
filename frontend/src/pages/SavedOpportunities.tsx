import React, { useState, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bookmark, Trash2, Search, Filter, SortAsc, ChevronDown, FlaskConical } from 'lucide-react';
import { useAppStore } from '../store';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';
import Button from '../components/common/Button';
import CompositeScoreRing from '../components/scoring/CompositeScoreRing';
import DimensionBar from '../components/scoring/DimensionBar';

const STATUS_OPTIONS = ['Investigating', 'Shortlisted', 'In Development', 'Deprioritized'] as const;
type Status = typeof STATUS_OPTIONS[number];

const STATUS_VARIANT: Record<string, string> = {
  Investigating: 'blue',
  Shortlisted: 'yellow',
  'In Development': 'teal',
  Deprioritized: 'gray',
};

const SORT_OPTIONS = [
  { id: 'recent', label: 'Recently Saved' },
  { id: 'score', label: 'Highest Score' },
  { id: 'alpha', label: 'Alphabetical' },
] as const;

const SavedOpportunities: React.FC = () => {
  const { savedOpportunities, removeOpportunity, updateOpportunityStatus, updateOpportunityNotes } = useAppStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('recent');
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [expandedNotes, setExpandedNotes] = useState<Set<string>>(new Set());
  const sortRef = useRef<HTMLDivElement>(null);
  const filterRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (sortRef.current && !sortRef.current.contains(e.target as Node)) setShowSortMenu(false);
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) setShowFilterMenu(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filtered = useMemo(() => {
    let items = [...savedOpportunities];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (o: any) =>
          o.drugName?.toLowerCase().includes(q) ||
          o.indication?.toLowerCase().includes(q) ||
          o.notes?.toLowerCase().includes(q)
      );
    }

    if (statusFilter !== 'all') {
      items = items.filter((o: any) => o.status === statusFilter);
    }

    switch (sortBy) {
      case 'score':
        items.sort((a: any, b: any) => (b.compositeScore ?? 0) - (a.compositeScore ?? 0));
        break;
      case 'alpha':
        items.sort((a: any, b: any) => (a.drugName || '').localeCompare(b.drugName || ''));
        break;
      default:
        break;
    }

    return items;
  }, [savedOpportunities, searchQuery, statusFilter, sortBy]);

  const grouped = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const item of filtered) {
      const key = item.drugName || 'Unknown';
      if (!map[key]) map[key] = [];
      map[key].push(item);
    }
    return map;
  }, [filtered]);

  const toggleNotes = (id: string) => {
    setExpandedNotes((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Saved Opportunities</h1>
          <p className="text-sm text-slate-600 mt-1">
            {savedOpportunities.length} opportunity{savedOpportunities.length !== 1 ? 'ies' : 'y'} bookmarked
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative w-full sm:w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          {/* Filter dropdown */}
          <div ref={filterRef} className="relative">
            <Button
              variant="secondary"
              size="sm"
              icon={<Filter className="w-3.5 h-3.5" />}
              onClick={() => { setShowFilterMenu(!showFilterMenu); setShowSortMenu(false); }}
            >
              <span className="hidden sm:inline">Filter</span>
            </Button>
            {showFilterMenu && (
              <div className="absolute right-0 top-full mt-1 w-48 bg-slate-50 border border-slate-200 rounded-lg shadow-xl z-20 py-1">
                <button
                  onClick={() => { setStatusFilter('all'); setShowFilterMenu(false); }}
                  className={`w-full text-left px-3 py-2 text-sm transition-colors ${statusFilter === 'all' ? 'text-cyan-700 bg-cyan-500/10' : 'text-slate-700 hover:bg-slate-50'}`}
                >
                  All Statuses
                </button>
                {STATUS_OPTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => { setStatusFilter(s); setShowFilterMenu(false); }}
                    className={`w-full text-left px-3 py-2 text-sm transition-colors ${statusFilter === s ? 'text-cyan-700 bg-cyan-500/10' : 'text-slate-700 hover:bg-slate-50'}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Sort dropdown */}
          <div ref={sortRef} className="relative">
            <Button
              variant="secondary"
              size="sm"
              icon={<SortAsc className="w-3.5 h-3.5" />}
              onClick={() => { setShowSortMenu(!showSortMenu); setShowFilterMenu(false); }}
            >
              <span className="hidden sm:inline">Sort</span>
              <ChevronDown className="w-3 h-3" />
            </Button>
            {showSortMenu && (
              <div className="absolute right-0 top-full mt-1 w-48 bg-slate-50 border border-slate-200 rounded-lg shadow-xl z-20 py-1">
                {SORT_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => { setSortBy(opt.id); setShowSortMenu(false); }}
                    className={`w-full text-left px-3 py-2 text-sm transition-colors ${sortBy === opt.id ? 'text-cyan-700 bg-cyan-500/10' : 'text-slate-700 hover:bg-slate-50'}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<Bookmark className="w-12 h-12" />}
          title="No saved opportunities"
          description={
            searchQuery || statusFilter !== 'all'
              ? 'No opportunities match your filters. Try adjusting your search or filter.'
              : 'Bookmark repurposing opportunities from drug search results to track them here.'
          }
        />
      ) : (
        <div className="space-y-8">
          {Object.entries(grouped).map(([drugName, items]) => (
            <div key={drugName}>
              <div className="flex items-center gap-2 mb-3">
                <FlaskConical className="w-4 h-4 text-cyan-700" />
                <span className="text-sm font-semibold text-slate-900">{drugName}</span>
                <Badge variant="yellow" size="sm">{items.length}</Badge>
              </div>
              <div className="space-y-3">
                {items.map((opp: any, idx: number) => (
                  <motion.div
                    key={opp.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.04 }}
                  >
                    <Card className="space-y-3">
                      <div className="flex items-start gap-4">
                        {opp.compositeScore != null && (
                          <div className="shrink-0">
                            <CompositeScoreRing score={opp.compositeScore} size={64} strokeWidth={5} />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0">
                              <p className="text-sm font-semibold text-slate-900 truncate">{opp.indication || opp.drugName}</p>
                              {opp.indication && opp.drugName && (
                                <p className="text-xs text-slate-500 mt-0.5">{opp.drugName}</p>
                              )}
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              {/* Status dropdown */}
                              <select
                                value={opp.status || 'Investigating'}
                                onChange={(e) => updateOpportunityStatus(opp.id, e.target.value)}
                                className="bg-slate-100 border border-gray-600/50 text-xs text-slate-800 rounded-md px-2 py-1 focus:outline-none focus:border-cyan-500/50 cursor-pointer"
                              >
                                {STATUS_OPTIONS.map((s) => (
                                  <option key={s} value={s}>{s}</option>
                                ))}
                              </select>
                              <Button
                                variant="ghost"
                                size="xs"
                                icon={<Trash2 className="w-3.5 h-3.5" />}
                                onClick={() => removeOpportunity(opp.id)}
                                className="text-slate-500 hover:text-red-400"
                              />
                            </div>
                          </div>

                          {opp.status && (
                            <Badge variant={STATUS_VARIANT[opp.status] || 'gray'} size="sm" className="mt-1.5">
                              {opp.status}
                            </Badge>
                          )}

                          {/* Dimension bars */}
                          {opp.dimensions && (
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-3">
                              {Object.entries(opp.dimensions).map(([dim, score]) => (
                                <DimensionBar key={dim} dimension={dim} score={score as number} compact />
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Notes */}
                      <div>
                        <button
                          onClick={() => toggleNotes(opp.id)}
                          className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
                        >
                          {expandedNotes.has(opp.id) ? 'Hide notes' : 'Add / view notes'}
                        </button>
                        <AnimatePresence>
                          {expandedNotes.has(opp.id) && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.2 }}
                              className="overflow-hidden"
                            >
                              <textarea
                                value={opp.notes || ''}
                                onChange={(e) => updateOpportunityNotes(opp.id, e.target.value)}
                                placeholder="Add notes about this opportunity..."
                                rows={3}
                                className="w-full mt-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 placeholder-slate-400 p-3 resize-none focus:outline-none focus:border-cyan-500/25"
                              />
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SavedOpportunities;
