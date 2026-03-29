import React from 'react';
import { motion } from 'framer-motion';
import { Bookmark, BookmarkCheck, FileText, ExternalLink } from 'lucide-react';
import CompositeScoreRing from '../scoring/CompositeScoreRing';
import DimensionBar from '../scoring/DimensionBar';
import Badge from '../common/Badge';
import { cn } from '../../utils/helpers';
import { EVIDENCE_SOURCES } from '../../utils/constants';

interface OpportunityCardProps {
  opportunity: any;
  drugName: string;
  onSave?: () => void;
  onSelect?: () => void;
  isSaved?: boolean;
  rank?: number;
}

const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  drugName,
  onSave,
  onSelect,
  isSaved = false,
  rank,
}) => {
  const indication = opportunity.indication || opportunity.disease || opportunity.name || 'Unknown';
  const cs = opportunity.composite_score ?? opportunity.compositeScore;
  const compositeScore = typeof cs === 'number'
    ? cs
    : cs?.overall_score != null
      ? cs.overall_score
      : typeof opportunity.score === 'number'
        ? (opportunity.score > 1 ? opportunity.score : opportunity.score * 100)
        : opportunity.confidence_score ?? 0;
  const dims = ['scientific_evidence', 'market_opportunity', 'competitive_landscape', 'development_feasibility'];
  const dimensionScores: Record<string, number> = {};
  dims.forEach((d) => {
    const sub = cs?.[d];
    dimensionScores[d] = typeof sub === 'object' && sub?.score != null ? sub.score : (opportunity.dimension_scores ?? opportunity.dimensionScores ?? opportunity.scores ?? {})[d] ?? 0;
  });
  const evidenceCount = opportunity.evidence_count ?? opportunity.evidenceCount ?? opportunity.evidence?.length ?? 0;

  const evidenceTypes = opportunity.evidence_types ?? opportunity.evidenceTypes ?? [];
  const displayTypes = Array.isArray(evidenceTypes)
    ? evidenceTypes
    : Object.keys(dimensionScores).length > 0
      ? Object.keys(EVIDENCE_SOURCES).slice(0, 3)
      : [];


  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: rank ? rank * 0.05 : 0 }}
      onClick={onSelect}
      className={cn(
        'group relative bg-slate-50 border border-slate-200 rounded-xl p-4 backdrop-blur-sm',
        'hover:border-cyan-500/25 hover:bg-white cursor-pointer transition-all duration-200'
      )}
    >
      {rank !== undefined && (
        <div className="absolute -top-2 -left-2 w-7 h-7 rounded-full bg-yellow-500 flex items-center justify-center shadow-lg shadow-cyan-500/15">
          <span className="text-xs font-bold text-gray-900">#{rank}</span>
        </div>
      )}

      {onSave && (
        <button
          onClick={(e) => { e.stopPropagation(); onSave(); }}
          className={cn(
            'absolute top-3 right-3 p-1.5 rounded-lg transition-all duration-200',
            isSaved
              ? 'text-cyan-700 bg-cyan-500/15 hover:bg-cyan-500/25'
              : 'text-slate-500 hover:text-cyan-700 hover:bg-slate-100'
          )}
        >
          {isSaved ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
        </button>
      )}

      <div className="flex items-start gap-4">
        <CompositeScoreRing score={compositeScore} size={64} strokeWidth={5} showLabel={false} />

        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 truncate pr-8">{indication}</h3>
          <p className="text-[11px] text-slate-600 mt-0.5">
            {drugName} → {indication}
          </p>

          <div className="mt-3 space-y-1.5">
            {dims.map((dim) => (
              <DimensionBar
                key={dim}
                dimension={dim}
                score={dimensionScores[dim] ?? 0}
                compact
              />
            ))}
          </div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-slate-200 pt-3">
        <div className="flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-[11px] text-slate-600">{evidenceCount} evidence items</span>
        </div>

        <div className="flex items-center gap-1">
          {displayTypes.slice(0, 3).map((type: string) => {
            const src = EVIDENCE_SOURCES[type];
            return (
              <Badge key={type} variant="gray" size="sm">
                {src?.label || type}
              </Badge>
            );
          })}
          {displayTypes.length > 3 && (
            <Badge variant="gray" size="sm">+{displayTypes.length - 3}</Badge>
          )}
        </div>
      </div>

      <div className="absolute inset-0 rounded-xl border-2 border-yellow-500/0 group-hover:border-cyan-500/15 transition-all duration-300 pointer-events-none" />
    </motion.div>
  );
};

export default OpportunityCard;
