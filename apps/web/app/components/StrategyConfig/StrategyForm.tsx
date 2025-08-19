"use client";

import { motion, AnimatePresence } from "framer-motion";
import { StrategyConfig } from "../../utils/api";
import WeightAllocation from "./WeightAllocation";
import RiskSettings from "./RiskSettings";
import { StrategyValidator } from "./ValidationRules";

interface StrategyFormProps {
  config: StrategyConfig;
  onChange: (config: StrategyConfig) => void;
  editMode: boolean;
  saving: boolean;
  onSave: () => void;
  onCancel: () => void;
  onEdit: () => void;
  onRebalance: () => void;
}

export default function StrategyForm({
  config,
  onChange,
  editMode,
  saving,
  onSave,
  onCancel,
  onEdit,
  onRebalance
}: StrategyFormProps) {
  const isValid = StrategyValidator.validateWeights(config);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="card"
    >
      <div className="border-b border-white/10 pb-4 mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold gradient-text">
              Strategy Configuration
            </h2>
            <p className="text-sm text-neutral-400 mt-1">
              Dynamic weighted AutoIndex strategy parameters
            </p>
          </div>
          <div className="flex gap-2">
            {editMode ? (
              <>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onSave}
                  disabled={saving || !isValid}
                  className="btn-primary btn-sm"
                >
                  {saving ? (
                    <span className="flex items-center gap-2">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full"
                      />
                      Saving...
                    </span>
                  ) : (
                    "Save & Recompute"
                  )}
                </motion.button>
                <button
                  onClick={onCancel}
                  className="btn-ghost btn-sm"
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button 
                  onClick={onEdit} 
                  className="btn-secondary btn-sm"
                >
                  Edit Configuration
                </button>
                <motion.button 
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onRebalance} 
                  className="btn-primary btn-sm"
                >
                  Force Rebalance
                </motion.button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* Weight Allocation Section */}
        <WeightAllocation
          config={config}
          onChange={onChange}
          editMode={editMode}
        />

        {/* Risk Settings Section */}
        <RiskSettings
          config={config}
          onChange={onChange}
          editMode={editMode}
        />

        {/* AI Status Section */}
        <AnimatePresence>
          {config.ai_adjusted && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg border border-purple-500/20"
            >
              <div className="flex items-start gap-3">
                <div className="mt-1">
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center"
                  >
                    <span className="text-white text-xs font-bold">AI</span>
                  </motion.div>
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-purple-300 mb-1">
                    AI-Optimized Configuration
                  </h4>
                  <p className="text-sm text-neutral-300">
                    {config.ai_adjustment_reason}
                  </p>
                  <div className="mt-2 flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-full bg-white/10 rounded-full h-2 w-24">
                        <div 
                          className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                          style={{ width: `${(config.ai_confidence_score || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-neutral-400">
                        {((config.ai_confidence_score || 0) * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}