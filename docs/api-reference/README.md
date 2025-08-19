# API Reference

## Overview
Complete API documentation for Waardhaven AutoIndex platform.

## Base Configuration
- **Production**: `https://waardhaven-api.onrender.com`
- **Local**: `http://localhost:8000`
- **Version**: v1 (`/api/v1/`)
- **Auth**: Bearer token (JWT)

## Quick Navigation

### By Category
- [Authentication](authentication/README.md) - User auth & JWT
- [Portfolio](endpoints/portfolio/README.md) - Index management
- [Strategy](endpoints/strategy/README.md) - Strategy config
- [Market Data](endpoints/market/README.md) - Prices & benchmarks
- [News](endpoints/news/README.md) - News & sentiment
- [Tasks](endpoints/tasks/README.md) - Background jobs
- [System](endpoints/system/README.md) - Health & diagnostics

### By Usage
- [Getting Started](integration/GETTING_STARTED.md)
- [Authentication Flow](authentication/FLOW.md)
- [Error Handling](integration/ERROR_HANDLING.md)
- [Rate Limiting](integration/RATE_LIMITING.md)
- [WebSockets](integration/WEBSOCKETS.md) (planned)

## API Structure

```
/api/v1/
├── /auth/          # Authentication
├── /index/         # Portfolio operations
├── /benchmark/     # Market comparison
├── /strategy/      # Strategy config
├── /news/          # News & sentiment
├── /background/    # Async tasks
├── /tasks/         # Task management
├── /diagnostics/   # System health
└── /manual/        # Admin operations
```

## Common Patterns

### Request Headers
```http
Authorization: Bearer <token>
Content-Type: application/json
```

### Response Format
```json
{
  "status": "success",
  "data": {},
  "timestamp": "2025-01-19T12:00:00Z"
}
```

### Error Format
```json
{
  "status": "error",
  "message": "Description",
  "error_code": "ERROR_CODE",
  "detail": {}
}
```

## Quick Links
- [OpenAPI Spec](https://waardhaven-api.onrender.com/openapi.json)
- [Swagger UI](https://waardhaven-api.onrender.com/docs)
- [ReDoc](https://waardhaven-api.onrender.com/redoc)

---
[← Main Documentation](../README.md)