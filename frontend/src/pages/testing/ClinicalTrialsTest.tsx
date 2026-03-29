import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AgentAPI, ClinicalTrialsTestResponse } from '../../api/endpoints';

export const ClinicalTrialsTest: React.FC = () => {
  const [prompt, setPrompt] = useState('Find new repurposing ideas for Metformin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ClinicalTrialsTestResponse | null>(null);

  const apiBase = (import.meta as ImportMeta).env?.VITE_API_URL || 'http://localhost:8000';

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    console.log('[ClinicalTrialsTest] Sending prompt to backend:', prompt);
    try {
      const response = await AgentAPI.clinicalTrialsTest(prompt);
      console.log('[ClinicalTrialsTest] Response from backend:', response);
      setData(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      console.error('[ClinicalTrialsTest] API error:', err);
    } finally {
      setLoading(false);
    }
  };

  const sr = data?.search_results;
  const hasError = typeof sr === 'object' && sr !== null && 'error' in sr;
  const errMsg = hasError ? (sr as { error?: string }).error : null;
  const analytics = sr && !hasError ? (sr as ClinicalTrialsTestResponse['search_results']).analytics : undefined;
  const results = sr && !hasError ? (sr as ClinicalTrialsTestResponse['search_results']).results : undefined;

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Link
            to="/search"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700"
          >
            ← Back to Drug Search
          </Link>
          <h1 className="text-2xl font-bold text-slate-800">ClinicalTrials.gov Test</h1>
        </div>
        <p className="text-sm text-slate-500 mb-4">
          Backend: <code className="bg-slate-200 px-1 rounded">{apiBase}</code> — Check backend console for request/response logs.
        </p>

        <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-2">Prompt (same as ClinicalTrails.gov)</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={2}
            minLength={1}
            placeholder="e.g. Find new repurposing ideas for Metformin"
            className="w-full min-h-[80px] max-h-[240px] resize-y overflow-y-auto box-border px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="mt-3 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-medium rounded-lg"
          >
            {loading ? 'Searching...' : 'Search ClinicalTrials.gov'}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {data && (
          <>
            <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
              <h2 className="text-lg font-semibold text-slate-800 mb-3">Decision (Gemini intent)</h2>
              <pre className="text-sm bg-slate-50 p-4 rounded-lg overflow-x-auto">
                {JSON.stringify(data.decision, null, 2)}
              </pre>
            </div>
            {errMsg && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
                <p className="text-amber-800 font-medium">API returned error</p>
                <p className="text-sm text-amber-700">{errMsg}</p>
              </div>
            )}
            {analytics && (
              <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
                <h2 className="text-lg font-semibold text-slate-800 mb-3">Analytics</h2>
                <p className="text-sm text-slate-600 mb-2">Total found: <strong>{analytics.total_found ?? 0}</strong></p>
                <p className="text-sm text-slate-600">Phase distribution: {JSON.stringify(analytics.phase_distribution ?? {})}</p>
                <p className="text-sm text-slate-600">Sponsor distribution: {JSON.stringify(analytics.sponsor_distribution ?? {})}</p>
              </div>
            )}
            {results && results.length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 p-6">
                <h2 className="text-lg font-semibold text-slate-800 mb-3">Results ({results.length})</h2>
                <ul className="space-y-4">
                  {results.slice(0, 5).map((r, i) => (
                    <li key={r.id || i} className="border-b border-slate-100 pb-4 last:border-0">
                      <p className="font-medium text-slate-800">{r.title}</p>
                      <p className="text-xs text-slate-500">NCT ID: {r.id} · Status: {r.status} · Phases: {Array.isArray(r.phases) ? r.phases.join(', ') : '-'}</p>
                      {r.conditions?.length > 0 && <p className="text-sm text-slate-600">Conditions: {r.conditions.join(', ')}</p>}
                      {r.brief_summary && <p className="text-sm text-slate-600 mt-1 line-clamp-2">{r.brief_summary}</p>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
