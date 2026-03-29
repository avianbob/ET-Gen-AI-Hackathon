import React from 'react';
import { TrendingDown, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

interface CompetitorIntelligenceProps {
  /** Your calculated cost per kg from TEA Agent */
  costPerKgUsd?: number | null;
  /** Drug/molecule name for context */
  drugName?: string | null;
  /** Market price (bulk API) from IQVIA/LLM when available; overrides mock */
  marketPriceUsdPerKg?: number | null;
}

// Fallback market prices when API does not provide typical_api_price_usd_per_kg
const MOCK_COMPETITORS: Record<string, { priceUsdPerKg: number; label: string }> = {
  default: { priceUsdPerKg: 42, label: 'Market (generic benchmark)' },
  metformin: { priceUsdPerKg: 18, label: 'Market (bulk API benchmark)' },
  roflumilast: { priceUsdPerKg: 38, label: 'Market (generic benchmark)' },
  paracetamol: { priceUsdPerKg: 8, label: 'Market (commodity)' },
  ibuprofen: { priceUsdPerKg: 12, label: 'Market (OTC benchmark)' },
  aspirin: { priceUsdPerKg: 6, label: 'Market (commodity)' },
};

function getMarketPrice(
  drugName?: string | null,
  fromApi?: number | null
): { priceUsdPerKg: number; label: string } {
  if (typeof fromApi === 'number' && fromApi > 0) {
    return { priceUsdPerKg: fromApi, label: 'Market' };
  }
  if (!drugName?.trim()) return MOCK_COMPETITORS.default;
  const key = drugName.toLowerCase().replace(/\s+/g, '');
  for (const [k, v] of Object.entries(MOCK_COMPETITORS)) {
    if (k !== 'default' && key.includes(k)) return v;
  }
  return MOCK_COMPETITORS.default;
}

export const CompetitorIntelligenceCard: React.FC<CompetitorIntelligenceProps> = ({
  costPerKgUsd,
  drugName,
  marketPriceUsdPerKg,
}) => {
  if (costPerKgUsd == null || costPerKgUsd <= 0) return null;

  const market = getMarketPrice(drugName, marketPriceUsdPerKg);
  const marketPrice = market.priceUsdPerKg;
  const diff = costPerKgUsd - marketPrice;
  const isCompetitive = diff <= 0;
  const diffPercent = marketPrice > 0 ? ((diff / marketPrice) * 100).toFixed(1) : '0';

  return (
    <div className="w-full rounded-xl sm:rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden">
      <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-3">
        <span className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600 shrink-0">
          <TrendingDown size={18} />
        </span>
        <div className="min-w-0">
          <h2 className="text-base sm:text-lg font-bold text-slate-800">Competitor Intelligence — War Room</h2>
          <p className="text-slate-500 text-xs mt-0.5">Your cost vs. market price (e.g. Cipla, Dr. Reddy&apos;s)</p>
        </div>
      </div>
      <div className="p-4 sm:p-6 space-y-4">
        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Your cost (TEA)</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">${costPerKgUsd.toFixed(2)}/kg</p>
          </div>
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Market price</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">${marketPrice.toFixed(2)}/kg</p>
            <p className="text-xs text-slate-500 mt-0.5">{market.label}</p>
          </div>
        </div>

        <div
          className={`rounded-xl p-4 flex items-start gap-3 ${
            isCompetitive ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'
          }`}
        >
          {isCompetitive ? (
            <CheckCircle className="text-emerald-600 shrink-0 mt-0.5" size={22} />
          ) : (
            <AlertTriangle className="text-red-600 shrink-0 mt-0.5" size={22} />
          )}
          <div>
            <p className={`font-bold ${isCompetitive ? 'text-emerald-800' : 'text-red-800'}`}>
              {isCompetitive
                ? 'Project is competitive.'
                : 'Project is NOT competitive.'}
            </p>
            <p className={`text-sm mt-1 ${isCompetitive ? 'text-emerald-700' : 'text-red-700'}`}>
              {isCompetitive
                ? `Your cost is at or below market (${marketPrice}/kg). Margin headroom available.`
                : `Your cost is $${costPerKgUsd.toFixed(2)}/kg. Market price is $${marketPrice.toFixed(2)}/kg. You are ${diffPercent}% above market — consider process optimization or scale.`}
            </p>
          </div>
        </div>

        <p className="text-xs text-slate-500 italic">
          Market prices are illustrative. Replace with live competitor/pricing API for production.
        </p>
      </div>
    </div>
  );
};
