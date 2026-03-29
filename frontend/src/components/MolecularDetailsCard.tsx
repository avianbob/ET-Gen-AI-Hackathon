import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Molecule3DViewer } from './Molecule3DViewer';

export interface MolecularDetails {
  molecular_name?: string;
  molecular_family?: string;
  molecular_weight_g_per_mol?: number;
  brief_details?: string;
  structure_image_url?: string;
  molecular_weight_impact?: string;
  solubility?: string;
  solubility_why_it_matters?: string;
  lipophilicity_log_p?: string;
  lipophilicity_why_it_matters?: string;
  pka?: string;
  pka_why_it_matters?: string;
  melting_point?: string;
  melting_point_why_it_matters?: string;
  crystalline_nature?: string;
  crystalline_why_it_matters?: string;
  hygroscopicity?: string;
  hygroscopicity_why_it_matters?: string;
  chemical_stability?: string;
  chemical_stability_why_it_matters?: string;
  particle_size_surface_area?: string;
  particle_size_why_it_matters?: string;
  bcs_class?: string;
  permeability_notes?: string;
  permeability_why_it_matters?: string;
  solid_state_properties?: string;
  solid_state_why_it_matters?: string;
  excipient_compatibility?: string;
  excipient_why_it_matters?: string;
}

interface MolecularDetailsCardProps {
  data: MolecularDetails | null | undefined;
  /** Fallback name when data.molecular_name is missing */
  fallbackName?: string | null;
  /** Compact layout (e.g. when placed next to Feasibility Score) */
  compact?: boolean;
}

export const MolecularDetailsCard: React.FC<MolecularDetailsCardProps> = ({
  data,
  fallbackName,
  compact = false,
}) => {
  const [imageError, setImageError] = useState(false);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');

  const name = data?.molecular_name?.trim() || fallbackName?.trim() || 'Molecule';
  const family = data?.molecular_family?.trim() || '—';
  const weight = data?.molecular_weight_g_per_mol;
  // Use backend URL, or construct PubChem URL when we have drug name (fallback for cached results)
  const backendUrl = data?.structure_image_url;
  const pubchemFallback = name && name !== 'Molecule' ? `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent(name)}/PNG?image_size=400x400` : null;
  const imageUrl = backendUrl && !imageError ? backendUrl : pubchemFallback && !imageError ? pubchemFallback : null;

  if (!data && !fallbackName?.trim()) return null;

  /* Rectangular box: wider than tall (aspect 4/3). Heights for 3D to match. */
  const boxMaxW = compact ? 'max-w-[340px]' : 'max-w-[520px]';
  const viewerHeight = compact ? 255 : 390; /* 340*(3/4) ≈ 255, 520*(3/4) = 390 */

  return (
    <div className={`w-full min-w-0 rounded-xl sm:rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden flex flex-col ${compact ? 'min-h-[320px] sm:min-h-[360px] h-full' : ''}`}>
      <div className={`px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-3 ${compact ? 'px-4 py-3' : ''}`}>
        <span className={`rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600 ${compact ? 'w-6 h-6' : 'w-8 h-8'}`}>
          <i className={`fas fa-atom ${compact ? 'text-xs' : 'text-sm'}`}></i>
        </span>
        <h2 className={`font-bold text-slate-800 ${compact ? 'text-sm' : 'text-lg'}`}>Molecular details</h2>
      </div>
      <div className={`flex flex-col gap-6 ${compact ? 'p-4' : 'p-6'}`}>
        {/* Structure: 2D/3D rectangular box with label below */}
        <div className="flex flex-col items-center justify-start w-full">
          <div className="flex gap-1.5 mb-2">
            <button
              type="button"
              onClick={() => setViewMode('2d')}
              className={`rounded-lg font-semibold transition ${compact ? 'px-2 py-1 text-[10px]' : 'px-3 py-1.5 text-xs'} ${viewMode === '2d' ? 'bg-slate-700 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
            >
              2D
            </button>
            <button
              type="button"
              onClick={() => setViewMode('3d')}
              className={`rounded-lg font-semibold transition ${compact ? 'px-2 py-1 text-[10px]' : 'px-3 py-1.5 text-xs'} ${viewMode === '3d' ? 'bg-slate-700 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
            >
              3D
            </button>
          </div>
          {viewMode === '2d' ? (
            <div className={`w-full aspect-[4/3] rounded-xl border-2 border-slate-200 bg-slate-50 flex items-center justify-center overflow-hidden ${boxMaxW}`}>
              {imageUrl ? (
                <img
                  src={imageUrl}
                  alt={`Structure of ${name}`}
                  className="w-full h-full object-contain"
                  onError={() => setImageError(true)}
                />
              ) : (
                <div className="text-slate-400 flex flex-col items-center gap-1 p-2">
                  <i className={`fas fa-flask ${compact ? 'text-3xl' : 'text-4xl'}`}></i>
                  <span className="text-[10px] text-center">No image</span>
                </div>
              )}
            </div>
          ) : (
            <div className={`w-full ${boxMaxW}`} style={{ height: viewerHeight }}>
              <Molecule3DViewer moleculeName={name} height={viewerHeight} />
            </div>
          )}
          <p className={`text-slate-500 text-center mt-2 ${compact ? 'text-[10px]' : 'text-xs'}`}>Molecular structure</p>
        </div>

        {/* Drug details: molecular name, family, weight — below the structure (brief details shown in Dashboard above Symptoms) */}
        <div className="space-y-3 w-full">
          <div className={`grid gap-3 ${compact ? 'grid-cols-2 gap-x-4' : 'grid-cols-1 sm:grid-cols-2 gap-4'}`}>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Molecular name</p>
              <p className={`font-bold text-slate-800 mt-0.5 ${compact ? 'text-base' : 'text-xl mt-1'}`}>{name}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Molecular family</p>
              <p className={`font-medium text-slate-700 mt-0.5 ${compact ? 'text-sm' : 'text-lg mt-1'}`}>{family}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Molecular weight</p>
              <p className={`font-medium text-slate-700 mt-0.5 ${compact ? 'text-sm' : 'text-lg mt-1'}`}>
                {weight != null && weight > 0 ? `${weight.toFixed(1)} g/mol` : '—'}
              </p>
              {data?.molecular_weight_impact?.trim() && (
                <p className={`text-slate-500 mt-0.5 italic ${compact ? 'text-[10px]' : 'text-xs'}`}>{data.molecular_weight_impact}</p>
              )}
            </div>
          </div>

          {/* Physicochemical / API properties: 2 per row, info icon for "why it matters" */}
          <PhysicochemicalBlock compact={compact} data={data} />
        </div>
      </div>
    </div>
  );
};

/** Renders physicochemical properties: 2 per row, value only; info icon shows "why it matters" in popover */
function PhysicochemicalBlock({ data, compact }: { data: MolecularDetails | null | undefined; compact: boolean }) {
  const [openInfoIndex, setOpenInfoIndex] = useState<number | null>(null);
  const [popoverStyle, setPopoverStyle] = useState<{ top: number; left: number } | null>(null);
  const buttonRefs = useRef<Map<number, HTMLButtonElement>>(new Map());
  const t = (v: string | undefined) => (v?.trim() || null);
  const rows: { label: string; value: string | null; why: string | null }[] = [
    { label: 'Solubility', value: t(data?.solubility), why: t(data?.solubility_why_it_matters) },
    { label: 'Lipophilicity (Log P / Log D)', value: t(data?.lipophilicity_log_p), why: t(data?.lipophilicity_why_it_matters) },
    { label: 'pKa', value: t(data?.pka), why: t(data?.pka_why_it_matters) },
    { label: 'Melting point', value: t(data?.melting_point), why: t(data?.melting_point_why_it_matters) },
    { label: 'Crystalline vs amorphous', value: t(data?.crystalline_nature), why: t(data?.crystalline_why_it_matters) },
    { label: 'Hygroscopicity', value: t(data?.hygroscopicity), why: t(data?.hygroscopicity_why_it_matters) },
    { label: 'Chemical stability', value: t(data?.chemical_stability), why: t(data?.chemical_stability_why_it_matters) },
    { label: 'Particle size & surface area', value: t(data?.particle_size_surface_area), why: t(data?.particle_size_why_it_matters) },
    { label: 'Permeability (BCS)', value: [t(data?.bcs_class), t(data?.permeability_notes)].filter(Boolean).join(' — ') || null, why: t(data?.permeability_why_it_matters) },
    { label: 'Solid-state properties', value: t(data?.solid_state_properties), why: t(data?.solid_state_why_it_matters) },
    { label: 'Compatibility with excipients', value: t(data?.excipient_compatibility), why: t(data?.excipient_why_it_matters) },
  ].filter((r) => r.value || r.why);

  useEffect(() => {
    if (openInfoIndex === null) {
      setPopoverStyle(null);
      return;
    }
    const btn = buttonRefs.current.get(openInfoIndex);
    if (!btn) return;
    const updatePosition = () => {
      const rect = btn.getBoundingClientRect();
      const popoverWidth = 280;
      const popoverHeight = 120;
      const padding = 8;
      let left = rect.left;
      let top = rect.bottom + 6;
      if (left + popoverWidth + padding > window.innerWidth) left = window.innerWidth - popoverWidth - padding;
      if (left < padding) left = padding;
      if (top + popoverHeight + padding > window.innerHeight) top = rect.top - popoverHeight - 6;
      if (top < padding) top = padding;
      setPopoverStyle({ top, left });
    };
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(updatePosition);
    });
    return () => cancelAnimationFrame(id);
  }, [openInfoIndex]);

  if (rows.length === 0) return null;

  const textCls = compact ? 'text-xs' : 'text-sm';
  const labelCls = 'text-xs font-semibold text-slate-500 uppercase tracking-wider';

  return (
    <div className="border-t border-slate-200 pt-4 mt-2">
      <h3 className={`font-semibold text-slate-700 mb-3 ${compact ? 'text-sm' : 'text-base'}`}>Physicochemical & API properties</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
        {rows.map((row, i) => (
          <div key={i} className="flex items-start gap-1.5 min-w-0">
            <div className="flex-1 min-w-0 space-y-0.5">
              <p className={labelCls}>{row.label}</p>
              {row.value && <p className={`text-slate-700 ${textCls}`}>{row.value}</p>}
            </div>
            {row.why != null && (
              <>
                <button
                  ref={(el) => { if (el) buttonRefs.current.set(i, el); }}
                  type="button"
                  onClick={() => setOpenInfoIndex(openInfoIndex === i ? null : i)}
                  className="shrink-0 text-slate-400 hover:text-cyan-600 mt-0.5 p-1 rounded focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                  aria-label="Why it matters"
                >
                  <i className="fas fa-info-circle text-xs" />
                </button>
                {openInfoIndex === i && popoverStyle != null && createPortal(
                  <>
                    <div className="fixed inset-0 z-40" aria-hidden onClick={() => setOpenInfoIndex(null)} />
                    <div
                      className="fixed z-[200] w-[280px] max-h-[min(60vh,320px)] overflow-y-auto bg-slate-800 text-slate-100 text-xs p-3 rounded-lg shadow-xl border border-slate-600"
                      style={{ top: popoverStyle.top, left: popoverStyle.left }}
                    >
                      <p className="font-semibold text-cyan-200 mb-1">Why it matters</p>
                      <p className="leading-relaxed">{row.why}</p>
                    </div>
                  </>,
                  document.body
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
