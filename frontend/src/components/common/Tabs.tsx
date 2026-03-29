import React from 'react';
import { cn } from '../../utils/helpers';

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  count?: number;
}

interface TabsProps {
  tabs: Tab[];
  active: string;
  onChange: (id: string) => void;
  className?: string;
}

const Tabs: React.FC<TabsProps> = ({ tabs, active, onChange, className }) => {
  return (
    <div
      className={cn(
        'flex gap-1 p-1 bg-slate-100/80 rounded-xl border border-slate-200/80',
        'flex-nowrap overflow-x-auto scrollbar-thin min-w-0',
        className
      )}
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={cn(
            'flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all shrink-0 whitespace-nowrap',
            active === tab.id
              ? 'bg-white text-cyan-800 border border-cyan-200 shadow-sm shadow-cyan-500/10'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/70 border border-transparent'
          )}
        >
          {tab.icon}
          {tab.label}
          {tab.count !== undefined && (
            <span className={cn(
              'px-1.5 py-0.5 text-xs rounded-full',
              active === tab.id ? 'bg-cyan-50 text-cyan-800' : 'bg-slate-200/80 text-slate-600'
            )}>
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
