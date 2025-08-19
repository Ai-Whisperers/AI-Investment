import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AllocationItem } from '../../../types/portfolio';

interface AssetSelectorProps {
  allocations: AllocationItem[];
  individualAssets: { [key: string]: boolean };
  setIndividualAssets: (assets: { [key: string]: boolean }) => void;
  loadingAssets: { [key: string]: boolean };
  showPanel: boolean;
}

export const AssetSelector: React.FC<AssetSelectorProps> = ({
  allocations,
  individualAssets,
  setIndividualAssets,
  loadingAssets,
  showPanel,
}) => {
  if (!showPanel) return null;

  const toggleAsset = (symbol: string) => {
    setIndividualAssets({
      ...individualAssets,
      [symbol]: !individualAssets[symbol],
    });
  };

  const selectAll = () => {
    const newState = allocations.reduce((acc, asset) => {
      acc[asset.symbol] = true;
      return acc;
    }, {} as { [key: string]: boolean });
    setIndividualAssets(newState);
  };

  const deselectAll = () => {
    setIndividualAssets({});
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-4 mb-4 border border-white/10"
      >
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-white/80 text-sm font-medium">Individual Assets</h4>
          <div className="flex gap-2">
            <button
              onClick={selectAll}
              className="text-xs px-2 py-1 bg-white/10 text-white/60 rounded hover:bg-white/20 transition-colors"
            >
              Select All
            </button>
            <button
              onClick={deselectAll}
              className="text-xs px-2 py-1 bg-white/10 text-white/60 rounded hover:bg-white/20 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 max-h-40 overflow-y-auto">
          {allocations.map((asset) => (
            <label
              key={asset.symbol}
              className="flex items-center gap-1 cursor-pointer hover:bg-white/5 p-1 rounded transition-colors"
            >
              <input
                type="checkbox"
                checked={individualAssets[asset.symbol] || false}
                onChange={() => toggleAsset(asset.symbol)}
                disabled={loadingAssets[asset.symbol]}
                className="w-3 h-3 rounded border-white/20 bg-white/10 text-purple-600 focus:ring-purple-500 disabled:opacity-50"
              />
              <span className="text-white/60 text-xs flex items-center gap-1">
                {asset.symbol}
                {loadingAssets[asset.symbol] && (
                  <svg className="animate-spin h-3 w-3 text-purple-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                <span className="text-white/40">({(asset.weight * 100).toFixed(1)}%)</span>
              </span>
            </label>
          ))}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};