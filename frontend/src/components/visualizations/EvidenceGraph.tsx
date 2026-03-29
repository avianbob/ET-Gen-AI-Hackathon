import React, { useMemo, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { cn } from '../../utils/helpers';

interface EvidenceGraphProps {
  data: any;
  className?: string;
}

const NODE_COLORS: Record<string, string> = {
  drug: '#FFE600',
  indication: '#00B4D8',
  evidence: '#A78BFA',
  target: '#00D4AA',
  pathway: '#F472B6',
};

const EvidenceGraph: React.FC<EvidenceGraphProps> = ({ data, className }) => {
  const graphRef = useRef<any>(null);

  const graphData = useMemo(() => {
    if (!data) return { nodes: [], links: [] };

    const nodes: any[] = [];
    const links: any[] = [];
    const seen = new Set<string>();

    const drugId = data.drug_name || data.drugName || 'drug';
    nodes.push({ id: drugId, label: drugId, type: 'drug', val: 20 });
    seen.add(drugId);

    const indications = data.indications || data.results || [];
    indications.forEach((ind: any, i: number) => {
      const name = ind.indication || ind.name || ind.disease || `Indication ${i + 1}`;
      const indId = `ind-${name}`;
      if (!seen.has(indId)) {
        nodes.push({ id: indId, label: name, type: 'indication', val: 12 });
        seen.add(indId);
        links.push({ source: drugId, target: indId, value: ind.score || ind.confidence || 0.5 });
      }

      const evidence = ind.evidence || ind.sources || [];
      evidence.forEach((ev: any, j: number) => {
        const evLabel = ev.source || ev.type || ev.title || `Evidence ${j + 1}`;
        const evId = `ev-${indId}-${j}`;
        if (!seen.has(evId)) {
          nodes.push({ id: evId, label: evLabel, type: 'evidence', val: 6 });
          seen.add(evId);
          links.push({ source: indId, target: evId, value: 0.3 });
        }
      });
    });

    if (nodes.length === 1) {
      return { nodes: [], links: [] };
    }

    return { nodes, links };
  }, [data]);

  const paintNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || node.id;
    const fontSize = Math.max(10 / globalScale, 3);
    const radius = Math.sqrt(node.val || 5) * 2;
    const color = NODE_COLORS[node.type] || '#9CA3AF';

    ctx.beginPath();
    ctx.arc(node.x!, node.y!, radius, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(node.x!, node.y!, radius + 1, 0, 2 * Math.PI);
    ctx.strokeStyle = `${color}66`;
    ctx.lineWidth = 2 / globalScale;
    ctx.stroke();

    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = '#E5E7EB';
    const truncated = label.length > 20 ? `${label.slice(0, 18)}…` : label;
    ctx.fillText(truncated, node.x!, node.y! + radius + 2);
  }, []);

  if (!data || graphData.nodes.length === 0) {
    return (
      <div className={cn('bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center p-8', className)}>
        <p className="text-slate-500 text-sm">No evidence data available for graph visualization.</p>
      </div>
    );
  }

  return (
    <div className={cn('bg-slate-100 rounded-xl border border-slate-200 overflow-hidden', className)}>
      <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Evidence Relationship Graph</h3>
        <div className="flex items-center gap-3">
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-[10px] text-slate-600 capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const radius = Math.sqrt(node.val || 5) * 2;
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, radius + 4, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        linkColor={() => 'rgba(255,255,255,0.08)'}
        linkWidth={(link: any) => Math.max(1, (link.value || 0.3) * 3)}
        backgroundColor="transparent"
        width={600}
        height={400}
        cooldownTicks={80}
        d3VelocityDecay={0.3}
      />
    </div>
  );
};

export default EvidenceGraph;
