import React from 'react';
import { getConfidenceColor, getConfidenceLabel } from '../../utils/formatters';

interface CompositeScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
  className?: string;
}

const CompositeScoreRing: React.FC<CompositeScoreRingProps> = ({ score, size = 80, strokeWidth = 6, showLabel = true, className }) => {
  const safeScore = Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (safeScore / 100) * circumference;
  const color = getConfidenceColor(safeScore);

  return (
    <div className={`relative inline-flex flex-col items-center ${className || ''}`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(15,23,42,0.08)" strokeWidth={strokeWidth} />
        <circle
          cx={size / 2} cy={size / 2} r={radius} fill="none"
          stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={circumference - progress}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-slate-900">{Math.round(safeScore)}</span>
      </div>
      {showLabel && <span className="text-[10px] font-medium mt-1" style={{ color }}>{getConfidenceLabel(safeScore)}</span>}
    </div>
  );
};

export default CompositeScoreRing;
