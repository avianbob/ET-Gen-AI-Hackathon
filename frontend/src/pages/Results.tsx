import React, { useState, useMemo, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Download,
  RefreshCw,
  FileText,
  BarChart3,
  Network,
  Shield,
  Sparkles,
  TrendingUp,
  FileStack,
  Clock,
  AlertTriangle,
  Database,
  Cog,
  Calculator,
  MapPin,
  Atom,
} from 'lucide-react';

import useAppStore from '../store';
import { exportPDF, exportExcel, exportJSON } from '../services/api';
import { downloadFile } from '../utils/helpers';

import OpportunityList from '../components/results/OpportunityList';
import EvidencePanel from '../components/results/EvidencePanel';
import StrategicBrief from '../components/results/StrategicBrief';
import RegulatoryPathway from '../components/results/RegulatoryPathway';
import AIInsights from '../components/results/AIInsights';
import FullReportExtensions from '../components/results/FullReportExtensions';
import ClinicalTrialsEvidencePanel, {
  countClinicalStyleEvidence,
} from '../components/results/ClinicalTrialsEvidencePanel';
import { MolecularDetailsCard } from '../components/MolecularDetailsCard';
import ReactMarkdown from 'react-markdown';
import { buildTemplateFullReportExtensions } from '../utils/fullReportTemplates';

import MarketDashboard from '../components/market/MarketDashboard';
import MarketOverview from '../components/market/MarketOverview';
import EvidenceGraph from '../components/visualizations/EvidenceGraph';
import SourceDistribution from '../components/visualizations/SourceDistribution';
import RadarChart from '../components/visualizations/RadarChart';

import CompositeScoreRing from '../components/scoring/CompositeScoreRing';
import ScoreBreakdown from '../components/scoring/ScoreBreakdown';
import { ProfessionalPID } from '../components/ProfessionalPID';
import { GradingSection, TeaSection } from '../components/ReportComponents';
import { PlantSiteMap } from '../components/PlantSiteMap';
import { MarketAndEximCharts } from '../components/MarketAndEximCharts';

import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import Tabs from '../components/common/Tabs';
import EmptyState from '../components/common/EmptyState';

const TAB_DEFS = [
  { id: 'opportunities', label: 'Opportunities', icon: <TrendingUp className="w-4 h-4" /> },
  { id: 'report', label: 'Report', icon: <FileText className="w-4 h-4" /> },
  { id: 'full-report', label: 'Full report', icon: <FileStack className="w-4 h-4" /> },
  { id: 'process-design', label: 'Process', icon: <Cog className="w-4 h-4" /> },
  { id: 'tea-analysis', label: 'TEA', icon: <Calculator className="w-4 h-4" /> },
  { id: 'demographics-sites', label: 'Sites', icon: <MapPin className="w-4 h-4" /> },
  { id: 'molecule-trials', label: 'Structure & trials', icon: <Atom className="w-4 h-4" /> },
  { id: 'market', label: 'Market', icon: <BarChart3 className="w-4 h-4" /> },
  { id: 'evidence', label: 'Evidence', icon: <FileText className="w-4 h-4" /> },
  { id: 'graph', label: 'Graph', icon: <Network className="w-4 h-4" /> },
  { id: 'strategy', label: 'Strategy', icon: <Shield className="w-4 h-4" /> },
  { id: 'ai-insights', label: 'AI Insights', icon: <Sparkles className="w-4 h-4" /> },
];

const Results: React.FC = () => {
  const { drugName: paramDrug } = useParams<{ drugName: string }>();
  const {
    searchResults,
    drugName: storeDrug,
    savedOpportunities,
    saveOpportunity,
    removeOpportunity,
    resetSearch,
  } = useAppStore();

  const drugName = paramDrug || storeDrug || 'Unknown Drug';

  const [activeTab, setActiveTab] = useState('opportunities');
  const [selectedOpp, setSelectedOpp] = useState<any>(null);
  const [evidencePanelOpen, setEvidencePanelOpen] = useState(false);
  const [exportLoading, setExportLoading] = useState<string | null>(null);

  const opportunities = useMemo(() => {
    if (!searchResults) return [];
    return searchResults.opportunities
      || searchResults.enhanced_indications
      || searchResults.indications
      || searchResults.results
      || [];
  }, [searchResults]);

  const allEvidence = useMemo(() => {
    if (!searchResults) return [];
    const ev = searchResults.all_evidence ?? searchResults.evidence ?? searchResults.evidence_items;
    if (Array.isArray(ev) && ev.length > 0) return ev;
    return opportunities.flatMap((o: any) => o.evidence_items ?? o.evidence ?? []);
  }, [searchResults, opportunities]);

  /** Extract numeric score from opportunity (handles composite_score object or direct number). Expect 0-100 for display. */
  const getOppScore = (o: any): number => {
    const cs = o?.composite_score ?? o?.compositeScore;
    if (typeof cs === 'number') return cs;
    if (cs && typeof cs.overall_score === 'number') return cs.overall_score;
    const s = o?.score ?? o?.confidence_score;
    if (typeof s === 'number') return s > 1 ? s : s * 100;
    return 0;
  };

  const overallScore = useMemo(() => {
    if (!searchResults) return 0;
    const g = searchResults.grading?.overall_score;
    if (typeof g === 'number') return g > 1 ? g : g * 100;
    if (typeof searchResults.composite_score === 'number') return searchResults.composite_score;
    if (typeof searchResults.compositeScore === 'number') return searchResults.compositeScore;
    if (opportunities.length === 0) return 0;
    const sum = opportunities.reduce((acc: number, o: any) => acc + getOppScore(o), 0);
    const avg = sum / opportunities.length;
    return Number.isFinite(avg) ? avg : 0;
  }, [searchResults, opportunities]);

  const overallDimensionScores = useMemo(() => {
    if (!searchResults) return {};
    const ds = searchResults.dimension_scores ?? searchResults.dimensionScores;
    if (ds && typeof ds === 'object') return ds;
    const g = searchResults.grading;
    if (g && typeof g === 'object') {
      const gradingToDim: Record<string, string> = {
        scientific_evidence: 'patents_and_trials',
        market_opportunity: 'market_demand',
        competitive_landscape: 'competition',
        development_feasibility: 'production_feasibility',
      };
      const out: Record<string, number> = {};
      Object.entries(gradingToDim).forEach(([dim, gradKey]) => {
        const v = (g as Record<string, unknown>)[gradKey];
        out[dim] = typeof v === 'number' ? (v > 1 ? v : v * 100) : 0;
      });
      return out;
    }
    if (opportunities.length === 0) return {};
    const dims = ['scientific_evidence', 'market_opportunity', 'competitive_landscape', 'development_feasibility'];
    const result: Record<string, number> = {};
    dims.forEach((d) => {
      const scores = opportunities
        .map((o: any) => {
          const cs = o?.composite_score ?? o?.compositeScore;
          const sub = cs?.[d];
          const v = typeof sub === 'object' && sub?.score != null ? sub.score : (o.dimension_scores ?? o.dimensionScores ?? o.scores ?? {})[d];
          return typeof v === 'number' ? v : null;
        })
        .filter((v: any): v is number => v != null);
      result[d] = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    });
    return result;
  }, [searchResults, opportunities]);

  const savedIds = useMemo(
    () => savedOpportunities.map((o: any) => o.id),
    [savedOpportunities]
  );

  const synthesisText = useMemo(() => {
    if (!searchResults) return '';
    return (
      searchResults.synthesis
      || searchResults.ai_synthesis
      || searchResults.aiSynthesis
      || searchResults.llm_analysis
      || ''
    );
  }, [searchResults]);

  const fullReportExt = useMemo(
    () => searchResults?.full_report_extensions || searchResults?.fullReportExtensions,
    [searchResults]
  );

  const topIndicationsCsv = useMemo(() => {
    return opportunities
      .slice(0, 8)
      .map((o: any) => (o.indication || o.disease || '').trim())
      .filter(Boolean)
      .join(', ');
  }, [opportunities]);

  const effectiveExt = useMemo(() => {
    const tpl = buildTemplateFullReportExtensions(drugName, topIndicationsCsv);
    const api = fullReportExt as Record<string, string | undefined> | undefined;
    if (!api) return tpl;
    return {
      process_design: (api.process_design || api.processDesign || '').trim() || tpl.process_design,
      techno_economic: (api.techno_economic || api.technoEconomic || '').trim() || tpl.techno_economic,
      demographics_sites:
        (api.demographics_sites || api.demographicsSites || '').trim() || tpl.demographics_sites,
    };
  }, [drugName, topIndicationsCsv, fullReportExt]);

  const molecularDetails = useMemo(
    () => searchResults?.visual_data?.molecular_details ?? searchResults?.molecular_details,
    [searchResults]
  );

  const clinicalStyleEvidenceCount = useMemo(
    () => countClinicalStyleEvidence(allEvidence),
    [allEvidence]
  );

  const topSnapshotOpps = useMemo(() => opportunities.slice(0, 5), [opportunities]);

  const handleSave = useCallback(
    (opp: any) => {
      const id = opp.id || `${opp.indication || opp.disease}`;
      if (savedIds.includes(id)) {
        removeOpportunity(id);
      } else {
        saveOpportunity({ ...opp, id, drugName, savedAt: new Date().toISOString() });
      }
    },
    [savedIds, saveOpportunity, removeOpportunity, drugName]
  );

  const handleSelect = useCallback((opp: any) => {
    setSelectedOpp(opp);
    setEvidencePanelOpen(true);
  }, []);

  const handleExport = useCallback(
    async (format: 'pdf' | 'excel' | 'json') => {
      if (!searchResults) return;
      setExportLoading(format);
      try {
        if (format === 'pdf') {
          const blob = await exportPDF(searchResults);
          downloadFile(blob, `${drugName}_report.pdf`);
        } else if (format === 'excel') {
          const blob = await exportExcel(searchResults);
          downloadFile(blob, `${drugName}_report.xlsx`);
        } else {
          const data = await exportJSON(searchResults);
          const jsonStr = JSON.stringify(data, null, 2);
          downloadFile(jsonStr, `${drugName}_report.json`, 'application/json');
        }
      } catch {
        // export failed silently
      } finally {
        setExportLoading(null);
      }
    },
    [searchResults, drugName]
  );

  if (!searchResults) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <EmptyState
          icon={<FileText className="w-12 h-12" />}
          title="No Results Available"
          description="Run a drug search to see repurposing opportunities and analysis."
          action={
            <Button variant="primary" onClick={resetSearch}>
              Start New Search
            </Button>
          }
        />
      </div>
    );
  }

  const tabsWithCounts = TAB_DEFS.map((t) => {
    if (t.id === 'opportunities') return { ...t, count: opportunities.length };
    if (t.id === 'evidence') return { ...t, count: allEvidence.length };
    if (t.id === 'molecule-trials') return { ...t, count: clinicalStyleEvidenceCount };
    return t;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div className="flex items-center gap-4">
          <CompositeScoreRing score={overallScore} size={72} strokeWidth={6} />
          <div>
            <h1 className="text-2xl font-bold text-slate-900 capitalize">{drugName}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="yellow" size="lg">
                {opportunities.length} opportunit{opportunities.length === 1 ? 'y' : 'ies'}
              </Badge>
              <Badge variant="teal" size="sm">
                {allEvidence.length} evidence items
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw className="w-4 h-4" />}
            onClick={resetSearch}
          >
            Re-analyze
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download className="w-4 h-4" />}
            loading={exportLoading === 'pdf'}
            onClick={() => handleExport('pdf')}
          >
            PDF
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download className="w-4 h-4" />}
            loading={exportLoading === 'excel'}
            onClick={() => handleExport('excel')}
          >
            Excel
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download className="w-4 h-4" />}
            loading={exportLoading === 'json'}
            onClick={() => handleExport('json')}
          >
            JSON
          </Button>
        </div>
      </motion.div>

      {/* Score Breakdown Summary */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-start gap-6">
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Score Breakdown</h3>
            <ScoreBreakdown scores={overallDimensionScores} />
          </div>
          <div className="w-px bg-slate-100 hidden sm:block self-stretch" />
          <div className="sm:w-72 sm:min-w-[280px]">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Radar Overview</h3>
            <RadarChart
              data={Object.entries(overallDimensionScores).map(([dimension, score]) => ({
                dimension,
                score: score as number,
              }))}
              className="min-h-[280px]"
            />
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs tabs={tabsWithCounts} active={activeTab} onChange={setActiveTab} />

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'opportunities' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <OpportunityList
                  opportunities={opportunities}
                  drugName={drugName}
                  onSelect={handleSelect}
                  onSave={handleSave}
                  savedIds={savedIds}
                />
              </div>
              <div className="space-y-4">
                {selectedOpp ? (
                  <>
                    <Card>
                      <h3 className="text-sm font-semibold text-slate-900 mb-3">
                        {selectedOpp.indication || selectedOpp.disease || 'Selected Opportunity'}
                      </h3>
                      <CompositeScoreRing
                        score={getOppScore(selectedOpp)}
                        size={100}
                        strokeWidth={8}
                        className="mx-auto mb-4"
                      />
                      <ScoreBreakdown
                        scores={(() => {
                          const cs = selectedOpp?.composite_score ?? selectedOpp?.compositeScore;
                          if (cs && typeof cs === 'object') {
                            const dims = ['scientific_evidence', 'market_opportunity', 'competitive_landscape', 'development_feasibility'];
                            const out: Record<string, number> = {};
                            dims.forEach((d) => {
                              const sub = cs[d];
                              out[d] = typeof sub === 'object' && sub?.score != null ? sub.score : 0;
                            });
                            return out;
                          }
                          return selectedOpp?.dimension_scores ?? selectedOpp?.dimensionScores ?? selectedOpp?.scores ?? {};
                        })()}
                      />
                    </Card>
                    {(selectedOpp.market_data || selectedOpp.marketData) && (
                      <MarketOverview
                        indication={selectedOpp.indication || selectedOpp.disease || ''}
                        marketData={selectedOpp.market_data || selectedOpp.marketData}
                      />
                    )}
                  </>
                ) : (
                  <Card className="flex items-center justify-center min-h-[200px]">
                    <p className="text-sm text-slate-500">Select an opportunity to see details</p>
                  </Card>
                )}
              </div>
            </div>
          )}

          {activeTab === 'report' && (
            <div className="space-y-8">
              {(searchResults?.pid_data || searchResults?.tea_data || searchResults?.grading) ? (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    <div className="lg:col-span-8">
                      <div className="w-full" style={{ minHeight: '400px' }}>
                        <ProfessionalPID
                          pidData={searchResults?.pid_data}
                          teaData={searchResults?.tea_data}
                          drugName={drugName}
                        />
                      </div>
                    </div>
                    <div className="lg:col-span-4">
                      <GradingSection data={searchResults?.grading} />
                    </div>
                  </div>
                  <TeaSection visualData={searchResults?.visual_data} teaData={searchResults?.tea_data} />
                  <MarketAndEximCharts
                    marketData={searchResults?.visual_data?.market_data ?? searchResults?.market_data}
                    eximData={searchResults?.visual_data?.exim_data ?? searchResults?.exim_data}
                    drugName={drugName}
                  />
                  <PlantSiteMap
                    sites={searchResults?.visual_data?.demographic_data?.plant_site_recommendations ?? []}
                    drugName={drugName}
                  />
                </>
              ) : (
                <Card className="border-amber-100 bg-amber-50/40">
                  <p className="text-sm text-slate-600">
                    Run a fresh search (with cache cleared) to generate process design, techno-economics, and site analysis.
                    Older cached results may not include these dashboard components.
                  </p>
                  <Button variant="primary" className="mt-4" onClick={resetSearch}>
                    Start New Search
                  </Button>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'market' && (
            <div className="space-y-6">
              <MarketAndEximCharts
                marketData={searchResults?.visual_data?.market_data ?? searchResults?.market_data}
                eximData={searchResults?.visual_data?.exim_data ?? searchResults?.exim_data}
                drugName={drugName}
              />
              {(!searchResults?.visual_data?.market_data && !searchResults?.visual_data?.exim_data) && (
                <MarketDashboard
                  data={searchResults?.market_data || searchResults?.marketData || searchResults?.market}
                />
              )}
              {selectedOpp && (
                <MarketOverview
                  indication={selectedOpp.indication || selectedOpp.disease || ''}
                  marketData={selectedOpp.market_data || selectedOpp.marketData}
                />
              )}
            </div>
          )}

          {activeTab === 'evidence' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card>
                  <h3 className="text-sm font-semibold text-slate-900 mb-4">Evidence Items</h3>
                  {allEvidence.length > 0 ? (
                    <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                      {allEvidence.map((item: any, idx: number) => (
                        <div
                          key={item.id || idx}
                          className="bg-slate-50 border border-slate-200 rounded-lg p-3"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <Badge variant={item.source === 'clinical_trials' ? 'teal' : 'blue'} size="sm">
                              {item.source || item.type || 'unknown'}
                            </Badge>
                            {(item.relevance_score ?? item.relevanceScore) != null && (
                              <span className="text-[11px] text-slate-600">
                                Relevance: {Number(item.relevance_score ?? item.relevanceScore).toFixed(1)}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-slate-700">
                            {item.summary || item.title || item.description || ''}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="No Evidence" description="No evidence data available." />
                  )}
                </Card>
              </div>
              <div>
                <Card>
                  <h3 className="text-sm font-semibold text-slate-900 mb-4">Source Distribution</h3>
                  <SourceDistribution evidence={allEvidence} className="h-64" />
                </Card>
              </div>
            </div>
          )}

          {activeTab === 'graph' && (
            <Card className="min-h-[500px]">
              <EvidenceGraph data={searchResults} className="h-[500px]" />
            </Card>
          )}

          {activeTab === 'full-report' && (
            <div className="space-y-6">
              <Card className="border-slate-200 bg-slate-50/50">
                <div className="flex flex-col sm:flex-row sm:flex-wrap gap-4 sm:items-center sm:justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <Database className="w-4 h-4 text-cyan-600" />
                      Report run summary
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">
                      Pipeline metadata for this drug search (aligned with dashboard-style reporting).
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-700">
                      <Clock className="w-3.5 h-3.5 text-cyan-600" />
                      {searchResults.execution_time != null
                        ? `${Number(searchResults.execution_time).toFixed(1)}s runtime`
                        : 'Runtime n/a'}
                    </span>
                    {searchResults.cached && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-900">
                        Cached result
                      </span>
                    )}
                    {Array.isArray(searchResults.errors) && searchResults.errors.length > 0 && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-50 border border-red-100 text-red-800">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        {searchResults.errors.length} warning{searchResults.errors.length !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                </div>
              </Card>

              <FullReportExtensions data={effectiveExt} drugName={drugName} showEmptyHint={false} />

              {topSnapshotOpps.length > 0 && (
                <Card>
                  <h3 className="text-sm font-semibold text-slate-900 mb-3">Top opportunities snapshot</h3>
                  <div className="space-y-2">
                    {topSnapshotOpps.map((o: any, i: number) => {
                      const ind = o.indication || o.disease || `Opportunity ${i + 1}`;
                      const sc = getOppScore(o);
                      const displayScore = Number.isFinite(sc) ? sc.toFixed(1) : '0';
                      return (
                        <div
                          key={ind + i}
                          className="flex items-center justify-between gap-3 py-2 border-b border-slate-100 last:border-0"
                        >
                          <span className="text-sm text-slate-800 truncate">{ind}</span>
                          <Badge variant="teal" size="sm">
                            {displayScore}
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}

              {synthesisText ? (
                <Card>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-cyan-600" />
                      AI synthesis (preview)
                    </h3>
                    <Button variant="ghost" size="sm" onClick={() => setActiveTab('ai-insights')}>
                      Open full AI Insights
                    </Button>
                  </div>
                  <div className="prose prose-sm prose-slate max-w-none max-h-72 overflow-y-auto pr-1 prose-p:text-slate-600">
                    <ReactMarkdown>
                      {synthesisText.length > 3500 ? `${synthesisText.slice(0, 3500)}…` : synthesisText}
                    </ReactMarkdown>
                  </div>
                </Card>
              ) : null}

              <StrategicBrief
                data={searchResults.strategic_brief || searchResults.strategicBrief || searchResults.strategy}
                drugName={drugName}
              />
              <RegulatoryPathway
                indication={
                  selectedOpp?.indication || selectedOpp?.disease || opportunities[0]?.indication || drugName
                }
                data={searchResults.regulatory_pathway || searchResults.regulatoryPathway}
              />
            </div>
          )}

          {activeTab === 'process-design' && (
            <div className="space-y-6">
              <div className="w-full" style={{ minHeight: '500px' }}>
                <ProfessionalPID
                  pidData={searchResults?.pid_data}
                  teaData={searchResults?.tea_data}
                  drugName={drugName}
                />
              </div>
              {effectiveExt.process_design?.trim() && (
                <Card>
                  <div className="flex items-center gap-2 mb-3">
                    <Cog className="w-4 h-4 text-cyan-600" />
                    <h3 className="text-sm font-semibold text-slate-900">Process design summary</h3>
                  </div>
                  <div className="prose prose-sm prose-slate max-w-none prose-p:text-slate-700">
                    <ReactMarkdown>{effectiveExt.process_design}</ReactMarkdown>
                  </div>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'tea-analysis' && (
            <div className="space-y-6">
              <TeaSection visualData={searchResults?.visual_data ?? {}} teaData={searchResults?.tea_data} />
              {effectiveExt.techno_economic?.trim() && (
                <Card>
                  <div className="flex items-center gap-2 mb-3">
                    <Calculator className="w-4 h-4 text-cyan-600" />
                    <h3 className="text-sm font-semibold text-slate-900">Techno-economics summary</h3>
                  </div>
                  <div className="prose prose-sm prose-slate max-w-none prose-p:text-slate-700">
                    <ReactMarkdown>{effectiveExt.techno_economic}</ReactMarkdown>
                  </div>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'demographics-sites' && (
            <div className="space-y-6">
              <PlantSiteMap
                sites={searchResults?.visual_data?.demographic_data?.plant_site_recommendations ?? []}
                drugName={drugName}
              />
              {effectiveExt.demographics_sites?.trim() && (
                <Card>
                  <div className="flex items-center gap-2 mb-3">
                    <MapPin className="w-4 h-4 text-cyan-600" />
                    <h3 className="text-sm font-semibold text-slate-900">Demographics summary</h3>
                  </div>
                  <div className="prose prose-sm prose-slate max-w-none prose-p:text-slate-700">
                    <ReactMarkdown>{effectiveExt.demographics_sites}</ReactMarkdown>
                  </div>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'molecule-trials' && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
              <MolecularDetailsCard data={molecularDetails} fallbackName={drugName} />
              <ClinicalTrialsEvidencePanel evidence={allEvidence} drugName={drugName} />
            </div>
          )}

          {activeTab === 'strategy' && (
            <div className="space-y-6">
              <StrategicBrief
                data={searchResults.strategic_brief || searchResults.strategicBrief || searchResults.strategy}
                drugName={drugName}
              />
              <RegulatoryPathway
                indication={
                  selectedOpp?.indication || selectedOpp?.disease || opportunities[0]?.indication || drugName
                }
                data={searchResults.regulatory_pathway || searchResults.regulatoryPathway}
              />
            </div>
          )}

          {activeTab === 'ai-insights' && (
            <AIInsights
              synthesis={
                searchResults.synthesis
                || searchResults.ai_synthesis
                || searchResults.aiSynthesis
                || searchResults.llm_analysis
                || 'No AI synthesis available for this analysis.'
              }
              insights={searchResults.insights || searchResults.ai_insights || searchResults.aiInsights}
            />
          )}
        </motion.div>
      </AnimatePresence>

      {/* Evidence Slide-over Panel */}
      <EvidencePanel
        isOpen={evidencePanelOpen}
        onClose={() => setEvidencePanelOpen(false)}
        evidence={selectedOpp?.evidence || allEvidence}
        indication={selectedOpp?.indication || selectedOpp?.disease}
      />
    </div>
  );
};

export default Results;
