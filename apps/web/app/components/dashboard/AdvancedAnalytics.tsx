"use client";

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { strategyService, portfolioService, benchmarkService } from '../../services/api';

interface AnalyticsData {
  riskMetrics: any;
  performanceComparison: any;
  correlationMatrix: any;
  sectorExposure: any;
  volatilityAnalysis: any;
}

interface AdvancedAnalyticsProps {
  allocations: any[];
  onRefresh?: () => void;
}

export default function AdvancedAnalytics({ allocations, onRefresh }: AdvancedAnalyticsProps) {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<30 | 90 | 365>(90);
  const [activeTab, setActiveTab] = useState<'risk' | 'performance' | 'correlation' | 'sectors'>('risk');

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod, allocations]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      const [riskMetrics, performanceComp] = await Promise.all([
        strategyService.getRiskMetrics(selectedPeriod),
        benchmarkService.comparePerformance()
      ]);

      // Calculate sector exposure from allocations
      const sectorMap = new Map<string, number>();
      allocations.forEach(alloc => {
        const sector = alloc.sector || 'Unknown';
        sectorMap.set(sector, (sectorMap.get(sector) || 0) + alloc.weight);
      });

      const sectorExposure = Array.from(sectorMap.entries()).map(([sector, weight]) => ({
        sector,
        weight: weight * 100,
        count: allocations.filter(a => (a.sector || 'Unknown') === sector).length
      }));

      // Mock correlation matrix (would come from API in real implementation)
      const correlationMatrix = allocations.slice(0, 8).map(asset => ({
        symbol: asset.symbol,
        correlations: allocations.slice(0, 8).map(other => ({
          symbol: other.symbol,
          value: asset.symbol === other.symbol ? 1 : Math.random() * 0.8 + 0.1
        }))
      }));

      setAnalyticsData({
        riskMetrics: riskMetrics.metrics?.[0] || {},
        performanceComparison: performanceComp || { series: [] },
        correlationMatrix,
        sectorExposure,
        volatilityAnalysis: {
          daily: Math.random() * 2 + 0.5,
          weekly: Math.random() * 4 + 1,
          monthly: Math.random() * 8 + 2,
          annual: Math.random() * 25 + 10
        }
      });
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-64 bg-gray-800/50 rounded-xl animate-pulse" />
        <div className="h-64 bg-gray-800/50 rounded-xl animate-pulse" />
      </div>
    );
  }

  const riskData = analyticsData?.riskMetrics ? [
    { metric: 'Sharpe Ratio', value: analyticsData.riskMetrics.sharpe_ratio || 0, target: 1.5 },
    { metric: 'Max Drawdown', value: Math.abs(analyticsData.riskMetrics.max_drawdown || 0) * 100, target: 15 },
    { metric: 'Volatility', value: (analyticsData.riskMetrics.volatility || 0) * 100, target: 20 },
    { metric: 'Beta', value: analyticsData.riskMetrics.beta_sp500 || 0, target: 1.0 },
    { metric: 'Correlation', value: Math.abs(analyticsData.riskMetrics.correlation_sp500 || 0), target: 0.7 }
  ] : [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header Controls */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          {['risk', 'performance', 'correlation', 'sectors'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab
                  ? 'bg-purple-600 text-white shadow-lg'
                  : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
        
        <div className="flex gap-2">
          {[30, 90, 365].map((days) => (
            <button
              key={days}
              onClick={() => setSelectedPeriod(days as any)}
              className={`px-3 py-1 rounded text-sm transition-all ${
                selectedPeriod === days
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {/* Risk Analysis Tab */}
      {activeTab === 'risk' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Risk Metrics Radar Chart */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Risk Profile</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={riskData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <PolarRadiusAxis angle={90} domain={[0, 'dataMax']} tick={false} />
                <Radar
                  name="Current"
                  dataKey="value"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
                <Radar
                  name="Target"
                  dataKey="target"
                  stroke="#10b981"
                  fill="transparent"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                  formatter={(value: any, name) => [
                    typeof value === 'number' ? value.toFixed(2) : value,
                    name
                  ]}
                />
              </RadarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Risk Metrics Table */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-6"
          >
            <h3 className="text-lg font-semibold text-white mb-4">Risk Metrics Detail</h3>
            <div className="space-y-4">
              {riskData.map((item, index) => (
                <div key={item.metric} className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                  <span className="text-gray-300">{item.metric}</span>
                  <div className="text-right">
                    <div className={`font-semibold ${
                      item.metric === 'Max Drawdown' 
                        ? item.value < item.target ? 'text-green-400' : 'text-red-400'
                        : item.value > item.target ? 'text-green-400' : 'text-yellow-400'
                    }`}>
                      {item.value.toFixed(2)}
                      {item.metric.includes('Drawdown') || item.metric.includes('Volatility') ? '%' : ''}
                    </div>
                    <div className="text-xs text-gray-500">
                      Target: {item.target.toFixed(1)}
                      {item.metric.includes('Drawdown') || item.metric.includes('Volatility') ? '%' : ''}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && analyticsData?.performanceComparison && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Performance vs Benchmark</h3>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={analyticsData.performanceComparison.series || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${value.toFixed(1)}%`}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                labelFormatter={(date) => new Date(date).toLocaleDateString()}
                formatter={(value: any) => [`${value.toFixed(2)}%`, '']}
              />
              <Line 
                type="monotone" 
                dataKey="portfolio_return" 
                stroke="#8b5cf6" 
                strokeWidth={3}
                name="Portfolio"
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="benchmark_return" 
                stroke="#ec4899" 
                strokeWidth={2}
                name="S&P 500"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Sector Exposure Tab */}
      {activeTab === 'sectors' && analyticsData?.sectorExposure && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Sector Exposure</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={analyticsData.sectorExposure}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="sector" 
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                formatter={(value: any, name) => [
                  `${value.toFixed(1)}%`,
                  'Weight'
                ]}
                labelFormatter={(sector) => `${sector} Sector`}
              />
              <Bar 
                dataKey="weight" 
                fill="#8b5cf6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Correlation Matrix Tab */}
      {activeTab === 'correlation' && analyticsData?.correlationMatrix && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-6"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Asset Correlation Matrix</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="text-left text-xs text-gray-400 p-2">Asset</th>
                  {analyticsData.correlationMatrix.map((asset: any) => (
                    <th key={asset.symbol} className="text-center text-xs text-gray-400 p-2 min-w-[50px]">
                      {asset.symbol}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {analyticsData.correlationMatrix.map((asset: any) => (
                  <tr key={asset.symbol}>
                    <td className="text-sm font-medium text-white p-2">{asset.symbol}</td>
                    {asset.correlations.map((corr: any) => (
                      <td 
                        key={corr.symbol}
                        className="text-center p-2"
                        style={{
                          backgroundColor: `rgba(139, 92, 246, ${corr.value * 0.5})`,
                          color: corr.value > 0.7 ? 'white' : '#e5e7eb'
                        }}
                      >
                        <span className="text-xs font-mono">
                          {corr.value.toFixed(2)}
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-6"
      >
        <h3 className="text-lg font-semibold text-white mb-4">Portfolio Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => strategyService.rebalance()}
            className="p-4 bg-purple-600/20 hover:bg-purple-600/30 rounded-lg border border-purple-500/30 transition-all group"
          >
            <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">️</div>
            <p className="text-sm font-medium text-white">Rebalance</p>
            <p className="text-xs text-gray-400">Optimize weights</p>
          </button>
          
          <button
            onClick={onRefresh}
            className="p-4 bg-blue-600/20 hover:bg-blue-600/30 rounded-lg border border-blue-500/30 transition-all group"
          >
            <div className="text-2xl mb-2 group-hover:scale-110 transition-transform"></div>
            <p className="text-sm font-medium text-white">Refresh</p>
            <p className="text-xs text-gray-400">Update data</p>
          </button>
          
          <button
            onClick={() => console.log('Export analytics')}
            className="p-4 bg-green-600/20 hover:bg-green-600/30 rounded-lg border border-green-500/30 transition-all group"
          >
            <div className="text-2xl mb-2 group-hover:scale-110 transition-transform"></div>
            <p className="text-sm font-medium text-white">Export</p>
            <p className="text-xs text-gray-400">Download report</p>
          </button>
          
          <button
            onClick={() => window.open('/strategy', '_blank')}
            className="p-4 bg-orange-600/20 hover:bg-orange-600/30 rounded-lg border border-orange-500/30 transition-all group"
          >
            <div className="text-2xl mb-2 group-hover:scale-110 transition-transform">️</div>
            <p className="text-sm font-medium text-white">Configure</p>
            <p className="text-xs text-gray-400">Strategy settings</p>
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}