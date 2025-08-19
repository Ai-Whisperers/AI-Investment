import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Brush, ReferenceLine } from 'recharts';
import { motion } from 'framer-motion';

type SeriesPoint = { date: string; value: number };

interface PortfolioChartProps {
  indexSeries: SeriesPoint[];
  spSeries: SeriesPoint[];
  assetSeriesData: {[key: string]: SeriesPoint[]};
  individualAssets: {[key: string]: boolean};
  showComparison: boolean;
  showMovingAverage: boolean;
  showVolatilityBands: boolean;
  filterDataByRange: (data: SeriesPoint[]) => SeriesPoint[];
  calculateMovingAverage: (data: SeriesPoint[], period?: number) => (number | null)[];
  calculateVolatility: (data: SeriesPoint[], period?: number) => { upper: number | null; lower: number | null }[];
}

export const PortfolioChart: React.FC<PortfolioChartProps> = ({
  indexSeries,
  spSeries,
  assetSeriesData,
  individualAssets,
  showComparison,
  showMovingAverage,
  showVolatilityBands,
  filterDataByRange,
  calculateMovingAverage,
  calculateVolatility
}) => {
  const chartData = useMemo(() => {
    const filteredIndex = filterDataByRange(indexSeries);
    const filteredSp = filterDataByRange(spSeries);
    
    const dates = new Set<string>();
    filteredIndex.forEach(point => dates.add(point.date));
    filteredSp.forEach(point => dates.add(point.date));
    
    Object.entries(individualAssets).forEach(([symbol, isSelected]) => {
      if (isSelected && assetSeriesData[symbol]) {
        const filtered = filterDataByRange(assetSeriesData[symbol]);
        filtered.forEach(point => dates.add(point.date));
      }
    });
    
    const sortedDates = Array.from(dates).sort();
    const indexMap = new Map(filteredIndex.map(p => [p.date, p.value]));
    const spMap = new Map(filteredSp.map(p => [p.date, p.value]));
    
    const assetMaps: {[key: string]: Map<string, number>} = {};
    Object.entries(individualAssets).forEach(([symbol, isSelected]) => {
      if (isSelected && assetSeriesData[symbol]) {
        const filtered = filterDataByRange(assetSeriesData[symbol]);
        assetMaps[symbol] = new Map(filtered.map(p => [p.date, p.value]));
      }
    });
    
    const movingAvg = showMovingAverage ? calculateMovingAverage(filteredIndex) : [];
    const volatilityBands = showVolatilityBands ? calculateVolatility(filteredIndex) : [];
    
    return sortedDates.map((date, index) => {
      const dataPoint: any = {
        date,
        autoindex: indexMap.get(date) || null,
        sp500: showComparison ? (spMap.get(date) || null) : null,
      };
      
      Object.entries(assetMaps).forEach(([symbol, map]) => {
        dataPoint[symbol] = map.get(date) || null;
      });
      
      if (showMovingAverage && movingAvg[index] !== null) {
        dataPoint.ma20 = movingAvg[index];
      }
      
      if (showVolatilityBands && volatilityBands[index]) {
        dataPoint.upperBand = volatilityBands[index].upper;
        dataPoint.lowerBand = volatilityBands[index].lower;
      }
      
      return dataPoint;
    });
  }, [indexSeries, spSeries, assetSeriesData, individualAssets, showComparison, 
      showMovingAverage, showVolatilityBands, filterDataByRange, 
      calculateMovingAverage, calculateVolatility]);

  const formatYAxis = (value: number) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
    return value.toFixed(0);
  };

  const formatTooltipValue = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const assetColors: {[key: string]: string} = {
    'AAPL': '#A8DADC',
    'GOOGL': '#457B9D',
    'MSFT': '#1D3557',
    'AMZN': '#F1FAEE',
    'TSLA': '#E63946',
    'NVDA': '#2A9D8F',
    'META': '#264653',
    'BRK.B': '#E76F51',
    'JPM': '#F4A261',
    'V': '#E9C46A'
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
    >
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis 
            dataKey="date" 
            stroke="rgba(255,255,255,0.5)"
            tick={{ fontSize: 12 }}
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear().toString().slice(-2)}`;
            }}
          />
          <YAxis 
            stroke="rgba(255,255,255,0.5)"
            tick={{ fontSize: 12 }}
            tickFormatter={formatYAxis}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(17, 24, 39, 0.95)', 
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px'
            }}
            labelStyle={{ color: 'rgba(255,255,255,0.8)' }}
            formatter={(value: any) => {
              if (value === null || value === undefined) return ['N/A', ''];
              return [formatTooltipValue(value), ''];
            }}
          />
          <Legend 
            wrapperStyle={{ color: 'rgba(255,255,255,0.8)' }}
            iconType="line"
          />
          
          {showVolatilityBands && (
            <>
              <Line 
                type="monotone" 
                dataKey="upperBand" 
                stroke="rgba(239, 68, 68, 0.3)" 
                strokeDasharray="5 5"
                dot={false}
                name="Upper Band"
              />
              <Line 
                type="monotone" 
                dataKey="lowerBand" 
                stroke="rgba(34, 197, 94, 0.3)" 
                strokeDasharray="5 5"
                dot={false}
                name="Lower Band"
              />
            </>
          )}
          
          <Line 
            type="monotone" 
            dataKey="autoindex" 
            stroke="#8b5cf6" 
            strokeWidth={2}
            dot={false}
            name="AutoIndex"
            connectNulls
          />
          
          {showComparison && (
            <Line 
              type="monotone" 
              dataKey="sp500" 
              stroke="#ec4899" 
              strokeWidth={2}
              dot={false}
              name="S&P 500"
              connectNulls
            />
          )}
          
          {showMovingAverage && (
            <Line 
              type="monotone" 
              dataKey="ma20" 
              stroke="rgba(251, 191, 36, 0.7)" 
              strokeWidth={1}
              strokeDasharray="3 3"
              dot={false}
              name="MA(20)"
            />
          )}
          
          {Object.entries(individualAssets).map(([symbol, isSelected]) => 
            isSelected && assetSeriesData[symbol] && (
              <Line 
                key={symbol}
                type="monotone" 
                dataKey={symbol} 
                stroke={assetColors[symbol] || '#94a3b8'}
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
            height={30} 
            stroke="rgba(139, 92, 246, 0.5)"
            fill="rgba(139, 92, 246, 0.1)"
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  );
};