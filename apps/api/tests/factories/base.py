"""
Base factory utilities for test data generation.
Provides common patterns without creating god objects.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random
import string


class BaseFactory:
    """Base class for test data factories."""
    
    @staticmethod
    def random_string(length: int = 10, prefix: str = "") -> str:
        """Generate a random string."""
        chars = string.ascii_lowercase + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(length))
        return f"{prefix}{random_part}" if prefix else random_part
    
    @staticmethod
    def random_email() -> str:
        """Generate a random email address."""
        username = BaseFactory.random_string(8)
        domain = random.choice(['example.com', 'test.com', 'demo.org'])
        return f"{username}@{domain}"
    
    @staticmethod
    def random_float(min_val: float = 0.0, max_val: float = 100.0, decimals: int = 2) -> float:
        """Generate a random float value."""
        value = random.uniform(min_val, max_val)
        return round(value, decimals)
    
    @staticmethod
    def random_date(start_days_ago: int = 365, end_days_ago: int = 0) -> datetime:
        """Generate a random date within a range."""
        start = datetime.now() - timedelta(days=start_days_ago)
        end = datetime.now() - timedelta(days=end_days_ago)
        delta = end - start
        random_days = random.randint(0, delta.days)
        return start + timedelta(days=random_days)