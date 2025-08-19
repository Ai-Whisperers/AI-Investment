"use client";

import { motion } from "framer-motion";
import { RiskMetric } from "../../utils/api";

interface BacktestResultsProps {
  metrics: RiskMetric[];
}

export default function BacktestResults({ metrics }: BacktestResultsProps) {
  if (!metrics || metrics.length === 0) {
    return null;
  }

  const latestMetric = metrics[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      <div className="border-b border-white/10 pb-4 mb-6">
        <h2 className="text-xl font-semibold gradient-text">Risk Analytics</h2>
        <p className="text-sm text-neutral-400 mt-1">
          Real-time risk metrics and performance indicators
        </p>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Sharpe Ratio"
          value={latestMetric.sharpe_ratio.toFixed(2)}
          description="Risk-adjusted return"
          delay={0.1}
          colorClass="gradient-text"
        />
        
        <MetricCard
          label="Sortino Ratio"
          value={latestMetric.sortino_ratio.toFixed(2)}
          description="Downside risk-adjusted"
          delay={0.2}
          colorClass="gradient-text"
        />
        
        <MetricCard
          label="Max Drawdown"
          value={`${(latestMetric.max_drawdown * 100).toFixed(1)}%`}
          description="Peak to trough"
          delay={0.3}
          colorClass="text-orange-400"
        />
        
        <MetricCard
          label="Current Drawdown"
          value={`${(latestMetric.current_drawdown * 100).toFixed(1)}%`}
          description="From recent peak"
          delay={0.4}
          colorClass={latestMetric.current_drawdown < -0.05 ? 'text-red-400' : 'text-green-400'}
        />
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
        <MetricCard
          label="Volatility"
          value={`${(latestMetric.volatility * 100).toFixed(1)}%`}
          description="Annualized std dev"
          delay={0.5}
          colorClass="text-neutral-300"
          small
        />
        
        <MetricCard
          label="Beta (S&P 500)"
          value={latestMetric.beta_sp500.toFixed(2)}
          description="Market correlation"
          delay={0.6}
          colorClass="text-neutral-300"
          small
        />
        
        <MetricCard
          label="Correlation"
          value={latestMetric.correlation_sp500.toFixed(2)}
          description="S&P 500 correlation"
          delay={0.7}
          colorClass="text-neutral-300"
          small
        />
      </div>

      {/* Returns Section */}
      {(latestMetric.total_return !== undefined || latestMetric.annualized_return !== undefined) && (
        <div className="mt-6 pt-6 border-t border-white/10">
          <h3 className="text-sm font-medium text-neutral-400 mb-3">Returns</h3>
          <div className="grid grid-cols-2 gap-4">
            {latestMetric.total_return !== undefined && (
              <div className="bg-white/5 rounded-lg p-3 border border-white/10">
                <p className="text-xs text-neutral-400">Total Return</p>
                <p className={`text-xl font-bold ${latestMetric.total_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {latestMetric.total_return >= 0 ? '+' : ''}{latestMetric.total_return.toFixed(2)}%
                </p>
              </div>
            )}
            
            {latestMetric.annualized_return !== undefined && (
              <div className="bg-white/5 rounded-lg p-3 border border-white/10">
                <p className="text-xs text-neutral-400">Annualized Return</p>
                <p className={`text-xl font-bold ${latestMetric.annualized_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {latestMetric.annualized_return >= 0 ? '+' : ''}{latestMetric.annualized_return.toFixed(2)}%
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  description: string;
  delay: number;
  colorClass: string;
  small?: boolean;
}

function MetricCard({ label, value, description, delay, colorClass, small = false }: MetricCardProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
      className="bg-white/5 rounded-lg p-4 border border-white/10 hover:bg-white/[0.08] transition-all"
    >
      <p className="text-xs text-neutral-400 mb-1">{label}</p>
      <p className={`${small ? 'text-xl' : 'text-2xl'} font-bold ${colorClass}`}>
        {value}
      </p>
      <p className="text-xs text-neutral-500 mt-1">{description}</p>
    </motion.div>
  );
}