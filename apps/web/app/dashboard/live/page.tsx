"use client";

import { WebSocketDemo } from "@/components/WebSocketDemo";

export default function LiveDashboardPage() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Live Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time market data and signal updates via WebSocket
        </p>
      </div>
      
      <WebSocketDemo />
    </div>
  );
}