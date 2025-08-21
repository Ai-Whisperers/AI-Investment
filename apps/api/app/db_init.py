import logging

from .core.database import Base, SessionLocal, engine
from .models import StrategyConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database with tables and default configuration."""
    Base.metadata.create_all(bind=engine)
    logger.info("DB tables created.")

    # Create default strategy configuration if it doesn't exist
    db = SessionLocal()
    try:
        config = db.query(StrategyConfig).first()
        if not config:
            logger.info("Creating default strategy configuration...")
            config = StrategyConfig(
                momentum_weight=0.4,
                market_cap_weight=0.3,
                risk_parity_weight=0.3,
                min_price_threshold=1.0,
                max_daily_return=0.5,
                min_daily_return=-0.5,
                max_forward_fill_days=2,
                outlier_std_threshold=3.0,
                rebalance_frequency="weekly",
                daily_drop_threshold=-0.01,
            )
            db.add(config)
            db.commit()
            logger.info("Created default strategy configuration")
    finally:
        db.close()


if __name__ == "__main__":
    main()
