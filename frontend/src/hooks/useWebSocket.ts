import { useEffect, useState, useCallback, useRef } from 'react';
import { getWebSocketUrl } from '../config/api';

export const useWebSocket = (sessionId: string | null, options: any = {}) => {
  const { onMessage = null, autoConnect = true, reconnect = true, reconnectInterval = 3000 } = options;

  const [connected, setConnected] = useState(false);
  const [agentProgress, setAgentProgress] = useState<Record<string, any>>({});
  const [workflowStatus, setWorkflowStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    if (!sessionId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const url = getWebSocketUrl(sessionId);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setMessages((prev) => [...prev, data]);

          switch (data.type) {
            case 'agent_progress':
              setAgentProgress((prev) => ({
                ...prev,
                [data.agent]: { status: data.status, message: data.message, evidenceCount: data.evidence_count, timestamp: data.timestamp },
              }));
              break;
            case 'workflow_status':
              setWorkflowStatus({ stage: data.stage, status: data.status, message: data.message, timestamp: data.timestamp });
              break;
            case 'error':
              setError(data.error);
              break;
            case 'complete':
              setWorkflowStatus({ stage: 'complete', status: 'success', message: 'Search completed', timestamp: data.timestamp });
              break;
          }

          if (onMessage) onMessage(data);
        } catch (err) {
          console.error('[WebSocket] Parse error:', err);
        }
      };

      ws.onerror = () => setError('WebSocket connection error');

      ws.onclose = () => {
        setConnected(false);
        if (reconnect && reconnectAttemptsRef.current < 5) {
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };
    } catch (err: any) {
      setError(err.message);
    }
  }, [sessionId, reconnect, reconnectInterval, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
    setConnected(false);
  }, []);

  const resetProgress = useCallback(() => {
    setAgentProgress({});
    setWorkflowStatus(null);
    setError(null);
  }, []);

  useEffect(() => {
    if (autoConnect && sessionId) connect();
    return () => disconnect();
  }, [sessionId, autoConnect]);

  return { connected, error, agentProgress, workflowStatus, messages, connect, disconnect, resetProgress };
};

export default useWebSocket;
