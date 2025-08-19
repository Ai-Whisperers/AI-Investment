# Quick Command Reference

## Development Commands

### Frontend
```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Build for production
npm run preview      # Preview production build
npm run type-check   # TypeScript validation
npm run lint         # ESLint check
npm run format       # Prettier format
```

### Backend
```bash
npm run dev          # Start with nodemon
npm run start        # Production start
npm run test         # Run tests
npm run test:watch   # Watch mode
npm run migrate      # Run DB migrations
npm run seed         # Seed database
```

### Docker
```bash
docker-compose up -d      # Start all services
docker-compose down       # Stop all services
docker-compose logs -f    # View logs
docker-compose exec api sh  # Shell into API container
```

### Database
```bash
# PostgreSQL
psql -U user -d database     # Connect to DB
\dt                          # List tables
\d tablename                 # Describe table
\q                          # Quit

# Migrations
npm run migrate:create       # Create new migration
npm run migrate:up          # Run migrations
npm run migrate:down        # Rollback
```

### Git Workflow
```bash
git checkout -b feature/name  # New feature branch
git add .                     # Stage changes
git commit -m "feat: message" # Commit
git push -u origin branch     # Push branch
git checkout main            # Switch to main
git pull origin main         # Update main
git merge feature/name       # Merge feature
```

### Testing
```bash
npm test                     # Run all tests
npm test -- --coverage       # With coverage
npm test -- UserService      # Specific file
npm test -- --watch          # Watch mode
```

### Debugging
```bash
# Node.js
node --inspect index.js      # Enable debugger
node --inspect-brk index.js  # Break on start

# Chrome DevTools
chrome://inspect             # Open debugger

# VS Code
F5                          # Start debugging
F10                         # Step over
F11                         # Step into
```

### Performance
```bash
# Bundle Analysis
npm run analyze             # Webpack bundle analyzer

# Lighthouse
npm run lighthouse          # Run lighthouse audit

# Load Testing
npm run load-test          # Run k6 tests
```

### Deployment
```bash
# Build & Deploy
npm run build              # Build application
npm run deploy:staging     # Deploy to staging
npm run deploy:production  # Deploy to production

# Monitoring
npm run logs:production    # View production logs
npm run health:check       # Check health endpoints
```

## Environment Variables

### Required
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db
JWT_SECRET=your-secret-key
API_KEY=external-service-key
```

### Optional
```bash
PORT=3000
NODE_ENV=development
LOG_LEVEL=debug
REDIS_URL=redis://localhost:6379
```

## Keyboard Shortcuts

### VS Code
- `Ctrl+P`: Quick file open
- `Ctrl+Shift+P`: Command palette
- `Ctrl+B`: Toggle sidebar
- `Ctrl+` `: Toggle terminal
- `F12`: Go to definition
- `Shift+F12`: Find references
- `Alt+Shift+F`: Format document

### Terminal
- `Ctrl+C`: Stop process
- `Ctrl+D`: Exit/EOF
- `Ctrl+L`: Clear screen
- `Ctrl+R`: Search history
- `Tab`: Autocomplete

## Port Reference

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 4000 | http://localhost:4000 |
| Database | 5432 | postgresql://localhost:5432 |
| Redis | 6379 | redis://localhost:6379 |
| Docs | 6060 | http://localhost:6060 |

## NPM Scripts Reference

```json
{
  "scripts": {
    "dev": "Start development server",
    "build": "Build for production",
    "start": "Start production server",
    "test": "Run tests",
    "lint": "Check code style",
    "format": "Format code",
    "type-check": "TypeScript check",
    "migrate": "Run DB migrations",
    "seed": "Seed database"
  }
}
```