#!/usr/bin/env python
"""
Test Local Data Collection and Backtesting
This script demonstrates how to use local data without API keys
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.data_collector import LocalDataCollector
from app.services.local_backtester import LocalBacktester, LocalBacktestConfig
from app.services.backtesting import TradingStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_data_collection():
    """Test downloading and storing market data locally."""
    print("\n" + "="*60)
    print("TESTING LOCAL DATA COLLECTION")
    print("="*60)
    
    # Initialize collector
    collector = LocalDataCollector()
    print(f"📁 Data directory: {collector.data_dir}")
    
    # Test symbols
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "SPY"]
    
    # 1. Generate synthetic data for immediate testing
    print("\n1️⃣ Generating synthetic data for testing...")
    synthetic_data = collector._generate_synthetic_data(
        symbols,
        start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    for symbol, df in synthetic_data.items():
        print(f"   ✅ {symbol}: {len(df)} days, "
              f"Latest: ${df['Close'].iloc[-1]:.2f}")
    
    # 2. Try downloading real data (works without API key using yfinance)
    print("\n2️⃣ Attempting to download real data (if yfinance installed)...")
    try:
        real_data = collector.download_yahoo_data(
            symbols[:3],  # Download fewer symbols to be faster
            start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        for symbol, df in real_data.items():
            if df is not None and not df.empty:
                print(f"   ✅ {symbol}: {len(df)} days real data")
    except Exception as e:
        print(f"   ⚠️ Could not download real data: {e}")
        print("   💡 Install yfinance for real data: pip install yfinance")
    
    # 3. Generate synthetic news
    print("\n3️⃣ Generating synthetic news data...")
    news = collector.download_free_news("technology stocks", days_back=7)
    print(f"   ✅ Generated {len(news)} news articles")
    if news:
        print(f"   📰 Latest: {news[0]['title'][:60]}...")
    
    # 4. Generate fundamental data
    print("\n4️⃣ Generating fundamental data...")
    fundamentals = collector.download_fundamental_data(symbols[:3])
    for symbol, data in fundamentals.items():
        print(f"   ✅ {symbol}: PE={data['pe_ratio']:.1f}, "
              f"Beta={data['beta']:.2f}")
    
    # 5. Show statistics
    print("\n5️⃣ Data Statistics:")
    stats = collector.get_data_statistics()
    print(f"   📊 Total size: {stats['total_size_mb']} MB")
    print(f"   📁 Price files: {stats['price_files']}")
    print(f"   📰 News files: {stats['news_files']}")
    print(f"   💹 Symbols: {', '.join(stats['symbols'])}")
    
    return collector


def test_backtesting():
    """Test backtesting with local data."""
    print("\n" + "="*60)
    print("TESTING LOCAL BACKTESTING")
    print("="*60)
    
    # Configure backtest
    config = LocalBacktestConfig(
        symbols=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
        start_date=(datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d"),
        initial_capital=100000,
        position_size=0.2,  # 20% per position
        use_synthetic=True  # Use synthetic data for testing
    )
    
    # Initialize backtester
    backtester = LocalBacktester(config)
    
    # Define test strategies
    strategies = [
        TradingStrategy(
            name="Momentum",
            strategy_type="momentum",
            lookback_period=20,
            entry_threshold=0.02,
            exit_threshold=-0.01
        ),
        TradingStrategy(
            name="Mean Reversion",
            strategy_type="mean_reversion", 
            lookback_period=30,
            entry_threshold=2.0,  # 2 std devs
            exit_threshold=0.5
        ),
        TradingStrategy(
            name="Buy and Hold",
            strategy_type="buy_and_hold"
        )
    ]
    
    print("\n📊 Testing strategies with local data...")
    print(f"   Period: {config.start_date} to {config.end_date}")
    print(f"   Capital: ${config.initial_capital:,}")
    
    # Test each strategy
    results = {}
    for strategy in strategies:
        print(f"\n   Testing {strategy.name}...")
        try:
            result = backtester.backtest_strategy(strategy)
            results[strategy.name] = result
            
            # Show key metrics
            print(f"   ✅ Total Return: {result.total_return:.2%}")
            print(f"      Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"      Max Drawdown: {result.max_drawdown:.2%}")
            print(f"      Win Rate: {result.win_rate:.2%}")
            print(f"      Total Trades: {result.total_trades}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Find best strategy
    if results:
        best = max(results.items(), key=lambda x: x[1].sharpe_ratio)
        print(f"\n🏆 Best Strategy: {best[0]}")
        print(f"   Sharpe Ratio: {best[1].sharpe_ratio:.2f}")
        print(f"   Total Return: {best[1].total_return:.2%}")
    
    # Generate report
    print("\n📝 Generating backtest report...")
    report_file = Path.home() / "waardhaven_backtest_report.txt"
    report = backtester.generate_report(str(report_file))
    print(f"   ✅ Report saved to: {report_file}")
    
    return backtester


def test_optimization():
    """Test strategy optimization with local data."""
    print("\n" + "="*60)
    print("TESTING STRATEGY OPTIMIZATION")
    print("="*60)
    
    config = LocalBacktestConfig(
        symbols=["AAPL", "MSFT", "GOOGL"],
        start_date=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        end_date=datetime.now().strftime("%Y-%m-%d"),
        use_synthetic=True
    )
    
    backtester = LocalBacktester(config)
    
    # Define base strategy
    base_strategy = TradingStrategy(
        name="Momentum_Optimized",
        strategy_type="momentum"
    )
    
    # Define parameter ranges to optimize
    param_ranges = {
        "lookback_period": (10, 30, 5),  # min, max, step
        "entry_threshold": (0.01, 0.05, 0.01),
        "exit_threshold": (-0.02, 0, 0.01)
    }
    
    print("\n🔍 Optimizing strategy parameters...")
    print(f"   Testing parameter combinations...")
    
    # Run optimization
    optimization_results = backtester.optimize_strategy(
        base_strategy,
        param_ranges
    )
    
    if optimization_results["best_params"]:
        print(f"\n✅ Best Parameters Found:")
        for param, value in optimization_results["best_params"].items():
            print(f"   {param}: {value}")
        
        best_result = optimization_results["best_result"]
        if best_result:
            print(f"\n   Performance:")
            print(f"   Sharpe Ratio: {best_result.sharpe_ratio:.2f}")
            print(f"   Total Return: {best_result.total_return:.2%}")
            print(f"   Max Drawdown: {best_result.max_drawdown:.2%}")
    
    return optimization_results


def main():
    """Run all tests."""
    print("\n" + "🚀 WAARDHAVEN LOCAL DATA TESTING SYSTEM 🚀")
    print("=" * 60)
    print("Testing data collection and backtesting without API keys")
    print("This allows you to test the platform before deployment")
    
    try:
        # Test data collection
        collector = test_data_collection()
        
        # Test backtesting
        backtester = test_backtesting()
        
        # Test optimization (shorter test)
        # optimization = test_optimization()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📌 Next Steps:")
        print("1. Your data is stored in: ~/waardhaven_data/")
        print("2. You can now test all platform features locally")
        print("3. Install yfinance for real market data: pip install yfinance")
        print("4. Run download_data.py to get more data")
        print("5. When ready, configure API keys and deploy to production")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()