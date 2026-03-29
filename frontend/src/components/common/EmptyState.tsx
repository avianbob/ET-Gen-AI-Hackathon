import React from 'react';
import { cn } from '../../utils/helpers';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action, className }) => {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      {icon && <div className="mb-4 text-slate-400">{icon}</div>}
      <h3 className="text-lg font-semibold text-slate-800 mb-2">{title}</h3>
      {description && <p className="text-sm text-slate-500 max-w-md mb-6">{description}</p>}
      {action}
    </div>
  );
};

export default EmptyState;
