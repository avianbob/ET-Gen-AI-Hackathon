import React from 'react';
import { motion } from 'framer-motion';
import { Shield, CheckCircle, Clock, Circle } from 'lucide-react';
import { cn } from '../../utils/helpers';

interface RegulatoryPathwayProps {
  indication: string;
  data?: any;
}

interface Step {
  id: string;
  label: string;
  duration: string;
  status: 'completed' | 'active' | 'pending';
  description: string;
}

const DEFAULT_STEPS: Step[] = [
  { id: 'ind', label: 'IND Filing', duration: '6–12 mo', status: 'pending', description: 'Investigational New Drug application to FDA' },
  { id: 'phase1', label: 'Phase I', duration: '1–2 yr', status: 'pending', description: 'Safety & dosage in small group' },
  { id: 'phase2', label: 'Phase II', duration: '1–3 yr', status: 'pending', description: 'Efficacy & side effects' },
  { id: 'phase3', label: 'Phase III', duration: '2–4 yr', status: 'pending', description: 'Large-scale efficacy confirmation' },
  { id: 'nda', label: 'NDA/BLA', duration: '6–12 mo', status: 'pending', description: 'New Drug Application review' },
  { id: 'approval', label: 'Approval', duration: '—', status: 'pending', description: 'FDA market authorization' },
];

const STATUS_CONFIG = {
  completed: {
    icon: CheckCircle,
    dotColor: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    lineColor: 'bg-emerald-500',
    ringColor: 'ring-emerald-500/30',
  },
  active: {
    icon: Clock,
    dotColor: 'bg-yellow-500',
    textColor: 'text-cyan-700',
    lineColor: 'bg-yellow-500',
    ringColor: 'ring-cyan-500/25',
  },
  pending: {
    icon: Circle,
    dotColor: 'bg-gray-600',
    textColor: 'text-slate-500',
    lineColor: 'bg-slate-200',
    ringColor: 'ring-gray-600/30',
  },
};

const RegulatoryPathway: React.FC<RegulatoryPathwayProps> = ({ indication, data }) => {
  const steps: Step[] = data?.steps
    ? data.steps.map((s: any, i: number) => ({
        id: s.id || `step-${i}`,
        label: s.label || s.name || `Step ${i + 1}`,
        duration: s.duration || s.estimated_duration || '—',
        status: s.status || 'pending',
        description: s.description || '',
      }))
    : DEFAULT_STEPS;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Shield className="w-5 h-5 text-cyan-700" />
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Regulatory Pathway</h2>
          <p className="text-sm text-slate-600">{indication}</p>
        </div>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 backdrop-blur-sm overflow-x-auto">
        <div className="flex items-start min-w-[640px]">
          {steps.map((step, idx) => {
            const config = STATUS_CONFIG[step.status];
            const Icon = config.icon;
            const isLast = idx === steps.length - 1;

            return (
              <div key={step.id} className="flex-1 flex flex-col items-center relative">
                <motion.div
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: idx * 0.1, type: 'spring', stiffness: 300 }}
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center ring-4 z-10',
                    config.dotColor,
                    config.ringColor
                  )}
                >
                  <Icon className="w-4.5 h-4.5 text-white" />
                </motion.div>

                {!isLast && (
                  <div className="absolute top-5 left-[calc(50%+20px)] right-[calc(-50%+20px)] h-0.5">
                    <div className={cn('h-full rounded-full', config.lineColor)} />
                  </div>
                )}

                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 + 0.15 }}
                  className="mt-3 text-center max-w-[120px]"
                >
                  <span className={cn('text-xs font-semibold block', config.textColor)}>
                    {step.label}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-0.5">{step.duration}</span>
                  <p className="text-[10px] text-slate-500 mt-1 leading-tight">{step.description}</p>
                </motion.div>
              </div>
            );
          })}
        </div>
      </div>

      {data?.estimated_total_time && (
        <div className="flex items-center justify-end gap-2">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-xs text-slate-600">
            Estimated total: <span className="text-slate-900 font-semibold">{data.estimated_total_time}</span>
          </span>
        </div>
      )}
    </div>
  );
};

export default RegulatoryPathway;
