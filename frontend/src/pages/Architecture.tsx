import React from 'react';
import { motion } from 'framer-motion';
import {
  GitBranch, Cpu, Database, Globe, FlaskConical, TrendingUp,
  FileText, Shield, Layers, Zap,
} from 'lucide-react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import { ET_AGENT_GROUPS, DIMENSION_CONFIG, AGENTS } from '../utils/constants';

const ICON_MAP: Record<string, React.ReactNode> = {
  GitBranch: <GitBranch className="w-5 h-5" />,
  Cpu: <Cpu className="w-5 h-5" />,
  Database: <Database className="w-5 h-5" />,
  Globe: <Globe className="w-5 h-5" />,
  FlaskConical: <FlaskConical className="w-5 h-5" />,
  TrendingUp: <TrendingUp className="w-5 h-5" />,
  FileText: <FileText className="w-5 h-5" />,
  Shield: <Shield className="w-5 h-5" />,
  Layers: <Layers className="w-5 h-5" />,
  Zap: <Zap className="w-5 h-5" />,
  BookOpen: <FileText className="w-5 h-5" />,
  Stethoscope: <Shield className="w-5 h-5" />,
};

const SYSTEM_HIGHLIGHTS = [
  { label: 'AI Agents', value: `${AGENTS.length}`, icon: 'Cpu', color: 'text-blue-400' },
  { label: '4D Scoring', value: '4 Dimensions', icon: 'Layers', color: 'text-cyan-700' },
  { label: 'Orchestrator', value: 'LangGraph', icon: 'GitBranch', color: 'text-emerald-400' },
  { label: 'Pipeline Groups', value: `${Object.keys(ET_AGENT_GROUPS).length}`, icon: 'Zap', color: 'text-purple-400' },
];

const WORKFLOW_STEPS = [
  { step: 1, title: 'Query Input', desc: 'User enters a drug name, disease area, or natural-language query' },
  { step: 2, title: 'Query Understanding', desc: 'NLP classifier determines intent, extracts entities & complexity' },
  { step: 3, title: 'Agent Orchestration', desc: 'LangGraph routes to relevant ET worker groups in parallel' },
  { step: 4, title: 'Data Collection', desc: 'Agents query 15+ external APIs, internal KB, and uploaded files' },
  { step: 5, title: 'Evidence Synthesis', desc: 'Raw data is normalized, deduplicated, and cross-referenced' },
  { step: 6, title: '4D Scoring', desc: 'Composite score computed across 4 weighted dimensions' },
  { step: 7, title: 'Insight Generation', desc: 'LLM generates strengths, risks, opportunities & next steps' },
  { step: 8, title: 'Report Delivery', desc: 'Interactive results with export to PDF, Excel, and comparison' },
];

const TECH_STACK = {
  frontend: [
    { name: 'React 18', desc: 'Component framework' },
    { name: 'TypeScript', desc: 'Type safety' },
    { name: 'Tailwind CSS', desc: 'Utility-first styling' },
    { name: 'Zustand', desc: 'State management' },
    { name: 'Framer Motion', desc: 'Animations' },
    { name: 'React Router', desc: 'Client routing' },
  ],
  backend: [
    { name: 'FastAPI', desc: 'Async Python API (single unified host)' },
    { name: 'LangGraph', desc: 'Agent orchestration' },
    { name: 'LangChain', desc: 'LLM framework' },
    { name: 'Disk cache', desc: 'JSON under data/cache (no Redis in this repo)' },
    { name: 'Gemini / Groq', desc: 'LLM providers (configurable)' },
    { name: 'ChromaDB', desc: 'Vector store (RAG)' },
  ],
};

const stagger = {
  animate: { transition: { staggerChildren: 0.06 } },
};
const fadeUp = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
};

const Architecture: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-10"
    >
      {/* Hero */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 mb-4">
          <GitBranch className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
            System Architecture
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-3">
          PharmAI Intelligence Platform
        </h1>
        <p className="text-slate-600 max-w-2xl mx-auto">
          Multi-agent pharmaceutical intelligence system powered by LangGraph orchestration,
          4-dimensional scoring, and 15+ real-time data sources.
        </p>
      </div>

      {/* System Overview */}
      <motion.div
        variants={stagger}
        initial="initial"
        animate="animate"
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {SYSTEM_HIGHLIGHTS.map((item) => (
          <motion.div key={item.label} variants={fadeUp}>
            <Card className="text-center py-5">
              <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl bg-white/5 mb-3 ${item.color}`}>
                {ICON_MAP[item.icon]}
              </div>
              <p className="text-xl font-bold text-slate-900">{item.value}</p>
              <p className="text-xs text-slate-600 mt-1">{item.label}</p>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Workflow Pipeline */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-cyan-700" />
          Processing Pipeline
        </h2>
        <div className="relative">
          <div className="absolute left-6 top-8 bottom-8 w-px bg-gradient-to-b from-blue-500/40 via-purple-500/40 to-emerald-500/40 hidden md:block" />
          <motion.div
            variants={stagger}
            initial="initial"
            animate="animate"
            className="space-y-3"
          >
            {WORKFLOW_STEPS.map((ws) => (
              <motion.div key={ws.step} variants={fadeUp}>
                <Card className="flex items-start gap-4 py-3">
                  <div className="relative z-10 shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/20 flex items-center justify-center">
                    <span className="text-sm font-bold text-blue-400">{ws.step}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-slate-900">{ws.title}</h3>
                    <p className="text-xs text-slate-600 mt-0.5">{ws.desc}</p>
                  </div>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>

      {/* Agent Groups */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-blue-400" />
          ET Agent Groups
        </h2>
        <motion.div
          variants={stagger}
          initial="initial"
          animate="animate"
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
        >
          {Object.entries(ET_AGENT_GROUPS).map(([key, group]) => (
            <motion.div key={key} variants={fadeUp}>
              <Card hover className="h-full">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400">
                    {ICON_MAP[group.icon] || <Cpu className="w-5 h-5" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-slate-900 truncate">{group.name}</h3>
                  </div>
                  <Badge variant="blue">{group.agents.length}</Badge>
                </div>
                <p className="text-xs text-slate-600 mb-3">{group.description}</p>
                <div className="flex flex-wrap gap-1">
                  {group.agents.map((a: string) => (
                    <Badge key={a} variant="gray">{a.replace(/Agent|Pipeline/g, '')}</Badge>
                  ))}
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* 4D Scoring */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-700" />
          4-Dimensional Scoring
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(DIMENSION_CONFIG).map(([key, dim]) => (
            <Card key={key} className="relative overflow-hidden">
              <div
                className="absolute inset-y-0 left-0 w-1 rounded-l-xl"
                style={{ backgroundColor: dim.color }}
              />
              <div className="pl-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-slate-900">{dim.shortLabel}</span>
                  <span
                    className="text-lg font-bold"
                    style={{ color: dim.color }}
                  >
                    {(dim.weight * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-slate-600">{dim.description}</p>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-emerald-400" />
          Technology Stack
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(TECH_STACK).map(([section, items]) => (
            <Card key={section}>
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3">
                {section}
              </h3>
              <div className="space-y-2">
                {items.map((tech) => (
                  <div
                    key={tech.name}
                    className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-white/[0.03] border border-slate-200"
                  >
                    <span className="text-sm font-medium text-slate-900">{tech.name}</span>
                    <span className="text-xs text-slate-500">{tech.desc}</span>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default Architecture;
