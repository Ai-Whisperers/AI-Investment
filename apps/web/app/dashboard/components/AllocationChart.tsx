import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { motion } from 'framer-motion';

type AllocationItem = { symbol: string; weight: number; name?: string; sector?: string };

interface AllocationChartProps {
  allocations: AllocationItem[];
  hoveredAsset: string | null;
  setHoveredAsset: (asset: string | null) => void;
}

const COLORS = ['#8b5cf6', '#ec4899', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#a855f7'];

export const AllocationChart: React.FC<AllocationChartProps> = ({
  allocations,
  hoveredAsset,
  setHoveredAsset
}) => {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-gray-900/95 p-3 rounded-lg border border-white/10">
          <p className="text-white font-medium">{data.payload.symbol}</p>
          {data.payload.name && (
            <p className="text-white/60 text-sm">{data.payload.name}</p>
          )}
          <p className="text-purple-400 font-bold">{(data.value * 100).toFixed(2)}%</p>
          {data.payload.sector && (
            <p className="text-white/40 text-xs mt-1">Sector: {data.payload.sector}</p>
          )}
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = (entry: AllocationItem) => {
    if (entry.weight < 0.03) return null; // Don't show labels for allocations < 3%
    return `${entry.symbol} ${(entry.weight * 100).toFixed(1)}%`;
  };

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
    >
      <h3 className="text-lg font-semibold mb-4 text-white">Current Allocation</h3>
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={allocations}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={120}
            fill="#8884d8"
            dataKey="weight"
            onMouseEnter={(data) => setHoveredAsset(data.symbol)}
            onMouseLeave={() => setHoveredAsset(null)}
          >
            {allocations.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={COLORS[index % COLORS.length]}
                style={{
                  filter: hoveredAsset && hoveredAsset !== entry.symbol ? 'opacity(0.3)' : 'none',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease'
                }}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="bottom" 
            height={36}
            formatter={(value: any, entry: any) => (
              <span style={{ color: 'rgba(255,255,255,0.8)' }}>
                {entry.payload.symbol}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
      
      <div className="mt-4 space-y-2">
        {allocations.slice(0, 5).map((allocation, index) => (
          <div 
            key={allocation.symbol}
            className="flex items-center justify-between p-2 rounded hover:bg-white/5 transition-colors cursor-pointer"
            onMouseEnter={() => setHoveredAsset(allocation.symbol)}
            onMouseLeave={() => setHoveredAsset(null)}
          >
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <span className="text-white/80">{allocation.symbol}</span>
              {allocation.name && (
                <span className="text-white/40 text-sm">({allocation.name})</span>
              )}
            </div>
            <span className="text-white/60 font-medium">
              {(allocation.weight * 100).toFixed(2)}%
            </span>
          </div>
        ))}
        {allocations.length > 5 && (
          <p className="text-white/40 text-sm text-center mt-2">
            +{allocations.length - 5} more assets
          </p>
        )}
      </div>
    </motion.div>
  );
};