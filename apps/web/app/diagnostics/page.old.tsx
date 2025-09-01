"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  diagnosticsService, 
  DatabaseStatus, 
  CacheStatus, 
  RefreshStatus,
  TestRefreshResult,
  RecalculateResult
} from '../services/api/diagnostics';

export default function DiagnosticsPage() {
  const router = useRouter();
  const [databaseStatus, setDatabaseStatus] = useState<DatabaseStatus | null>(null);
  const [cacheStatus, setCacheStatus] = useState<CacheStatus | null>(null);
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingRefresh, setTestingRefresh] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [invalidatingCache, setInvalidatingCache] = useState(false);
  
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    
    fetchAllStatuses();
    const interval = setInterval(fetchAllStatuses, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [token, router]);

  const fetchAllStatuses = async () => {
    try {
      const [db, cache, refresh] = await Promise.all([
        diagnosticsService.getDatabaseStatus(),
        diagnosticsService.getCacheStatus(),
        diagnosticsService.getRefreshStatus()
      ]);
      
      setDatabaseStatus(db);
      setCacheStatus(cache);
      setRefreshStatus(refresh);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTestRefresh = async () => {
    setTestingRefresh(true);
    try {
      const result = await diagnosticsService.testRefresh();
      alert(`Test ${result.overall_status}: ${result.steps.length} steps completed`);
      fetchAllStatuses();
    } catch (error: any) {
      alert('Test failed: ' + (error.message || 'Unknown error'));
    } finally {
      setTestingRefresh(false);
    }
  };

  const handleRecalculateIndex = async () => {
    if (!confirm('Recalculate the entire index? This may take a moment.')) return;
    
    setRecalculating(true);
    try {
      const result = await diagnosticsService.recalculateIndex();
      if (result.status === 'success') {
        alert('Index recalculated successfully!');
        fetchAllStatuses();
      } else {
        alert('Recalculation failed: ' + (result.error || 'Unknown error'));
      }
    } catch (error: any) {
      alert('Failed to recalculate: ' + (error.message || 'Unknown error'));
    } finally {
      setRecalculating(false);
    }
  };

  const handleInvalidateCache = async (pattern: string) => {
    setInvalidatingCache(true);
    try {
      const result = await diagnosticsService.invalidateCache(pattern);
      alert(`Cleared ${result.invalidated_count} cache entries`);
      fetchAllStatuses();
    } catch (error: any) {
      alert('Failed to clear cache: ' + (error.message || 'Unknown error'));
    } finally {
      setInvalidatingCache(false);
    }
  };

  const getHealthColor = (status: string): string => {
    switch (status) {
      case 'OK':
      case 'connected':
        return 'text-green-400';
      case 'EMPTY':
      case 'disconnected':
        return 'text-yellow-400';
      case 'ERROR':
      case 'error':
        return 'text-red-400';
      default:
        return 'text-neutral-400';
    }
  };

  const getHealthIcon = (status: string): string => {
    switch (status) {
      case 'OK':
      case 'connected':
        return '';
      case 'EMPTY':
      case 'disconnected':
        return '';
      case 'ERROR':
      case 'error':
        return '';
      default:
        return '?';
    }
  };

  const getHealthBg = (status: string): string => {
    switch (status) {
      case 'OK':
      case 'connected':
        return 'bg-green-500/10 border-green-500/30';
      case 'EMPTY':
      case 'disconnected':
        return 'bg-yellow-500/10 border-yellow-500/30';
      case 'ERROR':
      case 'error':
        return 'bg-red-500/10 border-red-500/30';
      default:
        return 'bg-neutral-500/10 border-neutral-500/30';
    }
  };

  return (
    <main className="min-h-screen relative">
      <div className="fixed inset-0 gradient-bg opacity-5" />
      
      <div className="max-w-7xl mx-auto px-6 py-10 relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <div className="flex justify-between items-start mb-8">
            <div>
              <h1 className="text-4xl font-bold mb-2 gradient-text">System Diagnostics</h1>
              <p className="text-neutral-400">Monitor system health and performance</p>
            </div>
            <div className="flex items-center gap-3 mt-2">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={fetchAllStatuses}
                className="btn-secondary text-sm px-4 py-2"
              >
                Refresh Status
              </motion.button>
              <button
                onClick={() => router.push("/dashboard")}
                className="btn-ghost btn-sm"
              >
                Back to Dashboard
              </button>
            </div>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="h-48 skeleton rounded-xl" />
              <div className="h-48 skeleton rounded-xl" />
              <div className="h-48 skeleton rounded-xl" />
            </div>
          ) : (
            <>
              {/* System Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* Database Health */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="card"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-white">Database</h3>
                    <span className={`text-2xl ${
                      databaseStatus?.simulation_ready 
                        ? 'text-green-400' 
                        : 'text-yellow-400'
                    }`}>
                      {databaseStatus?.simulation_ready ? '' : ''}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-400 mb-4">
                    {databaseStatus?.message}
                  </p>
                  <div className="space-y-2">
                    {databaseStatus && Object.entries(databaseStatus.tables).map(([table, info]) => (
                      <div key={table} className="flex justify-between text-xs">
                        <span className="text-neutral-400 capitalize">{table.replace('_', ' ')}</span>
                        <span className={getHealthColor(info.status)}>
                          {info.count.toLocaleString()} records
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>

                {/* Cache Health */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1 }}
                  className="card"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-white">Cache</h3>
                    <span className={`text-2xl ${getHealthColor(cacheStatus?.status || '')}`}>
                      {getHealthIcon(cacheStatus?.status || '')}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-400 mb-4">
                    {cacheStatus?.message}
                  </p>
                  {cacheStatus?.stats && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-neutral-400">Total Entries</span>
                        <span className="text-white">{cacheStatus.stats.total_entries}</span>
                      </div>
                      {cacheStatus.stats.hit_rate !== undefined && (
                        <div className="flex justify-between text-xs">
                          <span className="text-neutral-400">Hit Rate</span>
                          <span className="text-green-400">
                            {(cacheStatus.stats.hit_rate * 100).toFixed(1)}%
                          </span>
                        </div>
                      )}
                      {cacheStatus.stats.memory_usage && (
                        <div className="flex justify-between text-xs">
                          <span className="text-neutral-400">Memory</span>
                          <span className="text-white">{cacheStatus.stats.memory_usage}</span>
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>

                {/* Data Freshness */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 }}
                  className="card"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-white">Data Status</h3>
                    <span className={`text-2xl ${
                      refreshStatus?.prices.needs_update 
                        ? 'text-yellow-400' 
                        : 'text-green-400'
                    }`}>
                      {refreshStatus?.prices.needs_update ? '' : ''}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-400 mb-4">
                    {refreshStatus?.recommendation}
                  </p>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-neutral-400">Assets</span>
                      <span className="text-white">{refreshStatus?.assets.count || 0}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-neutral-400">Latest Update</span>
                      <span className="text-white">
                        {refreshStatus?.prices?.days_old !== null 
                          ? `${refreshStatus?.prices?.days_old} days ago`
                          : 'Never'}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-neutral-400">Benchmark</span>
                      <span className={refreshStatus?.assets.has_benchmark ? 'text-green-400' : 'text-yellow-400'}>
                        {refreshStatus?.assets.has_benchmark ? 'Available' : 'Missing'}
                      </span>
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Database Tables Detail */}
              {databaseStatus && (
                <motion.section
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="card mb-6"
                >
                  <h2 className="text-xl font-semibold gradient-text mb-4">Database Tables</h2>
                  
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {Object.entries(databaseStatus.tables).map(([table, info]) => (
                      <motion.div
                        key={table}
                        whileHover={{ scale: 1.05 }}
                        className={`p-4 rounded-lg border text-center ${getHealthBg(info.status)}`}
                      >
                        <div className={`text-2xl font-bold ${getHealthColor(info.status)}`}>
                          {info.count.toLocaleString()}
                        </div>
                        <div className="text-xs text-neutral-400 capitalize mt-1">
                          {table.replace('_', ' ')}
                        </div>
                        {info.latest_date && (
                          <div className="text-xs text-neutral-500 mt-1">
                            {new Date(info.latest_date).toLocaleDateString()}
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                </motion.section>
              )}

              {/* Cache Management */}
              {cacheStatus && (
                <motion.section
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="card mb-6"
                >
                  <h2 className="text-xl font-semibold gradient-text mb-4">Cache Management</h2>
                  
                  {cacheStatus.stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-white/5 rounded-lg p-4">
                        <p className="text-xs text-neutral-400">Total Entries</p>
                        <p className="text-xl font-bold text-white">
                          {cacheStatus.stats.total_entries.toLocaleString()}
                        </p>
                      </div>
                      {cacheStatus.stats.memory_usage && (
                        <div className="bg-white/5 rounded-lg p-4">
                          <p className="text-xs text-neutral-400">Memory Usage</p>
                          <p className="text-xl font-bold text-white">
                            {cacheStatus.stats.memory_usage}
                          </p>
                        </div>
                      )}
                      {cacheStatus.stats.hit_rate !== undefined && (
                        <div className="bg-white/5 rounded-lg p-4">
                          <p className="text-xs text-neutral-400">Hit Rate</p>
                          <p className="text-xl font-bold text-green-400">
                            {(cacheStatus.stats.hit_rate * 100).toFixed(1)}%
                          </p>
                        </div>
                      )}
                      {cacheStatus.stats.miss_rate !== undefined && (
                        <div className="bg-white/5 rounded-lg p-4">
                          <p className="text-xs text-neutral-400">Miss Rate</p>
                          <p className="text-xl font-bold text-orange-400">
                            {(cacheStatus.stats.miss_rate * 100).toFixed(1)}%
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Cache Actions */}
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => handleInvalidateCache('index')}
                      disabled={invalidatingCache}
                      className="btn-secondary btn-sm"
                    >
                      Clear Index Cache
                    </button>
                    <button
                      onClick={() => handleInvalidateCache('market')}
                      disabled={invalidatingCache}
                      className="btn-secondary btn-sm"
                    >
                      Clear Market Cache
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Clear all cache entries?')) {
                          handleInvalidateCache('*');
                        }
                      }}
                      disabled={invalidatingCache}
                      className="btn-ghost btn-sm text-red-400"
                    >
                      Clear All Cache
                    </button>
                  </div>
                </motion.section>
              )}

              {/* System Actions */}
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="card"
              >
                <h2 className="text-xl font-semibold gradient-text mb-4">System Actions</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleTestRefresh}
                    disabled={testingRefresh}
                    className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
                  >
                    <div className="text-2xl mb-2"></div>
                    <p className="text-sm font-medium">Test Refresh</p>
                    <p className="text-xs text-neutral-400 mt-1">
                      {testingRefresh ? 'Testing...' : 'Validate refresh process'}
                    </p>
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleRecalculateIndex}
                    disabled={recalculating}
                    className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
                  >
                    <div className="text-2xl mb-2"></div>
                    <p className="text-sm font-medium">Recalculate Index</p>
                    <p className="text-xs text-neutral-400 mt-1">
                      {recalculating ? 'Recalculating...' : 'Fix normalization issues'}
                    </p>
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={fetchAllStatuses}
                    className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
                  >
                    <div className="text-2xl mb-2"></div>
                    <p className="text-sm font-medium">Refresh All</p>
                    <p className="text-xs text-neutral-400 mt-1">Update all statistics</p>
                  </motion.button>
                </div>
              </motion.section>

              {/* System Information */}
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="card mt-6"
              >
                <h2 className="text-xl font-semibold gradient-text mb-4">System Information</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-medium text-neutral-300 mb-3">Environment</h3>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-neutral-400">API URL</span>
                        <span className="text-white font-mono">
                          {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Environment</span>
                        <span className="text-white">
                          {process.env.NODE_ENV === 'production' ? 'Production' : 'Development'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-neutral-300 mb-3">Timestamps</h3>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Database Check</span>
                        <span className="text-white">
                          {databaseStatus?.timestamp 
                            ? new Date(databaseStatus.timestamp).toLocaleTimeString()
                            : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Cache Check</span>
                        <span className="text-white">
                          {cacheStatus?.timestamp 
                            ? new Date(cacheStatus.timestamp).toLocaleTimeString()
                            : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.section>
            </>
          )}
        </motion.div>
      </div>
    </main>
  );
}