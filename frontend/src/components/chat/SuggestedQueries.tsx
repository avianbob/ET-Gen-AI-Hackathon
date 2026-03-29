import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, TrendingUp, FlaskConical, FileText, Globe, Pill } from 'lucide-react';

const suggestions = [
  { text: 'What are the top drug repurposing opportunities for Metformin?', icon: Sparkles, color: 'text-cyan-600' },
  { text: 'Analyze the market landscape for GLP-1 receptor agonists', icon: TrendingUp, color: 'text-teal-600' },
  { text: 'Compare Aspirin vs Ibuprofen for cardiovascular indications', icon: FlaskConical, color: 'text-sky-600' },
  { text: 'What clinical trials are running for Thalidomide analogs?', icon: FileText, color: 'text-violet-600' },
  { text: 'Show me EXIM trade data for Paracetamol in India', icon: Globe, color: 'text-cyan-600' },
  { text: 'Generate a full report for Sildenafil repurposing', icon: Pill, color: 'text-teal-600' },
  { text: 'What is the patent landscape for Remdesivir?', icon: FileText, color: 'text-amber-600' },
  { text: 'Find biosimilar opportunities in oncology', icon: Sparkles, color: 'text-emerald-600' },
];

interface SuggestedQueriesProps {
  onSelect: (query: string) => void;
}

const SuggestedQueries: React.FC<SuggestedQueriesProps> = ({ onSelect }) => {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">How can I help you today?</h2>
        <p className="text-slate-600 text-sm">Ask me anything about drug repurposing, market analysis, or clinical trials</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-2xl mx-auto">
        {suggestions.map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => onSelect(s.text)}
              className="flex items-center gap-3 p-3 text-left bg-white/90 border border-slate-200/90 rounded-xl hover:border-cyan-300 hover:shadow-md hover:shadow-cyan-500/10 transition-all group shadow-sm"
            >
              <Icon className={`w-4 h-4 ${s.color} flex-shrink-0`} />
              <span className="text-sm text-slate-700 group-hover:text-slate-900 transition-colors">{s.text}</span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
};

export default SuggestedQueries;
