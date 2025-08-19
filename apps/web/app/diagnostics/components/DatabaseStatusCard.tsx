import React from 'react';
import { motion } from 'framer-motion';
import { DatabaseStatus } from '../../services/api/diagnostics';

interface DatabaseStatusCardProps {
  status: DatabaseStatus | null;
  onRecalculate: () => void;
  recalculating: boolean;
}

export const DatabaseStatusCard: React.FC<DatabaseStatusCardProps> = ({ 
  status, 
  onRecalculate, 
  recalculating 
}) => {
  if (!status) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
      >
        <h2 className="text-xl font-semibold mb-4 text-white">Database Status</h2>
        <div className="animate-pulse">
          <div className="h-4 bg-white/10 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-white/10 rounded w-1/2"></div>
        </div>
      </motion.div>
    );
  }

  const formatTableInfo = (table: any) => {
    return `${table.count.toLocaleString()} rows`;
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">Database Status</h2>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
          status.connected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
        }`}>
          {status.connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/5 rounded-lg p-3">
            <p className="text-sm text-white/60 mb-1">Database</p>
            <p className="text-lg font-medium text-white">{status.database_name}</p>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <p className="text-sm text-white/60 mb-1">Total Records</p>
            <p className="text-lg font-medium text-white">
              {Object.values(status.tables).reduce((sum: number, table: any) => sum + table.count, 0).toLocaleString()}
            </p>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-white/80 mb-2">Table Statistics</h3>
          <div className="space-y-2">
            {Object.entries(status.tables).map(([name, info]: [string, any]) => (
              <div key={name} className="flex justify-between items-center p-2 bg-white/5 rounded">
                <span className="text-white/60 capitalize">{name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-white">{formatTableInfo(info)}</span>
                  {info.last_updated && (
                    <span className="text-xs text-white/40">
                      {new Date(info.last_updated).toLocaleTimeString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3 mt-4">
          <button
            onClick={onRecalculate}
            disabled={recalculating}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
              recalculating
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700 transform hover:scale-105'
            }`}
          >
            {recalculating ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Recalculating...
              </span>
            ) : (
              'Recalculate Index'
            )}
          </button>
        </div>
      </div>
    </motion.div>
  );
};