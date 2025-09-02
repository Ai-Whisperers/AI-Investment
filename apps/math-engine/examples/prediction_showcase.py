#!/usr/bin/env python3
"""
Waardhaven Mathematical Engine - Prediction Showcase
Demonstrates the pure computational prediction capabilities.
"""

import sys
from pathlib import Path

# Add math engine to path
engine_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(engine_path))

from core.types import Price, PriceSeries
from financial.returns import simple_returns_series, calculate_return_statistics
from prediction.trend_analysis import (
    linear_trend_prediction,
    ensemble_trend_prediction,
    trend_strength,
    momentum_prediction
)


def demo_basic_calculations():
    """Demonstrate basic financial calculations."""
    print("\n" + "="*60)
    print("🧮 BASIC FINANCIAL CALCULATIONS")
    print("="*60)
    
    # Sample price data (simulates AAPL-like movement)
    prices = [
        150.0, 152.5, 151.0, 154.0, 156.5, 155.0, 158.0, 160.0, 
        162.5, 159.0, 161.0, 165.0, 163.0, 167.0, 170.0
    ]
    
    print(f"📊 Price Series: {len(prices)} observations")
    print(f"   Range: ${min(prices):.2f} - ${max(prices):.2f}")
    
    # Calculate returns
    returns = simple_returns_series(prices)
    print(f"\n📈 Return Calculations:")
    print(f"   Return periods: {len(returns)}")
    print(f"   Mean return: {np.mean(returns):.4f} ({np.mean(returns)*252:.2%} annualized)")
    
    # Return statistics
    stats = calculate_return_statistics(returns)
    print(f"\n📊 Return Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.4f}")
        else:
            print(f"   {key}: {value}")


def demo_trend_analysis():
    """Demonstrate trend analysis capabilities."""
    print("\n" + "="*60)
    print("🔍 TREND ANALYSIS & PREDICTION")  
    print("="*60)
    
    # Trending price series
    trending_prices = [
        100.0, 102.0, 101.5, 104.0, 106.0, 105.5, 108.0, 110.0,
        112.0, 111.0, 114.0, 116.5, 115.0, 118.0, 120.5, 119.0,
        122.0, 125.0, 124.0, 127.0, 129.5
    ]
    
    print(f"📊 Trending Series: {len(trending_prices)} prices")
    print(f"   Start: ${trending_prices[0]:.2f}")
    print(f"   End: ${trending_prices[-1]:.2f}")
    print(f"   Total Return: {(trending_prices[-1]/trending_prices[0]-1):.2%}")
    
    # Analyze trend strength
    strength = trend_strength(trending_prices)
    print(f"\n🎯 Trend Strength: {strength:.3f} ({strength*100:.1f}%)")
    
    # Linear prediction
    linear_pred = linear_trend_prediction(trending_prices, 3)
    print(f"\n📈 Linear Trend Predictions (3 periods):")
    for i, (pred, conf) in enumerate(linear_pred, 1):
        print(f"   Period {i}: ${pred:.2f} (confidence: {conf:.3f})")
    
    # Ensemble prediction
    ensemble_pred = ensemble_trend_prediction(trending_prices, 3)
    print(f"\n🎯 Ensemble Predictions (3 periods):")
    for i, (pred, conf) in enumerate(ensemble_pred, 1):
        print(f"   Period {i}: ${pred:.2f} (confidence: {conf:.3f})")
    
    # Momentum prediction
    momentum_pred = momentum_prediction(trending_prices, lookback=10, prediction_periods=3)
    print(f"\n⚡ Momentum Predictions (3 periods):")
    for i, (pred, conf) in enumerate(momentum_pred, 1):
        print(f"   Period {i}: ${pred:.2f} (confidence: {conf:.3f})")


def demo_volatility_prediction():
    """Demonstrate volatility analysis."""
    print("\n" + "="*60)
    print("📊 VOLATILITY ANALYSIS")
    print("="*60)
    
    # Volatile price series
    volatile_prices = [
        100.0, 105.0, 98.0, 107.0, 102.0, 96.0, 110.0, 103.0,
        95.0, 112.0, 106.0, 92.0, 115.0, 108.0, 89.0, 118.0,
        111.0, 87.0, 121.0, 114.0, 85.0
    ]
    
    print(f"📊 Volatile Series: {len(volatile_prices)} prices")
    print(f"   Range: ${min(volatile_prices):.2f} - ${max(volatile_prices):.2f}")
    
    # Calculate returns and statistics
    returns = simple_returns_series(volatile_prices)
    stats = calculate_return_statistics(returns)
    
    print(f"\n📈 Volatility Metrics:")
    print(f"   Standard Deviation: {stats['std']:.4f}")
    print(f"   Annualized Volatility: {stats['std'] * np.sqrt(252):.2%}")
    print(f"   Skewness: {stats['skewness']:.4f}")
    print(f"   Kurtosis: {stats['kurtosis']:.4f}")
    
    # Trend strength in volatile environment
    volatile_strength = trend_strength(volatile_prices)
    print(f"   Trend Strength: {volatile_strength:.3f} (low due to volatility)")


def demo_prediction_comparison():
    """Compare different prediction methods."""
    print("\n" + "="*60)
    print("🔬 PREDICTION METHOD COMPARISON")
    print("="*60)
    
    # Real-world like price series (mixed trends)
    mixed_prices = [
        100.0, 101.0, 102.5, 101.8, 103.2, 104.1, 103.7, 105.0,
        106.2, 105.5, 107.0, 108.3, 107.9, 109.5, 111.0, 110.2,
        112.0, 113.5, 112.8, 114.5, 116.0
    ]
    
    print(f"📊 Mixed Trend Series: {len(mixed_prices)} prices")
    
    methods = {
        "Linear Trend": linear_trend_prediction(mixed_prices, 1),
        "Ensemble": ensemble_trend_prediction(mixed_prices, 1), 
        "Momentum": momentum_prediction(mixed_prices, lookback=10, prediction_periods=1)
    }
    
    print(f"\n🎯 1-Period Predictions:")
    for method_name, predictions in methods.items():
        if predictions:
            pred, conf = predictions[0]
            print(f"   {method_name:12}: ${pred:.2f} (confidence: {conf:.3f})")
    
    # Show actual vs predicted (for demonstration)
    actual_next = 118.0  # Simulated actual next price
    print(f"\n✅ Simulated Actual: ${actual_next:.2f}")
    
    print(f"\n📊 Prediction Accuracy:")
    for method_name, predictions in methods.items():
        if predictions:
            pred, conf = predictions[0]
            error = abs(pred - actual_next)
            accuracy = max(0, 1.0 - (error / actual_next))
            print(f"   {method_name:12}: {accuracy:.2%} accuracy (${error:.2f} error)")


def benchmark_performance():
    """Benchmark mathematical engine performance."""
    print("\n" + "="*60)
    print("⚡ PERFORMANCE BENCHMARKS")
    print("="*60)
    
    import time
    
    # Large dataset for performance testing
    large_prices = [100.0 + i*0.1 + np.sin(i*0.1)*5 for i in range(10000)]
    
    print(f"📊 Large Dataset: {len(large_prices):,} prices")
    
    # Benchmark return calculations
    start = time.time()
    returns = simple_returns_series(large_prices)
    calc_time = time.time() - start
    
    print(f"\n⚡ Performance Results:")
    print(f"   Return Calculation: {calc_time*1000:.2f}ms for {len(large_prices):,} prices")
    print(f"   Throughput: {len(large_prices)/calc_time:,.0f} prices/second")
    
    # Benchmark predictions
    start = time.time()
    prediction = ensemble_trend_prediction(large_prices[-100:], 1)  # Use last 100 prices
    pred_time = time.time() - start
    
    print(f"   Prediction: {pred_time*1000:.2f}ms for ensemble forecast")
    
    # Memory efficiency
    import psutil
    import os
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"   Memory Usage: {memory_mb:.1f} MB")


def main():
    """Main demonstration function."""
    try:
        print("🧮 WAARDHAVEN MATHEMATICAL ENGINE SHOWCASE")
        print("🚀 Pure Computational Core for Investment Intelligence")
        print("🎯 Designed for WebAssembly compilation and high performance")
        
        # Run demonstrations
        demo_basic_calculations()
        demo_trend_analysis() 
        demo_volatility_prediction()
        demo_prediction_comparison()
        benchmark_performance()
        
        print("\n" + "="*60)
        print("✅ MATHEMATICAL ENGINE DEMONSTRATION COMPLETE")
        print("="*60)
        print("\n🎯 Key Capabilities Demonstrated:")
        print("   • Pure mathematical return calculations")
        print("   • Advanced trend analysis and prediction")
        print("   • Ensemble prediction methods")
        print("   • High-performance computation (10,000+ prices/second)")
        print("   • Memory-efficient operations")
        
        print("\n🚀 Next Steps:")
        print("   • Add machine learning prediction models")
        print("   • Implement portfolio optimization algorithms")  
        print("   • Build signal processing capabilities")
        print("   • Compile to WebAssembly for browser execution")
        print("   • Integrate with main investment platform")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Import numpy for demonstrations
    import numpy as np
    
    success = main()
    sys.exit(0 if success else 1)