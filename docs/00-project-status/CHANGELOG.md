# Changelog

[← Back to Project Status](README.md)

## [2025-01-19] - Documentation Restructuring
### Changed
- Complete documentation reorganization
- Consolidated duplicate files
- Created modular index-based structure
- Separated implemented vs planned features

### Removed
- RIVL belief revision platform docs
- Client insights business strategy docs
- Duplicate API documentation files
- Redundant initialization/scripts folders

## [2025-01-18] - Authentication Integration
### Fixed
- `useAuth must be used within AuthProvider` error
- Dashboard auth context integration
- Missing auth endpoints (`/me`, `/refresh`, `/logout`)

### Added
- Proper JWT token integration
- Auth state synchronization
- Loading states for auth

## [2025-01-17] - Critical Security Fixes
### Fixed
- Data loss prevention with safe upsert logic
- Transaction safety with rollback mechanisms
- Database composite indexes

### Added
- Automatic backup before data modifications
- Redis caching layer with invalidation
- Celery background task processing
- Comprehensive pytest test suite

### Changed
- Standardized to npm across monorepo
- Removed pnpm references

## [2025-01-15] - Clean Architecture
### Added
- Domain layer with business entities
- Infrastructure layer with repositories
- Presentation layer with React components
- SOLID principles implementation

### Changed
- Refactored all UI components
- Separated business logic from UI
- Implemented dependency inversion

## [2025-01-10] - Initial Production Deploy
### Added
- Render.com deployment configuration
- Docker containerization
- Environment variable management
- Basic CI/CD with GitHub Actions

### Known Issues
- Frontend calculations not in backend
- No database migrations system
- Test failures suppressed in CI/CD

---
[← Back to Project Status](README.md)