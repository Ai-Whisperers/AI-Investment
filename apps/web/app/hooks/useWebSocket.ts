/**
 * WebSocket hook for real-time updates.
 * Implements reconnection, authentication, and room subscriptions.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface WSMessage {
  type: string;
  action: string;
  data: any;
  timestamp: string;
}

export interface UseWebSocketOptions {
  url?: string;
  token?: string | null;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectInterval?: number;
  reconnectAttempts?: number;
  rooms?: string[];
  onMessage?: (message: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export enum WebSocketState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTING = 'DISCONNECTING',
  DISCONNECTED = 'DISCONNECTED',
  ERROR = 'ERROR',
}

export function useWebSocket({
  url,
  token = null,
  autoConnect = true,
  reconnect = true,
  reconnectInterval = 5000,
  reconnectAttempts = 5,
  rooms = [],
  onMessage,
  onConnect,
  onDisconnect,
  onError,
}: UseWebSocketOptions) {
  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [messageHistory, setMessageHistory] = useState<WSMessage[]>([]);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingInterval = useRef<NodeJS.Timeout | null>(null);
  const subscribedRooms = useRef<Set<string>>(new Set());

  // Get WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    if (url) return url;
    
    // Auto-detect based on current environment
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NEXT_PUBLIC_WS_URL || 
                 process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:/, '') ||
                 window.location.host;
    
    let wsUrl = `${protocol}//${host}/ws`;
    
    // Add token as query parameter if provided
    if (token) {
      wsUrl += `?token=${encodeURIComponent(token)}`;
    }
    
    return wsUrl;
  }, [url, token]);

  // Send message through WebSocket
  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      const msgString = typeof message === 'string' ? message : JSON.stringify(message);
      ws.current.send(msgString);
      return true;
    }
    return false;
  }, []);

  // Subscribe to a room
  const subscribe = useCallback((room: string) => {
    if (subscribedRooms.current.has(room)) {
      return; // Already subscribed
    }
    
    const success = sendMessage({
      type: 'subscribe',
      room: room,
    });
    
    if (success) {
      subscribedRooms.current.add(room);
    }
    
    return success;
  }, [sendMessage]);

  // Unsubscribe from a room
  const unsubscribe = useCallback((room: string) => {
    if (!subscribedRooms.current.has(room)) {
      return; // Not subscribed
    }
    
    const success = sendMessage({
      type: 'unsubscribe',
      room: room,
    });
    
    if (success) {
      subscribedRooms.current.delete(room);
    }
    
    return success;
  }, [sendMessage]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setState(WebSocketState.CONNECTING);
    
    try {
      const wsUrl = getWebSocketUrl();
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setState(WebSocketState.CONNECTED);
        reconnectCount.current = 0;
        
        // Subscribe to initial rooms
        rooms.forEach(room => subscribe(room));
        
        // Start ping interval to keep connection alive
        pingInterval.current = setInterval(() => {
          sendMessage({ type: 'ping', timestamp: new Date().toISOString() });
        }, 30000); // Ping every 30 seconds
        
        onConnect?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          
          // Update state
          setLastMessage(message);
          setMessageHistory(prev => [...prev.slice(-99), message]); // Keep last 100 messages
          
          // Handle pong messages internally
          if (message.type === 'pong') {
            return; // Don't pass pong messages to handler
          }
          
          // Handle subscription confirmations
          if (message.type === 'system' && message.action === 'subscribed') {
            console.log(`Subscribed to room: ${message.data.room}`);
          }
          
          // Call message handler
          onMessage?.(message);
          
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(WebSocketState.ERROR);
        onError?.(error);
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setState(WebSocketState.DISCONNECTED);
        
        // Clear ping interval
        if (pingInterval.current) {
          clearInterval(pingInterval.current);
          pingInterval.current = null;
        }
        
        // Clear subscribed rooms
        subscribedRooms.current.clear();
        
        onDisconnect?.();
        
        // Attempt reconnection if enabled
        if (reconnect && reconnectCount.current < reconnectAttempts) {
          reconnectCount.current++;
          console.log(`Reconnecting in ${reconnectInterval}ms... (Attempt ${reconnectCount.current}/${reconnectAttempts})`);
          
          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setState(WebSocketState.ERROR);
    }
  }, [
    getWebSocketUrl,
    rooms,
    reconnect,
    reconnectInterval,
    reconnectAttempts,
    onConnect,
    onDisconnect,
    onError,
    onMessage,
    sendMessage,
    subscribe,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    setState(WebSocketState.DISCONNECTING);
    
    // Clear reconnect timeout
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
    
    // Clear ping interval
    if (pingInterval.current) {
      clearInterval(pingInterval.current);
      pingInterval.current = null;
    }
    
    // Close WebSocket connection
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    
    subscribedRooms.current.clear();
    setState(WebSocketState.DISCONNECTED);
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect]); // Only run once on mount
  
  // Reconnect if token changes
  useEffect(() => {
    if (token && state === WebSocketState.CONNECTED) {
      // Reconnect with new token
      disconnect();
      setTimeout(() => connect(), 100);
    }
  }, [token]);

  return {
    // State
    state,
    isConnected: state === WebSocketState.CONNECTED,
    isConnecting: state === WebSocketState.CONNECTING,
    isDisconnected: state === WebSocketState.DISCONNECTED,
    
    // Messages
    lastMessage,
    messageHistory,
    
    // Actions
    connect,
    disconnect,
    sendMessage,
    subscribe,
    unsubscribe,
    
    // Utilities
    clearHistory: () => setMessageHistory([]),
  };
}

// Specialized hooks for specific WebSocket endpoints

export function usePriceWebSocket(symbols: string[]) {
  const [prices, setPrices] = useState<Record<string, any>>({});
  
  const { isConnected, lastMessage } = useWebSocket({
    url: `/ws/prices?symbols=${symbols.join(',')}`,
    onMessage: (message) => {
      if (message.type === 'prices' && message.action === 'update') {
        setPrices(prev => ({
          ...prev,
          [message.data.symbol]: message.data,
        }));
      }
    },
  });
  
  return { isConnected, prices, lastUpdate: lastMessage?.timestamp };
}

export function useSignalWebSocket(minConfidence = 0.7) {
  const [signals, setSignals] = useState<WSMessage[]>([]);
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  
  const { isConnected, sendMessage } = useWebSocket({
    url: `/ws/signals?min_confidence=${minConfidence}`,
    token,
    onMessage: (message) => {
      if (message.type === 'signals' && message.action === 'alert') {
        setSignals(prev => [...prev, message]);
      }
    },
  });
  
  const updateConfidence = (newConfidence: number) => {
    sendMessage(`confidence:${newConfidence}`);
  };
  
  return { isConnected, signals, updateConfidence };
}

export function usePortfolioWebSocket() {
  const [portfolioUpdates, setPortfolioUpdates] = useState<any[]>([]);
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  
  const { isConnected } = useWebSocket({
    token,
    rooms: ['portfolio'],
    onMessage: (message) => {
      if (message.type === 'portfolio') {
        setPortfolioUpdates(prev => [...prev, message.data]);
      }
    },
  });
  
  return { isConnected, portfolioUpdates };
}