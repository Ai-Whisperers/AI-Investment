# Frontend Clean Architecture Implementation

## Executive Summary

The Waardhaven AutoIndex frontend implements **Clean Architecture** (also known as Onion Architecture) with strict separation of concerns and dependency inversion. This architecture ensures testability, maintainability, and framework independence.

## Architecture Overview

###  Clean Architecture Pattern Implementation

**Architecture Pattern**: **Clean/Onion Architecture**
- ** Domain Layer**: Pure business entities in `core/domain/entities/`
- ** Application Layer**: Use cases in `core/application/usecases/`
- ** Infrastructure Layer**: External APIs in `core/infrastructure/`
- ** Presentation Layer**: React components in `core/presentation/`

**Dependency Flow**: Follows clean architecture - outer depends on inner, never reverse
**Framework Independence**: Business logic isolated from React, easily testable

## Layer Structure

```
apps/web/app/core/
├── domain/                     # Pure business entities and rules
│   ├── entities/              # Business entities
│   │   ├── DataQuality.ts     # Data quality assessment entity
│   │   ├── Portfolio.ts       # Portfolio business entity
│   │   ├── SystemHealth.ts    # System health entity
│   │   └── User.ts           # User entity
│   ├── repositories/         # Repository interfaces (dependency inversion)
│   │   ├── IAuthRepository.ts
│   │   ├── IDataQualityRepository.ts
│   │   ├── IPortfolioRepository.ts
│   │   └── ISystemHealthRepository.ts
│   └── usecases/             # Business use cases
│       ├── AssessDataQualityUseCase.ts
│       └── MonitorSystemHealthUseCase.ts
│
├── application/              # Application-specific use cases
│   └── usecases/
│       └── auth/             # Authentication use cases
│           ├── GoogleAuthUseCase.ts
│           └── LoginUseCase.ts
│
├── infrastructure/           # External service implementations
│   ├── api/                  # External API clients
│   │   ├── ApiClient.ts      # HTTP client implementation
│   │   └── HttpClient.ts     # Base HTTP client
│   ├── auth/                 # Authentication providers
│   │   ├── GoogleAuthProvider.ts
│   │   └── TokenManager.ts
│   └── repositories/         # Concrete repository implementations
│       ├── AuthRepository.ts
│       ├── DataQualityRepository.ts
│       └── SystemHealthRepository.ts
│
└── presentation/             # React-specific presentation layer
    ├── components/           # Pure UI components
    │   ├── DataQualityIndicator/
    │   ├── SystemHealthIndicator/
    │   ├── ProtectedRoute.tsx
    │   └── auth/
    ├── contexts/             # React contexts
    │   └── AuthContext.tsx
    └── hooks/                # Custom presentation hooks
        ├── useApiRequest.ts
        ├── useDataQuality.ts
        └── useSystemHealth.ts
```

## Component Structure Pattern

Each component follows a consistent structure:

```
Component/
├── index.ts              # Public API export
├── Component.tsx         # UI logic and markup
├── Component.types.ts    # TypeScript interfaces
└── Component.styles.ts   # Styling constants
```

### Example: SystemHealthIndicator

```typescript
// SystemHealthIndicator/index.ts
export { SystemHealthIndicator } from './SystemHealthIndicator';
export type { SystemHealthIndicatorProps } from './SystemHealthIndicator.types';

// SystemHealthIndicator/SystemHealthIndicator.tsx
import { useSystemHealth } from '../../hooks/useSystemHealth';
import { SystemHealthIndicatorProps } from './SystemHealthIndicator.types';
import { STYLES } from './SystemHealthIndicator.styles';

export const SystemHealthIndicator: React.FC<SystemHealthIndicatorProps> = ({
  refreshInterval = 30000
}) => {
  const { health, loading, error } = useSystemHealth(refreshInterval);
  // Pure UI logic only
};

// SystemHealthIndicator/SystemHealthIndicator.types.ts
export interface SystemHealthIndicatorProps {
  refreshInterval?: number;
}

// SystemHealthIndicator/SystemHealthIndicator.styles.ts
export const STYLES = {
  container: "bg-white rounded-lg shadow-sm border p-4",
  healthyStatus: "text-green-600",
  errorStatus: "text-red-600"
} as const;
```

## Benefits Achieved

###  Single Responsibility Principle
- Each layer has one clear purpose
- Components focused only on UI logic
- Business logic isolated in use cases
- External services abstracted behind interfaces

###  Testability
- Business logic testable without UI framework
- Repository interfaces allow easy mocking
- Use cases can be unit tested in isolation
- Components can be tested with mocked dependencies

###  Maintainability
- Changes isolated to relevant layers
- Clear boundaries between concerns
- Framework-independent business logic
- Easy to understand and modify

###  Type Safety
- Full TypeScript compliance across all layers
- Interface-driven development
- Compile-time error detection
- IDE support with full autocomplete

###  Reusability
- Business logic shared across components
- Repository implementations can be swapped
- Use cases reusable in different contexts
- Components focused on presentation only

## Dependency Inversion Implementation

### Repository Pattern

```typescript
// Domain layer - Interface definition
export interface ISystemHealthRepository {
  getHealth(): Promise<SystemHealth>;
  monitorHealth(callback: (health: SystemHealth) => void): void;
}

// Infrastructure layer - Concrete implementation
export class SystemHealthRepository implements ISystemHealthRepository {
  constructor(private apiClient: ApiClient) {}
  
  async getHealth(): Promise<SystemHealth> {
    const response = await this.apiClient.get('/diagnostics/health');
    return SystemHealth.fromApiResponse(response);
  }
}

// Application layer - Use case
export class MonitorSystemHealthUseCase {
  constructor(private repository: ISystemHealthRepository) {}
  
  async execute(): Promise<SystemHealth> {
    return await this.repository.getHealth();
  }
}
```

### Presentation Layer Integration

```typescript
// Custom hook bridges infrastructure to presentation
export const useSystemHealth = (interval: number) => {
  const repository = useMemo(() => new SystemHealthRepository(apiClient), []);
  const useCase = useMemo(() => new MonitorSystemHealthUseCase(repository), [repository]);
  
  const [health, setHealth] = useState<SystemHealth | null>(null);
  
  useEffect(() => {
    const monitor = async () => {
      const result = await useCase.execute();
      setHealth(result);
    };
    
    monitor();
    const timer = setInterval(monitor, interval);
    return () => clearInterval(timer);
  }, [useCase, interval]);
  
  return { health, loading: !health };
};
```

## Page-Level Architecture

### Dashboard Implementation

The dashboard page demonstrates the clean architecture pattern:

```
dashboard/
├── page.tsx                  # Main page component (173 lines, 78% reduction)
├── components/               # Page-specific components
│   ├── DashboardMetrics.tsx  # Performance metrics display
│   ├── PortfolioChart.tsx    # Main chart component
│   ├── AllocationChart.tsx   # Pie chart for allocations
│   ├── ChartControls.tsx     # Chart control panel
│   ├── SimulationPanel.tsx   # Investment simulation
│   └── DashboardLayout.tsx   # Layout wrapper
├── hooks/                    # Business logic hooks
│   ├── useDashboardData.ts   # Data fetching logic
│   ├── useSimulation.ts      # Simulation state management
│   └── useChartControls.ts   # Chart control state
└── providers/                # Context management
    └── DashboardProvider.tsx # Dashboard context
```

### Before vs After Refactoring

**Before Refactoring**: 797 lines in single file
- Mixed UI, business logic, API calls, and styling
- Difficult to test and maintain
- Tight coupling between concerns

**After Refactoring**: 173 lines in main component
- Clear separation of concerns
- Business logic extracted to hooks
- UI components focused on presentation
- Easy to test and maintain

## Frontend-Backend Integration

### Type-Safe API Communication

```typescript
// Infrastructure layer - API client
export class ApiClient {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: this.getAuthHeaders(),
    });
    return response.json();
  }
}

// Domain layer - Entity
export class Portfolio {
  constructor(
    private readonly id: string,
    private readonly assets: Asset[],
    private readonly performance: PerformanceMetrics
  ) {}
  
  static fromApiResponse(data: PortfolioApiResponse): Portfolio {
    return new Portfolio(
      data.id,
      data.assets.map(Asset.fromApiResponse),
      PerformanceMetrics.fromApiResponse(data.performance)
    );
  }
}
```

## State Management Strategy

### React Query Integration

```typescript
// Custom hook with React Query
export const usePortfolioData = () => {
  const repository = useMemo(() => new PortfolioRepository(apiClient), []);
  
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: () => repository.getPortfolio(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
```

### Context for Cross-Cutting Concerns

```typescript
// Authentication context
export const AuthContext = createContext<AuthContextValue | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

## Performance Optimizations

### Memoization Strategy

```typescript
// Component memoization
export const DashboardMetrics = memo<DashboardMetricsProps>(({ data }) => {
  const metrics = useMemo(() => calculateMetrics(data), [data]);
  return <MetricsDisplay metrics={metrics} />;
});

// Hook optimization
export const useDashboardData = () => {
  const repository = useMemo(() => new DashboardRepository(apiClient), []);
  const useCase = useMemo(() => new GetDashboardDataUseCase(repository), [repository]);
  // ... rest of hook
};
```

### Lazy Loading

```typescript
// Component lazy loading
const AdvancedAnalytics = lazy(() => import('./components/AdvancedAnalytics'));

// Route-based code splitting
const DashboardPage = lazy(() => import('./dashboard/page'));
```

## Testing Strategy

### Unit Testing Entities

```typescript
describe('Portfolio Entity', () => {
  it('should calculate total value correctly', () => {
    const portfolio = new Portfolio(assets, performance);
    expect(portfolio.getTotalValue()).toBe(expectedValue);
  });
});
```

### Testing Use Cases

```typescript
describe('MonitorSystemHealthUseCase', () => {
  it('should return health status', async () => {
    const mockRepository = {
      getHealth: jest.fn().mockResolvedValue(mockHealth),
    };
    const useCase = new MonitorSystemHealthUseCase(mockRepository);
    
    const result = await useCase.execute();
    expect(result).toEqual(mockHealth);
  });
});
```

### Component Testing

```typescript
describe('SystemHealthIndicator', () => {
  it('should display health status', () => {
    const mockHealth = new SystemHealth('healthy', 99);
    jest.mocked(useSystemHealth).mockReturnValue({ health: mockHealth });
    
    render(<SystemHealthIndicator />);
    expect(screen.getByText('healthy')).toBeInTheDocument();
  });
});
```

## Conclusion

The Waardhaven AutoIndex frontend successfully implements Clean Architecture principles, resulting in:

- **Maintainable Code**: Clear separation of concerns
- **Testable Design**: Framework-independent business logic
- **Type Safety**: Full TypeScript compliance
- **Performance**: Optimized rendering and state management
- **Scalability**: Easy to extend and modify

This architecture provides a solid foundation for continued development and ensures the frontend can scale with business requirements while maintaining code quality and developer productivity.