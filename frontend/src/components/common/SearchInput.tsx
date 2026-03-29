import React from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '../../utils/helpers';

interface SearchInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit?: (value: string) => void;
  placeholder?: string;
  size?: string;
  className?: string;
}

const SearchInput: React.FC<SearchInputProps> = ({ value, onChange, onSubmit, placeholder = 'Search...', size = 'md', className }) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && onSubmit) onSubmit(value);
  };

  return (
    <div className={cn('relative w-full', className)}>
      <Search className={cn('absolute left-3 top-1/2 -translate-y-1/2 text-slate-400', size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4')} />
      <input
        type="text"
        value={value}
        onChange={onChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className={cn(
          'w-full bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/15 transition-all shadow-sm',
          size === 'sm' ? 'pl-8 pr-3 py-1.5 text-xs' : 'pl-10 pr-10 py-2.5 text-sm'
        )}
      />
      {value && (
        <button
          onClick={() => onChange({ target: { value: '' } } as any)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};

export default SearchInput;
