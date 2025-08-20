// Portfolio API service

import { ApiService } from './base';
import {
  SeriesPoint,
  AllocationItem,
  SimulationRequest,
  SimulationResult,
  RiskMetric,
} from '../../types/portfolio';
import { CurrencyMap } from '../../types/api';

interface IndexHistoryResponse {
  series: SeriesPoint[];
}

interface IndexCurrentResponse {
  date: string;
  allocations: AllocationItem[];
}

interface SimulationResponse extends SimulationResult {
  start_date: string;
  end_date: string;
  start_value: number;
  end_value: number;
  amount_initial: number;
  series: SeriesPoint[];
}

interface RiskMetricsResponse {
  metrics: RiskMetric[];
}

// Calculation API types
interface CalculateReturnsRequest {
  values: number[];
}

interface CalculateReturnsResponse {
  returns: number[];
}

interface CalculateTotalReturnRequest {
  start_value: number;
  end_value: number;
}

interface CalculateTotalReturnResponse {
  total_return: number;
}

interface CalculateAnnualizedReturnRequest {
  total_return: number;
  period_in_days: number;
}

interface CalculateAnnualizedReturnResponse {
  annualized_return: number;
}

interface CalculateVolatilityRequest {
  returns: number[];
}

interface CalculateVolatilityResponse {
  volatility: number;
}

interface CalculateSharpeRatioRequest {
  annualized_return: number;
  volatility: number;
  risk_free_rate?: number;
}

interface CalculateSharpeRatioResponse {
  sharpe_ratio: number;
}

interface CalculateMaxDrawdownRequest {
  values: number[];
}

interface CalculateMaxDrawdownResponse {
  max_drawdown: number;
  current_drawdown: number;
}

interface CalculatePortfolioMetricsRequest {
  values: number[];
  period_in_days: number;
}

interface PerformanceMetrics {
  total_return: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  current_drawdown: number;
}

interface CalculatePortfolioMetricsResponse {
  metrics: PerformanceMetrics;
}

class PortfolioService extends ApiService {
  async getIndexHistory(): Promise<IndexHistoryResponse> {
    return this.get<IndexHistoryResponse>('/api/v1/index/history');
  }

  async getCurrentAllocations(): Promise<IndexCurrentResponse> {
    return this.get<IndexCurrentResponse>('/api/v1/index/current');
  }

  async getAssetHistory(symbol: string): Promise<IndexHistoryResponse> {
    return this.get<IndexHistoryResponse>(`/api/v1/index/assets/${symbol}/history`);
  }

  async runSimulation(request: SimulationRequest): Promise<SimulationResponse> {
    const payload = {
      amount: request.amount,
      start_date: request.startDate,
      currency: request.currency,
    };
    return this.post<SimulationResponse>('/api/v1/index/simulate', payload);
  }

  async getCurrencies(): Promise<CurrencyMap> {
    return this.get<CurrencyMap>('/api/v1/index/currencies');
  }

  async getRiskMetrics(): Promise<RiskMetricsResponse> {
    return this.get<RiskMetricsResponse>('/api/v1/strategy/risk-metrics');
  }

  async refreshPortfolio(): Promise<any> {
    return this.post('/api/v1/manual/trigger-refresh');
  }

  // Calculation API methods
  async calculateReturns(values: number[]): Promise<number[]> {
    const response = await this.post<CalculateReturnsResponse>(
      '/api/v1/portfolio/calculations/returns',
      { values }
    );
    return response.returns;
  }

  async calculateTotalReturn(startValue: number, endValue: number): Promise<number> {
    const response = await this.post<CalculateTotalReturnResponse>(
      '/api/v1/portfolio/calculations/total-return',
      { start_value: startValue, end_value: endValue }
    );
    return response.total_return;
  }

  async calculateAnnualizedReturn(totalReturn: number, periodInDays: number): Promise<number> {
    const response = await this.post<CalculateAnnualizedReturnResponse>(
      '/api/v1/portfolio/calculations/annualized-return',
      { total_return: totalReturn, period_in_days: periodInDays }
    );
    return response.annualized_return;
  }

  async calculateVolatility(returns: number[]): Promise<number> {
    const response = await this.post<CalculateVolatilityResponse>(
      '/api/v1/portfolio/calculations/volatility',
      { returns }
    );
    return response.volatility;
  }

  async calculateSharpeRatio(
    annualizedReturn: number,
    volatility: number,
    riskFreeRate: number = 2.0
  ): Promise<number> {
    const response = await this.post<CalculateSharpeRatioResponse>(
      '/api/v1/portfolio/calculations/sharpe-ratio',
      { 
        annualized_return: annualizedReturn, 
        volatility, 
        risk_free_rate: riskFreeRate 
      }
    );
    return response.sharpe_ratio;
  }

  async calculateMaxDrawdown(values: number[]): Promise<{ maxDrawdown: number; currentDrawdown: number }> {
    const response = await this.post<CalculateMaxDrawdownResponse>(
      '/api/v1/portfolio/calculations/max-drawdown',
      { values }
    );
    return {
      maxDrawdown: response.max_drawdown,
      currentDrawdown: response.current_drawdown
    };
  }

  async calculatePortfolioMetrics(
    values: number[],
    periodInDays: number
  ): Promise<PerformanceMetrics> {
    const response = await this.post<CalculatePortfolioMetricsResponse>(
      '/api/v1/portfolio/calculations/portfolio-metrics',
      { values, period_in_days: periodInDays }
    );
    return response.metrics;
  }
}

export const portfolioService = new PortfolioService();

// Export types
export type { PerformanceMetrics };