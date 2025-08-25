"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Activity, 
  WifiOff, 
  Wifi, 
  TrendingUp, 
  AlertCircle,
  Bell,
  DollarSign
} from 'lucide-react';
import { useWebSocket, WebSocketState, usePriceWebSocket, useSignalWebSocket } from '@/hooks/useWebSocket';

export function WebSocketDemo() {
  const [selectedRooms, setSelectedRooms] = useState<string[]>(['prices', 'signals']);
  
  // Main WebSocket connection
  const {
    state,
    isConnected,
    lastMessage,
    messageHistory,
    subscribe,
    unsubscribe,
    sendMessage,
  } = useWebSocket({
    rooms: selectedRooms,
    onMessage: (msg) => {
      console.log('Received message:', msg);
    },
  });

  // Price feed for specific symbols
  const { prices, isConnected: pricesConnected } = usePriceWebSocket(['AAPL', 'GOOGL', 'MSFT']);
  
  // Signal feed with confidence threshold
  const { signals, isConnected: signalsConnected, updateConfidence } = useSignalWebSocket(0.8);

  const handleRoomToggle = (room: string) => {
    if (selectedRooms.includes(room)) {
      unsubscribe(room);
      setSelectedRooms(prev => prev.filter(r => r !== room));
    } else {
      subscribe(room);
      setSelectedRooms(prev => [...prev, room]);
    }
  };

  const getConnectionIcon = () => {
    switch (state) {
      case WebSocketState.CONNECTED:
        return <Wifi className="h-5 w-5 text-green-500" />;
      case WebSocketState.CONNECTING:
        return <Activity className="h-5 w-5 text-yellow-500 animate-pulse" />;
      case WebSocketState.ERROR:
      case WebSocketState.DISCONNECTED:
        return <WifiOff className="h-5 w-5 text-red-500" />;
      default:
        return <WifiOff className="h-5 w-5 text-gray-500" />;
    }
  };

  const getConnectionBadge = () => {
    switch (state) {
      case WebSocketState.CONNECTED:
        return <Badge variant="default" className="bg-green-500">Connected</Badge>;
      case WebSocketState.CONNECTING:
        return <Badge variant="secondary">Connecting...</Badge>;
      case WebSocketState.ERROR:
        return <Badge variant="destructive">Error</Badge>;
      case WebSocketState.DISCONNECTED:
        return <Badge variant="outline">Disconnected</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              {getConnectionIcon()}
              WebSocket Connection
            </span>
            {getConnectionBadge()}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Room Subscriptions */}
            <div>
              <h3 className="text-sm font-medium mb-2">Subscribed Rooms</h3>
              <div className="flex flex-wrap gap-2">
                {['prices', 'signals', 'news', 'portfolio', 'system'].map(room => (
                  <Button
                    key={room}
                    variant={selectedRooms.includes(room) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleRoomToggle(room)}
                    disabled={!isConnected}
                  >
                    {room}
                  </Button>
                ))}
              </div>
            </div>

            {/* Last Message */}
            {lastMessage && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Last Message:</strong> {lastMessage.type} - {lastMessage.action}
                  <br />
                  <span className="text-xs text-muted-foreground">
                    {new Date(lastMessage.timestamp).toLocaleTimeString()}
                  </span>
                </AlertDescription>
              </Alert>
            )}

            {/* Test Actions */}
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => sendMessage({ type: 'ping' })}
                disabled={!isConnected}
              >
                Send Ping
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => updateConfidence(0.9)}
                disabled={!signalsConnected}
              >
                Update Signal Confidence
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Price Feed */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Live Price Feed
            {pricesConnected && (
              <Badge variant="outline" className="ml-auto">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                Live
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {Object.keys(prices).length > 0 ? (
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(prices).map(([symbol, data]: [string, any]) => (
                <div key={symbol} className="p-3 border rounded-lg">
                  <div className="font-bold">{symbol}</div>
                  <div className="text-2xl">${data.price?.toFixed(2)}</div>
                  <div className={`text-sm ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {data.change >= 0 ? '+' : ''}{data.change_percent?.toFixed(2)}%
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">Waiting for price updates...</p>
          )}
        </CardContent>
      </Card>

      {/* Signal Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Signal Alerts
            {signalsConnected && (
              <Badge variant="outline" className="ml-auto">
                High Confidence (≥0.8)
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {signals.length > 0 ? (
            <div className="space-y-2">
              {signals.slice(-5).reverse().map((signal, idx) => (
                <Alert key={idx}>
                  <TrendingUp className="h-4 w-4" />
                  <AlertDescription>
                    <strong>{signal.data.signal_type || 'Signal'}</strong>
                    <br />
                    {JSON.stringify(signal.data)}
                    <br />
                    <span className="text-xs text-muted-foreground">
                      {new Date(signal.timestamp).toLocaleTimeString()}
                    </span>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No signals received yet...</p>
          )}
        </CardContent>
      </Card>

      {/* Message History */}
      <Card>
        <CardHeader>
          <CardTitle>Message History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-64 overflow-y-auto space-y-1">
            {messageHistory.slice(-10).reverse().map((msg, idx) => (
              <div key={idx} className="text-xs font-mono p-2 bg-muted rounded">
                <span className="text-muted-foreground">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
                {' '}
                <span className="font-semibold">{msg.type}</span>
                {' - '}
                <span>{msg.action}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}