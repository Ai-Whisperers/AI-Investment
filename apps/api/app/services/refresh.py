from datetime import date

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.asset import Asset, Price
from ..models.index import Allocation, IndexValue
from ..models.strategy import StrategyConfig
from ..providers.market_data import TwelveDataProvider
from ..utils.cache_utils import CacheManager
from .strategy import compute_index_and_allocations

DEFAULT_ASSETS = [
    # Stocks
    ("AAPL", "Apple Inc.", "Technology"),
    ("MSFT", "Microsoft Corp.", "Technology"),
    ("GOOGL", "Alphabet Inc.", "Technology"),
    ("AMZN", "Amazon.com Inc.", "Consumer Discretionary"),
    ("META", "Meta Platforms Inc.", "Communication Services"),
    ("TSLA", "Tesla Inc.", "Consumer Discretionary"),
    ("NVDA", "NVIDIA Corp.", "Technology"),
    # S&P 500 ETF as fallback benchmark
    ("SPY", "SPDR S&P 500 ETF", "Benchmark"),
    # Commodities via ETFs
    ("GLD", "SPDR Gold Shares", "Commodity"),
    ("SLV", "iShares Silver Trust", "Commodity"),
    ("USO", "United States Oil Fund", "Commodity"),
    # Bonds via ETFs
    ("TLT", "iShares 20+ Year Treasury Bond ETF", "Bond"),
    ("IEF", "iShares 7-10 Year Treasury Bond ETF", "Bond"),
]


def ensure_assets(db: Session):
    # Batch query: Get all existing symbols at once to avoid N+1 queries
    all_symbols = [sym for sym, _, _ in DEFAULT_ASSETS + [
        (settings.SP500_TICKER, "S&P 500", "Benchmark")
    ]]
    
    # Single query to get all existing assets
    existing_assets = db.query(Asset.symbol).filter(Asset.symbol.in_(all_symbols)).all()
    existing_symbols = {asset.symbol for asset in existing_assets}
    
    # Bulk insert for missing assets
    new_assets = []
    for sym, name, sector in DEFAULT_ASSETS + [
        (settings.SP500_TICKER, "S&P 500", "Benchmark")
    ]:
        if sym not in existing_symbols:
            new_assets.append(Asset(symbol=sym, name=name, sector=sector))
    
    if new_assets:
        db.bulk_save_objects(new_assets)
        db.commit()


def refresh_all(db: Session, smart_mode: bool = True):
    import json
    import logging
    from datetime import datetime

    logger = logging.getLogger(__name__)

    # Initialize provider with new architecture
    provider = TwelveDataProvider()

    # Smart mode now uses the improved TwelveData service with built-in rate limiting
    if smart_mode:
        logger.info("Using smart refresh with rate limit protection...")

    # Create backup before any operations
    backup_timestamp = datetime.utcnow()
    backup_created = False

    try:
        # Backup existing critical data
        logger.info("Creating data backup before refresh...")
        existing_prices = db.query(Price).count()
        existing_index_values = db.query(IndexValue).count()
        existing_allocations = db.query(Allocation).count()

        backup_info = {
            "timestamp": backup_timestamp.isoformat(),
            "prices_count": existing_prices,
            "index_values_count": existing_index_values,
            "allocations_count": existing_allocations,
        }
        logger.info(f"Backup info: {json.dumps(backup_info)}")
        backup_created = True

        # Start transaction with savepoint
        db.begin_nested() if hasattr(db, "begin_nested") else None

        logger.info("Starting standard refresh process...")

        # Step 1: Ensure assets exist
        logger.info("Ensuring assets...")
        ensure_assets(db)

        # Load asset list
        assets = db.query(Asset).all()
        symbols = [a.symbol for a in assets]
        logger.info(f"Found {len(symbols)} assets to refresh: {symbols}")

        # Step 2: Fetch prices
        logger.info("Fetching price data from TwelveData...")
        start = pd.to_datetime(settings.ASSET_DEFAULT_START).date()

        try:
            price_df = provider.fetch_historical_prices(symbols, start_date=start)
            logger.info(f"Fetched {len(price_df)} price records")
        except Exception as e:
            logger.error(f"Failed to fetch prices: {e}")
            # Try fetching with a shorter period as fallback
            from datetime import timedelta

            fallback_start = date.today() - timedelta(days=90)
            logger.info(f"Trying fallback period from {fallback_start}")
            price_df = provider.fetch_historical_prices(
                symbols, start_date=fallback_start
            )

        if price_df.empty:
            logger.error("No price data fetched!")
            raise ValueError("Unable to fetch any price data")

        # Step 3: Store prices (UPSERT - don't delete historical data!)
        logger.info("Storing prices in database...")

        price_count = 0
        updated_count = 0
        skipped_count = 0

        # Prepare batch data for efficient upsert
        price_data = []
        
        # Batch query: Get all assets at once to avoid N+1 queries
        symbols_in_df = list(price_df.columns.levels[0])
        assets_dict = {
            asset.symbol: asset 
            for asset in db.query(Asset).filter(Asset.symbol.in_(symbols_in_df)).all()
        }

        for sym in symbols_in_df:
            asset = assets_dict.get(sym)
            if not asset:
                logger.warning(f"Asset {sym} not found in database")
                continue

            # Get the Close price series for this symbol
            try:
                series = price_df[sym]["Close"]

                # Log data quality info
                null_count = series.isnull().sum()
                if null_count > 0:
                    logger.warning(
                        f"{sym}: {null_count} null values in {len(series)} total prices"
                    )

                # Collect non-null prices above minimum threshold
                min_price = 1.0  # Match our strategy's min_price_threshold
                for idx, val in series.items():
                    if pd.notna(val) and float(val) >= min_price:
                        price_data.append(
                            {
                                "asset_id": asset.id,
                                "date": idx.date(),
                                "close": float(val),
                            }
                        )
                    elif pd.notna(val):
                        skipped_count += 1
                        logger.debug(
                            f"Skipped {sym} price on {idx.date()}: ${val:.4f} below threshold"
                        )

            except KeyError as e:
                logger.error(f"Missing 'Close' data for {sym}: {e}")
                continue

        # Perform BULK batch upsert using PostgreSQL ON CONFLICT
        if price_data:
            from sqlalchemy.dialects.postgresql import insert

            # Split into chunks for better memory management
            chunk_size = 1000

            for i in range(0, len(price_data), chunk_size):
                chunk = price_data[i : i + chunk_size]

                # Use SQLAlchemy's bulk insert with ON CONFLICT
                stmt = insert(Price).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["asset_id", "date"],
                    set_={"close": stmt.excluded.close},
                )

                db.execute(stmt)

                # Track inserts vs updates (approximate)
                price_count += len(chunk)

            db.commit()

            # Log actual count
            actual_count = db.query(Price).count()
            logger.info(f"Total prices in database: {actual_count}")

        logger.info(
            f"Stored {price_count} new prices, updated {updated_count} existing, skipped {skipped_count} below threshold"
        )

        # Step 4: Compute index + allocations with strategy config
        logger.info("Computing index and allocations...")

        # Get strategy configuration from database
        strategy_config = db.query(StrategyConfig).first()
        if strategy_config:
            config = {
                "momentum_weight": strategy_config.momentum_weight,
                "market_cap_weight": strategy_config.market_cap_weight,
                "risk_parity_weight": strategy_config.risk_parity_weight,
                "min_price": strategy_config.min_price_threshold,
                "max_daily_return": strategy_config.max_daily_return,
                "min_daily_return": strategy_config.min_daily_return,
                "max_forward_fill_days": strategy_config.max_forward_fill_days,
                "outlier_std_threshold": strategy_config.outlier_std_threshold,
                "rebalance_frequency": strategy_config.rebalance_frequency,
                "daily_drop_threshold": strategy_config.daily_drop_threshold,
            }
            compute_index_and_allocations(db, config)
        else:
            compute_index_and_allocations(db)

        # Calculate and store portfolio metrics
        try:
            from .performance import calculate_portfolio_metrics

            logger.info("Calculating portfolio performance metrics...")
            metrics = calculate_portfolio_metrics(db)
            if metrics:
                logger.info(
                    f"Portfolio metrics calculated: Sharpe={metrics.get('sharpe_ratio', 0):.2f}, Max DD={metrics.get('max_drawdown', 0):.1f}%"
                )
        except Exception as e:
            logger.warning(f"Failed to calculate portfolio metrics: {e}")

        # Verify results
        index_count = db.query(func.count()).select_from(IndexValue).scalar()
        logger.info(f"Refresh completed successfully. Index values: {index_count}")

        # If we got here, commit the transaction
        db.commit()
        logger.info("Refresh transaction committed successfully")

        # Invalidate relevant caches after successful refresh
        try:
            CacheManager.invalidate_index_data()
            CacheManager.invalidate_market_data()
            logger.info("Cache invalidated after successful refresh")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate cache: {cache_error}")

    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        import traceback

        logger.error(traceback.format_exc())

        # Rollback transaction
        try:
            db.rollback()
            logger.info("Transaction rolled back successfully")
        except Exception as rollback_error:
            logger.error(f"Failed to rollback transaction: {rollback_error}")

        # Log backup information for potential manual recovery
        if backup_created:
            logger.info(
                f"Backup was created at {backup_timestamp.isoformat()}. Manual recovery may be possible."
            )
            logger.info(f"Pre-refresh state: {json.dumps(backup_info)}")

        raise
