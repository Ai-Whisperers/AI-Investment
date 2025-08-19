import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SmartRefresh from '../../components/SmartRefresh';
import TaskNotifications from '../../components/shared/TaskNotifications';
import { SystemHealthIndicator } from '../../core/presentation/components/SystemHealthIndicator';
import { DataQualityIndicator } from '../../core/presentation/components/DataQualityIndicator';

interface DashboardLayoutProps {
  children: React.ReactNode;
  refreshing: boolean;
  onRefresh: () => void;
  showAdvancedAnalytics: boolean;
  setShowAdvancedAnalytics: (show: boolean) => void;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  refreshing,
  onRefresh,
  showAdvancedAnalytics,
  setShowAdvancedAnalytics
}) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2">Portfolio Dashboard</h1>
          <p className="text-white/60">Track your AutoIndex performance and manage your investment strategy</p>
        </motion.div>

        <div className="flex flex-wrap gap-4 mb-6">
          <SmartRefresh onRefresh={onRefresh} isRefreshing={refreshing} />
          
          <button
            onClick={() => setShowAdvancedAnalytics(!showAdvancedAnalytics)}
            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all transform hover:scale-105"
          >
            {showAdvancedAnalytics ? 'Hide' : 'Show'} Advanced Analytics
          </button>

          <div className="ml-auto flex gap-4">
            <SystemHealthIndicator />
            <DataQualityIndicator />
          </div>
        </div>

        <TaskNotifications />

        <AnimatePresence mode="wait">
          {children}
        </AnimatePresence>
      </div>
    </div>
  );
};