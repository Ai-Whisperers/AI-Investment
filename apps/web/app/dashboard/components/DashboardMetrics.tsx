import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { type RiskMetric, portfolioService } from '../../services/api';

type SeriesPoint = { date: string; value: number };

interface DashboardMetricsProps {
  indexSeries: SeriesPoint[];
  spSeries: SeriesPoint[];
  riskMetrics: RiskMetric | null;
  simResult: { amount_final: number; roi_pct: number; currency: string } | null;
  currency: string;
}

export const DashboardMetrics: React.FC<DashboardMetricsProps> = ({
  indexSeries,
  spSeries,
  riskMetrics,
  simResult,
  currency
}) => {
  const [indexReturns, setIndexReturns] = useState({ daily: 0, monthly: 0, yearly: 0, total: 0 });
  const [spReturns, setSpReturns] = useState({ daily: 0, monthly: 0, yearly: 0, total: 0 });
  const [loading, setLoading] = useState(false);

  const calculateReturnsWithAPI = async (series: SeriesPoint[]) => {
    if (series.length < 2) return { daily: 0, monthly: 0, yearly: 0, total: 0 };
    
    try {
      const latest = series[series.length - 1];
      const yesterday = series[series.length - 2];
      const monthAgo = series.find((_, i) => i === Math.max(0, series.length - 30));
      const yearAgo = series.find((_, i) => i === Math.max(0, series.length - 252));
      const first = series[0];
      
      // Use API for total return calculation
      const total = await portfolioService.calculateTotalReturn(first.value, latest.value);
      
      // Calculate period returns using API
      const daily = yesterday ? await portfolioService.calculateTotalReturn(yesterday.value, latest.value) : 0;
      const monthly = monthAgo ? await portfolioService.calculateTotalReturn(monthAgo.value, latest.value) : 0;
      const yearly = yearAgo ? await portfolioService.calculateTotalReturn(yearAgo.value, latest.value) : 0;
      
      return { daily, monthly, yearly, total };
    } catch (error) {
      console.error('Error calculating returns:', error);
      // Fallback to local calculation if API fails
      const latest = series[series.length - 1];
      const yesterday = series[series.length - 2];
      const monthAgo = series.find((_, i) => i === Math.max(0, series.length - 30));
      const yearAgo = series.find((_, i) => i === Math.max(0, series.length - 252));
      const first = series[0];
      
      return {
        daily: yesterday ? ((latest.value - yesterday.value) / yesterday.value) * 100 : 0,
        monthly: monthAgo ? ((latest.value - monthAgo.value) / monthAgo.value) * 100 : 0,
        yearly: yearAgo ? ((latest.value - yearAgo.value) / yearAgo.value) * 100 : 0,
        total: ((latest.value - first.value) / first.value) * 100
      };
    }
  };

  // Calculate returns when series data changes
  useEffect(() => {
    const updateReturns = async () => {
      if (indexSeries.length > 0 || spSeries.length > 0) {
        setLoading(true);
        try {
          const [indexReturnsCalc, spReturnsCalc] = await Promise.all([
            calculateReturnsWithAPI(indexSeries),
            calculateReturnsWithAPI(spSeries)
          ]);
          setIndexReturns(indexReturnsCalc);
          setSpReturns(spReturnsCalc);
        } catch (error) {
          console.error('Error updating returns:', error);
        } finally {
          setLoading(false);
        }
      }
    };

    updateReturns();
  }, [indexSeries, spSeries]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
      >
        <h3 className="text-sm font-medium text-white/60 mb-2">Total Return</h3>
        <p className={`text-2xl font-bold ${indexReturns.total >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {indexReturns.total >= 0 ? '+' : ''}{indexReturns.total.toFixed(2)}%
        </p>
        <p className="text-xs text-white/40 mt-1">
          vs S&P 500: {(indexReturns.total - spReturns.total).toFixed(2)}%
        </p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
      >
        <h3 className="text-sm font-medium text-white/60 mb-2">Sharpe Ratio</h3>
        <p className="text-2xl font-bold text-purple-400">
          {riskMetrics?.sharpe_ratio?.toFixed(2) || 'N/A'}
        </p>
        <p className="text-xs text-white/40 mt-1">Risk-adjusted returns</p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
      >
        <h3 className="text-sm font-medium text-white/60 mb-2">Max Drawdown</h3>
        <p className="text-2xl font-bold text-orange-400">
          {riskMetrics?.max_drawdown ? `${(riskMetrics.max_drawdown * 100).toFixed(2)}%` : 'N/A'}
        </p>
        <p className="text-xs text-white/40 mt-1">Maximum loss from peak</p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
      >
        <h3 className="text-sm font-medium text-white/60 mb-2">Volatility</h3>
        <p className="text-2xl font-bold text-blue-400">
          {riskMetrics?.volatility ? `${(riskMetrics.volatility * 100).toFixed(2)}%` : 'N/A'}
        </p>
        <p className="text-xs text-white/40 mt-1">Annual standard deviation</p>
      </motion.div>

      {simResult && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="col-span-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-lg p-6 border border-purple-500/30"
        >
          <h3 className="text-lg font-medium text-white mb-3">Simulation Results</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-white/60">Final Amount</p>
              <p className="text-xl font-bold text-white">
                {new Intl.NumberFormat('en-US', { 
                  style: 'currency', 
                  currency: simResult.currency 
                }).format(simResult.amount_final)}
              </p>
            </div>
            <div>
              <p className="text-sm text-white/60">Return</p>
              <p className={`text-xl font-bold ${simResult.roi_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {simResult.roi_pct >= 0 ? '+' : ''}{simResult.roi_pct.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-white/60">Currency</p>
              <p className="text-xl font-bold text-white">{simResult.currency}</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};