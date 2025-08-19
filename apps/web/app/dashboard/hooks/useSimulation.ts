import { useState, useCallback } from 'react';
import { portfolioService } from '../../services/api';

interface SimulationResult {
  amount_final: number;
  roi_pct: number;
  currency: string;
}

export const useSimulation = () => {
  const [amount, setAmount] = useState(10000);
  const [currency, setCurrency] = useState("USD");
  const [startDate, setStartDate] = useState<string>("2019-01-01");
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simulating, setSimulating] = useState(false);

  const runSimulation = useCallback(async () => {
    setSimulating(true);
    try {
      const result = await portfolioService.runSimulation({ 
        amount, 
        startDate,
        currency 
      });
      setSimResult({ 
        amount_final: result.end_value, 
        roi_pct: ((result.end_value - amount) / amount) * 100,
        currency: result.currency || currency
      });
    } catch (error) {
      console.error('Simulation failed:', error);
      alert('Failed to run simulation. Please try again.');
    } finally {
      setSimulating(false);
    }
  }, [amount, startDate, currency]);

  return {
    amount,
    setAmount,
    currency,
    setCurrency,
    startDate,
    setStartDate,
    simResult,
    simulating,
    runSimulation
  };
};