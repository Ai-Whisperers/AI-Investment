#!/usr/bin/env python
"""
Download Market Data for Local Testing
Run this script to download real market data to your local disk for testing

LEGAL NOTICE: yfinance is intended for personal/educational use only.
Please review Yahoo's terms of use before extensive data usage.
Documentation: https://ranaroussi.github.io/yfinance/
"""

import argparse
import logging
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.data_collector import LocalDataCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Download market data for local testing"
    )
    
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "SPY", "QQQ"],
        help="Stock symbols to download"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days of historical data"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Directory to store data (default: ~/waardhaven_data)"
    )
    
    parser.add_argument(
        "--type",
        choices=["all", "prices", "news", "fundamentals"],
        default="all",
        help="Type of data to download"
    )
    
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Generate synthetic data instead of downloading"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics about local data"
    )
    
    parser.add_argument(
        "--clean",
        type=int,
        metavar="DAYS",
        help="Clean data older than specified days"
    )
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = LocalDataCollector(data_dir=args.data_dir)
    
    # Show stats if requested
    if args.stats:
        stats = collector.get_data_statistics()
        print("\n📊 Local Data Statistics:")
        print("-" * 40)
        print(f"Total Size: {stats['total_size_mb']} MB")
        print(f"Price Files: {stats['price_files']}")
        print(f"News Files: {stats['news_files']}")
        print(f"Fundamental Files: {stats['fundamental_files']}")
        print(f"Symbols: {', '.join(stats['symbols'])}")
        print(f"Last Updated: {stats['last_updated']}")
        return
    
    # Clean old data if requested
    if args.clean:
        cleaned = collector.clean_old_data(args.clean)
        print(f"✅ Cleaned {cleaned} files older than {args.clean} days")
        return
    
    # Calculate date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    
    print(f"\n🚀 Downloading data for {len(args.symbols)} symbols")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Storage: {collector.data_dir}")
    print("-" * 40)
    
    # Download price data
    if args.type in ["all", "prices"]:
        print("\n📈 Downloading price data...")
        print("⚖️ Note: yfinance is for personal/educational use only")
        
        if args.synthetic:
            # Generate synthetic data
            price_data = collector._generate_synthetic_data(
                args.symbols, start_date, end_date
            )
        else:
            # Use batch download for multiple symbols (more efficient)
            if len(args.symbols) > 3:
                print(f"   Using batch download for {len(args.symbols)} symbols...")
                price_data = collector.download_yahoo_batch(
                    args.symbols, start_date, end_date
                )
            else:
                # Use individual download for small batches
                price_data = collector.download_yahoo_data(
                    args.symbols, start_date, end_date
                )
        
        for symbol, df in price_data.items():
            if df is not None and not df.empty:
                print(f"  ✅ {symbol}: {len(df)} days of data")
                if 'Close' in df.columns:
                    print(f"     Latest close: ${df['Close'].iloc[-1]:.2f}")
                if 'Volume' in df.columns:
                    print(f"     Volume: {df['Volume'].iloc[-1]:,.0f}")
            else:
                print(f"  ❌ {symbol}: No data")
    
    # Download news data
    if args.type in ["all", "news"]:
        print("\n📰 Downloading news data...")
        news = collector.download_free_news("stock market", days_back=7)
        print(f"  ✅ Downloaded {len(news)} news articles")
        
        if news:
            print(f"     Latest: {news[0].get('title', 'N/A')[:60]}...")
    
    # Download fundamental data
    if args.type in ["all", "fundamentals"]:
        print("\n📊 Downloading fundamental data...")
        fundamentals = collector.download_fundamental_data(args.symbols)
        
        for symbol, data in fundamentals.items():
            print(f"  ✅ {symbol}: PE={data.get('pe_ratio', 0):.1f}, "
                  f"MarketCap=${data.get('market_cap', 0)/1e9:.1f}B")
    
    # Show final statistics
    print("\n" + "=" * 40)
    stats = collector.get_data_statistics()
    print(f"✅ Download complete!")
    print(f"📁 Total data size: {stats['total_size_mb']} MB")
    print(f"📊 Symbols available: {', '.join(stats['symbols'])}")
    print(f"\n💡 To use this data, import LocalDataCollector in your code:")
    print(f"   from app.services.data_collector import data_collector")
    print(f"   df = data_collector.load_price_data('AAPL')")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Download cancelled by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}")