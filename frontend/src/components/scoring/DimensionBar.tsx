import React from 'react';
import { DIMENSION_CONFIG } from '../../utils/constants';

interface DimensionBarProps {
  dimension: string;
  score: number;
  showLabel?: boolean;
  compact?: boolean;
}

const DimensionBar: React.FC<DimensionBarProps> = ({ dimension, score, showLabel = true, compact = false }) => {
  const config = DIMENSION_CONFIG[dimension] || { label: dimension, color: '#888', shortLabel: dimension };

  return (
    <div className={compact ? 'space-y-0.5' : 'space-y-1'}>
      {showLabel && (
        <div className="flex items-center justify-between">
          <span className={`${compact ? 'text-[10px]' : 'text-xs'} text-slate-500`}>{config.shortLabel}</span>
          <span className={`${compact ? 'text-[10px]' : 'text-xs'} font-medium text-slate-900`}>{Math.round(score)}</span>
        </div>
      )}
      <div className={`w-full bg-slate-200 rounded-full overflow-hidden ${compact ? 'h-1' : 'h-1.5'}`}>
        <div className="h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${Math.min(100, score)}%`, backgroundColor: config.color }} />
      </div>
    </div>
  );
};

export default DimensionBar;
