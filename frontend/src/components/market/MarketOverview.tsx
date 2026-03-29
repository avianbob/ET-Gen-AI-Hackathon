import React from 'react';
import Card from '../common/Card';
import { cn } from '../../utils/helpers';
import { formatCurrency, formatPercentage, formatCompactNumber } from '../../utils/formatters';

interface MarketOverviewProps {
  indication: string;
  marketData: any;
  className?: string;
}

const MarketOverview: React.FC<MarketOverviewProps> = ({ indication, marketData, className }) => {
  if (!marketData) {
    return (
      <div className={cn('bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center p-8', className)}>
        <p className="text-slate-500 text-sm">No market overview data available.</p>
      </div>
    );
  }

  const tam = marketData.tam ?? marketData.market_size ?? marketData.marketSize;
  const cagr = marketData.cagr ?? marketData.growth_rate ?? marketData.growthRate;
  const unmetNeed = marketData.unmet_need ?? marketData.unmetNeed ?? marketData.unmet_need_score;
  const patients = marketData.patient_population ?? marketData.patientPopulation ?? marketData.patients;
  const region = marketData.region || marketData.geography || 'Global';
  const year = marketData.year || marketData.forecast_year;

  const items = [
    { label: 'Total Addressable Market', value: formatCurrency(tam), accent: '#00D4AA' },
    { label: 'CAGR', value: cagr != null ? formatPercentage(cagr) : '—', accent: '#00B4D8' },
    { label: 'Unmet Need Score', value: unmetNeed != null ? `${Number(unmetNeed).toFixed(1)}/10` : '—', accent: '#FFE600' },
    { label: 'Patient Population', value: patients != null ? formatCompactNumber(patients) : '—', accent: '#A78BFA' },
  ];

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Market Overview</h3>
          <p className="text-xs text-slate-600 mt-0.5">
            {indication}{region ? ` · ${region}` : ''}{year ? ` · ${year}` : ''}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {items.map(({ label, value, accent }) => (
          <Card key={label} className="relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full rounded-l-xl" style={{ backgroundColor: accent }} />
            <div className="pl-3">
              <span className="text-[11px] text-slate-600 uppercase tracking-wider">{label}</span>
              <p className="text-lg font-bold text-slate-900 mt-0.5">{value}</p>
            </div>
          </Card>
        ))}
      </div>

      {(marketData.summary || marketData.description) && (
        <Card>
          <p className="text-xs text-slate-700 leading-relaxed">
            {marketData.summary || marketData.description}
          </p>
        </Card>
      )}

      {marketData.segments && marketData.segments.length > 0 && (
        <Card>
          <span className="text-[11px] text-slate-600 uppercase tracking-wider">Market Segments</span>
          <div className="mt-2 space-y-2">
            {marketData.segments.map((seg: any, i: number) => {
              const segName = seg.name || seg.segment || `Segment ${i + 1}`;
              const segShare = seg.share ?? seg.percentage;
              return (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-xs text-slate-700">{segName}</span>
                  <div className="flex items-center gap-2">
                    {segShare != null && (
                      <div className="w-24 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-cyan-400"
                          style={{ width: `${Math.min(100, segShare <= 1 ? segShare * 100 : segShare)}%` }}
                        />
                      </div>
                    )}
                    <span className="text-xs text-slate-600 w-12 text-right">
                      {segShare != null ? formatPercentage(segShare, 1, segShare <= 1) : '—'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
};

export default MarketOverview;
