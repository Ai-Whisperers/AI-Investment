"use client";

import { motion, AnimatePresence } from "framer-motion";
import { StrategyConfig } from "../../utils/api";
import { StrategyValidator } from "./ValidationRules";

interface WeightAllocationProps {
  config: StrategyConfig;
  onChange: (config: StrategyConfig) => void;
  editMode: boolean;
}

export default function WeightAllocation({ config, onChange, editMode }: WeightAllocationProps) {
  const handleWeightChange = (field: keyof StrategyConfig, value: number) => {
    onChange({
      ...config,
      [field]: value
    });
  };

  const isValidWeights = StrategyValidator.validateWeights(config);
  const weightSum = StrategyValidator.getWeightSum(config);

  const handleNormalizeWeights = () => {
    const normalized = StrategyValidator.normalizeWeights(config);
    onChange(normalized);
  };

  return (
    <div className="bg-white/5 rounded-lg p-4 border border-white/10">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-medium text-neutral-200 flex items-center gap-2">
          <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
          Strategy Weights
        </h3>
        {editMode && !isValidWeights && (
          <button
            onClick={handleNormalizeWeights}
            className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
          >
            Auto-normalize
          </button>
        )}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="text-xs text-neutral-400 uppercase tracking-wider">
            Momentum Weight
          </label>
          <div className="mt-2 relative">
            <input
              type="number"
              value={config.momentum_weight}
              onChange={(e) => handleWeightChange('momentum_weight', parseFloat(e.target.value))}
              disabled={!editMode}
              step="0.1"
              min="0"
              max="1"
              className="input"
            />
            <div className="mt-1 text-xs text-neutral-500">
              {(config.momentum_weight * 100).toFixed(0)}% of portfolio
            </div>
          </div>
        </div>
        
        <div>
          <label className="text-xs text-neutral-400 uppercase tracking-wider">
            Market Cap Weight
          </label>
          <div className="mt-2 relative">
            <input
              type="number"
              value={config.market_cap_weight}
              onChange={(e) => handleWeightChange('market_cap_weight', parseFloat(e.target.value))}
              disabled={!editMode}
              step="0.1"
              min="0"
              max="1"
              className="input"
            />
            <div className="mt-1 text-xs text-neutral-500">
              {(config.market_cap_weight * 100).toFixed(0)}% of portfolio
            </div>
          </div>
        </div>
        
        <div>
          <label className="text-xs text-neutral-400 uppercase tracking-wider">
            Risk Parity Weight
          </label>
          <div className="mt-2 relative">
            <input
              type="number"
              value={config.risk_parity_weight}
              onChange={(e) => handleWeightChange('risk_parity_weight', parseFloat(e.target.value))}
              disabled={!editMode}
              step="0.1"
              min="0"
              max="1"
              className="input"
            />
            <div className="mt-1 text-xs text-neutral-500">
              {(config.risk_parity_weight * 100).toFixed(0)}% of portfolio
            </div>
          </div>
        </div>
      </div>
      
      {/* Weight Sum Indicator */}
      <div className="mt-4">
        <div className="flex justify-between items-center text-xs text-neutral-400 mb-1">
          <span>Total Weight</span>
          <span className={isValidWeights ? "text-green-400" : "text-orange-400"}>
            {(weightSum * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-white/10 rounded-full h-2">
          <motion.div 
            className={`h-2 rounded-full ${isValidWeights ? 'bg-green-500' : 'bg-orange-500'}`}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(weightSum * 100, 100)}%` }}
            transition={{ type: "spring", stiffness: 100 }}
          />
        </div>
      </div>
      
      <AnimatePresence>
        {editMode && !isValidWeights && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg"
          >
            <p className="text-red-400 text-sm flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
              Weights must sum to 1.0 (current: {weightSum.toFixed(2)})
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}