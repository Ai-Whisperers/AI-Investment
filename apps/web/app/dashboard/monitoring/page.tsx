"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import {
  Activity,
  AlertCircle,
  CheckCircle,
  Database,
  Cpu,
  HardDrive,
  TrendingUp,
  AlertTriangle,
  Info,
} from "lucide-react";

interface SystemMetrics {
  database_connected: boolean;
  cache_connected: boolean;
  api_latency: number;
  memory_usage: number;
  cpu_usage: number;
  error_rate: number;
}

interface SignalMetrics {
  total: number;
  today: number;
  high_confidence: number;
  pending: Array<{
    ticker: string;
    confidence: number;
    expected_return: number;
    signal_type: string;
  }>;
  win_rate: number;
}

interface AlertStats {
  count: number;
  critical: number;
  warning: number;
  info: number;
}

interface DashboardData {
  timestamp: string;
  system: SystemMetrics;
  signals: SignalMetrics;
  alerts: AlertStats;
  history: {
    timestamps: string[];
    api_latency: number[];
    memory_usage: number[];
    cpu_usage: number[];
    signal_rate: number[];
  };
}

export default function MonitoringDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchDashboardData();

    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch("/api/v1/monitoring/dashboard/data");
      if (!response.ok) throw new Error("Failed to fetch dashboard data");
      const data = await response.json();
      setData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!data) return null;

  // Prepare chart data
  const chartData = data.history.timestamps.map((timestamp, index) => ({
    time: new Date(timestamp).toLocaleTimeString(),
    latency: data.history.api_latency[index],
    memory: data.history.memory_usage[index],
    cpu: data.history.cpu_usage[index],
    signals: data.history.signal_rate[index],
  }));

  const getSystemStatus = () => {
    if (!data.system.database_connected) return { status: "critical", color: "red" };
    if (data.system.error_rate > 5) return { status: "warning", color: "yellow" };
    if (data.system.api_latency > 1000) return { status: "degraded", color: "orange" };
    return { status: "healthy", color: "green" };
  };

  const systemStatus = getSystemStatus();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">System Monitoring</h1>
        <div className="flex items-center gap-4">
          <Badge variant={systemStatus.status === "healthy" ? "default" : "destructive"}>
            {systemStatus.status.toUpperCase()}
          </Badge>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="px-4 py-2 text-sm bg-primary text-white rounded hover:bg-primary/90"
          >
            {autoRefresh ? "Disable" : "Enable"} Auto-Refresh
          </button>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              {data.system.database_connected ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-500" />
              )}
              <span className="text-sm">
                {data.system.database_connected ? "Connected" : "Disconnected"}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Latency</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.system.api_latency.toFixed(0)}ms</div>
            <p className="text-xs text-muted-foreground">
              {data.system.api_latency < 100 ? "Excellent" : 
               data.system.api_latency < 500 ? "Good" : 
               data.system.api_latency < 1000 ? "Fair" : "Poor"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.system.memory_usage.toFixed(1)}%</div>
            <Progress value={data.system.memory_usage} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.system.cpu_usage.toFixed(1)}%</div>
            <Progress value={data.system.cpu_usage} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Signal Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Signal Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Total Signals</span>
                <span className="text-sm font-bold">{data.signals.total}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Signals Today</span>
                <span className="text-sm font-bold">{data.signals.today}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">High Confidence</span>
                <span className="text-sm font-bold">{data.signals.high_confidence}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Win Rate</span>
                <span className="text-sm font-bold">{data.signals.win_rate.toFixed(1)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Alert Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span className="text-sm">Critical</span>
                </div>
                <span className="text-sm font-bold">{data.alerts.critical}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm">Warning</span>
                </div>
                <span className="text-sm font-bold">{data.alerts.warning}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Info className="h-4 w-4 text-blue-500" />
                  <span className="text-sm">Info</span>
                </div>
                <span className="text-sm font-bold">{data.alerts.info}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>API Latency Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resource Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stackId="1"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Pending Signals */}
      {data.signals.pending.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Pending High-Confidence Signals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.signals.pending.map((signal, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-secondary rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <span className="font-bold">${signal.ticker}</span>
                    <Badge variant="outline">{signal.signal_type}</Badge>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm">
                      Confidence: {(signal.confidence * 100).toFixed(0)}%
                    </span>
                    <span className="text-sm font-bold text-green-600">
                      +{(signal.expected_return * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}