# 🚨 TECHNICAL DEBT RESOLUTION TODO LIST
*Last Updated: 2025-01-26 | Status: 1/22 items completed*

---

## 📋 **OVERVIEW**
This document contains the **exhaustive, detailed implementation plan** for resolving all technical debt identified in the comprehensive codebase analysis. Each item includes specific implementation steps, affected files, testing requirements, and acceptance criteria.

**Context**: Following comprehensive technical debt analysis, 22 critical issues were identified that must be resolved for production-scale deployment and long-term maintainability.

---

## 🔥 **CRITICAL PRIORITY** - *BLOCKING DEPLOYMENT*

### ✅ **ITEM 13: OAuth CSRF Security Fix** 
**Status**: ✅ **COMPLETED** | **Priority**: CRITICAL | **Effort**: 2-3 days
- **Issue**: OAuth state validation relied on client-side cookies (CSRF vulnerable)
- **Solution**: Implemented server-side Redis state management
- **Files Modified**: `apps/api/app/routers/auth.py`
- **Security Impact**: Eliminated CSRF attack vector

---

### **ITEM 10: Fix Clean Architecture Violations**
**Status**: 🔄 **IN PROGRESS** | **Priority**: CRITICAL | **Effort**: 1-2 weeks
**Progress**: 40% Complete - Technical Analysis and Authentication endpoints refactored (2/5 major areas completed)

#### **Problem Analysis**
- **Location**: `apps/api/app/routers/analysis.py:25-96`, `apps/api/app/routers/auth.py:51-76`
- **Issue**: Domain business logic embedded directly in presentation layer (router endpoints)
- **Impact**: Violates Clean Architecture principles, makes testing impossible, creates tight coupling
- **Root Cause**: Business logic mixed with HTTP handling concerns

#### **Detailed Implementation Plan**

##### **Step 1: Create Domain Service Layer (2-3 days)**
```python
# NEW FILE: apps/api/app/services/domain/analysis_service.py
class TechnicalAnalysisService:
    """Domain service for technical analysis operations."""
    
    def __init__(self, price_repository: IPriceRepository):
        self.price_repository = price_repository
    
    def calculate_rsi(self, symbol: str, period: int = 14) -> float:
        """Calculate RSI indicator - pure business logic"""
        # Move logic from router here
        pass
    
    def calculate_moving_average(self, symbol: str, period: int) -> float:
        """Calculate moving average - pure business logic"""
        # Move logic from router here
        pass
```

##### **Step 2: Create Application Use Cases (2-3 days)**
```python
# NEW FILE: apps/api/app/use_cases/get_technical_analysis.py
class GetTechnicalAnalysisUseCase:
    """Application use case for getting technical analysis."""
    
    def __init__(self, analysis_service: TechnicalAnalysisService):
        self.analysis_service = analysis_service
    
    async def execute(self, request: TechnicalAnalysisRequest) -> TechnicalAnalysisResponse:
        """Execute the use case with validation and orchestration"""
        # Input validation
        # Business logic coordination
        # Response formatting
        pass
```

##### **Step 3: Refactor Router to Pure Presentation (1-2 days)**
```python
# MODIFY: apps/api/app/routers/analysis.py
@router.get("/technical/{symbol}")
async def get_technical_analysis(
    symbol: str,
    use_case: GetTechnicalAnalysisUseCase = Depends()
) -> TechnicalAnalysisResponse:
    """Pure presentation layer - no business logic"""
    try:
        request = TechnicalAnalysisRequest(symbol=symbol)
        return await use_case.execute(request)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### **Files to Create/Modify**
- **NEW**: `apps/api/app/services/domain/analysis_service.py`
- **NEW**: `apps/api/app/services/domain/auth_service.py`
- **NEW**: `apps/api/app/use_cases/get_technical_analysis.py`
- **NEW**: `apps/api/app/use_cases/authenticate_user.py`
- **MODIFY**: `apps/api/app/routers/analysis.py` (remove business logic)
- **MODIFY**: `apps/api/app/routers/auth.py` (remove business logic)
- **NEW**: `apps/api/app/schemas/use_case_requests.py`
- **NEW**: `apps/api/app/schemas/use_case_responses.py`

#### **Testing Requirements**
- [ ] Unit tests for domain services (isolated business logic)
- [ ] Unit tests for use cases (application orchestration)
- [ ] Integration tests for router endpoints (HTTP layer only)
- [ ] Test coverage must increase to 60%+

#### **Acceptance Criteria**
- [ ] No business logic in router files
- [ ] Domain services are pure business logic (no HTTP, DB, external dependencies)
- [ ] Use cases orchestrate domain services
- [ ] Routers only handle HTTP concerns (validation, status codes, serialization)
- [ ] All existing functionality preserved
- [ ] All tests passing

---

### **ITEM 11: Implement Repository Pattern**
**Status**: 🔄 **PENDING** | **Priority**: CRITICAL | **Effort**: 2-3 weeks

#### **Problem Analysis**
- **Location**: Throughout `apps/api/app/routers/` - multiple files
- **Issue**: Direct SQLAlchemy ORM queries in presentation layer
- **Impact**: Violates Dependency Inversion Principle, makes testing impossible
- **Root Cause**: No abstraction layer between business logic and data persistence

#### **Detailed Implementation Plan**

##### **Step 1: Define Domain Interfaces (2-3 days)**
```python
# NEW FILE: apps/api/app/domain/repositories/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.asset import Asset
from ..entities.price import Price

class IAssetRepository(ABC):
    """Asset repository interface - defines contract"""
    
    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get asset by symbol"""
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100) -> List[Asset]:
        """Get all assets with pagination"""
        pass
    
    @abstractmethod
    async def create(self, asset: Asset) -> Asset:
        """Create new asset"""
        pass

class IPriceRepository(ABC):
    """Price repository interface"""
    
    @abstractmethod
    async def get_price_history(
        self, 
        symbol: str, 
        days: int = 30,
        eager_load: bool = True
    ) -> List[Price]:
        """Get price history with eager loading to prevent N+1"""
        pass
```

##### **Step 2: Create Domain Entities (1-2 days)**
```python
# NEW FILE: apps/api/app/domain/entities/asset.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Asset:
    """Pure domain entity - no ORM dependencies"""
    symbol: str
    name: str
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    prices: List['Price'] = None
    
    def __post_init__(self):
        if self.prices is None:
            self.prices = []
```

##### **Step 3: Implement Infrastructure Repository (3-4 days)**
```python
# NEW FILE: apps/api/app/infrastructure/repositories/sqlalchemy_asset_repository.py
from sqlalchemy.orm import Session, joinedload
from ...domain.repositories.interfaces import IAssetRepository
from ...domain.entities.asset import Asset
from ...models.asset import Asset as AssetModel

class SQLAlchemyAssetRepository(IAssetRepository):
    """SQLAlchemy implementation of asset repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get asset with eager loading to prevent N+1 queries"""
        model = (
            self.db.query(AssetModel)
            .options(joinedload(AssetModel.prices))
            .filter_by(symbol=symbol)
            .first()
        )
        return self._to_entity(model) if model else None
    
    def _to_entity(self, model: AssetModel) -> Asset:
        """Convert ORM model to domain entity"""
        return Asset(
            symbol=model.symbol,
            name=model.name,
            sector=model.sector,
            market_cap=model.market_cap,
            prices=[self._price_to_entity(p) for p in model.prices]
        )
```

##### **Step 4: Update Dependency Injection (2 days)**
```python
# MODIFY: apps/api/app/core/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from .database import get_db
from ..infrastructure.repositories.sqlalchemy_asset_repository import SQLAlchemyAssetRepository
from ..domain.repositories.interfaces import IAssetRepository

def get_asset_repository(db: Session = Depends(get_db)) -> IAssetRepository:
    """Dependency injection for asset repository"""
    return SQLAlchemyAssetRepository(db)
```

##### **Step 5: Remove Direct ORM from Routers (3-4 days)**
```python
# MODIFY: apps/api/app/routers/analysis.py
@router.get("/assets/{symbol}")
async def get_asset(
    symbol: str,
    asset_repo: IAssetRepository = Depends(get_asset_repository)
):
    """Router now uses repository interface - no direct ORM"""
    asset = await asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset
```

#### **Files to Create/Modify**
- **NEW**: `apps/api/app/domain/repositories/interfaces.py`
- **NEW**: `apps/api/app/domain/entities/asset.py`
- **NEW**: `apps/api/app/domain/entities/price.py`
- **NEW**: `apps/api/app/domain/entities/user.py`
- **NEW**: `apps/api/app/infrastructure/repositories/sqlalchemy_asset_repository.py`
- **NEW**: `apps/api/app/infrastructure/repositories/sqlalchemy_price_repository.py`
- **NEW**: `apps/api/app/infrastructure/repositories/sqlalchemy_user_repository.py`
- **MODIFY**: All router files to use repositories instead of direct ORM
- **NEW**: `apps/api/app/core/dependencies.py` (repository dependency injection)

#### **Testing Requirements**
- [ ] Unit tests for repository interfaces (mocked implementations)
- [ ] Unit tests for domain entities (business rules)
- [ ] Integration tests for SQLAlchemy repositories (real database)
- [ ] Router tests using mocked repositories
- [ ] Performance tests to verify N+1 query resolution

#### **Acceptance Criteria**
- [ ] Zero direct SQLAlchemy queries in router files
- [ ] All data access goes through repository interfaces
- [ ] Domain entities are pure (no ORM dependencies)
- [ ] Repository implementations handle all ORM concerns
- [ ] N+1 query patterns eliminated with eager loading
- [ ] All existing functionality preserved

---

## 🔴 **HIGH PRIORITY** - *PERFORMANCE & MAINTAINABILITY*

### **ITEM 12: Break Down Monolithic Investment Engine**
**Status**: 🔄 **PENDING** | **Priority**: HIGH | **Effort**: 2-3 weeks

#### **Problem Analysis**
- **Location**: `apps/api/app/services/investment_engine.py` (735 lines)
- **Issue**: Single class handling analysis, recommendations, signals, risk assessment
- **Impact**: Violates Single Responsibility Principle, impossible to test/maintain
- **Root Cause**: God class anti-pattern

#### **Detailed Implementation Plan**

##### **Step 1: Extract Signal Analysis Service (4-5 days)**
```python
# NEW FILE: apps/api/app/services/analysis/signal_analyzer.py
class SignalAnalyzer:
    """Focused class for signal analysis only"""
    
    def __init__(self, price_repo: IPriceRepository, news_repo: INewsRepository):
        self.price_repo = price_repo
        self.news_repo = news_repo
    
    def analyze_technical_signals(self, symbol: str) -> TechnicalSignals:
        """Analyze technical indicators - 50-75 lines max"""
        pass
    
    def analyze_fundamental_signals(self, symbol: str) -> FundamentalSignals:
        """Analyze fundamental data - 50-75 lines max"""
        pass
    
    def analyze_sentiment_signals(self, symbol: str) -> SentimentSignals:
        """Analyze news/social sentiment - 50-75 lines max"""
        pass
```

##### **Step 2: Extract Recommendation Generator (4-5 days)**
```python
# NEW FILE: apps/api/app/services/recommendations/recommendation_generator.py
class RecommendationGenerator:
    """Focused class for generating investment recommendations"""
    
    def __init__(self, signal_analyzer: SignalAnalyzer, risk_assessor: RiskAssessor):
        self.signal_analyzer = signal_analyzer
        self.risk_assessor = risk_assessor
    
    def generate_recommendation(self, symbol: str) -> InvestmentRecommendation:
        """Generate buy/hold/sell recommendation - 75-100 lines max"""
        # Combine signals from analyzer
        # Apply risk constraints from assessor
        # Generate final recommendation
        pass
    
    def calculate_position_size(self, symbol: str, portfolio_value: float) -> float:
        """Calculate optimal position size - 30-50 lines max"""
        pass
```

##### **Step 3: Extract Risk Assessor (3-4 days)**
```python
# NEW FILE: apps/api/app/services/risk/risk_assessor.py
class RiskAssessor:
    """Focused class for risk assessment"""
    
    def assess_volatility_risk(self, symbol: str) -> VolatilityRisk:
        """Assess price volatility risk - 40-60 lines max"""
        pass
    
    def assess_correlation_risk(self, symbol: str, portfolio: Portfolio) -> CorrelationRisk:
        """Assess portfolio correlation risk - 40-60 lines max"""
        pass
    
    def assess_concentration_risk(self, symbol: str, portfolio: Portfolio) -> ConcentrationRisk:
        """Assess position concentration risk - 30-50 lines max"""
        pass
```

##### **Step 4: Create Investment Orchestrator (2-3 days)**
```python
# NEW FILE: apps/api/app/services/investment/investment_orchestrator.py
class InvestmentOrchestrator:
    """Lightweight orchestrator - coordinates focused services"""
    
    def __init__(
        self, 
        signal_analyzer: SignalAnalyzer,
        recommendation_generator: RecommendationGenerator,
        risk_assessor: RiskAssessor
    ):
        self.signal_analyzer = signal_analyzer
        self.recommendation_generator = recommendation_generator
        self.risk_assessor = risk_assessor
    
    async def get_investment_analysis(self, symbol: str) -> InvestmentAnalysis:
        """Orchestrate the investment analysis process - 50-75 lines max"""
        # This replaces the 735-line monolithic class
        signals = await self.signal_analyzer.analyze_all_signals(symbol)
        risk_assessment = await self.risk_assessor.assess_all_risks(symbol)
        recommendation = await self.recommendation_generator.generate_recommendation(
            symbol, signals, risk_assessment
        )
        
        return InvestmentAnalysis(
            signals=signals,
            risk_assessment=risk_assessment,
            recommendation=recommendation
        )
```

##### **Step 5: Update All Dependencies (2-3 days)**
```python
# MODIFY: apps/api/app/routers/investment.py
@router.post("/analyze/{symbol}")
async def analyze_investment(
    symbol: str,
    orchestrator: InvestmentOrchestrator = Depends(get_investment_orchestrator)
):
    """Router now uses orchestrator instead of monolithic engine"""
    return await orchestrator.get_investment_analysis(symbol)
```

#### **Files to Create/Modify**
- **DELETE**: `apps/api/app/services/investment_engine.py` (735 lines → 0 lines)
- **NEW**: `apps/api/app/services/analysis/signal_analyzer.py` (~150 lines)
- **NEW**: `apps/api/app/services/recommendations/recommendation_generator.py` (~200 lines)
- **NEW**: `apps/api/app/services/risk/risk_assessor.py` (~150 lines)
- **NEW**: `apps/api/app/services/investment/investment_orchestrator.py` (~100 lines)
- **NEW**: `apps/api/app/schemas/investment_analysis.py` (data transfer objects)
- **MODIFY**: All router files using investment engine
- **MODIFY**: Dependency injection configuration

#### **Testing Requirements**
- [ ] Unit tests for each focused service (easier to test smaller classes)
- [ ] Unit tests for orchestrator (mocked dependencies)
- [ ] Integration tests for full investment analysis flow
- [ ] Performance tests to ensure no regression
- [ ] Test coverage should reach 70%+ (easier with smaller classes)

#### **Acceptance Criteria**
- [ ] No single class over 200 lines
- [ ] Each service has single, focused responsibility
- [ ] Services are loosely coupled through interfaces
- [ ] Orchestrator coordinates services without business logic
- [ ] All existing functionality preserved
- [ ] Performance equal or better than monolithic version

---

### **ITEM 14: Resolve N+1 Query Patterns**
**Status**: 🔄 **PENDING** | **Priority**: HIGH | **Effort**: 1 week

#### **Problem Analysis**
- **Location**: `apps/api/app/services/strategy.py:105-109`
- **Issue**: Loading assets and prices separately in loops causes N+1 queries
- **Impact**: Poor database performance, slow response times under load
- **Root Cause**: Missing eager loading and inefficient query patterns

#### **Detailed Implementation Plan**

##### **Step 1: Identify All N+1 Patterns (1 day)**
```python
# AUDIT: Find all patterns like this in codebase
def get_portfolio_data(portfolio_id: int):
    portfolio = db.query(Portfolio).filter_by(id=portfolio_id).first()  # 1 query
    
    assets = []
    for allocation in portfolio.allocations:  # N queries (one per allocation)
        asset = db.query(Asset).filter_by(id=allocation.asset_id).first()
        asset.prices = db.query(Price).filter_by(asset_id=asset.id).all()  # Another N queries
        assets.append(asset)
    
    return assets  # Total: 1 + N + N = 1 + 2N queries instead of 1
```

##### **Step 2: Implement Eager Loading (2-3 days)**
```python
# MODIFY: apps/api/app/services/strategy.py
from sqlalchemy.orm import joinedload, selectinload

def get_portfolio_data_optimized(portfolio_id: int):
    """Optimized version with eager loading"""
    portfolio = (
        db.query(Portfolio)
        .options(
            joinedload(Portfolio.allocations)
            .joinedload(Allocation.asset)
            .joinedload(Asset.prices)
        )
        .filter_by(id=portfolio_id)
        .first()
    )  # Single query with joins - eliminates N+1
    
    return portfolio.allocations  # All data already loaded
```

##### **Step 3: Add Query Performance Monitoring (1-2 days)**
```python
# NEW FILE: apps/api/app/utils/query_monitor.py
import logging
from sqlalchemy.event import listen
from sqlalchemy.engine import Engine
import time

logger = logging.getLogger(__name__)

@listen(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@listen(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log slow queries
        logger.warning(f"Slow query detected: {total:.3f}s - {statement[:100]}...")
```

##### **Step 4: Batch Loading for Complex Queries (2-3 days)**
```python
# NEW FILE: apps/api/app/utils/batch_loader.py
class BatchLoader:
    """Batch loader to prevent N+1 queries in complex scenarios"""
    
    def __init__(self, db: Session):
        self.db = db
        self._asset_cache = {}
        self._price_cache = {}
    
    async def load_assets_batch(self, asset_ids: List[int]) -> Dict[int, Asset]:
        """Load multiple assets in single query"""
        if not asset_ids:
            return {}
            
        assets = (
            self.db.query(Asset)
            .filter(Asset.id.in_(asset_ids))
            .all()
        )
        return {asset.id: asset for asset in assets}
    
    async def load_prices_batch(self, asset_ids: List[int], days: int = 30) -> Dict[int, List[Price]]:
        """Load prices for multiple assets in single query"""
        prices = (
            self.db.query(Price)
            .filter(
                Price.asset_id.in_(asset_ids),
                Price.date >= datetime.now() - timedelta(days=days)
            )
            .order_by(Price.asset_id, Price.date)
            .all()
        )
        
        # Group by asset_id
        result = {}
        for price in prices:
            if price.asset_id not in result:
                result[price.asset_id] = []
            result[price.asset_id].append(price)
        
        return result
```

#### **Files to Create/Modify**
- **MODIFY**: `apps/api/app/services/strategy.py` (add eager loading)
- **MODIFY**: `apps/api/app/services/portfolio.py` (fix query patterns)
- **MODIFY**: `apps/api/app/routers/analysis.py` (optimize data loading)
- **NEW**: `apps/api/app/utils/query_monitor.py` (performance monitoring)
- **NEW**: `apps/api/app/utils/batch_loader.py` (batch loading utilities)
- **MODIFY**: All repository implementations (add eager loading options)

#### **Testing Requirements**
- [ ] Performance tests comparing before/after query counts
- [ ] Load tests to verify scalability improvements
- [ ] Unit tests for batch loader functionality
- [ ] Integration tests for all optimized queries
- [ ] Database query logging in test environment

#### **Acceptance Criteria**
- [ ] No N+1 query patterns in codebase
- [ ] All related data loaded with eager loading or batching
- [ ] API response times improved by 50%+ under load
- [ ] Query monitoring shows <2 queries per request average
- [ ] All existing functionality preserved

---

## 🟡 **MEDIUM PRIORITY** - *CODE QUALITY & SECURITY*

### **ITEM 17: Add Missing Admin Authentication**
**Status**: 🔄 **PENDING** | **Priority**: MEDIUM | **Effort**: 3-5 days

#### **Problem Analysis**
- **Location**: `apps/api/app/routers/websocket.py:285`
- **Issue**: Admin endpoints with TODO comments, no authentication
- **Impact**: Security exposure, potential unauthorized access
- **Root Cause**: Incomplete authentication implementation

#### **Detailed Implementation Plan**

##### **Step 1: Create Admin Authentication Middleware (2 days)**
```python
# NEW FILE: apps/api/app/middleware/admin_auth.py
from fastapi import HTTPException, Depends, status
from ..utils.token_dep import get_current_user
from ..models.user import User

async def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Middleware to require admin privileges"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user cannot access admin endpoints"
        )
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

async def require_super_admin(current_user: User = Depends(require_admin_user)) -> User:
    """Middleware for super admin only endpoints"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    
    return current_user
```

##### **Step 2: Update User Model with Admin Fields (1 day)**
```python
# MODIFY: apps/api/app/models/user.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # NEW
    is_super_admin = Column(Boolean, default=False)  # NEW
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
```

##### **Step 3: Secure WebSocket Admin Endpoints (1-2 days)**
```python
# MODIFY: apps/api/app/routers/websocket.py
@router.post("/admin/broadcast")
async def admin_broadcast_message(
    message: AdminBroadcastRequest,
    admin_user: User = Depends(require_admin_user)  # NEW: Authentication required
):
    """Admin endpoint to broadcast message - now secured"""
    await websocket_manager.broadcast({
        "type": "admin_message",
        "message": message.content,
        "sent_by": admin_user.email,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"status": "Message broadcasted successfully"}

@router.delete("/admin/connections/{connection_id}")
async def admin_disconnect_user(
    connection_id: str,
    admin_user: User = Depends(require_super_admin)  # NEW: Super admin only
):
    """Admin endpoint to disconnect user - now secured"""
    success = await websocket_manager.disconnect_user(connection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {"status": "User disconnected successfully"}
```

##### **Step 4: Create Admin Management Endpoints (1-2 days)**
```python
# NEW FILE: apps/api/app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from ..middleware.admin_auth import require_super_admin
from ..schemas.admin import AdminUserRequest, AdminUserResponse

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: int,
    admin_user: User = Depends(require_super_admin)
):
    """Promote user to admin - super admin only"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_admin = True
    db.commit()
    
    return {"status": "User promoted to admin successfully"}

@router.get("/system/health")
async def admin_system_health(
    admin_user: User = Depends(require_admin_user)
):
    """Admin-only system health endpoint"""
    return {
        "status": "healthy",
        "active_connections": websocket_manager.get_connection_count(),
        "database_status": "connected",
        "redis_status": redis_client.health_check()
    }
```

#### **Files to Create/Modify**
- **NEW**: `apps/api/app/middleware/admin_auth.py`
- **NEW**: `apps/api/app/routers/admin.py`
- **NEW**: `apps/api/app/schemas/admin.py`
- **MODIFY**: `apps/api/app/models/user.py` (add admin fields)
- **MODIFY**: `apps/api/app/routers/websocket.py` (secure admin endpoints)
- **NEW**: Database migration for admin fields
- **MODIFY**: `apps/api/app/main.py` (include admin router)

#### **Testing Requirements**
- [ ] Unit tests for admin authentication middleware
- [ ] Integration tests for admin endpoints
- [ ] Security tests for unauthorized access attempts
- [ ] Admin user creation and promotion tests

#### **Acceptance Criteria**
- [ ] All admin endpoints require authentication
- [ ] Proper HTTP status codes for unauthorized access
- [ ] Admin user management functionality
- [ ] No TODO comments in production code
- [ ] Security audit passing for admin features

---

### **ITEM 15: Split Oversized Service Files**
**Status**: 🔄 **PENDING** | **Priority**: MEDIUM | **Effort**: 2-3 weeks

#### **Problem Analysis**
- **Location**: 
  - `apps/api/app/services/performance_modules/return_calculator.py` (672 lines)
  - `apps/api/app/services/strategy_modules/weight_calculator.py` (663 lines)
- **Issue**: Single files handling multiple related but distinct responsibilities
- **Impact**: Difficult to maintain, test, and understand
- **Root Cause**: Logical cohesion without proper separation of concerns

#### **Detailed Implementation Plan**

##### **Step 1: Analyze and Plan Return Calculator Split (2-3 days)**
```python
# ANALYSIS: Current return_calculator.py structure
# - Basic return calculations (100 lines)
# - Compound return calculations (120 lines)  
# - Risk-adjusted returns (150 lines)
# - Benchmark comparisons (100 lines)
# - Performance metrics (100 lines)
# - Utility functions (102 lines)

# PLAN: Split into focused modules
```

##### **Step 2: Extract Basic Return Calculator (3-4 days)**
```python
# NEW FILE: apps/api/app/services/returns/basic_return_calculator.py
class BasicReturnCalculator:
    """Focused on basic return calculations only"""
    
    def calculate_simple_return(self, initial_value: float, final_value: float) -> float:
        """Calculate simple return percentage"""
        if initial_value == 0:
            raise ValueError("Initial value cannot be zero")
        return ((final_value - initial_value) / initial_value) * 100
    
    def calculate_logarithmic_return(self, initial_value: float, final_value: float) -> float:
        """Calculate logarithmic return"""
        if initial_value <= 0 or final_value <= 0:
            raise ValueError("Values must be positive for log returns")
        return np.log(final_value / initial_value)
    
    def calculate_period_returns(self, prices: List[float]) -> List[float]:
        """Calculate period-over-period returns"""
        if len(prices) < 2:
            return []
        
        returns = []
        for i in range(1, len(prices)):
            period_return = self.calculate_simple_return(prices[i-1], prices[i])
            returns.append(period_return)
        
        return returns
    
    # ~80-100 lines total - focused responsibility
```

##### **Step 3: Extract Risk-Adjusted Return Calculator (3-4 days)**
```python
# NEW FILE: apps/api/app/services/returns/risk_adjusted_calculator.py
class RiskAdjustedReturnCalculator:
    """Focused on risk-adjusted return metrics"""
    
    def __init__(self, basic_calculator: BasicReturnCalculator):
        self.basic_calculator = basic_calculator
    
    def calculate_sharpe_ratio(
        self, 
        returns: List[float], 
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe ratio"""
        if not returns:
            return 0.0
            
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
            
        return (mean_return - risk_free_rate) / std_return
    
    def calculate_sortino_ratio(
        self, 
        returns: List[float], 
        target_return: float = 0.0
    ) -> float:
        """Calculate Sortino ratio (downside deviation only)"""
        if not returns:
            return 0.0
            
        mean_return = np.mean(returns)
        downside_returns = [r for r in returns if r < target_return]
        
        if not downside_returns:
            return float('inf')
            
        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return 0.0
            
        return (mean_return - target_return) / downside_deviation
    
    # ~120-150 lines total - focused on risk metrics
```

##### **Step 4: Extract Weight Calculator Components (4-5 days)**
```python
# NEW FILE: apps/api/app/services/weights/constraint_calculator.py
class ConstraintCalculator:
    """Handle weight constraints and bounds"""
    
    def apply_weight_constraints(
        self, 
        weights: np.ndarray, 
        min_weight: float = 0.01,
        max_weight: float = 0.20
    ) -> np.ndarray:
        """Apply min/max weight constraints"""
        # Ensure weights are within bounds
        constrained_weights = np.clip(weights, min_weight, max_weight)
        
        # Normalize to sum to 1.0
        total = np.sum(constrained_weights)
        if total > 0:
            constrained_weights = constrained_weights / total
        
        return constrained_weights
    
    def validate_weight_constraints(self, weights: np.ndarray) -> bool:
        """Validate that weights meet all constraints"""
        # Check sum to 1.0
        if not np.isclose(np.sum(weights), 1.0, rtol=1e-5):
            return False
            
        # Check no negative weights
        if np.any(weights < 0):
            return False
            
        # Check max concentration
        if np.max(weights) > 0.25:  # No single position > 25%
            return False
            
        return True
    
    # ~100-120 lines total - focused on constraints
```

##### **Step 5: Create Orchestrator Services (2-3 days)**
```python
# NEW FILE: apps/api/app/services/returns/return_calculator_orchestrator.py
class ReturnCalculatorOrchestrator:
    """Lightweight orchestrator for return calculations"""
    
    def __init__(
        self,
        basic_calculator: BasicReturnCalculator,
        risk_calculator: RiskAdjustedReturnCalculator,
        benchmark_calculator: BenchmarkReturnCalculator
    ):
        self.basic_calculator = basic_calculator
        self.risk_calculator = risk_calculator
        self.benchmark_calculator = benchmark_calculator
    
    def calculate_complete_analysis(
        self, 
        prices: List[float],
        benchmark_prices: List[float] = None
    ) -> CompleteReturnAnalysis:
        """Orchestrate complete return analysis"""
        # Basic calculations
        returns = self.basic_calculator.calculate_period_returns(prices)
        total_return = self.basic_calculator.calculate_total_return(prices)
        
        # Risk-adjusted metrics
        sharpe_ratio = self.risk_calculator.calculate_sharpe_ratio(returns)
        sortino_ratio = self.risk_calculator.calculate_sortino_ratio(returns)
        
        # Benchmark comparison (if provided)
        alpha = None
        beta = None
        if benchmark_prices:
            alpha, beta = self.benchmark_calculator.calculate_alpha_beta(
                prices, benchmark_prices
            )
        
        return CompleteReturnAnalysis(
            total_return=total_return,
            period_returns=returns,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            alpha=alpha,
            beta=beta
        )
    
    # ~80-100 lines total - pure orchestration
```

#### **Files to Create/Modify**
- **DELETE**: `return_calculator.py` (672 lines)
- **DELETE**: `weight_calculator.py` (663 lines) 
- **NEW**: `basic_return_calculator.py` (~100 lines)
- **NEW**: `risk_adjusted_calculator.py` (~150 lines)
- **NEW**: `benchmark_calculator.py` (~120 lines)
- **NEW**: `return_calculator_orchestrator.py` (~100 lines)
- **NEW**: `constraint_calculator.py` (~120 lines)
- **NEW**: `optimization_calculator.py` (~140 lines)
- **NEW**: `weight_calculator_orchestrator.py` (~100 lines)
- **MODIFY**: All files importing the old monolithic services

#### **Testing Requirements**
- [ ] Unit tests for each focused calculator (easier testing)
- [ ] Unit tests for orchestrator services
- [ ] Integration tests ensuring all functionality preserved
- [ ] Performance tests (should be same or better)
- [ ] Migration tests for existing data

#### **Acceptance Criteria**  
- [ ] No file over 200 lines
- [ ] Each service has single, focused responsibility
- [ ] All existing functionality preserved
- [ ] Test coverage maintained or improved
- [ ] No performance regression
- [ ] Clean import structure

---

### **ITEM 16: Implement Proper Error Boundaries**
**Status**: 🔄 **PENDING** | **Priority**: MEDIUM | **Effort**: 1-2 weeks

#### **Problem Analysis**
- **Location**: Throughout codebase - multiple files
- **Issue**: Generic exception handling without specific error recovery
- **Impact**: Poor user experience, difficult debugging, cascading failures
- **Root Cause**: No comprehensive error handling strategy

#### **Detailed Implementation Plan**

##### **Step 1: Define Custom Exception Hierarchy (2-3 days)**
```python
# NEW FILE: apps/api/app/exceptions/base.py
class WaardhavenException(Exception):
    """Base exception for all Waardhaven-specific errors"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

# NEW FILE: apps/api/app/exceptions/business.py
class InvestmentAnalysisError(WaardhavenException):
    """Raised when investment analysis fails"""
    pass

class InsufficientDataError(WaardhavenException):
    """Raised when not enough data for analysis"""
    pass

class InvalidPortfolioError(WaardhavenException):
    """Raised when portfolio validation fails"""
    pass

# NEW FILE: apps/api/app/exceptions/external.py
class ExternalAPIError(WaardhavenException):
    """Raised when external API calls fail"""
    pass

class DataProviderError(ExternalAPIError):
    """Raised when data provider (TwelveData, MarketAux) fails"""
    pass

class RateLimitExceededError(ExternalAPIError):
    """Raised when API rate limits are exceeded"""
    pass
```

##### **Step 2: Create Global Exception Handler (2-3 days)**
```python
# NEW FILE: apps/api/app/middleware/exception_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..exceptions.base import WaardhavenException
from ..exceptions.external import ExternalAPIError, RateLimitExceededError
from ..exceptions.business import InsufficientDataError
import logging

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler with proper error responses"""
    
    # Handle custom business exceptions
    if isinstance(exc, InsufficientDataError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "suggestion": "Please provide more historical data or try a different time period"
                }
            }
        )
    
    # Handle external API errors
    if isinstance(exc, RateLimitExceededError):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "type": exc.error_code,
                    "message": "API rate limit exceeded",
                    "details": exc.details,
                    "retry_after": 60  # seconds
                }
            }
        )
    
    if isinstance(exc, ExternalAPIError):
        logger.error(f"External API error: {exc.message}", extra=exc.details)
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "type": exc.error_code,
                    "message": "External service temporarily unavailable",
                    "suggestion": "Please try again in a few minutes"
                }
            }
        )
    
    # Handle all other Waardhaven exceptions
    if isinstance(exc, WaardhavenException):
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": exc.error_code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
    
    # Handle validation errors
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "ValidationError",
                    "message": str(exc),
                    "suggestion": "Please check your input parameters"
                }
            }
        )
    
    # Log unexpected errors
    logger.exception("Unexpected error occurred", exc_info=exc)
    
    # Generic error response (don't expose internals)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "InternalError",
                "message": "An unexpected error occurred",
                "suggestion": "Please try again or contact support if the problem persists"
            }
        }
    )
```

##### **Step 3: Implement Circuit Breaker Pattern (3-4 days)**
```python
# NEW FILE: apps/api/app/utils/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any
import asyncio
import logging

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit tripped, failing fast
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker pattern for external service calls"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
        self.logger = logging.getLogger(__name__)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise ExternalAPIError(
                    "Service is currently unavailable (circuit breaker open)",
                    error_code="CircuitBreakerOpen",
                    details={
                        "failure_count": self.failure_count,
                        "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
                    }
                )
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise ExternalAPIError(
                f"Service call failed: {str(e)}",
                error_code="ServiceCallFailed",
                details={"original_error": str(e)}
            )
    
    def _on_success(self):
        """Reset failure count on success"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failure - increment count and potentially trip circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit"""
        return (
            self.last_failure_time and
            datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
```

##### **Step 4: Add Retry Logic with Exponential Backoff (2-3 days)**
```python
# NEW FILE: apps/api/app/utils/retry.py
import asyncio
import random
from typing import Callable, Any, Type
from ..exceptions.external import RateLimitExceededError

class RetryConfig:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (ConnectionError, TimeoutError)
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

async def retry_with_backoff(func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
    """Retry function with exponential backoff"""
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            return result
            
        except RateLimitExceededError:
            # Don't retry rate limit errors immediately
            raise
            
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts - 1:
                # Last attempt failed
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                config.initial_delay * (config.backoff_multiplier ** attempt),
                config.max_delay
            )
            
            # Add jitter to prevent thundering herd
            if config.jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            await asyncio.sleep(delay)
    
    # All attempts failed
    raise ExternalAPIError(
        f"Function failed after {config.max_attempts} attempts",
        error_code="RetryExhausted",
        details={
            "attempts": config.max_attempts,
            "last_error": str(last_exception)
        }
    ) from last_exception
```

##### **Step 5: Update Services with Error Boundaries (3-4 days)**
```python
# MODIFY: apps/api/app/services/twelvedata.py
class TwelveDataService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=300,  # 5 minutes
            expected_exception=(httpx.HTTPError, httpx.TimeoutException)
        )
        self.retry_config = RetryConfig(max_attempts=3)
    
    async def get_stock_price(self, symbol: str) -> StockPrice:
        """Get stock price with error boundaries"""
        try:
            # Use circuit breaker and retry logic
            result = await self.circuit_breaker.call(
                retry_with_backoff,
                self._fetch_price_data,
                self.retry_config,
                symbol
            )
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitExceededError(
                    "TwelveData API rate limit exceeded",
                    error_code="TwelveDataRateLimit",
                    details={"symbol": symbol, "status_code": 429}
                )
            elif e.response.status_code == 404:
                raise InsufficientDataError(
                    f"No data available for symbol {symbol}",
                    error_code="SymbolNotFound",
                    details={"symbol": symbol}
                )
            else:
                raise DataProviderError(
                    f"TwelveData API error: {e.response.status_code}",
                    error_code="TwelveDataAPIError",
                    details={"symbol": symbol, "status_code": e.response.status_code}
                )
                
        except Exception as e:
            raise DataProviderError(
                f"Unexpected error fetching data for {symbol}",
                error_code="TwelveDataUnexpectedError",
                details={"symbol": symbol, "error": str(e)}
            ) from e
```

#### **Files to Create/Modify**
- **NEW**: `apps/api/app/exceptions/` (complete exception hierarchy)
- **NEW**: `apps/api/app/middleware/exception_handler.py`
- **NEW**: `apps/api/app/utils/circuit_breaker.py`
- **NEW**: `apps/api/app/utils/retry.py`
- **MODIFY**: All service files to use new exception handling
- **MODIFY**: `apps/api/app/main.py` (add global exception handler)
- **NEW**: `apps/api/app/schemas/error_responses.py`

#### **Testing Requirements**
- [ ] Unit tests for all exception types
- [ ] Unit tests for circuit breaker functionality
- [ ] Unit tests for retry logic
- [ ] Integration tests for error scenarios
- [ ] Load tests to verify error handling under stress

#### **Acceptance Criteria**
- [ ] Comprehensive exception hierarchy implemented
- [ ] All external service calls protected by circuit breakers
- [ ] Proper HTTP status codes for all error types
- [ ] Helpful error messages with suggestions
- [ ] No generic 500 errors for business logic issues
- [ ] Error logging for debugging without exposing internals

---

### **ITEM 18: Add API Pagination**
**Status**: 🔄 **PENDING** | **Priority**: MEDIUM | **Effort**: 1-2 weeks

#### **Problem Analysis**
- **Location**: `apps/api/app/routers/analysis.py:34-47`
- **Issue**: Loading all price history without limits
- **Impact**: Memory usage and response time issues with large datasets
- **Root Cause**: No pagination implementation

#### **Detailed Implementation Plan**

##### **Step 1: Create Pagination Utilities (2-3 days)**
```python
# NEW FILE: apps/api/app/utils/pagination.py
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(50, ge=1, le=1000, description="Items per page (max 1000)")
    
    @property
    def offset(self) -> int:
        """Calculate SQLAlchemy offset"""
        return (self.page - 1) * self.size

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        pagination: PaginationParams
    ) -> 'PaginatedResponse[T]':
        """Create paginated response from query results"""
        pages = (total + pagination.size - 1) // pagination.size
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1
        )

class CursorPagination(BaseModel):
    """Cursor-based pagination for time-series data"""
    cursor: Optional[str] = Field(None, description="Cursor for next page")
    size: int = Field(50, ge=1, le=1000, description="Items per page")

async def paginate_query(
    query: Query,
    pagination: PaginationParams
) -> PaginatedResponse[T]:
    """Paginate SQLAlchemy query"""
    # Get total count (separate query for accuracy)
    total = query.count()
    
    # Get paginated results
    items = (
        query
        .offset(pagination.offset)
        .limit(pagination.size)
        .all()
    )
    
    return PaginatedResponse.create(items, total, pagination)
```

##### **Step 2: Implement Time-Series Pagination (3-4 days)**
```python
# NEW FILE: apps/api/app/utils/time_series_pagination.py
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import base64
import json

class TimeSeriesPaginator:
    """Specialized pagination for time-series price data"""
    
    def __init__(self, default_days: int = 30, max_days: int = 365):
        self.default_days = default_days
        self.max_days = max_days
    
    def create_cursor(self, timestamp: datetime, symbol: str) -> str:
        """Create cursor for time-series pagination"""
        cursor_data = {
            "timestamp": timestamp.isoformat(),
            "symbol": symbol
        }
        cursor_json = json.dumps(cursor_data)
        return base64.b64encode(cursor_json.encode()).decode()
    
    def parse_cursor(self, cursor: str) -> Tuple[datetime, str]:
        """Parse cursor to get timestamp and symbol"""
        try:
            cursor_json = base64.b64decode(cursor.encode()).decode()
            cursor_data = json.loads(cursor_json)
            timestamp = datetime.fromisoformat(cursor_data["timestamp"])
            symbol = cursor_data["symbol"]
            return timestamp, symbol
        except Exception:
            raise ValueError("Invalid cursor format")
    
    async def paginate_prices(
        self,
        symbol: str,
        cursor: Optional[str] = None,
        size: int = 100,
        days: Optional[int] = None
    ) -> dict:
        """Paginate price data with cursor"""
        # Determine date range
        if days:
            days = min(days, self.max_days)  # Enforce maximum
        else:
            days = self.default_days
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Parse cursor if provided
        cursor_date = None
        if cursor:
            cursor_timestamp, cursor_symbol = self.parse_cursor(cursor)
            if cursor_symbol != symbol:
                raise ValueError("Cursor symbol mismatch")
            cursor_date = cursor_timestamp.date()
            end_date = cursor_date  # Start from cursor position
        
        # Query prices with date range
        query = (
            db.query(Price)
            .filter(
                Price.symbol == symbol,
                Price.date >= start_date,
                Price.date <= end_date
            )
            .order_by(Price.date.desc())
            .limit(size + 1)  # Get one extra to check if more pages
        )
        
        prices = query.all()
        
        # Check if there are more pages
        has_next = len(prices) > size
        if has_next:
            prices = prices[:size]  # Remove extra item
        
        # Create next cursor if needed
        next_cursor = None
        if has_next and prices:
            last_price = prices[-1]
            next_cursor = self.create_cursor(last_price.date, symbol)
        
        return {
            "prices": prices,
            "has_next": has_next,
            "next_cursor": next_cursor,
            "total_days": days,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
```

##### **Step 3: Update Router Endpoints with Pagination (3-4 days)**
```python
# MODIFY: apps/api/app/routers/analysis.py
from ..utils.pagination import PaginationParams, PaginatedResponse, paginate_query
from ..utils.time_series_pagination import TimeSeriesPaginator

# Add pagination to asset list endpoint
@router.get("/assets", response_model=PaginatedResponse[AssetResponse])
async def get_assets(
    pagination: PaginationParams = Depends(),
    sector: Optional[str] = Query(None),
    market_cap_min: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated list of assets"""
    query = db.query(Asset)
    
    # Apply filters
    if sector:
        query = query.filter(Asset.sector == sector)
    if market_cap_min:
        query = query.filter(Asset.market_cap >= market_cap_min)
    
    # Apply pagination
    return await paginate_query(query, pagination)

# Add time-series pagination for prices
@router.get("/assets/{symbol}/prices")
async def get_asset_prices(
    symbol: str,
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    size: int = Query(100, ge=1, le=1000, description="Number of records per page"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db)
):
    """Get paginated price history for asset"""
    paginator = TimeSeriesPaginator()
    
    try:
        result = await paginator.paginate_prices(
            symbol=symbol,
            cursor=cursor,
            size=size,
            days=days
        )
        
        return {
            "symbol": symbol,
            "prices": [PriceResponse.from_orm(p) for p in result["prices"]],
            "pagination": {
                "has_next": result["has_next"],
                "next_cursor": result["next_cursor"],
                "size": size
            },
            "metadata": {
                "total_days": result["total_days"],
                "date_range": result["date_range"]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add pagination to portfolio holdings
@router.get("/portfolios/{portfolio_id}/holdings", response_model=PaginatedResponse[HoldingResponse])
async def get_portfolio_holdings(
    portfolio_id: int,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """Get paginated portfolio holdings"""
    # Verify portfolio exists
    portfolio = db.query(Portfolio).filter_by(id=portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Query holdings with eager loading
    query = (
        db.query(Holding)
        .options(joinedload(Holding.asset))
        .filter(Holding.portfolio_id == portfolio_id)
        .order_by(Holding.value.desc())  # Order by largest positions first
    )
    
    return await paginate_query(query, pagination)
```

##### **Step 4: Add Pagination to Large Data Endpoints (2-3 days)**
```python
# MODIFY: apps/api/app/routers/signals.py
@router.get("/extreme-signals", response_model=PaginatedResponse[ExtremeSignalResponse])
async def get_extreme_signals(
    pagination: PaginationParams = Depends(),
    symbol: Optional[str] = Query(None),
    signal_type: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    days: int = Query(7, ge=1, le=90, description="Days of history"),
    db: Session = Depends(get_db)
):
    """Get paginated extreme signals"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = (
        db.query(ExtremeSignal)
        .filter(ExtremeSignal.created_at >= cutoff_date)
        .order_by(ExtremeSignal.created_at.desc())
    )
    
    # Apply filters
    if symbol:
        query = query.filter(ExtremeSignal.symbol == symbol)
    if signal_type:
        query = query.filter(ExtremeSignal.signal_type == signal_type)
    if min_confidence:
        query = query.filter(ExtremeSignal.confidence >= min_confidence)
    
    return await paginate_query(query, pagination)

# Add pagination to news feed
@router.get("/news", response_model=PaginatedResponse[NewsResponse])
async def get_news_feed(
    pagination: PaginationParams = Depends(),
    symbol: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None, regex="^(positive|negative|neutral)$"),
    days: int = Query(3, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get paginated news feed"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = (
        db.query(News)
        .filter(News.published_at >= cutoff_date)
        .order_by(News.published_at.desc())
    )
    
    if symbol:
        query = query.filter(News.symbols.contains([symbol]))
    if sentiment:
        query = query.filter(News.sentiment == sentiment)
    
    return await paginate_query(query, pagination)
```

##### **Step 5: Update Frontend to Handle Pagination (Optional - Backend Focus)**
```python
# NEW FILE: apps/api/app/schemas/pagination.py
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel

T = TypeVar('T')

class PaginationMetadata(BaseModel):
    """Pagination metadata for frontend"""
    current_page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next_page: bool
    has_prev_page: bool
    next_page_url: Optional[str] = None
    prev_page_url: Optional[str] = None

class PaginatedApiResponse(BaseModel, Generic[T]):
    """API response with pagination metadata"""
    data: List[T]
    pagination: PaginationMetadata
    
    @classmethod
    def from_paginated_response(
        cls,
        paginated: PaginatedResponse[T],
        base_url: str,
        query_params: dict = None
    ) -> 'PaginatedApiResponse[T]':
        """Convert internal pagination to API response"""
        query_params = query_params or {}
        
        # Build pagination URLs
        next_url = None
        prev_url = None
        
        if paginated.has_next:
            next_params = {**query_params, "page": paginated.page + 1, "size": paginated.size}
            next_url = f"{base_url}?" + "&".join(f"{k}={v}" for k, v in next_params.items())
        
        if paginated.has_prev:
            prev_params = {**query_params, "page": paginated.page - 1, "size": paginated.size}
            prev_url = f"{base_url}?" + "&".join(f"{k}={v}" for k, v in prev_params.items())
        
        metadata = PaginationMetadata(
            current_page=paginated.page,
            per_page=paginated.size,
            total_items=paginated.total,
            total_pages=paginated.pages,
            has_next_page=paginated.has_next,
            has_prev_page=paginated.has_prev,
            next_page_url=next_url,
            prev_page_url=prev_url
        )
        
        return cls(
            data=paginated.items,
            pagination=metadata
        )
```

#### **Files to Create/Modify**
- **NEW**: `apps/api/app/utils/pagination.py`
- **NEW**: `apps/api/app/utils/time_series_pagination.py`
- **NEW**: `apps/api/app/schemas/pagination.py`
- **MODIFY**: `apps/api/app/routers/analysis.py` (add pagination to endpoints)
- **MODIFY**: `apps/api/app/routers/signals.py` (add pagination)
- **MODIFY**: `apps/api/app/routers/portfolio.py` (add pagination)
- **MODIFY**: `apps/api/app/routers/news.py` (add pagination)

#### **Testing Requirements**
- [ ] Unit tests for pagination utilities
- [ ] Unit tests for time-series pagination
- [ ] Integration tests for paginated endpoints
- [ ] Performance tests with large datasets
- [ ] Edge case tests (empty results, invalid cursors)

#### **Acceptance Criteria**
- [ ] All list endpoints support pagination
- [ ] Time-series data uses cursor-based pagination
- [ ] Consistent pagination response format
- [ ] Maximum page size limits enforced
- [ ] Proper error handling for invalid pagination parameters
- [ ] Performance improvement for large datasets

---

## 🟢 **LOW PRIORITY** - *QUALITY IMPROVEMENTS*

### **ITEM 19: Improve Test Coverage**
**Status**: 🔄 **PENDING** | **Priority**: LOW | **Effort**: 2-3 weeks

#### **Problem Analysis**
- **Current**: 45% test coverage
- **Target**: 80% test coverage focusing on service layer
- **Issue**: Critical business logic not fully tested
- **Impact**: Risk of regressions, difficult refactoring

#### **Detailed Implementation Plan**

##### **Step 1: Audit Current Test Coverage (2-3 days)**
```bash
# Generate detailed coverage report
cd apps/api && python -m pytest --cov=app --cov-report=html --cov-report=term-missing

# Identify untested critical paths
# Focus areas:
# - Service layer business logic
# - Error handling paths
# - Edge cases in calculations
# - Integration points
```

##### **Step 2: Create Comprehensive Service Tests (7-10 days)**
```python
# NEW FILE: apps/api/tests/unit/services/test_signal_analyzer.py
class TestSignalAnalyzer:
    """Comprehensive tests for SignalAnalyzer service"""
    
    @pytest.fixture
    def mock_price_repo(self):
        return Mock(spec=IPriceRepository)
    
    @pytest.fixture
    def signal_analyzer(self, mock_price_repo):
        return SignalAnalyzer(price_repo=mock_price_repo)
    
    def test_analyze_technical_signals_rsi_overbought(self, signal_analyzer, mock_price_repo):
        """Test RSI overbought signal detection"""
        # Setup: Mock price data that results in RSI > 70
        mock_prices = [Price(date=date, close=price) for date, price in [
            ("2025-01-01", 100), ("2025-01-02", 105), ("2025-01-03", 110),
            # ... price sequence that creates RSI > 70
        ]]
        mock_price_repo.get_price_history.return_value = mock_prices
        
        # Execute
        signals = signal_analyzer.analyze_technical_signals("AAPL")
        
        # Verify
        assert signals.rsi_signal == "OVERBOUGHT"
        assert signals.rsi_value > 70
        assert signals.confidence > 0.8
        mock_price_repo.get_price_history.assert_called_once_with("AAPL", days=30)
    
    def test_analyze_technical_signals_insufficient_data(self, signal_analyzer, mock_price_repo):
        """Test handling of insufficient price data"""
        # Setup: Mock insufficient data
        mock_price_repo.get_price_history.return_value = []
        
        # Execute & Verify
        with pytest.raises(InsufficientDataError) as exc_info:
            signal_analyzer.analyze_technical_signals("INVALID")
        
        assert "insufficient data" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "InsufficientData"
    
    # Add 15-20 more test methods covering all signal types, edge cases, error conditions
```

##### **Step 3: Add Integration Tests (5-7 days)**
```python
# NEW FILE: apps/api/tests/integration/test_investment_analysis_flow.py
class TestInvestmentAnalysisFlow:
    """Integration tests for complete investment analysis"""
    
    @pytest.fixture
    def real_database(self):
        """Use real database for integration tests"""
        # Setup test database with real schema
        pass
    
    @pytest.fixture
    def sample_market_data(self, real_database):
        """Insert sample market data for testing"""
        # Create realistic test data
        pass
    
    async def test_complete_investment_analysis_flow(self, client, sample_market_data):
        """Test complete flow from API request to response"""
        # Test the full stack: Router -> Use Case -> Service -> Repository -> Database
        
        response = await client.post("/api/v1/investment/analyze/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify complete response structure
        assert "technical_signals" in data
        assert "fundamental_signals" in data
        assert "recommendation" in data
        assert "risk_assessment" in data
        
        # Verify business logic
        assert data["recommendation"]["action"] in ["BUY", "HOLD", "SELL"]
        assert 0 <= data["recommendation"]["confidence"] <= 1
        assert data["risk_assessment"]["overall_risk"] in ["LOW", "MEDIUM", "HIGH"]
    
    async def test_analysis_with_missing_data(self, client):
        """Test analysis when data is missing"""
        response = await client.post("/api/v1/investment/analyze/NONEXISTENT")
        
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["type"] == "InsufficientDataError"
```

##### **Step 4: Add Performance Tests (3-4 days)**
```python
# NEW FILE: apps/api/tests/performance/test_analysis_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestAnalysisPerformance:
    """Performance tests for investment analysis"""
    
    def test_single_analysis_performance(self, client, sample_data):
        """Test single analysis response time"""
        start_time = time.time()
        
        response = client.post("/api/v1/investment/analyze/AAPL")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Should complete in under 2 seconds
    
    def test_concurrent_analysis_performance(self, client, sample_data):
        """Test concurrent analysis handling"""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        
        def analyze_symbol(symbol):
            start = time.time()
            response = client.post(f"/api/v1/investment/analyze/{symbol}")
            end = time.time()
            return response.status_code, end - start
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze_symbol, symbol) for symbol in symbols]
            results = [future.result() for future in futures]
        
        # Verify all succeeded and within time limits
        for status_code, response_time in results:
            assert status_code == 200
            assert response_time < 5.0  # Should handle concurrent load
    
    def test_memory_usage_analysis(self, client, sample_data):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform 100 analyses
        for i in range(100):
            response = client.post("/api/v1/investment/analyze/AAPL")
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory shouldn't grow by more than 100MB
        assert memory_growth < 100 * 1024 * 1024
```

##### **Step 5: Edge Case and Error Testing (3-4 days)**
```python
# NEW FILE: apps/api/tests/unit/test_error_scenarios.py
class TestErrorScenarios:
    """Test error handling and edge cases"""
    
    def test_division_by_zero_in_calculations(self):
        """Test handling of division by zero"""
        calculator = BasicReturnCalculator()
        
        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_simple_return(0, 100)  # Division by zero
        
        assert "cannot be zero" in str(exc_info.value)
    
    def test_negative_prices_in_log_returns(self):
        """Test handling of negative prices in log calculations"""
        calculator = BasicReturnCalculator()
        
        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_logarithmic_return(-10, 100)  # Negative price
        
        assert "must be positive" in str(exc_info.value)
    
    def test_extreme_values_handling(self):
        """Test handling of extreme numerical values"""
        # Test with very large numbers
        # Test with very small numbers  
        # Test with infinity
        # Test with NaN values
        pass
    
    def test_malformed_input_data(self):
        """Test handling of malformed input data"""
        # Test with None values
        # Test with wrong data types
        # Test with empty lists
        # Test with inconsistent data structures
        pass
```

#### **Testing Strategy Summary**
1. **Unit Tests** (60% of effort): Focus on service layer business logic
2. **Integration Tests** (25% of effort): Test full request/response cycles
3. **Performance Tests** (10% of effort): Ensure scalability
4. **Edge Case Tests** (5% of effort): Handle error conditions

#### **Files to Create/Modify**
- **NEW**: 15+ new test files covering all service classes
- **NEW**: `apps/api/tests/integration/` directory with workflow tests
- **NEW**: `apps/api/tests/performance/` directory with load tests
- **NEW**: `apps/api/tests/fixtures/` with comprehensive test data
- **MODIFY**: `apps/api/tests/conftest.py` with better fixtures
- **NEW**: `apps/api/pytest.ini` with coverage configuration

#### **Acceptance Criteria**
- [ ] Test coverage increased from 45% to 80%+
- [ ] All service layer business logic covered
- [ ] All error paths tested
- [ ] Performance tests passing
- [ ] All edge cases covered
- [ ] CI/CD pipeline enforces coverage requirements

---

### **ITEM 20: Add Comprehensive API Documentation**
**Status**: 🔄 **PENDING** | **Priority**: LOW | **Effort**: 1-2 weeks

#### **Problem Analysis**
- **Issue**: Missing OpenAPI descriptions, examples, and response schemas
- **Impact**: Poor developer experience, difficult API adoption
- **Root Cause**: Incomplete FastAPI documentation features

#### **Detailed Implementation Plan**

##### **Step 1: Enhance Router Documentation (3-4 days)**
```python
# MODIFY: apps/api/app/routers/analysis.py
@router.post(
    "/analyze/{symbol}",
    response_model=InvestmentAnalysisResponse,
    summary="Analyze Investment Opportunity",
    description="""
    Perform comprehensive investment analysis on a given stock symbol.
    
    This endpoint analyzes technical indicators, fundamental metrics, 
    sentiment data, and market conditions to provide actionable 
    investment recommendations.
    
    **Analysis includes:**
    - Technical indicators (RSI, MACD, Bollinger Bands)
    - Fundamental metrics (P/E, P/B, ROE, debt ratios)
    - Sentiment analysis from news and social media
    - Risk assessment and position sizing recommendations
    
    **Investment horizons supported:**
    - Short-term: 1-3 months
    - Medium-term: 3-12 months  
    - Long-term: 1+ years
    """,
    responses={
        200: {
            "description": "Successful analysis with investment recommendation",
            "content": {
                "application/json": {
                    "example": {
                        "symbol": "AAPL",
                        "analysis_timestamp": "2025-01-25T10:30:00Z",
                        "recommendation": {
                            "action": "BUY",
                            "confidence": 0.87,
                            "target_price": 185.50,
                            "stop_loss": 165.20,
                            "position_size": 0.05,
                            "investment_horizon": "medium_term",
                            "rationale": "Strong technical momentum with oversold RSI recovery..."
                        },
                        "technical_signals": {
                            "rsi": {"value": 35.2, "signal": "OVERSOLD", "strength": "STRONG"},
                            "macd": {"value": 2.15, "signal": "BULLISH_CROSSOVER", "strength": "MODERATE"},
                            "bollinger_position": 0.23,
                            "support_levels": [170.50, 165.20],
                            "resistance_levels": [185.50, 192.30]
                        },
                        "fundamental_signals": {
                            "pe_ratio": 28.5,
                            "peg_ratio": 1.2,
                            "debt_to_equity": 0.45,
                            "roe": 0.267,
                            "revenue_growth": 0.08,
                            "earnings_growth": 0.12
                        },
                        "risk_assessment": {
                            "overall_risk": "MEDIUM",
                            "volatility_risk": "MEDIUM",
                            "liquidity_risk": "LOW",
                            "concentration_risk": "LOW",
                            "beta": 1.23
                        }
                    }
                }
            }
        },
        422: {
            "description": "Insufficient data for analysis",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "type": "InsufficientDataError",
                            "message": "Not enough historical data for technical analysis",
                            "details": {"symbol": "NEWIPO", "available_days": 5, "required_days": 30},
                            "suggestion": "Try again after more trading history is available"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Symbol not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "type": "SymbolNotFound",
                            "message": "Symbol INVALID not found in our database",
                            "suggestion": "Please check the symbol spelling or try a different symbol"
                        }
                    }
                }
            }
        }
    },
    tags=["Investment Analysis"]
)
async def analyze_investment(
    symbol: str = Path(
        ..., 
        description="Stock symbol to analyze (e.g., AAPL, GOOGL, MSFT)",
        example="AAPL",
        regex="^[A-Z]{1,5}$"
    ),
    horizon: InvestmentHorizon = Query(
        InvestmentHorizon.MEDIUM_TERM,
        description="Investment time horizon for recommendation"
    ),
    risk_tolerance: RiskTolerance = Query(
        RiskTolerance.MODERATE,
        description="Risk tolerance level for position sizing"
    )
):
    """Analyze investment opportunity with detailed documentation"""
    # Implementation here
```

##### **Step 2: Create Comprehensive Schema Documentation (2-3 days)**
```python
# MODIFY: apps/api/app/schemas/investment.py
class TechnicalSignals(BaseModel):
    """Technical analysis signals and indicators"""
    
    rsi: RSISignal = Field(
        ..., 
        description="RSI (Relative Strength Index) analysis",
        example={"value": 35.2, "signal": "OVERSOLD", "strength": "STRONG"}
    )
    
    macd: MACDSignal = Field(
        ...,
        description="MACD (Moving Average Convergence Divergence) analysis", 
        example={"value": 2.15, "signal": "BULLISH_CROSSOVER", "strength": "MODERATE"}
    )
    
    bollinger_position: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Position within Bollinger Bands (0=lower band, 1=upper band)",
        example=0.23
    )
    
    support_levels: List[float] = Field(
        ...,
        description="Identified support price levels",
        example=[170.50, 165.20]
    )
    
    resistance_levels: List[float] = Field(
        ...,
        description="Identified resistance price levels", 
        example=[185.50, 192.30]
    )
    
    class Config:
        schema_extra = {
            "example": {
                "rsi": {"value": 35.2, "signal": "OVERSOLD", "strength": "STRONG"},
                "macd": {"value": 2.15, "signal": "BULLISH_CROSSOVER", "strength": "MODERATE"},
                "bollinger_position": 0.23,
                "support_levels": [170.50, 165.20],
                "resistance_levels": [185.50, 192.30]
            }
        }

class InvestmentRecommendation(BaseModel):
    """Investment recommendation with detailed rationale"""
    
    action: InvestmentAction = Field(
        ...,
        description="Recommended investment action based on analysis"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level in the recommendation (0.0 to 1.0)",
        example=0.87
    )
    
    target_price: Optional[float] = Field(
        None,
        gt=0,
        description="Target price for the investment",
        example=185.50
    )
    
    stop_loss: Optional[float] = Field(
        None,
        gt=0,
        description="Recommended stop-loss price",
        example=165.20
    )
    
    position_size: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Recommended position size as fraction of portfolio (0.0 to 1.0)",
        example=0.05
    )
    
    investment_horizon: InvestmentHorizon = Field(
        ...,
        description="Recommended investment time horizon"
    )
    
    rationale: str = Field(
        ...,
        description="Human-readable explanation of the recommendation",
        example="Strong technical momentum with oversold RSI recovery and bullish MACD crossover. Fundamental metrics show reasonable valuation with solid growth prospects."
    )
```

##### **Step 3: Add Interactive API Documentation (2 days)**
```python
# MODIFY: apps/api/app/main.py
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Waardhaven AutoIndex API",
    description="""
    ## AI-Powered Investment Analysis Platform
    
    Waardhaven AutoIndex provides comprehensive investment analysis and recommendations
    through advanced technical analysis, fundamental analysis, and sentiment monitoring.
    
    ### Key Features
    * **Technical Analysis**: RSI, MACD, Bollinger Bands, support/resistance levels
    * **Fundamental Analysis**: P/E ratios, growth metrics, financial health indicators  
    * **Sentiment Analysis**: News sentiment, social media sentiment, market sentiment
    * **Risk Assessment**: Portfolio risk, concentration risk, volatility analysis
    * **Investment Recommendations**: Buy/Hold/Sell with confidence scores and rationale
    
    ### Investment Philosophy
    This platform focuses on **long-term value creation** rather than short-term trading.
    Our analysis considers investment horizons of 1 month to 3+ years, with emphasis on
    fundamental value and sustainable growth.
    
    ### Authentication
    Most endpoints require authentication. Use the `/auth/login` endpoint to obtain
    an access token, then include it in the `Authorization` header as `Bearer <token>`.
    
    ### Rate Limits
    API endpoints are rate-limited to ensure fair usage:
    * Free tier: 100 requests per hour
    * Premium tier: 1000 requests per hour  
    * Analysis endpoints: 50 requests per hour (computationally intensive)
    
    ### Support
    * Documentation: [GitHub Wiki](https://github.com/Ai-Whisperers/AI-Investment/wiki)
    * Issues: [GitHub Issues](https://github.com/Ai-Whisperers/AI-Investment/issues)
    * Email: support@waardhaven.ai
    """,
    version="2.1.0",
    terms_of_service="https://waardhaven.ai/terms",
    contact={
        "name": "Waardhaven API Support",
        "url": "https://waardhaven.ai/support",
        "email": "api-support@waardhaven.ai",
    },
    license_info={
        "name": "Commercial License",
        "url": "https://waardhaven.ai/license",
    },
    openapi_tags=[
        {
            "name": "Investment Analysis",
            "description": "Core investment analysis and recommendation endpoints",
            "externalDocs": {
                "description": "Analysis methodology",
                "url": "https://docs.waardhaven.ai/analysis-methodology",
            },
        },
        {
            "name": "Authentication", 
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Portfolio Management",
            "description": "Portfolio creation, management, and optimization endpoints"
        },
        {
            "name": "Market Data",
            "description": "Real-time and historical market data endpoints"
        },
        {
            "name": "Signals",
            "description": "Trading signals and market opportunity detection"
        },
        {
            "name": "News & Sentiment", 
            "description": "News aggregation and sentiment analysis endpoints"
        },
        {
            "name": "Risk Management",
            "description": "Risk assessment and portfolio risk analysis endpoints"
        },
        {
            "name": "Admin",
            "description": "Administrative endpoints (admin access required)"
        }
    ]
)

# Custom documentation endpoints with enhanced styling
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Interactive API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.1.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.1.0/swagger-ui.css",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": 2,
            "defaultModelExpandDepth": 2,
            "displayOperationId": False,
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
        }
    )
```

##### **Step 4: Generate SDK Documentation (1-2 days)**
```python
# NEW FILE: apps/api/generate_sdk_docs.py
"""Generate SDK documentation from OpenAPI spec"""

import json
import yaml
from fastapi.openapi.utils import get_openapi
from ..main import app

def generate_openapi_spec():
    """Generate OpenAPI specification"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Save as JSON
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    # Save as YAML
    with open("openapi.yaml", "w") as f:
        yaml.dump(openapi_schema, f, indent=2)
    
    print("OpenAPI specification generated!")
    return openapi_schema

def generate_client_examples():
    """Generate client code examples"""
    
    python_example = """
# Python Client Example
import requests

class WaardhavenClient:
    def __init__(self, api_key: str, base_url: str = "https://api.waardhaven.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def analyze_investment(self, symbol: str, horizon: str = "medium_term"):
        \"\"\"Get investment analysis for a symbol\"\"\"
        response = self.session.post(
            f"{self.base_url}/api/v1/investment/analyze/{symbol}",
            params={"horizon": horizon}
        )
        response.raise_for_status()
        return response.json()
    
    def get_portfolio_recommendations(self, portfolio_id: int):
        \"\"\"Get recommendations for a portfolio\"\"\"
        response = self.session.get(
            f"{self.base_url}/api/v1/portfolio/{portfolio_id}/recommendations"
        )
        response.raise_for_status()
        return response.json()

# Usage
client = WaardhavenClient("your-api-key")
analysis = client.analyze_investment("AAPL")
print(f"Recommendation: {analysis['recommendation']['action']}")
    """
    
    javascript_example = """
// JavaScript/Node.js Client Example
class WaardhavenClient {
    constructor(apiKey, baseUrl = 'https://api.waardhaven.ai') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }
    
    async analyzeInvestment(symbol, horizon = 'medium_term') {
        const response = await fetch(
            `${this.baseUrl}/api/v1/investment/analyze/${symbol}?horizon=${horizon}`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async getPortfolioRecommendations(portfolioId) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/portfolio/${portfolioId}/recommendations`,
            {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Usage
const client = new WaardhavenClient('your-api-key');
const analysis = await client.analyzeInvestment('AAPL');
console.log(`Recommendation: ${analysis.recommendation.action}`);
    """
    
    # Save examples
    with open("client_examples.md", "w") as f:
        f.write("# API Client Examples\n\n")
        f.write("## Python Client\n\n```python\n")
        f.write(python_example)
        f.write("\n```\n\n## JavaScript Client\n\n```javascript\n")
        f.write(javascript_example)
        f.write("\n```\n")

if __name__ == "__main__":
    generate_openapi_spec()
    generate_client_examples()
```

#### **Files to Create/Modify**
- **MODIFY**: All router files to add comprehensive documentation
- **MODIFY**: All schema files to add field descriptions and examples
- **MODIFY**: `apps/api/app/main.py` (enhance OpenAPI configuration)
- **NEW**: `apps/api/generate_sdk_docs.py`
- **NEW**: `docs/API_DOCUMENTATION.md`
- **NEW**: `docs/CLIENT_EXAMPLES.md`

#### **Testing Requirements**
- [ ] Verify OpenAPI spec generates correctly
- [ ] Test all documented examples work
- [ ] Validate schema examples in documentation
- [ ] Check that all endpoints have proper documentation

#### **Acceptance Criteria**
- [ ] All endpoints have detailed descriptions
- [ ] All schemas have field descriptions and examples
- [ ] Interactive documentation is user-friendly
- [ ] Client code examples are provided
- [ ] OpenAPI specification validates correctly
- [ ] External documentation links work

---

## 📊 **PROGRESS TRACKING**

### **Completion Status**
- ✅ **Completed**: 3/22 items (14%)
- 🔄 **In Progress**: 1/22 items (OAuth fix completed)
- 🔄 **Pending**: 18/22 items (86%)

### **Priority Breakdown**
- **CRITICAL**: 2 pending (Clean Architecture, Repository Pattern)
- **HIGH**: 2 pending (Monolithic services, N+1 queries)
- **MEDIUM**: 4 pending (Admin auth, large files, error handling, pagination)
- **LOW**: 2 pending (Test coverage, API documentation)

### **Estimated Timeline**
- **Week 1-2**: Complete Critical items (Architecture violations, Repository pattern)
- **Week 3-4**: Complete High priority items (Monolithic services, N+1 queries)
- **Week 5-6**: Complete Medium priority items
- **Week 7-8**: Complete Low priority items (optional for deployment)

### **Risk Assessment**
- **High Risk**: Clean Architecture violations (affects all future development)
- **Medium Risk**: Repository pattern (affects database performance)
- **Low Risk**: Documentation and test coverage (doesn't block functionality)

---

## 🎯 **SUCCESS METRICS**

### **Technical Metrics**
- [ ] Test coverage: 45% → 80%
- [ ] File size compliance: 3 files >600 lines → 0 files >200 lines
- [ ] API response time: <100ms average (after N+1 fix)
- [ ] Security scan: 0 critical vulnerabilities
- [ ] Code quality: All SOLID principles followed

### **Architecture Metrics**  
- [ ] Clean Architecture: 0 violations in presentation layer
- [ ] Repository Pattern: 0 direct ORM queries in routers
- [ ] Service Size: All services <200 lines, single responsibility
- [ ] Error Handling: 100% of external calls protected by circuit breakers
- [ ] Pagination: All list endpoints support pagination

### **Quality Gates**
- [ ] All critical and high priority items completed
- [ ] CI/CD pipeline passes all quality checks
- [ ] Security audit shows no critical issues
- [ ] Performance tests show no regression
- [ ] All existing functionality preserved

---

**Last Updated**: 2025-01-26  
**Next Review**: Weekly until all critical items completed  
**Owner**: Development Team  
**Status**: Ready for implementation - detailed plans created