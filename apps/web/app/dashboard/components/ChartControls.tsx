import React from 'react';
import { motion } from 'framer-motion';

type AllocationItem = { symbol: string; weight: number; name?: string; sector?: string };

interface ChartControlsProps {
  chartTimeRange: string;
  setChartTimeRange: (range: string) => void;
  showComparison: boolean;
  setShowComparison: (show: boolean) => void;
  showMovingAverage: boolean;
  setShowMovingAverage: (show: boolean) => void;
  showVolatilityBands: boolean;
  setShowVolatilityBands: (show: boolean) => void;
  individualAssets: {[key: string]: boolean};
  setIndividualAssets: React.Dispatch<React.SetStateAction<{[key: string]: boolean}>>;
  allocations: AllocationItem[];
  loadingAssets: {[key: string]: boolean};
}

export const ChartControls: React.FC<ChartControlsProps> = ({
  chartTimeRange,
  setChartTimeRange,
  showComparison,
  setShowComparison,
  showMovingAverage,
  setShowMovingAverage,
  showVolatilityBands,
  setShowVolatilityBands,
  individualAssets,
  setIndividualAssets,
  allocations,
  loadingAssets
}) => {
  const timeRanges = ["1M", "3M", "6M", "1Y", "3Y", "5Y", "all"];

  return (
    <div className="space-y-4">
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10"
      >
        <h4 className="text-sm font-medium text-white/80 mb-3">Time Range</h4>
        <div className="flex flex-wrap gap-2">
          {timeRanges.map((range) => (
            <button
              key={range}
              onClick={() => setChartTimeRange(range)}
              className={`px-3 py-1 rounded-md text-sm transition-all ${
                chartTimeRange === range
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/10 text-white/60 hover:bg-white/20'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10"
      >
        <h4 className="text-sm font-medium text-white/80 mb-3">Chart Options</h4>
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showComparison}
              onChange={(e) => setShowComparison(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500"
            />
            <span className="text-white/60 text-sm">Show S&P 500 Comparison</span>
          </label>
          
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showMovingAverage}
              onChange={(e) => setShowMovingAverage(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500"
            />
            <span className="text-white/60 text-sm">Show 20-Day Moving Average</span>
          </label>
          
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showVolatilityBands}
              onChange={(e) => setShowVolatilityBands(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500"
            />
            <span className="text-white/60 text-sm">Show Volatility Bands</span>
          </label>
        </div>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10"
      >
        <h4 className="text-sm font-medium text-white/80 mb-3">Individual Assets</h4>
        <div className="max-h-40 overflow-y-auto space-y-2">
          {allocations.map((allocation) => (
            <label key={allocation.symbol} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={individualAssets[allocation.symbol] || false}
                onChange={(e) => setIndividualAssets(prev => ({
                  ...prev,
                  [allocation.symbol]: e.target.checked
                }))}
                disabled={loadingAssets[allocation.symbol]}
                className="w-4 h-4 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500 disabled:opacity-50"
              />
              <span className="text-white/60 text-sm flex items-center gap-1">
                {allocation.symbol}
                {loadingAssets[allocation.symbol] && (
                  <svg className="animate-spin h-3 w-3 text-purple-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
              </span>
            </label>
          ))}
        </div>
      </motion.div>
    </div>
  );
};