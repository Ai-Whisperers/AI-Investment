# Context Optimization Template

This template provides the ideal project structure and documentation patterns to help AI assistants work efficiently with your codebase.

## Quick Start

1. Copy this template structure to your project root
2. Adapt the examples to your tech stack
3. Keep files under recommended line counts
4. Use index files liberally

## Directory Structure

```
template-context-improvement/
├── README.md                     # This file
├── PROJECT_INDEX.md             # Complete project map
├── ARCHITECTURE.md              # Design decisions
├── PATTERNS.md                  # Code patterns to follow
├── CONTEXT_TIPS.md              # AI optimization tips
├── docs/
│   ├── quick-reference/         # Quick lookup guides
│   ├── common-issues/           # Known problems & solutions
│   └── examples/                # Code examples
├── backend-template/
│   ├── MODULE_INDEX.md          # Backend module map
│   ├── api/                     # API structure examples
│   ├── services/                # Service layer examples
│   └── models/                  # Data model examples
├── frontend-template/
│   ├── COMPONENT_MAP.md         # Component hierarchy
│   ├── components/              # Component templates
│   ├── hooks/                   # Custom hook examples
│   └── services/                # Frontend service examples
└── scripts/
    └── helpers/                 # Useful scripts
```

## Key Principles

1. **Small, Focused Files**: 200-500 lines ideal, 800 max
2. **Clear Indexes**: Every folder should have an index or map
3. **Consistent Patterns**: Use same patterns throughout
4. **Documentation Near Code**: Keep docs close to what they document
5. **Explicit Over Implicit**: Clear paths and dependencies

## File Size Guidelines

| File Type | Ideal Lines | Max Lines | Why |
|-----------|------------|-----------|-----|
| Component | 50-200 | 400 | Full context understanding |
| Service | 100-300 | 500 | Complete logic flow |
| Documentation | 100-300 | 500 | Quick scanning |
| Config | 20-100 | 200 | Easy reference |
| Types/Interfaces | 50-150 | 300 | Reusable definitions |