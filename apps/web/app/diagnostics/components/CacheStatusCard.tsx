import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CacheStatus } from '../../services/api/diagnostics';

interface CacheStatusCardProps {
  status: CacheStatus | null;
  onInvalidate: (pattern: string) => void;
  invalidating: boolean;
}

export const CacheStatusCard: React.FC<CacheStatusCardProps> = ({ 
  status, 
  onInvalidate, 
  invalidating 
}) => {
  const [cachePattern, setCachePattern] = useState('*');

  if (!status) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
      >
        <h2 className="text-xl font-semibold mb-4 text-white">Cache Status</h2>
        <div className="animate-pulse">
          <div className="h-4 bg-white/10 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-white/10 rounded w-1/2"></div>
        </div>
      </motion.div>
    );
  }

  const hitRate = (status.total_requests ?? 0) > 0 
    ? (((status.hits ?? 0) / (status.total_requests ?? 1)) * 100).toFixed(1)
    : '0.0';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">Cache Status</h2>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
          status.connected ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
        }`}>
          {status.connected ? 'Redis Connected' : 'Fallback Mode'}
        </div>
      </div>
      
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/5 rounded-lg p-3">
            <p className="text-sm text-white/60 mb-1">Cache Entries</p>
            <p className="text-lg font-medium text-white">{status.keys}</p>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <p className="text-sm text-white/60 mb-1">Hit Rate</p>
            <p className="text-lg font-medium text-green-400">{hitRate}%</p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-white/80 mb-2">Cache Statistics</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center p-2 bg-white/5 rounded">
              <span className="text-white/60">Total Requests</span>
              <span className="text-white">{(status.total_requests ?? 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-white/5 rounded">
              <span className="text-white/60">Cache Hits</span>
              <span className="text-green-400">{(status.hits ?? 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-white/5 rounded">
              <span className="text-white/60">Cache Misses</span>
              <span className="text-orange-400">{(status.misses ?? 0).toLocaleString()}</span>
            </div>
            {status.memory_usage && (
              <div className="flex justify-between items-center p-2 bg-white/5 rounded">
                <span className="text-white/60">Memory Usage</span>
                <span className="text-white">{status.memory_usage}</span>
              </div>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-white/80 mb-2">Cache By Type</h3>
          <div className="space-y-2">
            {Object.entries(status.cache_by_type ?? {}).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center p-2 bg-white/5 rounded">
                <span className="text-white/60 capitalize">{type.replace(/_/g, ' ')}</span>
                <span className="text-white">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={cachePattern}
              onChange={(e) => setCachePattern(e.target.value)}
              placeholder="Cache pattern (e.g., portfolio:*)"
              className="flex-1 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              onClick={() => onInvalidate(cachePattern)}
              disabled={invalidating}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                invalidating
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-red-600 text-white hover:bg-red-700'
              }`}
            >
              {invalidating ? 'Clearing...' : 'Clear Cache'}
            </button>
          </div>
          <p className="text-xs text-white/40">
            Use * as wildcard. Examples: portfolio:*, user:123, *
          </p>
        </div>
      </div>
    </motion.div>
  );
};