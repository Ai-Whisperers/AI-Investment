import React from 'react';
import { formatTooltipValue } from './chartConfig';

interface ChartTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

export const ChartTooltip: React.FC<ChartTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  return (
    <div className="bg-gray-900/95 p-3 rounded-lg border border-white/10 shadow-xl">
      <p className="text-white/80 text-sm mb-2 font-medium">
        {label && formatDate(label)}
      </p>
      <div className="space-y-1">
        {payload.map((entry, index) => {
          if (entry.value === null || entry.value === undefined) return null;
          
          return (
            <div key={`item-${index}`} className="flex items-center gap-2">
              <div 
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-white/60 text-xs">{entry.name}:</span>
              <span className="text-white font-medium text-sm">
                {formatTooltipValue(entry.value)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};