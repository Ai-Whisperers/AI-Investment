# AI Context Optimization Tips

## How to Help AI Assistants Work Better

### 1. Request Formatting

#### ✅ GOOD Requests
```
"Edit the UserService.getUser method in /api/services/UserService.ts to add caching"
"Fix the type error at line 45 in components/Dashboard.tsx"
"Add error handling to the login function following our existing patterns"
```

#### ❌ BAD Requests
```
"Make it better"
"Fix the bug"
"Refactor everything"
```

### 2. Provide Context

#### Essential Information
- **File paths**: Always provide exact paths
- **Line numbers**: For specific issues
- **Error messages**: Complete error text
- **Related files**: Mention dependencies
- **Existing patterns**: Reference similar code

#### Example Context
```
"Add a new endpoint for user profile updates.
- Similar to the existing endpoint in /api/routes/userRoutes.ts line 45
- Should follow the same validation pattern as updateUser
- Use the UserService class in /api/services/UserService.ts
- Return format should match our standard API response"
```

### 3. Task Chunking

#### ✅ GOOD: Small, Atomic Tasks
```
Task 1: "Create a UserProfile interface in types/user.ts"
Task 2: "Add a getUserProfile method to UserService"
Task 3: "Create the API endpoint for getUserProfile"
Task 4: "Add tests for the new endpoint"
```

#### ❌ BAD: Large, Vague Tasks
```
"Build a complete user management system with all features"
```

### 4. File Organization for AI

#### Optimal Structure
```
feature/
├── index.ts           # Exports only (5 lines)
├── types.ts           # All types (50-100 lines)
├── service.ts         # Business logic (200-300 lines)
├── api.ts            # API calls (100-150 lines)
├── components/       # UI components
│   ├── List.tsx      # (150 lines)
│   └── Detail.tsx    # (150 lines)
└── hooks/            # Custom hooks
    └── useFeature.ts # (50-100 lines)
```

#### Why This Works
- **Clear boundaries**: Each file has one purpose
- **Predictable locations**: AI knows where to look
- **Manageable sizes**: Can read entire file at once
- **Explicit dependencies**: Clear imports

### 5. Documentation for AI

#### Project-Level Docs
```markdown
# CLAUDE.md (or AI_CONTEXT.md)

## Quick Start
- Main entry point: /api/main.ts
- Frontend entry: /web/pages/index.tsx
- Config files: /config/*

## Common Tasks
- Add API endpoint: See /api/routes/examples.ts
- Add component: Follow /components/Button/*
- Add test: Match pattern in *.test.ts files

## Key Dependencies
- Web: React 18, Next.js 14
- API: Express 4, PostgreSQL
- Testing: Jest, React Testing Library

## Commands
npm run dev     # Start development
npm run test    # Run tests
npm run build   # Build production
```

#### Inline Documentation
```typescript
/**
 * IMPORTANT FOR AI:
 * This service handles all user operations.
 * Always check cache before database.
 * Methods should be under 50 lines.
 * Follow the pattern in TeamService.ts
 */
export class UserService {
  // AI: Dependencies injected via constructor
  constructor(
    private db: Database,    // From /lib/database
    private cache: Cache,    // From /lib/cache
  ) {}
}
```

### 6. Error Messages for AI

#### Helpful Error Context
```typescript
try {
  const result = await api.call();
} catch (error) {
  // AI: This is a known issue with the vendor API
  // Retry logic is in /utils/retry.ts
  // Error codes: 429 = rate limit, 503 = maintenance
  throw new Error(`API call failed: ${error.message}`);
}
```

### 7. Testing Patterns for AI

#### Test File Organization
```typescript
// UserService.test.ts
describe('UserService', () => {
  // AI: Setup uses factories from /test/factories
  // Mock data in /test/fixtures
  
  describe('getUser', () => {
    it('should return cached user if available', async () => {
      // AI: This tests the caching behavior
      // Cache mock is in /test/mocks/cache.ts
    });
  });
});
```

### 8. Index Files Are Critical

#### Create Index Maps
```typescript
// components/index.ts
// AI: This file helps me find all components quickly
export { Button } from './Button';
export { Card } from './Card';
export { Modal } from './Modal';
export { Table } from './Table';
export { Form } from './Form';

// Re-export types
export type { ButtonProps } from './Button/Button.types';
export type { CardProps } from './Card/Card.types';
```

### 9. Configuration for AI

#### Environment Setup
```bash
# .env.example
# AI: Copy this to .env and fill in values

# Required
DATABASE_URL=postgresql://...  # Get from Render dashboard
API_KEY=xxx                    # Get from service provider

# Optional (defaults work)
PORT=3000
LOG_LEVEL=info
```

#### Config Files
```javascript
// config/defaults.js
// AI: These are safe defaults for development
module.exports = {
  api: {
    timeout: 5000,        // 5 seconds
    retries: 3,          
    rateLimit: 100,      // requests per minute
  },
  cache: {
    ttl: 300,            // 5 minutes
    maxSize: 100,        // MB
  }
};
```

### 10. Common Patterns Reference

#### Pattern Library
```typescript
// patterns/examples.ts
// AI: Reference these patterns when writing new code

// API Response Pattern
export const apiResponse = <T>(data: T) => ({
  success: true,
  data,
  timestamp: new Date().toISOString(),
});

// Error Response Pattern
export const errorResponse = (message: string, code?: string) => ({
  success: false,
  error: { message, code },
});

// Validation Pattern
export const validateUser = (data: unknown): User => {
  // AI: Use zod for validation - see /schemas/user.ts
  return userSchema.parse(data);
};
```

### 11. Performance Tips for AI

#### Code Organization for Speed
```typescript
// ✅ FAST: AI can process this quickly
import { userService } from './services';
const user = await userService.getUser(id);

// ❌ SLOW: AI needs to trace through multiple files
import { container } from './ioc';
const service = container.get<IUserService>(TYPES.UserService);
const user = await service.getUser(id);
```

### 12. Migration Guide for AI

#### When Updating Code
```markdown
# MIGRATION.md

## From v1 to v2
- Replace all `fetch()` with `apiClient.get()`
- Update imports: `@/old/path` → `@/new/path`
- Schema changes: `userId` → `user_id`

## Deprecated Patterns
- DON'T use: `class Component extends React.Component`
- DO use: `const Component: React.FC = () => {}`
```

### 13. Quick Reference Card

#### AI Cheat Sheet
```yaml
# File Locations Quick Reference
Components: /components/*
API Routes: /api/routes/*
Services: /api/services/*
Database: /api/models/*
Types: /types/*
Utils: /utils/*
Tests: /**/*.test.ts
Styles: /**/*.styles.ts

# Naming Patterns
Component: PascalCase.tsx
Service: PascalCase.service.ts
Hook: camelCase starting with 'use'
Test: [name].test.ts
Type: PascalCase.types.ts

# Common Imports
API Client: import { api } from '@/lib/api'
Database: import { db } from '@/lib/database'
Types: import type { User } from '@/types'
Utils: import { formatDate } from '@/utils'

# Test Utilities
Mocks: /test/mocks/*
Factories: /test/factories/*
Fixtures: /test/fixtures/*
```

### 14. Debugging Hints for AI

#### Troubleshooting Guide
```markdown
# Common Issues & Solutions

## Type Errors
- Check: /types/* for type definitions
- Fix: Update imports to use `type` keyword

## API Errors
- Check: .env for API_URL
- Check: /api/middleware/cors.ts for CORS
- Fix: Verify token in Authorization header

## Build Errors
- Check: tsconfig.json for paths
- Check: package.json for missing deps
- Fix: Run `npm install` then `npm run build`

## Test Failures
- Check: /test/setup.ts for test config
- Check: Mock implementations in /test/mocks
- Fix: Update snapshots with `npm test -- -u`
```

### 15. Best Practices Summary

#### Do's and Don'ts for Optimal AI Performance

**DO:**
- ✅ Keep files under 500 lines
- ✅ Use descriptive file names
- ✅ Create index files for folders
- ✅ Add brief comments for complex logic
- ✅ Follow consistent patterns
- ✅ Provide example code to follow
- ✅ Include error messages in full
- ✅ Specify exact file paths

**DON'T:**
- ❌ Create files over 800 lines
- ❌ Mix multiple concerns in one file
- ❌ Use complex dependency injection
- ❌ Have deeply nested folders (>4 levels)
- ❌ Use ambiguous names
- ❌ Hide configuration in random places
- ❌ Make AI search for patterns
- ❌ Assume AI knows your custom setup

## Final Note

The key to optimal AI assistance is **predictability and clarity**. The more consistent and well-organized your codebase, the better AI can help you. Think of your codebase as a conversation with future developers (including AI) - make it clear, concise, and easy to navigate.