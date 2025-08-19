# Getting Started

## Quick Navigation

### 🚀 [Quick Start](QUICK_START.md)
5-minute setup to run the application

### 🛠️ [Development Setup](DEVELOPMENT_SETUP.md)
Complete development environment setup

### 🔐 [Environment Variables](ENVIRONMENT_VARIABLES.md)
Required configuration and secrets

## Prerequisites

### Required Software
- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- Redis 5+
- Git

### Recommended Tools
- Docker Desktop
- VS Code
- Postman/Insomnia
- pgAdmin

## Quick Commands

```bash
# Clone repository
git clone https://github.com/waardhaven/autoindex.git
cd waardhaven-autoindex

# Install dependencies
npm install

# Start development
npm run dev

# Run tests
npm test
```

## Project Structure
```
waardhaven-autoindex/
├── apps/api/     # Backend (FastAPI)
├── apps/web/     # Frontend (Next.js)
├── docs/         # Documentation
└── package.json  # Monorepo config
```

## Next Steps
1. [Set up environment](ENVIRONMENT_VARIABLES.md)
2. [Run locally](QUICK_START.md)
3. [Explore API](../api-reference/README.md)
4. [Check features](../features/implemented/README.md)

---
[← Main Documentation](../README.md)