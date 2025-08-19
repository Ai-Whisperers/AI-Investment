"use client";

import { StrategyConfig } from "../../utils/api";

interface RiskSettingsProps {
  config: StrategyConfig;
  onChange: (config: StrategyConfig) => void;
  editMode: boolean;
}

export default function RiskSettings({ config, onChange, editMode }: RiskSettingsProps) {
  const handleChange = (field: keyof StrategyConfig, value: number | string) => {
    onChange({
      ...config,
      [field]: value
    });
  };

  return (
    <div className="space-y-4">
      {/* Risk Parameters */}
      <div className="bg-white/5 rounded-lg p-4 border border-white/10">
        <h3 className="font-medium text-neutral-200 mb-4 flex items-center gap-2">
          <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
          Risk Parameters
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-neutral-400 uppercase tracking-wider">
              Min Price ($)
            </label>
            <input
              type="number"
              value={config.min_price_threshold}
              onChange={(e) => handleChange('min_price_threshold', parseFloat(e.target.value))}
              disabled={!editMode}
              step="0.1"
              min="0.01"
              className="input mt-2"
            />
          </div>
          
          <div>
            <label className="text-xs text-neutral-400 uppercase tracking-wider">
              Max Daily Return
            </label>
            <div className="relative">
              <input
                type="number"
                value={config.max_daily_return}
                onChange={(e) => handleChange('max_daily_return', parseFloat(e.target.value))}
                disabled={!editMode}
                step="0.1"
                className="input mt-2"
              />
              <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-500 text-sm mt-1">
                {(config.max_daily_return * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          
          <div>
            <label className="text-xs text-neutral-400 uppercase tracking-wider">
              Min Daily Return
            </label>
            <div className="relative">
              <input
                type="number"
                value={config.min_daily_return}
                onChange={(e) => handleChange('min_daily_return', parseFloat(e.target.value))}
                disabled={!editMode}
                step="0.1"
                className="input mt-2"
              />
              <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-500 text-sm mt-1">
                {(config.min_daily_return * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          
          <div>
            <label className="text-xs text-neutral-400 uppercase tracking-wider">
              Drop Threshold
            </label>
            <div className="relative">
              <input
                type="number"
                value={config.daily_drop_threshold}
                onChange={(e) => handleChange('daily_drop_threshold', parseFloat(e.target.value))}
                disabled={!editMode}
                step="0.01"
                className="input mt-2"
              />
              <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-500 text-sm mt-1">
                {(config.daily_drop_threshold * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Rebalancing Settings */}
      <div className="bg-white/5 rounded-lg p-4 border border-white/10">
        <h3 className="font-medium text-neutral-200 mb-4 flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          Rebalancing Settings
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-neutral-400 uppercase tracking-wider">
              Frequency
            </label>
            <select
              value={config.rebalance_frequency}
              onChange={(e) => handleChange('rebalance_frequency', e.target.value)}
              disabled={!editMode}
              className="input mt-2"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          
          <div>
            <label className="text-xs text-neutral-400 uppercase tracking-wider">
              Last Rebalance
            </label>
            <div className="input mt-2 bg-white/[0.05] cursor-not-allowed">
              {config.last_rebalance 
                ? new Date(config.last_rebalance).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })
                : "Never"
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}