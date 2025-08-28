# Fix Methodology

## Standard Operating Procedure for Code Fixes

This document outlines the standardized methodology for implementing fixes in the Waardhaven AutoIndex codebase. All fixes MUST follow this procedure to ensure consistency, traceability, and quality.

## The Three-Phase Fix Protocol

### 📝 Phase 1: FIX
**Implement the actual code fix**

1. **Create Todo List**
   - Use TodoWrite tool to track all steps
   - Break down the fix into manageable tasks
   - Mark tasks as in_progress when starting

2. **Analyze the Problem**
   - Understand the root cause
   - Identify affected files and components
   - Check for similar issues elsewhere

3. **Implement the Solution**
   - Make ONE fix at a time (never multiple fixes simultaneously)
   - Follow existing code patterns and conventions
   - Ensure backward compatibility when possible

4. **Test the Fix**
   - Run relevant unit tests
   - Verify the fix resolves the issue
   - Check for regression in related areas
   - Test imports and basic functionality

### 📚 Phase 2: DOCS
**Update all relevant documentation**

1. **Create/Update Technical Documentation**
   - Document the fix approach and rationale
   - Add code examples (before/after)
   - Include best practices for future reference

2. **Update Security Documentation** (if applicable)
   - Document security implications
   - Update SECURITY_CONFIGURATION.md if needed
   - Add to compliance checklists

3. **Update Architecture Documentation** (if applicable)
   - Document architectural changes
   - Update ARCHITECTURE_PATTERNS.md if needed
   - Add to pattern library

4. **Update E2E Scan Report**
   - Mark issue as resolved in scan report
   - Update metrics (security score, architecture quality, etc.)
   - Add fix details to tracking section

### 🚀 Phase 3: PUSH
**Commit and push to repository**

1. **Stage Changes**
   ```bash
   git add <modified files>
   git status  # Verify correct files
   ```

2. **Commit with Descriptive Message**
   ```bash
   git commit -m "<TYPE>: <Brief description>
   
   - <Change detail 1>
   - <Change detail 2>
   - <Impact statement>
   
   <Extended description if needed>
   
   🤖 Generated with Claude Code (https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

3. **Push to Repository**
   ```bash
   git push origin main
   ```

## Fix Categories & Commit Types

### Commit Message Prefixes
- `CRITICAL SECURITY FIX:` - Security vulnerabilities
- `SECURITY FIX:` - Security improvements
- `ARCHITECTURE FIX:` - Architecture violations
- `PERFORMANCE FIX:` - Performance optimizations
- `BUG FIX:` - Bug corrections
- `REFACTOR:` - Code refactoring
- `DOCS:` - Documentation only changes

### Priority Levels
1. **CRITICAL** - Production-breaking or security vulnerabilities
2. **HIGH** - Major functionality or architecture issues
3. **MEDIUM** - Performance or maintainability issues
4. **LOW** - Code quality or minor improvements

## Fix Tracking Template

```markdown
#### Fix #N: <Fix Title>
- **Date**: YYYY-MM-DD
- **Priority**: CRITICAL/HIGH/MEDIUM/LOW
- **Category**: Security/Architecture/Performance/Bug
- **Files Modified**:
  - `path/to/file1.py` - Description of changes
  - `path/to/file2.md` - Documentation updates
- **Impact**: <Metric> improved from X to Y
- **Changes**:
  - Specific change 1
  - Specific change 2
  - Test coverage added
```

## Quality Checklist

Before committing any fix, ensure:

### Code Quality
- [ ] Fix addresses the root cause, not symptoms
- [ ] No new warnings or errors introduced
- [ ] Code follows existing patterns and conventions
- [ ] Proper error handling implemented
- [ ] No hardcoded values or magic numbers

### Testing
- [ ] Relevant tests pass
- [ ] Import test successful (`python -c "from module import *"`)
- [ ] No regression in related functionality
- [ ] Edge cases considered

### Documentation
- [ ] Code comments updated (if necessary)
- [ ] Technical documentation created/updated
- [ ] E2E scan report updated
- [ ] Commit message follows format

### Security
- [ ] No credentials exposed
- [ ] No new security vulnerabilities
- [ ] Input validation maintained
- [ ] Authentication/authorization preserved

## Example Fix Flow

### Example: Fixing N+1 Query Pattern

#### Phase 1: FIX
```python
# BEFORE (N+1 Query)
for portfolio in portfolios:
    allocations = db.query(Allocation).filter(
        Allocation.portfolio_id == portfolio.id
    ).all()

# AFTER (Eager Loading)
portfolios = db.query(Portfolio).options(
    selectinload(Portfolio.allocations)
).all()
```

#### Phase 2: DOCS
- Update ARCHITECTURE_PATTERNS.md with N+1 prevention patterns
- Add to performance best practices
- Update E2E scan report

#### Phase 3: PUSH
```bash
git add apps/api/app/services/strategy.py docs/ARCHITECTURE_PATTERNS.md
git commit -m "PERFORMANCE FIX: Resolve N+1 query patterns with eager loading

- Implemented eager loading for portfolio allocations
- Reduced database queries from N+1 to 2
- Performance improved by ~80% for portfolio operations

🤖 Generated with Claude Code (https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

## Common Patterns

### Repository Pattern Implementation
1. Create repository interface
2. Implement concrete repository
3. Refactor router to use repository
4. Update tests with mocked repository

### Security Fix Pattern
1. Identify vulnerability
2. Implement secure solution
3. Add security tests
4. Update security documentation
5. Rotate affected credentials (if applicable)

### Performance Fix Pattern
1. Profile and identify bottleneck
2. Implement optimization
3. Measure improvement
4. Document optimization technique

## Metrics Tracking

Track these metrics after each fix:
- **Security Score**: X/10
- **Architecture Quality**: X/10
- **Performance Score**: X/10
- **Test Coverage**: X%
- **Code Quality**: X/10

## Fix History

Maintain a running log of all fixes in the E2E scan report:
- Fix number and title
- Date completed
- Impact on metrics
- Files modified
- Next priority items

## Guidelines

1. **One Fix at a Time**: Never mix multiple fixes in a single commit
2. **Test Before Push**: Always verify the fix works before committing
3. **Document Everything**: Future developers (including yourself) will thank you
4. **Follow Patterns**: Use existing patterns and conventions
5. **Update Reports**: Keep the E2E scan report current

## Anti-Patterns to Avoid

❌ **DON'T**:
- Mix multiple fixes in one commit
- Push without testing
- Skip documentation updates
- Leave TODO comments without tracking
- Commit commented-out code
- Push with failing tests

✅ **DO**:
- Focus on one issue at a time
- Test thoroughly before pushing
- Update all relevant documentation
- Track TODOs in issues/tickets
- Remove dead code
- Ensure all tests pass

## Continuous Improvement

This methodology should evolve as we learn. When you discover better approaches:
1. Document the improvement
2. Update this methodology
3. Share with the team
4. Apply consistently

Remember: **Consistency and quality over speed**. A well-implemented, documented, and tested fix is worth more than multiple rushed fixes that create new problems.