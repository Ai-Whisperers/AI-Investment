"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useDiagnosticsData } from './hooks/useDiagnosticsData';
import { SystemSummaryCard } from './components/SystemSummaryCard';
import { DatabaseStatusCard } from './components/DatabaseStatusCard';
import { CacheStatusCard } from './components/CacheStatusCard';
import { RefreshStatusCard } from './components/RefreshStatusCard';

export default function DiagnosticsPage() {
  const router = useRouter();
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const {
    databaseStatus,
    cacheStatus,
    refreshStatus,
    loading,
    testingRefresh,
    recalculating,
    invalidatingCache,
    handleTestRefresh,
    handleRecalculateIndex,
    handleInvalidateCache
  } = useDiagnosticsData();

  useEffect(() => {
    if (!token) {
      router.push("/login");
    }
  }, [token, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-white text-center">
          <svg className="animate-spin h-12 w-12 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-lg">Loading diagnostics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2">System Diagnostics</h1>
          <p className="text-white/60">Monitor and manage your AutoIndex infrastructure</p>
        </motion.div>

        <div className="space-y-6">
          <SystemSummaryCard
            databaseStatus={databaseStatus}
            cacheStatus={cacheStatus}
            refreshStatus={refreshStatus}
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <DatabaseStatusCard
              status={databaseStatus}
              onRecalculate={handleRecalculateIndex}
              recalculating={recalculating}
            />

            <CacheStatusCard
              status={cacheStatus}
              onInvalidate={handleInvalidateCache}
              invalidating={invalidatingCache}
            />

            <RefreshStatusCard
              status={refreshStatus}
              onTestRefresh={handleTestRefresh}
              testing={testingRefresh}
            />
          </div>
        </div>
      </div>
    </div>
  );
}