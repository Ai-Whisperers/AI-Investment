# Code Patterns Guide

## Purpose
Standard patterns to follow for consistency. AI assistants should reference this before writing new code.

## Naming Conventions

### Files
```
# Components
UserProfile.tsx         # Component file
UserProfile.types.ts    # Type definitions
UserProfile.styles.ts   # Styles
UserProfile.test.tsx    # Tests

# Services
AuthService.ts          # Service class
authService.ts          # Service instance

# Hooks
useAuth.ts             # Custom hook
useUserData.ts         # Data fetching hook

# Utilities
formatDate.ts          # Utility function
validators.ts          # Validation functions
```

### Variables & Functions
```typescript
// Constants
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';

// Functions
function calculateTotal(items: Item[]): number
const handleSubmit = async (data: FormData): Promise<void>

// Classes
class UserService {}
class AuthenticationError extends Error {}

// Interfaces/Types
interface UserData {}
type UserId = string;
```

## Component Patterns

### Basic Component Template
```typescript
// UserCard.tsx (Keep under 200 lines)
import React from 'react';
import { UserCardProps } from './UserCard.types';
import { cardStyles } from './UserCard.styles';

export const UserCard: React.FC<UserCardProps> = ({
  user,
  onEdit,
  isLoading = false,
}) => {
  // Hooks first
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Event handlers
  const handleClick = () => {
    setIsExpanded(!isExpanded);
  };
  
  // Early returns
  if (isLoading) return <Skeleton />;
  if (!user) return null;
  
  // Main render
  return (
    <div className={cardStyles.container}>
      {/* Content here */}
    </div>
  );
};
```

### Custom Hook Pattern
```typescript
// useUserData.ts (Keep under 150 lines)
export function useUserData(userId: string) {
  const [data, setData] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await api.getUser(userId);
        setData(response);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [userId]);
  
  return { data, loading, error };
}
```

## Service Patterns

### Service Class Template
```typescript
// UserService.ts (Keep methods under 50 lines each)
export class UserService {
  constructor(
    private api: ApiClient,
    private cache: CacheService
  ) {}
  
  async getUser(id: string): Promise<User> {
    // Check cache first
    const cached = await this.cache.get(`user:${id}`);
    if (cached) return cached;
    
    // Fetch from API
    const user = await this.api.get(`/users/${id}`);
    
    // Cache for 5 minutes
    await this.cache.set(`user:${id}`, user, 300);
    
    return user;
  }
  
  async updateUser(id: string, data: Partial<User>): Promise<User> {
    const user = await this.api.patch(`/users/${id}`, data);
    
    // Invalidate cache
    await this.cache.delete(`user:${id}`);
    
    return user;
  }
}
```

### Repository Pattern
```typescript
// UserRepository.ts (Keep under 300 lines)
export class UserRepository {
  async findById(id: string): Promise<User | null> {
    return await db.user.findUnique({
      where: { id }
    });
  }
  
  async create(data: CreateUserDto): Promise<User> {
    return await db.user.create({
      data
    });
  }
  
  async update(id: string, data: UpdateUserDto): Promise<User> {
    return await db.user.update({
      where: { id },
      data
    });
  }
}
```

## API Patterns

### Express Route Handler
```typescript
// userRoutes.ts (Keep handlers under 30 lines)
router.get('/users/:id', 
  authenticate,
  validate(getUserSchema),
  async (req, res, next) => {
    try {
      const user = await userService.getUser(req.params.id);
      
      if (!user) {
        return res.status(404).json({
          error: 'User not found'
        });
      }
      
      res.json({
        success: true,
        data: user
      });
    } catch (error) {
      next(error);
    }
  }
);
```

### FastAPI Route Handler
```python
# user_routes.py (Keep handlers under 30 lines)
@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    user = await service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return UserResponse(
        success=True,
        data=user
    )
```

## Error Handling Patterns

### Custom Error Classes
```typescript
// errors.ts (Keep under 100 lines total)
export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code?: string
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: any) {
    super(message, 400, 'VALIDATION_ERROR');
    this.details = details;
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 404, 'NOT_FOUND');
  }
}
```

### Error Handler Middleware
```typescript
// errorHandler.ts (Keep under 50 lines)
export const errorHandler = (
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details
      }
    });
  }
  
  // Log unexpected errors
  console.error('Unexpected error:', err);
  
  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred'
    }
  });
};
```

## Testing Patterns

### Unit Test Template
```typescript
// UserService.test.ts (Keep under 200 lines per file)
describe('UserService', () => {
  let service: UserService;
  let mockApi: jest.Mocked<ApiClient>;
  
  beforeEach(() => {
    mockApi = createMockApi();
    service = new UserService(mockApi);
  });
  
  describe('getUser', () => {
    it('should return user when found', async () => {
      // Arrange
      const expectedUser = { id: '1', name: 'John' };
      mockApi.get.mockResolvedValue(expectedUser);
      
      // Act
      const user = await service.getUser('1');
      
      // Assert
      expect(user).toEqual(expectedUser);
      expect(mockApi.get).toHaveBeenCalledWith('/users/1');
    });
    
    it('should throw error when user not found', async () => {
      // Arrange
      mockApi.get.mockRejectedValue(new NotFoundError('User'));
      
      // Act & Assert
      await expect(service.getUser('999')).rejects.toThrow(NotFoundError);
    });
  });
});
```

### Integration Test Template
```typescript
// api.test.ts (Keep under 300 lines per file)
describe('User API', () => {
  beforeAll(async () => {
    await setupTestDatabase();
  });
  
  afterAll(async () => {
    await cleanupTestDatabase();
  });
  
  describe('GET /users/:id', () => {
    it('should return user', async () => {
      // Arrange
      const user = await createTestUser();
      
      // Act
      const response = await request(app)
        .get(`/users/${user.id}`)
        .set('Authorization', `Bearer ${getTestToken()}`);
      
      // Assert
      expect(response.status).toBe(200);
      expect(response.body.data.id).toBe(user.id);
    });
  });
});
```

## State Management Patterns

### Redux Slice Pattern
```typescript
// userSlice.ts (Keep under 150 lines)
const userSlice = createSlice({
  name: 'user',
  initialState: {
    data: null,
    loading: false,
    error: null
  },
  reducers: {
    setUser: (state, action) => {
      state.data = action.payload;
    },
    clearUser: (state) => {
      state.data = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});
```

### Context Pattern
```typescript
// AuthContext.tsx (Keep under 200 lines)
const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadUser = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          const user = await api.getCurrentUser();
          setUser(user);
        }
      } finally {
        setLoading(false);
      }
    };
    
    loadUser();
  }, []);
  
  const login = async (credentials: LoginCredentials) => {
    const { user, token } = await api.login(credentials);
    localStorage.setItem('token', token);
    setUser(user);
  };
  
  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };
  
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

## Database Patterns

### Migration Template
```sql
-- migrations/001_create_users.sql
-- Keep migrations under 100 lines
BEGIN;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

COMMIT;
```

### Query Patterns
```typescript
// queries.ts (Keep queries under 20 lines each)
export const getUserWithPosts = async (userId: string) => {
  return await db.user.findUnique({
    where: { id: userId },
    include: {
      posts: {
        orderBy: { createdAt: 'desc' },
        take: 10
      }
    }
  });
};
```

## Configuration Patterns

### Environment Config
```typescript
// config.ts (Keep under 100 lines)
export const config = {
  app: {
    port: process.env.PORT || 3000,
    env: process.env.NODE_ENV || 'development',
  },
  database: {
    url: process.env.DATABASE_URL,
    poolSize: parseInt(process.env.DB_POOL_SIZE || '10'),
  },
  auth: {
    jwtSecret: process.env.JWT_SECRET,
    jwtExpiry: process.env.JWT_EXPIRY || '1d',
  },
  redis: {
    url: process.env.REDIS_URL,
  }
};

// Validate required config
const requiredEnvVars = ['DATABASE_URL', 'JWT_SECRET'];
for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
}
```

## Anti-Patterns to Avoid

### ❌ DON'T DO THIS
```typescript
// Huge files
// Files over 800 lines

// Deep nesting
if (condition1) {
  if (condition2) {
    if (condition3) {
      if (condition4) {
        // Too deep!
      }
    }
  }
}

// Magic numbers/strings
setTimeout(() => {}, 3000); // What is 3000?

// Mixed concerns
const UserComponent = () => {
  // API calls in component
  const user = await fetch('/api/user');
  
  // Business logic in component
  const tax = price * 0.08;
  
  // Direct DOM manipulation
  document.getElementById('user').innerHTML = user.name;
};

// God objects
class EverythingService {
  // 50+ methods
  // 2000+ lines
}
```

### ✅ DO THIS INSTEAD
```typescript
// Small, focused files
// Under 500 lines

// Early returns
if (!condition1) return;
if (!condition2) return;
if (!condition3) return;
// Main logic here

// Named constants
const DELAY_MS = 3000;
setTimeout(() => {}, DELAY_MS);

// Separated concerns
const UserComponent = () => {
  const { user } = useUser(); // Hook for data
  const { tax } = useTaxCalculator(price); // Hook for logic
  
  return <div>{user.name}</div>; // Pure rendering
};

// Single responsibility
class UserService { /* User operations only */ }
class TaxService { /* Tax calculations only */ }
```

## Notes for AI Assistants

1. **Always check this file** before writing new code
2. **Keep functions small** - If it's over 50 lines, split it
3. **Use existing patterns** - Don't introduce new patterns without discussion
4. **Prefer composition** - Small, composable functions over large monoliths
5. **Ask if unsure** - Better to ask than to introduce inconsistency