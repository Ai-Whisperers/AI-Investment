"""Domain services containing pure business logic.

This package contains domain services that implement business rules
without any infrastructure dependencies (no HTTP, DB, external services).
Following Clean Architecture and Domain-Driven Design principles.
"""

from .technical_analysis_service import (
    TechnicalAnalysisService,
    PriceData,
    TechnicalAnalysisResult
)
from .auth_service import (
    AuthenticationService,
    UserRegistrationData,
    UserCredentials,
    AuthenticatedUser,
    AuthenticationResult
)

__all__ = [
    'TechnicalAnalysisService',
    'PriceData',
    'TechnicalAnalysisResult',
    'AuthenticationService',
    'UserRegistrationData',
    'UserCredentials',
    'AuthenticatedUser',
    'AuthenticationResult'
]