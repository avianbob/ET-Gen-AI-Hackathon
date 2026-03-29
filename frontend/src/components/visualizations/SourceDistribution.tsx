import React, { useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { cn } from '../../utils/helpers';
import { EVIDENCE_SOURCES } from '../../utils/constants';

interface SourceDistributionProps {
  evidence: any[];
  className?: string;
}

const FALLBACK_COLOR = '#6B7280';

const SourceDistribution: React.FC<SourceDistributionProps> = ({ evidence, className }) => {
  const chartData = useMemo(() => {
    if (!evidence || evidence.length === 0) return [];

    const counts: Record<string, number> = {};
    evidence.forEach((item) => {
      const source = item.source || item.type || item.agent || 'unknown';
      const key = source.toLowerCase().replace(/\s+/g, '_');
      counts[key] = (counts[key] || 0) + 1;
    });

    return Object.entries(counts)
      .map(([key, count]) => ({
        name: EVIDENCE_SOURCES[key]?.label || key.replace(/_/g, ' '),
        value: count,
        color: EVIDENCE_SOURCES[key]?.color || FALLBACK_COLOR,
      }))
      .sort((a, b) => b.value - a.value);
  }, [evidence]);

  if (chartData.length === 0) {
    return (
      <div className={cn('bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center p-8', className)}>
        <p className="text-slate-500 text-sm">No evidence sources to display.</p>
      </div>
    );
  }

  return (
    <div className={cn('bg-slate-100 rounded-xl border border-slate-200 p-4', className)}>
      <h3 className="text-sm font-semibold text-slate-900 mb-3">Evidence Source Distribution</h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="45%"
            innerRadius={50}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
            nameKey="name"
            stroke="rgba(0,0,0,0.3)"
            strokeWidth={1}
          >
            {chartData.map((entry, idx) => (
              <Cell key={`cell-${idx}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#E5E7EB',
              fontSize: '12px',
            }}
            formatter={(value: number, name: string) => [
              `${value} item${value !== 1 ? 's' : ''}`,
              name,
            ]}
          />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            iconSize={8}
            formatter={(value: string) => (
              <span style={{ color: '#9CA3AF', fontSize: '11px' }}>{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SourceDistribution;
