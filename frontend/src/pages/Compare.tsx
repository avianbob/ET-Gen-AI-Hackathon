import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GitCompareArrows, Plus, X, Crown, TrendingUp, Search } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';
import { useAppStore } from '../store';
import { compareDrugs } from '../services/api';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';

const MAX_DRUGS = 3;
const DRUG_COLORS = ['#FFE600', '#00D4AA', '#00B4D8'];
const DIMENSION_KEYS = ['scientific_evidence', 'market_opportunity', 'competitive_landscape', 'development_feasibility'];
const DIMENSION_LABELS: Record<string, string> = {
  scientific_evidence: 'Scientific',
  market_opportunity: 'Market',
  competitive_landscape: 'Competition',
  development_feasibility: 'Feasibility',
};

const Compare: React.FC = () => {
  const { searchHistory } = useAppStore();
  const [selected, setSelected] = useState<string[]>([]);
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [selectorQuery, setSelectorQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const uniqueDrugs = useMemo(() => {
    const seen = new Set<string>();
    return searchHistory
      .filter((h: any) => {
        const name = h.drugName?.toLowerCase();
        if (!name || seen.has(name)) return false;
        seen.add(name);
        return true;
      })
      .map((h: any) => h.drugName);
  }, [searchHistory]);

  const filteredDrugs = useMemo(() => {
    if (!selectorQuery.trim()) return uniqueDrugs.filter((d) => !selected.includes(d));
    const q = selectorQuery.toLowerCase();
    return uniqueDrugs.filter((d) => d.toLowerCase().includes(q) && !selected.includes(d));
  }, [uniqueDrugs, selectorQuery, selected]);

  const addDrug = (name: string) => {
    if (selected.length >= MAX_DRUGS) return;
    setSelected((prev) => [...prev, name]);
    setSelectorOpen(false);
    setSelectorQuery('');
    setResult(null);
  };

  const removeDrug = (name: string) => {
    setSelected((prev) => prev.filter((d) => d !== name));
    setResult(null);
  };

  const handleCompare = async () => {
    if (selected.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const data = await compareDrugs(selected);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  const radarData = useMemo(() => {
    if (!result?.drugs) return [];
    return DIMENSION_KEYS.map((dim) => {
      const entry: any = { dimension: DIMENSION_LABELS[dim] || dim };
      result.drugs.forEach((drug: any, idx: number) => {
        entry[drug.name] = drug.dimensions?.[dim] ?? 0;
      });
      return entry;
    });
  }, [result]);

  const overallScores = useMemo(() => {
    if (!result?.drugs) return [];
    return result.drugs.map((drug: any) => ({
      name: drug.name,
      score: drug.compositeScore ?? drug.overall_score ?? 0,
    }));
  }, [result]);

  const dimensionLeaders = useMemo(() => {
    if (!result?.drugs) return {};
    const leaders: Record<string, { name: string; score: number }> = {};
    for (const dim of DIMENSION_KEYS) {
      let best = { name: '', score: -1 };
      for (const drug of result.drugs) {
        const s = drug.dimensions?.[dim] ?? 0;
        if (s > best.score) best = { name: drug.name, score: s };
      }
      leaders[dim] = best;
    }
    return leaders;
  }, [result]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Drug Comparison</h1>
        <p className="text-sm text-slate-600 mt-1">Compare up to {MAX_DRUGS} drugs side by side</p>
      </div>

      {/* Drug selector slots */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {Array.from({ length: MAX_DRUGS }).map((_, idx) => {
          const drug = selected[idx];
          return (
            <Card key={idx} className="flex items-center justify-center min-h-[80px]">
              {drug ? (
                <div className="flex items-center gap-3 w-full">
                  <div
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: DRUG_COLORS[idx] }}
                  />
                  <span className="text-sm font-semibold text-slate-900 flex-1 truncate">{drug}</span>
                  <button
                    onClick={() => removeDrug(drug)}
                    className="text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => { setSelectorOpen(true); setSelectorQuery(''); }}
                  disabled={selected.length >= MAX_DRUGS}
                  className="flex flex-col items-center gap-1 text-slate-500 hover:text-cyan-700 transition-colors disabled:opacity-30"
                >
                  <Plus className="w-6 h-6" />
                  <span className="text-xs">Add Drug</span>
                </button>
              )}
            </Card>
          );
        })}
      </div>

      {/* Drug selector popover */}
      <AnimatePresence>
        {selectorOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <Card className="space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  autoFocus
                  type="text"
                  placeholder="Search drugs from history..."
                  value={selectorQuery}
                  onChange={(e) => setSelectorQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              {filteredDrugs.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-3">No drugs found in search history</p>
              ) : (
                <div className="max-h-48 overflow-y-auto space-y-1">
                  {filteredDrugs.map((d) => (
                    <button
                      key={d}
                      onClick={() => addDrug(d)}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-md transition-colors"
                    >
                      {d}
                    </button>
                  ))}
                </div>
              )}
              <div className="flex justify-end">
                <Button variant="ghost" size="xs" onClick={() => setSelectorOpen(false)}>Cancel</Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Compare button */}
      <div className="flex items-center gap-3">
        <Button
          variant="primary"
          icon={<GitCompareArrows className="w-4 h-4" />}
          onClick={handleCompare}
          loading={loading}
          disabled={selected.length < 2}
        >
          Compare {selected.length} Drug{selected.length !== 1 ? 's' : ''}
        </Button>
        {error && <span className="text-sm text-red-400">{error}</span>}
      </div>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Overall score bars */}
            <Card>
              <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-700" />
                Overall Scores
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={overallScores} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" tick={{ fill: '#E5E7EB', fontSize: 12 }} width={100} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }}
                    labelStyle={{ color: '#F3F4F6' }}
                    itemStyle={{ color: '#FFE600' }}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {overallScores.map((_: any, i: number) => (
                      <rect key={i} fill={DRUG_COLORS[i % DRUG_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            {/* Radar chart overlay */}
            {radarData.length > 0 && (
              <Card>
                <h3 className="text-sm font-semibold text-slate-700 mb-4">Dimension Overlay</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#374151" />
                    <PolarAngleAxis dataKey="dimension" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
                    <PolarRadiusAxis domain={[0, 100]} tick={{ fill: '#6B7280', fontSize: 10 }} />
                    {result.drugs.map((drug: any, idx: number) => (
                      <Radar
                        key={drug.name}
                        name={drug.name}
                        dataKey={drug.name}
                        stroke={DRUG_COLORS[idx]}
                        fill={DRUG_COLORS[idx]}
                        fillOpacity={0.15}
                        strokeWidth={2}
                      />
                    ))}
                    <Legend wrapperStyle={{ color: '#D1D5DB', fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: 8 }}
                      labelStyle={{ color: '#F3F4F6' }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </Card>
            )}

            {/* Dimension leaders */}
            <Card>
              <h3 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
                <Crown className="w-4 h-4 text-cyan-700" />
                Dimension Leaders
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(dimensionLeaders).map(([dim, leader]) => (
                  <div key={dim} className="flex items-center justify-between p-3 rounded-lg bg-slate-100/40 border border-slate-200">
                    <div>
                      <p className="text-xs text-slate-500">{DIMENSION_LABELS[dim] || dim}</p>
                      <p className="text-sm font-semibold text-slate-900">{leader.name}</p>
                    </div>
                    <Badge variant="yellow" size="md">{Math.round(leader.score)}</Badge>
                  </div>
                ))}
              </div>
            </Card>

            {/* Head-to-head matrix */}
            {result.drugs?.length > 1 && (
              <Card>
                <h3 className="text-sm font-semibold text-slate-700 mb-4">Head-to-Head Indication Matrix</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr>
                        <th className="text-left text-xs text-slate-500 font-medium pb-2 pr-4">Dimension</th>
                        {result.drugs.map((drug: any, i: number) => (
                          <th key={drug.name} className="text-center text-xs font-medium pb-2 px-2" style={{ color: DRUG_COLORS[i] }}>
                            {drug.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {DIMENSION_KEYS.map((dim) => {
                        const scores = result.drugs.map((d: any) => d.dimensions?.[dim] ?? 0);
                        const maxScore = Math.max(...scores);
                        return (
                          <tr key={dim} className="border-t border-slate-200/50">
                            <td className="py-2 pr-4 text-xs text-slate-600">{DIMENSION_LABELS[dim]}</td>
                            {scores.map((score: number, i: number) => (
                              <td key={i} className="py-2 px-2 text-center">
                                <span className={`text-xs font-medium ${score === maxScore ? 'text-cyan-700' : 'text-slate-600'}`}>
                                  {Math.round(score)}
                                  {score === maxScore && <Crown className="w-3 h-3 inline ml-1 -mt-0.5" />}
                                </span>
                              </td>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}

            {/* Evidence source breakdown */}
            {result.drugs?.some((d: any) => d.evidenceSources || d.evidence_sources) && (
              <Card>
                <h3 className="text-sm font-semibold text-slate-700 mb-4">Evidence Source Breakdown</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {result.drugs.map((drug: any, idx: number) => {
                    const sources = drug.evidenceSources || drug.evidence_sources || {};
                    return (
                      <div key={drug.name} className="space-y-2">
                        <p className="text-xs font-semibold" style={{ color: DRUG_COLORS[idx] }}>{drug.name}</p>
                        {Object.entries(sources).length > 0 ? (
                          Object.entries(sources).map(([src, count]) => (
                            <div key={src} className="flex items-center justify-between text-xs">
                              <span className="text-slate-600 capitalize">{src.replace(/_/g, ' ')}</span>
                              <Badge variant="gray" size="sm">{String(count)}</Badge>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-slate-500">No source data</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {!result && !loading && selected.length === 0 && (
        <EmptyState
          icon={<GitCompareArrows className="w-12 h-12" />}
          title="Start a comparison"
          description="Select 2 or 3 drugs from your search history to compare their repurposing potential side by side."
        />
      )}
    </div>
  );
};

export default Compare;
