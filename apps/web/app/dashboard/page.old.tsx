"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../core/presentation/contexts/AuthContext";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell, ReferenceLine, Brush } from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import { 
  portfolioService, 
  benchmarkService, 
  strategyService,
  backgroundTaskService,
  type RiskMetric 
} from "../services/api";
import SmartRefresh from "../components/SmartRefresh";
import AdvancedAnalytics from "../components/dashboard/AdvancedAnalytics";
import { SystemHealthIndicator } from "../core/presentation/components/SystemHealthIndicator";
import { DataQualityIndicator } from "../core/presentation/components/DataQualityIndicator";
import TaskNotifications from "../components/shared/TaskNotifications";

type SeriesPoint = { date: string; value: number };
type AllocationItem = { symbol: string; weight: number; name?: string; sector?: string };

export default function Dashboard() {
  const router = useRouter();
  const [indexSeries, setIndexSeries] = useState<SeriesPoint[]>([]);
  const [spSeries, setSpSeries] = useState<SeriesPoint[]>([]);
  const [allocations, setAllocations] = useState<AllocationItem[]>([]);
  const [amount, setAmount] = useState(10000);
  const [currency, setCurrency] = useState("USD");
  const [currencies, setCurrencies] = useState<{[key: string]: string}>({});
  const [startDate, setStartDate] = useState<string>("2019-01-01");
  const [simResult, setSimResult] = useState<{amount_final:number; roi_pct:number; currency:string} | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [hoveredAsset, setHoveredAsset] = useState<string | null>(null);
  const [chartTimeRange, setChartTimeRange] = useState<string>("all");
  const [showComparison, setShowComparison] = useState(true);
  const [showDataPanel, setShowDataPanel] = useState(false);
  const [selectedDataSeries, setSelectedDataSeries] = useState<string[]>(["autoindex", "sp500"]);
  const [showVolume, setShowVolume] = useState(false);
  const [showMovingAverage, setShowMovingAverage] = useState(false);
  const [showVolatilityBands, setShowVolatilityBands] = useState(false);
  const [individualAssets, setIndividualAssets] = useState<{[key: string]: boolean}>({});
  const [assetSeriesData, setAssetSeriesData] = useState<{[key: string]: SeriesPoint[]}>({});
  const [loadingAssets, setLoadingAssets] = useState<{[key: string]: boolean}>({});
  const [riskMetrics, setRiskMetrics] = useState<RiskMetric | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showAdvancedAnalytics, setShowAdvancedAnalytics] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();
  
  // Function to refresh dashboard data using new services
  const refreshDashboardData = async () => {
    setRefreshing(true);
    try {
      // Trigger background refresh task
      const taskResponse = await backgroundTaskService.triggerRefresh({ mode: 'smart' });
      
      // Poll for task completion
      await backgroundTaskService.pollTaskStatus(
        taskResponse.task_id,
        (status) => {
          console.log('Refresh task status:', status);
        },
        1000,
        30
      );
      
      // Reload data after refresh
      await loadDashboardData();
    } catch (err) {
      console.error('Failed to refresh dashboard data:', err);
    } finally {
      setRefreshing(false);
    }
  };

  // Function to load dashboard data
  const loadDashboardData = async () => {
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
    }
  };

  // Function to fetch individual asset data with better error handling
  const fetchAssetData = async (symbol: string) => {
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
      setIndividualAssets(prev => ({ ...prev, [symbol]: false }));
    } finally {
      setLoadingAssets(prev => ({ ...prev, [symbol]: false }));
    }
  };

  // Chart colors for pie chart
  const COLORS = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#a855f7'];

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
      return;
    }
    
    if (!isLoading && isAuthenticated) {
      loadDashboardData().finally(() => setLoading(false));
    }
  }, [isAuthenticated, isLoading, router]);

  // Fetch asset data when individual assets are selected
  useEffect(() => {
    Object.entries(individualAssets).forEach(([symbol, isSelected]) => {
      if (isSelected && !assetSeriesData[symbol] && !loadingAssets[symbol]) {
        fetchAssetData(symbol);
      }
    });
  }, [individualAssets]);

  const runSimulation = async () => {
    setSimulating(true);
    try {
      const result = await portfolioService.runSimulation({ 
        amount, 
        startDate,
        currency 
      });
      setSimResult({ 
        amount_final: result.end_value, 
        roi_pct: ((result.end_value - amount) / amount) * 100,
        currency: result.currency || currency
      });
    } catch (error) {
      console.error('Simulation failed:', error);
      alert('Failed to run simulation. Please try again.');
    } finally {
      setSimulating(false);
    }
  };

  // Filter data based on time range
  const filterDataByRange = (data: SeriesPoint[]) => {
    if (chartTimeRange === "all" || data.length === 0) return data;
    
    const now = new Date();
    const ranges: {[key: string]: number} = {
      "1M": 30,
      "3M": 90,
      "6M": 180,
      "1Y": 365,
      "3Y": 1095,
      "5Y": 1825
    };
    
    const daysToShow = ranges[chartTimeRange];
    if (!daysToShow) return data;
    
    const cutoffDate = new Date(now.getTime() - daysToShow * 24 * 60 * 60 * 1000);
    return data.filter(point => new Date(point.date) >= cutoffDate);
  };

  // Calculate moving average
  const calculateMovingAverage = (data: SeriesPoint[], period: number = 20) => {
    return data.map((_, index) => {
      if (index < period - 1) return null;
      const slice = data.slice(index - period + 1, index + 1);
      const avg = slice.reduce((sum, point) => sum + point.value, 0) / period;
      return avg;
    }).filter(val => val !== null);
  };

  // Calculate volatility bands (simplified Bollinger Bands)
  const calculateVolatilityBands = (data: SeriesPoint[], period: number = 20) => {
    const ma = calculateMovingAverage(data, period);
    return data.slice(period - 1).map((point, index) => {
      const maValue = ma[index] as number;
      const slice = data.slice(index, index + period);
      const variance = slice.reduce((sum, p) => sum + Math.pow(p.value - maValue, 2), 0) / period;
      const stdDev = Math.sqrt(variance);
      return {
        upper: maValue + 2 * stdDev,
        lower: maValue - 2 * stdDev,
        middle: maValue
      };
    });
  };

  // Prepare chart data
  const chartData = useMemo(() => {
    const filteredIndex = filterDataByRange(indexSeries);
    const filteredSP = filterDataByRange(spSeries);
    
    // Find common dates
    const indexMap = new Map(filteredIndex.map(p => [p.date, p.value]));
    const spMap = new Map(filteredSP.map(p => [p.date, p.value]));
    const allDates = Array.from(new Set([...indexMap.keys(), ...spMap.keys()])).sort();
    
    // Build combined data
    let combinedData = allDates.map(date => {
      const dataPoint: any = {
        date,
        autoindex: indexMap.get(date) || null,
        sp500: spMap.get(date) || null,
      };
      
      // Add individual asset data
      Object.entries(individualAssets).forEach(([symbol, isSelected]) => {
        if (isSelected && assetSeriesData[symbol]) {
          const assetData = filterDataByRange(assetSeriesData[symbol]);
          const assetValue = assetData.find(p => p.date === date)?.value;
          dataPoint[symbol] = assetValue || null;
        }
      });
      
      return dataPoint;
    });
    
    // Add technical indicators if enabled
    if (showMovingAverage && filteredIndex.length >= 20) {
      const ma = calculateMovingAverage(filteredIndex, 20);
      combinedData = combinedData.slice(-ma.length).map((point, index) => ({
        ...point,
        ma20: ma[index]
      }));
    }
    
    if (showVolatilityBands && filteredIndex.length >= 20) {
      const bands = calculateVolatilityBands(filteredIndex, 20);
      combinedData = combinedData.slice(-bands.length).map((point, index) => ({
        ...point,
        upperBand: bands[index].upper,
        lowerBand: bands[index].lower
      }));
    }
    
    return combinedData;
  }, [indexSeries, spSeries, chartTimeRange, showMovingAverage, showVolatilityBands, individualAssets, assetSeriesData]);

  // Prepare allocation data for pie chart
  const pieData = useMemo(() => {
    return allocations.map(alloc => ({
      name: alloc.symbol,
      value: alloc.weight * 100,
      sector: alloc.sector || 'Unknown'
    }));
  }, [allocations]);

  if (loading || isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 flex items-center justify-center">
        <div className="text-white text-2xl animate-pulse">Loading dashboard...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect to login
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 p-8">
      {/* Task Notifications */}
      <TaskNotifications />
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        {/* Header */}
        <div className="mb-6 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-white bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600 mb-2">
              Portfolio Dashboard
            </h1>
            <SystemHealthIndicator className="w-80" />
          </div>
          <div className="flex gap-4">
            <SmartRefresh 
              onRefresh={refreshDashboardData}
              className="bg-purple-600 hover:bg-purple-700"
            />
            <button
              onClick={() => setShowAdvancedAnalytics(!showAdvancedAnalytics)}
              className={`px-6 py-3 rounded-lg transition-all ${
                showAdvancedAnalytics 
                  ? 'bg-purple-700 text-white shadow-lg' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Advanced Analytics
            </button>
            <button
              onClick={() => router.push('/news')}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg transition-all"
            >
              Market News
            </button>
          </div>
        </div>

        {/* System Status Row */}
        <div className="mb-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <DataQualityIndicator 
            onRefreshNeeded={refreshDashboardData}
            className="lg:col-span-2"
          />
          <div className="space-y-4">
            <button
              onClick={() => router.push('/tasks')}
              className="w-full p-4 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 hover:bg-gray-700/50 transition-all text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">Task Center</h3>
                  <p className="text-sm text-gray-400">Monitor background operations</p>
                </div>
                <span className="text-gray-400">→</span>
              </div>
            </button>
            <button
              onClick={() => router.push('/diagnostics')}
              className="w-full p-4 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 hover:bg-gray-700/50 transition-all text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">System Health</h3>
                  <p className="text-sm text-gray-400">Full diagnostics panel</p>
                </div>
                <span className="text-gray-400">→</span>
              </div>
            </button>
          </div>
        </div>

        {/* Risk Metrics Card */}
        {riskMetrics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8 p-6 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700"
          >
            <h2 className="text-xl font-semibold text-white mb-4">Risk Metrics</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <div className="text-center">
                <p className="text-gray-400 text-sm">Total Return</p>
                <p className={`text-lg font-bold ${riskMetrics.total_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(riskMetrics.total_return * 100).toFixed(2)}%
                </p>
              </div>
              <div className="text-center">
                <p className="text-gray-400 text-sm">Sharpe Ratio</p>
                <p className="text-lg font-bold text-white">{riskMetrics.sharpe_ratio.toFixed(3)}</p>
              </div>
              <div className="text-center">
                <p className="text-gray-400 text-sm">Max Drawdown</p>
                <p className="text-lg font-bold text-red-400">
                  {(riskMetrics.max_drawdown * 100).toFixed(2)}%
                </p>
              </div>
              {riskMetrics.volatility && (
                <div className="text-center">
                  <p className="text-gray-400 text-sm">Volatility</p>
                  <p className="text-lg font-bold text-yellow-400">
                    {(riskMetrics.volatility * 100).toFixed(2)}%
                  </p>
                </div>
              )}
              {riskMetrics.beta_sp500 !== undefined && (
                <div className="text-center">
                  <p className="text-gray-400 text-sm">Beta (S&P500)</p>
                  <p className="text-lg font-bold text-white">{riskMetrics.beta_sp500.toFixed(3)}</p>
                </div>
              )}
              {riskMetrics.correlation_sp500 !== undefined && (
                <div className="text-center">
                  <p className="text-gray-400 text-sm">Correlation</p>
                  <p className="text-lg font-bold text-white">{riskMetrics.correlation_sp500.toFixed(3)}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Performance Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-8 p-6 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700"
        >
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">Performance</h2>
            <div className="flex gap-2">
              {["1M", "3M", "6M", "1Y", "3Y", "5Y", "all"].map(range => (
                <button
                  key={range}
                  onClick={() => setChartTimeRange(range)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    chartTimeRange === range 
                      ? 'bg-purple-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>

          {/* Chart Controls */}
          <div className="flex gap-4 mb-4">
            <label className="flex items-center gap-2 text-gray-300">
              <input
                type="checkbox"
                checked={showComparison}
                onChange={(e) => setShowComparison(e.target.checked)}
                className="rounded"
              />
              S&P 500
            </label>
            <label className="flex items-center gap-2 text-gray-300">
              <input
                type="checkbox"
                checked={showMovingAverage}
                onChange={(e) => setShowMovingAverage(e.target.checked)}
                className="rounded"
              />
              MA(20)
            </label>
            <label className="flex items-center gap-2 text-gray-300">
              <input
                type="checkbox"
                checked={showVolatilityBands}
                onChange={(e) => setShowVolatilityBands(e.target.checked)}
                className="rounded"
              />
              Volatility Bands
            </label>
          </div>

          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorAutoIndex" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                </linearGradient>
                <linearGradient id="colorSP500" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ec4899" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#ec4899" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}
              />
              <YAxis 
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#9ca3af' }}
                formatter={(value: any) => value ? `$${value.toFixed(2)}` : 'N/A'}
              />
              <Legend />
              
              {/* Main series */}
              <Area 
                type="monotone" 
                dataKey="autoindex" 
                stroke="#8b5cf6" 
                fillOpacity={1}
                fill="url(#colorAutoIndex)"
                strokeWidth={2}
                name="AutoIndex"
              />
              
              {showComparison && (
                <Area 
                  type="monotone" 
                  dataKey="sp500" 
                  stroke="#ec4899" 
                  fillOpacity={1}
                  fill="url(#colorSP500)"
                  strokeWidth={2}
                  name="S&P 500"
                />
              )}
              
              {/* Individual assets */}
              {Object.entries(individualAssets).map(([symbol, isSelected], index) => {
                if (!isSelected) return null;
                const color = COLORS[index % COLORS.length];
                return (
                  <Line
                    key={symbol}
                    type="monotone"
                    dataKey={symbol}
                    stroke={color}
                    strokeWidth={1.5}
                    dot={false}
                    name={symbol}
                  />
                );
              })}
              
              {/* Technical indicators */}
              {showMovingAverage && (
                <Line
                  type="monotone"
                  dataKey="ma20"
                  stroke="#10b981"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="MA(20)"
                />
              )}
              
              {showVolatilityBands && (
                <>
                  <Line
                    type="monotone"
                    dataKey="upperBand"
                    stroke="#ef4444"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                    name="Upper Band"
                  />
                  <Line
                    type="monotone"
                    dataKey="lowerBand"
                    stroke="#ef4444"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                    name="Lower Band"
                  />
                </>
              )}
              
              <Brush 
                dataKey="date" 
                height={30} 
                stroke="#8b5cf6"
                fill="#1f2937"
                tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short' })}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Allocation Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="mb-8 p-6 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700"
        >
          <h2 className="text-xl font-semibold text-white mb-4">Portfolio Allocation</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value.toFixed(1)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  animationBegin={0}
                  animationDuration={800}
                >
                  {pieData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={COLORS[index % COLORS.length]}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredAsset(entry.name)}
                      onMouseLeave={() => setHoveredAsset(null)}
                    />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                  formatter={(value: any) => `${value.toFixed(2)}%`}
                />
              </PieChart>
            </ResponsiveContainer>
            
            {/* Allocation Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-gray-300">
                <thead className="text-xs uppercase bg-gray-700/50">
                  <tr>
                    <th className="px-4 py-2">Symbol</th>
                    <th className="px-4 py-2">Weight</th>
                    <th className="px-4 py-2">Sector</th>
                    <th className="px-4 py-2">Track</th>
                  </tr>
                </thead>
                <tbody>
                  {allocations.map((alloc, index) => (
                    <tr 
                      key={alloc.symbol}
                      className={`border-b border-gray-700 hover:bg-gray-700/30 transition-colors ${
                        hoveredAsset === alloc.symbol ? 'bg-gray-700/50' : ''
                      }`}
                      onMouseEnter={() => setHoveredAsset(alloc.symbol)}
                      onMouseLeave={() => setHoveredAsset(null)}
                    >
                      <td className="px-4 py-2 font-medium text-white">{alloc.symbol}</td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-700 rounded-full h-2">
                            <div 
                              className="h-2 rounded-full"
                              style={{ 
                                width: `${alloc.weight * 100}%`,
                                backgroundColor: COLORS[index % COLORS.length]
                              }}
                            />
                          </div>
                          <span>{(alloc.weight * 100).toFixed(2)}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-2">{alloc.sector || 'Unknown'}</td>
                      <td className="px-4 py-2">
                        <input
                          type="checkbox"
                          checked={individualAssets[alloc.symbol] || false}
                          onChange={(e) => setIndividualAssets(prev => ({
                            ...prev,
                            [alloc.symbol]: e.target.checked
                          }))}
                          className="rounded cursor-pointer"
                          disabled={loadingAssets[alloc.symbol]}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>

        {/* Investment Simulator */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="p-6 bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700"
        >
          <h2 className="text-xl font-semibold text-white mb-4">Investment Simulator</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-gray-300 mb-2">Amount</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
                min="100"
                step="100"
              />
            </div>
            <div>
              <label className="block text-gray-300 mb-2">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                {Object.entries(currencies).map(([code, name]) => (
                  <option key={code} value={code}>{code} - {name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-gray-300 mb-2">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={runSimulation}
                disabled={simulating}
                className={`w-full px-6 py-2 rounded-lg font-semibold transition-all ${
                  simulating 
                    ? 'bg-gray-600 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:shadow-lg hover:scale-105'
                } text-white`}
              >
                {simulating ? 'Simulating...' : 'Run Simulation'}
              </button>
            </div>
          </div>

          {/* Simulation Results */}
          <AnimatePresence>
            {simResult && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-6 p-4 bg-gradient-to-r from-purple-900/50 to-pink-900/50 rounded-lg border border-purple-500"
              >
                <h3 className="text-lg font-semibold text-white mb-2">Simulation Results</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-gray-400">Final Amount</p>
                    <p className="text-2xl font-bold text-white">
                      {simResult.currency} {simResult.amount_final.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-400">Return on Investment</p>
                    <p className={`text-2xl font-bold ${simResult.roi_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {simResult.roi_pct >= 0 ? '+' : ''}{simResult.roi_pct.toFixed(2)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-400">Profit/Loss</p>
                    <p className={`text-2xl font-bold ${simResult.amount_final >= amount ? 'text-green-400' : 'text-red-400'}`}>
                      {simResult.currency} {(simResult.amount_final - amount).toFixed(2)}
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Advanced Analytics Section */}
        <AnimatePresence>
          {showAdvancedAnalytics && (
            <motion.div
              initial={{ opacity: 0, height: 0, y: 20 }}
              animate={{ opacity: 1, height: 'auto', y: 0 }}
              exit={{ opacity: 0, height: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="mt-8"
            >
              <AdvancedAnalytics 
                allocations={allocations}
                onRefresh={refreshDashboardData}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}