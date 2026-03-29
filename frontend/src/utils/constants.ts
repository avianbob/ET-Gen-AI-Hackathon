export const CONFIDENCE_LEVELS = {
  veryHigh: { min: 80, color: '#00D4AA', bgColor: 'bg-emerald-500/20', label: 'Very High' },
  high: { min: 65, color: '#4ADE80', bgColor: 'bg-green-500/20', label: 'High' },
  moderate: { min: 50, color: '#FFE600', bgColor: 'bg-yellow-500/20', label: 'Moderate' },
  low: { min: 35, color: '#FFB800', bgColor: 'bg-orange-500/20', label: 'Low' },
  veryLow: { min: 0, color: '#FF4757', bgColor: 'bg-red-500/20', label: 'Very Low' },
};

export const DIMENSION_CONFIG: Record<string, any> = {
  scientific_evidence: {
    weight: 0.4, label: 'Scientific Evidence', shortLabel: 'Scientific',
    icon: 'FlaskConical', color: '#00B4D8',
    description: 'Quality and quantity of scientific evidence supporting the indication',
  },
  market_opportunity: {
    weight: 0.25, label: 'Market Opportunity', shortLabel: 'Market',
    icon: 'TrendingUp', color: '#00D4AA',
    description: 'Market size, growth potential, and commercial viability',
  },
  competitive_landscape: {
    weight: 0.2, label: 'Competitive Position', shortLabel: 'Competition',
    icon: 'Users', color: '#FFE600',
    description: 'Level of competition and differentiation potential',
  },
  development_feasibility: {
    weight: 0.15, label: 'Development Feasibility', shortLabel: 'Feasibility',
    icon: 'Settings', color: '#A78BFA',
    description: 'Technical and regulatory feasibility of development',
  },
};

export const AGENTS = [
  { id: 'LiteratureAgent', name: 'PubMed', icon: 'BookOpen', description: 'PubMed & scientific literature', etGroup: 'web_intelligence' },
  { id: 'ClinicalTrialsAgent', name: 'Clinical Trials', icon: 'Stethoscope', description: 'ClinicalTrials.gov pipeline', etGroup: 'clinical_trials' },
  { id: 'BioactivityAgent', name: 'ChEMBL', icon: 'Dna', description: 'ChEMBL bioactivity assays', etGroup: 'web_intelligence' },
  { id: 'PatentAgent', name: 'USPTO Patents', icon: 'FileText', description: 'USPTO PatentsView landscape', etGroup: 'patent_landscape' },
  { id: 'InternalAgent', name: 'Internal KB', icon: 'Database', description: 'Internal knowledge base', etGroup: 'internal_knowledge' },
  { id: 'OpenFDAAgent', name: 'OpenFDA', icon: 'Shield', description: 'FDA adverse events & labeling', etGroup: 'clinical_trials' },
  { id: 'OpenTargetsAgent', name: 'OpenTargets', icon: 'Target', description: 'Target-disease associations', etGroup: 'web_intelligence' },
  { id: 'SemanticScholarAgent', name: 'Semantic Scholar', icon: 'GraduationCap', description: 'Academic citation network', etGroup: 'web_intelligence' },
  { id: 'DailyMedAgent', name: 'DailyMed', icon: 'Pill', description: 'Drug labeling & SPL data', etGroup: 'clinical_trials' },
  { id: 'KEGGAgent', name: 'KEGG Pathways', icon: 'GitBranch', description: 'Biological pathway data', etGroup: 'web_intelligence' },
  { id: 'UniProtAgent', name: 'UniProt', icon: 'Atom', description: 'Protein & function data', etGroup: 'web_intelligence' },
  { id: 'OrangeBookAgent', name: 'Orange Book', icon: 'Book', description: 'FDA patent/exclusivity data', etGroup: 'patent_landscape' },
  { id: 'RxNormAgent', name: 'RxNorm', icon: 'Layers', description: 'Drug nomenclature mapping', etGroup: 'clinical_trials' },
  { id: 'WHOAgent', name: 'WHO', icon: 'Globe', description: 'WHO essential medicines list', etGroup: 'web_intelligence' },
  { id: 'DrugBankAgent', name: 'DrugBank', icon: 'Boxes', description: 'Comprehensive drug database', etGroup: 'web_intelligence' },
  { id: 'IQVIAPipelineAgent', name: 'IQVIA Market', icon: 'TrendingUp', description: 'Market size, CAGR, unmet need', etGroup: 'iqvia_insights' },
  { id: 'EXIMPipelineAgent', name: 'EXIM Trade', icon: 'Globe', description: 'Import-export trade data', etGroup: 'exim_trade' },
  { id: 'WebIntelligencePipelineAgent', name: 'Web Intel', icon: 'BookOpen', description: 'Guidelines, RWE, news', etGroup: 'web_intelligence' },
  { id: 'ProcessDesignAgent', name: 'Process design', icon: 'Cog', description: 'CMC routes, QbD, scale-up narrative', etGroup: 'process_design' },
  { id: 'TechnoEconomicAgent', name: 'Techno-economics', icon: 'Calculator', description: 'COGS, capex sensitivity, TEA snapshot', etGroup: 'techno_economic' },
  { id: 'DemographicsPlantAgent', name: 'Demographics & sites', icon: 'MapPin', description: 'Patient burden & India plant clusters', etGroup: 'demographics_plant' },
  { id: 'ReportGenerator', name: 'Report assembly', icon: 'FileStack', description: 'Unified PDF / export packaging', etGroup: 'report_generator' },
];

export const ET_AGENT_GROUPS: Record<string, any> = {
  iqvia_insights: {
    name: 'IQVIA Insights Agent', icon: 'TrendingUp',
    description: 'Market size, CAGR, competitor analysis, and commercial viability',
    agents: ['IQVIAPipelineAgent'],
  },
  exim_trade: {
    name: 'EXIM Trade Agent', icon: 'Globe',
    description: 'Import-export trade data, supply chain analysis, geographic arbitrage',
    agents: ['EXIMPipelineAgent'],
  },
  patent_landscape: {
    name: 'Patent Landscape Agent', icon: 'FileText',
    description: 'USPTO patent filings, expiry timelines, FTO risk, biosimilar windows',
    agents: ['PatentAgent', 'OrangeBookAgent'],
  },
  clinical_trials: {
    name: 'Clinical Trials Agent', icon: 'Stethoscope',
    description: 'ClinicalTrials.gov pipeline, FDA data, drug labeling, nomenclature',
    agents: ['ClinicalTrialsAgent', 'OpenFDAAgent', 'DailyMedAgent', 'RxNormAgent'],
  },
  internal_knowledge: {
    name: 'Internal Knowledge Agent', icon: 'Database',
    description: 'Internal documents, uploaded PDFs, proprietary knowledge base',
    agents: ['InternalAgent'],
  },
  web_intelligence: {
    name: 'Web Intelligence Agent', icon: 'BookOpen',
    description: 'Literature, targets, pathways, proteins, guidelines, and publications',
    agents: ['LiteratureAgent', 'SemanticScholarAgent', 'OpenTargetsAgent', 'BioactivityAgent', 'KEGGAgent', 'UniProtAgent', 'WHOAgent', 'DrugBankAgent', 'WebIntelligencePipelineAgent'],
  },
  process_design: {
    name: 'Process Design Agent', icon: 'Cog',
    description: 'Process flow, unit operations, scale-up, and QbD-aligned CMC narrative',
    agents: ['ProcessDesignAgent'],
  },
  techno_economic: {
    name: 'Techno-Economic Agent', icon: 'Calculator',
    description: 'COGS drivers, batch economics, capex sensitivity—high-level TEA (not investment advice)',
    agents: ['TechnoEconomicAgent'],
  },
  demographics_plant: {
    name: 'Demographics & Plant Siting Agent', icon: 'MapPin',
    description: 'Patient burden, epidemiology hooks, and India manufacturing cluster considerations',
    agents: ['DemographicsPlantAgent'],
  },
  report_generator: {
    name: 'Report Generator Agent', icon: 'FileText',
    description: 'Assembles the unified search report (strategy, evidence, exports)',
    agents: ['ReportGenerator'],
  },
};

export const AGENT_STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'text-gray-400', bgColor: 'bg-gray-400/20' },
  running: { label: 'Running', color: 'text-blue-400', bgColor: 'bg-blue-400/20' },
  success: { label: 'Complete', color: 'text-green-400', bgColor: 'bg-green-400/20' },
  error: { label: 'Error', color: 'text-red-400', bgColor: 'bg-red-400/20' },
};

export const ROUTES = {
  CHAT: '/chat',
  DASHBOARD: '/dashboard',
  SEARCH: '/search',
  RESULTS: '/results',
  HISTORY: '/history',
  SAVED: '/saved',
  COMPARE: '/compare',
  INTEGRATIONS: '/integrations',
  SETTINGS: '/settings',
  ARCHITECTURE: '/architecture',
  LOGIN: '/login',
  HOME: '/',
};

export const NAV_ITEMS = {
  main: [
    { path: ROUTES.CHAT, label: 'AI Assistant', icon: 'MessageSquare', badge: 'NEW' },
    { path: ROUTES.DASHBOARD, label: 'Dashboard', icon: 'LayoutDashboard' },
    { path: ROUTES.SEARCH, label: 'Drug Search', icon: 'Search' },
    { path: ROUTES.HISTORY, label: 'History', icon: 'Clock' },
  ],
  intelligence: [
    { path: ROUTES.SAVED, label: 'Saved Opportunities', icon: 'Bookmark' },
    { path: ROUTES.COMPARE, label: 'Drug Comparison', icon: 'GitCompareArrows' },
  ],
  configuration: [
    { path: ROUTES.ARCHITECTURE, label: 'Architecture', icon: 'GitBranch' },
    { path: ROUTES.INTEGRATIONS, label: 'Integrations', icon: 'Plug' },
    { path: ROUTES.SETTINGS, label: 'Settings', icon: 'Settings' },
  ],
};

export const EVIDENCE_SOURCES: Record<string, any> = {
  literature: { label: 'Literature', icon: 'BookOpen', color: '#00B4D8' },
  clinical_trials: { label: 'Clinical Trials', icon: 'Stethoscope', color: '#00D4AA' },
  bioactivity: { label: 'Bioactivity', icon: 'Dna', color: '#A78BFA' },
  patent: { label: 'Patents', icon: 'FileText', color: '#FFE600' },
  internal: { label: 'Internal', icon: 'Database', color: '#F472B6' },
  openfda: { label: 'OpenFDA', icon: 'Shield', color: '#34D399' },
  opentargets: { label: 'OpenTargets', icon: 'Target', color: '#60A5FA' },
  semantic_scholar: { label: 'Semantic Scholar', icon: 'GraduationCap', color: '#FBBF24' },
  dailymed: { label: 'DailyMed', icon: 'Pill', color: '#F87171' },
  kegg: { label: 'KEGG', icon: 'GitBranch', color: '#A3E635' },
  uniprot: { label: 'UniProt', icon: 'Atom', color: '#C084FC' },
  orange_book: { label: 'Orange Book', icon: 'Book', color: '#FB923C' },
  rxnorm: { label: 'RxNorm', icon: 'Layers', color: '#2DD4BF' },
  who: { label: 'WHO', icon: 'Globe', color: '#818CF8' },
  drugbank: { label: 'DrugBank', icon: 'Boxes', color: '#F472B6' },
  market_data: { label: 'Market Data', icon: 'TrendingUp', color: '#00D4AA' },
  iqvia: { label: 'IQVIA', icon: 'TrendingUp', color: '#00D4AA' },
  exim: { label: 'EXIM Trade', icon: 'Globe', color: '#818CF8' },
};

export const INSIGHT_CATEGORIES: Record<string, any> = {
  strength: { label: 'Strength', icon: 'CheckCircle', color: 'text-teal-800', bgColor: 'bg-teal-50 border border-teal-100' },
  risk: { label: 'Risk', icon: 'AlertTriangle', color: 'text-red-800', bgColor: 'bg-red-50 border border-red-100' },
  opportunity: { label: 'Opportunity', icon: 'Lightbulb', color: 'text-amber-800', bgColor: 'bg-amber-50 border border-amber-100' },
  recommendation: { label: 'Next Step', icon: 'ArrowRight', color: 'text-sky-800', bgColor: 'bg-sky-50 border border-sky-100' },
};

export const ANIMATION_VARIANTS = {
  fadeIn: { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 } },
  slideUp: { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -20 } },
  slideDown: { initial: { opacity: 0, y: -20 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 20 } },
  scaleIn: { initial: { opacity: 0, scale: 0.95 }, animate: { opacity: 1, scale: 1 }, exit: { opacity: 0, scale: 0.95 } },
  staggerContainer: { animate: { transition: { staggerChildren: 0.05 } } },
  staggerItem: { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } },
};
