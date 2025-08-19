import { useState, useEffect, useCallback } from 'react';
import { 
  portfolioService, 
  benchmarkService, 
  strategyService,
  backgroundTaskService,
  type RiskMetric 
} from '../../services/api';

type SeriesPoint = { date: string; value: number };
type AllocationItem = { symbol: string; weight: number; name?: string; sector?: string };

export const useDashboardData = () => {
  const [indexSeries, setIndexSeries] = useState<SeriesPoint[]>([]);
  const [spSeries, setSpSeries] = useState<SeriesPoint[]>([]);
  const [allocations, setAllocations] = useState<AllocationItem[]>([]);
  const [currencies, setCurrencies] = useState<{[key: string]: string}>({});
  const [riskMetrics, setRiskMetrics] = useState<RiskMetric | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [assetSeriesData, setAssetSeriesData] = useState<{[key: string]: SeriesPoint[]}>({});
  const [loadingAssets, setLoadingAssets] = useState<{[key: string]: boolean}>({});

  const loadDashboardData = useCallback(async () => {
    try {
      const [indexRes, spRes, allocRes, currRes, riskRes] = await Promise.all([
        portfolioService.getIndexHistory(),
        benchmarkService.getSP500Data().catch(() => ({ series: [] })),
        portfolioService.getCurrentAllocations(),
        portfolioService.getCurrencies(),
        strategyService.getRiskMetrics(30).catch(() => ({ metrics: [] }))
      ]);
      
      setIndexSeries(indexRes.series);
      setSpSeries(spRes.series);
      setAllocations(allocRes.allocations);
      setCurrencies(currRes);
      
      if (riskRes.metrics && riskRes.metrics.length > 0) {
        setRiskMetrics(riskRes.metrics[0]);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshDashboardData = useCallback(async () => {
    setRefreshing(true);
    try {
      const taskResponse = await backgroundTaskService.triggerRefresh({ mode: 'smart' });
      
      await backgroundTaskService.pollTaskStatus(
        taskResponse.task_id,
        (status) => {
          console.log('Refresh task status:', status);
        },
        1000,
        30
      );
      
      await loadDashboardData();
    } catch (err) {
      console.error('Failed to refresh dashboard data:', err);
    } finally {
      setRefreshing(false);
    }
  }, [loadDashboardData]);

  const fetchAssetData = useCallback(async (symbol: string) => {
    if (assetSeriesData[symbol] || loadingAssets[symbol]) return;
    
    setLoadingAssets(prev => ({ ...prev, [symbol]: true }));
    
    try {
      const response = await portfolioService.getAssetHistory(symbol);
      if (response && response.series) {
        setAssetSeriesData(prev => ({ 
          ...prev, 
          [symbol]: response.series 
        }));
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err: any) {
      console.error(`Failed to fetch data for ${symbol}:`, err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load asset data';
      console.warn(`${symbol}: ${errorMessage}`);
    } finally {
      setLoadingAssets(prev => ({ ...prev, [symbol]: false }));
    }
  }, [assetSeriesData, loadingAssets]);

  return {
    indexSeries,
    spSeries,
    allocations,
    currencies,
    riskMetrics,
    loading,
    refreshing,
    assetSeriesData,
    loadingAssets,
    loadDashboardData,
    refreshDashboardData,
    fetchAssetData
  };
};