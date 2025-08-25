# Local Data Testing Guide

## 🚀 Test Without API Keys!

This guide shows how to download real market data to your local hard disk and test the platform before deployment. No API keys required!

## Quick Start

### 1. Install Dependencies
```bash
cd apps/api
pip install yfinance  # For real market data (optional but recommended)
```

### 2. Download Market Data
```bash
# Download real market data to your disk
python download_data.py --symbols AAPL MSFT GOOGL TSLA NVDA --days 365

# Or generate synthetic data for immediate testing
python download_data.py --synthetic --symbols AAPL MSFT GOOGL

# Show statistics about your local data
python download_data.py --stats
```

### 3. Test the Platform
```bash
# Run comprehensive tests with local data
python test_local_data.py
```

## 📁 Data Storage

Data is stored in your home directory:
- **Windows**: `C:\Users\YourName\waardhaven_data\`
- **Mac/Linux**: `~/waardhaven_data/`

Structure:
```
waardhaven_data/
├── prices/          # Historical price data (Parquet format)
├── news/            # News articles (JSON)
├── fundamentals/    # Company fundamentals (JSON)
├── cache/           # Temporary cache files
└── inventory.json   # Data catalog
```

## 🎯 Features You Can Test

### With Local Data Only (No API Keys)
✅ **Backtesting System**
- Test any trading strategy
- Optimize parameters
- Generate performance reports
- Compare multiple strategies

✅ **Investment Analysis**
- Technical indicators (RSI, MACD, Bollinger Bands)
- Fundamental analysis
- Risk metrics calculation
- Portfolio optimization

✅ **Paper Trading**
- Simulated order execution
- Portfolio tracking
- Performance monitoring
- Risk management

✅ **AI Features**
- Investment chatbot (rule-based)
- Signal detection
- Pattern recognition
- Credibility scoring

### After Adding API Keys
🔑 **Real-Time Features**
- Live market data streaming
- Real news aggregation
- Social media monitoring
- Discord alerts

## 📊 Usage Examples

### Download Specific Symbols
```bash
python download_data.py --symbols AAPL MSFT GOOGL AMZN TSLA NVDA META
```

### Download Different Time Periods
```bash
# Last 30 days
python download_data.py --days 30

# Last 2 years
python download_data.py --days 730
```

### Download Different Data Types
```bash
# Just prices
python download_data.py --type prices

# Just news
python download_data.py --type news

# Everything
python download_data.py --type all
```

### Clean Old Data
```bash
# Remove data older than 30 days
python download_data.py --clean 30
```

## 🧪 Testing Strategies

The `test_local_data.py` script tests:
1. **Data Collection** - Downloads and stores market data
2. **Backtesting** - Tests multiple strategies
3. **Optimization** - Finds best parameters
4. **Report Generation** - Creates detailed analysis

Example output:
```
TESTING LOCAL BACKTESTING
=========================================
📊 Testing strategies with local data...
   Period: 2024-07-25 to 2025-01-25
   Capital: $100,000

   Testing Momentum...
   ✅ Total Return: 12.34%
      Sharpe Ratio: 1.45
      Max Drawdown: -8.21%
      Win Rate: 58.33%
      Total Trades: 48

🏆 Best Strategy: Momentum
   Sharpe Ratio: 1.45
   Total Return: 12.34%
```

## 🔧 Programmatic Usage

### In Your Code
```python
from app.services.data_collector import data_collector
from app.services.local_backtester import LocalBacktester, LocalBacktestConfig

# Download data
data = data_collector.download_yahoo_data(
    ["AAPL", "MSFT", "GOOGL"],
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Run backtest
config = LocalBacktestConfig(
    symbols=["AAPL", "MSFT", "GOOGL"],
    initial_capital=100000
)
backtester = LocalBacktester(config)
result = backtester.backtest_strategy(my_strategy)

print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

## 📈 Data Sources

### Free Data (No API Key)
- **Yahoo Finance**: Historical prices via yfinance
  - Documentation: https://ranaroussi.github.io/yfinance/
  - Note: For personal/educational use only
- **Synthetic Data**: Realistic generated data for testing

### With API Keys (Production)
- **TwelveData**: Real-time prices and technical indicators
- **MarketAux**: Financial news
- **Reddit**: Social sentiment
- **YouTube**: Video transcripts and analysis

## 🎯 What You Can Test Locally

| Feature | Local Data | Real Data |
|---------|------------|-----------|
| Backtesting | ✅ Full | ✅ Full |
| Technical Analysis | ✅ Full | ✅ Full |
| Fundamental Analysis | ✅ Synthetic | ✅ Real |
| Paper Trading | ✅ Full | ✅ Full |
| AI Chatbot | ✅ Full | ✅ Enhanced |
| News Analysis | ✅ Synthetic | ✅ Real |
| Social Sentiment | ❌ | ✅ Real |
| Real-time Updates | ❌ | ✅ WebSocket |
| Discord Alerts | ❌ | ✅ Live |

## 💡 Tips

1. **Start with synthetic data** for immediate testing
2. **Install yfinance** to get real historical data
3. **Download once, use many times** - Data is cached locally
4. **Test strategies offline** before deploying
5. **Generate reports** to analyze performance

## 🚀 Next Steps

After testing locally:
1. Configure API keys on Render.com
2. Deploy to production
3. Enable real-time features
4. Start live trading!

## 📝 Notes

- Local data is perfect for development and testing
- Synthetic data is surprisingly realistic for backtesting
- Real Yahoo Finance data is free but delayed (15-20 minutes)
- Production deployment adds real-time capabilities

---

**Remember**: You can fully test the platform's core functionality without spending any money on API keys!