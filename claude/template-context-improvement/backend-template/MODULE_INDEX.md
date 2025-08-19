# Backend Module Index

## Directory Structure
```
backend-template/
├── api/              # API routes and controllers
├── services/         # Business logic layer
├── models/           # Database models
├── middleware/       # Express/FastAPI middleware
├── utils/           # Utility functions
├── config/          # Configuration files
├── database/        # Database connection and migrations
└── tests/           # Test files
```

## Module Descriptions

### API Routes (`/api`)
**Purpose:** Handle HTTP requests and responses
**Files:** 50-200 lines each
**Pattern:** One file per resource

Example structure:
```
api/
├── auth.routes.ts       # Auth endpoints
├── user.routes.ts       # User CRUD
├── product.routes.ts    # Product endpoints
└── index.ts            # Route aggregator
```

### Services (`/services`)
**Purpose:** Business logic and data processing
**Files:** 100-300 lines each
**Pattern:** One service per domain

Example structure:
```
services/
├── AuthService.ts       # Authentication logic
├── UserService.ts       # User operations
├── EmailService.ts      # Email sending
├── CacheService.ts      # Caching layer
└── index.ts            # Service exports
```

### Models (`/models`)
**Purpose:** Database schemas and models
**Files:** 50-150 lines each
**Pattern:** One model per table

Example structure:
```
models/
├── User.model.ts        # User schema
├── Product.model.ts     # Product schema
├── Order.model.ts       # Order schema
└── index.ts            # Model exports
```

### Middleware (`/middleware`)
**Purpose:** Request processing and validation
**Files:** 30-100 lines each
**Pattern:** Single responsibility

Example structure:
```
middleware/
├── auth.middleware.ts   # JWT validation
├── error.middleware.ts  # Error handling
├── cors.middleware.ts   # CORS config
├── validate.middleware.ts # Request validation
└── index.ts            # Middleware exports
```

## Import Map

### Common Imports
```typescript
// Services
import { UserService } from '@/services/UserService';
import { AuthService } from '@/services/AuthService';

// Models
import { User } from '@/models/User.model';
import { Product } from '@/models/Product.model';

// Middleware
import { authenticate } from '@/middleware/auth';
import { validate } from '@/middleware/validate';

// Utils
import { logger } from '@/utils/logger';
import { database } from '@/database';
```

## API Endpoint Map

### Authentication
```
POST   /api/auth/register     # User registration
POST   /api/auth/login        # User login
POST   /api/auth/refresh      # Refresh token
POST   /api/auth/logout       # User logout
GET    /api/auth/me          # Current user
```

### Users
```
GET    /api/users            # List users
GET    /api/users/:id        # Get user
POST   /api/users            # Create user
PUT    /api/users/:id        # Update user
DELETE /api/users/:id        # Delete user
```

### Products
```
GET    /api/products         # List products
GET    /api/products/:id     # Get product
POST   /api/products         # Create product
PUT    /api/products/:id     # Update product
DELETE /api/products/:id     # Delete product
```

## Service Method Map

### UserService
```typescript
class UserService {
  findAll(filters?)         // 30 lines
  findById(id)              // 20 lines
  create(data)              // 40 lines
  update(id, data)          // 35 lines
  delete(id)                // 25 lines
  findByEmail(email)        // 15 lines
}
```

### AuthService
```typescript
class AuthService {
  register(data)            // 50 lines
  login(credentials)        // 40 lines
  refresh(token)            // 30 lines
  logout(userId)            // 20 lines
  validateToken(token)      // 25 lines
}
```

## Database Schema Map

### User Table
```sql
users
├── id (UUID, PK)
├── email (VARCHAR, UNIQUE)
├── password (VARCHAR)
├── name (VARCHAR)
├── role (ENUM)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

### Product Table
```sql
products
├── id (UUID, PK)
├── name (VARCHAR)
├── description (TEXT)
├── price (DECIMAL)
├── stock (INTEGER)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

## Configuration Map

### Environment Variables
```env
# Server
PORT=4000
NODE_ENV=development

# Database
DATABASE_URL=postgresql://...

# Auth
JWT_SECRET=secret
JWT_EXPIRY=1d

# External Services
REDIS_URL=redis://...
EMAIL_API_KEY=...
```

## Testing Structure

### Test Files
```
tests/
├── unit/
│   ├── services/         # Service tests
│   └── utils/           # Utility tests
├── integration/
│   ├── api/             # API tests
│   └── database/        # DB tests
└── fixtures/            # Test data
```

## Error Codes

| Code | Description |
|------|------------|
| AUTH_001 | Invalid credentials |
| AUTH_002 | Token expired |
| AUTH_003 | Unauthorized access |
| VAL_001 | Validation failed |
| VAL_002 | Missing required field |
| DB_001 | Database connection error |
| DB_002 | Record not found |
| SRV_001 | Internal server error |

## Performance Metrics

### Target Response Times
- Authentication: < 200ms
- CRUD Operations: < 100ms
- Search/Filter: < 500ms
- File Upload: < 2s

### Optimization Points
1. Database indexes on foreign keys
2. Redis caching for frequent queries
3. Connection pooling
4. Query optimization
5. Response compression