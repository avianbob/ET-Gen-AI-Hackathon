import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plug, Check, X, Settings, ExternalLink, Key, Search } from 'lucide-react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import useAppStore from '../store';
import {
  getIntegrations,
  enableIntegration,
  disableIntegration,
  configureIntegration,
} from '../services/api';

interface Integration {
  id: string;
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  status: string;
  requiresApiKey?: boolean;
}

const DEFAULT_INTEGRATIONS: Integration[] = [
  { id: 'pubmed', name: 'PubMed', description: 'Biomedical literature from NCBI', category: 'Literature & Research', enabled: true, status: 'active' },
  { id: 'semantic_scholar', name: 'Semantic Scholar', description: 'Academic citation network & paper search', category: 'Literature & Research', enabled: true, status: 'active' },
  { id: 'drugbank', name: 'DrugBank', description: 'Comprehensive drug database', category: 'Literature & Research', enabled: true, status: 'active', requiresApiKey: true },
  { id: 'clinical_trials', name: 'ClinicalTrials.gov', description: 'NIH clinical trials registry', category: 'Clinical & Regulatory', enabled: true, status: 'active' },
  { id: 'openfda', name: 'OpenFDA', description: 'FDA adverse events & drug labeling', category: 'Clinical & Regulatory', enabled: true, status: 'active' },
  { id: 'dailymed', name: 'DailyMed', description: 'Drug labeling & SPL data', category: 'Clinical & Regulatory', enabled: true, status: 'active' },
  { id: 'rxnorm', name: 'RxNorm', description: 'Drug nomenclature mapping', category: 'Clinical & Regulatory', enabled: false, status: 'inactive' },
  { id: 'opentargets', name: 'OpenTargets', description: 'Target-disease association platform', category: 'Targets & Pathways', enabled: true, status: 'active' },
  { id: 'chembl', name: 'ChEMBL', description: 'Bioactivity assays & compound data', category: 'Targets & Pathways', enabled: true, status: 'active' },
  { id: 'kegg', name: 'KEGG Pathways', description: 'Biological pathway data', category: 'Targets & Pathways', enabled: true, status: 'active' },
  { id: 'uniprot', name: 'UniProt', description: 'Protein sequence & function', category: 'Targets & Pathways', enabled: false, status: 'inactive' },
  { id: 'iqvia', name: 'IQVIA Market Data', description: 'Market size, CAGR, unmet need analysis', category: 'Market & Epidemiology', enabled: true, status: 'active', requiresApiKey: true },
  { id: 'exim', name: 'EXIM Trade Data', description: 'Import-export trade flow analysis', category: 'Market & Epidemiology', enabled: true, status: 'active' },
  { id: 'who', name: 'WHO Essential Medicines', description: 'WHO essential medicines list', category: 'Market & Epidemiology', enabled: true, status: 'active' },
  { id: 'uspto', name: 'USPTO PatentsView', description: 'Patent filings & landscape analysis', category: 'Patents & IP', enabled: true, status: 'active' },
  { id: 'orange_book', name: 'FDA Orange Book', description: 'Patent & exclusivity listings', category: 'Patents & IP', enabled: true, status: 'active' },
  { id: 'epo', name: 'EPO Espacenet', description: 'European patent search', category: 'Patents & IP', enabled: false, status: 'inactive' },
  { id: 'web_intelligence', name: 'Web Intelligence', description: 'Guidelines, RWE & news aggregation', category: 'Intelligence & Knowledge', enabled: true, status: 'active' },
  { id: 'internal_kb', name: 'Internal Knowledge Base', description: 'Proprietary documents & PDFs', category: 'Intelligence & Knowledge', enabled: true, status: 'active' },
  { id: 'google_scholar', name: 'Google Scholar', description: 'Broad academic search', category: 'Intelligence & Knowledge', enabled: false, status: 'inactive' },
  { id: 'cortellis', name: 'Cortellis', description: 'Competitive intelligence & pipeline data', category: 'Premium', enabled: false, status: 'inactive', requiresApiKey: true },
  { id: 'evaluate_pharma', name: 'Evaluate Pharma', description: 'Pharma consensus forecasts', category: 'Premium', enabled: false, status: 'inactive', requiresApiKey: true },
];

const CATEGORIES = [
  'All',
  'Literature & Research',
  'Clinical & Regulatory',
  'Targets & Pathways',
  'Market & Epidemiology',
  'Patents & IP',
  'Intelligence & Knowledge',
  'Premium',
];

const Integrations: React.FC = () => {
  const storeIntegrations = useAppStore((s) => s.integrations);
  const setIntegrations = useAppStore((s) => s.setIntegrations);
  const setIntegrationsLoading = useAppStore((s) => s.setIntegrationsLoading);
  const updateIntegrationStatus = useAppStore((s) => s.updateIntegrationStatus);
  const integrationsLoading = useAppStore((s) => s.integrationsLoading);

  const [activeCategory, setActiveCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [configModal, setConfigModal] = useState<Integration | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [saving, setSaving] = useState(false);

  const integrations: Integration[] =
    storeIntegrations.length > 0
      ? (storeIntegrations as Integration[])
      : DEFAULT_INTEGRATIONS;

  useEffect(() => {
    const load = async () => {
      setIntegrationsLoading(true);
      try {
        const data = await getIntegrations();
        if (data?.length) setIntegrations(data);
        else setIntegrations(DEFAULT_INTEGRATIONS);
      } catch {
        setIntegrations(DEFAULT_INTEGRATIONS);
      }
    };
    if (storeIntegrations.length === 0) load();
  }, []);

  const filtered = useMemo(() => {
    let list = integrations;
    if (activeCategory !== 'All') {
      list = list.filter((i) => i.category === activeCategory);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (i) =>
          i.name.toLowerCase().includes(q) ||
          i.description.toLowerCase().includes(q)
      );
    }
    return list;
  }, [integrations, activeCategory, searchQuery]);

  const activeCount = integrations.filter((i) => i.enabled).length;
  const categoryCount = new Set(integrations.map((i) => i.category)).size;

  const handleToggle = async (integration: Integration) => {
    const next = !integration.enabled;
    updateIntegrationStatus(integration.id, next);
    try {
      if (next) await enableIntegration(integration.id);
      else await disableIntegration(integration.id);
    } catch {
      updateIntegrationStatus(integration.id, !next);
    }
  };

  const handleConfigure = async () => {
    if (!configModal || !apiKey.trim()) return;
    setSaving(true);
    try {
      await configureIntegration(configModal.id, { api_key: apiKey });
      updateIntegrationStatus(configModal.id, true);
    } catch {
      // keep modal open on failure
    }
    setSaving(false);
    setApiKey('');
    setConfigModal(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
            <Plug className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Integrations</h1>
            <p className="text-sm text-slate-600">Manage data source connections</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="teal" size="lg">{activeCount} active</Badge>
          <Badge variant="blue" size="lg">{categoryCount} categories</Badge>
        </div>
      </div>

      {/* Search & Filter */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search integrations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500/50"
            />
          </div>
          <div className="flex flex-wrap gap-1.5">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                  activeCategory === cat
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50 border border-transparent'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Integration Grid */}
      {integrationsLoading ? (
        <div className="flex items-center justify-center py-16">
          <svg className="animate-spin h-6 w-6 text-blue-400" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <AnimatePresence mode="popLayout">
            {filtered.map((integration, idx) => (
              <motion.div
                key={integration.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2, delay: idx * 0.03 }}
              >
                <Card hover className="flex flex-col h-full">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0 mr-3">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-sm font-semibold text-slate-900 truncate">
                          {integration.name}
                        </h3>
                        <Badge
                          variant={integration.enabled ? 'teal' : 'gray'}
                        >
                          {integration.enabled ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-600 line-clamp-2">
                        {integration.description}
                      </p>
                    </div>
                    <button
                      onClick={() => handleToggle(integration)}
                      className={`relative shrink-0 w-10 h-5.5 rounded-full transition-colors duration-200 ${
                        integration.enabled ? 'bg-emerald-500' : 'bg-slate-300'
                      }`}
                      style={{ minWidth: 40, height: 22 }}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-[18px] h-[18px] bg-white rounded-full shadow transition-transform duration-200 ${
                          integration.enabled ? 'translate-x-[18px]' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>
                  <div className="flex items-center justify-between mt-auto pt-3 border-t border-slate-200">
                    <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">
                      {integration.category}
                    </span>
                    {integration.requiresApiKey && (
                      <button
                        onClick={() => setConfigModal(integration)}
                        className="flex items-center gap-1 text-xs text-slate-600 hover:text-blue-400 transition-colors"
                      >
                        <Key className="w-3 h-3" />
                        <span>Configure</span>
                      </button>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {filtered.length === 0 && !integrationsLoading && (
        <Card className="text-center py-12">
          <Search className="w-8 h-8 text-slate-500 mx-auto mb-3" />
          <p className="text-sm text-slate-600">No integrations match your search.</p>
        </Card>
      )}

      {/* Configure Modal */}
      <Modal
        isOpen={!!configModal}
        onClose={() => {
          setConfigModal(null);
          setApiKey('');
        }}
        title={`Configure ${configModal?.name ?? ''}`}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              API Key
            </label>
            <div className="relative">
              <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key..."
                className="w-full pl-9 pr-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500/50"
              />
            </div>
          </div>
          <p className="text-xs text-slate-500">
            Your key is encrypted and stored securely. You can update or revoke it at any time.
          </p>
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setConfigModal(null);
                setApiKey('');
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<Check className="w-4 h-4" />}
              loading={saving}
              disabled={!apiKey.trim()}
              onClick={handleConfigure}
            >
              Save Configuration
            </Button>
          </div>
        </div>
      </Modal>
    </motion.div>
  );
};

export default Integrations;
