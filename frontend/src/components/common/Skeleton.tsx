import React from 'react';
import { cn } from '../../utils/helpers';

interface SkeletonProps {
  className?: string;
  count?: number;
}

const Skeleton: React.FC<SkeletonProps> = ({ className, count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={cn('animate-pulse bg-gray-700/50 rounded-lg', className)} />
      ))}
    </>
  );
};

export default Skeleton;
