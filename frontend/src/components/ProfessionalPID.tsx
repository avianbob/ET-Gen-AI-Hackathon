import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import html2canvas from 'html2canvas';
import { Info, DollarSign, Activity, Settings, TrendingUp, ZoomIn, ZoomOut, Maximize, Download, RefreshCw } from 'lucide-react';

/** Info button that explains what a Process Diagram is — always visible, never shrinks */
const ProcessDiagramInfoButton: React.FC = () => {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative inline-block shrink-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-8 h-8 sm:w-7 sm:h-7 rounded-full bg-cyan-100 hover:bg-cyan-200 text-cyan-600 hover:text-cyan-700 flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50 touch-target border border-cyan-200/60"
        aria-label="What is a Process Diagram?"
        title="What is a Process Diagram?"
      >
        <Info size={18} className="sm:w-4 sm:h-4" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-[100]" aria-hidden onClick={() => setOpen(false)} />
          <div className="absolute left-0 bottom-full mb-2 z-[110] w-72 bg-slate-800 text-slate-100 text-xs p-4 rounded-lg shadow-xl border border-slate-600">
            <p className="font-bold text-cyan-200 mb-2">What is a Process Diagram?</p>
            <p className="leading-relaxed">
              A Process and Instrumentation Diagram (P&amp;ID) shows the flow of a pharmaceutical manufacturing process: feed tanks, reactors, separators, and crystallizers. Equipment tags (e.g. R-101, S-201) and control loops (temperature, pressure) follow engineering standards. This view is derived from your molecule and scale.
            </p>
          </div>
        </>
      )}
    </div>
  );
};

/** TEA data from TechnoEconomicAgent; used to show cost badges on P&ID equipment. */
interface TEAData {
  equipment_costs?: Record<string, { cost_million_usd: number }>;
  total_capex_million_usd?: number;
  cost_per_kg_usd?: number;
  internal_rate_of_return?: number;
}

interface PIDData {
  equipment?: Array<{
    id: string;
    type: string;
    name: string;
    temperature: number;
    pressure: number;
    flow_rate?: number;
    specs?: Record<string, any>;
  }>;
  control_loops?: Array<{
    tag: string;
    description: string;
    setpoint: number;
    range: number[];
    unit: string;
  }>;
  reactor?: {
    temperature: number;
    pressure: number;
    volume: number;
  };
  process_conditions?: {
    operating_temperature_range?: string;
    operating_pressure_range?: string;
    residence_time?: string;
    number_of_reactors?: number;
    reactor_types?: string[];
    number_of_steps?: number;
    synthesis_route?: string;
  };
  material_handling?: {
    reactants?: string[];
    catalysts?: string[];
    intermediates?: string[];
    products?: string[];
    recycle_streams?: string[];
    target_molecule?: string;
    synthesis_route?: string;
  };
}

interface ProfessionalPIDProps {
  pidData?: PIDData;
  teaData?: TEAData | null;
  drugName?: string | null;
}

function getDisplayDrugName(
  drugName: string | null | undefined,
  targetMolecule: string | undefined
): string {
  const fromProp = drugName?.trim();
  if (fromProp) return fromProp;
  if (targetMolecule?.trim()) return targetMolecule.trim();
  return 'API';
}

// --- ANIMATIONS & STYLES ---
const flowAnimationStyles = `
  @keyframes flowDash {
    to { stroke-dashoffset: -20; }
  }
  .animate-flow {
    animation: flowDash 1s linear infinite;
  }
  .lcd-text {
    font-family: 'Courier New', Courier, monospace;
    letter-spacing: -0.5px;
  }
`;

/** Format specs value for display */
function formatSpec(value: unknown): string {
  if (value == null) return '—';
  if (typeof value === 'string' || typeof value === 'number') return String(value);
  return JSON.stringify(value);
}

const CARD_WIDTH = 256;
const CARD_GAP = 8;
const MIN_VIEWPORT_PAD = 8;

/** Wrapper for equipment that handles Hover Cards and Cost Badges. Uses a portal for the hover card so it is never cut by the header or canvas. */
const EquipmentNode: React.FC<{
  eq: { id: string; name: string; type?: string; temperature: number; pressure: number; flow_rate?: number; specs?: Record<string, any> };
  costData?: { cost_million_usd: number };
  children: React.ReactNode;
}> = ({ eq, costData, children }) => {
  const specs = eq.specs || {};
  const hasSpecs = Object.keys(specs).length > 0;
  const nodeRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState(false);
  const [cardStyle, setCardStyle] = useState<React.CSSProperties>({});

  useEffect(() => {
    if (!hovered || !nodeRef.current || typeof document === 'undefined') return;
    const el = nodeRef.current;
    const rect = el.getBoundingClientRect();
    const preferAbove = rect.top > 280;
    const left = Math.max(MIN_VIEWPORT_PAD, Math.min(window.innerWidth - CARD_WIDTH - MIN_VIEWPORT_PAD, rect.left + rect.width / 2 - CARD_WIDTH / 2));
    let top: number;
    if (preferAbove) {
      top = rect.top - CARD_GAP;
      top = top - 320;
      if (top < MIN_VIEWPORT_PAD) top = rect.bottom + CARD_GAP;
    } else {
      top = rect.bottom + CARD_GAP;
    }
    top = Math.max(MIN_VIEWPORT_PAD, Math.min(window.innerHeight - 340, top));
    setCardStyle({ position: 'fixed', left, top, zIndex: 9999, width: CARD_WIDTH });
  }, [hovered]);

  const cardContent = (
    <div className="bg-slate-900/95 backdrop-blur-md text-slate-100 p-3 rounded-lg shadow-2xl border border-slate-700 text-xs w-64 max-h-[80vh] overflow-y-auto">
      <div className="flex justify-between items-start border-b border-slate-700 pb-2 mb-2">
        <span className="font-bold text-white text-sm">{eq.name}</span>
        <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">{eq.id}</span>
      </div>
      {eq.type && (
        <div className="mb-2">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">Type</span>
          <span className="block font-mono text-slate-200">{eq.type}</span>
        </div>
      )}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2">
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">Temp</span>
          <span className="font-mono text-amber-400 font-bold">{eq.temperature}°C</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">Pressure</span>
          <span className="font-mono text-cyan-400 font-bold">{eq.pressure} bar</span>
        </div>
        {eq.flow_rate != null && (
          <div className="col-span-2 flex flex-col">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider">Flow rate</span>
            <span className="font-mono text-slate-200">{eq.flow_rate} L/hr</span>
          </div>
        )}
      </div>
      {hasSpecs && (
        <div className="mt-2 pt-2 border-t border-slate-700 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">Specs</span>
          {(['volume', 'material', 'type', 'residence_time', 'length', 'diameter'] as const).map((key) =>
            specs[key] != null && specs[key] !== '' ? (
              <div key={key} className="flex justify-between gap-2">
                <span className="text-slate-400 capitalize">{key.replace('_', ' ')}</span>
                <span className="font-mono text-slate-200 text-right">{formatSpec(specs[key])}</span>
              </div>
            ) : null
          )}
        </div>
      )}
      {costData != null && (
        <div className="mt-2 pt-2 border-t border-slate-800 flex justify-between items-center">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">Est. Cost</span>
          <span className="font-mono text-emerald-400 font-bold">${costData.cost_million_usd.toFixed(2)}M</span>
        </div>
      )}
    </div>
  );

  return (
    <>
      <div
        ref={nodeRef}
        className="relative group flex flex-col items-center p-2 z-10 overflow-visible"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {/* The SVG Icon - no overlapping badge */}
        <div className="transform transition-all duration-300 group-hover:scale-105 group-hover:drop-shadow-xl cursor-pointer">
          {children}
        </div>

        {/* ID Label (Always visible below) */}
        <div className="mt-2 px-2 py-0.5 bg-slate-100 border border-slate-300 rounded text-[9px] font-bold text-slate-700 shadow-sm font-mono tracking-tighter">
          {eq.id}
        </div>

        {/* Cost Badge - below ID label so it never overlaps icon or name */}
        {costData != null && (
          <div className="mt-1 bg-gradient-to-br from-emerald-500 to-emerald-700 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-md border border-emerald-400 flex items-center gap-0.5 w-fit">
            <DollarSign size={8} />
            {costData.cost_million_usd.toFixed(2)}M
          </div>
        )}
      </div>

      {hovered && typeof document !== 'undefined' &&
        createPortal(
          <div style={cardStyle} className="animate-in fade-in duration-150" role="tooltip">
            {cardContent}
          </div>,
          document.body
        )}
    </>
  );
};

// --- SVG ENGINEERING SYMBOLS ---

const TankSVG: React.FC<{ width?: number; height?: number; fill?: string }> = ({ width = 60, height = 40, fill = "#f8fafc" }) => (
  <svg width={width} height={height} viewBox="0 0 60 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Main Body */}
    <path d="M10 5 H50 V35 H10 V5 Z" fill={fill} stroke="#475569" strokeWidth="2"/>
    {/* Curved Ends (Caps) */}
    <path d="M10 5 C4 5 4 35 10 35" fill={fill} stroke="#475569" strokeWidth="2"/>
    <path d="M50 5 C56 5 56 35 50 35" fill={fill} stroke="#475569" strokeWidth="2"/>
    {/* Detail lines to show volume/curvature */}
    <path d="M50 5 C46 5 46 35 50 35" stroke="#cbd5e1" strokeWidth="1" strokeDasharray="2 2"/>
  </svg>
);

const ReactorSVG: React.FC<{ width?: number; height?: number; fill?: string }> = ({ width = 50, height = 80, fill = "#f8fafc" }) => (
  <svg width={width} height={height} viewBox="0 0 50 80" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Legs */}
    <path d="M10 70 L5 80" stroke="#475569" strokeWidth="2" strokeLinecap="round"/>
    <path d="M40 70 L45 80" stroke="#475569" strokeWidth="2" strokeLinecap="round"/>
    
    {/* Main Vessel */}
    <path d="M10 15 H40 V65 C40 73.2843 33.2843 80 25 80 C16.7157 80 10 73.2843 10 65 V15 Z" fill={fill} stroke="#475569" strokeWidth="2"/>
    
    {/* Top Head */}
    <path d="M10 15 C10 6 40 6 40 15" fill={fill} stroke="#475569" strokeWidth="2"/>
    
    {/* Agitator Motor */}
    <rect x="20" y="0" width="10" height="8" rx="1" fill="#cbd5e1" stroke="#475569" strokeWidth="2"/>
    <line x1="25" y1="8" x2="25" y2="15" stroke="#475569" strokeWidth="2"/>
    
    {/* Impeller (Internal - dashed or lighter to show it's inside) */}
    <line x1="25" y1="15" x2="25" y2="60" stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="2 1"/>
    <path d="M15 60 L35 60" stroke="#94a3b8" strokeWidth="1.5"/>
    <path d="M15 55 L35 65" stroke="#94a3b8" strokeWidth="1.5"/>

    {/* Jacket indicators */}
    <path d="M8 20 V60" stroke="#e2e8f0" strokeWidth="1"/>
    <path d="M42 20 V60" stroke="#e2e8f0" strokeWidth="1"/>
  </svg>
);

const SeparatorSVG: React.FC<{ width?: number; height?: number; fill?: string }> = ({ width = 40, height = 70, fill = "#f8fafc" }) => (
  <svg width={width} height={height} viewBox="0 0 40 70" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Legs */}
    <path d="M8 60 L4 70" stroke="#475569" strokeWidth="2"/>
    <path d="M32 60 L36 70" stroke="#475569" strokeWidth="2"/>

    {/* Body */}
    <rect x="8" y="10" width="24" height="50" rx="2" fill={fill} stroke="#475569" strokeWidth="2"/>
    <path d="M8 10 C8 5 32 5 32 10" fill={fill} stroke="#475569" strokeWidth="2"/>
    <path d="M8 60 C8 65 32 65 32 60" fill={fill} stroke="#475569" strokeWidth="2"/>
    
    {/* Internal Baffles/Plates */}
    <line x1="8" y1="25" x2="25" y2="25" stroke="#cbd5e1" strokeWidth="1"/>
    <line x1="15" y1="35" x2="32" y2="35" stroke="#cbd5e1" strokeWidth="1"/>
    <line x1="8" y1="45" x2="25" y2="45" stroke="#cbd5e1" strokeWidth="1"/>
  </svg>
);

const CrystallizerSVG: React.FC<{ width?: number; height?: number; fill?: string }> = ({ width = 50, height = 70, fill = "#f8fafc" }) => (
  <svg width={width} height={height} viewBox="0 0 50 70" fill="none" xmlns="http://www.w3.org/2000/svg">
     {/* Conical Bottom */}
    <path d="M10 40 L25 65 L40 40" fill={fill} stroke="#475569" strokeWidth="2" strokeLinejoin="round"/>
    {/* Main Body */}
    <rect x="10" y="10" width="30" height="30" fill={fill} stroke="#475569" strokeWidth="2"/>
    {/* Top */}
    <path d="M10 10 C10 5 40 5 40 10" fill={fill} stroke="#475569" strokeWidth="2"/>
    
    {/* Cooling Coil Sketch */}
    <path d="M14 15 C14 15 36 18 36 20 C36 22 14 22 14 25 C14 28 36 28 36 30" stroke="#3b82f6" strokeWidth="1.5" strokeOpacity="0.5" fill="none"/>
  </svg>
);


/** ISA-style instrument bubble */
const InstrumentTag: React.FC<{ type: string; tag: string; value: number; unit: string; colorClass: string }> = ({ type, tag, value, unit, colorClass }) => (
  <div className="relative group z-20">
    <div className="w-10 h-10 bg-white border-2 border-slate-600 rounded-full flex flex-col items-center justify-center shadow-md relative overflow-hidden transition-transform hover:scale-110">
      {/* Horizontal Line for standard ISA bubble (Locally mounted vs control room usually denotes line, simplifying here) */}
      <div className="absolute top-1/2 w-full h-px bg-slate-300"></div>
      <span className="text-[10px] font-bold text-slate-800 relative -top-0.5 leading-none">{type}</span>
      <span className="text-[7px] font-mono text-slate-500 relative -bottom-0.5 leading-none">{tag.split('-')[1] || tag}</span>
    </div>
    
    {/* Digital Readout Tooltip */}
    <div className={`absolute left-1/2 -translate-x-1/2 -top-8 px-2 py-1 ${colorClass} text-white text-[10px] font-mono rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-30`}>
      {value} {unit}
      <div className={`absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-${colorClass.split(' ')[0].replace('bg-', '')}`} />
    </div>
  </div>
);

/** Control Valve Symbol */
const ControlValve: React.FC<{ tag: string }> = ({ tag }) => (
  <div className="flex flex-col items-center justify-center relative w-8">
    <div className="relative h-6 w-8 flex items-center justify-center">
      {/* Bowtie shape for valve */}
      <svg width="24" height="14" viewBox="0 0 24 14" fill="#cbd5e1" stroke="#475569" strokeWidth="1.5">
        <path d="M0 0 L12 7 L0 14 V0 Z" />
        <path d="M24 0 L12 7 L24 14 V0 Z" />
        {/* Stem */}
        <line x1="12" y1="7" x2="12" y2="-5" stroke="#475569" strokeWidth="1.5" />
        {/* Actuator Top */}
        <path d="M7 -5 Q12 -10 17 -5" stroke="#475569" strokeWidth="1.5" fill="none"/>
      </svg>
    </div>
    <span className="text-[7px] font-mono text-slate-500 mt-0.5">{tag}</span>
  </div>
);

/** Animated Flow Line */
const FlowLine: React.FC<{ width?: number; vertical?: boolean; label?: string }> = ({ width = 60, vertical = false, label }) => {
  const markerId = `arrow-${React.useId().replace(/:/g, '')}`;
  return (
    <div className={`relative flex items-center justify-center ${vertical ? 'h-16 w-4 flex-col' : 'h-4'}`} style={{ width: vertical ? 'auto' : width }}>
      {label && (
        <span className={`absolute ${vertical ? 'left-4 top-1/2 -translate-y-1/2' : '-top-3'} text-[8px] uppercase font-bold text-slate-400 whitespace-nowrap`}>
          {label}
        </span>
      )}
      <svg className="overflow-visible w-full h-full" viewBox={vertical ? "0 0 20 80" : "0 0 100 20"} preserveAspectRatio="none">
        <defs>
          <marker id={markerId} viewBox="0 0 12 12" refX="10" refY="6" markerWidth="10" markerHeight="10" orient="auto-start-reverse">
            <path d="M 0 0 L 12 6 L 0 12 z" fill="#475569" />
          </marker>
        </defs>
        {vertical ? (
          <>
            <line x1="10" y1="0" x2="10" y2="80" stroke="#94a3b8" strokeWidth="3" />
            <line x1="10" y1="0" x2="10" y2="80" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4 4" className="animate-flow" />
            <line x1="10" y1="64" x2="10" y2="80" stroke="#475569" strokeWidth="4" markerEnd={`url(#${markerId})`} />
          </>
        ) : (
          <>
            <line x1="0" y1="10" x2="100" y2="10" stroke="#94a3b8" strokeWidth="3" />
            <line x1="0" y1="10" x2="100" y2="10" stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4 4" className="animate-flow" />
            <line x1="80" y1="10" x2="100" y2="10" stroke="#475569" strokeWidth="4" markerEnd={`url(#${markerId})`} />
          </>
        )}
      </svg>
    </div>
  );
};


export const ProfessionalPID: React.FC<ProfessionalPIDProps> = ({ pidData, teaData, drugName }) => {
  const [zoom, setZoom] = useState(100);
  const [showTea, setShowTea] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);

  const displayDrugName = getDisplayDrugName(
    drugName ?? null,
    pidData?.material_handling?.target_molecule
  );

  const defaultEquipment = [
    { id: 'FEED-01', type: 'Feed Tank', name: 'Reactant A', temperature: 25, pressure: 1.0, specs: { volume: '2000L' } },
    { id: 'FEED-02', type: 'Feed Tank', name: 'Reactant B', temperature: 25, pressure: 1.0, specs: { volume: '2000L' } },
  ];

  const defaultReactor = { id: 'R-101', type: 'CSTR Reactor', name: 'Main Reactor', temperature: 150, pressure: 6.5, specs: { volume: '5000L' } };
  const defaultSeparator = { id: 'S-201', type: 'Separator', name: 'Separator', temperature: 120, pressure: 5.5, specs: { type: 'Decanter' } };
  const defaultCrystallizer = { id: 'C-301', type: 'Crystallizer', name: 'Crystallizer', temperature: 20, pressure: 5.0, specs: { type: 'Cooling' } };

  const equipment = pidData?.equipment || [...defaultEquipment, defaultReactor, defaultSeparator, defaultCrystallizer];
  const controlLoops = pidData?.control_loops || [];

  const feedTanks = equipment.filter(eq => eq.type.includes('Feed') || eq.id.includes('FEED'));
  const reactors = equipment.filter(eq => eq.id.startsWith('R-')).sort((a, b) => a.id.localeCompare(b.id));
  const separators = equipment.filter(eq => eq.id.startsWith('S-')).sort((a, b) => a.id.localeCompare(b.id));
  const crystallizerEq = equipment.find(eq => eq.type.includes('Crystallizer') || eq.id.startsWith('C-')) || defaultCrystallizer;

  /** Format IRR for display (backend may send 0–1 or 0–100). */
  const formatIRR = (val: number | undefined | null): string => {
    if (val == null || Number.isNaN(val)) return '—';
    const pct = val > 1 ? val : val * 100;
    if (pct <= 0) return '—';
    return `${Math.min(99.9, pct).toFixed(1)}%`;
  };

  const containerRef = useRef<HTMLDivElement>(null);

  const handleDownload = async () => {
    const el = containerRef.current;
    if (!el) return;
    try {
      const canvas = await html2canvas(el, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#f8fafc',
        windowWidth: el.scrollWidth,
        windowHeight: el.scrollHeight,
      });
      const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png', 1));
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PID_Diagram_${(displayDrugName || 'Process').replace(/\s+/g, '_')}.png`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('P&ID image download failed', e);
      alert('Failed to download diagram image. Please try again.');
    }
  };

  return (
    <div ref={containerRef} id="pid-diagram-section" className="print-pid-only flex flex-col h-full bg-slate-50 border border-slate-200 rounded-xl shadow-sm font-sans">
      <style>{flowAnimationStyles}</style>
      
      {/* Header Toolbar - rounded-t-xl and overflow-visible so info icon is never clipped by container */}
      <div className="px-3 sm:px-6 py-3 sm:py-4 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 z-20 overflow-visible rounded-t-xl">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 overflow-visible">
          <span className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600 shrink-0">
            <Settings size={16} className="sm:w-[18px] sm:h-[18px]" />
          </span>
          <div className="relative min-w-0 flex-1 overflow-visible pr-3">
            <div className="flex items-center gap-2 min-w-0 overflow-visible">
              <h2 className="text-base sm:text-lg font-bold text-slate-800 truncate min-w-0">Process Diagram</h2>
              <ProcessDiagramInfoButton />
            </div>
            <div className="flex items-center gap-2 text-[10px] sm:text-xs text-slate-500 font-mono mt-0.5 flex-wrap">
              <span className="bg-slate-200/80 px-1.5 py-0.5 rounded">ID: {displayDrugName.substring(0,8).toUpperCase()}</span>
              {teaData ? <span className="text-teal-600 font-bold flex items-center gap-1"><DollarSign size={8}/> ECO-OPTIMIZED</span> : <span>STD-PROCESS</span>}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
          <div className="flex items-center bg-slate-100 rounded-lg p-1">
            <button type="button" onClick={() => setZoom(Math.max(50, zoom - 10))} className="p-1.5 hover:bg-white rounded shadow-sm text-slate-600 transition touch-target min-h-[36px]"><ZoomOut size={14} /></button>
            <span className="text-[10px] font-bold w-8 sm:w-10 text-center text-slate-700">{zoom}%</span>
            <button type="button" onClick={() => setZoom(Math.min(150, zoom + 10))} className="p-1.5 hover:bg-white rounded shadow-sm text-slate-600 transition touch-target min-h-[36px]"><ZoomIn size={14} /></button>
          </div>
          
          <button 
            type="button"
            onClick={() => setShowTea(!showTea)}
            className={`flex items-center gap-2 px-2.5 sm:px-3 py-1.5 rounded-lg text-[10px] sm:text-xs font-bold transition border touch-target min-h-[36px] ${showTea ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-white border-slate-200 text-slate-600'}`}
          >
            <Activity size={14} />
            <span className="hidden sm:inline">{showTea ? 'Hide Economics' : 'Show Economics'}</span>
          </button>

          <button type="button" onClick={handleDownload} className="p-2 text-slate-500 hover:text-slate-800 transition touch-target min-h-[36px]" title="Download P&ID as image (PNG)">
            <Download size={16} />
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div 
        ref={canvasRef}
        className="flex-1 overflow-auto relative bg-slate-50 rounded-b-xl"
        style={{
          backgroundImage: 'linear-gradient(#e2e8f0 1px, transparent 1px), linear-gradient(90deg, #e2e8f0 1px, transparent 1px)',
          backgroundSize: '20px 20px'
        }}
      >
        {/* Economics Overlay */}
        {showTea && teaData && (
          <div className="absolute top-4 right-4 z-40 bg-white/90 backdrop-blur border border-amber-200 p-4 rounded-xl shadow-lg w-64 animate-in fade-in slide-in-from-top-4">
            <div className="flex items-center gap-2 text-amber-800 font-bold text-xs mb-3 border-b border-amber-100 pb-2">
              <TrendingUp size={14} /> ECONOMIC ANALYSIS
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-end">
                <span className="text-[10px] text-slate-500 font-bold uppercase">Total Capex</span>
                <span className="text-sm font-mono font-bold text-slate-800">${teaData.total_capex_million_usd?.toFixed(1) ?? '0.0'}M</span>
              </div>
              <div className="flex justify-between items-end">
                <span className="text-[10px] text-slate-500 font-bold uppercase">Unit Cost</span>
                <span className="text-sm font-mono font-bold text-emerald-600">${teaData.cost_per_kg_usd?.toFixed(2) ?? '0.00'}/kg</span>
              </div>
              {(() => {
                const irr = teaData.internal_rate_of_return;
                const pct = irr != null && !Number.isNaN(irr) ? (irr > 1 ? irr : irr * 100) : 0;
                if (pct >= 99.5) return null;
                return (
                  <>
                    <div className="w-full bg-slate-100 rounded-full h-1.5 mt-1 overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${Math.min(pct, 100)}%` }}></div>
                    </div>
                    <div className="text-[9px] text-center text-slate-400">IRR: {formatIRR(irr)}</div>
                  </>
                );
              })()}
            </div>
          </div>
        )}

        {/* Diagram Content - overflow-visible so hover info boxes are not clipped */}
        <div 
          className="min-w-full min-h-full flex items-center justify-center p-4 sm:p-6 md:p-10 overflow-visible"
          style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'center center' }}
        >
          <div className="flex items-center gap-0 overflow-visible">
            
            {/* 1. Feed Section */}
            <div className="flex flex-col gap-8 items-end relative">
              {feedTanks.map((tank, i) => (
                <div key={tank.id} className="flex items-center gap-4">
                  <EquipmentNode eq={tank} costData={teaData?.equipment_costs?.[tank.id]}>
                    <TankSVG />
                  </EquipmentNode>
                  <div className="flex flex-col items-center">
                    <InstrumentTag type="FT" tag={`FT-0${i+1}`} value={120} unit="L/hr" colorClass="bg-cyan-500" />
                    <ControlValve tag={`FV-0${i+1}`} />
                  </div>
                  <FlowLine width={40} />
                </div>
              ))}
              {/* Manifold line joining feeds */}
              <div className="absolute right-[-20px] top-[30px] bottom-[30px] border-r-4 border-slate-400 w-4 rounded-r-lg"></div>
            </div>

            {/* Connection to Reactor */}
            <div className="w-12">
               <FlowLine width={48} label="Mixed Feed" />
            </div>

            {/* 2. Reaction Section */}
            {reactors.map((reactor) => (
              <React.Fragment key={reactor.id}>
                <div className="flex flex-col items-center gap-4 relative px-4 bg-slate-100/50 rounded-xl border border-dashed border-slate-300 py-6 mx-2">
                   <div className="absolute -top-3 left-4 text-[9px] font-bold text-slate-400 uppercase tracking-widest bg-slate-50 px-2">Reaction Zone</div>
                   
                   {/* Top Instruments */}
                   <div className="flex gap-4 mb-2">
                      <InstrumentTag type="TIC" tag={`TIC-${reactor.id.split('-')[1]}`} value={reactor.temperature} unit="°C" colorClass="bg-red-500" />
                      <InstrumentTag type="PIC" tag={`PIC-${reactor.id.split('-')[1]}`} value={reactor.pressure} unit="bar" colorClass="bg-cyan-600" />
                   </div>

                   <EquipmentNode eq={reactor} costData={teaData?.equipment_costs?.[reactor.id]}>
                      <ReactorSVG />
                   </EquipmentNode>
                </div>
                <FlowLine width={60} label="Effluent" />
              </React.Fragment>
            ))}

            {/* 3. Separation Section */}
            {separators.map((sep) => (
              <React.Fragment key={sep.id}>
                <div className="flex flex-col items-center gap-4 mx-2">
                   <EquipmentNode eq={sep} costData={teaData?.equipment_costs?.[sep.id]}>
                      <SeparatorSVG />
                   </EquipmentNode>
                   <div className="flex gap-2">
                      <InstrumentTag type="LIC" tag={`LIC-${sep.id.split('-')[1]}`} value={55} unit="%" colorClass="bg-amber-500" />
                      <ControlValve tag={`LV-${sep.id.split('-')[1]}`} />
                   </div>
                </div>
                <FlowLine width={60} />
              </React.Fragment>
            ))}

            {/* 4. Crystallization */}
            <div className="flex flex-col items-center gap-4 mx-2 bg-slate-100/50 rounded-xl border border-dashed border-slate-300 py-6 px-4 relative">
               <div className="absolute -top-3 left-4 text-[9px] font-bold text-slate-400 uppercase tracking-widest bg-slate-50 px-2">Purification</div>
               <EquipmentNode eq={crystallizerEq} costData={teaData?.equipment_costs?.[crystallizerEq.id]}>
                  <CrystallizerSVG />
               </EquipmentNode>
               <InstrumentTag type="TIC" tag="TIC-301" value={crystallizerEq.temperature} unit="°C" colorClass="bg-cyan-600" />
            </div>

            <FlowLine width={50} label="Product" />

            {/* 5. Final Product Tank */}
            <div className="flex flex-col items-center p-4 bg-emerald-50 border border-emerald-200 rounded-xl shadow-sm">
               <div className="w-16 h-16 bg-white border-2 border-emerald-400 rounded-full flex items-center justify-center mb-2 shadow-inner">
                  <RefreshCw className="text-emerald-500 animate-spin-slow" size={24} />
               </div>
               <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider text-center max-w-[100px] leading-tight">
                 {displayDrugName}
               </span>
               <div className="mt-1 px-2 py-0.5 bg-emerald-200 text-emerald-900 text-[9px] font-mono rounded">99.8% Purity</div>
            </div>

          </div>
        </div>

        {/* Legend Footer - high z-index so it stays on top and doesn't get overlapped */}
        <div className="absolute bottom-4 left-4 z-50 bg-white border border-slate-200 p-2.5 rounded-lg text-[9px] text-slate-500 flex gap-4 shadow-md">
          <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-red-500"></div> Temp</div>
          <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-cyan-600"></div> Pressure</div>
          <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-cyan-500"></div> Flow</div>
          <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-amber-500"></div> Level</div>
        </div>
      </div>

      {/* Process Parameters - separate section below diagram (not overlay) */}
      {(pidData?.reactor || pidData?.process_conditions || pidData?.material_handling) && (
        <div className="border-t border-slate-200 bg-white rounded-b-xl">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600">
              <Info size={18} />
            </span>
            <h3 className="text-lg font-bold text-slate-800">Process Parameters</h3>
          </div>
          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            {pidData.reactor && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Reactor</div>
                <div className="grid grid-cols-2 gap-x-3 gap-y-1 font-mono">
                  <span className="text-slate-500">Temp</span>
                  <span className="text-slate-800">{pidData.reactor.temperature}°C</span>
                  <span className="text-slate-500">Pressure</span>
                  <span className="text-slate-800">{pidData.reactor.pressure} bar</span>
                  <span className="text-slate-500">Volume</span>
                  <span className="text-slate-800">{pidData.reactor.volume != null ? `${pidData.reactor.volume} L` : '—'}</span>
                </div>
              </div>
            )}
            {pidData.process_conditions && Object.keys(pidData.process_conditions).length > 0 && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 md:col-span-2">
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Process conditions</div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1 font-mono text-xs">
                  {pidData.process_conditions.operating_temperature_range && (
                    <><span className="text-slate-500">Temp range</span><span className="text-slate-800 col-span-1">{pidData.process_conditions.operating_temperature_range}</span></>
                  )}
                  {pidData.process_conditions.operating_pressure_range && (
                    <><span className="text-slate-500">Pressure range</span><span className="text-slate-800 col-span-1">{pidData.process_conditions.operating_pressure_range}</span></>
                  )}
                  {pidData.process_conditions.residence_time && (
                    <><span className="text-slate-500">Residence time</span><span className="text-slate-800 col-span-1">{pidData.process_conditions.residence_time}</span></>
                  )}
                  {pidData.process_conditions.number_of_reactors != null && (
                    <><span className="text-slate-500">No. reactors</span><span className="text-slate-800 col-span-1">{pidData.process_conditions.number_of_reactors}</span></>
                  )}
                  {pidData.process_conditions.reactor_types && pidData.process_conditions.reactor_types.length > 0 && (
                    <><span className="text-slate-500">Reactor types</span><span className="text-slate-800 col-span-1">{pidData.process_conditions.reactor_types.join(', ')}</span></>
                  )}
                  {pidData.process_conditions.number_of_steps != null && (
                    <><span className="text-slate-500">No. steps</span><span className="text-slate-800 col-span-1">{pidData.process_conditions.number_of_steps}</span></>
                  )}
                </div>
                {pidData.process_conditions.synthesis_route && (
                  <p className="mt-2 pt-2 border-t border-slate-200 text-slate-700 text-xs">{pidData.process_conditions.synthesis_route}</p>
                )}
              </div>
            )}
            {pidData.material_handling && (pidData.material_handling.reactants?.length || pidData.material_handling.catalysts?.length || pidData.material_handling.synthesis_route) && (
              <div className="md:col-span-3 bg-slate-50 rounded-xl p-4 border border-slate-200">
                <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Material handling</div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  {pidData.material_handling.reactants && pidData.material_handling.reactants.length > 0 && (
                    <div><span className="text-slate-500 block mb-0.5">Reactants</span><span className="text-slate-800">{pidData.material_handling.reactants.join(', ')}</span></div>
                  )}
                  {pidData.material_handling.catalysts && pidData.material_handling.catalysts.length > 0 && (
                    <div><span className="text-slate-500 block mb-0.5">Catalysts</span><span className="text-slate-800">{pidData.material_handling.catalysts.join(', ')}</span></div>
                  )}
                  {pidData.material_handling.recycle_streams && pidData.material_handling.recycle_streams.length > 0 && (
                    <div><span className="text-slate-500 block mb-0.5">Recycle streams</span><span className="text-slate-800">{pidData.material_handling.recycle_streams.join(', ')}</span></div>
                  )}
                  {pidData.material_handling.synthesis_route && (
                    <div className="sm:col-span-3"><span className="text-slate-500 block mb-0.5">Synthesis route</span><span className="text-slate-800">{pidData.material_handling.synthesis_route}</span></div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};