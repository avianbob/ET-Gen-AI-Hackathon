export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export const ENDPOINTS = {
  SEARCH: '/api/search',
  SEARCH_STATUS: (sessionId: string) => `/api/search/status/${sessionId}`,
  CACHE_STATS: '/api/search/cache/stats',
  CLEAR_CACHE: '/api/search/cache/clear',
  CLEAR_DRUG_CACHE: (drugName: string) => `/api/search/cache/${drugName}`,
  CLEAR_ALL_DATA: '/api/data/clear-all',

  CHAT: '/api/chat',
  CHAT_MESSAGE: '/api/chat/message',
  CHAT_HEALTH: '/api/chat/health',

  FILES_UPLOAD: '/api/files/upload',
  FILES_LIST: '/api/files',
  FILE_SUMMARY: (fileId: string) => `/api/files/${fileId}/summary`,

  EXPORT_PDF: '/api/export/pdf',
  EXPORT_OPPORTUNITY_PDF: '/api/export/opportunity-pdf',
  EXPORT_EXCEL: '/api/export/excel',
  EXPORT_JSON: '/api/export/json',

  COMPARE: '/api/compare',

  REPORTS_LIST: '/api/reports',
  REPORTS_FOR_DRUG: (drugName: string) => `/api/reports/drug/${encodeURIComponent(drugName)}`,
  REPORT_DOWNLOAD: (reportId: string) => `/api/reports/${reportId}/download`,
  REPORT_DELETE: (reportId: string) => `/api/reports/${reportId}`,

  CONVERSATIONS_LIST: '/api/chat/conversations',
  CONVERSATION_GET: (id: string) => `/api/chat/conversations/${id}`,
  CONVERSATION_DELETE: (id: string) => `/api/chat/conversations/${id}`,

  AUTH_REGISTER: '/api/auth/register',
  AUTH_LOGIN: '/api/auth/login',
  AUTH_ME: '/api/auth/me',
  AUTH_STATUS: '/api/auth/status',

  INTEGRATIONS: '/api/integrations',
  INTEGRATIONS_ENABLED: '/api/integrations/enabled',
  INTEGRATION_ENABLE: (id: string) => `/api/integrations/${id}/enable`,
  INTEGRATION_DISABLE: (id: string) => `/api/integrations/${id}/disable`,
  INTEGRATION_CONFIGURE: (id: string) => `/api/integrations/${id}/configure`,
  INTEGRATION_TEST: (id: string) => `/api/integrations/${id}/test`,

  DRUG_INFO: (drugName: string) => `/api/drug-info/${drugName}`,
  MARKET_ANALYZE: '/api/market/analyze',

  HEALTH: '/health',

  // Legacy PharmAI endpoints
  RUN_AGENT: '/api/run-agent',
  GENERATE_PDF: '/api/generate-pdf',
  GENERATE_PPTX: '/api/generate-pptx',
  EXPORT_REPORT: '/api/export-report',
  CLINICAL_TRIALS_TEST: '/api/clinical-trials-test',
  TEST_GEMINI: '/api/test-gemini',
  TEST_GROQ: '/api/test-groq',
  TEST_LLM: '/api/test-llm',
};

export const getWebSocketUrl = (sessionId: string) => `${WS_URL}/${sessionId}`;

export const API_TIMEOUT = 600000;
