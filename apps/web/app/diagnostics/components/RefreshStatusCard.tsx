import React from 'react';
import { motion } from 'framer-motion';
import { RefreshStatus } from '../../services/api/diagnostics';

interface RefreshStatusCardProps {
  status: RefreshStatus | null;
  onTestRefresh: () => void;
  testing: boolean;
}

export const RefreshStatusCard: React.FC<RefreshStatusCardProps> = ({ 
  status, 
  onTestRefresh, 
  testing 
}) => {
  if (!status) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
      >
        <h2 className="text-xl font-semibold mb-4 text-white">Refresh Status</h2>
        <div className="animate-pulse">
          <div className="h-4 bg-white/10 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-white/10 rounded w-1/2"></div>
        </div>
      </motion.div>
    );
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'running':
        return 'text-yellow-400';
      default:
        return 'text-white/60';
    }
  };

  const getDataFreshness = () => {
    if (!status.last_successful) return 'No data';
    
    const lastUpdate = new Date(status.last_successful);
    const now = new Date();
    const diffMs = now.getTime() - lastUpdate.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 24) {
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays} day${diffDays > 1 ? 's' : ''} old`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} old`;
    } else {
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} old`;
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">Refresh Status</h2>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
          status.data_freshness?.status === 'fresh' 
            ? 'bg-green-500/20 text-green-400' 
            : status.data_freshness?.status === 'stale'
            ? 'bg-yellow-500/20 text-yellow-400'
            : 'bg-red-500/20 text-red-400'
        }`}>
          {status.data_freshness?.status === 'fresh' ? 'Fresh Data' : 
           status.data_freshness?.status === 'stale' ? 'Stale Data' : 'No Data'}
        </div>
      </div>
      
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/5 rounded-lg p-3">
            <p className="text-sm text-white/60 mb-1">Data Age</p>
            <p className="text-lg font-medium text-white">{getDataFreshness()}</p>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <p className="text-sm text-white/60 mb-1">Last Status</p>
            <p className={`text-lg font-medium ${getStatusColor(status.last_status)}`}>
              {status.last_status.charAt(0).toUpperCase() + status.last_status.slice(1)}
            </p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-white/80 mb-2">Refresh History</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center p-2 bg-white/5 rounded">
              <span className="text-white/60">Last Attempt</span>
              <span className="text-white text-sm">{formatDate(status.last_attempt)}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-white/5 rounded">
              <span className="text-white/60">Last Success</span>
              <span className="text-green-400 text-sm">{formatDate(status.last_successful)}</span>
            </div>
            {status.last_error && (
              <div className="p-2 bg-red-500/10 rounded">
                <p className="text-sm text-red-400 font-medium mb-1">Last Error</p>
                <p className="text-xs text-white/60">{status.last_error}</p>
              </div>
            )}
          </div>
        </div>

        {status.assets_updated !== undefined && (
          <div>
            <h3 className="text-sm font-medium text-white/80 mb-2">Update Statistics</h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-white/5 rounded p-2">
                <p className="text-xs text-white/60">Assets Updated</p>
                <p className="text-lg font-medium text-white">{status.assets_updated}</p>
              </div>
              <div className="bg-white/5 rounded p-2">
                <p className="text-xs text-white/60">Prices Added</p>
                <p className="text-lg font-medium text-white">{status.prices_added || 0}</p>
              </div>
            </div>
          </div>
        )}

        <button
          onClick={onTestRefresh}
          disabled={testing}
          className={`w-full px-4 py-2 rounded-lg font-medium transition-all ${
            testing
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700 transform hover:scale-105'
          }`}
        >
          {testing ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Testing Refresh...
            </span>
          ) : (
            'Test Refresh Pipeline'
          )}
        </button>
      </div>
    </motion.div>
  );
};