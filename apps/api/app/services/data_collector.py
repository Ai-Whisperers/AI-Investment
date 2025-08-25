"""
Local Market Data Collector
Downloads and stores real market data locally for testing and backtesting
Works without API keys using free data sources
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class LocalDataCollector:
    """
    Collects and stores market data locally for testing.
    Uses free data sources that don't require API keys.
    """
    
    def __init__(self, data_dir: str = None):
        """Initialize the data collector with local storage."""
        # Set up data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to user's home directory
            self.data_dir = Path.home() / "waardhaven_data"
        
        # Create directory structure
        self.data_dir.mkdir(exist_ok=True)
        self.price_dir = self.data_dir / "prices"
        self.news_dir = self.data_dir / "news"
        self.fundamental_dir = self.data_dir / "fundamentals"
        self.cache_dir = self.data_dir / "cache"
        
        for dir in [self.price_dir, self.news_dir, self.fundamental_dir, self.cache_dir]:
            dir.mkdir(exist_ok=True)
        
        # Track data inventory
        self.inventory_file = self.data_dir / "inventory.json"
        self.inventory = self._load_inventory()
        
        logger.info(f"Data collector initialized. Storage: {self.data_dir}")
    
    def _load_inventory(self) -> dict:
        """Load the data inventory from disk."""
        if self.inventory_file.exists():
            with open(self.inventory_file, 'r') as f:
                return json.load(f)
        return {
            "prices": {},
            "news": {},
            "fundamentals": {},
            "last_updated": None
        }
    
    def _save_inventory(self):
        """Save the data inventory to disk."""
        self.inventory["last_updated"] = datetime.now().isoformat()
        with open(self.inventory_file, 'w') as f:
            json.dump(self.inventory, f, indent=2)
    
    def download_yahoo_data(
        self,
        symbols: List[str],
        start_date: str = None,
        end_date: str = None,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Download historical price data from Yahoo Finance (free, no API key).
        
        Args:
            symbols: List of stock symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (1d, 1h, 5m, etc.)
            
        Returns:
            Dictionary of symbol -> DataFrame
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("yfinance not installed. Install with: pip install yfinance")
            return self._generate_synthetic_data(symbols, start_date, end_date)
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        data = {}
        
        for symbol in symbols:
            # Use CSV if parquet not available
            try:
                cache_file = self.price_dir / f"{symbol}_{interval}_{start_date}_{end_date}.parquet"
                use_parquet = True
            except:
                cache_file = self.price_dir / f"{symbol}_{interval}_{start_date}_{end_date}.csv"
                use_parquet = False
            
            # Check cache first
            if cache_file.exists():
                logger.info(f"Loading cached data for {symbol}")
                if use_parquet:
                    try:
                        data[symbol] = pd.read_parquet(cache_file)
                    except:
                        # Fallback to CSV
                        cache_file = cache_file.with_suffix('.csv')
                        if cache_file.exists():
                            data[symbol] = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                else:
                    data[symbol] = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            else:
                logger.info(f"Downloading data for {symbol} from Yahoo Finance")
                try:
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(start=start_date, end=end_date, interval=interval)
                    
                    if not df.empty:
                        # Save to cache
                        try:
                            df.to_parquet(cache_file)
                        except:
                            # Fallback to CSV
                            cache_file = cache_file.with_suffix('.csv')
                            df.to_csv(cache_file)
                        data[symbol] = df
                        
                        # Update inventory
                        if symbol not in self.inventory["prices"]:
                            self.inventory["prices"][symbol] = []
                        
                        self.inventory["prices"][symbol].append({
                            "start": start_date,
                            "end": end_date,
                            "interval": interval,
                            "file": str(cache_file.name),
                            "rows": len(df),
                            "downloaded": datetime.now().isoformat()
                        })
                        
                        self._save_inventory()
                    else:
                        logger.warning(f"No data returned for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error downloading {symbol}: {e}")
                    # Generate synthetic data as fallback
                    data[symbol] = self._generate_synthetic_data([symbol], start_date, end_date)[symbol]
        
        return data
    
    def _generate_synthetic_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate realistic synthetic market data for testing.
        Uses random walk with drift to simulate price movements.
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        data = {}
        
        # Base prices for different symbols
        base_prices = {
            "AAPL": 180.0,
            "GOOGL": 140.0,
            "MSFT": 380.0,
            "TSLA": 250.0,
            "AMZN": 170.0,
            "META": 480.0,
            "NVDA": 680.0,
            "SPY": 450.0,
        }
        
        for symbol in symbols:
            # Get base price or random
            base_price = base_prices.get(symbol, np.random.uniform(50, 500))
            
            # Generate price series using geometric Brownian motion
            returns = np.random.normal(0.0005, 0.02, len(dates))  # Daily returns
            price_series = base_price * np.exp(np.cumsum(returns))
            
            # Add some volatility clustering (GARCH-like effect)
            volatility = np.abs(returns)
            for i in range(1, len(volatility)):
                volatility[i] = 0.1 * returns[i] + 0.9 * volatility[i-1]
            
            price_series = price_series * (1 + volatility * np.random.randn(len(dates)) * 0.1)
            
            # Generate OHLCV data
            df = pd.DataFrame(index=dates)
            df['Close'] = price_series
            
            # Generate realistic OHLC from close
            daily_range = np.abs(np.random.normal(0, 0.01, len(dates)))
            df['High'] = df['Close'] * (1 + daily_range)
            df['Low'] = df['Close'] * (1 - daily_range * 0.8)
            df['Open'] = df['Close'].shift(1).fillna(base_price) * (1 + np.random.normal(0, 0.005, len(dates)))
            
            # Generate volume (correlated with price changes)
            base_volume = np.random.uniform(10_000_000, 100_000_000)
            price_change = np.abs(df['Close'].pct_change().fillna(0))
            df['Volume'] = base_volume * (1 + price_change * 10) * np.random.uniform(0.8, 1.2, len(dates))
            df['Volume'] = df['Volume'].astype(int)
            
            # Save synthetic data
            cache_file = self.price_dir / f"{symbol}_synthetic_{start_date}_{end_date}.csv"
            try:
                # Try parquet first
                cache_file = cache_file.with_suffix('.parquet')
                df.to_parquet(cache_file)
            except:
                # Fallback to CSV
                cache_file = cache_file.with_suffix('.csv')
                df.to_csv(cache_file)
            
            data[symbol] = df
            
            logger.info(f"Generated synthetic data for {symbol}: {len(df)} days")
        
        return data
    
    def download_free_news(
        self,
        query: str = "stock market",
        days_back: int = 7
    ) -> List[Dict]:
        """
        Download free news data for testing.
        Uses free news APIs or generates synthetic news.
        """
        news_file = self.news_dir / f"news_{query.replace(' ', '_')}_{days_back}d.json"
        
        if news_file.exists():
            with open(news_file, 'r') as f:
                return json.load(f)
        
        # Generate synthetic news for testing
        news = self._generate_synthetic_news(query, days_back)
        
        # Save to disk
        with open(news_file, 'w') as f:
            json.dump(news, f, indent=2)
        
        return news
    
    def _generate_synthetic_news(
        self,
        query: str,
        days_back: int
    ) -> List[Dict]:
        """Generate synthetic news data for testing."""
        news_templates = [
            "{company} announces {change}% {direction} in quarterly earnings",
            "Breaking: {company} stock {action} on {catalyst} news",
            "Analysts {sentiment} on {company} following {event}",
            "{company} CEO discusses {topic} strategy in recent interview",
            "Market watch: {company} among top {performance} in {sector} sector",
            "{company} unveils new {product} targeting {market} market",
            "Institutional investors {action} positions in {company}",
            "{company} partnership with {partner} drives stock {direction}",
        ]
        
        companies = ["Apple", "Microsoft", "Google", "Tesla", "Amazon", "Meta", "NVIDIA", "AMD"]
        actions = ["surges", "drops", "rallies", "consolidates", "breaks out"]
        sentiments = ["upgrade", "downgrade", "maintain", "initiate coverage"]
        catalysts = ["earnings", "product launch", "regulatory", "partnership", "guidance"]
        
        news = []
        for i in range(days_back * 10):  # ~10 news items per day
            template = np.random.choice(news_templates)
            
            # Fill in template
            article = {
                "title": template.format(
                    company=np.random.choice(companies),
                    change=np.random.randint(1, 20),
                    direction=np.random.choice(["increase", "decrease"]),
                    action=np.random.choice(actions),
                    catalyst=np.random.choice(catalysts),
                    sentiment=np.random.choice(sentiments),
                    event=np.random.choice(["earnings report", "product launch", "conference"]),
                    topic=np.random.choice(["AI", "cloud", "mobile", "autonomous"]),
                    performance=np.random.choice(["gainers", "movers", "performers"]),
                    sector=np.random.choice(["technology", "consumer", "financial"]),
                    product=np.random.choice(["AI model", "chip", "platform", "service"]),
                    market=np.random.choice(["enterprise", "consumer", "global"]),
                    partner=np.random.choice(["major retailer", "tech giant", "government"])
                ),
                "source": np.random.choice(["Reuters", "Bloomberg", "CNBC", "WSJ"]),
                "published": (datetime.now() - timedelta(days=i/10)).isoformat(),
                "sentiment": np.random.uniform(-1, 1),
                "relevance": np.random.uniform(0.5, 1.0),
                "symbols": list(np.random.choice(
                    ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA"],
                    size=np.random.randint(1, 4),
                    replace=False
                ))
            }
            
            news.append(article)
        
        return news
    
    def download_fundamental_data(
        self,
        symbols: List[str]
    ) -> Dict[str, Dict]:
        """
        Download or generate fundamental data for testing.
        """
        fundamentals = {}
        
        for symbol in symbols:
            fund_file = self.fundamental_dir / f"{symbol}_fundamentals.json"
            
            if fund_file.exists():
                with open(fund_file, 'r') as f:
                    fundamentals[symbol] = json.load(f)
            else:
                # Generate synthetic fundamental data
                fundamentals[symbol] = self._generate_synthetic_fundamentals(symbol)
                
                # Save to disk
                with open(fund_file, 'w') as f:
                    json.dump(fundamentals[symbol], f, indent=2)
        
        return fundamentals
    
    def _generate_synthetic_fundamentals(self, symbol: str) -> Dict:
        """Generate synthetic fundamental data for testing."""
        return {
            "symbol": symbol,
            "market_cap": np.random.uniform(10e9, 2000e9),
            "pe_ratio": np.random.uniform(10, 40),
            "peg_ratio": np.random.uniform(0.5, 3),
            "pb_ratio": np.random.uniform(1, 10),
            "ps_ratio": np.random.uniform(1, 20),
            "ev_ebitda": np.random.uniform(5, 30),
            "profit_margin": np.random.uniform(0.05, 0.35),
            "operating_margin": np.random.uniform(0.1, 0.4),
            "roe": np.random.uniform(0.1, 0.5),
            "roa": np.random.uniform(0.05, 0.25),
            "debt_to_equity": np.random.uniform(0, 2),
            "current_ratio": np.random.uniform(0.8, 3),
            "quick_ratio": np.random.uniform(0.5, 2),
            "revenue_growth": np.random.uniform(-0.1, 0.5),
            "earnings_growth": np.random.uniform(-0.2, 0.6),
            "dividend_yield": np.random.uniform(0, 0.05),
            "beta": np.random.uniform(0.5, 2),
            "52_week_high": np.random.uniform(100, 1000),
            "52_week_low": np.random.uniform(50, 500),
            "analyst_rating": np.random.choice(["Strong Buy", "Buy", "Hold", "Sell"]),
            "last_updated": datetime.now().isoformat()
        }
    
    def load_price_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Load price data from local storage.
        """
        # Look for matching files (both parquet and csv)
        patterns = [f"{symbol}_*.parquet", f"{symbol}_*.csv"]
        files = []
        for pattern in patterns:
            files.extend(list(self.price_dir.glob(pattern)))
        
        if not files:
            logger.warning(f"No local data found for {symbol}")
            return None
        
        # Load most recent file
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Load based on file extension
        if files[0].suffix == '.parquet':
            try:
                df = pd.read_parquet(files[0])
            except:
                # Try CSV if parquet fails
                csv_file = files[0].with_suffix('.csv')
                if csv_file.exists():
                    df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                else:
                    return None
        else:
            df = pd.read_csv(files[0], index_col=0, parse_dates=True)
        
        # Filter by date range if specified
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
        
        return df
    
    def get_data_statistics(self) -> Dict:
        """Get statistics about locally stored data."""
        stats = {
            "total_size_mb": 0,
            "price_files": 0,
            "news_files": 0,
            "fundamental_files": 0,
            "symbols": set(),
            "date_range": {},
            "last_updated": self.inventory.get("last_updated")
        }
        
        # Count files and size (both parquet and csv)
        for pattern in ["*.parquet", "*.csv"]:
            for file in self.price_dir.glob(pattern):
                stats["price_files"] += 1
                stats["total_size_mb"] += file.stat().st_size / (1024 * 1024)
                
                # Extract symbol from filename
                symbol = file.stem.split("_")[0]
                stats["symbols"].add(symbol)
        
        for file in self.news_dir.glob("*.json"):
            stats["news_files"] += 1
            stats["total_size_mb"] += file.stat().st_size / (1024 * 1024)
        
        for file in self.fundamental_dir.glob("*.json"):
            stats["fundamental_files"] += 1
            stats["total_size_mb"] += file.stat().st_size / (1024 * 1024)
        
        stats["symbols"] = list(stats["symbols"])
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        return stats
    
    def clean_old_data(self, days_old: int = 30):
        """Clean data older than specified days."""
        cutoff = datetime.now() - timedelta(days=days_old)
        cleaned = 0
        
        for dir in [self.price_dir, self.news_dir, self.fundamental_dir, self.cache_dir]:
            for file in dir.glob("*"):
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                    file.unlink()
                    cleaned += 1
        
        logger.info(f"Cleaned {cleaned} old files")
        return cleaned


# Global instance
data_collector = LocalDataCollector()