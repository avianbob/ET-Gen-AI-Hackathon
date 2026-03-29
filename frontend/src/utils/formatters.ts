import { CONFIDENCE_LEVELS } from './constants';

export const formatScore = (score: number | null | undefined, decimals = 1) => {
  if (score === null || score === undefined) return '—';
  return Number(score).toFixed(decimals);
};

export const formatNumber = (num: number | null | undefined) => {
  if (num === null || num === undefined) return '—';
  return new Intl.NumberFormat('en-US').format(num);
};

export const formatCurrency = (amount: number | null | undefined, decimals = 1) => {
  if (amount === null || amount === undefined) return '—';
  const abs = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  if (abs >= 1e12) return `${sign}$${(abs / 1e12).toFixed(decimals)}T`;
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(decimals)}B`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(decimals)}M`;
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(decimals)}K`;
  return `${sign}$${abs.toFixed(decimals)}`;
};

export const formatPercentage = (value: number | null | undefined, decimals = 1, isDecimal = false) => {
  if (value === null || value === undefined) return '—';
  const pct = isDecimal ? value * 100 : value;
  return `${pct.toFixed(decimals)}%`;
};

export const formatTimeAgo = (date: string | Date | null) => {
  if (!date) return '—';
  const now = new Date();
  const past = new Date(date);
  const diffS = Math.floor((now.getTime() - past.getTime()) / 1000);
  if (diffS < 60) return 'just now';
  const diffM = Math.floor(diffS / 60);
  if (diffM < 60) return `${diffM}m ago`;
  const diffH = Math.floor(diffM / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 7) return `${diffD}d ago`;
  const diffW = Math.floor(diffD / 7);
  if (diffW < 4) return `${diffW}w ago`;
  const diffMo = Math.floor(diffD / 30);
  if (diffMo < 12) return `${diffMo}mo ago`;
  return `${Math.floor(diffD / 365)}y ago`;
};

export const formatDate = (date: string | Date | null, options: Intl.DateTimeFormatOptions = {}) => {
  if (!date) return '—';
  return new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', ...options });
};

export const formatDuration = (seconds: number | null | undefined) => {
  if (seconds === null || seconds === undefined) return '—';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m < 60) return `${m}m ${s.toFixed(0)}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
};

export const getConfidenceLevel = (score: number | null | undefined) => {
  if (score === null || score === undefined) return CONFIDENCE_LEVELS.veryLow;
  if (score >= CONFIDENCE_LEVELS.veryHigh.min) return CONFIDENCE_LEVELS.veryHigh;
  if (score >= CONFIDENCE_LEVELS.high.min) return CONFIDENCE_LEVELS.high;
  if (score >= CONFIDENCE_LEVELS.moderate.min) return CONFIDENCE_LEVELS.moderate;
  if (score >= CONFIDENCE_LEVELS.low.min) return CONFIDENCE_LEVELS.low;
  return CONFIDENCE_LEVELS.veryLow;
};

export const getConfidenceColor = (score: number | null | undefined) => getConfidenceLevel(score).color;
export const getConfidenceLabel = (score: number | null | undefined) => getConfidenceLevel(score).label;

export const truncateText = (text: string, maxLength = 100) => {
  if (!text) return '';
  return text.length <= maxLength ? text : `${text.substring(0, maxLength).trim()}...`;
};

export const formatDrugName = (name: string) => {
  if (!name) return '';
  return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
};

export const formatCompactNumber = (num: number | null | undefined) => {
  if (num === null || num === undefined) return '—';
  const abs = Math.abs(num);
  const sign = num < 0 ? '-' : '';
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(1)}K`;
  return `${sign}${abs}`;
};
