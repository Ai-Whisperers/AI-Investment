import React from 'react';
import { motion } from 'framer-motion';
import { DatabaseStatus, CacheStatus, RefreshStatus } from '../../services/api/diagnostics';

interface SystemSummaryCardProps {
  databaseStatus: DatabaseStatus | null;
  cacheStatus: CacheStatus | null;
  refreshStatus: RefreshStatus | null;
}

export const SystemSummaryCard: React.FC<SystemSummaryCardProps> = ({
  databaseStatus,
  cacheStatus,
  refreshStatus
}) => {
  const getOverallHealth = () => {
    let score = 0;
    let total = 0;
    
    if (databaseStatus) {
      total++;
      if (databaseStatus.connected) score++;
    }
    
    if (cacheStatus) {
      total++;
      if (cacheStatus.connected) score++;
    }
    
    if (refreshStatus) {
      total++;
      if (refreshStatus.data_freshness === 'fresh') score++;
    }
    
    if (total === 0) return 'unknown';
    
    const percentage = (score / total) * 100;
    if (percentage === 100) return 'healthy';
    if (percentage >= 66) return 'degraded';
    return 'critical';
  };
  
  const health = getOverallHealth();
  
  const getHealthColor = () => {
    switch (health) {
      case 'healthy':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'degraded':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };
  
  const getHealthIcon = () => {
    switch (health) {
      case 'healthy':
        return '✓';
      case 'degraded':
        return '⚠';
      case 'critical':
        return '✗';
      default:
        return '?';
    }
  };
  
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`bg-white/5 backdrop-blur-sm rounded-lg p-6 border ${getHealthColor()}`}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">System Health</h2>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full font-medium ${getHealthColor()}`}>
          <span className="text-2xl">{getHealthIcon()}</span>
          <span className="capitalize">{health}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full mb-2 ${
            databaseStatus?.connected 
              ? 'bg-green-500/20 text-green-400' 
              : 'bg-red-500/20 text-red-400'
          }`}>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7"></path>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4-3.582-4-8-4-8 1.79-8 4z"></path>
            </svg>
          </div>
          <p className="text-sm font-medium text-white">Database</p>
          <p className="text-xs text-white/60">
            {databaseStatus?.connected ? 'Connected' : 'Disconnected'}
          </p>
        </div>
        
        <div className="text-center">
          <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full mb-2 ${
            cacheStatus?.connected 
              ? 'bg-green-500/20 text-green-400' 
              : 'bg-yellow-500/20 text-yellow-400'
          }`}>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
            </svg>
          </div>
          <p className="text-sm font-medium text-white">Cache</p>
          <p className="text-xs text-white/60">
            {cacheStatus?.connected ? 'Active' : 'Fallback'}
          </p>
        </div>
        
        <div className="text-center">
          <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full mb-2 ${
            refreshStatus?.data_freshness === 'fresh'
              ? 'bg-green-500/20 text-green-400'
              : refreshStatus?.data_freshness === 'stale'
              ? 'bg-yellow-500/20 text-yellow-400'
              : 'bg-red-500/20 text-red-400'
          }`}>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
          </div>
          <p className="text-sm font-medium text-white">Data Refresh</p>
          <p className="text-xs text-white/60">
            {refreshStatus?.data_freshness === 'fresh' ? 'Fresh' : 
             refreshStatus?.data_freshness === 'stale' ? 'Stale' : 'No Data'}
          </p>
        </div>
      </div>
      
      {health !== 'healthy' && (
        <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
          <p className="text-sm text-yellow-400">
            {health === 'degraded' 
              ? 'System is operational but some services are experiencing issues.'
              : 'Critical system components are offline. Immediate attention required.'}
          </p>
        </div>
      )}
    </motion.div>
  );
};