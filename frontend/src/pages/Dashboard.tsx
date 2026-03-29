import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Download, Menu } from 'lucide-react';
import { Sidebar, HistoryItem } from '../components/sidebar';
import { GradingSection, TeaSection } from '../components/ReportComponents';
import { ProfessionalPID } from '../components/ProfessionalPID';
import { IndicationsAndTrialsSection } from '../components/IndicationsAndTrialsSection';
import { SymptomsDiseaseSideEffectsSummary } from '../components/SymptomsDiseaseSideEffectsSummary';
import { MarketAndEximCharts } from '../components/MarketAndEximCharts';
import { PlantSiteMap } from '../components/PlantSiteMap';
import { MolecularDetailsCard } from '../components/MolecularDetailsCard';
import { InvestmentMemo } from '../components/InvestmentMemo';
import { CompetitorIntelligenceCard } from '../components/CompetitorIntelligenceCard';
import { AgentAPI } from '../api/endpoints';

const QUERY_PLACEHOLDER = 'e.g. Paracetamol API market analysis, Roflumilast repurposing...';
const LOADING_MESSAGES = [
  'Understanding your query...',
  'Running market & EXIM agents...',
  'Fetching clinical trials...',
  'Analyzing process design...',
  'Computing techno-economics...',
  'Evaluating demographics & sites...',
  'Synthesizing investment memo...',
];

export const Dashboard: React.FC = () => {
  const [input, setInput] = useState('');
  const [result, setResult] = useState<any | null>(null); 
  const [loading, setLoading] = useState(false);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [sidebarMinimized, setSidebarMinimized] = useState(true);
  const [sidebarMobileOpen, setSidebarMobileOpen] = useState(false);
  const [showLogoutPage, setShowLogoutPage] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Update document title when result/loading changes
  useEffect(() => {
    document.title = loading ? 'Analyzing... – PharmAI' : result?.query_context?.drug ? `${result.query_context.drug} – PharmAI` : 'PharmAI – Pharmaceutical Intelligence';
  }, [loading, result]);

  // Debug: log query_context (Symptoms / Disease / Side effects) when result is set
  useEffect(() => {
    if (result?.query_context) {
      const qc = result.query_context;
      console.log('[PharmAI] query_context from backend:', {
        drug: qc.drug,
        disease: qc.disease,
        symptoms: qc.symptoms,
        diseases: qc.diseases,
        side_effects: qc.side_effects,
        full: qc,
      });
    }
  }, [result]);

  // Cycle loading messages every 2.5s while loading
  useEffect(() => {
    if (!loading) return;
    const id = setInterval(() => {
      setLoadingMessageIndex((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 2500);
    return () => clearInterval(id);
  }, [loading]);

  // Auto-resize textarea
  const adjustTextareaHeight = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 280)}px`;
  };
  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  // Existing robust handleRun with History and Error handling
  const handleRun = async () => {
    if (!input.trim()) return;
    
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // 1. Call the API
      const responseData = await AgentAPI.runAgent({
        query: input,
        complexity: 2 
      });
      console.log("Response Data", responseData);
      
      // 2. Set Real Data
      setResult(responseData);
      if (responseData.llm_fallback_used?.length) {
        console.log('LLM fallback (Groq) used for:', responseData.llm_fallback_used);
      }

      // 3. Update History
      const newItem: HistoryItem = {
        id: Date.now(),
        query: input,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        data: responseData
      };
      setHistory(prev => [newItem, ...prev]);

      // 4. Auto-scroll
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);

    } catch (err) {
      console.error("API Error:", err);
      setError("Failed to connect to the Agent Backend. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  const apiBase = (import.meta as ImportMeta).env?.VITE_API_URL ?? 'http://localhost:8000';

  const handleDownloadPDF = async () => {
    if (!result) return;
    try {
      const response = await axios.post(`${apiBase}/api/generate-pdf`, { text: result.analysis }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Investment_Memo_${result.query_context?.drug || result.agent_id || 'report'}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error('PDF download failed', e);
      alert('Failed to download PDF. Please check backend connection.');
    }
  };

  const handleDownloadPPTX = async () => {
    if (!result) return;
    try {
      const response = await axios.post(
        `${apiBase}/api/generate-pptx`,
        { text: result.analysis, title: `${result.query_context?.drug ?? 'Pharmaceutical Asset'} — Investment Memorandum` },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Investment_Memo_${result.query_context?.drug || result.agent_id || 'report'}.pptx`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error('PPTX download failed', e);
      alert('Failed to download PowerPoint. Ensure backend has python-pptx installed.');
    }
  };

  const handleExportReport = async () => {
    if (!result) return;
    try {
      const response = await axios.post(
        `${apiBase}/api/export-report`,
        result,
        { responseType: 'blob' }
      );
      const name = result.query_context?.drug || result.agent_id || 'report';
      const safeName = String(name).replace(/[^a-zA-Z0-9-_ ]/g, '_').slice(0, 50);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `PharmAI_Full_Report_${safeName}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Export report failed', e);
      alert('Failed to export full report. Please check backend connection.');
    }
  };

  const startNewChat = () => {
    setResult(null);
    setInput('');
    setError(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100/80 to-slate-50 font-sans text-slate-800">
      
      {/* Mock Logout page overlay */}
      {showLogoutPage && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-8 text-center animate-fade-in-up">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-100 flex items-center justify-center">
              <i className="fas fa-check text-2xl text-emerald-600"></i>
            </div>
            <h2 className="text-xl font-bold text-slate-800 mb-2">You have been logged out</h2>
            <p className="text-slate-500 text-sm mb-8">This is a mock logout. Sign in again to continue.</p>
            <button
              type="button"
              onClick={() => setShowLogoutPage(false)}
              className="px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-xl transition-colors"
            >
              Back to PharmAI
            </button>
          </div>
        </div>
      )}

      <Sidebar 
        history={history} 
        onSelectHistory={(item) => setResult(item.data)}
        onNewChat={startNewChat}
        onToggle={setSidebarMinimized}
        onLogoutClick={() => setShowLogoutPage(true)}
        initialMinimized={true}
        mobileOpen={sidebarMobileOpen}
        onMobileClose={() => setSidebarMobileOpen(false)}
      />

      <div className={`min-h-screen flex flex-col relative transition-all duration-300 ${sidebarMinimized ? 'md:ml-16' : 'md:ml-80'} print:ml-0`}>
        
        {/* Fixed Header — hamburger on mobile, logo and actions; hidden when printing / Save as PDF */}
        <header 
          className={`fixed top-0 left-0 right-0 h-16 bg-white z-40 flex items-center justify-between md:justify-end gap-3 px-4 md:px-8 md:pr-8 transition-all duration-300 border-b border-slate-200 ${sidebarMinimized ? 'md:left-16' : 'md:left-80'} print:hidden`}
        >
          <button
            type="button"
            onClick={() => setSidebarMobileOpen(true)}
            className="md:hidden w-10 h-10 flex items-center justify-center rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 touch-target"
            aria-label="Open menu"
          >
            <Menu size={22} className="text-slate-600" />
          </button>
          <div className="flex-1 md:flex-none flex items-center justify-end gap-3 md:gap-4">
            {result && !loading && (
              <button
                type="button"
                onClick={() => window.print()}
                className="flex items-center gap-1.5 md:gap-2 px-3 md:px-4 py-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 hover:text-slate-800 hover:border-slate-300 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                title="Print / Save as PDF"
              >
                <Download size={18} />
                <span className="text-sm font-medium hidden sm:inline">Download</span>
              </button>
            )}
            <div className="flex items-center gap-2 md:gap-3">
              <div className="w-9 h-9 flex items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-teal-600 shadow-md">
                <i className="fas fa-dna text-white text-lg"></i>
              </div>
              <span className="font-extrabold text-lg tracking-tight text-slate-800">PharmAI</span>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 md:p-8 pt-20 md:pt-24 max-w-[1600px] mx-auto w-full flex flex-col">
          
          {/* Landing / Input Section */}
          <div className={`transition-all duration-700 ease-in-out flex flex-col ${result ? 'py-0 mb-6 md:mb-8' : 'py-16 sm:py-24 md:py-32 items-center justify-center text-center'}`}>
            
            {!result && !loading && (
              <div className="animate-fade-in-up">
                 <div className="inline-block p-6 md:p-8 rounded-2xl mb-6 md:mb-8 card-elevated border border-slate-200/60 glow-cyan">
                    <i className="fas fa-dna text-5xl md:text-6xl text-transparent bg-clip-text bg-gradient-to-r from-cyan-500 to-teal-500"></i>
                 </div>
                 <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black text-slate-900 mb-4 md:mb-6 tracking-tight leading-tight">
                   Discover the <br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-teal-600">Future of Pharma</span>
                 </h1>
                 <p className="text-base md:text-lg lg:text-xl text-slate-600 mb-8 md:mb-12 max-w-2xl mx-auto font-medium leading-relaxed px-2">
                   Enter a molecule or disease area to launch agents for market analysis, patent landscape, and manufacturing feasibility.
                 </p>
              </div>
            )}

            <div className={`w-full z-20 ${result ? '' : 'max-w-3xl'}`}>
              <div
                className={`relative rounded-2xl border transition-all duration-300 ${
                  result
                    ? 'bg-white border-slate-200 shadow-sm'
                    : 'bg-white border-slate-200/90 shadow-lg shadow-slate-200/50'
                } focus-within:border-cyan-400 focus-within:ring-2 focus-within:ring-cyan-500/20 focus-within:shadow-md focus-within:shadow-cyan-500/5`}
              >
                <div className="relative">
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleRun(); } }}
                    placeholder={QUERY_PLACEHOLDER}
                    rows={1}
                    className={`w-full min-h-[48px] md:min-h-[52px] max-h-[280px] resize-none overflow-y-auto bg-transparent text-slate-800 placeholder-slate-400 outline-none transition-all box-border ${
                      result
                        ? 'py-3 md:py-4 pl-4 sm:pl-6 pr-24 sm:pr-28 md:pr-36 text-sm sm:text-base md:text-lg rounded-2xl'
                        : 'py-3 md:py-5 pl-4 sm:pl-6 pr-24 sm:pr-28 md:pr-36 text-sm sm:text-base md:text-lg font-medium rounded-2xl'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={handleRun}
                    disabled={loading || !input.trim()}
                    className="absolute top-2.5 md:top-3 right-2 sm:right-3 flex items-center justify-center gap-1 sm:gap-2 rounded-xl font-bold text-white text-xs sm:text-sm px-3 sm:px-4 md:px-6 py-2 md:py-2.5 transition-all duration-300 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 shadow-md shadow-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/40 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:shadow-md touch-target min-h-[44px]"
                  >
                    {loading ? (
                      <i className="fas fa-circle-notch animate-spin text-base" />
                    ) : (
                      <>
                        <span>Analyze</span>
                        <i className="fas fa-arrow-right text-xs opacity-90" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
            {error && <div className="mt-4 px-4 py-2.5 rounded-xl bg-red-50 border border-red-200 text-red-700 font-semibold text-sm">{error}</div>}
          </div>

          {/* Loading: orchestration message + animation */}
          {loading && (
             <div className="flex flex-col items-center justify-center py-24 flex-1">
                <div className="relative mb-10">
                  <div className="w-28 h-28 rounded-full border-4 border-slate-200 border-t-cyan-500 border-r-teal-500 animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <i className="fas fa-dna text-3xl text-cyan-500/80 animate-pulse" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-slate-800 mb-2">Orchestrating Agents</h3>
                <p className="text-slate-500 font-medium transition-opacity duration-300">
                  {LOADING_MESSAGES[loadingMessageIndex]}
                </p>
             </div>
          )}

          {/* Results View */}
          {result && !loading && (
            <div ref={resultsRef} className="space-y-10 animate-fade-in-up pb-20">
              {/* Molecular details (wider) | Feasibility + Symptoms (narrower) */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6 items-stretch min-h-0 lg:min-h-[480px]">
                <div className="lg:col-span-7 min-h-0 lg:min-h-[480px]">
                  <MolecularDetailsCard
                    data={result.visual_data?.molecular_details}
                    fallbackName={result.query_context?.drug}
                    compact
                  />
                </div>
                <div className="lg:col-span-5 flex flex-col gap-4 min-h-0 lg:min-h-[480px]">
                  <div className="shrink-0">
                    <GradingSection data={result.grading ?? undefined} />
                  </div>
                  {/* Brief details below Feasibility score */}
                  {result.visual_data?.molecular_details?.brief_details?.trim() && (
                    <div className="shrink-0 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Brief details</p>
                      <p className="text-slate-600 text-sm leading-relaxed">{result.visual_data.molecular_details.brief_details.trim()}</p>
                    </div>
                  )}
                  <div className="flex-1 min-h-0 flex flex-col">
                    <SymptomsDiseaseSideEffectsSummary
                      symptoms={result.query_context?.symptoms?.length ? result.query_context.symptoms : (result.clinical_trials_data?.extracted_insights?.symptoms ?? undefined)}
                      disease={result.query_context?.disease ?? (result.clinical_trials_data?.extracted_insights?.diseases?.[0] ?? undefined)}
                      sideEffects={result.query_context?.side_effects?.length ? result.query_context.side_effects : (result.clinical_trials_data?.extracted_insights?.side_effects ?? undefined)}
                      vertical
                    />
                  </div>
                </div>
              </div>

              {/* Professional P&ID Diagram — above Sales & Market Trend */}
              <div className="w-full" style={{ minHeight: '500px' }}>
                 <ProfessionalPID
                   pidData={result.pid_data}
                   teaData={result.tea_data}
                   drugName={result.visual_data?.molecular_details?.molecular_name ?? result.query_context?.drug}
                 />
              </div>

              {/* Sales & Market Trend + EXIM charts */}
              <MarketAndEximCharts
                marketData={result.visual_data?.market_data ?? null}
                eximData={result.visual_data?.exim_data ?? null}
                drugName={result.query_context?.drug}
              />

              {/* Competitor Intelligence — War Room */}
              <CompetitorIntelligenceCard
                costPerKgUsd={result.tea_data?.cost_per_kg_usd}
                drugName={result.query_context?.drug}
                marketPriceUsdPerKg={result.visual_data?.market_data?.typical_api_price_usd_per_kg}
              />

              {/* Advanced TEA Section - UPDATED with detailed PID-based analysis */}
              <div className="w-full">
                 <TeaSection visualData={result.visual_data} teaData={result.tea_data} />
              </div>

              {/* Drug Indications, Symptoms & Clinical Trial History */}
              <IndicationsAndTrialsSection
                queryContext={result.query_context}
                clinicalTrialsData={result.clinical_trials_data}
              />

              {/* Recommended plant locations (Demographic agent) + Google Map - below clinical trials */}
              <PlantSiteMap
                sites={result.visual_data?.demographic_data?.plant_site_recommendations ?? []}
                drugName={result.query_context?.drug}
              />

              {/* Final Investment Memorandum */}
              <div className="w-full animate-fade-in-up delay-300">
                <div className="flex items-center gap-3 mb-6">
                  <span className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600">
                    <i className="fas fa-file-contract text-sm"></i>
                  </span>
                  <h2 className="text-lg font-bold text-slate-800">Final Investment Memorandum</h2>
                </div>
                <InvestmentMemo
                  reportContent={result.analysis}
                  drugName={result.query_context?.drug}
                  indication={result.query_context?.disease}
                  grading={result.grading}
                />
              </div>

            </div>
          )}

        </main>
      </div>
    </div>
  );
};