import React from 'react';
import { useLocation, useParams, Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { formatDrugName } from '../../utils/formatters';

const routeLabels: Record<string, string> = {
  chat: 'AI Assistant', dashboard: 'Dashboard', search: 'Drug Search',
  results: 'Results', history: 'History', saved: 'Saved Opportunities',
  integrations: 'Integrations', settings: 'Settings', compare: 'Comparison',
  architecture: 'Architecture', dash: 'Analysis',
};

const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  const params = useParams();
  const segments = location.pathname.split('/').filter(Boolean);
  if (segments.length === 0) return null;

  const crumbs = segments.map((seg, i) => {
    const path = '/' + segments.slice(0, i + 1).join('/');
    const isParam = (params as any).drugName && seg === (params as any).drugName;
    const label = isParam ? formatDrugName(decodeURIComponent(seg)) : (routeLabels[seg] || seg);
    return { label, path, isLast: i === segments.length - 1 };
  });

  return (
    <nav className="flex items-center gap-1.5 text-xs">
      <Link to="/dashboard" className="text-slate-400 hover:text-cyan-600 transition-colors flex items-center gap-1"><Home className="w-3 h-3" /></Link>
      {crumbs.map((crumb, i) => (
        <React.Fragment key={i}>
          <ChevronRight className="w-3 h-3 text-slate-300" />
          {crumb.isLast ? (
            <span className="text-slate-600 font-medium">{crumb.label}</span>
          ) : (
            <Link to={crumb.path} className="text-slate-400 hover:text-cyan-600 transition-colors">{crumb.label}</Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

export default Breadcrumbs;
