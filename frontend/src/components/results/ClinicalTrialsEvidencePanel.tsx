import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Stethoscope, FlaskConical } from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import EmptyState from '../common/EmptyState';

const CLINICAL_SOURCE = /clinical|trial|dailymed|openfda|rxnorm|semanticscholar|pubmed/i;

function sourceOf(item: Record<string, unknown>): string {
  return String(item.source || item.type || item.agent || '').toLowerCase();
}

/** Count of evidence rows surfaced on the Structure & trials tab (for tab badge). */
export function countClinicalStyleEvidence(evidence: any[]): number {
  if (!evidence?.length) return 0;
  const clinicalItems = evidence.filter((item) => {
    const s = sourceOf(item as Record<string, unknown>);
    return s.includes('clinical') || s.includes('trial') || CLINICAL_SOURCE.test(s);
  });
  const trialLike = evidence.filter((item) => {
    if (clinicalItems.includes(item)) return false;
    const text = `${(item as any).summary || ''} ${(item as any).title || ''} ${(item as any).description || ''}`.toLowerCase();
    return text.includes('trial') || text.includes('phase') || text.includes('nct');
  });
  const seen = new Set<string>();
  let n = 0;
  for (const item of [...clinicalItems, ...trialLike]) {
    const key = `${(item as any).id || ''}-${(item as any).summary || (item as any).title || ''}`.slice(0, 200);
    if (seen.has(key)) continue;
    seen.add(key);
    n++;
    if (n >= 80) break;
  }
  return n;
}

interface ClinicalTrialsEvidencePanelProps {
  evidence: any[];
  drugName: string;
}

const ClinicalTrialsEvidencePanel: React.FC<ClinicalTrialsEvidencePanelProps> = ({
  evidence,
  drugName,
}) => {
  const clinicalItems = useMemo(() => {
    if (!evidence?.length) return [];
    return evidence.filter((item) => {
      const s = sourceOf(item as Record<string, unknown>);
      return s.includes('clinical') || s.includes('trial') || CLINICAL_SOURCE.test(s);
    });
  }, [evidence]);

  const trialLike = useMemo(() => {
    const rest = evidence.filter((item) => !clinicalItems.includes(item));
    return rest.filter((item) => {
      const text = `${(item as any).summary || ''} ${(item as any).title || ''} ${(item as any).description || ''}`.toLowerCase();
      return text.includes('trial') || text.includes('phase') || text.includes('nct');
    });
  }, [evidence, clinicalItems]);

  const combined = useMemo(() => {
    const seen = new Set<string>();
    const out: any[] = [];
    for (const item of [...clinicalItems, ...trialLike]) {
      const key = `${(item as any).id || ''}-${(item as any).summary || (item as any).title || ''}`.slice(0, 200);
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(item);
    }
    return out.slice(0, 80);
  }, [clinicalItems, trialLike]);

  return (
    <div className="space-y-6">
      <Card className="border-cyan-100/80 bg-gradient-to-br from-white to-cyan-50/30">
        <div className="flex items-start gap-3">
          <Stethoscope className="w-5 h-5 text-cyan-600 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Clinical & regulatory evidence</h3>
            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
              Pulled from the same multi-agent run as your repurposing report: trials-style sources, labeling-related
              feeds, and items whose text references phases or NCT IDs. For <span className="font-medium capitalize">{drugName}</span>.
            </p>
          </div>
        </div>
      </Card>

      {combined.length === 0 ? (
        <EmptyState
          icon={<FlaskConical className="w-10 h-10" />}
          title="No clinical-trial-shaped rows"
          description="Try another drug or check the Evidence tab for the full corpus."
        />
      ) : (
        <Card>
          <h3 className="text-sm font-semibold text-slate-900 mb-4">
            {combined.length} curated items
          </h3>
          <div className="space-y-3 max-h-[min(70vh,560px)] overflow-y-auto pr-1">
            {combined.map((item: any, idx: number) => (
              <div
                key={item.id || idx}
                className="rounded-xl border border-slate-200 bg-slate-50/80 p-3"
              >
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <Badge variant="teal" size="sm">
                    {item.source || item.type || 'evidence'}
                  </Badge>
                  {(item.indication || item.disease) && (
                    <span className="text-[11px] text-slate-600 truncate max-w-[200px]">
                      {(item.indication || item.disease) as string}
                    </span>
                  )}
                </div>
                <div className="prose prose-sm prose-slate max-w-none prose-p:text-slate-700 prose-p:my-1">
                  <ReactMarkdown>
                    {(item.summary || item.title || item.description || '_No summary_') as string}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default ClinicalTrialsEvidencePanel;
