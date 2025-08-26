"""Application use cases for orchestrating business logic.

This package contains use cases that orchestrate domain services
with infrastructure concerns (repositories, external services).
Following Clean Architecture principles.
"""

from .get_technical_analysis import (
    GetTechnicalAnalysisUseCase,
    AssetNotFoundError,
    InsufficientPriceDataError
)
from .auth_use_cases import (
    RegisterUserUseCase,
    LoginUserUseCase,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserInactiveError,
    ValidationError
)

__all__ = [
    'GetTechnicalAnalysisUseCase',
    'AssetNotFoundError',
    'InsufficientPriceDataError',
    'RegisterUserUseCase',
    'LoginUserUseCase',
    'EmailAlreadyExistsError',
    'InvalidCredentialsError',
    'UserInactiveError',
    'ValidationError'
]