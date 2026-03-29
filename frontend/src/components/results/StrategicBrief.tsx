import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, AlertTriangle, Target, ArrowRight } from 'lucide-react';
import Card from '../common/Card';
import { cn } from '../../utils/helpers';

interface StrategicBriefProps {
  data: any;
  drugName: string;
}

const SECTIONS = [
  {
    key: 'executive_summary',
    altKeys: ['executiveSummary', 'summary'],
    title: 'Executive Summary',
    icon: FileText,
    accentColor: 'text-cyan-400',
    borderColor: 'border-cyan-500/30',
  },
  {
    key: 'key_opportunities',
    altKeys: ['keyOpportunities', 'opportunities'],
    title: 'Key Opportunities',
    icon: Target,
    accentColor: 'text-emerald-400',
    borderColor: 'border-emerald-500/30',
  },
  {
    key: 'risk_assessment',
    altKeys: ['riskAssessment', 'risks'],
    title: 'Risk Assessment',
    icon: AlertTriangle,
    accentColor: 'text-red-400',
    borderColor: 'border-red-500/30',
  },
  {
    key: 'recommended_next_steps',
    altKeys: ['recommendedNextSteps', 'nextSteps', 'next_steps'],
    title: 'Recommended Next Steps',
    icon: ArrowRight,
    accentColor: 'text-cyan-700',
    borderColor: 'border-cyan-500/25',
  },
];

const resolveContent = (data: any, key: string, altKeys: string[]): string | null => {
  if (data[key]) return data[key];
  for (const alt of altKeys) {
    if (data[alt]) return data[alt];
  }
  return null;
};

const StrategicBrief: React.FC<StrategicBriefProps> = ({ data, drugName }) => {
  if (!data) {
    return (
      <div className="bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-center p-8">
        <p className="text-slate-500 text-sm">No strategic brief data available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <FileText className="w-5 h-5 text-cyan-700" />
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Strategic Brief</h2>
          <p className="text-sm text-slate-600">{drugName} — Repurposing Strategy</p>
        </div>
      </div>

      <div className="space-y-4">
        {SECTIONS.map((section) => {
          const content = resolveContent(data, section.key, section.altKeys);
          if (!content) return null;

          const Icon = section.icon;
          const markdown = typeof content === 'string' ? content : JSON.stringify(content, null, 2);

          return (
            <Card key={section.key} className={cn('border-l-2', section.borderColor)}>
              <div className="flex items-center gap-2 mb-3">
                <Icon className={cn('w-4 h-4', section.accentColor)} />
                <h3 className={cn('text-sm font-semibold', section.accentColor)}>{section.title}</h3>
              </div>
              <div className="prose prose-sm prose-slate max-w-none text-slate-700 leading-relaxed">
                <ReactMarkdown>{markdown}</ReactMarkdown>
              </div>
            </Card>
          );
        })}
      </div>

      {data.generated_at && (
        <p className="text-[11px] text-slate-500 text-right">
          Generated: {new Date(data.generated_at).toLocaleString()}
        </p>
      )}
    </div>
  );
};

export default StrategicBrief;
