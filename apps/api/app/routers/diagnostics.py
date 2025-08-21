"""
Diagnostics router facade.
Combines health, metrics, and system status endpoints for backward compatibility.
"""

from fastapi import APIRouter

# Import the modular routers
from .health import router as health_router
from .metrics import router as metrics_router
from .system_status import router as system_router

# Create main diagnostics router
router = APIRouter()

# Include sub-routers without prefixes for backward compatibility
# This maintains the original API paths
router.include_router(
    health_router,
    prefix="",  # No prefix to maintain original paths
    include_in_schema=False  # Hide from schema to avoid duplication
)

router.include_router(
    metrics_router,
    prefix="",  # No prefix to maintain original paths
    include_in_schema=False  # Hide from schema to avoid duplication
)

router.include_router(
    system_router,
    prefix="",  # No prefix to maintain original paths
    include_in_schema=False  # Hide from schema to avoid duplication
)

# Re-export the endpoints with their original paths for backward compatibility
# The actual implementation is in the modular routers above

__all__ = ["router"]
