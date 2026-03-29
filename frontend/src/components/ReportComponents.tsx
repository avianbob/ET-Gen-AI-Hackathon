import React, { useState } from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, AreaChart, Area
} from 'recharts';
import { ProfessionalPID } from './ProfessionalPID';

/**
 * 1. Grading Radar Chart - Feasibility Score
 */
interface GradingProps {
  data?: {
    market_demand?: number;
    production_feasibility?: number;
    demographics?: number;
    patents_and_trials?: number;
    competition?: number;
    overall_score?: number;
  } | null;
}

const defaultScores = {
  market_demand: 0.5,
  production_feasibility: 0.5,
  demographics: 0.5,
  patents_and_trials: 0.5,
  competition: 0.5,
  overall_score: 0.5,
};

function toNum(v: unknown, fallback: number): number {
  if (typeof v === 'number' && !Number.isNaN(v)) return Math.max(0, Math.min(1, v));
  return fallback;
}

/** Format IRR: backend may send 0–1 (e.g. 0.15) or 0–100 (e.g. 15). Avoid showing raw 100/0 when invalid. */
function formatIRR(val: number | undefined | null): string {
  if (val == null || Number.isNaN(val)) return '—';
  const pct = val > 1 ? val : val * 100;
  if (pct <= 0) return '—';
  return `${Math.min(99.9, pct).toFixed(1)}%`;
}

/** Format NPV: show — when missing; otherwise show value (e.g. $12.50M or −$5.00M). */
function formatNPV(npv: number | undefined | null): string {
  if (npv == null || Number.isNaN(npv)) return '—';
  const sign = npv >= 0 ? '' : '−';
  return `${sign}$${Math.abs(npv).toFixed(2)}M`;
}

/** True if IRR should be shown (not 100%, which often indicates invalid/uncomputed). */
function shouldShowIRR(val: number | undefined | null): boolean {
  if (val == null || Number.isNaN(val)) return false;
  const pct = val > 1 ? val : val * 100;
  return pct < 99.5; // Don't show when effectively 100%
}

export const GradingSection: React.FC<GradingProps> = ({ data }) => {
  const d = data && typeof data === 'object' ? data : {};
  const scores = {
    market_demand: toNum(d.market_demand, defaultScores.market_demand),
    production_feasibility: toNum(d.production_feasibility, defaultScores.production_feasibility),
    demographics: toNum(d.demographics, defaultScores.demographics),
    patents_and_trials: toNum(d.patents_and_trials, defaultScores.patents_and_trials),
    competition: toNum(d.competition, defaultScores.competition),
    overall_score: toNum(d.overall_score, defaultScores.overall_score),
  };

  const chartData = [
    { subject: 'Market Demand', A: scores.market_demand * 100, fullMark: 100 },
    { subject: 'Patent Viability', A: scores.patents_and_trials * 100, fullMark: 100 },
    { subject: 'Scalability', A: scores.production_feasibility * 100, fullMark: 100 },
    { subject: 'Demographics', A: scores.demographics * 100, fullMark: 100 },
    { subject: 'Competition', A: scores.competition * 100, fullMark: 100 },
  ];

  const gradeLetter = scores.overall_score > 0.75 ? 'A+' : scores.overall_score > 0.5 ? 'B' : 'C';
  const gradeColor = scores.overall_score > 0.75 ? 'text-emerald-500' : 'text-yellow-500';

  const chartHeight = 320;

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 flex flex-col overflow-hidden min-h-[380px]">
      <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 shrink-0">
        <h3 className="text-base sm:text-lg font-bold text-slate-800">Feasibility Score</h3>
        <span className={`text-base sm:text-lg font-bold ${gradeColor}`}>Grade: {gradeLetter}</span>
      </div>
      <div className="p-3 sm:p-4 w-full shrink-0" style={{ height: chartHeight, minHeight: 240 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="subject" />
            <Radar name="Score" dataKey="A" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.4} />
            <Tooltip formatter={(value: number) => [value.toFixed(0), 'Score']} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
/**
 * 2. Enhanced Process and Instrumentation Diagram (PID) - Chemical Engineering Grade
 */
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
  };
}

interface FlowDiagramProps {
  pidData?: PIDData;
}

// Equipment Icon Component
const EquipmentIcon: React.FC<{
  type: string;
  name: string;
  id: string;
  temperature: number;
  pressure: number;
  specs?: Record<string, any>;
  size?: 'small' | 'medium' | 'large';
}> = ({ type, name, id, temperature, pressure, specs, size = 'medium' }) => {
  const sizeClasses = {
    small: 'w-24 h-24',
    medium: 'w-32 h-32',
    large: 'w-44 h-44'
  };

  const getIcon = () => {
    if (type.includes('Reactor')) return 'fa-atom';
    if (type.includes('Separator') || type.includes('Filter')) return 'fa-filter';
    if (type.includes('Crystallizer')) return 'fa-snowflake';
    if (type.includes('Dryer')) return 'fa-wind';
    if (type.includes('Feed')) return 'fa-flask';
    return 'fa-cog';
  };

  const getColorClasses = () => {
    if (type.includes('Reactor')) return 'from-blue-500 to-blue-600';
    if (type.includes('Separator')) return 'from-purple-500 to-purple-600';
    if (type.includes('Crystallizer')) return 'from-teal-500 to-teal-600';
    if (type.includes('Filter')) return 'from-orange-500 to-orange-600';
    if (type.includes('Dryer')) return 'from-amber-500 to-amber-600';
    return 'from-slate-500 to-slate-600';
  };
  
  const getBorderColor = () => {
    if (type.includes('Reactor')) return 'border-blue-200';
    if (type.includes('Separator')) return 'border-purple-200';
    if (type.includes('Crystallizer')) return 'border-teal-200';
    if (type.includes('Filter')) return 'border-orange-200';
    if (type.includes('Dryer')) return 'border-amber-200';
    return 'border-slate-200';
  };

  const colorClasses = getColorClasses();
  const borderColor = getBorderColor();
  
  return (
    <div className="relative group cursor-pointer z-10">
      <div className={`${sizeClasses[size]} rounded-full border-4 border-white shadow-2xl bg-gradient-to-br ${colorClasses} flex flex-col items-center justify-center relative z-20 transform transition-all group-hover:scale-110`}>
        <i className={`fas ${getIcon()} text-2xl text-white mb-1 ${type.includes('Reactor') ? 'animate-spin-slow' : ''}`}></i>
        <span className="font-bold text-white text-xs text-center px-1">{name}</span>
        <span className="text-[10px] text-white/90 bg-black/20 px-1.5 py-0.5 rounded-full mt-0.5">{id}</span>
      </div>
      
      {/* Temperature Badge */}
      <div className="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] font-bold px-2 py-1 rounded-full shadow-lg border-2 border-white z-30">
        {temperature}°C
      </div>
      
      {/* Pressure Badge */}
      <div className="absolute -bottom-2 -right-2 bg-blue-500 text-white text-[10px] font-bold px-2 py-1 rounded-full shadow-lg border-2 border-white z-30">
        {pressure} bar
      </div>
      
      {/* Hover Tooltip with Specs */}
      {specs && (
        <div className="absolute left-full ml-4 top-1/2 -translate-y-1/2 bg-slate-900 text-white text-xs rounded-lg p-3 shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity z-50 min-w-[200px] pointer-events-none">
          <div className="font-bold mb-2 text-teal-400">{id} - {name}</div>
          <div className="space-y-1">
            <div><span className="text-slate-400">Temp:</span> <span className="text-red-300">{temperature}°C</span></div>
            <div><span className="text-slate-400">Pressure:</span> <span className="text-blue-300">{pressure} bar</span></div>
            {Object.entries(specs).map(([key, value]) => (
              <div key={key}>
                <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}:</span>{' '}
                <span className="text-white">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Outer Glow Ring */}
      <div className={`absolute -inset-4 rounded-full border-2 ${borderColor} border-dashed ${type.includes('Reactor') ? 'animate-spin-slow' : ''} -z-10`}></div>
    </div>
  );
};

// Control Loop Indicator
const ControlLoopBadge: React.FC<{
  tag: string;
  value: number;
  unit: string;
  position: 'top' | 'bottom';
}> = ({ tag, value, unit, position }) => {
  return (
    <div className={`absolute ${position === 'top' ? '-top-8' : '-bottom-8'} left-1/2 -translate-x-1/2 bg-slate-800 text-white text-[9px] font-mono px-2 py-1 rounded shadow-lg border border-slate-600 z-20 whitespace-nowrap`}>
      <span className="text-cyan-400">{tag}</span>: <span className="text-yellow-300">{value}</span> <span className="text-slate-400">{unit}</span>
    </div>
  );
};

export const FlowDiagramSection: React.FC<FlowDiagramProps> = ({ pidData }) => {
  // Default data if not provided
  const defaultEquipment = [
    { id: 'FEED-001', type: 'Feed Tank', name: 'Reactant A', temperature: 25, pressure: 1.0, specs: { volume: '2000L' } },
    { id: 'FEED-002', type: 'Feed Tank', name: 'Reactant B', temperature: 25, pressure: 1.0, specs: { volume: '2000L' } },
    { id: 'FEED-003', type: 'Feed Tank', name: 'Catalyst', temperature: 30, pressure: 1.0, specs: { volume: '500L' } },
  ];

  const defaultReactor = { id: 'R-101', type: 'CSTR Reactor', name: 'CSTR', temperature: 150, pressure: 6.5, specs: { volume: '5000L' } };
  const defaultSeparator = { id: 'S-201', type: 'Separator', name: 'Separator', temperature: 120, pressure: 5.5, specs: { type: 'Decanter' } };
  const defaultCrystallizer = { id: 'C-301', type: 'Crystallizer', name: 'Crystallizer', temperature: 20, pressure: 5.0, specs: { type: 'Cooling' } };
  const defaultFilter = { id: 'F-401', type: 'Filter', name: 'Filter', temperature: 25, pressure: 0.3, specs: { type: 'Vacuum' } };
  const defaultDryer = { id: 'D-501', type: 'Dryer', name: 'Dryer', temperature: 60, pressure: 1.0, specs: { type: 'Fluidized Bed' } };

  const equipment = pidData?.equipment || [
    ...defaultEquipment,
    defaultReactor,
    defaultSeparator,
    defaultCrystallizer,
    defaultFilter,
    defaultDryer
  ];

  const reactor = pidData?.reactor || { temperature: 150, pressure: 6.5, volume: 5000 };
  const controlLoops = pidData?.control_loops || [];

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
        <div>
          <h3 className="font-bold text-slate-800 text-xl flex items-center gap-3">
            <span className="p-2 bg-teal-100 rounded-lg text-teal-600">
              <i className="fas fa-industry"></i>
            </span>
            Process & Instrumentation Diagram (PID)
          </h3>
          <p className="text-xs text-slate-500 mt-1 ml-11 font-mono">
            MODEL: CONT-FLOW-V3 // CHEMICAL ENGINEERING GRADE // P&T INSTRUMENTED
          </p>
        </div>
        {pidData?.process_conditions && (
          <div className="text-right">
            <div className="text-xs text-slate-600 font-semibold">Operating Conditions</div>
            <div className="text-[10px] text-slate-500 font-mono">
              {pidData.process_conditions.operating_temperature_range && (
                <div>Temp: {pidData.process_conditions.operating_temperature_range}</div>
              )}
              {pidData.process_conditions.operating_pressure_range && (
                <div>Press: {pidData.process_conditions.operating_pressure_range}</div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Main PID Diagram */}
      <div className="p-8 bg-gradient-to-br from-slate-50 to-blue-50/30 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[1400px] relative py-8">
          
          {/* Feed Tanks Section */}
          <div className="flex flex-col gap-4 relative z-10">
            {equipment.filter(eq => eq.type.includes('Feed')).map((eq, i) => (
              <div key={eq.id} className="relative">
                <EquipmentIcon
                  type={eq.type}
                  name={eq.name}
                  id={eq.id}
                  temperature={eq.temperature}
                  pressure={eq.pressure}
                  specs={eq.specs}
                  size="small"
                />
              </div>
            ))}
          </div>

          {/* Arrow to Reactor */}
          <div className="flex-1 h-1 bg-gradient-to-r from-slate-400 to-blue-500 relative mx-6">
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-l-8 border-l-blue-500 border-t-4 border-t-transparent border-b-4 border-b-transparent"></div>
            {controlLoops.find(cl => cl.tag.includes('FIC')) && (
              <ControlLoopBadge
                tag={controlLoops.find(cl => cl.tag.includes('FIC'))!.tag}
                value={controlLoops.find(cl => cl.tag.includes('FIC'))!.setpoint}
                unit={controlLoops.find(cl => cl.tag.includes('FIC'))!.unit}
                position="top"
              />
            )}
          </div>

          {/* Reactor - Centerpiece */}
          <div className="relative">
            <EquipmentIcon
              type="CSTR Reactor"
              name="CSTR Reactor"
              id={equipment.find(eq => eq.type.includes('Reactor'))?.id || 'R-101'}
              temperature={reactor.temperature}
              pressure={reactor.pressure}
              specs={{ volume: `${reactor.volume}L`, residence_time: pidData?.process_conditions?.residence_time }}
              size="large"
            />
            {controlLoops.find(cl => cl.tag.includes('TIC')) && (
              <ControlLoopBadge
                tag={controlLoops.find(cl => cl.tag.includes('TIC'))!.tag}
                value={controlLoops.find(cl => cl.tag.includes('TIC'))!.setpoint}
                unit={controlLoops.find(cl => cl.tag.includes('TIC'))!.unit}
                position="top"
              />
            )}
            {controlLoops.find(cl => cl.tag.includes('PIC')) && (
              <ControlLoopBadge
                tag={controlLoops.find(cl => cl.tag.includes('PIC'))!.tag}
                value={controlLoops.find(cl => cl.tag.includes('PIC'))!.setpoint}
                unit={controlLoops.find(cl => cl.tag.includes('PIC'))!.unit}
                position="bottom"
              />
            )}
          </div>

          {/* Arrow to Separator */}
          <div className="flex-1 h-1 bg-gradient-to-r from-blue-500 to-purple-500 relative mx-6">
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-l-8 border-l-purple-500 border-t-4 border-t-transparent border-b-4 border-b-transparent"></div>
          </div>

          {/* Separator */}
          <div className="relative">
            <EquipmentIcon
              type="Separator"
              name="Separator"
              id={equipment.find(eq => eq.type.includes('Separator'))?.id || 'S-201'}
              temperature={equipment.find(eq => eq.type.includes('Separator'))?.temperature || 120}
              pressure={equipment.find(eq => eq.type.includes('Separator'))?.pressure || 5.5}
              specs={equipment.find(eq => eq.type.includes('Separator'))?.specs}
              size="medium"
            />
            {controlLoops.find(cl => cl.tag.includes('LIC')) && (
              <ControlLoopBadge
                tag={controlLoops.find(cl => cl.tag.includes('LIC'))!.tag}
                value={controlLoops.find(cl => cl.tag.includes('LIC'))!.setpoint}
                unit={controlLoops.find(cl => cl.tag.includes('LIC'))!.unit}
                position="top"
              />
            )}
          </div>

          {/* Arrow to Crystallizer */}
          <div className="flex-1 h-1 bg-gradient-to-r from-purple-500 to-teal-500 relative mx-6">
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-l-8 border-l-teal-500 border-t-4 border-t-transparent border-b-4 border-b-transparent"></div>
          </div>

          {/* Crystallizer */}
          <div className="relative">
            <EquipmentIcon
              type="Crystallizer"
              name="Crystallizer"
              id={equipment.find(eq => eq.type.includes('Crystallizer'))?.id || 'C-301'}
              temperature={equipment.find(eq => eq.type.includes('Crystallizer'))?.temperature || 20}
              pressure={equipment.find(eq => eq.type.includes('Crystallizer'))?.pressure || 5.0}
              specs={equipment.find(eq => eq.type.includes('Crystallizer'))?.specs}
              size="medium"
            />
            {controlLoops.find(cl => cl.tag.includes('TIC-301')) && (
              <ControlLoopBadge
                tag={controlLoops.find(cl => cl.tag.includes('TIC-301'))!.tag}
                value={controlLoops.find(cl => cl.tag.includes('TIC-301'))!.setpoint}
                unit={controlLoops.find(cl => cl.tag.includes('TIC-301'))!.unit}
                position="top"
              />
            )}
          </div>

          {/* Arrow to Filter */}
          <div className="flex-1 h-1 bg-gradient-to-r from-teal-500 to-orange-500 relative mx-6">
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-l-8 border-l-orange-500 border-t-4 border-t-transparent border-b-4 border-b-transparent"></div>
          </div>

          {/* Filter */}
          <div className="relative">
            <EquipmentIcon
              type="Filter"
              name="Vacuum Filter"
              id={equipment.find(eq => eq.type.includes('Filter'))?.id || 'F-401'}
              temperature={equipment.find(eq => eq.type.includes('Filter'))?.temperature || 25}
              pressure={equipment.find(eq => eq.type.includes('Filter'))?.pressure || 0.3}
              specs={equipment.find(eq => eq.type.includes('Filter'))?.specs}
              size="small"
            />
          </div>

          {/* Arrow to Dryer */}
          <div className="flex-1 h-1 bg-gradient-to-r from-orange-500 to-amber-500 relative mx-6">
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-l-8 border-l-amber-500 border-t-4 border-t-transparent border-b-4 border-b-transparent"></div>
          </div>

          {/* Dryer */}
          <div className="relative">
            <EquipmentIcon
              type="Dryer"
              name="Dryer"
              id={equipment.find(eq => eq.type.includes('Dryer'))?.id || 'D-501'}
              temperature={equipment.find(eq => eq.type.includes('Dryer'))?.temperature || 60}
              pressure={equipment.find(eq => eq.type.includes('Dryer'))?.pressure || 1.0}
              specs={equipment.find(eq => eq.type.includes('Dryer'))?.specs}
              size="small"
            />
          </div>

          {/* Arrow to Final Product */}
          <div className="flex-1 h-1 bg-gradient-to-r from-amber-500 to-emerald-500 relative mx-6">
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-l-8 border-l-emerald-500 border-t-4 border-t-transparent border-b-4 border-b-transparent"></div>
          </div>

          {/* Final Product */}
          <div className="w-32 h-32 rounded-full bg-gradient-to-br from-emerald-400 to-green-500 flex flex-col items-center justify-center shadow-xl shadow-green-100 z-10 text-white transform hover:scale-105 transition-transform border-4 border-white">
            <i className="fas fa-check-circle text-3xl mb-1"></i>
            <span className="font-bold text-sm">Final API</span>
            <span className="text-[10px] text-green-100 mt-0.5">99.5% Pure</span>
          </div>

        </div>
      </div>

      {/* Legend and Control Loops Summary */}
      <div className="p-6 bg-slate-50 border-t border-slate-200">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h4 className="text-xs font-bold text-slate-700 mb-3 uppercase tracking-wide">Instrumentation Legend</h4>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span className="text-slate-600">Temperature Indicator (TI)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-slate-600">Pressure Indicator (PI)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-cyan-500"></div>
                <span className="text-slate-600">Flow Indicator (FI)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <span className="text-slate-600">Level Indicator (LI)</span>
              </div>
            </div>
          </div>
          {controlLoops.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-700 mb-3 uppercase tracking-wide">Control Loops</h4>
              <div className="space-y-1 text-xs font-mono">
                {controlLoops.map((loop) => (
                  <div key={loop.tag} className="flex justify-between items-center bg-white px-2 py-1 rounded border border-slate-200">
                    <span className="text-cyan-600">{loop.tag}</span>
                    <span className="text-slate-600">{loop.setpoint} {loop.unit}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * 3. Advanced TEA (Techno-Economic Analysis) Section - Detailed Breakdown
 */
interface TeaProps {
  visualData: {
    revenue_projection: any[];
  };
  teaData?: {
    // CAPEX Breakdown
    equipment_capex_million_usd?: number;
    installation_capex_million_usd?: number;
    piping_instrumentation_capex_million_usd?: number;
    buildings_infrastructure_capex_million_usd?: number;
    engineering_design_capex_million_usd?: number;
    contingency_capex_million_usd?: number;
    total_capex_million_usd?: number;
    
    // OPEX Breakdown
    raw_material_cost_million_usd_per_year?: number;
    utility_cost_million_usd_per_year?: number;
    labor_cost_million_usd_per_year?: number;
    maintenance_cost_million_usd_per_year?: number;
    insurance_overhead_cost_million_usd_per_year?: number;
    total_opex_million_usd_per_year?: number;
    
    // Financial Metrics
    revenue_million_usd_per_year?: number;
    gross_profit_million_usd_per_year?: number;
    gross_margin_percent?: number;
    payback_period_years?: number;
    internal_rate_of_return?: number;
    net_present_value_million_usd?: number;
    product_price_usd_per_kg?: number;
    production_capacity_kg_per_year?: number;
    cost_per_kg_usd?: number;
    production_feasibility_score?: number;
    
    // Equipment Costs
    equipment_costs?: Record<string, any>;
  };
}

/** Derive revenue projection array from teaData when visualData.revenue_projection is empty */
function deriveRevenueProjection(teaData: TeaProps['teaData'], visualData: TeaProps['visualData']): Array<{ year: string; revenue: number; cost: number; profit?: number }> {
  const existing = visualData?.revenue_projection;
  if (Array.isArray(existing) && existing.length > 0) return existing;
  if (!teaData) return [];
  const rev = teaData.revenue_million_usd_per_year ?? 0;
  const cost = teaData.total_opex_million_usd_per_year ?? 0;
  const profit = teaData.gross_profit_million_usd_per_year ?? rev - cost;
  const baseYear = new Date().getFullYear();
  return Array.from({ length: 5 }, (_, i) => ({
    year: String(baseYear + i),
    revenue: Math.round(rev * (1 + i * 0.05) * 100) / 100,
    cost: Math.round(cost * (1 + i * 0.02) * 100) / 100,
    profit: Math.round((rev * (1 + i * 0.05) - cost * (1 + i * 0.02)) * 100) / 100,
  }));
}

export const TeaSection: React.FC<TeaProps> = ({ visualData, teaData }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'capex' | 'opex' | 'financial'>('overview');

  const revenueProjection = React.useMemo(
    () => deriveRevenueProjection(teaData, visualData),
    [teaData, visualData]
  );

  // Calculate CAPEX breakdown percentages
  const capexBreakdown = teaData ? [
    { name: 'Equipment', value: teaData.equipment_capex_million_usd || 0, color: '#06b6d4' },
    { name: 'Installation', value: teaData.installation_capex_million_usd || 0, color: '#8b5cf6' },
    { name: 'Piping & Instrumentation', value: teaData.piping_instrumentation_capex_million_usd || 0, color: '#06b6d4' },
    { name: 'Buildings & Infrastructure', value: teaData.buildings_infrastructure_capex_million_usd || 0, color: '#10b981' },
    { name: 'Engineering & Design', value: teaData.engineering_design_capex_million_usd || 0, color: '#f59e0b' },
    { name: 'Contingency', value: teaData.contingency_capex_million_usd || 0, color: '#ef4444' },
  ].filter(item => item.value > 0) : [];

  // Calculate OPEX breakdown percentages
  const opexBreakdown = teaData ? [
    { name: 'Raw Materials', value: teaData.raw_material_cost_million_usd_per_year || 0, color: '#06b6d4' },
    { name: 'Utilities', value: teaData.utility_cost_million_usd_per_year || 0, color: '#8b5cf6' },
    { name: 'Labor', value: teaData.labor_cost_million_usd_per_year || 0, color: '#06b6d4' },
    { name: 'Maintenance', value: teaData.maintenance_cost_million_usd_per_year || 0, color: '#10b981' },
    { name: 'Insurance & Overhead', value: teaData.insurance_overhead_cost_million_usd_per_year || 0, color: '#f59e0b' },
  ].filter(item => item.value > 0) : [];

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
      {/* Header - stacked on mobile */}
      <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 bg-slate-50">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3 sm:mb-4">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <span className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600 shrink-0">
              <i className="fas fa-chart-line text-sm sm:text-base"></i>
            </span>
            <h3 className="text-base sm:text-lg font-bold text-slate-800 truncate">Advanced Techno-Economic Analysis</h3>
          </div>
          {teaData?.pid_based && (
            <span className="text-xs bg-cyan-100 text-cyan-700 px-2 py-1 rounded font-semibold shrink-0 w-fit">
              PID-Based Calculation
            </span>
          )}
        </div>
        
        {/* Tabs - wrap on mobile */}
        <div className="flex flex-wrap gap-1.5 sm:gap-2">
          {['overview', 'capex', 'opex', 'financial'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition ${
                activeTab === tab
                  ? 'bg-cyan-600 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 sm:p-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-4 sm:space-y-6">
            {/* Key Metrics Grid - 2 cols mobile, 4 desktop */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
              <div className="bg-cyan-50 rounded-xl p-3 sm:p-4 border border-cyan-200">
                <div className="text-xs text-cyan-700 font-semibold mb-0.5 sm:mb-1">Total CAPEX</div>
                <div className="text-base sm:text-xl font-bold text-slate-800">
                  ${teaData?.total_capex_million_usd?.toFixed(1) || '0.0'}M
                </div>
              </div>
              <div className="bg-teal-50 rounded-xl p-3 sm:p-4 border border-teal-200">
                <div className="text-xs text-teal-700 font-semibold mb-0.5 sm:mb-1">Annual OPEX</div>
                <div className="text-base sm:text-xl font-bold text-slate-800">
                  ${teaData?.total_opex_million_usd_per_year?.toFixed(1) || '0.0'}M
                </div>
              </div>
              {teaData && shouldShowIRR(teaData.internal_rate_of_return) && (
                <div className="bg-emerald-50 rounded-xl p-3 sm:p-4 border border-emerald-200">
                  <div className="text-xs text-emerald-700 font-semibold mb-0.5 sm:mb-1">IRR</div>
                  <div className="text-base sm:text-xl font-bold text-slate-800">
                    {formatIRR(teaData.internal_rate_of_return)}
                  </div>
                </div>
              )}
            </div>

            {/* Revenue Projection Chart */}
            <div>
              <h4 className="font-semibold text-slate-700 mb-2 sm:mb-3 text-sm sm:text-base">Revenue & Cost Projection</h4>
              <div className="h-[220px] sm:h-[300px] min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={revenueProjection} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="revenue" stroke="#10b981" fill="url(#colorRev)" />
                    <Area type="monotone" dataKey="cost" stroke="#ef4444" fill="url(#colorCost)" />
                    {revenueProjection[0]?.profit != null && (
                      <Line type="monotone" dataKey="profit" stroke="#06b6d4" strokeWidth={2} />
                    )}
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Production Metrics */}
            {teaData && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="text-xs text-slate-600 mb-1">Production Capacity</div>
                  <div className="text-lg font-bold text-slate-800">
                    {(teaData.production_capacity_kg_per_year || 0) / 1000} tons/year
                  </div>
                </div>
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="text-xs text-slate-600 mb-1">Cost per kg</div>
                  <div className="text-lg font-bold text-slate-800">
                    ${teaData.cost_per_kg_usd?.toFixed(2) || '0.00'}/kg
                  </div>
                </div>
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="text-xs text-slate-600 mb-1">Product Price</div>
                  <div className="text-lg font-bold text-slate-800">
                    ${teaData.product_price_usd_per_kg?.toFixed(2) || '0.00'}/kg
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* CAPEX Breakdown Tab */}
        {activeTab === 'capex' && teaData && (
          <div className="space-y-4 sm:space-y-6">
            <div>
              <h4 className="font-semibold text-slate-700 mb-3 sm:mb-4 text-sm sm:text-base">Capital Expenditure (CAPEX) Breakdown</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-4 sm:mb-6">
                {capexBreakdown.map((item, idx) => {
                  const percentage = teaData.total_capex_million_usd 
                    ? (item.value / teaData.total_capex_million_usd * 100).toFixed(1)
                    : '0';
                  return (
                    <div key={idx} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-slate-700">{item.name}</span>
                        <span className="text-xs text-slate-500">{percentage}%</span>
                      </div>
                      <div className="text-xl font-bold" style={{ color: item.color }}>
                        ${item.value.toFixed(2)}M
                      </div>
                      <div className="mt-2 h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all"
                          style={{ 
                            width: `${percentage}%`, 
                            backgroundColor: item.color 
                          }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
              
              {/* Equipment Cost Details */}
              {teaData.equipment_costs && (
                <div>
                  <h5 className="font-semibold text-slate-700 mb-3">Equipment Cost Details</h5>
                  <div className="bg-slate-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                    <div className="space-y-2">
                      {Object.entries(teaData.equipment_costs).map(([id, details]: [string, any]) => (
                        <div key={id} className="flex items-center justify-between py-2 border-b border-slate-200 last:border-0">
                          <div>
                            <div className="font-semibold text-slate-700 text-sm">{details.name}</div>
                            <div className="text-xs text-slate-500">{details.type}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-blue-600">${details.cost_million_usd.toFixed(2)}M</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* OPEX Breakdown Tab */}
        {activeTab === 'opex' && teaData && (
          <div className="space-y-4 sm:space-y-6">
            <div>
              <h4 className="font-semibold text-slate-700 mb-3 sm:mb-4 text-sm sm:text-base">Operational Expenditure (OPEX) Breakdown</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-4 sm:mb-6">
                {opexBreakdown.map((item, idx) => {
                  const percentage = teaData.total_opex_million_usd_per_year
                    ? (item.value / teaData.total_opex_million_usd_per_year * 100).toFixed(1)
                    : '0';
                  return (
                    <div key={idx} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-slate-700">{item.name}</span>
                        <span className="text-xs text-slate-500">{percentage}%</span>
                      </div>
                      <div className="text-xl font-bold" style={{ color: item.color }}>
                        ${item.value.toFixed(2)}M/year
                      </div>
                      <div className="mt-2 h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all"
                          style={{ 
                            width: `${percentage}%`, 
                            backgroundColor: item.color 
                          }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Financial Metrics Tab */}
        {activeTab === 'financial' && teaData && (
          <div className="space-y-4 sm:space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              {/* Revenue & Profit */}
              <div className="bg-emerald-50 rounded-xl p-4 sm:p-6 border border-emerald-200">
                <h5 className="font-semibold text-emerald-800 mb-3 sm:mb-4 text-sm sm:text-base">Revenue & Profitability</h5>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Annual Revenue</span>
                    <span className="font-bold text-emerald-700">
                      ${teaData.revenue_million_usd_per_year?.toFixed(2) || '0.00'}M
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Annual OPEX</span>
                    <span className="font-bold text-red-600">
                      ${teaData.total_opex_million_usd_per_year?.toFixed(2) || '0.00'}M
                    </span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-emerald-300">
                    <span className="text-slate-700 font-semibold">Gross Profit</span>
                    <span className="font-bold text-emerald-800">
                      ${teaData.gross_profit_million_usd_per_year?.toFixed(2) || '0.00'}M
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Gross Margin</span>
                    <span className="font-bold text-emerald-700">
                      {teaData.gross_margin_percent?.toFixed(1) || '0.0'}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Investment Metrics */}
              <div className="bg-blue-50 rounded-xl p-4 sm:p-6 border border-blue-200">
                <h5 className="font-semibold text-blue-800 mb-3 sm:mb-4 text-sm sm:text-base">Investment Metrics</h5>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Total CAPEX</span>
                    <span className="font-bold text-blue-700">
                      ${teaData.total_capex_million_usd?.toFixed(2) || '0.00'}M
                    </span>
                  </div>
                  {shouldShowIRR(teaData.internal_rate_of_return) && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">IRR</span>
                      <span className="font-bold text-blue-700">
                        {formatIRR(teaData.internal_rate_of_return)}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between pt-2 border-t border-blue-300">
                    <span className="text-slate-700 font-semibold">NPV (10% discount)</span>
                    <span className="font-bold text-blue-800">
                      {formatNPV(teaData.net_present_value_million_usd)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Production Economics */}
            <div className="bg-slate-50 rounded-xl p-4 sm:p-6 border border-slate-200">
              <h5 className="font-semibold text-slate-800 mb-3 sm:mb-4 text-sm sm:text-base">Production Economics</h5>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                <div>
                  <div className="text-xs text-slate-600 mb-1">Capacity</div>
                  <div className="text-lg font-bold text-slate-800">
                    {(teaData.production_capacity_kg_per_year || 0) / 1000} tons/yr
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-600 mb-1">Cost/kg</div>
                  <div className="text-lg font-bold text-red-600">
                    ${teaData.cost_per_kg_usd?.toFixed(2) || '0.00'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-600 mb-1">Price/kg</div>
                  <div className="text-lg font-bold text-emerald-600">
                    ${teaData.product_price_usd_per_kg?.toFixed(2) || '0.00'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-600 mb-1">Margin/kg</div>
                  <div className="text-lg font-bold text-blue-600">
                    ${((teaData.product_price_usd_per_kg || 0) - (teaData.cost_per_kg_usd || 0)).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};