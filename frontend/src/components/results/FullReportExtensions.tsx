import React, { useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Cog, Calculator, MapPin, FileStack, CheckCircle2, Circle, Search,
} from 'lucide-react';
import Card from '../common/Card';
import { Link } from 'react-router-dom';

export type FullReportExtensionsData = {
  process_design?: string;
  techno_economic?: string;
  demographics_sites?: string;
};

interface FullReportExtensionsProps {
  data: FullReportExtensionsData | null | undefined;
  drugName: string;
  /** When extensions are missing (e.g. cached run before backend upgrade) */
  showEmptyHint?: boolean;
}

const AGENT_CHIPS = [
  { id: 'ProcessDesignAgent', label: 'Process design', key: 'process_design' as const },
  { id: 'TechnoEconomicAgent', label: 'Techno-economics', key: 'techno_economic' as const },
  { id: 'DemographicsPlantAgent', label: 'Demographics & sites', key: 'demographics_sites' as const },
  { id: 'ReportGenerator', label: 'Report assembly', key: null },
];

const SectionPanel: React.FC<{
  title: string;
  icon: React.ReactNode;
  markdown?: string;
  active: boolean;
}> = ({ title, icon, markdown, active }) => {
  if (!active || !markdown?.trim()) return null;
  return (
    <div className="rounded-xl border border-slate-200/90 bg-white/90 p-4 sm:p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-cyan-600">{icon}</span>
        <h4 className="text-base font-semibold text-slate-900">{title}</h4>
      </div>
      <div className="prose prose-sm prose-slate max-w-none prose-p:text-slate-600 prose-headings:text-slate-800 prose-strong:text-slate-900 prose-li:text-slate-600">
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </div>
    </div>
  );
};

const FullReportExtensions: React.FC<FullReportExtensionsProps> = ({
  data,
  drugName,
  showEmptyHint = true,
}) => {
  const [tab, setTab] = useState<'process' | 'tea' | 'demo'>('process');

  const hasAny = useMemo(
    () =>
      !!(data?.process_design?.trim() || data?.techno_economic?.trim() || data?.demographics_sites?.trim()),
    [data]
  );

  const filled = (key: keyof FullReportExtensionsData) => !!(data?.[key]?.trim());

  if (!hasAny) {
    if (!showEmptyHint) return null;
    return (
      <Card className="border-amber-100 bg-amber-50/40">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-slate-900 mb-1">Process, TEA & site analysis</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              This result has no <strong>unified report extensions</strong> yet (common for cached searches from an older
              pipeline). Run a <strong>fresh search</strong> for <span className="capitalize font-medium">{drugName}</span> to
              generate process design, techno-economics, and demographics sections.
            </p>
          </div>
          <Link
            to={`/search?q=${encodeURIComponent(drugName)}`}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-600 text-white text-sm font-semibold shadow-md shadow-cyan-500/20 hover:from-cyan-500 hover:to-teal-500 shrink-0"
          >
            <Search className="w-4 h-4" />
            New search
          </Link>
        </div>
      </Card>
    );
  }

  return (
    <Card className="border-cyan-100/90 bg-gradient-to-br from-white via-white to-cyan-50/50 overflow-hidden">
      <div className="flex flex-col lg:flex-row lg:items-start gap-6 mb-6">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-slate-900 mb-1">Unified intelligence report</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Process design, techno-economics, and demographics &mdash; the same dimensions as the legacy full-analysis
            dashboard, produced by dedicated post-scoring agents for{' '}
            <span className="font-medium text-slate-800 capitalize">{drugName}</span>.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 lg:justify-end">
          {AGENT_CHIPS.map((a) => {
            const ok = a.key ? filled(a.key) : hasAny;
            return (
              <span
                key={a.id}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium border bg-white/90 border-slate-200 text-slate-700"
              >
                {ok ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                ) : (
                  <Circle className="w-3.5 h-3.5 text-slate-300 shrink-0" />
                )}
                {a.label}
              </span>
            );
          })}
        </div>
      </div>

      {/* Sub-tabs (dash-style section switching) */}
      <div className="flex flex-wrap gap-2 p-1 rounded-xl bg-slate-100/80 border border-slate-200/80 mb-5">
        {(
          [
            { id: 'process' as const, label: 'Process design', icon: Cog, ok: filled('process_design') },
            { id: 'tea' as const, label: 'Techno-economics', icon: Calculator, ok: filled('techno_economic') },
            { id: 'demo' as const, label: 'Demographics & sites', icon: MapPin, ok: filled('demographics_sites') },
          ]
        ).map((t) => {
          const Icon = t.icon;
          const active = tab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                active
                  ? 'bg-white text-cyan-900 shadow-sm border border-cyan-200/80'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${t.ok ? 'text-teal-600' : 'text-slate-400'}`} />
              {t.label}
            </button>
          );
        })}
      </div>

      {tab === 'process' && (
        <SectionPanel
          title="Process design & CMC"
          icon={<Cog className="w-5 h-5" />}
          markdown={data?.process_design}
          active
        />
      )}
      {tab === 'tea' && (
        <SectionPanel
          title="Techno-economic snapshot"
          icon={<Calculator className="w-5 h-5" />}
          markdown={data?.techno_economic}
          active
        />
      )}
      {tab === 'demo' && (
        <SectionPanel
          title="Demographics & manufacturing footprint"
          icon={<MapPin className="w-5 h-5" />}
          markdown={data?.demographics_sites}
          active
        />
      )}

      <div className="mt-5 pt-4 border-t border-slate-100 flex items-center gap-2 text-[11px] text-slate-500">
        <FileStack className="w-3.5 h-3.5 text-cyan-600" />
        Sections are included in PDF export when generated from this search result.
      </div>
    </Card>
  );
};

export default FullReportExtensions;
