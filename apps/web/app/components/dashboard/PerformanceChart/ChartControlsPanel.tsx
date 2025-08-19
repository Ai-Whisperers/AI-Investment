import React from 'react';
import { motion } from 'framer-motion';
import { TIME_RANGES } from './chartConfig';

interface ChartControlsPanelProps {
  chartTimeRange: string;
  setChartTimeRange: (range: string) => void;
  showComparison: boolean;
  setShowComparison: (show: boolean) => void;
  showMovingAverage: boolean;
  setShowMovingAverage: (show: boolean) => void;
  showVolatilityBands: boolean;
  setShowVolatilityBands: (show: boolean) => void;
  showDataPanel: boolean;
  setShowDataPanel: (show: boolean) => void;
}

export const ChartControlsPanel: React.FC<ChartControlsPanelProps> = ({
  chartTimeRange,
  setChartTimeRange,
  showComparison,
  setShowComparison,
  showMovingAverage,
  setShowMovingAverage,
  showVolatilityBands,
  setShowVolatilityBands,
  showDataPanel,
  setShowDataPanel,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-4 mb-4">
      {/* Time Range Selector */}
      <div className="flex items-center gap-2">
        <span className="text-white/60 text-sm">Period:</span>
        <div className="flex gap-1">
          {Object.entries(TIME_RANGES).map(([key, config]) => (
            <button
              key={key}
              onClick={() => setChartTimeRange(key)}
              className={`px-3 py-1 rounded text-xs transition-all ${
                chartTimeRange === key
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/10 text-white/60 hover:bg-white/20'
              }`}
            >
              {key}
            </button>
          ))}
        </div>
      </div>

      {/* Toggle Controls */}
      <div className="flex items-center gap-4 ml-auto">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showComparison}
            onChange={(e) => setShowComparison(e.target.checked)}
            className="w-4 h-4 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500"
          />
          <span className="text-white/60 text-sm">S&P 500</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showMovingAverage}
            onChange={(e) => setShowMovingAverage(e.target.checked)}
            className="w-4 h-4 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500"
          />
          <span className="text-white/60 text-sm">MA(20)</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showVolatilityBands}
            onChange={(e) => setShowVolatilityBands(e.target.checked)}
            className="w-4 h-4 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500"
          />
          <span className="text-white/60 text-sm">Volatility</span>
        </label>

        <button
          onClick={() => setShowDataPanel(!showDataPanel)}
          className={`px-3 py-1 rounded text-sm transition-all ${
            showDataPanel
              ? 'bg-purple-600 text-white'
              : 'bg-white/10 text-white/60 hover:bg-white/20'
          }`}
        >
          Data Panel
        </button>
      </div>
    </div>
  );
};