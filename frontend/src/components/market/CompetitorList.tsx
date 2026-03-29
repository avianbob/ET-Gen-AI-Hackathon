import React from 'react';
import Card from '../common/Card';
import { cn } from '../../utils/helpers';
import { formatPercentage } from '../../utils/formatters';

interface CompetitorListProps {
  competitors: any[];
  className?: string;
}

const STATUS_STYLES: Record<string, { bg: string; text: string }> = {
  approved: { bg: 'bg-green-400/15', text: 'text-green-400' },
  marketed: { bg: 'bg-green-400/15', text: 'text-green-400' },
  'phase 3': { bg: 'bg-blue-400/15', text: 'text-blue-400' },
  'phase 2': { bg: 'bg-cyan-400/15', text: 'text-cyan-400' },
  'phase 1': { bg: 'bg-purple-400/15', text: 'text-purple-400' },
  preclinical: { bg: 'bg-gray-400/15', text: 'text-slate-600' },
  discontinued: { bg: 'bg-red-400/15', text: 'text-red-400' },
};

const getStatusStyle = (status: string) => {
  const key = status?.toLowerCase().trim() || '';
  return STATUS_STYLES[key] || { bg: 'bg-gray-400/15', text: 'text-slate-600' };
};

const CompetitorList: React.FC<CompetitorListProps> = ({ competitors, className }) => {
  if (!competitors || competitors.length === 0) {
    return (
      <div className={cn('bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center p-8', className)}>
        <p className="text-slate-500 text-sm">No competitor data available.</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      <h3 className="text-sm font-semibold text-slate-900">Competitor Landscape</h3>
      <div className="space-y-2">
        {competitors.map((comp, idx) => {
          const name = comp.name || comp.company || comp.drug_name || `Competitor ${idx + 1}`;
          const share = comp.market_share ?? comp.marketShare ?? comp.share;
          const status = comp.status || comp.phase || comp.stage || '';
          const molecule = comp.molecule || comp.drug || comp.product || '';
          const statusStyle = getStatusStyle(status);

          return (
            <Card key={idx} hover className="flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-900 truncate">{name}</span>
                  {status && (
                    <span className={cn('text-[10px] font-medium px-2 py-0.5 rounded-full', statusStyle.bg, statusStyle.text)}>
                      {status}
                    </span>
                  )}
                </div>
                {molecule && (
                  <p className="text-xs text-slate-600 mt-0.5 truncate">{molecule}</p>
                )}
              </div>
              {share != null && (
                <div className="flex flex-col items-end shrink-0">
                  <span className="text-sm font-semibold text-slate-900">
                    {formatPercentage(share, 1, share <= 1)}
                  </span>
                  <span className="text-[10px] text-slate-500">market share</span>
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default CompetitorList;
