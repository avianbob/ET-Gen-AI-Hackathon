import React from 'react';
import {
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { cn } from '../../utils/helpers';

interface RadarChartProps {
  data: { dimension: string; score: number }[];
  className?: string;
}

const RADAR_COLOR = '#00B4D8';

const RadarChart: React.FC<RadarChartProps> = ({ data, className }) => {
  if (!data || data.length === 0) {
    return (
      <div className={cn('bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center p-8', className)}>
        <p className="text-slate-500 text-sm">No scoring dimensions available.</p>
      </div>
    );
  }

  const chartData = data
    .filter((d) => d && Number.isFinite(d.score))
    .map((d) => ({
      dimension: String(d.dimension || ''),
      score: Math.max(0, Math.min(100, Number(d.score) || 0)),
      fullMark: 100,
    }));

  const chartHeight = 260;
  return (
    <div className={cn('bg-slate-100 rounded-xl border border-slate-200 p-4', className)}>
      <h3 className="text-sm font-semibold text-slate-900 mb-3">4D Scoring Dimensions</h3>
      <div className="w-full flex items-center justify-center" style={{ height: chartHeight, minHeight: chartHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          <RechartsRadarChart data={chartData} cx="50%" cy="50%" outerRadius="55%" margin={{ top: 24, right: 24, bottom: 24, left: 24 }}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            tickLine={false}
            tickFormatter={(v) => (typeof v === 'string' && v.length > 12 ? v.slice(0, 11) + '…' : v)}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: '#6B7280', fontSize: 10 }}
            axisLine={false}
            tickCount={5}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke={RADAR_COLOR}
            fill={RADAR_COLOR}
            fillOpacity={0.2}
            strokeWidth={2}
            dot={{ r: 4, fill: RADAR_COLOR, stroke: '#111827', strokeWidth: 2 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#E5E7EB',
              fontSize: '12px',
            }}
            formatter={(value: number) => [`${value.toFixed(1)}`, 'Score']}
          />
          </RechartsRadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default RadarChart;
