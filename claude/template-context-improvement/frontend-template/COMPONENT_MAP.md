# Frontend Component Map

## Component Hierarchy
```
App
├── Layout
│   ├── Header
│   │   ├── Navigation
│   │   ├── UserMenu
│   │   └── SearchBar
│   ├── Sidebar
│   │   ├── MenuItems
│   │   └── QuickActions
│   └── Footer
├── Pages
│   ├── Home
│   │   ├── Hero
│   │   ├── Features
│   │   └── CTA
│   ├── Dashboard
│   │   ├── Stats
│   │   ├── Charts
│   │   └── RecentActivity
│   └── Settings
│       ├── ProfileForm
│       ├── SecuritySettings
│       └── Preferences
└── Shared
    ├── Button
    ├── Modal
    ├── Form
    ├── Table
    └── Card
```

## Component Directory Structure
```
components/
├── layout/              # Layout components
├── pages/              # Page-specific components
├── shared/             # Reusable components
├── forms/              # Form components
├── charts/             # Data visualization
└── providers/          # Context providers
```

## Component File Structure

### Standard Component
```
Button/
├── index.ts            # Public exports (5 lines)
├── Button.tsx          # Component (100-150 lines)
├── Button.types.ts     # TypeScript types (20 lines)
├── Button.styles.ts    # Styles (50 lines)
├── Button.test.tsx     # Tests (150 lines)
└── Button.stories.tsx  # Storybook (100 lines)
```

## Shared Components

### Button
**Location:** `/components/shared/Button`
**Props:** variant, size, disabled, loading, onClick
**Lines:** ~120 total
**Usage:**
```tsx
<Button variant="primary" size="md" onClick={handleClick}>
  Click Me
</Button>
```

### Modal
**Location:** `/components/shared/Modal`
**Props:** isOpen, onClose, title, size
**Lines:** ~180 total
**Usage:**
```tsx
<Modal isOpen={isOpen} onClose={handleClose} title="Confirm">
  <p>Modal content here</p>
</Modal>
```

### Form Components
**Location:** `/components/forms`
```
forms/
├── Input/              # Text input (100 lines)
├── Select/             # Dropdown (120 lines)
├── Checkbox/           # Checkbox (80 lines)
├── Radio/              # Radio button (90 lines)
├── TextArea/           # Text area (100 lines)
└── FormField/          # Field wrapper (150 lines)
```

### Table
**Location:** `/components/shared/Table`
**Props:** columns, data, onSort, onFilter
**Lines:** ~300 total
**Features:** Sorting, filtering, pagination

## Page Components

### Dashboard Components
```
dashboard/
├── StatsCard/          # Metric display (80 lines)
├── Chart/              # Chart wrapper (150 lines)
├── ActivityFeed/       # Recent activities (200 lines)
├── QuickActions/       # Action buttons (100 lines)
└── index.ts           # Exports (10 lines)
```

### Settings Components
```
settings/
├── ProfileForm/        # User profile (200 lines)
├── PasswordChange/     # Password form (150 lines)
├── NotificationPrefs/  # Notifications (180 lines)
├── ThemeSelector/      # Theme picker (100 lines)
└── index.ts           # Exports (10 lines)
```

## Hooks Directory

### Custom Hooks
```
hooks/
├── useAuth.ts          # Authentication (100 lines)
├── useApi.ts           # API calls (150 lines)
├── useForm.ts          # Form handling (200 lines)
├── useDebounce.ts      # Debouncing (30 lines)
├── useLocalStorage.ts  # Local storage (50 lines)
└── index.ts           # Exports (15 lines)
```

## Services Directory

### Frontend Services
```
services/
├── api/
│   ├── client.ts       # Axios instance (50 lines)
│   ├── auth.api.ts     # Auth endpoints (100 lines)
│   ├── user.api.ts     # User endpoints (120 lines)
│   └── index.ts        # Exports (10 lines)
├── storage/
│   ├── localStorage.ts # Local storage (80 lines)
│   ├── sessionStorage.ts # Session storage (80 lines)
│   └── cookies.ts      # Cookie handling (100 lines)
└── utils/
    ├── formatters.ts   # Data formatting (150 lines)
    ├── validators.ts   # Validation (200 lines)
    └── helpers.ts      # Helper functions (100 lines)
```

## State Management

### Context Providers
```
providers/
├── AuthProvider.tsx    # Auth context (150 lines)
├── ThemeProvider.tsx   # Theme context (100 lines)
├── AppProvider.tsx     # App state (200 lines)
└── index.tsx          # Combined provider (50 lines)
```

### Store Structure (if using Redux)
```
store/
├── slices/
│   ├── authSlice.ts    # Auth state (100 lines)
│   ├── userSlice.ts    # User state (120 lines)
│   └── uiSlice.ts      # UI state (80 lines)
├── store.ts           # Store config (50 lines)
└── hooks.ts           # Typed hooks (20 lines)
```

## Routing Structure

### Route Map
```
routes/
├── public/
│   ├── / (Home)
│   ├── /login
│   ├── /register
│   └── /forgot-password
├── protected/
│   ├── /dashboard
│   ├── /profile
│   ├── /settings
│   └── /admin
└── layouts/
    ├── PublicLayout
    ├── ProtectedLayout
    └── AdminLayout
```

## Component Props Reference

### Common Prop Patterns
```typescript
// Size variants
type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// Color variants
type Variant = 'primary' | 'secondary' | 'danger' | 'success';

// Base props
interface BaseProps {
  className?: string;
  children?: React.ReactNode;
  id?: string;
  testId?: string;
}

// Event handlers
interface EventProps {
  onClick?: (e: React.MouseEvent) => void;
  onChange?: (e: React.ChangeEvent) => void;
  onSubmit?: (e: React.FormEvent) => void;
}
```

## Component Communication

### Props Flow
```
App (global state)
  ↓ props
Layout (layout state)
  ↓ props
Page (page state)
  ↓ props
Component (local state)
```

### Event Flow
```
Component (user action)
  ↑ callback
Page (handle event)
  ↑ callback
Layout (update state)
  ↑ dispatch
App (global update)
```

## Performance Optimization

### Code Splitting Points
- Route level (each page)
- Modal components (lazy load)
- Heavy components (charts, editors)
- Admin features (separate bundle)

### Memoization Strategy
- React.memo for pure components
- useMemo for expensive computations
- useCallback for stable callbacks
- Virtualization for long lists

## Testing Strategy

### Component Tests
```typescript
// Button.test.tsx
describe('Button', () => {
  it('renders with text', () => {});
  it('handles click events', () => {});
  it('shows loading state', () => {});
  it('is disabled when prop is true', () => {});
});
```

### Integration Tests
```typescript
// Dashboard.test.tsx
describe('Dashboard Page', () => {
  it('loads user data', () => {});
  it('displays stats cards', () => {});
  it('updates on refresh', () => {});
});
```

## Styling Approach

### Style Organization
```
styles/
├── globals.css         # Global styles
├── variables.css       # CSS variables
├── mixins.scss        # SCSS mixins
└── themes/
    ├── light.css      # Light theme
    └── dark.css       # Dark theme
```

### Component Styles
- CSS Modules for scoping
- Tailwind for utilities
- Styled-components for dynamic
- CSS-in-JS for themes

## Import Aliases

### Common Aliases
```typescript
// tsconfig.json paths
'@/components': './components'
'@/hooks': './hooks'
'@/services': './services'
'@/utils': './utils'
'@/types': './types'
'@/styles': './styles'
```

## Build Output

### Bundle Structure
```
dist/
├── index.html
├── assets/
│   ├── js/
│   │   ├── main.[hash].js
│   │   ├── vendor.[hash].js
│   │   └── [route].[hash].js
│   └── css/
│       └── main.[hash].css
└── images/
```