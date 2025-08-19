"use client";

import { useState, useEffect } from "react";
import { strategyApi, StrategyConfig as IStrategyConfig, RiskMetric } from "../../utils/api";
import BacktestResults from "./BacktestResults";
import StrategyForm from "./StrategyForm";

/**
 * Main StrategyConfig component.
 * Orchestrates strategy configuration, risk metrics display, and API interactions.
 */
export default function StrategyConfig() {
  const [config, setConfig] = useState<IStrategyConfig | null>(null);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [localConfig, setLocalConfig] = useState<IStrategyConfig | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [configRes, metricsRes] = await Promise.all([
        strategyApi.getConfig(),
        strategyApi.getRiskMetrics()
      ]);
      
      setConfig(configRes.data);
      setLocalConfig(configRes.data);
      setRiskMetrics(metricsRes.data.metrics);
    } catch (error) {
      console.error("Failed to load strategy data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!localConfig) return;
    
    setSaving(true);
    try {
      await strategyApi.updateConfig(localConfig, true);
      setConfig(localConfig);
      setEditMode(false);
      
      // Reload metrics after recomputation
      setTimeout(async () => {
        const metricsRes = await strategyApi.getRiskMetrics();
        setRiskMetrics(metricsRes.data.metrics);
      }, 2000);
    } catch (error) {
      console.error("Failed to save configuration:", error);
      alert("Failed to save configuration. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleRebalance = async () => {
    try {
      await strategyApi.triggerRebalance(true);
      alert("Rebalancing triggered successfully");
      loadData();
    } catch (error) {
      console.error("Failed to trigger rebalance:", error);
      alert("Failed to trigger rebalance. Please try again.");
    }
  };

  const handleEdit = () => {
    setEditMode(true);
  };

  const handleCancel = () => {
    setLocalConfig(config);
    setEditMode(false);
  };

  const handleConfigChange = (newConfig: IStrategyConfig) => {
    setLocalConfig(newConfig);
  };

  if (loading) {
    return (
      <div className="card">
        <div className="h-96 skeleton rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Risk Metrics Summary */}
      <BacktestResults metrics={riskMetrics} />

      {/* Strategy Configuration Form */}
      {localConfig && (
        <StrategyForm
          config={localConfig}
          onChange={handleConfigChange}
          editMode={editMode}
          saving={saving}
          onSave={handleSave}
          onCancel={handleCancel}
          onEdit={handleEdit}
          onRebalance={handleRebalance}
        />
      )}
    </div>
  );
}