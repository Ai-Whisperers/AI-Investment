# Implementation Documentation

## Overview
Technical implementation details for developers and DevOps engineers.

## Sections

### 🔧 [Backend](backend/README.md)
FastAPI application architecture and implementation
- Architecture patterns
- Database design
- Service layer
- API routers
- Testing

### 🎨 [Frontend](frontend/README.md)
Next.js application with Clean Architecture
- Component structure
- State management
- API integration
- Testing

### 🚀 [Deployment](deployment/README.md)
Infrastructure and deployment configuration
- Docker setup
- Render.com config
- CI/CD pipelines
- Monitoring

## Quick Links

### Backend
- [System Architecture](backend/architecture/README.md)
- [Database Schema](backend/database/README.md)
- [API Services](backend/services/README.md)
- [Providers](backend/providers/README.md)
- [Operations](backend/operations/README.md)
- **[🧪 Testing Strategy](backend/testing/TESTING_STRATEGY.md)** ✅ 95%+ Coverage Required

### Frontend
- [Clean Architecture](frontend/architecture/README.md)
- [Components](frontend/components/README.md)
- [Pages](frontend/pages/README.md)
- [Services](frontend/services/README.md)
- **[🎨 Testing Specification](frontend/testing/FRONTEND_TESTING.md)** ✅ 90%+ Coverage Required

### DevOps
- [Docker Config](deployment/docker/README.md)
- [CI/CD](deployment/ci-cd/README.md)
- [Monitoring](deployment/monitoring/README.md)

### 🔴 Testing (Priority #0)
- **[Backend Testing Strategy](backend/testing/TESTING_STRATEGY.md)** - TDD, 95%+ coverage, financial calculations
- **[Frontend Testing Spec](frontend/testing/FRONTEND_TESTING.md)** - React Testing Library, Playwright, MSW
- **[Critical TODO](../05-roadmap/CRITICAL.md#0-urgent-comprehensive-testing-suite-implementation)** - Testing is blocking all other work

## Technology Stack

### Backend
- FastAPI 0.112.0
- SQLAlchemy 2.0.32
- PostgreSQL
- Redis 5.0.7
- Celery 5.3.4

### Frontend
- Next.js 14.2.32
- React 18.3.1
- TypeScript 5.5.4
- Tailwind CSS 3.4.7
- Recharts

### Infrastructure
- Docker
- Render.com
- GitHub Actions
- Turborepo

---
[← Main Documentation](../README.md)