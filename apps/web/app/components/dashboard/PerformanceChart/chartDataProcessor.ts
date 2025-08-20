import { SeriesPoint } from '../../../types/portfolio';
import { TIME_RANGES } from './chartConfig';
import { portfolioService } from '../../../services/api/portfolio';

/**
 * Filter data by time range
 */
export function filterDataByRange(
  data: SeriesPoint[],
  timeRange: string
): SeriesPoint[] {
  if (timeRange === 'all' || data.length === 0) return data;

  const rangeConfig = TIME_RANGES[timeRange as keyof typeof TIME_RANGES];
  if (!rangeConfig || !rangeConfig.days) return data;

  const now = new Date();
  const cutoffDate = new Date(now.getTime() - rangeConfig.days * 24 * 60 * 60 * 1000);
  
  return data.filter(point => new Date(point.date) >= cutoffDate);
}

/**
 * Calculate moving average
 */
export function calculateMovingAverage(
  data: SeriesPoint[],
  period: number = 20
): (number | null)[] {
  return data.map((_, index) => {
    if (index < period - 1) return null;
    
    const slice = data.slice(index - period + 1, index + 1);
    const avg = slice.reduce((sum, point) => sum + point.value, 0) / period;
    return avg;
  });
}

/**
 * Calculate volatility bands
 */
export function calculateVolatilityBands(
  data: SeriesPoint[],
  period: number = 20
): { upper: (number | null)[]; lower: (number | null)[] } {
  const upper: (number | null)[] = [];
  const lower: (number | null)[] = [];

  data.forEach((point, index) => {
    if (index < period) {
      upper.push(null);
      lower.push(null);
      return;
    }

    const slice = data.slice(Math.max(0, index - period), index);
    const values = slice.map(p => p.value);
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    upper.push(point.value + 2 * stdDev);
    lower.push(point.value - 2 * stdDev);
  });

  return { upper, lower };
}

/**
 * Align multiple data series to common dates
 */
export function alignDataSeries(
  series: { [key: string]: SeriesPoint[] }
): any[] {
  // Collect all unique dates
  const allDates = new Set<string>();
  Object.values(series).forEach(data => {
    data.forEach(point => allDates.add(point.date));
  });

  // Sort dates
  const sortedDates = Array.from(allDates).sort();

  // Create maps for each series
  const seriesMaps: { [key: string]: Map<string, number> } = {};
  Object.entries(series).forEach(([key, data]) => {
    seriesMaps[key] = new Map(data.map(p => [p.date, p.value]));
  });

  // Build aligned data
  return sortedDates.map(date => {
    const dataPoint: any = { date };
    Object.entries(seriesMaps).forEach(([key, map]) => {
      dataPoint[key] = map.get(date) || null;
    });
    return dataPoint;
  });
}

/**
 * Calculate performance metrics using backend API
 */
export async function calculatePerformanceMetrics(data: SeriesPoint[]) {
  if (data.length < 2) {
    return {
      totalReturn: 0,
      dailyReturn: 0,
      monthlyReturn: 0,
      yearlyReturn: 0,
      volatility: 0,
    };
  }

  try {
    const latest = data[data.length - 1];
    const first = data[0];
    const yesterday = data[data.length - 2];
    const monthAgo = data[Math.max(0, data.length - 30)];
    const yearAgo = data[Math.max(0, data.length - 252)];

    // Convert to values array for API calculations
    const values = data.map(point => point.value);
    
    // Calculate returns using API
    const [totalReturn, dailyReturn, monthlyReturn, yearlyReturn, returns, volatility] = await Promise.all([
      portfolioService.calculateTotalReturn(first.value, latest.value),
      portfolioService.calculateTotalReturn(yesterday.value, latest.value),
      monthAgo ? portfolioService.calculateTotalReturn(monthAgo.value, latest.value) : Promise.resolve(0),
      yearAgo ? portfolioService.calculateTotalReturn(yearAgo.value, latest.value) : Promise.resolve(0),
      portfolioService.calculateReturns(values),
      portfolioService.calculateVolatility(values.slice(1).map((val, i) => (val - values[i]) / values[i]))
    ]);

    return {
      totalReturn,
      dailyReturn,
      monthlyReturn,
      yearlyReturn,
      volatility,
    };
  } catch (error) {
    console.error('Error calculating performance metrics via API:', error);
    
    // Fallback to local calculation if API fails
    const latest = data[data.length - 1];
    const first = data[0];
    const yesterday = data[data.length - 2];
    const monthAgo = data[Math.max(0, data.length - 30)];
    const yearAgo = data[Math.max(0, data.length - 252)];

    // Calculate returns
    const totalReturn = ((latest.value - first.value) / first.value) * 100;
    const dailyReturn = ((latest.value - yesterday.value) / yesterday.value) * 100;
    const monthlyReturn = monthAgo ? ((latest.value - monthAgo.value) / monthAgo.value) * 100 : 0;
    const yearlyReturn = yearAgo ? ((latest.value - yearAgo.value) / yearAgo.value) * 100 : 0;

    // Calculate volatility (simplified)
    const returns = data.slice(1).map((point, i) => 
      (point.value - data[i].value) / data[i].value
    );
    const meanReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - meanReturn, 2), 0) / returns.length;
    const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100; // Annualized

    return {
      totalReturn,
      dailyReturn,
      monthlyReturn,
      yearlyReturn,
      volatility,
    };
  }
}

/**
 * Normalize data series for comparison
 */
export function normalizeDataSeries(
  series: SeriesPoint[],
  baseValue: number = 100
): SeriesPoint[] {
  if (series.length === 0) return [];

  const firstValue = series[0].value;
  const multiplier = baseValue / firstValue;

  return series.map(point => ({
    ...point,
    value: point.value * multiplier,
  }));
}