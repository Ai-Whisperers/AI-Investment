#!/bin/bash

# setup-project.sh - Project setup helper script
# AI NOTE: This script helps set up a new project with optimal structure

echo "🚀 Setting up project with AI-optimized structure..."

# Create directory structure
create_directories() {
    echo "📁 Creating directory structure..."
    
    # Backend directories
    mkdir -p api/{routes,services,models,middleware,utils,config,tests}
    
    # Frontend directories
    mkdir -p web/{components,pages,hooks,services,utils,styles,public}
    mkdir -p web/components/{layout,shared,forms}
    
    # Documentation
    mkdir -p docs/{api,guides,architecture}
    
    # Configuration
    mkdir -p config
    
    echo "✅ Directories created"
}

# Create index files
create_index_files() {
    echo "📝 Creating index files..."
    
    # Backend indexes
    cat > api/routes/index.ts << 'EOF'
// Route exports
export * from './auth.routes';
export * from './user.routes';
EOF

    cat > api/services/index.ts << 'EOF'
// Service exports
export * from './AuthService';
export * from './UserService';
EOF

    cat > api/models/index.ts << 'EOF'
// Model exports
export * from './User.model';
EOF

    # Frontend indexes
    cat > web/components/index.ts << 'EOF'
// Component exports
export * from './shared';
export * from './layout';
export * from './forms';
EOF

    cat > web/hooks/index.ts << 'EOF'
// Hook exports
export * from './useAuth';
export * from './useApi';
EOF

    echo "✅ Index files created"
}

# Create documentation files
create_documentation() {
    echo "📚 Creating documentation..."
    
    cat > PROJECT_INDEX.md << 'EOF'
# Project Index

## Quick Navigation
- API Routes: `/api/routes/`
- Services: `/api/services/`
- Components: `/web/components/`
- Hooks: `/web/hooks/`

## Key Files
- Main API: `/api/index.ts`
- Main Web: `/web/pages/index.tsx`
- Config: `/config/`
EOF

    cat > ARCHITECTURE.md << 'EOF'
# Architecture

## Backend
- Clean Architecture pattern
- Service layer for business logic
- Repository pattern for data access

## Frontend
- Component-based architecture
- Custom hooks for logic
- Services for API calls
EOF

    cat > PATTERNS.md << 'EOF'
# Code Patterns

## Naming
- Components: PascalCase
- Hooks: useXxx
- Services: XxxService
- Files: feature.type.ts

## Structure
- Keep files under 500 lines
- One component per file
- Separate types into .types.ts
EOF

    echo "✅ Documentation created"
}

# Create config files
create_config_files() {
    echo "⚙️ Creating configuration files..."
    
    # TypeScript config
    cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "paths": {
      "@/*": ["./src/*"],
      "@/api/*": ["./api/*"],
      "@/web/*": ["./web/*"]
    }
  }
}
EOF

    # ESLint config
    cat > .eslintrc.json << 'EOF'
{
  "extends": ["eslint:recommended"],
  "rules": {
    "max-lines": ["error", 500],
    "max-lines-per-function": ["error", 50],
    "complexity": ["error", 10]
  }
}
EOF

    # Prettier config
    cat > .prettierrc << 'EOF'
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "printWidth": 80
}
EOF

    echo "✅ Config files created"
}

# Create example env file
create_env_example() {
    echo "🔐 Creating .env.example..."
    
    cat > .env.example << 'EOF'
# Server
PORT=3000
NODE_ENV=development

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Auth
JWT_SECRET=your-secret-key
JWT_EXPIRY=1d

# External Services
API_KEY=your-api-key
REDIS_URL=redis://localhost:6379

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:4000
EOF

    echo "✅ .env.example created"
}

# Create package.json with scripts
create_package_json() {
    echo "📦 Creating package.json..."
    
    cat > package.json << 'EOF'
{
  "name": "project-name",
  "version": "1.0.0",
  "scripts": {
    "dev": "npm run dev:api & npm run dev:web",
    "dev:api": "cd api && nodemon index.ts",
    "dev:web": "cd web && next dev",
    "build": "npm run build:api && npm run build:web",
    "build:api": "cd api && tsc",
    "build:web": "cd web && next build",
    "test": "jest",
    "lint": "eslint . --ext .ts,.tsx",
    "format": "prettier --write .",
    "type-check": "tsc --noEmit"
  }
}
EOF

    echo "✅ package.json created"
}

# Main execution
main() {
    create_directories
    create_index_files
    create_documentation
    create_config_files
    create_env_example
    create_package_json
    
    echo ""
    echo "✨ Project setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.example to .env and fill in values"
    echo "2. Run 'npm install' to install dependencies"
    echo "3. Run 'npm run dev' to start development"
    echo ""
    echo "📖 Check PROJECT_INDEX.md for navigation"
    echo "📐 Check ARCHITECTURE.md for design patterns"
    echo "🎨 Check PATTERNS.md for code conventions"
}

# Run main function
main