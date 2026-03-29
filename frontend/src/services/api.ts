import axios from 'axios';
import { API_BASE_URL, ENDPOINTS, API_TIMEOUT } from '../config/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text();
        const json = JSON.parse(text);
        return Promise.reject(new Error(json.detail || 'An error occurred'));
      } catch {
        return Promise.reject(new Error('An error occurred'));
      }
    }
    const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
    return Promise.reject(new Error(errorMessage));
  }
);

export const searchDrug = async (drugName: string, options: any = {}) => {
  const { context = {}, sessionId = null, forceRefresh = false } = options;
  const response = await api.post(ENDPOINTS.SEARCH, {
    drug_name: drugName, context, session_id: sessionId, force_refresh: forceRefresh,
  });
  return response.data;
};

export const getCacheStats = async () => {
  const response = await api.get(ENDPOINTS.CACHE_STATS);
  return response.data;
};

export const clearCache = async () => {
  const response = await api.delete(ENDPOINTS.CLEAR_CACHE);
  return response.data;
};

export const clearAllData = async () => {
  const response = await api.delete(ENDPOINTS.CLEAR_ALL_DATA);
  return response.data;
};

export const compareDrugs = async (drugNames: string[]) => {
  const response = await api.post(ENDPOINTS.COMPARE, { drug_names: drugNames });
  return response.data;
};

export const sendChatMessage = async (
  message: string,
  conversationId?: string,
  history?: any[],
  sessionId?: string | null
) => {
  const body: Record<string, unknown> = {
    message,
    conversation_id: conversationId,
    conversation_history: history ?? [],
  };
  if (sessionId) body.session_id = sessionId;
  const response = await api.post(ENDPOINTS.CHAT_MESSAGE, body);
  return response.data;
};

export const getChatHealth = async () => {
  const response = await api.get(ENDPOINTS.CHAT_HEALTH);
  return response.data;
};

export const exportPDF = async (searchResults: any) => {
  const response = await api.post(ENDPOINTS.EXPORT_PDF, searchResults, { responseType: 'blob' });
  return response.data;
};

export const exportExcel = async (searchResults: any) => {
  const response = await api.post(ENDPOINTS.EXPORT_EXCEL, searchResults, { responseType: 'blob' });
  return response.data;
};

export const exportJSON = async (searchResults: any) => {
  const response = await api.post(ENDPOINTS.EXPORT_JSON, searchResults);
  return response.data;
};

export const checkHealth = async () => {
  const response = await api.get(ENDPOINTS.HEALTH);
  return response.data;
};

export const getIntegrations = async () => {
  const response = await api.get(ENDPOINTS.INTEGRATIONS);
  return response.data;
};

export const enableIntegration = async (id: string) => {
  const response = await api.post(ENDPOINTS.INTEGRATION_ENABLE(id));
  return response.data;
};

export const disableIntegration = async (id: string) => {
  const response = await api.post(ENDPOINTS.INTEGRATION_DISABLE(id));
  return response.data;
};

export const configureIntegration = async (id: string, config: any) => {
  const response = await api.put(ENDPOINTS.INTEGRATION_CONFIGURE(id), config);
  return response.data;
};

export const testIntegration = async (id: string) => {
  const response = await api.post(ENDPOINTS.INTEGRATION_TEST(id));
  return response.data;
};

export const getArchivedReports = async (limit = 50) => {
  const response = await api.get(`${ENDPOINTS.REPORTS_LIST}?limit=${limit}`);
  return response.data;
};

export const downloadArchivedReport = async (reportId: string) => {
  const response = await api.get(ENDPOINTS.REPORT_DOWNLOAD(reportId), { responseType: 'blob' });
  return response.data;
};

export const deleteArchivedReport = async (reportId: string) => {
  const response = await api.delete(ENDPOINTS.REPORT_DELETE(reportId));
  return response.data;
};

export const getConversations = async (limit = 50) => {
  const response = await api.get(`${ENDPOINTS.CONVERSATIONS_LIST}?limit=${limit}`);
  return response.data;
};

export const getConversation = async (conversationId: string) => {
  const response = await api.get(ENDPOINTS.CONVERSATION_GET(conversationId));
  return response.data;
};

export const deleteConversation = async (conversationId: string) => {
  const response = await api.delete(ENDPOINTS.CONVERSATION_DELETE(conversationId));
  return response.data;
};

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post(ENDPOINTS.FILES_UPLOAD, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getFiles = async () => {
  const response = await api.get(ENDPOINTS.FILES_LIST);
  return response.data;
};

// Legacy PharmAI endpoints
export const runAgent = async (query: string, complexity?: string) => {
  const response = await api.post(ENDPOINTS.RUN_AGENT, { query, complexity });
  return response.data;
};

export default api;
