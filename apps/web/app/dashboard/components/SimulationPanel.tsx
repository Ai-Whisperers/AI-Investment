import React from 'react';
import { motion } from 'framer-motion';

interface SimulationPanelProps {
  amount: number;
  setAmount: (amount: number) => void;
  currency: string;
  setCurrency: (currency: string) => void;
  startDate: string;
  setStartDate: (date: string) => void;
  currencies: {[key: string]: string};
  simulating: boolean;
  runSimulation: () => void;
}

export const SimulationPanel: React.FC<SimulationPanelProps> = ({
  amount,
  setAmount,
  currency,
  setCurrency,
  startDate,
  setStartDate,
  currencies,
  simulating,
  runSimulation
}) => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-white/10"
    >
      <h3 className="text-lg font-semibold mb-4 text-white">Investment Simulation</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-white/60 mb-1">
            Investment Amount
          </label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="10000"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-white/60 mb-1">
            Currency
          </label>
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            {Object.entries(currencies).map(([code, name]) => (
              <option key={code} value={code} className="bg-gray-900">
                {code} - {name}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-white/60 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        
        <div className="flex items-end">
          <button
            onClick={runSimulation}
            disabled={simulating || !amount || !startDate}
            className={`w-full px-4 py-2 rounded-md font-medium transition-all ${
              simulating || !amount || !startDate
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 transform hover:scale-105'
            }`}
          >
            {simulating ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Simulating...
              </span>
            ) : (
              'Run Simulation'
            )}
          </button>
        </div>
      </div>
      
      <div className="mt-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
        <p className="text-sm text-white/60">
          This simulation calculates how your investment would have performed from the selected start date to today, 
          based on the current portfolio allocation strategy.
        </p>
      </div>
    </motion.div>
  );
};