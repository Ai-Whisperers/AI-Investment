/**
 * Validation rules and utilities for strategy configuration.
 * Handles weight validation, risk parameter validation, and configuration constraints.
 */

import { StrategyConfig } from "../../utils/api";

export class StrategyValidator {
  /**
   * Validate that strategy weights sum to 1.0
   */
  static validateWeights(config: StrategyConfig): boolean {
    const total = config.momentum_weight + config.market_cap_weight + config.risk_parity_weight;
    return Math.abs(total - 1.0) < 0.001;
  }

  /**
   * Get the current weight sum
   */
  static getWeightSum(config: StrategyConfig): number {
    return config.momentum_weight + config.market_cap_weight + config.risk_parity_weight;
  }

  /**
   * Validate risk parameters are within acceptable ranges
   */
  static validateRiskParameters(config: StrategyConfig): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (config.min_price_threshold < 0.01) {
      errors.push("Minimum price threshold must be at least $0.01");
    }

    if (config.max_daily_return <= config.min_daily_return) {
      errors.push("Maximum daily return must be greater than minimum daily return");
    }

    if (config.daily_drop_threshold <= 0 || config.daily_drop_threshold > 1) {
      errors.push("Daily drop threshold must be between 0 and 1");
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate the entire configuration
   */
  static validateConfig(config: StrategyConfig): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    // Check weights
    if (!this.validateWeights(config)) {
      errors.push(`Weights must sum to 1.0 (current: ${this.getWeightSum(config).toFixed(3)})`);
    }

    // Check individual weight ranges
    if (config.momentum_weight < 0 || config.momentum_weight > 1) {
      errors.push("Momentum weight must be between 0 and 1");
    }

    if (config.market_cap_weight < 0 || config.market_cap_weight > 1) {
      errors.push("Market cap weight must be between 0 and 1");
    }

    if (config.risk_parity_weight < 0 || config.risk_parity_weight > 1) {
      errors.push("Risk parity weight must be between 0 and 1");
    }

    // Check risk parameters
    const riskValidation = this.validateRiskParameters(config);
    errors.push(...riskValidation.errors);

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Auto-normalize weights to sum to 1.0
   */
  static normalizeWeights(config: StrategyConfig): StrategyConfig {
    const total = this.getWeightSum(config);
    
    if (total === 0) {
      // Equal distribution if all weights are 0
      return {
        ...config,
        momentum_weight: 1/3,
        market_cap_weight: 1/3,
        risk_parity_weight: 1/3
      };
    }

    // Normalize to sum to 1
    return {
      ...config,
      momentum_weight: config.momentum_weight / total,
      market_cap_weight: config.market_cap_weight / total,
      risk_parity_weight: config.risk_parity_weight / total
    };
  }
}