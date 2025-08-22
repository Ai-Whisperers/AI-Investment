"""
Global pytest configuration and fixtures.
"""

import asyncio
import os
from collections.abc import Generator
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment variable for faster bcrypt
os.environ["TESTING"] = "true"

from app.core.database import Base
from app.core.dependencies import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.asset import Asset, Price
from app.models.portfolio import Portfolio
from app.models.user import User

# Import modular test factories
from tests.factories import AssetFactory, PortfolioFactory, StrategyFactory, UserFactory

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 20,  # Add timeout for SQLite
        },
        poolclass=StaticPool,
        echo=False
    )

    # Enable foreign key constraints for SQLite
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA synchronous=NORMAL")  # Faster but still safe
            cursor.execute("PRAGMA cache_size=10000")  # Increase cache
            cursor.execute("PRAGMA temp_store=memory")  # Use memory for temp tables
            cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    
    # Proper cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()  # Critical: dispose engine to free connections


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a test database session with transaction rollback."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    
    try:
        yield session
    except Exception:
        if transaction.is_active:
            transaction.rollback()
        raise
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()  # Always rollback to ensure clean state
        connection.close()


@pytest.fixture(scope="function")
def client(test_db_session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db_session) -> User:
    """Create a test user using factory."""
    user_data = UserFactory.create_user_data(email="test@example.com")
    user = User(
        email=user_data["email"],
        password_hash=get_password_hash(user_data["password"]),
        is_google_user=user_data["is_google_user"],
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(test_db_session) -> User:
    """Create an admin user using factory."""
    admin_data = UserFactory.create_user_data(
        email="admin@example.com",
        password="AdminPassword123!"
    )
    user = User(
        email=admin_data["email"],
        password_hash=get_password_hash(admin_data["password"]),
        is_google_user=False,
        is_active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Create authentication headers for test user."""
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user) -> dict:
    """Create authentication headers for admin user."""
    access_token = create_access_token({"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_assets(test_db_session) -> list[Asset]:
    """Create sample assets using factory."""
    assets = []
    test_symbols = [("AAPL", "Apple Inc."), ("GOOGL", "Alphabet Inc."),
                    ("MSFT", "Microsoft Corp."), ("SPY", "SPDR S&P 500 ETF")]

    for symbol, name in test_symbols:
        asset_data = AssetFactory.create_asset_data(symbol=symbol, name=name)
        asset = Asset(**asset_data)
        test_db_session.add(asset)
        assets.append(asset)

    test_db_session.commit()
    return assets


@pytest.fixture
def sample_prices(test_db_session, sample_assets) -> list[Price]:
    """Create sample price data for testing."""
    prices = []
    base_date = datetime.now().date() - timedelta(days=30)

    for asset in sample_assets:
        for i in range(30):
            price_date = base_date + timedelta(days=i)
            base_price = {"AAPL": 150, "GOOGL": 2800, "MSFT": 400, "SPY": 450}[asset.symbol]

            # Add some realistic variation
            variation = 1 + (i % 5 - 2) * 0.01  # +/- 2% variation

            price = Price(
                asset_id=asset.id,
                date=price_date,
                open=Decimal(str(base_price * variation * 0.99)),
                high=Decimal(str(base_price * variation * 1.01)),
                low=Decimal(str(base_price * variation * 0.98)),
                close=Decimal(str(base_price * variation)),
                volume=1000000 + i * 10000
            )
            prices.append(price)
            test_db_session.add(price)

    test_db_session.commit()
    return prices


@pytest.fixture
def sample_portfolio(test_db_session, test_user, sample_assets) -> Portfolio:
    """Create a sample portfolio using factory."""
    portfolio_data = PortfolioFactory.create_portfolio_data(
        name="Test Portfolio",
        user_id=test_user.id,
        total_value=100000.00
    )
    # Add strategy config from factory
    portfolio_data["strategy_config"] = StrategyFactory.create_strategy_config()

    portfolio = Portfolio(**portfolio_data)
    test_db_session.add(portfolio)
    test_db_session.commit()
    test_db_session.refresh(portfolio)
    return portfolio


@pytest.fixture
def mock_twelvedata_response():
    """Mock TwelveData API response."""
    return {
        "meta": {
            "symbol": "AAPL",
            "interval": "1day",
            "currency": "USD",
            "exchange": "NASDAQ",
            "type": "Common Stock"
        },
        "values": [
            {
                "datetime": "2024-01-19",
                "open": "149.50",
                "high": "151.00",
                "low": "149.00",
                "close": "150.25",
                "volume": "58245100"
            },
            {
                "datetime": "2024-01-18",
                "open": "148.00",
                "high": "150.00",
                "low": "147.50",
                "close": "149.50",
                "volume": "55123000"
            }
        ],
        "status": "ok"
    }


@pytest.fixture
def mock_marketaux_response():
    """Mock MarketAux API response."""
    return {
        "data": [
            {
                "uuid": "test-uuid-1",
                "title": "Apple Reports Strong Q4 Earnings",
                "description": "Apple Inc. reported better than expected earnings...",
                "url": "https://example.com/article1",
                "published_at": "2024-01-19T10:00:00Z",
                "source": "Reuters",
                "entities": [
                    {"symbol": "AAPL", "name": "Apple Inc."}
                ],
                "sentiment": 0.85
            }
        ],
        "meta": {
            "found": 1,
            "returned": 1,
            "limit": 10,
            "page": 1
        }
    }


# Performance testing fixtures
@pytest.fixture
def large_dataset(test_db_session, sample_assets):
    """Create a large dataset for performance testing."""
    # Reduce size for faster testing - only 30 days instead of 365
    prices = []
    base_date = datetime.now().date() - timedelta(days=30)

    price_mappings = []
    for asset in sample_assets:
        for i in range(30):  # Reduced from 365 to 30
            price_date = base_date + timedelta(days=i)
            price_mapping = {
                "asset_id": asset.id,
                "date": price_date,
                "open": Decimal(str(100 + i % 50)),
                "high": Decimal(str(105 + i % 50)),
                "low": Decimal(str(95 + i % 50)),
                "close": Decimal(str(100 + i % 50)),
                "volume": 1000000
            }
            price_mappings.append(price_mapping)

    # Use bulk_insert_mappings for better performance
    test_db_session.bulk_insert_mappings(Price, price_mappings)
    test_db_session.commit()
    return len(price_mappings)
