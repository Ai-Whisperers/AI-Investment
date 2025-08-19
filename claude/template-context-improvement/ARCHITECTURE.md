# Architecture Decisions

## Overview
Quick reference for architectural patterns and decisions in this codebase.

## Core Architecture Pattern

### Clean Architecture Layers
```
Presentation Layer (UI/Controllers)
        ↓
Application Layer (Use Cases)
        ↓
Domain Layer (Business Logic)
        ↓
Infrastructure Layer (DB/External Services)
```

### Why This Pattern?
- **Testability**: Business logic independent of frameworks
- **Flexibility**: Easy to swap implementations
- **Maintainability**: Clear separation of concerns

## Frontend Architecture

### Component Structure
```
ComponentName/
├── index.ts                 # Public API (5 lines)
├── ComponentName.tsx        # UI logic only (100-200 lines)
├── ComponentName.types.ts   # TypeScript interfaces (20-50 lines)
├── ComponentName.styles.ts  # Styling (30-80 lines)
├── ComponentName.hooks.ts   # Custom hooks (50-100 lines)
└── ComponentName.test.tsx   # Tests (100-200 lines)
```

### State Management Strategy
- **Local State**: useState for component-specific
- **Global State**: Context/Redux for app-wide
- **Server State**: React Query/SWR for API data
- **Form State**: React Hook Form for forms

### Data Flow
```
User Action → Component → Hook → Service → API → Backend
                ↑                              ↓
            State Update ← Response ← Process ←
```

## Backend Architecture

### API Structure
```
Request → Router → Middleware → Controller → Service → Repository → Database
           ↓          ↓            ↓           ↓          ↓
        Validate   Authorize    Process    Business   Database
                                 Request     Logic      Query
```

### Service Layer Pattern
```python
# Service handles business logic
class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository
    
    def create_user(self, data: UserDTO) -> User:
        # Business logic here (50-150 lines per method)
        validated = self.validate(data)
        return self.repo.create(validated)
```

### Repository Pattern
```python
# Repository handles data access
class UserRepository:
    def create(self, user: User) -> User:
        # Database operations only (20-50 lines per method)
        return db.insert(user)
```

## Database Design

### Schema Principles
1. **Normalization**: 3NF for transactional data
2. **Denormalization**: Selected read-heavy tables
3. **Indexing**: On foreign keys and frequent WHERE columns

### Common Patterns
```sql
-- Soft deletes
deleted_at TIMESTAMP NULL

-- Audit fields
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
created_by VARCHAR(255)
updated_by VARCHAR(255)

-- Optimistic locking
version INTEGER DEFAULT 1
```

## API Design

### RESTful Conventions
```
GET    /api/v1/resources      # List
GET    /api/v1/resources/:id  # Get one
POST   /api/v1/resources      # Create
PUT    /api/v1/resources/:id  # Update (full)
PATCH  /api/v1/resources/:id  # Update (partial)
DELETE /api/v1/resources/:id  # Delete
```

### Response Format
```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
  },
  "errors": []
}
```

### Error Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "User-friendly message",
    "details": []
  }
}
```

## Security Architecture

### Authentication Flow
```
1. User provides credentials
2. Validate against database
3. Generate JWT token
4. Return token + refresh token
5. Client stores in secure storage
6. Include token in API requests
7. Validate token on each request
```

### Authorization Levels
- **Public**: No auth required
- **Authenticated**: Valid JWT required
- **Authorized**: Specific permissions required
- **Admin**: Admin role required

## Performance Strategies

### Caching Layers
1. **Browser Cache**: Static assets
2. **CDN Cache**: Images, scripts
3. **Application Cache**: Redis/Memory
4. **Database Cache**: Query results

### Optimization Techniques
- **Lazy Loading**: Components and routes
- **Code Splitting**: By route/feature
- **Debouncing**: User input (300ms)
- **Pagination**: Limit to 50 items
- **Indexing**: Database queries

## Testing Strategy

### Test Pyramid
```
        E2E Tests (5%)
       /           \
    Integration (25%)
   /               \
Unit Tests (70%)
```

### Test File Organization
- Place tests next to source files
- Use `.test.ts` or `.spec.ts` suffix
- Mock external dependencies
- Use factories for test data

## Deployment Architecture

### Environment Strategy
```
Development → Staging → Production
    ↓           ↓          ↓
  Local       Test      Live Users
  Debug      UAT        Monitoring
```

### Container Structure
```
docker-compose.yml
├── api-service
├── web-service
├── database
├── redis
└── nginx
```

## Code Quality Standards

### File Size Limits
- **Components**: Max 400 lines
- **Services**: Max 500 lines
- **Tests**: Max 300 lines per file
- **Config**: Max 200 lines

### Complexity Limits
- **Function**: Max 50 lines
- **Cyclomatic Complexity**: Max 10
- **Nesting**: Max 3 levels
- **Parameters**: Max 4

## Monitoring & Logging

### Log Levels
```
ERROR   - System errors requiring attention
WARN    - Potential issues
INFO    - Important events
DEBUG   - Detailed debugging info
```

### Metrics to Track
- Response times (p50, p95, p99)
- Error rates
- Database query times
- Cache hit rates
- Memory usage

## Decision Records

### Why TypeScript?
- Type safety catches errors early
- Better IDE support
- Self-documenting code

### Why PostgreSQL?
- ACID compliance
- Complex queries support
- JSON support for flexibility

### Why Docker?
- Consistent environments
- Easy deployment
- Isolated dependencies

### Why Redis?
- Fast caching
- Session storage
- Pub/sub capabilities

## Notes for AI Assistants

1. **Check existing patterns** before implementing new ones
2. **Keep layers separate** - don't mix concerns
3. **Prefer composition** over inheritance
4. **Use dependency injection** for testability
5. **Follow RESTful conventions** unless specified otherwise