# Architecture Patterns Documentation
**Last Updated**: January 28, 2025 - Added Service Orchestration Pattern

## Clean Architecture Implementation

This document outlines the architectural patterns and best practices implemented in the Waardhaven AutoIndex platform.

## Repository Pattern

### Overview
The Repository Pattern provides an abstraction layer between the data access logic and the business logic. This ensures:
- **Separation of Concerns**: Business logic is decoupled from data access
- **Testability**: Repositories can be easily mocked for testing
- **Flexibility**: Data source can be changed without affecting business logic
- **Clean Architecture**: Follows dependency inversion principle

### Implementation

#### Repository Interfaces
All repositories implement interfaces defined in `app/repositories/interfaces.py`:

```python
class IAssetRepository(ABC):
    """Interface for asset repository operations."""
    
    @abstractmethod
    def get_by_id(self, asset_id: int) -> Optional[Asset]:
        pass
    
    @abstractmethod
    def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        pass
    
    @abstractmethod
    def get_all(self, limit: Optional[int] = None) -> List[Asset]:
        pass
```

#### Concrete Implementations
SQLAlchemy implementations in `app/repositories/`:
- `asset_repository.py` - Asset data access
- `price_repository.py` - Price history data access
- `user_repository.py` - User management
- `portfolio_repository.py` - Portfolio operations

### Usage in Routers

#### ❌ BAD: Direct Database Access (Anti-pattern)
```python
@router.get("/asset/{symbol}")
def get_asset(symbol: str, db: Session = Depends(get_db)):
    # Direct database query in presentation layer - VIOLATION!
    asset = db.query(Asset).filter(Asset.symbol == symbol).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Not found")
    return asset
```

#### ✅ GOOD: Using Repository Pattern
```python
@router.get("/asset/{symbol}")
def get_asset(symbol: str, db: Session = Depends(get_db)):
    # Use repository for data access
    asset_repo = SQLAssetRepository(db)
    asset = asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(status_code=404, detail="Not found")
    return asset
```

## Use Case Pattern

### Overview
Use Cases encapsulate business logic and orchestrate the flow of data between repositories and the presentation layer.

### Implementation

#### Use Case Structure
```python
class RegisterUserUseCase:
    """Use case for user registration business logic."""
    
    def __init__(self, db: Session):
        self.user_repo = SQLUserRepository(db)
        self.auth_service = AuthService()
    
    def execute(self, email: str, password: str) -> RegisterResult:
        # Validate input
        self._validate_password(password)
        
        # Check if user exists
        if self.user_repo.get_by_email(email):
            raise EmailAlreadyExistsError()
        
        # Create user
        user = self.user_repo.create(email, password)
        
        # Generate token
        token = self.auth_service.create_token(user)
        
        return RegisterResult(user=user, access_token=token)
```

### Usage in Routers

#### ✅ Clean Presentation Layer
```python
@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Pure presentation layer - no business logic."""
    use_case = RegisterUserUseCase(db)
    
    try:
        result = use_case.execute(email=req.email, password=req.password)
        return TokenResponse(access_token=result.access_token)
    except DomainValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except EmailAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Dependency Injection

### Database Session Management
```python
def get_db():
    """Dependency injection for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Repository Injection (Future Enhancement)
```python
def get_asset_repository(db: Session = Depends(get_db)) -> IAssetRepository:
    """Dependency injection for repositories."""
    return SQLAssetRepository(db)

@router.get("/asset/{symbol}")
def get_asset(
    symbol: str,
    asset_repo: IAssetRepository = Depends(get_asset_repository)
):
    asset = asset_repo.get_by_symbol(symbol)
    # ...
```

## Service Decomposition Pattern

### Problem: Monolithic Service Classes
Large service classes violating Single Responsibility Principle make code hard to maintain, test, and extend.

#### Example of Monolithic Service (Anti-pattern)
```python
# BAD: 700+ line class with multiple responsibilities
class InvestmentDecisionEngine:
    def analyze_fundamentals(self, asset): ...
    def analyze_technicals(self, asset): ...
    def analyze_sentiment(self, asset): ...
    def analyze_momentum(self, asset): ...
    def analyze_risk(self, asset): ...
    def aggregate_signals(self, signals): ...
    def generate_recommendation(self, aggregated): ...
    def identify_risks(self, asset): ...
    def identify_catalysts(self, asset): ...
    def screen_opportunities(self, symbols): ...
    # ... many more methods
```

### Solution: Focused Service Classes
Break down monolithic services into focused, composable services following Single Responsibility Principle.

#### Decomposed Services (Best Practice)
```python
# GOOD: Focused services with single responsibilities

# 1. Signal Analysis Service
class SignalAnalyzer:
    """Responsible ONLY for analyzing individual signals"""
    def analyze_fundamentals(self, asset): ...
    def analyze_technicals(self, asset): ...
    def analyze_momentum(self, asset): ...
    def analyze_risk(self, asset): ...

# 2. Signal Aggregation Service  
class SignalAggregator:
    """Responsible ONLY for combining signals"""
    def aggregate_signals(self, signals, horizon): ...
    def calculate_position_size(self, signal, confidence): ...
    def calculate_entry_exit_targets(self, price, signal): ...

# 3. Recommendation Generation Service
class RecommendationGenerator:
    """Responsible ONLY for generating recommendations"""
    def generate_recommendation(self, asset, signals): ...
    def generate_rationale(self, signal_breakdown): ...
    def identify_risks(self, asset): ...
    def identify_catalysts(self, asset): ...

# 4. Orchestration Service
class InvestmentEngine:
    """Orchestrates the specialized services"""
    def __init__(self, db):
        self.signal_analyzer = SignalAnalyzer(db)
        self.signal_aggregator = SignalAggregator()
        self.recommendation_generator = RecommendationGenerator()
    
    def analyze_investment(self, symbol):
        # Orchestrate the services
        signals = self.signal_analyzer.collect_signals(asset)
        aggregated = self.signal_aggregator.aggregate(signals)
        recommendation = self.recommendation_generator.generate(aggregated)
        return recommendation
```

### Benefits of Service Decomposition

1. **Single Responsibility**: Each service has one clear purpose
2. **Testability**: Services can be tested in isolation
3. **Maintainability**: Changes are localized to specific services
4. **Reusability**: Services can be reused in different contexts
5. **Scalability**: Services can be scaled independently
6. **Team Collaboration**: Different team members can work on different services

### Refactoring Strategy

1. **Identify Responsibilities**: List all responsibilities of the monolithic class
2. **Group Related Methods**: Group methods by responsibility
3. **Extract Services**: Create focused service classes
4. **Define Interfaces**: Create clear interfaces between services
5. **Orchestrate**: Create an orchestrator that coordinates services

## Service Orchestration Pattern

### Overview
The Service Orchestration Pattern coordinates multiple specialized services to accomplish complex tasks. An orchestrator acts as the conductor, delegating work to focused services while maintaining backward compatibility.

### Implementation Example: Return Calculator

#### ❌ BAD: Monolithic Calculator (673 lines)
```python
class ReturnCalculator:
    """Single class handling all return calculations"""
    def calculate_returns(self, values): ...
    def total_return(self, values): ...
    def annualized_return(self, values, days): ...
    def calculate_daily_returns(self, prices): ...
    def calculate_monthly_returns(self, prices): ...
    def excess_returns(self, portfolio, benchmark): ...
    def active_returns(self, portfolio, benchmark): ...
    def calculate_time_weighted_return(self, values, dates, cash_flows): ...
    def calculate_money_weighted_return(self, cash_flows): ...
    # ... 30+ more methods in one class
```

#### ✅ GOOD: Orchestrated Services
```python
# 1. Basic Returns Service (145 lines)
class BasicReturnCalculator:
    """Handles simple and compound returns"""
    def calculate_returns(self, values): ...
    def total_return(self, values): ...
    def calculate_log_returns(self, prices): ...

# 2. Period Returns Service (214 lines)
class PeriodReturnCalculator:
    """Handles time-period specific calculations"""
    def annualized_return(self, values, days): ...
    def calculate_daily_returns(self, prices): ...
    def calculate_ytd_return(self, prices): ...

# 3. Benchmark Returns Service (137 lines)
class BenchmarkReturnCalculator:
    """Handles benchmark comparisons"""
    def excess_returns(self, portfolio, benchmark): ...
    def calculate_tracking_error(self, portfolio, benchmark): ...

# 4. Advanced Returns Service (287 lines)
class AdvancedReturnCalculator:
    """Handles cash flows and complex metrics"""
    def calculate_time_weighted_return(self, values, dates, cash_flows): ...
    def calculate_money_weighted_return(self, cash_flows): ...

# 5. Orchestrator (198 lines)
class ReturnCalculator:
    """Orchestrates specialized calculators"""
    def __init__(self):
        self.basic = BasicReturnCalculator()
        self.period = PeriodReturnCalculator()
        self.benchmark = BenchmarkReturnCalculator()
        self.advanced = AdvancedReturnCalculator()
    
    # Delegate to appropriate service
    def calculate_returns(self, values):
        return self.basic.calculate_returns(values)
    
    def excess_returns(self, portfolio, benchmark):
        return self.benchmark.excess_returns(portfolio, benchmark)
```

### Benefits of Service Orchestration

1. **Separation of Concerns**: Each service handles one domain
2. **Maintainability**: Focused services are easier to understand
3. **Testability**: Services can be mocked independently
4. **Backward Compatibility**: Orchestrator maintains existing API
5. **Flexible Composition**: Services can be mixed and matched

## Benefits of Clean Architecture

### 1. Testability
```python
def test_get_asset():
    # Mock repository
    mock_repo = Mock(spec=IAssetRepository)
    mock_repo.get_by_symbol.return_value = Asset(symbol="AAPL")
    
    # Test business logic without database
    result = service.process_asset(mock_repo, "AAPL")
    assert result.symbol == "AAPL"
```

### 2. Maintainability
- Changes to database schema only affect repository layer
- Business logic remains unchanged
- Easy to locate and fix issues

### 3. Scalability
- Can switch from SQLAlchemy to MongoDB without changing business logic
- Can add caching layer transparently
- Can implement different data sources (API, CSV, etc.)

### 4. Code Organization
```
app/
├── routers/          # Presentation Layer (HTTP endpoints)
├── use_cases/        # Application Layer (business workflows)
├── services/         # Domain Layer (business logic)
├── repositories/     # Data Access Layer (persistence)
└── models/          # Data Models (entities)
```

## Migration Guide

### Step 1: Identify Direct DB Access
```bash
# Find violations
grep -r "db.query(" app/routers/
grep -r "db.add(" app/routers/
grep -r "db.commit(" app/routers/
```

### Step 2: Create Repository
```python
class SQLAssetRepository(IAssetRepository):
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        return self.db.query(Asset).filter(
            Asset.symbol == symbol.upper()
        ).first()
```

### Step 3: Refactor Router
```python
# Before
asset = db.query(Asset).filter(Asset.symbol == symbol).first()

# After
asset_repo = SQLAssetRepository(db)
asset = asset_repo.get_by_symbol(symbol)
```

## Performance Considerations

### N+1 Query Prevention

#### Problem: N+1 Query Pattern
```python
# BAD: N+1 Query Pattern - Makes N+1 database queries
for sym, name, sector in assets_list:
    exists = db.query(Asset).filter(Asset.symbol == sym).first()  # N queries
    if not exists:
        db.add(Asset(symbol=sym, name=name, sector=sector))

# BAD: Another N+1 pattern
for sym in symbols:
    asset = db.query(Asset).filter(Asset.symbol == sym).first()  # N queries
    prices = db.query(Price).filter(Price.asset_id == asset.id).all()  # N more queries
```

#### Solution 1: Batch Query with Dictionary Lookup
```python
# GOOD: Single query for all assets, then dictionary lookup
all_symbols = [sym for sym, _, _ in assets_list]
existing_assets = db.query(Asset.symbol).filter(Asset.symbol.in_(all_symbols)).all()
existing_symbols = {asset.symbol for asset in existing_assets}

# Now check existence in memory (O(1) lookup)
for sym, name, sector in assets_list:
    if sym not in existing_symbols:
        new_assets.append(Asset(symbol=sym, name=name, sector=sector))

# Bulk insert all at once
if new_assets:
    db.bulk_save_objects(new_assets)
```

#### Solution 2: Eager Loading with Relationships
```python
# GOOD: Repository with eager loading
from sqlalchemy.orm import selectinload, joinedload

def get_portfolio_with_allocations(self, portfolio_id: int):
    return self.db.query(Portfolio).options(
        selectinload(Portfolio.allocations)  # Eager load in single query
    ).filter(Portfolio.id == portfolio_id).first()

def get_prices_with_assets(self):
    return self.db.query(Price).options(
        joinedload(Price.asset)  # Join load to avoid N+1
    ).all()
```

#### Solution 3: Batch Processing with Dictionaries
```python
# GOOD: Build lookup dictionary for batch processing
symbols_in_df = list(price_df.columns.levels[0])
assets_dict = {
    asset.symbol: asset 
    for asset in db.query(Asset).filter(Asset.symbol.in_(symbols_in_df)).all()
}

# Process using dictionary (O(1) lookups instead of N queries)
for sym in symbols_in_df:
    asset = assets_dict.get(sym)  # O(1) memory lookup
    if asset:
        process_asset(asset)
```

#### Performance Impact
- **Before**: N+1 queries (e.g., 100 assets = 101 queries)
- **After**: 2 queries (one for batch fetch, one for bulk insert)
- **Improvement**: ~98% reduction in database roundtrips
- **Speed increase**: 10-100x faster for large datasets

### Pagination Support
```python
def get_prices_paginated(
    self,
    asset_id: int,
    offset: int = 0,
    limit: int = 100
) -> List[Price]:
    return self.db.query(Price).filter(
        Price.asset_id == asset_id
    ).offset(offset).limit(limit).all()
```

## Future Improvements

1. **Dependency Injection Container**: Use a DI container for automatic injection
2. **Unit of Work Pattern**: Manage transactions across repositories
3. **Specification Pattern**: Complex query building
4. **CQRS**: Separate read and write models
5. **Event Sourcing**: Audit trail and event-driven architecture

## Compliance Checklist

- [ ] No direct DB queries in routers
- [ ] All data access through repositories
- [ ] Business logic in use cases/services
- [ ] Proper error handling and mapping
- [ ] Repository interfaces defined
- [ ] Pagination support for large datasets
- [ ] Eager loading to prevent N+1 queries
- [ ] Transaction management
- [ ] Proper testing with mocked repositories