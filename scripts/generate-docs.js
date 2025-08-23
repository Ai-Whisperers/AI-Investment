#!/usr/bin/env node

/**
 * Documentation Auto-Generation Script
 * Generates documentation from code and OpenAPI spec
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Configuration
const CONFIG = {
  apiUrl: process.env.API_URL || 'http://localhost:8000',
  docsPath: path.join(__dirname, '../docs'),
  outputPaths: {
    openapi: '02-api-reference/generated/openapi.md',
    envVars: '01-getting-started/generated/env-vars.md',
    schema: '03-implementation/backend/generated/schema.md',
    search: '_SEARCH.md',
    glossary: '_GLOSSARY.md'
  }
};

/**
 * Generate API documentation from OpenAPI spec
 */
async function generateApiDocs() {
  console.log(' Generating API documentation...');
  
  try {
    // Fetch OpenAPI spec
    const response = await axios.get(`${CONFIG.apiUrl}/openapi.json`);
    const spec = response.data;
    
    // Generate markdown documentation
    let markdown = `---
title: Auto-generated API Reference
generated: ${new Date().toISOString()}
source: OpenAPI Specification
---

# API Reference (Auto-generated)

## Base URL
\`${spec.servers?.[0]?.url || CONFIG.apiUrl}\`

## Version
${spec.info.version}

## Endpoints

`;

    // Process paths
    for (const [path, methods] of Object.entries(spec.paths || {})) {
      for (const [method, details] of Object.entries(methods)) {
        if (typeof details === 'object') {
          markdown += `### ${method.toUpperCase()} ${path}\n`;
          markdown += `**${details.summary || 'No description'}**\n\n`;
          
          if (details.description) {
            markdown += `${details.description}\n\n`;
          }
          
          // Parameters
          if (details.parameters?.length > 0) {
            markdown += `**Parameters:**\n`;
            details.parameters.forEach(param => {
              markdown += `- \`${param.name}\` (${param.in}): ${param.description || 'No description'}\n`;
            });
            markdown += '\n';
          }
          
          // Request body
          if (details.requestBody) {
            markdown += `**Request Body:**\n\`\`\`json\n`;
            const schema = details.requestBody.content?.['application/json']?.schema;
            if (schema) {
              markdown += JSON.stringify(generateExample(schema), null, 2);
            }
            markdown += `\n\`\`\`\n\n`;
          }
          
          // Responses
          markdown += `**Responses:**\n`;
          for (const [code, response] of Object.entries(details.responses || {})) {
            markdown += `- \`${code}\`: ${response.description}\n`;
          }
          markdown += '\n---\n\n';
        }
      }
    }
    
    // Write to file
    const outputPath = path.join(CONFIG.docsPath, CONFIG.outputPaths.openapi);
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, markdown);
    
    console.log(' API documentation generated');
  } catch (error) {
    console.error(' Failed to generate API docs:', error.message);
  }
}

/**
 * Generate environment variables documentation
 */
function generateEnvVarsDocs() {
  console.log(' Generating environment variables documentation...');
  
  const envVars = [];
  
  // Scan backend .env.example
  const backendEnvPath = path.join(__dirname, '../apps/api/.env.example');
  if (fs.existsSync(backendEnvPath)) {
    const content = fs.readFileSync(backendEnvPath, 'utf8');
    const lines = content.split('\n');
    
    lines.forEach(line => {
      const match = line.match(/^([A-Z_]+)=(.*)$/);
      if (match) {
        envVars.push({
          name: match[1],
          example: match[2],
          location: 'Backend'
        });
      }
    });
  }
  
  // Scan frontend .env.example
  const frontendEnvPath = path.join(__dirname, '../apps/web/.env.example');
  if (fs.existsSync(frontendEnvPath)) {
    const content = fs.readFileSync(frontendEnvPath, 'utf8');
    const lines = content.split('\n');
    
    lines.forEach(line => {
      const match = line.match(/^(NEXT_PUBLIC_[A-Z_]+)=(.*)$/);
      if (match) {
        envVars.push({
          name: match[1],
          example: match[2],
          location: 'Frontend'
        });
      }
    });
  }
  
  // Generate markdown
  let markdown = `---
title: Environment Variables Reference
generated: ${new Date().toISOString()}
source: .env.example files
---

# Environment Variables (Auto-generated)

## Required Variables

| Variable | Location | Example | Description |
|----------|----------|---------|-------------|
`;

  envVars.forEach(env => {
    markdown += `| \`${env.name}\` | ${env.location} | \`${env.example}\` | TODO: Add description |\n`;
  });
  
  markdown += `
## Backend Variables (.env)

\`\`\`bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# Security
SECRET_KEY=your-secret-key-here
ADMIN_TOKEN=admin-access-token

# External APIs
TWELVEDATA_API_KEY=your-api-key
MARKETAUX_API_KEY=your-api-key

# Redis
REDIS_URL=redis://localhost:6379

# Frontend
FRONTEND_URL=http://localhost:3000
\`\`\`

## Frontend Variables (.env)

\`\`\`bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
\`\`\`
`;

  // Write to file
  const outputPath = path.join(CONFIG.docsPath, CONFIG.outputPaths.envVars);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, markdown);
  
  console.log(' Environment variables documentation generated');
}

/**
 * Generate search index
 */
function generateSearchIndex() {
  console.log(' Generating search index...');
  
  const keywords = {};
  
  // Recursively scan all markdown files
  function scanDirectory(dirPath) {
    const files = fs.readdirSync(dirPath);
    
    files.forEach(file => {
      const fullPath = path.join(dirPath, file);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory() && !file.startsWith('.')) {
        scanDirectory(fullPath);
      } else if (file.endsWith('.md')) {
        const content = fs.readFileSync(fullPath, 'utf8');
        const relativePath = path.relative(CONFIG.docsPath, fullPath);
        
        // Extract keywords (headers and bold text)
        const headers = content.match(/^#{1,6}\s+(.+)$/gm) || [];
        headers.forEach(header => {
          const keyword = header.replace(/^#+\s+/, '').toLowerCase();
          if (!keywords[keyword]) {
            keywords[keyword] = [];
          }
          keywords[keyword].push(relativePath);
        });
      }
    });
  }
  
  scanDirectory(CONFIG.docsPath);
  
  // Generate search index markdown
  let markdown = `---
title: Documentation Search Index
generated: ${new Date().toISOString()}
---

# Search Index

## Keywords

`;

  const sortedKeywords = Object.keys(keywords).sort();
  sortedKeywords.forEach(keyword => {
    markdown += `### ${keyword}\n`;
    keywords[keyword].forEach(file => {
      markdown += `- [${file}](${file})\n`;
    });
    markdown += '\n';
  });

  // Write to file
  const outputPath = path.join(CONFIG.docsPath, CONFIG.outputPaths.search);
  fs.writeFileSync(outputPath, markdown);
  
  console.log(' Search index generated');
}

/**
 * Generate example from schema
 */
function generateExample(schema) {
  if (!schema) return {};
  
  if (schema.example) return schema.example;
  
  if (schema.type === 'object' && schema.properties) {
    const example = {};
    for (const [key, prop] of Object.entries(schema.properties)) {
      example[key] = generateExample(prop);
    }
    return example;
  }
  
  if (schema.type === 'array' && schema.items) {
    return [generateExample(schema.items)];
  }
  
  // Default examples by type
  const defaults = {
    string: 'string',
    number: 0,
    integer: 0,
    boolean: false
  };
  
  return defaults[schema.type] || null;
}

/**
 * Main execution
 */
async function main() {
  console.log(' Starting documentation generation...\n');
  
  // Check if API is running
  try {
    await axios.get(`${CONFIG.apiUrl}/health`);
  } catch (error) {
    console.warn('️  API not running, skipping OpenAPI generation');
  }
  
  // Run generators
  await generateApiDocs();
  generateEnvVarsDocs();
  generateSearchIndex();
  
  console.log('\n Documentation generation complete!');
  console.log(' Generated files in:', CONFIG.docsPath);
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = {
  generateApiDocs,
  generateEnvVarsDocs,
  generateSearchIndex
};