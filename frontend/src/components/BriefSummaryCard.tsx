import React from 'react';

interface BriefSummaryCardProps {
  /** Full analysis text from the pipeline */
  analysis?: string | null;
  /** Final recommendation one-liner */
  recommendation?: string | null;
  /** Optional query/molecule for context */
  query?: string | null;
}

/** Truncate to roughly N chars, at a sentence boundary when possible */
function truncateAtSentence(text: string, maxChars: number): string {
  if (!text || text.length <= maxChars) return text;
  const cut = text.slice(0, maxChars);
  const lastPeriod = cut.lastIndexOf('.');
  const lastNewline = cut.lastIndexOf('\n');
  const breakAt = Math.max(lastPeriod, lastNewline, maxChars - 80);
  if (breakAt > maxChars * 0.5) return text.slice(0, breakAt + 1).trim();
  return cut.trim() + '…';
}

export const BriefSummaryCard: React.FC<BriefSummaryCardProps> = ({
  analysis,
  recommendation,
  query,
}) => {
  const hasContent = (analysis?.trim()?.length ?? 0) > 0 || (recommendation?.trim()?.length ?? 0) > 0;
  if (!hasContent) return null;

  const summaryText = analysis?.trim()
    ? truncateAtSentence(analysis.trim(), 600)
    : '';
  const rec = recommendation?.trim() || '';

  return (
    <div className="w-full rounded-2xl border border-slate-200 bg-white shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-slate-700 to-slate-600 px-6 py-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
            <i className="fas fa-file-alt text-white text-sm"></i>
          </span>
          Brief summary
        </h2>
        {query?.trim() && (
          <p className="text-slate-200 text-sm mt-1">Analysis for: {query}</p>
        )}
      </div>
      <div className="p-6 space-y-4">
        {summaryText && (
          <div>
            <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{summaryText}</p>
          </div>
        )}
        {rec && (
          <div className="pt-3 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Recommendation</p>
            <p className="text-base font-medium text-slate-800 mt-1">{rec}</p>
          </div>
        )}
      </div>
    </div>
  );
};
