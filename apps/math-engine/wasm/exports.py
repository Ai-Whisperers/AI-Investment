"""
WebAssembly export definitions for the mathematical engine.
Defines which functions will be available in the compiled WASM module.
"""

# Export configuration for WebAssembly compilation
WASM_EXPORTS = {
    "financial_operations": [
        "simple_returns_series",
        "cumulative_return", 
        "annualized_return",
        "calculate_return_statistics"
    ],
    
    "prediction_algorithms": [
        "linear_trend_prediction",
        "ensemble_trend_prediction", 
        "momentum_prediction",
        "trend_strength"
    ],
    
    "risk_calculations": [
        "calculate_volatility",
        "calculate_sharpe_ratio",
        "calculate_max_drawdown",
        "calculate_correlation"
    ],
    
    "portfolio_optimization": [
        "optimize_portfolio_weights",
        "validate_weights",
        "calculate_portfolio_return"
    ],
    
    "machine_learning": [
        "create_ensemble_predictor",
        "train_bagging_model",
        "predict_ensemble"
    ],
    
    "utilities": [
        "validate_price_series",
        "validate_return_series", 
        "sanitize_price_series",
        "check_numerical_stability"
    ]
}

# JavaScript interface mappings
JS_INTERFACE = {
    "calculateReturns": "simple_returns_series",
    "predictTrend": "ensemble_trend_prediction", 
    "optimizePortfolio": "optimize_portfolio_weights",
    "calculateSharpe": "calculate_sharpe_ratio",
    "calculateVolatility": "calculate_volatility",
    "validatePrices": "validate_price_series",
    "getTrendStrength": "trend_strength",
    "trainEnsemble": "create_ensemble_predictor"
}

# TypeScript type definitions for frontend integration
TYPESCRIPT_DEFINITIONS = '''
// Waardhaven Math Engine TypeScript Definitions
// Auto-generated from Python mathematical engine

export interface PredictionResult {
  prediction: number;
  confidence: number;
}

export interface ReturnStatistics {
  mean: number;
  median: number;
  std: number;
  skewness: number;
  kurtosis: number;
  min: number;
  max: number;
  count: number;
  positive_periods: number;
  negative_periods: number;
}

export interface MathEngineInterface {
  // Financial calculations
  calculateReturns(prices: number[]): number[];
  calculateCumulativeReturn(returns: number[]): number;
  calculateAnnualizedReturn(returns: number[], periodsPerYear?: number): number;
  getReturnStatistics(returns: number[]): ReturnStatistics;
  
  // Prediction methods
  predictTrend(prices: number[], periods?: number): PredictionResult[];
  getTrendStrength(prices: number[]): number;
  predictMomentum(prices: number[], lookback?: number, periods?: number): PredictionResult[];
  
  // Risk calculations
  calculateVolatility(returns: number[], annualize?: boolean): number;
  calculateSharpe(returns: number[], riskFreeRate?: number): number;
  calculateMaxDrawdown(prices: number[]): number;
  calculateCorrelation(series1: number[], series2: number[]): number;
  
  // Portfolio optimization
  optimizePortfolio(expectedReturns: number[], covarianceMatrix: number[][]): number[];
  calculatePortfolioReturn(weights: number[], assetReturns: number[][]): number[];
  validateWeights(weights: number[], tolerance?: number): boolean;
  
  // Machine learning
  trainEnsemble(features: number[][], targets: number[], type?: "bagging" | "forest"): string;
  predictEnsemble(modelId: string, features: number[][]): PredictionResult[];
  
  // Validation utilities  
  validatePrices(prices: number[]): boolean;
  validateReturns(returns: number[]): boolean;
  sanitizePrices(rawPrices: (number | string | null)[]): number[];
}

// Module loading function
export function loadMathEngine(): Promise<MathEngineInterface>;
'''

def generate_wasm_config() -> dict:
    """Generate configuration for WASM compilation."""
    return {
        "module_name": "waardhaven_math_engine",
        "exports": WASM_EXPORTS,
        "js_interface": JS_INTERFACE,
        "typescript_defs": TYPESCRIPT_DEFINITIONS,
        "optimization": {
            "level": "O3",
            "size_optimization": True,
            "memory_limit": "64MB",
            "stack_size": "8MB"
        },
        "features": {
            "simd": True,
            "threads": False,  # Start without threading for simplicity
            "bulk_memory": True,
            "sign_extension": True
        }
    }


def generate_package_json() -> str:
    """Generate package.json for npm distribution of WASM module."""
    return '''{
  "name": "@waardhaven/math-engine",
  "version": "0.1.0",
  "description": "High-performance mathematical engine for investment intelligence",
  "main": "dist/math-engine.js",
  "types": "dist/math-engine.d.ts",
  "files": [
    "dist/",
    "README.md"
  ],
  "scripts": {
    "build": "python build.py",
    "test": "node test/test-wasm.js",
    "benchmark": "node benchmark/bench-wasm.js"
  },
  "keywords": [
    "finance",
    "mathematics", 
    "webassembly",
    "wasm",
    "investment",
    "prediction",
    "portfolio-optimization"
  ],
  "author": "Waardhaven AI",
  "license": "MIT",
  "dependencies": {},
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/Ai-Whisperers/AI-Investment.git",
    "directory": "apps/math-engine"
  },
  "bugs": {
    "url": "https://github.com/Ai-Whisperers/AI-Investment/issues"
  },
  "homepage": "https://github.com/Ai-Whisperers/AI-Investment#readme"
}'''