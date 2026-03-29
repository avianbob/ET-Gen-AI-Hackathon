import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, Filter } from 'lucide-react';
import Badge from '../common/Badge';
import { cn } from '../../utils/helpers';
import { EVIDENCE_SOURCES } from '../../utils/constants';
import { formatDate } from '../../utils/formatters';

interface EvidencePanelProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: any[];
  indication?: string;
}

const VARIANT_MAP: Record<string, string> = {
  literature: 'blue',
  clinical_trials: 'teal',
  bioactivity: 'purple',
  patent: 'yellow',
  internal: 'red',
  openfda: 'teal',
  opentargets: 'blue',
  semantic_scholar: 'yellow',
  market_data: 'teal',
};

const EvidencePanel: React.FC<EvidencePanelProps> = ({ isOpen, onClose, evidence, indication }) => {
  const [sourceFilter, setSourceFilter] = useState<string>('all');

  const sources = useMemo(() => {
    const set = new Set<string>();
    evidence.forEach((e) => {
      const src = e.source || e.type || 'unknown';
      set.add(src);
    });
    return Array.from(set);
  }, [evidence]);

  const filtered = useMemo(() => {
    if (sourceFilter === 'all') return evidence;
    return evidence.filter((e) => (e.source || e.type) === sourceFilter);
  }, [evidence, sourceFilter]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-slate-900/30 backdrop-blur-sm z-40"
            onClick={onClose}
          />
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-lg bg-slate-100 border-l border-slate-200 z-50 flex flex-col shadow-2xl"
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Evidence Details</h2>
                {indication && (
                  <p className="text-sm text-slate-600 mt-0.5">{indication}</p>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2 overflow-x-auto">
              <Filter className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
              <button
                onClick={() => setSourceFilter('all')}
                className={cn(
                  'px-2.5 py-1 rounded-full text-xs font-medium transition-colors whitespace-nowrap',
                  sourceFilter === 'all'
                    ? 'bg-cyan-500/15 text-cyan-700 border border-cyan-500/25'
                    : 'text-slate-600 hover:text-slate-800 bg-slate-50 border border-slate-200'
                )}
              >
                All ({evidence.length})
              </button>
              {sources.map((src) => {
                const config = EVIDENCE_SOURCES[src];
                const count = evidence.filter((e) => (e.source || e.type) === src).length;
                return (
                  <button
                    key={src}
                    onClick={() => setSourceFilter(src)}
                    className={cn(
                      'px-2.5 py-1 rounded-full text-xs font-medium transition-colors whitespace-nowrap',
                      sourceFilter === src
                        ? 'bg-cyan-500/15 text-cyan-700 border border-cyan-500/25'
                        : 'text-slate-600 hover:text-slate-800 bg-slate-50 border border-slate-200'
                    )}
                  >
                    {config?.label || src} ({count})
                  </button>
                );
              })}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {filtered.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">No evidence items match this filter.</p>
              ) : (
                filtered.map((item, idx) => {
                  const source = item.source || item.type || 'unknown';
                  const relevance = item.relevance_score ?? item.relevanceScore ?? item.relevance;
                  const summary = item.summary || item.title || item.description || '';
                  const pubDate = item.publication_date ?? item.publicationDate ?? item.date;
                  const url = item.url || item.link;
                  const badgeVariant = VARIANT_MAP[source] || 'gray';

                  return (
                    <motion.div
                      key={item.id || idx}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.03 }}
                      className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <Badge variant={badgeVariant} size="sm">
                          {EVIDENCE_SOURCES[source]?.label || source}
                        </Badge>
                        {relevance != null && (
                          <span className="text-[11px] font-medium text-slate-600">
                            Relevance: <span className="text-cyan-700 font-semibold">{Number(relevance).toFixed(1)}</span>
                          </span>
                        )}
                      </div>

                      <p className="text-sm text-slate-700 leading-relaxed">{summary}</p>

                      <div className="flex items-center justify-between">
                        {pubDate && (
                          <span className="text-[11px] text-slate-500">{formatDate(pubDate)}</span>
                        )}
                        {url && (
                          <a
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 transition-colors"
                          >
                            View source <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </motion.div>
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

export default EvidencePanel;
