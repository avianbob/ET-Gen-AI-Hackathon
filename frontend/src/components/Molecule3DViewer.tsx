import React, { useEffect, useRef, useState } from 'react';

declare global {
  interface Window {
    $3Dmol?: {
      createViewer: (element: HTMLDivElement, options?: Record<string, unknown>) => {
        addModel: (data: string, type: string) => unknown;
        setStyle: (style: Record<string, unknown>, spec: Record<string, unknown>) => void;
        zoomTo: () => void;
        render: () => void;
        clear: () => void;
      };
    };
  }
}

interface Molecule3DViewerProps {
  /** Molecule name for PubChem lookup (e.g. Paracetamol, Roflumilast) */
  moleculeName: string | null | undefined;
  /** Optional SMILES or SDF string; if provided, skips PubChem fetch */
  sdfOrSmiles?: string | null;
  className?: string;
  height?: number;
}

/** Fetches 3D SDF from PubChem by compound name and renders with 3dmol.js */
export const Molecule3DViewer: React.FC<Molecule3DViewerProps> = ({
  moleculeName,
  sdfOrSmiles,
  className = '',
  height = 280,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const el = containerRef.current;
    const name = moleculeName?.trim();
    if (!el || (!name && !sdfOrSmiles?.trim())) {
      setLoading(false);
      setError(name ? null : 'No molecule name provided');
      return;
    }

    const createViewer = window.$3Dmol?.createViewer;
    if (!createViewer) {
      setLoading(false);
      setError('3D viewer library not loaded');
      return;
    }

    let cancelled = false;
    setError(null);
    setLoading(true);

    const renderSdf = (sdfContent: string) => {
      if (cancelled || !el) return;
      try {
        const viewer = createViewer(el, { backgroundColor: 'white' });
        viewer.addModel(sdfContent, 'sdf');
        viewer.setStyle({}, { stick: { radius: 0.2 }, sphere: { scale: 0.3 } });
        viewer.zoomTo();
        viewer.render();
      } catch (e) {
        if (!cancelled) setError('Failed to render 3D model');
      }
      setLoading(false);
    };

    if (sdfOrSmiles?.trim()) {
      // If it looks like SDF (contains V2000 or M  END), use as SDF; else could add MOL/SMILES handling
      const sdf = sdfOrSmiles.trim();
      if (sdf.includes('V2000') || sdf.includes('M  END')) {
        renderSdf(sdf);
        return;
      }
    }

    const encoded = encodeURIComponent(name!);
    const url = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encoded}/record/SDF?record_type=3d`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error('PubChem 3D not available');
        return res.text();
      })
      .then((text) => {
        if (!cancelled && text?.trim()) renderSdf(text);
        else if (!cancelled) setError('No 3D structure found');
      })
      .catch(() => {
        if (!cancelled) setError('Could not load 3D structure');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [moleculeName, sdfOrSmiles]);

  return (
    <div className={`relative rounded-xl border-2 border-slate-200 bg-slate-50 overflow-hidden ${className}`} style={{ height }}>
      <div ref={containerRef} className="w-full h-full" style={{ minHeight: height }} />
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-100/80">
          <span className="text-sm text-slate-500">Loading 3D model…</span>
        </div>
      )}
      {error && !loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-100/90 p-4">
          <span className="text-sm text-slate-500 text-center">{error}</span>
        </div>
      )}
    </div>
  );
};
