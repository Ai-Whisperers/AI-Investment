"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import SmartRefresh from "../components/SmartRefresh";
import StrategyConfig from "../components/StrategyConfig";
import { marketDataApi, DatabaseStatus } from "../utils/api";

export default function AdminPage() {
  const router = useRouter();
  const [databaseStatus, setDatabaseStatus] = useState<DatabaseStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    
    loadDatabaseStatus();
  }, [token, router]);

  const loadDatabaseStatus = async () => {
    try {
      const response = await marketDataApi.getDatabaseStatus();
      setDatabaseStatus(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load database status:', err);
      setError('Failed to load status: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav className="bg-black/20 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push("/dashboard")}
                className="btn-ghost btn-sm"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-semibold text-white">
                Admin Panel
              </h1>
            </div>
            
            <button
              onClick={() => {
                localStorage.removeItem("token");
                router.push("/login");
              }}
              className="btn-ghost btn-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* System Status Overview */}
        <div className="card">
          <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
            System Status
          </h2>
          
          {loading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-white/20 rounded w-1/4"></div>
              <div className="h-20 bg-white/20 rounded"></div>
            </div>
          ) : error ? (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400">{error}</p>
              <button
                onClick={loadDatabaseStatus}
                className="btn-secondary btn-sm mt-2"
              >
                Retry
              </button>
            </div>
          ) : databaseStatus ? (
            <div className="space-y-4">
              <div className={`p-4 rounded-lg border ${
                databaseStatus.simulation_ready 
                  ? 'bg-green-500/10 border-green-500/30' 
                  : 'bg-yellow-500/10 border-yellow-500/30'
              }`}>
                <p className={`font-medium ${
                  databaseStatus.simulation_ready ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {databaseStatus.simulation_ready ? ' ' : ' '}
                  {databaseStatus.message}
                </p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(databaseStatus.tables).map(([table, info]) => (
                  <div
                    key={table}
                    className={`p-4 rounded-lg border text-center backdrop-blur-sm ${
                      info.status === 'OK' 
                        ? 'bg-green-500/10 border-green-500/30' 
                        : info.status === 'EMPTY'
                        ? 'bg-yellow-500/10 border-yellow-500/30'
                        : 'bg-red-500/10 border-red-500/30'
                    }`}
                  >
                    <div className={`text-2xl font-bold ${
                      info.status === 'OK' ? 'text-green-400' : 
                      info.status === 'EMPTY' ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {info.count.toLocaleString()}
                    </div>
                    <div className="text-sm text-neutral-400 capitalize">{table.replace('_', ' ')}</div>
                    {info.latest_date && (
                      <div className="text-xs text-neutral-400 mt-1">
                        Latest: {new Date(info.latest_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        {/* Smart Refresh Panel */}
        <SmartRefresh onRefreshComplete={loadDatabaseStatus} />

        {/* Strategy Configuration */}
        <StrategyConfig />

        {/* AutoIndex Recalculation */}
        <div className="card">
          <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
            AutoIndex Management
          </h2>
          
          <div className="space-y-4">
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
              <h3 className="font-medium text-yellow-400 mb-2">️ Fix AutoIndex Normalization</h3>
              <p className="text-sm text-yellow-300 mb-3">
                If AutoIndex values appear extremely large compared to individual assets, 
                this indicates a normalization issue that can be fixed by recalculating.
              </p>
              <button
                onClick={async () => {
                  try {
                    setLoading(true);
                    const response = await marketDataApi.recalculateIndex();
                    console.log('Recalculation result:', response.data);
                    if (response.data.status === 'success') {
                      alert('AutoIndex recalculated successfully! Values should now be normalized to base 100.');
                      loadDatabaseStatus();
                    } else {
                      alert('Recalculation failed: ' + response.data.error);
                    }
                  } catch (err: any) {
                    console.error('Recalculation error:', err);
                    alert('Failed to recalculate: ' + (err.response?.data?.detail || err.message));
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
                className="btn-secondary btn-sm"
              >
                {loading ? 'Recalculating...' : 'Recalculate AutoIndex'}
              </button>
            </div>
          </div>
        </div>

        {/* API Information */}
        <div className="card">
          <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
            API Endpoints
          </h2>
          
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium text-neutral-200 mb-2">Market Data Management</h3>
                <ul className="space-y-1 text-neutral-300">
                  <li><code className="bg-white/10 px-2 py-1 rounded text-xs">POST /api/v1/manual/smart-refresh</code></li>
                  <li><code className="bg-white/10 px-2 py-1 rounded text-xs">POST /api/v1/manual/trigger-refresh</code></li>
                  <li><code className="bg-white/10 px-2 py-1 rounded text-xs">POST /api/v1/manual/minimal-refresh</code></li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium text-neutral-200 mb-2">Diagnostics</h3>
                <ul className="space-y-1 text-neutral-300">
                  <li><code className="bg-white/10 px-2 py-1 rounded text-xs">GET /api/v1/diagnostics/database-status</code></li>
                  <li><code className="bg-white/10 px-2 py-1 rounded text-xs">GET /api/v1/diagnostics/refresh-status</code></li>
                  <li><code className="bg-white/10 px-2 py-1 rounded text-xs">POST /api/v1/diagnostics/test-refresh</code></li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Configuration Info */}
        <div className="card">
          <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
            Configuration Tips
          </h2>
          
          <div className="space-y-4 text-sm text-neutral-300">
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
              <h3 className="font-medium text-blue-400 mb-2">For Free Tier Users</h3>
              <div className="space-y-1 text-neutral-300">
                <div><code className="bg-white/10 px-1 py-0.5 rounded text-xs">REFRESH_MODE=minimal</code> - Fetches only 5 priority symbols</div>
                <div><code className="bg-white/10 px-1 py-0.5 rounded text-xs">TWELVEDATA_RATE_LIMIT=8</code> - Respects free tier limits</div>
                <div><code className="bg-white/10 px-1 py-0.5 rounded text-xs">ENABLE_MARKET_DATA_CACHE=true</code> - Use caching to reduce API calls</div>
              </div>
            </div>
            
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
              <h3 className="font-medium text-green-400 mb-2">For Paid Plans</h3>
              <div className="space-y-1 text-neutral-300">
                <div><code className="bg-white/10 px-1 py-0.5 rounded text-xs">REFRESH_MODE=auto</code> - Smart mode selection</div>
                <div><code className="bg-white/10 px-1 py-0.5 rounded text-xs">TWELVEDATA_RATE_LIMIT=800</code> - Higher limits (adjust based on plan)</div>
                <div><code className="bg-white/10 px-1 py-0.5 rounded text-xs">SKIP_STARTUP_REFRESH=false</code> - Full refresh on deployment</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}