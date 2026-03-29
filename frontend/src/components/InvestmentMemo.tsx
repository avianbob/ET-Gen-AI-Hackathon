import React, { useMemo, memo } from 'react';
import { FileText, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

interface InvestmentMemoProps {
  reportContent: string;
  drugName?: string;
  /** Therapeutic indication (e.g. "Paracetamol overdose") — shown as subtitle when present */
  indication?: string | null;
  grading?: {
    overall_score?: number;
  };
  /** Report date for header (e.g. "10/02/2026"). Defaults to current date. */
  reportDate?: string | null;
}

// Moved outside to avoid recreation on every render
const getIconForSection = (text: string) => {
  const lower = text.toLowerCase();
  if (lower.includes('risk') || lower.includes('technical')) return <AlertTriangle className="text-amber-600" size={20} />;
  if (lower.includes('financial') || lower.includes('commercial')) return <TrendingUp className="text-emerald-600" size={20} />;
  if (lower.includes('market') && lower.includes('demand')) return <TrendingUp className="text-cyan-600" size={20} />;
  if (lower.includes('thesis') || lower.includes('executive') || lower.includes('subject')) return <FileText className="text-cyan-600" size={20} />;
  if (lower.includes('strategic') || lower.includes('recommendation')) return <CheckCircle className="text-emerald-600" size={20} />;
  return <CheckCircle className="text-slate-400" size={20} />;
};

const getScoreColor = (score: number) => {
  if (score >= 0.8) return 'bg-emerald-100 text-emerald-800 border-emerald-200';
  if (score >= 0.6) return 'bg-amber-100 text-amber-800 border-amber-200';
  return 'bg-red-100 text-red-800 border-red-200';
}

/** Split on **SECTION NAME:** or 1. / ### / SECTION: / RECOMMENDATIONS: style headers */
const SECTION_REGEX = /(?=^\s*(?:\d\.\s+|###\s+|\*\*[^*]+\*\*:\s*|SECTION:\s*|(?:\*\*)?\s*RECOMMENDATIONS\s*(?:\*\*)?\s*:\s*))/gim;

/** Strip markdown **bold** from text */
function stripMarkdownBold(text: string): string {
  return text.replace(/\*\*([^*]+)\*\*/g, '$1').replace(/\*\*/g, '').trim();
}

/** Strip HTML tags (e.g. <strong>, <b>) so body is plain text only */
function stripHtml(text: string): string {
  return text.replace(/<[^>]+>/g, '').trim();
}

/** Remove Recommendation date line (e.g. "Recommendation date: February 11, 2026") */
function removeRecommendationDate(text: string): string {
  return text.replace(/\n?\s*Recommendation\s+date\s*:\s*[^\n]+/gi, '').trim();
}

/** Remove payback when it is 0 (e.g. "payback 0.0 years", "; payback 0 years", etc.) */
function removeZeroPayback(text: string): string {
  return text
    .replace(/[,;]?\s*payback\s+0(\.0)?\s*years?[,;]?/gi, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/\s*,\s*,/g, ',')
    .trim();
}

/** Normalize report body: strip HTML, markdown bold, recommendation date and zero payback, fix $/number breaks */
function normalizeReportBody(text: string): string {
  return removeZeroPayback(removeRecommendationDate(stripHtml(stripMarkdownBold(
    text
      .replace(/\$\s*\n\s*/g, '$')
      .replace(/(\d)\s*\n\s*(%|bar|years?|B|M)\b/gi, '$1$2')
  ))));
}

/** Convert ALL CAPS or UPPERCASE line to sentence case for simpler reading */
function toSentenceCase(line: string): string {
  const t = line.trim();
  if (t.length <= 1) return t;
  if (t !== t.toUpperCase()) return t; // already mixed case, leave as-is
  return t.charAt(0).toUpperCase() + t.slice(1).toLowerCase();
}

/** Section display order: each group lists keywords that identify that section (first match wins). */
const SECTION_ORDER: string[][] = [
  ['subject', 'investment committee', 'memorandum', 'for:', 'date', 'author', 'confidential'],
  ['executive thesis', "why now", 'thesis'],
  ['market demand', 'market demand'],
  ['technical', 'operational risk', 'operational risks'],
  ['financial outlook', 'financial'],
  ['strategic recommendation', 'strategic'],
  ['recommendations'],
  ['conclusion'],
];

function getSectionOrder(title: string): number {
  const lower = title.toLowerCase().trim();
  for (let i = 0; i < SECTION_ORDER.length; i++) {
    if (SECTION_ORDER[i].some((key) => lower.includes(key))) return i;
  }
  return SECTION_ORDER.length;
}

export const InvestmentMemo = memo<InvestmentMemoProps>(function InvestmentMemo({
  reportContent,
  drugName,
  indication,
  grading,
  reportDate: reportDateProp,
}) {
  const content = typeof reportContent === 'string' ? reportContent : '';
  const sections = useMemo(() => {
    const parts = content.split(SECTION_REGEX).filter((s) => s.trim().length > 0);
    const filtered = parts.filter((section) => {
      const firstLine = (section.trim().split('\n')[0] ?? '').trim();
      const title = firstLine.replace(/^\s*\*\*|\*\*:\s*$/g, '').replace(/[*#]/g, '').trim().toLowerCase();
      if (title.includes('recommendation date')) return false;
      return true;
    });
    // Sort into logical order: Subject → Thesis → Market → Technical → Financial → Strategic → Recommendations
    return [...filtered].sort((a, b) => {
      const titleA = (a.trim().split('\n')[0] ?? '').replace(/^\s*\*\*|\*\*:\s*$/g, '').trim();
      const titleB = (b.trim().split('\n')[0] ?? '').replace(/^\s*\*\*|\*\*:\s*$/g, '').trim();
      return getSectionOrder(titleA) - getSectionOrder(titleB);
    });
  }, [content]);
  const reportDate = useMemo(
    () => reportDateProp ?? new Date().toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }),
    [reportDateProp]
  );
  const displayTitle = drugName && drugName.trim() ? drugName.trim() : 'Pharmaceutical Asset';
  const displaySubtitle = indication && indication.trim() && indication.trim() !== displayTitle
    ? indication.trim()
    : null;

  return (
    <div className="bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden w-full my-6 md:my-8 font-serif">
      {/* Header acting as a "Letterhead" */}
      <div className="bg-slate-900 text-white p-4 sm:p-6 md:p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-20 sm:p-32 bg-cyan-500 rounded-full mix-blend-overlay opacity-20 transform translate-x-1/2 -translate-y-1/2"></div>

        <div className="relative z-10 flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
          <div className="min-w-0">
            <div className="text-[10px] sm:text-xs font-bold tracking-[0.2em] text-cyan-200 uppercase mb-1 sm:mb-2">Confidential Investment Memorandum</div>
            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold font-sans tracking-tight mb-0.5 truncate">{displayTitle}</h1>
            {displaySubtitle && (
              <p className="text-slate-300 text-sm sm:text-base font-medium mb-1 truncate">{displaySubtitle}</p>
            )}
            <p className="text-slate-400 text-xs sm:text-sm">
              Automated Due Diligence Report • {reportDate}
            </p>
          </div>

          {grading?.overall_score !== undefined && (
            <div className={`flex flex-col items-center justify-center p-3 sm:p-4 rounded-lg border shrink-0 ${getScoreColor(grading.overall_score)}`}>
              <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider mb-1">Feasibility</span>
              <span className="text-2xl sm:text-3xl font-black font-sans">{(grading.overall_score * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
      </div>

      {/* Toolbar: section labels only (export buttons removed) */}
      <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 bg-slate-50">
        <div className="flex flex-wrap gap-3 sm:gap-4 text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider">
          <span><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block mr-1"></span>Financials</span>
          <span><span className="w-2 h-2 rounded-full bg-amber-500 inline-block mr-1"></span>Risk Analysis</span>
          <span><span className="w-2 h-2 rounded-full bg-cyan-500 inline-block mr-1"></span>Market Fit</span>
        </div>
      </div>

      {/* Content Body — only headings bold; all body text plain */}
      <div className="p-4 sm:p-6 md:p-10 space-y-8 md:space-y-10 bg-white font-normal">
        {sections.length > 0 ? (
          sections.map((section, idx) => {
            const lines = section.trim().split('\n');
            const rawTitle = lines[0] ?? '';
            const body = lines.slice(1).join('\n');
            const title = stripMarkdownBold(rawTitle).replace(/[*#]/g, '').trim() || 'Section';
            const stepNum = idx + 1;
            const normalizedBody = normalizeReportBody(body);
            const bodyLines = normalizedBody.split('\n').filter((l) => l.trim());
            const looksLikeList = bodyLines.length >= 2 && /^\s*\d+\.\s+/.test(bodyLines[0]) && /^\s*\d+\.\s+/.test(bodyLines[1]);
            const isRecommendationsSection = title.toLowerCase().includes('recommendations');
            const isOnlyRecommendations = /^\s*(?:\*\*)?\s*recommendations\s*(?:\*\*)?\s*:\s*$/i.test(title) || title.toLowerCase().trim() === 'recommendations:';
            // If body starts with "RECOMMENDATIONS:" then list (embedded in e.g. STRATEGIC RECOMMENDATION section), show RECOMMENDATIONS as same bold heading then list
            const firstLinePlain = bodyLines[0] ? stripMarkdownBold(bodyLines[0]).replace(/[*#]/g, '').trim().toLowerCase() : '';
            const bodyStartsWithRecommendationsThenList = bodyLines.length >= 2 && firstLinePlain === 'recommendations:' && /^\s*\d+\.\s+/.test(bodyLines[1]);
            const listStartIdx = bodyStartsWithRecommendationsThenList ? 1 : 0;
            const listLines = bodyStartsWithRecommendationsThenList ? bodyLines.slice(1) : bodyLines;
            const showRecommendationsSubheading = bodyStartsWithRecommendationsThenList;
            const listLooksLikeList = listLines.length >= 2 && /^\s*\d+\.\s+/.test(listLines[0]) && /^\s*\d+\.\s+/.test(listLines[1]);

            const sectionHeadingClass = 'text-lg sm:text-xl font-extrabold font-sans text-slate-900 uppercase tracking-tight flex-1';

            return (
              <section key={idx} className="relative pl-6 sm:pl-10 border-l-4 border-cyan-200 hover:border-cyan-500 transition-colors bg-slate-50/50 rounded-r-lg py-4 pr-4 sm:py-5 sm:pr-5">
                <div className="absolute -left-[15px] top-6 bg-white p-0.5 rounded-full border-2 border-cyan-500 shadow-sm z-10">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-cyan-600 text-xs font-black text-white">
                    {stepNum}
                  </span>
                </div>
                <div className="flex items-start gap-3 mb-3">
                  <h3 className={sectionHeadingClass}>{title}</h3>
                  <span className="shrink-0 mt-0.5">{getIconForSection(rawTitle)}</span>
                </div>
                {showRecommendationsSubheading ? (
                  <>
                    <h3 className={`${sectionHeadingClass} mb-3 mt-4`}>RECOMMENDATIONS</h3>
                    {listLooksLikeList && (
                      <ol className="list-decimal list-inside space-y-2 leading-relaxed break-words text-slate-900 font-extrabold text-base sm:text-lg tracking-tight">
                        {listLines.map((line, i) => {
                          const match = line.match(/^\s*(\d+)\.\s+(.*)$/);
                          const label = match ? match[1] : '';
                          const rest = match ? toSentenceCase(match[2].trim()) : toSentenceCase(line.trim());
                          return (
                            <li key={i} className="pl-1 font-extrabold">
                              {label}. {rest}
                            </li>
                          );
                        })}
                      </ol>
                    )}
                  </>
                ) : looksLikeList ? (
                  <ol className={`list-decimal list-inside space-y-2 leading-relaxed break-words ${isRecommendationsSection || isOnlyRecommendations ? 'text-slate-900 font-extrabold text-base sm:text-lg tracking-tight' : 'text-slate-600 font-normal [&_*]:font-normal'}`}>
                    {bodyLines.map((line, i) => {
                      const match = line.match(/^\s*(\d+)\.\s+(.*)$/);
                      const label = match ? match[1] : '';
                      const rest = match ? toSentenceCase(match[2].trim()) : toSentenceCase(line.trim());
                      return (
                        <li key={i} className={isRecommendationsSection || isOnlyRecommendations ? 'pl-1 font-extrabold' : 'pl-1 font-normal'}>
                          {label}. {rest}
                        </li>
                      );
                    })}
                  </ol>
                ) : (
                  <div className="max-w-none text-slate-600 leading-relaxed whitespace-pre-line break-words font-normal [&_*]:font-normal text-[15px]">
                    {normalizedBody}
                  </div>
                )}
              </section>
            );
          })
        ) : (
          <div className="max-w-none text-slate-600 leading-relaxed whitespace-pre-wrap break-words font-normal [&_*]:font-normal">
            {normalizeReportBody(content)}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-slate-50 p-4 sm:p-6 text-center border-t border-slate-200 space-y-1">
        <p className="text-[10px] text-slate-400 uppercase tracking-widest">Generated by PharmAI • Strategic Intelligence Engine</p>
      </div>
    </div>
  );
});
