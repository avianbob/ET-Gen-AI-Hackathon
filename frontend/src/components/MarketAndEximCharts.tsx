import React, { useState } from 'react';
import { Info } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  DefaultTooltipContent,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import type { TooltipContentProps } from 'recharts';

/** Prevents tooltip from overlapping Y-axis on narrow viewports (e.g. mobile) */
function MarketTrendTooltipContent(props: TooltipContentProps<number, string>) {
  const { coordinate } = props;
  const minLeft = 56;
  const pushRight = coordinate?.x != null && coordinate.x < minLeft ? minLeft - coordinate.x : 0;
  return (
    <div style={{ marginLeft: pushRight }}>
      <DefaultTooltipContent {...props} />
    </div>
  );
}

/** Market data from IQVIA agent: trend, regional breakdown, CAGR, technical details */
export interface MarketData {
  estimated_market_size_billion_usd?: number;
  cagr?: number;
  cagr_percent?: number;
  key_regions?: string[];
  market_demand_score?: number;
  market_trend?: Array<{ year: string; market_size_billion_usd?: number; sales_billion_usd?: number }>;
  regional_breakdown?: Array<{ region: string; share_percent?: number; value_billion_usd?: number }>;
  estimated_sales_projection?: Array<{ year: string; sales_billion_usd?: number }>;
  technical_details?: {
    methodology?: string;
    currency?: string;
    base_year?: number;
    definition_market_size?: string;
    definition_cagr?: string;
  };
}

/** EXIM data from EXIM agent: trade trend, regional trade, scores */
export interface EximData {
  import_dependency_score?: number;
  export_opportunity_score?: number;
  overall_market_demand_score?: number;
  trade_trend?: Array<{
    year: string;
    import_index?: number;
    export_index?: number;
    import_value_billion_usd?: number;
    export_value_billion_usd?: number;
  }>;
  regional_trade?: Array<{
    region: string;
    import_share_percent?: number;
    export_share_percent?: number;
  }>;
  technical_details?: {
    methodology?: string;
    currency?: string;
    definition_import_dependency?: string;
    definition_export_opportunity?: string;
    source_note?: string;
  };
}

interface MarketAndEximChartsProps {
  marketData?: MarketData | null;
  eximData?: EximData | null;
  /** Optional molecule/drug name for titles */
  drugName?: string | null;
}

const CHART_COLORS = {
  primary: '#06b6d4',
  secondary: '#0d9488',
  areaFill: 'rgba(6, 182, 212, 0.2)',
  exportColor: '#0d9488',
  importColor: '#f59e0b',
  pie: ['#06b6d4', '#0d9488', '#14b8a6', '#f59e0b', '#64748b'],
};

/** Info button for EXIM section: explains Import dependency & Export opportunity */
function EximInfoButton({ eximData }: { eximData?: EximData | null }) {
  const [open, setOpen] = useState(false);
  const defImport = eximData?.technical_details?.definition_import_dependency?.trim();
  const defExport = eximData?.technical_details?.definition_export_opportunity?.trim();
  return (
    <div className="relative inline-block shrink-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-7 h-7 rounded-full bg-slate-200 hover:bg-cyan-100 text-slate-500 hover:text-cyan-600 flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        aria-label="What do Import dependency and Export opportunity mean?"
      >
        <Info size={14} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" aria-hidden onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 z-[200] w-80 bg-slate-800 text-slate-100 text-xs p-4 rounded-lg shadow-xl border border-slate-600">
            <p className="font-bold text-cyan-200 mb-2">EXIM metrics</p>
            <p className="font-semibold text-slate-200 mt-2">Import dependency</p>
            <p className="leading-relaxed text-slate-300 mt-0.5">
              {defImport || 'Measures how reliant the market is on imports for this product. Lower score means less import dependency (more self-sufficient or export-oriented).'}
            </p>
            <p className="font-semibold text-slate-200 mt-3">Export opportunity</p>
            <p className="leading-relaxed text-slate-300 mt-0.5">
              {defExport || 'Indicates the potential for exporting this product. Higher score suggests stronger export opportunity.'}
            </p>
          </div>
        </>
      )}
    </div>
  );
}

export const MarketAndEximCharts: React.FC<MarketAndEximChartsProps> = ({
  marketData,
  eximData,
  drugName,
}) => {
  const hasMarket = marketData && (marketData.market_trend?.length || marketData.regional_breakdown?.length || marketData.estimated_market_size_billion_usd != null);
  const hasExim = eximData && (eximData.trade_trend?.length || eximData.regional_trade?.length || eximData.import_dependency_score != null);

  if (!hasMarket && !hasExim) {
    return null;
  }

  const titleSuffix = drugName?.trim() ? ` · ${drugName}` : '';

  return (
    <div className="w-full space-y-6 md:space-y-8">
      {/* Section title - matches site UI */}
      <div className="flex items-center gap-3">
        <span className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600 shrink-0">
          <i className="fas fa-chart-line text-sm"></i>
        </span>
        <h2 className="text-base sm:text-lg font-bold text-slate-800 truncate">Sales &amp; Market Trend{titleSuffix}</h2>
      </div>

      {/* --- Market (IQVIA) --- */}
      {hasMarket && (
        <div className="bg-white rounded-xl sm:rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
          <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 bg-slate-50">
            <h3 className="text-base font-bold text-slate-800">Market size &amp; estimated sales</h3>
            <p className="text-xs text-slate-500 mt-0.5">IQVIA-style market insights (TAM, CAGR, regional split)</p>
          </div>
          <div className="p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
            {/* KPI cards — min-w-0 + overflow-visible so labels (e.g. USD) don't get cut off on mobile */}
            <div className="lg:col-span-3 flex flex-wrap gap-3 sm:gap-4">
              <div className="bg-cyan-50 rounded-xl px-4 sm:px-5 py-3 sm:py-4 border border-cyan-100 min-w-0 flex-1 sm:flex-none sm:min-w-[140px] overflow-visible">
                <p className="text-xs font-semibold text-cyan-700 uppercase tracking-wider">Market size (TAM)</p>
                <p className="text-2xl font-bold text-slate-800 mt-1 break-words">
                  ${marketData!.estimated_market_size_billion_usd ?? 0}B
                  <span className="text-sm font-normal text-slate-500 ml-1 whitespace-nowrap">USD</span>
                </p>
              </div>
              <div className="bg-teal-50 rounded-xl px-4 sm:px-5 py-3 sm:py-4 border border-teal-100 min-w-0 flex-1 sm:flex-none sm:min-w-[140px] overflow-visible">
                <p className="text-xs font-semibold text-teal-700 uppercase tracking-wider">CAGR</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">
                  {(marketData!.cagr_percent ?? (marketData!.cagr ?? 0) * 100).toFixed(1)}%
                  <span className="text-sm font-normal text-slate-500 ml-1">p.a.</span>
                </p>
              </div>
              <div className="bg-slate-50 rounded-xl px-4 sm:px-5 py-3 sm:py-4 border border-slate-100 min-w-0 flex-1 sm:flex-none sm:min-w-[140px] overflow-visible">
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Demand score</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">
                  {((marketData!.market_demand_score ?? 0) * 100).toFixed(0)}
                  <span className="text-sm font-normal text-slate-500 ml-1">/ 100</span>
                </p>
              </div>
            </div>

            {/* Market trend / estimated sales over time */}
            {marketData!.market_trend && marketData!.market_trend.length > 0 && (
              <div className="lg:col-span-2 min-w-0">
                <p className="text-sm font-medium text-slate-600 mb-2">Market trend &amp; estimated sales</p>
                <div className="h-[260px] w-full min-w-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={marketData!.market_trend}
                      margin={{ top: 8, right: 8, left: 48, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="marketGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={CHART_COLORS.primary} stopOpacity={0.35} />
                          <stop offset="100%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="#64748b" />
                      <YAxis tick={{ fontSize: 11 }} stroke="#64748b" tickFormatter={(v) => `$${v}B`} width={40} />
                      <Tooltip
                        content={<MarketTrendTooltipContent />}
                        formatter={(v: number) => [`$${v} B USD`, 'Market size']}
                        labelFormatter={(l) => `Year ${l}`}
                        wrapperStyle={{ maxWidth: '85%' }}
                      />
                      <Area type="monotone" dataKey="market_size_billion_usd" name="Market size (B USD)" stroke={CHART_COLORS.primary} fill="url(#marketGrad)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Regional breakdown */}
            {marketData!.regional_breakdown && marketData!.regional_breakdown.length > 0 && (
              <div className="lg:col-span-1">
                <p className="text-sm font-medium text-slate-600 mb-2">Regional share</p>
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={marketData!.regional_breakdown}
                        dataKey="share_percent"
                        nameKey="region"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label={({ region, share_percent }) => `${region} ${share_percent ?? 0}%`}
                        labelLine={false}
                      >
                        {(marketData!.regional_breakdown ?? []).map((_, i) => (
                          <Cell key={i} fill={CHART_COLORS.pie[i % CHART_COLORS.pie.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(v: number, _name: string, props: { payload?: { region?: string; value_billion_usd?: number } }) => [
                          `${v}% · $${props.payload?.value_billion_usd ?? 0}B`,
                          props.payload?.region ?? 'Region',
                        ]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Regional bar (alternative view) */}
            {marketData!.regional_breakdown && marketData!.regional_breakdown.length > 0 && (
              <div className="lg:col-span-3">
                <p className="text-sm font-medium text-slate-600 mb-2">Regional market value (B USD)</p>
                <div className="h-[220px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={marketData!.regional_breakdown} layout="vertical" margin={{ top: 4, right: 24, left: 48, bottom: 4 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis type="number" tickFormatter={(v) => `$${v}`} tick={{ fontSize: 10 }} />
                      <YAxis type="category" dataKey="region" width={44} tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(v: number) => [`$${v} B`, 'Value']} />
                      <Bar dataKey="value_billion_usd" name="Value (B USD)" fill={CHART_COLORS.primary} radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- EXIM --- */}
      {hasExim && (
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-start justify-between gap-2">
            <div>
              <h3 className="text-base font-bold text-slate-800">EXIM trade trend</h3>
              <p className="text-xs text-slate-500 mt-0.5">Import dependency &amp; export opportunity</p>
            </div>
            <EximInfoButton eximData={eximData} />
          </div>
          <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* EXIM score cards */}
            <div className="lg:col-span-3 flex flex-wrap gap-4">
              <div className="bg-amber-50 rounded-xl px-5 py-4 border border-amber-100 min-w-[140px]">
                <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider">Import dependency</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">
                  {((eximData!.import_dependency_score ?? 0) * 100).toFixed(0)}
                  <span className="text-sm font-normal text-slate-500 ml-1">/ 100 (lower = better)</span>
                </p>
              </div>
              <div className="bg-emerald-50 rounded-xl px-5 py-4 border border-emerald-100 min-w-[140px]">
                <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Export opportunity</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">
                  {((eximData!.export_opportunity_score ?? 0) * 100).toFixed(0)}
                  <span className="text-sm font-normal text-slate-500 ml-1">/ 100</span>
                </p>
              </div>
              <div className="bg-slate-50 rounded-xl px-5 py-4 border border-slate-100 min-w-[140px]">
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Overall demand score</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">
                  {((eximData!.overall_market_demand_score ?? 0) * 100).toFixed(0)}
                  <span className="text-sm font-normal text-slate-500 ml-1">/ 100</span>
                </p>
              </div>
            </div>

            {/* Trade trend: import vs export index */}
            {eximData!.trade_trend && eximData!.trade_trend.length > 0 && (
              <div className="lg:col-span-2">
                <p className="text-sm font-medium text-slate-600 mb-2">Import vs export index (base 100)</p>
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={eximData!.trade_trend} margin={{ top: 8, right: 8, left: 48, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="#64748b" />
                      <YAxis tick={{ fontSize: 11 }} stroke="#64748b" />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="import_index" name="Import index" stroke={CHART_COLORS.importColor} strokeWidth={2} dot={{ r: 4 }} />
                      <Line type="monotone" dataKey="export_index" name="Export index" stroke={CHART_COLORS.exportColor} strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Trade value over time (optional) */}
            {eximData!.trade_trend && eximData!.trade_trend.some((t) => t.import_value_billion_usd != null || t.export_value_billion_usd != null) && (
              <div className="lg:col-span-1">
                <p className="text-sm font-medium text-slate-600 mb-2">Trade value (B USD)</p>
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={eximData!.trade_trend} margin={{ top: 8, right: 8, left: 48, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `$${v}`} />
                      <Tooltip formatter={(v: number) => [`$${v}B`, '']} />
                      <Legend />
                      <Bar dataKey="import_value_billion_usd" name="Import" fill={CHART_COLORS.importColor} radius={[4, 4, 0, 0]} />
                      <Bar dataKey="export_value_billion_usd" name="Export" fill={CHART_COLORS.exportColor} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Regional trade share */}
            {eximData!.regional_trade && eximData!.regional_trade.length > 0 && (
              <div className="lg:col-span-3">
                <p className="text-sm font-medium text-slate-600 mb-2">Regional trade share (%)</p>
                <div className="h-[240px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={eximData!.regional_trade} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="region" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                      <Tooltip formatter={(v: number) => [`${v}%`, '']} />
                      <Legend />
                      <Bar dataKey="import_share_percent" name="Import share" fill={CHART_COLORS.importColor} radius={[4, 4, 0, 0]} />
                      <Bar dataKey="export_share_percent" name="Export share" fill={CHART_COLORS.exportColor} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
};
