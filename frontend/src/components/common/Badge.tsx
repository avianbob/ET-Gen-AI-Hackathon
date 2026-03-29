import React from 'react';
import { cn } from '../../utils/helpers';

const variants: Record<string, string> = {
  yellow: 'bg-amber-50 text-amber-800 border-amber-200',
  teal: 'bg-teal-50 text-teal-800 border-teal-200',
  blue: 'bg-sky-50 text-sky-800 border-sky-200',
  red: 'bg-red-50 text-red-800 border-red-200',
  purple: 'bg-violet-50 text-violet-800 border-violet-200',
  gray: 'bg-slate-100 text-slate-700 border-slate-200',
};

interface BadgeProps {
  variant?: string;
  size?: string;
  children: React.ReactNode;
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({ variant = 'gray', size = 'sm', children, className }) => {
  return (
    <span className={cn(
      'inline-flex items-center font-medium border rounded-full',
      size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
      variants[variant] || variants.gray,
      className
    )}>
      {children}
    </span>
  );
};

export default Badge;
