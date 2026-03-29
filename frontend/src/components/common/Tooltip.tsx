import React, { useState } from 'react';

interface TooltipProps {
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  children: React.ReactNode;
}

const Tooltip: React.FC<TooltipProps> = ({ content, position = 'top', children }) => {
  const [visible, setVisible] = useState(false);

  const positions: Record<string, string> = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div className="relative inline-flex" onMouseEnter={() => setVisible(true)} onMouseLeave={() => setVisible(false)}>
      {children}
      {visible && (
        <div className={`absolute ${positions[position]} px-2 py-1 text-xs font-medium text-slate-800 bg-white border border-slate-200 rounded-lg shadow-lg shadow-slate-200/50 whitespace-nowrap z-50 pointer-events-none`}>
          {content}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
