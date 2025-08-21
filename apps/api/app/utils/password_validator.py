"""Password validation utilities."""

import re


class PasswordValidator:
    """Validate password strength and complexity."""

    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str) -> tuple[bool, list[str]]:
        """
        Validate password against security requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Length check
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")

        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must not exceed {cls.MAX_LENGTH} characters")

        # Complexity checks
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            errors.append("Password must contain at least one number")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        # Common password patterns to avoid
        if password.lower() in cls._get_common_passwords():
            errors.append(
                "Password is too common. Please choose a more unique password"
            )

        # Check for sequences
        if cls._has_sequence(password):
            errors.append("Password contains predictable sequences")

        return (len(errors) == 0, errors)

    @staticmethod
    def _get_common_passwords() -> set:
        """Get set of common passwords to check against."""
        return {
            "password",
            "password123",
            "123456",
            "12345678",
            "qwerty",
            "abc123",
            "monkey",
            "1234567",
            "letmein",
            "trustno1",
            "dragon",
            "baseball",
            "111111",
            "iloveyou",
            "master",
            "sunshine",
            "ashley",
            "bailey",
            "passw0rd",
            "shadow",
            "123123",
            "654321",
            "superman",
            "qazwsx",
            "michael",
        }

    @staticmethod
    def _has_sequence(password: str) -> bool:
        """Check if password contains keyboard sequences or repeated characters."""
        sequences = [
            "qwerty",
            "asdfgh",
            "zxcvbn",
            "123456",
            "098765",
            "abcdef",
            "fedcba",
        ]

        password_lower = password.lower()

        # Check for keyboard sequences
        for seq in sequences:
            if seq in password_lower:
                return True

        # Check for repeated characters (e.g., "aaa", "111")
        for i in range(len(password) - 2):
            if password[i] == password[i + 1] == password[i + 2]:
                return True

        return False

    @classmethod
    def get_strength_score(cls, password: str) -> int:
        """
        Calculate password strength score (0-100).

        Args:
            password: Password to score

        Returns:
            Score from 0 (weak) to 100 (strong)
        """
        score = 0

        # Length scoring (max 30 points)
        length_score = min(30, len(password) * 2)
        score += length_score

        # Complexity scoring (max 40 points)
        if re.search(r"[A-Z]", password):
            score += 10
        if re.search(r"[a-z]", password):
            score += 10
        if re.search(r"\d", password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 10

        # Variety scoring (max 20 points)
        unique_chars = len(set(password))
        variety_score = min(20, unique_chars)
        score += variety_score

        # Penalty for common patterns (max -10 points)
        if password.lower() in cls._get_common_passwords():
            score -= 10

        # Bonus for length over minimum (max 10 points)
        if len(password) > 12:
            score += min(10, (len(password) - 12) * 2)

        return max(0, min(100, score))
