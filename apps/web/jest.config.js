/**
 * Jest configuration for Next.js with TypeScript
 * Modular test configuration - avoiding monolithic setup
 */

const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Custom Jest configuration
const customJestConfig = {
  // Test environment
  testEnvironment: 'jest-environment-jsdom',
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  
  // Module name mapper for path aliases
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/app/$1',
    '^@components/(.*)$': '<rootDir>/app/components/$1',
    '^@services/(.*)$': '<rootDir>/app/services/$1',
    '^@hooks/(.*)$': '<rootDir>/app/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/app/utils/$1',
    '^@core/(.*)$': '<rootDir>/app/core/$1',
    
    // Mock CSS modules
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  
  // Test match patterns
  testMatch: [
    '**/__tests__/**/*.(test|spec).[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)',
  ],
  
  // Coverage configuration
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    '!app/**/*.d.ts',
    '!app/**/index.ts',
    '!app/**/types.ts',
    '!app/**/*.stories.tsx',
    '!app/layout.tsx',
    '!app/page.tsx',
  ],
  
  // Coverage thresholds (start low, increase gradually)
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
  },
  
  // Transform ignore patterns
  transformIgnorePatterns: [
    '/node_modules/',
    '^.+\\.module\\.(css|sass|scss)$',
  ],
  
  // Module directories
  modulePaths: ['<rootDir>'],
  
  // Verbose output
  verbose: true,
}

// Export config through Next.js
module.exports = createJestConfig(customJestConfig)