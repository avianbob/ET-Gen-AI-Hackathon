export const cn = (...classes: (string | boolean | undefined | null)[]) => {
  return classes.flat().filter((cls) => typeof cls === 'string' && cls.trim()).join(' ');
};

export const debounce = <T extends (...args: any[]) => any>(fn: T, delay = 300) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

export const generateSessionId = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

export const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const safeJsonParse = (str: string, fallback: any = null) => {
  try { return JSON.parse(str); } catch { return fallback; }
};

export const sortBy = (arr: any[], key: string, order: 'asc' | 'desc' = 'desc') => {
  return [...arr].sort((a, b) => {
    const aVal = a[key] ?? 0;
    const bVal = b[key] ?? 0;
    return order === 'asc' ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
  });
};

export const groupBy = <T>(arr: T[], key: string | ((item: T) => string)): Record<string, T[]> => {
  return arr.reduce((acc: Record<string, T[]>, item: any) => {
    const groupKey = typeof key === 'function' ? key(item) : item[key];
    if (!acc[groupKey]) acc[groupKey] = [];
    acc[groupKey].push(item);
    return acc;
  }, {});
};

export const unique = <T>(arr: T[], key?: string): T[] => {
  if (key) {
    const seen = new Set();
    return arr.filter((item: any) => {
      const val = item[key];
      if (seen.has(val)) return false;
      seen.add(val);
      return true;
    });
  }
  return [...new Set(arr)];
};

export const isEmpty = (value: any) => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

export const clamp = (num: number, min: number, max: number) => Math.min(Math.max(num, min), max);

export const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
};

export const downloadFile = (data: Blob | string, filename: string, mimeType = 'application/octet-stream') => {
  const blob = data instanceof Blob ? data : new Blob([data], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  setTimeout(() => {
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, 1000);
};
