import { useState, useEffect, useCallback } from 'react';
import { 
  diagnosticsService, 
  DatabaseStatus, 
  CacheStatus, 
  RefreshStatus 
} from '../../services/api/diagnostics';

export const useDiagnosticsData = () => {
  const [databaseStatus, setDatabaseStatus] = useState<DatabaseStatus | null>(null);
  const [cacheStatus, setCacheStatus] = useState<CacheStatus | null>(null);
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingRefresh, setTestingRefresh] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [invalidatingCache, setInvalidatingCache] = useState(false);

  const fetchAllStatuses = useCallback(async () => {
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
  }, []);

  const handleTestRefresh = useCallback(async () => {
    setTestingRefresh(true);
    try {
      const result = await diagnosticsService.testRefresh();
      alert(`Test ${result.overall_status}: ${result.steps.length} steps completed`);
      await fetchAllStatuses();
      return result;
    } catch (error: any) {
      alert('Test failed: ' + (error.message || 'Unknown error'));
      throw error;
    } finally {
      setTestingRefresh(false);
    }
  }, [fetchAllStatuses]);

  const handleRecalculateIndex = useCallback(async () => {
    if (!confirm('Recalculate the entire index? This may take a moment.')) {
      return null;
    }
    
    setRecalculating(true);
    try {
      const result = await diagnosticsService.recalculateIndex();
      if (result.status === 'success') {
        alert('Index recalculated successfully!');
        await fetchAllStatuses();
      } else {
        alert('Recalculation failed: ' + (result.error || 'Unknown error'));
      }
      return result;
    } catch (error: any) {
      alert('Failed to recalculate: ' + (error.message || 'Unknown error'));
      throw error;
    } finally {
      setRecalculating(false);
    }
  }, [fetchAllStatuses]);

  const handleInvalidateCache = useCallback(async (pattern: string) => {
    setInvalidatingCache(true);
    try {
      const result = await diagnosticsService.invalidateCache(pattern);
      alert(`Cleared ${result.invalidated_count} cache entries`);
      await fetchAllStatuses();
      return result;
    } catch (error: any) {
      alert('Failed to clear cache: ' + (error.message || 'Unknown error'));
      throw error;
    } finally {
      setInvalidatingCache(false);
    }
  }, [fetchAllStatuses]);

  useEffect(() => {
    fetchAllStatuses();
    const interval = setInterval(fetchAllStatuses, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchAllStatuses]);

  return {
    databaseStatus,
    cacheStatus,
    refreshStatus,
    loading,
    testingRefresh,
    recalculating,
    invalidatingCache,
    fetchAllStatuses,
    handleTestRefresh,
    handleRecalculateIndex,
    handleInvalidateCache
  };
};