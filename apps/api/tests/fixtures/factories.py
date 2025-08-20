"""
Test data factories using factory_boy.
"""

import factory
from factory import fuzzy
from decimal import Decimal
from datetime import datetime, timedelta
import random

from app.models.user import User
from app.models.asset import Asset, Price
from app.models.index import IndexValue, Allocation
from app.models.portfolio import Portfolio
from app.models.strategy import StrategyConfig


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate test users."""
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = factory.Faker('email')
    username = factory.Faker('user_name')
    hashed_password = factory.LazyFunction(lambda: "$2b$12$test_hash")
    is_active = True
    is_superuser = False
    created_at = factory.LazyFunction(datetime.now)


class AssetFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate test assets."""
    class Meta:
        model = Asset
        sqlalchemy_session_persistence = "commit"
    
    symbol = factory.Sequence(lambda n: f"TEST{n:04d}")
    name = factory.Faker('company')
    asset_type = fuzzy.FuzzyChoice(['stock', 'etf', 'commodity'])
    sector = fuzzy.FuzzyChoice(['Technology', 'Finance', 'Healthcare', 'Energy'])
    market_cap = fuzzy.FuzzyDecimal(1000000000, 1000000000000, precision=2)


class PriceFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate realistic price data."""
    class Meta:
        model = Price
        sqlalchemy_session_persistence = "commit"
    
    asset = factory.SubFactory(AssetFactory)
    date = fuzzy.FuzzyDate(datetime.now().date() - timedelta(days=365), datetime.now().date())
    open = fuzzy.FuzzyDecimal(50, 500, precision=2)
    close = factory.LazyAttribute(lambda obj: Decimal(str(float(obj.open) * random.uniform(0.95, 1.05))).quantize(Decimal('0.01')))
    high = factory.LazyAttribute(lambda obj: max(obj.open, obj.close) * Decimal('1.02'))
    low = factory.LazyAttribute(lambda obj: min(obj.open, obj.close) * Decimal('0.98'))
    volume = fuzzy.FuzzyInteger(1000000, 100000000)
    
    @factory.lazy_attribute
    def adjusted_close(self):
        return self.close


class PortfolioFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate test portfolios."""
    class Meta:
        model = Portfolio
        sqlalchemy_session_persistence = "commit"
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('catch_phrase')
    initial_value = fuzzy.FuzzyDecimal(10000, 1000000, precision=2)
    current_value = factory.LazyAttribute(lambda obj: obj.initial_value * Decimal('1.1'))
    strategy = fuzzy.FuzzyChoice(['conservative', 'moderate', 'aggressive'])
    created_at = factory.LazyFunction(datetime.now)
    
    @factory.post_generation
    def positions(self, create, extracted, **kwargs):
        """Add positions after portfolio creation."""
        if not create:
            return
        
        if extracted:
            for position in extracted:
                self.positions.append(position)


class IndexValueFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate index values."""
    class Meta:
        model = IndexValue
        sqlalchemy_session_persistence = "commit"
    
    date = fuzzy.FuzzyDate(datetime.now().date() - timedelta(days=30), datetime.now().date())
    value = fuzzy.FuzzyDecimal(1000, 2000, precision=4)
    daily_return = fuzzy.FuzzyDecimal(-0.05, 0.05, precision=6)
    cumulative_return = fuzzy.FuzzyDecimal(-0.2, 0.5, precision=6)
    
    @factory.lazy_attribute
    def volatility(self):
        return Decimal(str(abs(float(self.daily_return)) * 2)).quantize(Decimal('0.000001'))


class AllocationFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate allocation data."""
    class Meta:
        model = Allocation
        sqlalchemy_session_persistence = "commit"
    
    date = fuzzy.FuzzyDate(datetime.now().date() - timedelta(days=30), datetime.now().date())
    asset = factory.SubFactory(AssetFactory)
    weight = fuzzy.FuzzyDecimal(0.01, 0.4, precision=6)
    shares = fuzzy.FuzzyInteger(1, 1000)
    value = fuzzy.FuzzyDecimal(1000, 100000, precision=2)


class StrategyConfigFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate strategy configurations."""
    class Meta:
        model = StrategyConfig
        sqlalchemy_session_persistence = "commit"
    
    name = factory.Faker('bs')
    risk_level = fuzzy.FuzzyChoice(['low', 'medium', 'high'])
    rebalance_frequency = fuzzy.FuzzyChoice(['daily', 'weekly', 'monthly', 'quarterly'])
    min_weight = Decimal('0.01')
    max_weight = Decimal('0.40')
    target_return = fuzzy.FuzzyDecimal(0.05, 0.20, precision=4)
    max_drawdown = fuzzy.FuzzyDecimal(0.10, 0.30, precision=4)
    
    @factory.lazy_attribute
    def config_json(self):
        return {
            "risk_level": self.risk_level,
            "rebalance_frequency": self.rebalance_frequency,
            "constraints": {
                "min_weight": str(self.min_weight),
                "max_weight": str(self.max_weight)
            }
        }


# Helper functions for generating test data
def create_price_series(asset, start_date, num_days=30, base_price=100):
    """Create a series of prices for an asset."""
    prices = []
    current_price = base_price
    
    for i in range(num_days):
        date = start_date + timedelta(days=i)
        # Random walk with slight upward bias
        change = random.gauss(0.001, 0.02)
        current_price = current_price * (1 + change)
        
        prices.append(Price(
            asset_id=asset.id,
            date=date,
            open=Decimal(str(current_price * 0.99)),
            high=Decimal(str(current_price * 1.01)),
            low=Decimal(str(current_price * 0.98)),
            close=Decimal(str(current_price)),
            volume=random.randint(1000000, 10000000)
        ))
    
    return prices


def create_portfolio_with_positions(session, user, assets, weights=None):
    """Create a portfolio with allocated positions."""
    if weights is None:
        weights = [1.0 / len(assets)] * len(assets)
    
    portfolio = PortfolioFactory(user=user)
    session.add(portfolio)
    
    total_value = float(portfolio.initial_value)
    
    for asset, weight in zip(assets, weights):
        allocation = AllocationFactory(
            asset=asset,
            weight=Decimal(str(weight)),
            value=Decimal(str(total_value * weight)),
            date=datetime.now().date()
        )
        session.add(allocation)
    
    session.commit()
    return portfolio