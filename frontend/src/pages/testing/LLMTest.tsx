import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const API_BASE = (import.meta as ImportMeta).env?.VITE_API_URL || 'http://localhost:8000';

interface LLMStatus {
  gemini_configured: boolean;
  groq_configured: boolean;
  message?: string;
}

export const LLMTest: React.FC = () => {
  const [status, setStatus] = useState<LLMStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [prompt, setPrompt] = useState('Say hello in one sentence.');
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testing, setTesting] = useState<'gemini' | 'groq' | null>(null);

  const api = (path: string) => `${API_BASE.replace(/\/$/, '')}/api${path.startsWith('/') ? path : `/${path}`}`;

  const loadStatus = async () => {
    setStatusLoading(true);
    setError(null);
    try {
      const r = await fetch(api('/test-llm'));
      const d = await r.json();
      setStatus(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load status');
      setStatus(null);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const testGemini = async () => {
    setLoading(true);
    setTesting('gemini');
    setResult(null);
    setError(null);
    try {
      const r = await fetch(api('/test-gemini'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: prompt }),
      });
      const d = await r.json();
      if (r.ok) setResult(d.response || d.message || 'OK');
      else setError(d.detail || d.message || `Error ${r.status}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
      setTesting(null);
    }
  };

  const testGroq = async () => {
    setLoading(true);
    setTesting('groq');
    setResult(null);
    setError(null);
    try {
      const r = await fetch(api('/test-groq'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      const d = await r.json();
      if (r.ok && d.success) setResult(d.response || 'OK');
      else setError(d.error || d.detail || `Error ${r.status}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
      setTesting(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-4">
          <Link to="/search" className="text-sm font-medium text-slate-600 hover:text-blue-600">
            ← Back to Drug Search
          </Link>
        </div>
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 mb-6">
          <h1 className="text-xl font-bold text-slate-800 mb-1">Test Gemini & Groq API</h1>
          <p className="text-sm text-slate-500 mb-4">
            Uses backend at <code className="bg-slate-100 px-1 rounded">{API_BASE}</code>. Set GEMINI_API_KEY and/or GROQ_API_KEY in backend <code className="bg-slate-100 px-1 rounded">.env</code>.
          </p>

          {/* Status */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold text-slate-700">Status</h2>
              <button
                type="button"
                onClick={loadStatus}
                disabled={statusLoading}
                className="text-sm text-blue-600 hover:underline disabled:opacity-50"
              >
                {statusLoading ? 'Loading…' : 'Refresh'}
              </button>
            </div>
            {status && (
              <div className="flex gap-3 flex-wrap">
                <span
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                    status.gemini_configured ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  Gemini: {status.gemini_configured ? 'Configured' : 'Not configured'}
                </span>
                <span
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                    status.groq_configured ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                  }`}
                >
                  Groq: {status.groq_configured ? 'Configured' : 'Not configured'}
                </span>
              </div>
            )}
            {status?.message && (
              <p className="text-xs text-slate-500 mt-2">{status.message}</p>
            )}
          </div>

          {/* Prompt */}
          <label className="block text-sm font-medium text-slate-700 mb-2">Prompt (for both tests)</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
            placeholder="e.g. What is Paracetamol used for?"
          />

          {/* Buttons */}
          <div className="flex gap-3 mt-4">
            <button
              type="button"
              onClick={testGemini}
              disabled={loading || !status?.gemini_configured}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium rounded-lg transition"
            >
              {loading && testing === 'gemini' ? 'Calling…' : 'Test Gemini'}
            </button>
            <button
              type="button"
              onClick={testGroq}
              disabled={loading || !status?.groq_configured}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium rounded-lg transition"
            >
              {loading && testing === 'groq' ? 'Calling…' : 'Test Groq'}
            </button>
          </div>

          {/* Result / Error */}
          {(result !== null || error) && (
            <div className="mt-6 p-4 rounded-lg bg-slate-100 border border-slate-200">
              {error && (
                <p className="text-red-700 text-sm font-medium mb-2">Error: {error}</p>
              )}
              {result !== null && (
                <div>
                  <p className="text-xs font-medium text-slate-500 mb-1">Response</p>
                  <pre className="text-sm text-slate-800 whitespace-pre-wrap break-words">{result}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
