/**
 * Chart configuration constants and utilities
 */

export const CHART_COLORS = {
  autoindex: '#8b5cf6',
  sp500: '#ec4899',
  movingAverage: 'rgba(251, 191, 36, 0.7)',
  upperBand: 'rgba(239, 68, 68, 0.3)',
  lowerBand: 'rgba(34, 197, 94, 0.3)',
  assets: {
    'AAPL': '#A8DADC',
    'GOOGL': '#457B9D',
    'MSFT': '#1D3557',
    'AMZN': '#F1FAEE',
    'TSLA': '#E63946',
    'NVDA': '#2A9D8F',
    'META': '#264653',
    'BRK.B': '#E76F51',
    'JPM': '#F4A261',
    'V': '#E9C46A',
    default: '#94a3b8'
  }
};

export const CHART_STYLES = {
  tooltip: {
    backgroundColor: 'rgba(17, 24, 39, 0.95)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    padding: '12px',
  },
  axis: {
    stroke: 'rgba(255,255,255,0.5)',
    fontSize: 12,
  },
  grid: {
    strokeDasharray: '3 3',
    stroke: 'rgba(255,255,255,0.1)',
  },
  legend: {
    color: 'rgba(255,255,255,0.8)',
  },
  brush: {
    stroke: 'rgba(139, 92, 246, 0.5)',
    fill: 'rgba(139, 92, 246, 0.1)',
    height: 30,
  }
};

export const CHART_MARGINS = {
  top: 5,
  right: 30,
  left: 20,
  bottom: 5,
};

export const TIME_RANGES = {
  '1M': { days: 30, label: '1 Month' },
  '3M': { days: 90, label: '3 Months' },
  '6M': { days: 180, label: '6 Months' },
  '1Y': { days: 365, label: '1 Year' },
  '3Y': { days: 1095, label: '3 Years' },
  '5Y': { days: 1825, label: '5 Years' },
  'all': { days: null, label: 'All Time' },
};

export const ANIMATION_CONFIG = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.3 },
};

/**
 * Format value for Y-axis display
 */
export function formatYAxisValue(value: number): string {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
  return value.toFixed(0);
}

/**
 * Format value for tooltip display
 */
export function formatTooltipValue(value: number): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

/**
 * Format date for X-axis display
 */
export function formatXAxisDate(date: string): string {
  const d = new Date(date);
  return `${d.getMonth() + 1}/${d.getDate()}/${d.getFullYear().toString().slice(-2)}`;
}

/**
 * Get color for asset
 */
export function getAssetColor(symbol: string): string {
  return CHART_COLORS.assets[symbol as keyof typeof CHART_COLORS.assets] || CHART_COLORS.assets.default;
}