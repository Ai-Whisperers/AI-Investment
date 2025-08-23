"use client";

import { useState, useEffect } from "react";
import { diagnosticsService, manualService } from "../services/api";
import type { DatabaseStatus, RefreshStatus, RefreshResponse } from "../services/api";

interface SmartRefreshProps {
  onRefresh?: () => void;
  onRefreshComplete?: () => void;
  className?: string;
}

const RefreshModeInfo = {
  auto: {
    name: "Auto",
    description: "Intelligently chooses the best strategy based on your API plan",
    icon: "",
    color: "blue"
  },
  minimal: {
    name: "Minimal",
    description: "Fetches only priority assets (optimized for free tier)",
    icon: "",
    color: "green"
  },
  cached: {
    name: "Cached",
    description: "Uses cached data only (no API calls)",
    icon: "",
    color: "gray"
  },
  full: {
    name: "Full",
    description: "Complete refresh with rate limiting protection",
    icon: "",
    color: "purple"
  }
};

export default function SmartRefresh({ onRefresh, onRefreshComplete, className }: SmartRefreshProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatus | null>(null);
  const [databaseStatus, setDatabaseStatus] = useState<DatabaseStatus | null>(null);
  const [selectedMode, setSelectedMode] = useState<'auto' | 'minimal' | 'cached' | 'full'>('auto');
  const [lastRefreshResult, setLastRefreshResult] = useState<RefreshResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Load initial status
  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const [refreshRes, dbRes] = await Promise.all([
        diagnosticsService.getRefreshStatus(),
        diagnosticsService.getDatabaseStatus()
      ]);
      
      setRefreshStatus(refreshRes);
      setDatabaseStatus(dbRes);
      setError(null);
    } catch (err: any) {
      console.error('Error loading status:', err);
      setError('Failed to load status: ' + (err.message || 'Unknown error'));
    }
  };

  const handleSmartRefresh = async () => {
    setIsRefreshing(true);
    setError(null);
    setLastRefreshResult(null);

    try {
      // Call the onRefresh callback if provided
      if (onRefresh) {
        onRefresh();
      }

      const response = await manualService.smartRefresh({ mode: selectedMode });
      setLastRefreshResult(response);
      
      // Wait a moment then reload status
      setTimeout(() => {
        loadStatus();
        if (onRefreshComplete) {
          onRefreshComplete();
        }
      }, 2000);
      
    } catch (err: any) {
      console.error('Smart refresh failed:', err);
      setError('Smart refresh failed: ' + (err.message || 'Unknown error'));
    } finally {
      setIsRefreshing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OK': return 'text-green-400';
      case 'EMPTY': return 'text-yellow-400';
      case 'ERROR': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const isDataStale = refreshStatus?.prices.days_old && refreshStatus.prices.days_old > 1;
  const needsRefresh = refreshStatus?.prices.needs_update || !databaseStatus?.simulation_ready;

  // Simple button mode for dashboard
  if (!showDetails) {
    return (
      <div className="flex gap-2">
        <button
          onClick={handleSmartRefresh}
          disabled={isRefreshing}
          className={`px-6 py-3 rounded-lg font-semibold transition-all text-white ${
            isRefreshing 
              ? 'bg-gray-600 cursor-not-allowed' 
              : className || 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:shadow-lg hover:scale-105'
          }`}
        >
          {isRefreshing ? (
            <span className="flex items-center gap-2">
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
              Refreshing...
            </span>
          ) : (
            'Refresh Data'
          )}
        </button>
        <button
          onClick={() => setShowDetails(true)}
          className="px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-all"
          title="Show refresh options"
        >
          ️
        </button>
      </div>
    );
  }

  // Detailed mode with all options
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 border border-gray-700">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Smart Market Data Refresh</h2>
            <p className="text-gray-400">
              Intelligent market data management with rate limiting protection
            </p>
          </div>
          <button
            onClick={() => setShowDetails(false)}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {/* Current Status */}
        {refreshStatus && (
          <div className="bg-gray-900/50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-white mb-3">Current Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Assets:</span>
                <span className="ml-2 font-medium text-white">{refreshStatus.assets.count} symbols</span>
              </div>
              <div>
                <span className="text-gray-400">Latest data:</span>
                <span className="ml-2 font-medium text-white">
                  {refreshStatus.prices.latest_date || 'No data'}
                  {refreshStatus.prices.days_old !== null && (
                    <span className={`ml-1 ${isDataStale ? 'text-yellow-400' : 'text-green-400'}`}>
                      ({refreshStatus.prices.days_old} days old)
                    </span>
                  )}
                </span>
              </div>
              <div className="md:col-span-2">
                <span className="text-gray-400">Recommendation:</span>
                <span className={`ml-2 font-medium ${needsRefresh ? 'text-orange-400' : 'text-green-400'}`}>
                  {refreshStatus.recommendation}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Database Status */}
        {databaseStatus && (
          <div className="bg-gray-900/50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-white mb-3">Database Status</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
              {Object.entries(databaseStatus.tables).map(([table, info]) => (
                <div key={table} className="text-center">
                  <div className={`font-medium ${getStatusColor(info.status)}`}>
                    {info.count.toLocaleString()}
                  </div>
                  <div className="text-gray-400 capitalize text-xs">{table.replace('_', ' ')}</div>
                </div>
              ))}
            </div>
            <div className={`mt-3 text-sm font-medium ${
              databaseStatus.simulation_ready ? 'text-green-400' : 'text-orange-400'
            }`}>
              {databaseStatus.message}
            </div>
          </div>
        )}

        {/* Refresh Mode Selection */}
        <div className="mb-6">
          <h3 className="font-semibold text-white mb-3">Refresh Mode</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(RefreshModeInfo).map(([mode, info]) => (
              <button
                key={mode}
                onClick={() => setSelectedMode(mode as any)}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  selectedMode === mode
                    ? 'border-purple-500 bg-purple-500/20'
                    : 'border-gray-600 hover:border-gray-500 bg-gray-700/50'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{info.icon}</span>
                  <span className="font-semibold text-white">{info.name}</span>
                </div>
                <p className="text-xs text-gray-400">{info.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={handleSmartRefresh}
            disabled={isRefreshing}
            className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all text-white ${
              isRefreshing
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:shadow-lg hover:scale-105'
            }`}
          >
            {isRefreshing ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                Refreshing in {RefreshModeInfo[selectedMode].name} mode...
              </span>
            ) : (
              `Start ${RefreshModeInfo[selectedMode].name} Refresh`
            )}
          </button>

          <button
            onClick={loadStatus}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-all"
          >
            Reload Status
          </button>
        </div>

        {/* Results */}
        {lastRefreshResult && (
          <div className="bg-green-900/30 border border-green-500/50 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-green-400 mb-2">Refresh Complete</h4>
            <p className="text-sm text-green-300 mb-2">{lastRefreshResult.message}</p>
            {lastRefreshResult.mode && (
              <div className="text-xs text-green-400">
                <div><strong>Mode:</strong> {lastRefreshResult.mode}</div>
                {lastRefreshResult.features && (
                  <div><strong>Features:</strong> {lastRefreshResult.features.join(', ')}</div>
                )}
                {lastRefreshResult.note && (
                  <div className="mt-1 italic">{lastRefreshResult.note}</div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-red-400 mb-2">Error</h4>
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        {/* Help Text */}
        <div className="text-xs text-gray-500 space-y-1">
          <p><strong>Tip:</strong> Use "Minimal" mode for free TwelveData plans to avoid rate limits.</p>
          <p><strong>Performance:</strong> Smart refresh automatically handles caching and rate limiting.</p>
          <p><strong>Background:</strong> Refresh runs in the background - you can continue using the app.</p>
        </div>
      </div>
    </div>
  );
}