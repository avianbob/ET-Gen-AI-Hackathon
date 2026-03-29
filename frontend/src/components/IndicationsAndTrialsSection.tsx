import React, { useState } from 'react';

interface QueryContext {
  drug?: string | null;
  disease?: string | null;
  diseases?: string[] | null;
  symptoms?: string[] | null;
  side_effects?: string[] | null;
  regions?: string[] | null;
  phase?: string | null;
}

interface TrialResult {
  id: string;
  title: string;
  status: string;
  phases: string[];
  sponsor: string;
  conditions: string[];
  brief_summary?: string;
  primary_outcome?: string;
}

interface ClinicalTrialsData {
  decision?: { drug?: string; disease?: string; intent?: string; reasoning?: string };
  analytics?: {
    phase_distribution?: Record<string, number>;
    sponsor_distribution?: Record<string, number>;
    total_found?: number;
  };
  results?: TrialResult[];
  ongoing_trials_count?: number;
  extracted_insights?: {
    symptoms?: string[];
    diseases?: string[];
    side_effects?: string[];
  };
}

interface IndicationsAndTrialsSectionProps {
  queryContext?: QueryContext | null;
  clinicalTrialsData?: ClinicalTrialsData | null;
}

export const IndicationsAndTrialsSection: React.FC<IndicationsAndTrialsSectionProps> = ({
  queryContext,
  clinicalTrialsData,
}) => {
  const hasData = queryContext || (clinicalTrialsData && (clinicalTrialsData.results?.length || clinicalTrialsData.analytics));
  if (!hasData) return null;

  const q = queryContext || {};
  const insights = clinicalTrialsData?.extracted_insights;
  const diseases = (q.diseases?.length ? q.diseases : insights?.diseases) || [];
  const sideEffects = (q.side_effects?.length ? q.side_effects : insights?.side_effects) || [];
  const trials = clinicalTrialsData?.results || [];
  const analytics = clinicalTrialsData?.analytics || {};
  const decision = clinicalTrialsData?.decision;
  const totalFound = clinicalTrialsData?.ongoing_trials_count ?? analytics.total_found ?? trials.length;

  const allConditions = Array.from(
    new Set(trials.flatMap((t) => (Array.isArray(t.conditions) ? t.conditions : [])))
  ).filter(Boolean);

  const [conditionsExpanded, setConditionsExpanded] = useState(false);
  const conditionsToShow = 20;
  const visibleConditions = conditionsExpanded ? allConditions : allConditions.slice(0, conditionsToShow);
  const hasMoreConditions = allConditions.length > conditionsToShow;

  const phaseEntries = analytics.phase_distribution
    ? Object.entries(analytics.phase_distribution).sort((a, b) => b[1] - a[1])
    : [];
  const sponsorEntries = analytics.sponsor_distribution
    ? Object.entries(analytics.sponsor_distribution).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <div className="w-full space-y-6">
      <div className="bg-white rounded-xl sm:rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
        <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 bg-slate-50 flex items-start sm:items-center gap-3">
          <span className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600 shrink-0">
            <i className="fas fa-stethoscope text-sm"></i>
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="text-base sm:text-lg font-bold text-slate-800 break-words">Drug Indications, Symptoms & Trial History</h2>
            <p className="text-xs text-slate-500 mt-0.5 break-words">From query context and ClinicalTrials.gov API</p>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Drug, Disease, Symptoms */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {q.drug && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 min-w-0">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Drug / Molecule</p>
                <p className="text-slate-800 font-medium mt-1 break-words">{q.drug}</p>
              </div>
            )}
            {q.disease && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 min-w-0">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Disease / Indication</p>
                <p className="text-slate-800 font-medium mt-1 break-words">{q.disease}</p>
              </div>
            )}
            {q.symptoms && q.symptoms.length > 0 && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 min-w-0">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Symptoms (drug can help with)</p>
                <p className="text-slate-800 font-medium mt-1 break-words">{q.symptoms.join(', ')}</p>
              </div>
            )}
            {diseases.length > 0 && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 min-w-0">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Diseases / conditions</p>
                <p className="text-slate-800 font-medium mt-1 break-words">{diseases.join(', ')}</p>
              </div>
            )}
            {sideEffects.length > 0 && (
              <div className="bg-amber-50 rounded-xl p-4 border border-amber-100 min-w-0">
                <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider">Side effects</p>
                <p className="text-slate-800 font-medium mt-1 break-words">{sideEffects.join(', ')}</p>
              </div>
            )}
            {q.regions && q.regions.length > 0 && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 min-w-0">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Regions</p>
                <p className="text-slate-800 font-medium mt-1 break-words">{q.regions.join(', ')}</p>
              </div>
            )}
            {q.phase && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 min-w-0">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Phase focus</p>
                <p className="text-slate-800 font-medium mt-1 break-words">{q.phase}</p>
              </div>
            )}
            {decision?.intent && (
              <div className="bg-cyan-50 rounded-xl p-4 border border-cyan-100 min-w-0">
                <p className="text-xs font-semibold text-cyan-700 uppercase tracking-wider">Search intent</p>
                <p className="text-slate-800 font-medium mt-1 break-words">{decision.intent}</p>
                {decision.reasoning && (
                  <p className="text-xs text-slate-500 mt-1 break-words">{decision.reasoning}</p>
                )}
              </div>
            )}
          </div>

          {/* Conditions this drug can help in (from trials) */}
          {allConditions.length > 0 && (
            <div className="min-w-0">
              <h3 className="text-sm font-bold text-slate-700 mb-2 break-words">Conditions this drug is studied in (from trials)</h3>
              <div className="flex flex-wrap gap-2 items-center">
                {visibleConditions.map((c, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-emerald-50 text-emerald-800 rounded-full text-sm border border-emerald-100 break-words max-w-full inline-block"
                  >
                    {c}
                  </span>
                ))}
                {hasMoreConditions && !conditionsExpanded && (
                  <button
                    type="button"
                    onClick={() => setConditionsExpanded(true)}
                    className="px-3 py-1 rounded-full text-sm font-medium text-cyan-600 bg-cyan-50 border border-cyan-200 hover:bg-cyan-100 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                  >
                    +{allConditions.length - conditionsToShow} more
                  </button>
                )}
                {hasMoreConditions && conditionsExpanded && (
                  <button
                    type="button"
                    onClick={() => setConditionsExpanded(false)}
                    className="px-3 py-1 rounded-full text-sm font-medium text-slate-600 bg-slate-100 border border-slate-200 hover:bg-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400/50"
                  >
                    Show less
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Phase & Sponsor distribution */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {phaseEntries.length > 0 && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <h3 className="text-sm font-bold text-slate-700 mb-2">Phase distribution</h3>
                <ul className="space-y-1 text-sm">
                  {phaseEntries.map(([phase, count]) => (
                    <li key={phase} className="flex justify-between">
                      <span className="text-slate-600">{phase}</span>
                      <span className="font-medium text-slate-800">{count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {sponsorEntries.length > 0 && (
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <h3 className="text-sm font-bold text-slate-700 mb-2">Sponsor distribution</h3>
                <ul className="space-y-1 text-sm">
                  {sponsorEntries.map(([sponsor, count]) => (
                    <li key={sponsor} className="flex justify-between">
                      <span className="text-slate-600">{sponsor}</span>
                      <span className="font-medium text-slate-800">{count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Trial history table */}
          {trials.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-slate-700 mb-3">
                Trial history ({totalFound} trials)
              </h3>
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100 sticky top-0">
                      <tr>
                        <th className="text-left p-3 font-semibold text-slate-700">NCT ID</th>
                        <th className="text-left p-3 font-semibold text-slate-700">Title</th>
                        <th className="text-left p-3 font-semibold text-slate-700">Status</th>
                        <th className="text-left p-3 font-semibold text-slate-700">Phase</th>
                        <th className="text-left p-3 font-semibold text-slate-700">Sponsor</th>
                        <th className="text-left p-3 font-semibold text-slate-700">Conditions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {trials.map((t, i) => (
                        <tr key={t.id || i} className="hover:bg-slate-50">
                          <td className="p-3 font-mono text-xs text-cyan-600">
                            <a
                              href={`https://clinicaltrials.gov/study/${t.id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:underline"
                            >
                              {t.id}
                            </a>
                          </td>
                          <td className="p-3 text-slate-800 min-w-0 max-w-[300px] sm:max-w-[380px]">
                            <span className="line-clamp-4 break-words block" title={t.title}>
                              {t.title}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-medium ${
                                t.status === 'RECRUITING'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : t.status === 'COMPLETED'
                                  ? 'bg-slate-100 text-slate-700'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {t.status}
                            </span>
                          </td>
                          <td className="p-3 text-slate-600">
                            {Array.isArray(t.phases) ? t.phases.join(', ') : '-'}
                          </td>
                          <td className="p-3 text-slate-600 min-w-0 max-w-[140px] sm:max-w-[180px]">
                            <span className="line-clamp-2 break-words block" title={t.sponsor}>
                              {t.sponsor}
                            </span>
                          </td>
                          <td className="p-3 text-slate-600 min-w-0 max-w-[220px] sm:max-w-[300px]">
                            <span className="line-clamp-4 break-words block" title={Array.isArray(t.conditions) ? t.conditions.join(', ') : undefined}>
                              {Array.isArray(t.conditions) ? t.conditions.slice(0, 3).join(', ') : '-'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {(!clinicalTrialsData?.results?.length && totalFound === 0) && (
            <p className="text-slate-500 text-sm">No trial records returned for this query.</p>
          )}
        </div>
      </div>
    </div>
  );
};
