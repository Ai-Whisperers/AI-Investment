# Architecture Patterns Documentation

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
```python
# Repository with eager loading
def get_portfolio_with_allocations(self, portfolio_id: int):
    return self.db.query(Portfolio).options(
        selectinload(Portfolio.allocations)
    ).filter(Portfolio.id == portfolio_id).first()
```

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