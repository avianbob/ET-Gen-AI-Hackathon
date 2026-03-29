import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { cn } from '../../utils/helpers';

interface Column {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: any) => React.ReactNode;
  className?: string;
}

interface DataTableProps {
  columns: Column[];
  data: any[];
  className?: string;
  emptyMessage?: string;
}

const DataTable: React.FC<DataTableProps> = ({ columns, data, className, emptyMessage = 'No data available' }) => {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const sortedData = sortKey
    ? [...data].sort((a, b) => {
        const aVal = a[sortKey] ?? '';
        const bVal = b[sortKey] ?? '';
        const cmp = typeof aVal === 'string' ? aVal.localeCompare(bVal) : aVal - bVal;
        return sortDir === 'asc' ? cmp : -cmp;
      })
    : data;

  if (data.length === 0) return <p className="text-center text-slate-500 py-8 text-sm">{emptyMessage}</p>;

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200">
            {columns.map((col) => (
              <th
                key={col.key}
                onClick={() => col.sortable && handleSort(col.key)}
                className={cn('px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider', col.sortable && 'cursor-pointer hover:text-cyan-700', col.className)}
              >
                <div className="flex items-center gap-1">
                  {col.label}
                  {col.sortable && sortKey === col.key && (sortDir === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {sortedData.map((row, i) => (
            <tr key={i} className="hover:bg-slate-50 transition-colors">
              {columns.map((col) => (
                <td key={col.key} className={cn('px-4 py-3 text-slate-700', col.className)}>
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;
