import React from 'react';
import { DIMENSION_CONFIG } from '../../utils/constants';
import DimensionBar from './DimensionBar';

interface ScoreBreakdownProps {
  scores: Record<string, number>;
  className?: string;
}

const ScoreBreakdown: React.FC<ScoreBreakdownProps> = ({ scores, className }) => {
  return (
    <div className={`space-y-3 ${className || ''}`}>
      {Object.keys(DIMENSION_CONFIG).map((dim) => (
        <DimensionBar key={dim} dimension={dim} score={scores[dim] || 0} />
      ))}
    </div>
  );
};

export default ScoreBreakdown;
