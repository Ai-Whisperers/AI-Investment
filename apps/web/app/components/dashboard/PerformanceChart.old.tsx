"use client";

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  Brush,
} from 'recharts';

import { SeriesPoint, AllocationItem } from '../../types/portfolio';
import { TimeRange } from '../../types/chart';
import { useChartData } from '../../hooks/useChartData';
import { portfolioService } from '../../services/api/portfolio';
import { CHART_COLORS, CHART_TOOLTIP_STYLE, CHART_AXIS_STYLE } from '../../constants/theme';
import { TIME_RANGE_OPTIONS, PORTFOLIO_CONFIG } from '../../constants/config';
import { LoadingChart } from '../shared/LoadingSkeleton';

interface PerformanceChartProps {
  indexSeries: SeriesPoint[];
  spSeries: SeriesPoint[];
  loading: boolean;
  chartTimeRange: TimeRange;
  setChartTimeRange: (range: TimeRange) => void;
  showComparison: boolean;
  setShowComparison: (show: boolean) => void;
  showDataPanel: boolean;
  setShowDataPanel: (show: boolean) => void;
  showMovingAverage: boolean;
  setShowMovingAverage: (show: boolean) => void;
  showVolatilityBands: boolean;
  setShowVolatilityBands: (show: boolean) => void;
  individualAssets: { [key: string]: boolean };
  setIndividualAssets: (assets: { [key: string]: boolean }) => void;
  allocations: AllocationItem[];
}

export function PerformanceChart({
  indexSeries,
  spSeries,
  loading,
  chartTimeRange,
  setChartTimeRange,
  showComparison,
  setShowComparison,
  showDataPanel,
  setShowDataPanel,
  showMovingAverage,
  setShowMovingAverage,
  showVolatilityBands,
  setShowVolatilityBands,
  individualAssets,
  setIndividualAssets,
  allocations,
}: PerformanceChartProps) {
  const [assetSeriesData, setAssetSeriesData] = useState<{ [key: string]: SeriesPoint[] }>({});
  const [loadingAssets, setLoadingAssets] = useState<{ [key: string]: boolean }>({});

  // Use chart data hook
  const { filteredIndexSeries, filteredSpSeries, alignedChartData } = useChartData({
    indexSeries,
    spSeries,
    timeRange: chartTimeRange,
    showComparison,
    showMovingAverage,
    showVolatilityBands,
    individualAssets: assetSeriesData,
  });

  // Fetch individual asset data
  const fetchAssetData = async (symbol: string) => {
    if (assetSeriesData[symbol] || loadingAssets[symbol]) return;
    
    setLoadingAssets(prev => ({ ...prev, [symbol]: true }));
    
    try {
      const response = await portfolioService.getAssetHistory(symbol);
      setAssetSeriesData(prev => ({ 
        ...prev, 
        [symbol]: response.series 
      }));
    } catch (err) {
      console.error(`Failed to fetch data for ${symbol}:`, err);
      setIndividualAssets({ ...individualAssets, [symbol]: false });
    } finally {
      setLoadingAssets(prev => ({ ...prev, [symbol]: false }));
    }
  };

  // Fetch asset data when selected
  useEffect(() => {
    Object.entries(individualAssets).forEach(([symbol, isSelected]) => {
      if (isSelected && !assetSeriesData[symbol] && !loadingAssets[symbol]) {
        fetchAssetData(symbol);
      }
    });
  }, [individualAssets]);

  // Calculate performance metrics
  const calculatePerformanceMetrics = () => {
    if (filteredIndexSeries.length === 0) return null;
    
    const indexStart = filteredIndexSeries[0]?.value || 100;
    const indexEnd = filteredIndexSeries[filteredIndexSeries.length - 1]?.value || 100;
    const spStart = filteredSpSeries[0]?.value || 100;
    const spEnd = filteredSpSeries[filteredSpSeries.length - 1]?.value || 100;
    
    const indexReturn = ((indexEnd - indexStart) / indexStart) * 100;
    const spReturn = ((spEnd - spStart) / spStart) * 100;
    const outperformance = indexReturn - spReturn;
    
    return {
      indexReturn,
      spReturn,
      outperformance,
      indexValue: indexEnd,
      spValue: spEnd
    };
  };
  
  const performanceMetrics = calculatePerformanceMetrics();

  if (loading) {
    return <LoadingChart />;
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="card mb-6"
    >
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold gradient-text mb-2">Performance History</h2>
            <p className="text-sm text-neutral-400">AutoIndex vs S&P 500 Benchmark Comparison</p>
          </div>
          
          {/* Performance Metrics Display */}
          {performanceMetrics && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex gap-4 mt-4 sm:mt-0"
            >
              <div className="text-center">
                <p className="text-xs text-neutral-400">AutoIndex</p>
                <p className={`text-lg font-bold ${performanceMetrics.indexReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {performanceMetrics.indexReturn >= 0 ? '+' : ''}{performanceMetrics.indexReturn.toFixed(2)}%
                </p>
              </div>
              
              {filteredSpSeries.length > 0 && (
                <>
                  <div className="text-center">
                    <p className="text-xs text-neutral-400">S&P 500</p>
                    <p className={`text-lg font-bold ${performanceMetrics.spReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {performanceMetrics.spReturn >= 0 ? '+' : ''}{performanceMetrics.spReturn.toFixed(2)}%
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-neutral-400">Outperformance</p>
                    <p className={`text-lg font-bold ${performanceMetrics.outperformance >= 0 ? 'text-purple-400' : 'text-orange-400'}`}>
                      {performanceMetrics.outperformance >= 0 ? '+' : ''}{performanceMetrics.outperformance.toFixed(2)}%
                    </p>
                  </div>
                </>
              )}
            </motion.div>
          )}
        </div>
        
        {/* Controls */}
        <div className="flex flex-wrap gap-2">
          {/* Time Range Selector */}
          <div className="flex bg-white/5 rounded-lg p-1">
            {TIME_RANGE_OPTIONS.map((range) => (
              <button
                key={range.key}
                onClick={() => setChartTimeRange(range.key)}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${
                  chartTimeRange === range.key
                    ? "bg-purple-500 text-white"
                    : "text-neutral-400 hover:text-white hover:bg-white/5"
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
          
          {/* Data Panel Toggle */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowDataPanel(!showDataPanel)}
            className="btn-secondary btn-sm"
          >
            {showDataPanel ? "Hide" : "Show"} Data Options
          </motion.button>
        </div>
        
        {/* Data Panel */}
        <AnimatePresence>
          {showDataPanel && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-4 p-4 bg-white/5 rounded-lg border border-white/10"
            >
              <ChartDataPanel
                showComparison={showComparison}
                setShowComparison={setShowComparison}
                showMovingAverage={showMovingAverage}
                setShowMovingAverage={setShowMovingAverage}
                showVolatilityBands={showVolatilityBands}
                setShowVolatilityBands={setShowVolatilityBands}
                individualAssets={individualAssets}
                setIndividualAssets={setIndividualAssets}
                allocations={allocations}
                loadingAssets={loadingAssets}
                filteredIndexSeries={filteredIndexSeries}
                filteredSpSeries={filteredSpSeries}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart 
          data={alignedChartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 40 }}
        >
          <defs>
            <linearGradient id="colorIndex" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="colorSP" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ec4899" stopOpacity={0.6}/>
              <stop offset="95%" stopColor="#ec4899" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          
          <XAxis 
            dataKey="date" 
            minTickGap={50}
            {...CHART_AXIS_STYLE}
            tickFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
            }}
          />
          
          <YAxis 
            {...CHART_AXIS_STYLE}
            tickFormatter={(value) => `${value.toFixed(0)}`}
          />
          
          <Tooltip 
            contentStyle={CHART_TOOLTIP_STYLE}
            labelStyle={{ color: '#e5e5e5' }}
            itemStyle={{ color: '#e5e5e5' }}
            labelFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleDateString('en-US', { 
                weekday: 'short',
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
              });
            }}
            formatter={(value: number, name: string) => {
              const labels: { [key: string]: string } = {
                value: "AutoIndex",
                sp: "S&P 500",
                ma: "50-Day MA",
                upperBand: "Upper Band",
                lowerBand: "Lower Band"
              };
              const label = labels[name] || name;
              return [
                value ? `${value.toFixed(2)}` : 'N/A',
                label
              ];
            }}
          />
          
          <Legend />
          
          <ReferenceLine y={100} stroke="rgba(255,255,255,0.3)" strokeDasharray="5 5" />
          
          <Area 
            type="monotone" 
            dataKey="value" 
            name="AutoIndex" 
            stroke="#8b5cf6" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorIndex)"
            dot={false}
            activeDot={{ r: 6, stroke: '#8b5cf6', strokeWidth: 2, fill: '#1f1f23' }}
          />
          
          {showComparison && (
            <Area 
              type="monotone" 
              dataKey="sp" 
              name="S&P 500" 
              stroke="#ec4899" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorSP)"
              dot={false}
              activeDot={{ r: 6, stroke: '#ec4899', strokeWidth: 2, fill: '#1f1f23' }}
            />
          )}
          
          {/* Technical Indicators */}
          {showMovingAverage && (
            <Line 
              type="monotone" 
              dataKey="ma" 
              name="50-Day MA" 
              stroke="#10b981" 
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              fill="none"
              activeDot={{ r: 4, stroke: '#10b981', strokeWidth: 2, fill: '#1f1f23' }}
            />
          )}
          
          {showVolatilityBands && (
            <>
              <Line 
                type="monotone" 
                dataKey="upperBand" 
                name="Upper Band" 
                stroke="#3b82f6" 
                strokeWidth={1}
                strokeDasharray="3 3"
                dot={false}
                fill="none"
              />
              <Line 
                type="monotone" 
                dataKey="lowerBand" 
                name="Lower Band" 
                stroke="#3b82f6" 
                strokeWidth={1}
                strokeDasharray="3 3"
                dot={false}
                fill="none"
              />
            </>
          )}
          
          {/* Individual Asset Lines */}
          {Object.entries(individualAssets).map(([symbol, isSelected], index) => {
            if (!isSelected || !assetSeriesData[symbol]) return null;
            
            const color = CHART_COLORS[(index + 2) % CHART_COLORS.length];
            
            return (
              <Line 
                key={symbol}
                type="monotone" 
                dataKey={symbol} 
                name={symbol} 
                stroke={color} 
                strokeWidth={2}
                dot={false}
                fill="none"
                activeDot={{ r: 4, stroke: color, strokeWidth: 2, fill: '#1f1f23' }}
              />
            );
          })}
          
          <Brush 
            dataKey="date" 
            height={30} 
            stroke="#8b5cf6"
            tickFormatter={(value) => {
              const date = new Date(value);
              return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.section>
  );
}

// Chart Data Panel Component
function ChartDataPanel({
  showComparison,
  setShowComparison,
  showMovingAverage,
  setShowMovingAverage,
  showVolatilityBands,
  setShowVolatilityBands,
  individualAssets,
  setIndividualAssets,
  allocations,
  loadingAssets,
  filteredIndexSeries,
  filteredSpSeries,
}: any) {
  return (
    <>
      <div className="mb-4">
        <h3 className="text-sm font-medium text-neutral-300 mb-3">Chart Display Options</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Primary Data Series */}
          <div>
            <p className="text-xs text-neutral-400 mb-2">Primary Data</p>
            <div className="space-y-2">
              <button
                onClick={() => setShowComparison(!showComparison)}
                className={`w-full px-3 py-2 rounded-lg text-sm transition-all flex items-center justify-between ${
                  showComparison
                    ? "bg-purple-500 text-white"
                    : "bg-white/10 text-neutral-400 hover:bg-white/20"
                } ${filteredSpSeries.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={filteredSpSeries.length === 0}
              >
                <span className="flex items-center gap-2">
                  <span>S&P 500 Benchmark</span>
                  {filteredSpSeries.length === 0 && (
                    <span className="text-xs opacity-75">(No Data)</span>
                  )}
                </span>
                <span className={`w-2 h-2 rounded-full ${showComparison && filteredSpSeries.length > 0 ? 'bg-white' : 'bg-neutral-600'}`}></span>
              </button>
            </div>
          </div>
          
          {/* Technical Indicators */}
          <div>
            <p className="text-xs text-neutral-400 mb-2">Technical Indicators</p>
            <div className="space-y-2">
              <button
                onClick={() => setShowVolatilityBands(!showVolatilityBands)}
                className={`w-full px-3 py-2 rounded-lg text-sm transition-all flex items-center justify-between ${
                  showVolatilityBands
                    ? "bg-blue-500 text-white"
                    : "bg-white/10 text-neutral-400 hover:bg-white/20"
                }`}
              >
                <span>Volatility Bands</span>
                <span className={`w-2 h-2 rounded-full ${showVolatilityBands ? 'bg-white' : 'bg-neutral-600'}`}></span>
              </button>
              
              <button
                onClick={() => setShowMovingAverage(!showMovingAverage)}
                className={`w-full px-3 py-2 rounded-lg text-sm transition-all flex items-center justify-between ${
                  showMovingAverage
                    ? "bg-green-500 text-white"
                    : "bg-white/10 text-neutral-400 hover:bg-white/20"
                }`}
              >
                <span>Moving Average (50)</span>
                <span className={`w-2 h-2 rounded-full ${showMovingAverage ? 'bg-white' : 'bg-neutral-600'}`}></span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Individual Assets Section */}
      {allocations.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-neutral-300 mb-3">Individual Assets</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-32 overflow-y-auto">
            {allocations.slice(0, PORTFOLIO_CONFIG.MAX_ASSETS_DISPLAY).map((asset: AllocationItem, index: number) => (
              <button
                key={asset.symbol}
                onClick={() => setIndividualAssets((prev: any) => ({
                  ...prev,
                  [asset.symbol]: !prev[asset.symbol]
                }))}
                disabled={loadingAssets[asset.symbol]}
                className={`px-2 py-1 rounded text-xs transition-all flex items-center justify-between ${
                  individualAssets[asset.symbol]
                    ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                    : "bg-white/10 text-neutral-400 hover:bg-white/20"
                } ${loadingAssets[asset.symbol] ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <span className="flex items-center">
                  <div 
                    className="w-2 h-2 rounded-full mr-2" 
                    style={{ backgroundColor: CHART_COLORS[(index + 2) % CHART_COLORS.length] }}
                  />
                  {asset.symbol}
                  {loadingAssets[asset.symbol] && (
                    <div className="ml-1 w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin"></div>
                  )}
                </span>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  individualAssets[asset.symbol] ? 'bg-white' : 'bg-neutral-600'
                }`}></span>
              </button>
            ))}
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div className="bg-white/5 rounded-lg p-2">
          <p className="text-neutral-400 mb-1">Data Points</p>
          <p className="font-medium text-white">{filteredIndexSeries.length}</p>
        </div>
        <div className="bg-white/5 rounded-lg p-2">
          <p className="text-neutral-400 mb-1">Date Range</p>
          <p className="font-medium text-white">
            {filteredIndexSeries[0]?.date ? new Date(filteredIndexSeries[0].date).toLocaleDateString() : 'N/A'}
          </p>
        </div>
        <div className="bg-white/5 rounded-lg p-2">
          <p className="text-neutral-400 mb-1">Update Status</p>
          <p className="font-medium text-green-400">Live</p>
        </div>
        <div className="bg-white/5 rounded-lg p-2">
          <p className="text-neutral-400 mb-1">Benchmark</p>
          <p className="font-medium text-white">S&P 500</p>
        </div>
      </div>
    </>
  );
}