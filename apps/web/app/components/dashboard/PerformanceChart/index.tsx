"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Brush,
  ReferenceLine,
} from 'recharts';

import { SeriesPoint, AllocationItem } from '../../../types/portfolio';
import { portfolioService } from '../../../services/api/portfolio';

// Import components
import { ChartTooltip } from './ChartTooltip';
import { ChartControlsPanel } from './ChartControlsPanel';
import { AssetSelector } from './AssetSelector';

// Import utilities
import {
  CHART_COLORS,
  CHART_STYLES,
  CHART_MARGINS,
  ANIMATION_CONFIG,
  formatYAxisValue,
  formatXAxisDate,
  getAssetColor,
} from './chartConfig';

import {
  filterDataByRange,
  calculateMovingAverage,
  calculateVolatilityBands,
  alignDataSeries,
} from './chartDataProcessor';

interface PerformanceChartProps {
  indexSeries: SeriesPoint[];
  spSeries: SeriesPoint[];
  allocations: AllocationItem[];
  loading?: boolean;
}

export function PerformanceChart({
  indexSeries,
  spSeries,
  allocations,
  loading = false,
}: PerformanceChartProps) {
  // Chart controls state
  const [chartTimeRange, setChartTimeRange] = useState('all');
  const [showComparison, setShowComparison] = useState(true);
  const [showMovingAverage, setShowMovingAverage] = useState(false);
  const [showVolatilityBands, setShowVolatilityBands] = useState(false);
  const [showDataPanel, setShowDataPanel] = useState(false);
  
  // Asset selection state
  const [individualAssets, setIndividualAssets] = useState<{ [key: string]: boolean }>({});
  const [assetSeriesData, setAssetSeriesData] = useState<{ [key: string]: SeriesPoint[] }>({});
  const [loadingAssets, setLoadingAssets] = useState<{ [key: string]: boolean }>({});

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
      setIndividualAssets(prev => ({ ...prev, [symbol]: false }));
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

  // Process chart data
  const chartData = useMemo(() => {
    // Filter data by time range
    const filteredIndex = filterDataByRange(indexSeries, chartTimeRange);
    const filteredSp = filterDataByRange(spSeries, chartTimeRange);
    
    // Prepare series object
    const series: { [key: string]: SeriesPoint[] } = {
      autoindex: filteredIndex,
    };
    
    if (showComparison) {
      series.sp500 = filteredSp;
    }
    
    // Add individual asset series
    Object.entries(individualAssets).forEach(([symbol, isSelected]) => {
      if (isSelected && assetSeriesData[symbol]) {
        series[symbol] = filterDataByRange(assetSeriesData[symbol], chartTimeRange);
      }
    });
    
    // Align all series to common dates
    const aligned = alignDataSeries(series);
    
    // Add technical indicators if needed
    if (showMovingAverage && filteredIndex.length >= 20) {
      const ma = calculateMovingAverage(filteredIndex);
      aligned.forEach((point, index) => {
        point.ma20 = ma[index];
      });
    }
    
    if (showVolatilityBands && filteredIndex.length >= 20) {
      const bands = calculateVolatilityBands(filteredIndex);
      aligned.forEach((point, index) => {
        point.upperBand = bands.upper[index];
        point.lowerBand = bands.lower[index];
      });
    }
    
    return aligned;
  }, [indexSeries, spSeries, chartTimeRange, showComparison, showMovingAverage, 
      showVolatilityBands, individualAssets, assetSeriesData]);

  if (loading) {
    return (
      <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
        <div className="animate-pulse">
          <div className="h-[400px] bg-white/10 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <motion.div {...ANIMATION_CONFIG} className="space-y-4">
      <div className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Performance Chart</h3>
        </div>

        <ChartControlsPanel
          chartTimeRange={chartTimeRange}
          setChartTimeRange={setChartTimeRange}
          showComparison={showComparison}
          setShowComparison={setShowComparison}
          showMovingAverage={showMovingAverage}
          setShowMovingAverage={setShowMovingAverage}
          showVolatilityBands={showVolatilityBands}
          setShowVolatilityBands={setShowVolatilityBands}
          showDataPanel={showDataPanel}
          setShowDataPanel={setShowDataPanel}
        />

        <AssetSelector
          allocations={allocations}
          individualAssets={individualAssets}
          setIndividualAssets={setIndividualAssets}
          loadingAssets={loadingAssets}
          showPanel={showDataPanel}
        />

        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={CHART_MARGINS}>
            <CartesianGrid {...CHART_STYLES.grid} />
            <XAxis 
              dataKey="date"
              tick={{ ...CHART_STYLES.axis }}
              tickFormatter={formatXAxisDate}
            />
            <YAxis 
              tick={{ ...CHART_STYLES.axis }}
              tickFormatter={formatYAxisValue}
            />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={CHART_STYLES.legend} iconType="line" />
            
            {/* Volatility Bands */}
            {showVolatilityBands && (
              <>
                <Line
                  type="monotone"
                  dataKey="upperBand"
                  stroke={CHART_COLORS.upperBand}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Upper Band"
                />
                <Line
                  type="monotone"
                  dataKey="lowerBand"
                  stroke={CHART_COLORS.lowerBand}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Lower Band"
                />
              </>
            )}
            
            {/* Main series */}
            <Line
              type="monotone"
              dataKey="autoindex"
              stroke={CHART_COLORS.autoindex}
              strokeWidth={2}
              dot={false}
              name="AutoIndex"
              connectNulls
            />
            
            {showComparison && (
              <Line
                type="monotone"
                dataKey="sp500"
                stroke={CHART_COLORS.sp500}
                strokeWidth={2}
                dot={false}
                name="S&P 500"
                connectNulls
              />
            )}
            
            {/* Moving Average */}
            {showMovingAverage && (
              <Line
                type="monotone"
                dataKey="ma20"
                stroke={CHART_COLORS.movingAverage}
                strokeWidth={1}
                strokeDasharray="3 3"
                dot={false}
                name="MA(20)"
              />
            )}
            
            {/* Individual Assets */}
            {Object.entries(individualAssets).map(([symbol, isSelected]) =>
              isSelected && assetSeriesData[symbol] && (
                <Line
                  key={symbol}
                  type="monotone"
                  dataKey={symbol}
                  stroke={getAssetColor(symbol)}
                  strokeWidth={1.5}
                  dot={false}
                  name={symbol}
                  connectNulls
                  opacity={0.8}
                />
              )
            )}
            
            <Brush 
              dataKey="date"
              {...CHART_STYLES.brush}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}

export default PerformanceChart;