"""
Global pytest configuration and fixtures.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import Base
from app.main import app
from app.core.dependencies import get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.asset import Asset, Price
from app.models.index import IndexValue, Allocation
from app.models.portfolio import Portfolio


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
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


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
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True,
        is_superuser=False
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(test_db_session) -> User:
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("AdminPassword123!"),
        is_active=True,
        is_superuser=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Create authentication headers for test user."""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user) -> dict:
    """Create authentication headers for admin user."""
    access_token = create_access_token(data={"sub": admin_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_assets(test_db_session) -> list[Asset]:
    """Create sample assets for testing."""
    assets = [
        Asset(symbol="AAPL", name="Apple Inc.", asset_type="stock", sector="Technology"),
        Asset(symbol="GOOGL", name="Alphabet Inc.", asset_type="stock", sector="Technology"),
        Asset(symbol="MSFT", name="Microsoft Corp.", asset_type="stock", sector="Technology"),
        Asset(symbol="SPY", name="SPDR S&P 500 ETF", asset_type="etf", sector="Index"),
    ]
    for asset in assets:
        test_db_session.add(asset)
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
    """Create a sample portfolio for testing."""
    portfolio = Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        initial_value=Decimal("100000.00"),
        strategy="moderate",
        created_at=datetime.now()
    )
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
    prices = []
    base_date = datetime.now().date() - timedelta(days=365)
    
    for asset in sample_assets:
        for i in range(365):
            price_date = base_date + timedelta(days=i)
            price = Price(
                asset_id=asset.id,
                date=price_date,
                close=Decimal(str(100 + i % 50)),
                volume=1000000
            )
            prices.append(price)
    
    test_db_session.bulk_insert_mappings(Price, [p.__dict__ for p in prices])
    test_db_session.commit()
    return len(prices)