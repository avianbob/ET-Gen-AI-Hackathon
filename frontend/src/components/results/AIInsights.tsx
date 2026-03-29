import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Sparkles } from 'lucide-react';
import InsightCard from '../scoring/InsightCard';
import Card from '../common/Card';

interface AIInsightsProps {
  synthesis: string;
  insights?: any[];
}

const AIInsights: React.FC<AIInsightsProps> = ({ synthesis, insights = [] }) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-cyan-500/15 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-cyan-700" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-900">AI-Generated Insights</h2>
          <p className="text-sm text-slate-600">LLM-synthesized analysis summary</p>
        </div>
      </div>

      <Card className="border-l-2 border-cyan-500/25">
        <div className="prose prose-sm prose-slate max-w-none text-slate-700 leading-relaxed">
          <ReactMarkdown>{synthesis}</ReactMarkdown>
        </div>
      </Card>

      {insights.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-700">Key Findings</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {insights.map((insight, idx) => (
              <InsightCard
                key={insight.id || idx}
                category={insight.category || insight.type || 'recommendation'}
                text={insight.text || insight.summary || insight.description || ''}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIInsights;
