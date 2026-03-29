import React, { useState, useMemo } from 'react';
import { ArrowUpDown } from 'lucide-react';
import OpportunityCard from './OpportunityCard';
import EmptyState from '../common/EmptyState';
import { cn } from '../../utils/helpers';

type SortKey = 'score' | 'alphabetical';

interface OpportunityListProps {
  opportunities: any[];
  drugName: string;
  onSelect: (opp: any) => void;
  onSave?: (opp: any) => void;
  savedIds?: string[];
}

const OpportunityList: React.FC<OpportunityListProps> = ({
  opportunities,
  drugName,
  onSelect,
  onSave,
  savedIds = [],
}) => {
  const [sortBy, setSortBy] = useState<SortKey>('score');

  const sorted = useMemo(() => {
    const list = [...opportunities];
    if (sortBy === 'score') {
      list.sort((a, b) => {
        const sa = a.composite_score ?? a.compositeScore ?? a.score ?? 0;
        const sb = b.composite_score ?? b.compositeScore ?? b.score ?? 0;
        return sb - sa;
      });
    } else {
      list.sort((a, b) => {
        const na = (a.indication || a.disease || a.name || '').toLowerCase();
        const nb = (b.indication || b.disease || b.name || '').toLowerCase();
        return na.localeCompare(nb);
      });
    }
    return list;
  }, [opportunities, sortBy]);

  if (!opportunities.length) {
    return (
      <EmptyState
        title="No Opportunities Found"
        description="No repurposing opportunities were identified for this drug. Try a different search."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-600">
          {opportunities.length} opportunit{opportunities.length === 1 ? 'y' : 'ies'} found
        </span>
        <div className="flex items-center gap-2">
          <ArrowUpDown className="w-3.5 h-3.5 text-slate-500" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortKey)}
            className={cn(
              'bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700',
              'px-3 py-1.5 focus:outline-none focus:border-cyan-500/50'
            )}
          >
            <option value="score">Sort by Score</option>
            <option value="alphabetical">Sort Alphabetically</option>
          </select>
        </div>
      </div>

      <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-gray-700">
        {sorted.map((opp, idx) => {
          const id = opp.id || `${opp.indication || opp.disease || idx}`;
          return (
            <OpportunityCard
              key={id}
              opportunity={opp}
              drugName={drugName}
              rank={sortBy === 'score' ? idx + 1 : undefined}
              isSaved={savedIds.includes(id)}
              onSelect={() => onSelect(opp)}
              onSave={onSave ? () => onSave(opp) : undefined}
            />
          );
        })}
      </div>
    </div>
  );
};

export default OpportunityList;
