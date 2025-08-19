---
title: Technical Glossary
category: Reference
priority: 99
status: stable
last-updated: 2025-08-19
owner: documentation-team
---

# 📖 Technical Glossary

## A

**API (Application Programming Interface)**
- The backend service that handles data processing and business logic
- Built with FastAPI framework
- Located at: `apps/api/`

**Authentication**
- JWT-based token system for user identity verification
- Includes Google OAuth integration
- See: [Authentication Guide](02-api-reference/authentication/README.md)

**Alembic**
- Database migration tool for Python/SQLAlchemy
- Status: 🔴 Not implemented (Critical Priority #1)

**Architecture Pattern**
- Hexagonal + Clean Architecture implementation
- Status: ✅ COMPLETED (95%+ implementation achieved)
- All god files eliminated, modular structure ready

## B

**Backend**
- FastAPI-based server application
- Handles business logic, data processing, and external integrations
- Path: `apps/api/`

**Benchmark**
- S&P 500 index used for performance comparison
- Endpoint: `/api/v1/benchmark/`

## C

**Celery**
- Distributed task queue for background processing
- Used for async operations like data refresh
- Config: `apps/api/app/core/celery_app.py`

**Clean Architecture**
- Design pattern separating concerns into layers
- Domain → Application → Infrastructure → Presentation
- Status: ✅ FULLY IMPLEMENTED in `apps/web/app/core/`
- Achieved 71% average line reduction across refactored files

**CORS (Cross-Origin Resource Sharing)**
- Security feature controlling cross-domain requests
- Configured for frontend-backend communication

## D

**Docker**
- Containerization platform for deployment
- Dockerfiles in: `apps/api/Dockerfile`, `apps/web/Dockerfile`

**Domain Layer**
- Business entities and rules independent of framework
- Location: `apps/web/app/core/domain/`

## E

**Environment Variables**
- Configuration values stored in `.env` files
- See: [Environment Setup](01-getting-started/04-environment-variables.md)

## F

**FastAPI**
- High-performance Python web framework
- Async support with automatic API documentation
- Main file: `apps/api/app/main.py`

**Frontend**
- Next.js-based web application
- Server-side rendered React
- Path: `apps/web/`

## I

**Index**
- Portfolio value calculation based on weighted assets
- Core feature of the platform
- Endpoint: `/api/v1/index/`

## J

**JWT (JSON Web Token)**
- Token format for secure authentication
- 30-minute access token, 7-day refresh token
- Implementation: `apps/api/app/utils/security.py`

## M

**MarketAux**
- External API for news and sentiment data
- Status: 🚧 Integration in progress
- Provider: `apps/api/app/providers/marketaux_provider.py`

**Mermaid**
- Diagram syntax for architecture visualization
- Used in: `docs/03-implementation/diagrams/`

**Monorepo**
- Single repository containing multiple projects
- Managed with npm workspaces and Turborepo

## N

**Next.js**
- React framework with SSR/SSG capabilities
- Version: 14.2.32
- Config: `apps/web/next.config.js`

## P

**PostgreSQL**
- Primary relational database
- Stores users, assets, prices, portfolios
- Connection: `DATABASE_URL` environment variable

**Provider Pattern**
- Design pattern for external service integration
- Base class with circuit breaker support
- Location: `apps/api/app/providers/`

**Pydantic**
- Data validation library for Python
- Used for request/response schemas
- Location: `apps/api/app/schemas/`

## R

**Redis**
- In-memory cache and message broker
- Used for caching and Celery queue
- Connection: `REDIS_URL` environment variable

**Render.com**
- Cloud platform for deployment
- Config: `render.yaml`
- Production URL: https://waardhaven-api.onrender.com

**Rebalancing**
- Portfolio adjustment to maintain target allocations
- Frequencies: Daily, Weekly, Monthly, Quarterly
- Endpoint: `/api/v1/strategy/rebalance`

## S

**SQLAlchemy**
- Python ORM (Object-Relational Mapping)
- Database abstraction layer
- Models: `apps/api/app/models/`

**Strategy**
- Investment strategy configuration
- Includes momentum, market cap, risk parity weights
- Endpoint: `/api/v1/strategy/config`

## T

**Testing Infrastructure**
- Unit, integration, and E2E test frameworks
- Status: 🔴 CRITICAL ISSUE - 0% coverage found vs 95% target
- Priority: Immediate implementation for financial regulatory compliance
- Frameworks: pytest (backend), Jest (frontend planned)

**TwelveData**
- External API for market data and prices
- Rate limited based on plan
- Provider: `apps/api/app/providers/twelvedata_provider.py`

**TypeScript**
- Typed superset of JavaScript
- Used throughout frontend
- Config: `apps/web/tsconfig.json`

**Turborepo**
- Build system for monorepos
- Config: `turbo.json`

## U

**Uvicorn**
- ASGI server for FastAPI
- Command: `uvicorn app.main:app --reload`

## W

**WebSocket**
- Protocol for real-time communication
- Status: 📝 Planned feature
- Use case: Live portfolio updates

## Acronyms

| Acronym | Full Form |
|---------|-----------|
| API | Application Programming Interface |
| ASGI | Asynchronous Server Gateway Interface |
| CDN | Content Delivery Network |
| CI/CD | Continuous Integration/Continuous Deployment |
| CORS | Cross-Origin Resource Sharing |
| CRUD | Create, Read, Update, Delete |
| CSS | Cascading Style Sheets |
| ETF | Exchange-Traded Fund |
| JWT | JSON Web Token |
| MVC | Model-View-Controller |
| MVP | Minimum Viable Product |
| ORM | Object-Relational Mapping |
| REST | Representational State Transfer |
| S&P | Standard & Poor's |
| SLA | Service Level Agreement |
| SQL | Structured Query Language |
| SSG | Static Site Generation |
| SSR | Server-Side Rendering |
| TDD | Test-Driven Development |
| UI/UX | User Interface/User Experience |
| URL | Uniform Resource Locator |
| UUID | Universally Unique Identifier |
| VaR | Value at Risk |

---
*Missing a term? Add it in alphabetical order with a clear, concise definition.*