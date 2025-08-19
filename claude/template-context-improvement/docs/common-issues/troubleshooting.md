# Common Issues & Solutions

## Build Errors

### Module Not Found
```
Error: Cannot find module '@/components/Button'
```
**Solution:**
- Check tsconfig.json paths configuration
- Verify file exists at specified path
- Run `npm install` to ensure dependencies

### Type Errors
```
TS2339: Property 'user' does not exist on type
```
**Solution:**
- Update type definitions in `/types`
- Check for missing imports
- Run `npm run type-check` to find all issues

### Memory Errors
```
FATAL ERROR: JavaScript heap out of memory
```
**Solution:**
```bash
# Increase memory limit
NODE_OPTIONS="--max-old-space-size=4096" npm run build
```

## Runtime Errors

### CORS Issues
```
Access to API has been blocked by CORS policy
```
**Solution:**
- Check FRONTEND_URL in backend .env
- Verify cors middleware configuration
- Ensure correct headers in API requests

### Authentication Errors
```
Error: useAuth must be used within AuthProvider
```
**Solution:**
- Wrap app with AuthProvider in layout/app
- Check context is imported correctly
- Verify provider hierarchy

### Database Connection
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```
**Solution:**
- Check DATABASE_URL in .env
- Verify PostgreSQL is running
- Check Docker containers if using Docker

## API Issues

### 404 Not Found
**Common Causes:**
- Wrong API endpoint URL
- Missing route handler
- Incorrect HTTP method

**Debug Steps:**
1. Check API_URL in frontend .env
2. Verify route exists in backend
3. Check request method (GET/POST/etc)

### 401 Unauthorized
**Common Causes:**
- Missing JWT token
- Expired token
- Invalid token secret

**Solutions:**
- Check token in localStorage/cookies
- Verify JWT_SECRET matches
- Implement token refresh logic

### 500 Internal Server Error
**Debug Steps:**
1. Check backend logs for stack trace
2. Verify database connection
3. Check for missing environment variables
4. Look for unhandled promise rejections

## Testing Issues

### Test Timeout
```
Timeout - Async callback was not invoked
```
**Solution:**
```javascript
// Increase timeout
jest.setTimeout(10000);

// Or per test
test('slow test', async () => {
  // test code
}, 10000);
```

### Snapshot Failures
```
Snapshot test failed
```
**Solution:**
```bash
# Update snapshots
npm test -- -u

# Review changes carefully before committing
```

### Mock Issues
```
Cannot find module '@/mocks/api'
```
**Solution:**
- Check jest.config.js moduleNameMapper
- Verify mock file exists
- Clear jest cache: `npm test -- --clearCache`

## Performance Issues

### Slow Build Times
**Solutions:**
- Use incremental builds
- Implement caching
- Optimize webpack config
- Use esbuild or swc

### Large Bundle Size
**Solutions:**
- Implement code splitting
- Use dynamic imports
- Tree shake unused code
- Analyze with webpack-bundle-analyzer

### Memory Leaks
**Debug Steps:**
1. Use Chrome DevTools Memory Profiler
2. Check for event listener cleanup
3. Review useEffect cleanup functions
4. Look for circular references

## Docker Issues

### Container Won't Start
```
docker: Error response from daemon
```
**Solutions:**
- Check Docker daemon is running
- Verify Dockerfile syntax
- Check port conflicts
- Review docker-compose.yml

### Can't Connect to Container
**Solutions:**
- Check port mapping in docker-compose
- Verify container is running: `docker ps`
- Check container logs: `docker logs <container>`

## Git Issues

### Merge Conflicts
**Resolution Steps:**
1. `git status` to see conflicts
2. Open conflicted files
3. Resolve conflicts manually
4. `git add <resolved-files>`
5. `git commit` to complete merge

### Detached HEAD
```
You are in 'detached HEAD' state
```
**Solution:**
```bash
# Create branch from current state
git checkout -b new-branch

# Or return to branch
git checkout main
```

## Environment Issues

### Missing Environment Variables
**Debug:**
```javascript
// Add validation on startup
const required = ['DATABASE_URL', 'JWT_SECRET'];
for (const key of required) {
  if (!process.env[key]) {
    throw new Error(`Missing required env var: ${key}`);
  }
}
```

### Wrong Environment
**Solution:**
- Check NODE_ENV value
- Verify correct .env file is loaded
- Use dotenv for local development

## Quick Fixes

### Clear All Caches
```bash
# NPM
npm cache clean --force

# Jest
npm test -- --clearCache

# Next.js
rm -rf .next

# Node modules
rm -rf node_modules package-lock.json
npm install
```

### Reset Database
```bash
# Drop and recreate
npm run db:reset

# Fresh migrations
npm run migrate:fresh

# Reseed
npm run seed
```

### Full Reset
```bash
# Nuclear option - reset everything
git clean -fdx
npm install
npm run migrate
npm run seed
npm run dev
```

## Debugging Tools

### Console Debugging
```javascript
// Better console logs
console.log('User:', JSON.stringify(user, null, 2));

// Conditional logging
if (process.env.DEBUG) {
  console.log('Debug info:', data);
}

// Performance timing
console.time('operation');
// ... code ...
console.timeEnd('operation');
```

### Node Debugger
```bash
# Start with debugger
node --inspect index.js

# Break on first line
node --inspect-brk index.js

# Attach VS Code debugger
# F5 with launch.json configured
```

### Network Debugging
```javascript
// Log all API calls
axios.interceptors.request.use(request => {
  console.log('Starting Request:', request);
  return request;
});

axios.interceptors.response.use(response => {
  console.log('Response:', response);
  return response;
});
```