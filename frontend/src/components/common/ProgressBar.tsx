import React from 'react';
import { cn } from '../../utils/helpers';

interface ProgressBarProps {
  value: number;
  max?: number;
  color?: string;
  size?: string;
  showLabel?: boolean;
  className?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ value, max = 100, color = 'bg-gradient-to-r from-cyan-500 to-teal-500', size = 'sm', showLabel, className }) => {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className={cn('w-full', className)}>
      {showLabel && <div className="flex justify-between text-xs text-slate-600 mb-1"><span>{pct.toFixed(0)}%</span></div>}
      <div className={cn('w-full bg-slate-100 rounded-full overflow-hidden', size === 'sm' ? 'h-1.5' : size === 'md' ? 'h-2.5' : 'h-4')}>
        <div className={cn('h-full rounded-full transition-all duration-500', color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

export default ProgressBar;
