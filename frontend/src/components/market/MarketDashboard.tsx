import React from 'react';
import Card from '../common/Card';
import { cn } from '../../utils/helpers';
import { formatCurrency, formatPercentage, formatCompactNumber } from '../../utils/formatters';

interface MarketDashboardProps {
  data: any;
  className?: string;
}

interface MetricCardProps {
  label: string;
  value: string;
  subtitle?: string;
  trend?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, subtitle, trend }) => (
  <Card className="flex flex-col gap-1">
    <span className="text-[11px] text-slate-600 uppercase tracking-wider">{label}</span>
    <span className="text-xl font-bold text-slate-900">{value}</span>
    {subtitle && <span className="text-xs text-slate-500">{subtitle}</span>}
    {trend !== undefined && (
      <span className={cn('text-xs font-medium', trend >= 0 ? 'text-green-400' : 'text-red-400')}>
        {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
      </span>
    )}
  </Card>
);

const MarketDashboard: React.FC<MarketDashboardProps> = ({ data, className }) => {
  if (!data) {
    return (
      <div className={cn('bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center p-8', className)}>
        <p className="text-slate-500 text-sm">No market data available.</p>
      </div>
    );
  }

  const marketSize = data.market_size ?? data.marketSize ?? data.tam;
  const growthRate = data.growth_rate ?? data.growthRate ?? data.cagr;
  const patientPop = data.patient_population ?? data.patientPopulation ?? data.patients;
  const unmetNeed = data.unmet_need ?? data.unmetNeed;
  const competitors = data.competitors?.length ?? data.competitor_count ?? data.competitorCount;
  const peakSales = data.peak_sales ?? data.peakSales;

  return (
    <div className={cn('space-y-4', className)}>
      <h3 className="text-sm font-semibold text-slate-900">Market Dashboard</h3>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <MetricCard
          label="Market Size (TAM)"
          value={formatCurrency(marketSize)}
          subtitle="Total addressable market"
        />
        <MetricCard
          label="Growth Rate"
          value={growthRate != null ? formatPercentage(growthRate) : '—'}
          subtitle="CAGR"
          trend={growthRate}
        />
        <MetricCard
          label="Patient Population"
          value={patientPop != null ? formatCompactNumber(patientPop) : '—'}
          subtitle="Estimated patients"
        />
        <MetricCard
          label="Unmet Need Score"
          value={unmetNeed != null ? `${Number(unmetNeed).toFixed(1)}/10` : '—'}
          subtitle="Clinical gap"
        />
        <MetricCard
          label="Competitors"
          value={competitors != null ? String(competitors) : '—'}
          subtitle="Active market players"
        />
        <MetricCard
          label="Peak Sales Estimate"
          value={formatCurrency(peakSales)}
          subtitle="Annual peak revenue"
        />
      </div>

      {data.key_drivers && (
        <Card>
          <span className="text-[11px] text-slate-600 uppercase tracking-wider">Key Market Drivers</span>
          <ul className="mt-2 space-y-1">
            {data.key_drivers.map((driver: string, i: number) => (
              <li key={i} className="text-xs text-slate-700 flex items-start gap-2">
                <span className="text-cyan-700 mt-0.5">•</span>
                {driver}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
};

export default MarketDashboard;
