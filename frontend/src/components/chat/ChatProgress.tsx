import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface ChatProgressProps {
  agentProgress: Record<string, any>;
  workflowStatus: any;
}

const ChatProgress: React.FC<ChatProgressProps> = ({ agentProgress, workflowStatus }) => {
  const activeAgents = Object.entries(agentProgress).filter(([, v]) => v.status === 'running');

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-3">
      <div className="w-8 h-8 bg-cyan-100 border border-cyan-200 rounded-full flex items-center justify-center flex-shrink-0">
        <Loader2 className="w-4 h-4 text-cyan-600 animate-spin" />
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[80%] shadow-sm">
        <p className="text-sm text-slate-700 mb-2">
          {workflowStatus?.message || 'Processing your request...'}
        </p>
        {activeAgents.length > 0 && (
          <div className="space-y-1">
            {activeAgents.slice(0, 3).map(([name, info]) => (
              <div key={name} className="flex items-center gap-2 text-xs text-slate-500">
                <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-pulse" />
                <span>{name}: {info.message}</span>
              </div>
            ))}
            {activeAgents.length > 3 && (
              <span className="text-xs text-slate-400">+{activeAgents.length - 3} more agents running...</span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ChatProgress;
