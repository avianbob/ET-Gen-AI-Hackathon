import React from 'react';

interface Props {
  symptoms?: string[] | null;
  disease?: string | null;
  sideEffects?: string[] | string | null;
  /** Stack Symptoms / Disease / Side effects vertically (e.g. in narrow column) */
  vertical?: boolean;
}

/** Safely render a value as text: only strings/numbers; objects (e.g. { step_1, step_2 }) become — */
function toDisplayText(value: unknown): string {
  if (value == null) return '—';
  if (typeof value === 'string') return value.trim() || '—';
  if (typeof value === 'number') return String(value);
  if (Array.isArray(value)) return value.map((v) => (typeof v === 'string' ? v : String(v))).filter(Boolean).join(', ') || '—';
  return '—'; // object or other: do not render as React child
}

export const SymptomsDiseaseSideEffectsSummary: React.FC<Props> = ({
  symptoms,
  disease,
  sideEffects,
  vertical = false,
}) => {
  const symptomsStr = Array.isArray(symptoms)
    ? symptoms.map((s) => (typeof s === 'string' ? s : typeof s === 'number' ? String(s) : '')).filter(Boolean).join(', ') || '—'
    : toDisplayText(symptoms);
  const diseaseStr = toDisplayText(disease);
  const sideEffectsStr = Array.isArray(sideEffects)
    ? sideEffects.map((s) => (typeof s === 'string' ? s : typeof s === 'number' ? String(s) : '')).filter(Boolean).join(', ') || '—'
    : toDisplayText(sideEffects);

  const content = (
    <>
      <div className={vertical ? 'border-b border-slate-100 pb-3' : 'border-r border-slate-100 sm:border-r last:border-r-0 pr-4'}>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Symptoms</p>
        <p className="text-slate-800 font-medium text-sm">{symptomsStr || '—'}</p>
      </div>
      <div className={vertical ? 'border-b border-slate-100 py-3' : 'border-r border-slate-100 sm:border-r last:border-r-0 pr-4'}>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Disease</p>
        <p className="text-slate-800 font-medium text-sm">{diseaseStr}</p>
      </div>
      <div className={vertical ? 'pt-3' : ''}>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Side effects</p>
        <p className="text-slate-800 font-medium text-sm">{sideEffectsStr}</p>
      </div>
    </>
  );

  return (
    <div className="bg-white rounded-xl shadow border border-slate-100 p-4 h-full flex flex-col min-h-0">
      <div className={vertical ? 'flex flex-col gap-0 flex-1 min-h-0' : 'grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm'}>
        {content}
      </div>
    </div>
  );
};
