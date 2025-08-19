import { useState, useCallback, useMemo } from 'react';

type SeriesPoint = { date: string; value: number };

export const useChartControls = () => {
  const [chartTimeRange, setChartTimeRange] = useState<string>("all");
  const [showComparison, setShowComparison] = useState(true);
  const [showDataPanel, setShowDataPanel] = useState(false);
  const [selectedDataSeries, setSelectedDataSeries] = useState<string[]>(["autoindex", "sp500"]);
  const [showVolume, setShowVolume] = useState(false);
  const [showMovingAverage, setShowMovingAverage] = useState(false);
  const [showVolatilityBands, setShowVolatilityBands] = useState(false);
  const [individualAssets, setIndividualAssets] = useState<{[key: string]: boolean}>({});
  const [hoveredAsset, setHoveredAsset] = useState<string | null>(null);
  const [showAdvancedAnalytics, setShowAdvancedAnalytics] = useState(false);

  const filterDataByRange = useCallback((data: SeriesPoint[]) => {
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
  }, [chartTimeRange]);

  const calculateMovingAverage = useCallback((data: SeriesPoint[], period: number = 20) => {
    return data.map((_, index) => {
      if (index < period - 1) return null;
      const slice = data.slice(index - period + 1, index + 1);
      const avg = slice.reduce((sum, point) => sum + point.value, 0) / period;
      return avg;
    });
  }, []);

  const calculateVolatility = useCallback((data: SeriesPoint[], period: number = 20) => {
    const returns = data.slice(1).map((point, i) => 
      (point.value - data[i].value) / data[i].value
    );
    
    return data.map((_, index) => {
      if (index < period) return { upper: null, lower: null };
      
      const slice = returns.slice(Math.max(0, index - period), index);
      const mean = slice.reduce((sum, r) => sum + r, 0) / slice.length;
      const variance = slice.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / slice.length;
      const stdDev = Math.sqrt(variance) * Math.sqrt(252); // Annualized
      
      const currentValue = data[index].value;
      return {
        upper: currentValue * (1 + 2 * stdDev),
        lower: currentValue * (1 - 2 * stdDev)
      };
    });
  }, []);

  return {
    chartTimeRange,
    setChartTimeRange,
    showComparison,
    setShowComparison,
    showDataPanel,
    setShowDataPanel,
    selectedDataSeries,
    setSelectedDataSeries,
    showVolume,
    setShowVolume,
    showMovingAverage,
    setShowMovingAverage,
    showVolatilityBands,
    setShowVolatilityBands,
    individualAssets,
    setIndividualAssets,
    hoveredAsset,
    setHoveredAsset,
    showAdvancedAnalytics,
    setShowAdvancedAnalytics,
    filterDataByRange,
    calculateMovingAverage,
    calculateVolatility
  };
};