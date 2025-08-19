# Project Index - Complete Map

## Purpose
This file helps AI assistants quickly locate any part of your codebase without extensive searching.

## Core Modules

### Authentication
- **Location**: `/api/auth/` or `/backend/auth/`
- **Entry Point**: `AuthController.ts` or `auth.py`
- **Key Files**:
  - `AuthService` - Business logic (150 lines)
  - `AuthMiddleware` - JWT validation (80 lines)
  - `UserModel` - User data structure (100 lines)
- **Frontend**: `/components/auth/LoginForm.tsx` (120 lines)

### Data Management
- **Location**: `/api/data/` or `/backend/services/`
- **Entry Point**: `DataService.ts` or `data_service.py`
- **Key Operations**:
  - CRUD operations: `DataRepository` (200 lines)
  - Validation: `DataValidator` (100 lines)
  - Caching: `CacheService` (150 lines)

### API Endpoints
- **Base URL**: `/api/v1/`
- **Documentation**: `/docs/api/`
- **Main Routes**:
  ```
  /auth/*     - Authentication (5 endpoints)
  /users/*    - User management (8 endpoints)
  /data/*     - Data operations (12 endpoints)
  /admin/*    - Admin functions (6 endpoints)
  ```

## Frontend Structure

### Pages/Routes
```
/                    - Home page (LandingPage.tsx, 200 lines)
/dashboard           - Main dashboard (Dashboard.tsx, 350 lines)
/settings            - User settings (Settings.tsx, 250 lines)
/admin               - Admin panel (AdminPanel.tsx, 400 lines)
```

### Shared Components
- **Location**: `/components/shared/`
- **Key Components**:
  - `Button` - Reusable button (80 lines total)
  - `Modal` - Modal dialog (150 lines total)
  - `Table` - Data table (300 lines total)
  - `Form` - Form components (200 lines total)

### State Management
- **Store**: `/store/` or `/state/`
- **Slices**:
  - `authSlice` - Authentication state (100 lines)
  - `dataSlice` - Application data (150 lines)
  - `uiSlice` - UI state (80 lines)

## Database

### Models
- **Location**: `/models/` or `/database/models/`
- **Schema Files**:
  - `User.model` - User schema
  - `Data.model` - Main data schema
  - `Settings.model` - Configuration schema

### Migrations
- **Location**: `/migrations/`
- **Latest**: `v2.0.0_add_indexes.sql`

## Configuration

### Environment Variables
- **Development**: `.env.development`
- **Production**: `.env.production`
- **Required Variables**: See `/docs/ENVIRONMENT.md`

### Build Configuration
- **Frontend**: `webpack.config.js` or `next.config.js`
- **Backend**: `tsconfig.json` or `setup.py`
- **Docker**: `Dockerfile` and `docker-compose.yml`

## Testing

### Test Structure
```
/tests/
├── unit/          - Unit tests (small, focused)
├── integration/   - Integration tests (API, DB)
├── e2e/          - End-to-end tests (full flow)
└── fixtures/     - Test data and mocks
```

### Coverage Goals
- Unit Tests: 80% coverage
- Integration: Critical paths
- E2E: Happy paths + main error cases

## Common Tasks

### Adding a New Feature
1. Check `/PATTERNS.md` for code patterns
2. Look at similar features in this index
3. Follow the same structure

### Debugging Issues
1. Check `/docs/common-issues/`
2. Review relevant service in `/services/`
3. Check error handling in `/middleware/`

### Performance Optimization
1. Profile endpoints in `/api/diagnostics/`
2. Check caching in `/services/cache/`
3. Review database queries in `/models/`

## Quick Commands

```bash
# Development
npm run dev              # Start development server
npm run test            # Run tests
npm run lint            # Check code quality

# Production
npm run build           # Build for production
npm run start           # Start production server

# Database
npm run migrate         # Run migrations
npm run seed            # Seed database
```

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Component | PascalCase | `UserProfile.tsx` |
| Service | PascalCase + Service | `AuthService.ts` |
| Hook | camelCase + use | `useAuth.ts` |
| Utility | camelCase | `formatDate.ts` |
| Test | [name].test | `auth.test.ts` |
| Style | [name].styles | `Button.styles.ts` |

## Dependencies Quick Reference

### Frontend
- Framework: React 18 / Next.js 14
- State: Redux Toolkit / Zustand
- Styling: Tailwind CSS / Styled Components
- Forms: React Hook Form
- HTTP: Axios / Fetch API

### Backend
- Framework: Express / FastAPI
- Database: PostgreSQL / MongoDB
- ORM: Prisma / SQLAlchemy
- Auth: JWT / OAuth2
- Validation: Joi / Pydantic

## Notes for AI Assistants

1. **Always check this index first** before searching
2. **File sizes are approximate** - use as guidelines
3. **Prefer editing existing files** over creating new ones
4. **Follow existing patterns** found in similar modules
5. **Ask for clarification** if structure doesn't match