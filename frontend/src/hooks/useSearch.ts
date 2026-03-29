import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchDrug } from '../services/api';
import { useWebSocket } from './useWebSocket';
import { generateSessionId } from '../utils/helpers';
import { ROUTES } from '../utils/constants';
import useAppStore from '../store';

export const useSearch = (options: any = {}) => {
  const { autoNavigate = true, onComplete = null, onError = null } = options;
  const navigate = useNavigate();
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  const startTimeRef = useRef<number | null>(null);
  const timerRef = useRef<any>(null);

  const { setSearchResults, addToHistory } = useAppStore();

  const { connected, agentProgress, workflowStatus, resetProgress } = useWebSocket(sessionId, { autoConnect: !!sessionId });

  useEffect(() => {
    if (isSearching && startTimeRef.current) {
      timerRef.current = setInterval(() => {
        setElapsedTime((Date.now() - (startTimeRef.current || 0)) / 1000);
      }, 100);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isSearching]);

  const search = useCallback(async (drugName: string, searchOptions: any = {}) => {
    if (!drugName?.trim() || isSearching) return;
    const { forceRefresh = false, context = {} } = searchOptions;
    const newSessionId = generateSessionId();

    setSessionId(newSessionId);
    setIsSearching(true);
    setError(null);
    resetProgress();
    startTimeRef.current = Date.now();
    setElapsedTime(0);

    try {
      const results = await searchDrug(drugName.trim(), { sessionId: newSessionId, forceRefresh, context });
      setSearchResults(results);
      addToHistory({
        drugName: drugName.trim(),
        timestamp: new Date().toISOString(),
        opportunityCount: results.enhanced_indications?.length || results.ranked_indications?.length || 0,
        cached: results.cached || false,
      });
      if (onComplete) onComplete(results);
      if (autoNavigate) navigate(`${ROUTES.RESULTS}/${encodeURIComponent(drugName.trim())}`);
      return results;
    } catch (err: any) {
      const msg = err.message || 'Search failed. Please try again.';
      setError(msg);
      if (onError) onError(err);
      throw err;
    } finally {
      setIsSearching(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }, [isSearching, resetProgress, setSearchResults, addToHistory, onComplete, onError, autoNavigate, navigate]);

  const reset = useCallback(() => {
    setIsSearching(false);
    setError(null);
    setSessionId(null);
    setElapsedTime(0);
    resetProgress();
  }, [resetProgress]);

  return { isSearching, error, sessionId, elapsedTime, connected, agentProgress, workflowStatus, search, reset, cancel: reset };
};

export default useSearch;
