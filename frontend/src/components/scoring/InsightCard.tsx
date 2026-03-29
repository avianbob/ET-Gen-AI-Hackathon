import React from 'react';
import { CheckCircle, AlertTriangle, Lightbulb, ArrowRight } from 'lucide-react';
import { INSIGHT_CATEGORIES } from '../../utils/constants';

const iconMap: Record<string, any> = { CheckCircle, AlertTriangle, Lightbulb, ArrowRight };

interface InsightCardProps {
  category: string;
  text: string;
  className?: string;
}

const InsightCard: React.FC<InsightCardProps> = ({ category, text, className }) => {
  const config = INSIGHT_CATEGORIES[category] || INSIGHT_CATEGORIES.recommendation;
  const Icon = iconMap[config.icon] || ArrowRight;

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg ${config.bgColor} ${className || ''}`}>
      <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${config.color}`} />
      <div>
        <span className={`text-xs font-semibold ${config.color}`}>{config.label}</span>
        <p className="text-sm text-slate-700 mt-0.5">{text}</p>
      </div>
    </div>
  );
};

export default InsightCard;
