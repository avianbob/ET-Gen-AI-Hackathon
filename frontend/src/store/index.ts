import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AppState {
  user: any;
  setUser: (user: any) => void;
  clearUser: () => void;

  searchResults: any;
  isSearching: boolean;
  searchError: string | null;
  sessionId: string | null;
  drugName: string;
  setSearchResults: (results: any) => void;
  setIsSearching: (s: boolean) => void;
  setSearchError: (e: string | null) => void;
  setSessionId: (s: string | null) => void;
  setDrugName: (n: string) => void;

  searchHistory: any[];
  addToHistory: (s: any) => void;
  clearHistory: () => void;
  deleteFromHistory: (drugName: string, timestamp: string) => void;

  savedOpportunities: any[];
  saveOpportunity: (o: any) => void;
  removeOpportunity: (id: string) => void;
  clearSavedOpportunities: () => void;
  updateOpportunityStatus: (id: string, status: string) => void;
  updateOpportunityNotes: (id: string, notes: string) => void;

  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  theme: string;
  toggleTheme: () => void;
  activeTab: string;
  setActiveTab: (t: string) => void;
  selectedIndication: any;
  setSelectedIndication: (i: any) => void;

  chatMessages: any[];
  isChatOpen: boolean;
  addChatMessage: (m: any) => void;
  clearChatMessages: () => void;
  setIsChatOpen: (o: boolean) => void;

  cacheStats: any;
  setCacheStats: (s: any) => void;

  integrations: any[];
  integrationsLoading: boolean;
  integrationsError: string | null;
  setIntegrations: (i: any[]) => void;
  setIntegrationsLoading: (l: boolean) => void;
  setIntegrationsError: (e: string | null) => void;
  updateIntegrationStatus: (id: string, enabled: boolean) => void;

  notifications: any[];
  addNotification: (n: any) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  resetSearch: () => void;
  reset: () => void;
  clearAllData: () => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        setUser: (user) => set({ user }),
        clearUser: () => set({ user: null }),

        searchResults: null,
        isSearching: false,
        searchError: null,
        sessionId: null,
        drugName: '',
        setSearchResults: (results) => set({ searchResults: results, searchError: null }),
        setIsSearching: (isSearching) => set({ isSearching }),
        setSearchError: (error) => set({ searchError: error, isSearching: false }),
        setSessionId: (sessionId) => set({ sessionId }),
        setDrugName: (drugName) => set({ drugName }),

        searchHistory: [],
        addToHistory: (search) =>
          set((state) => {
            const exists = state.searchHistory.some(
              (s: any) => s.drugName.toLowerCase() === search.drugName.toLowerCase() &&
                Date.now() - new Date(s.timestamp).getTime() < 3600000
            );
            if (exists) return state;
            return { searchHistory: [search, ...state.searchHistory.slice(0, 49)] };
          }),
        clearHistory: () => set({ searchHistory: [] }),
        deleteFromHistory: (drugName, timestamp) =>
          set((state) => ({
            searchHistory: state.searchHistory.filter(
              (s: any) => !(s.drugName === drugName && s.timestamp === timestamp)
            ),
          })),

        savedOpportunities: [],
        saveOpportunity: (opportunity) =>
          set((state) => ({ savedOpportunities: [opportunity, ...state.savedOpportunities] })),
        removeOpportunity: (id) =>
          set((state) => ({ savedOpportunities: state.savedOpportunities.filter((o: any) => o.id !== id) })),
        clearSavedOpportunities: () => set({ savedOpportunities: [] }),
        updateOpportunityStatus: (id, status) =>
          set((state) => ({
            savedOpportunities: state.savedOpportunities.map((o: any) => o.id === id ? { ...o, status } : o),
          })),
        updateOpportunityNotes: (id, notes) =>
          set((state) => ({
            savedOpportunities: state.savedOpportunities.map((o: any) => o.id === id ? { ...o, notes } : o),
          })),

        sidebarCollapsed: false,
        toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
        theme: 'light',
        toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
        activeTab: 'opportunities',
        setActiveTab: (tab) => set({ activeTab: tab }),
        selectedIndication: null,
        setSelectedIndication: (indication) => set({ selectedIndication: indication }),

        chatMessages: [],
        isChatOpen: false,
        addChatMessage: (message) => set((state) => ({ chatMessages: [...state.chatMessages, message] })),
        clearChatMessages: () => set({ chatMessages: [] }),
        setIsChatOpen: (isOpen) => set({ isChatOpen: isOpen }),

        cacheStats: null,
        setCacheStats: (stats) => set({ cacheStats: stats }),

        integrations: [],
        integrationsLoading: false,
        integrationsError: null,
        setIntegrations: (integrations) => set({ integrations, integrationsLoading: false, integrationsError: null }),
        setIntegrationsLoading: (loading) => set({ integrationsLoading: loading }),
        setIntegrationsError: (error) => set({ integrationsError: error, integrationsLoading: false }),
        updateIntegrationStatus: (integrationId, enabled) =>
          set((state) => ({
            integrations: state.integrations.map((i: any) =>
              i.id === integrationId ? { ...i, enabled, status: enabled ? 'active' : 'inactive' } : i
            ),
          })),

        notifications: [],
        addNotification: (n) => set((state) => ({ notifications: [n, ...state.notifications.slice(0, 19)] })),
        removeNotification: (id) => set((state) => ({ notifications: state.notifications.filter((n: any) => n.id !== id) })),
        clearNotifications: () => set({ notifications: [] }),

        resetSearch: () =>
          set({
            searchResults: null, isSearching: false, searchError: null,
            sessionId: null, drugName: '', chatMessages: [], isChatOpen: false,
            activeTab: 'opportunities', selectedIndication: null,
          }),
        reset: () =>
          set({
            searchResults: null, isSearching: false, searchError: null,
            sessionId: null, drugName: '', chatMessages: [], isChatOpen: false,
            activeTab: 'opportunities', selectedIndication: null,
            cacheStats: null, integrations: [], integrationsLoading: false, integrationsError: null,
          }),
        clearAllData: () =>
          set({
            searchHistory: [], savedOpportunities: [], searchResults: null,
            isSearching: false, searchError: null, sessionId: null, drugName: '',
            chatMessages: [], isChatOpen: false, activeTab: 'opportunities',
            selectedIndication: null, cacheStats: null, notifications: [],
          }),
      }),
      {
        name: 'pharmai-storage',
        partialize: (state) => ({
          user: state.user,
          searchHistory: state.searchHistory,
          savedOpportunities: state.savedOpportunities,
          sidebarCollapsed: state.sidebarCollapsed,
          theme: state.theme,
        }),
      }
    ),
    { name: 'pharmai-store' }
  )
);

export default useAppStore;
