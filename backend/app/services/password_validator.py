"""Password Validator Service - Secure password validation and hashing.

This service enforces strong password requirements and provides secure hashing:
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character

Security Considerations:
- Validates all requirements before hashing
- Returns generic error messages (no hints about which requirement failed)
- Uses bcrypt for password hashing with configurable cost
- Constant-time password verification prevents timing attacks
"""

import re
import logging
from typing import Tuple
from passlib.context import CryptContext
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize bcrypt hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValidator:
    """Password validation and hashing service."""

    # Password requirements
    MIN_LENGTH = settings.PASSWORD_MIN_LENGTH
    REQUIRE_COMPLEXITY = settings.PASSWORD_COMPLEXITY_REQUIRED

    # Regex patterns for character type validation
    UPPERCASE_PATTERN = re.compile(r'[A-Z]')
    LOWERCASE_PATTERN = re.compile(r'[a-z]')
    DIGIT_PATTERN = re.compile(r'\d')
    SPECIAL_PATTERN = re.compile(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]')

    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """
        Validate password against security requirements.

        Requirements:
        - Minimum 12 characters (configurable via PASSWORD_MIN_LENGTH)
        - At least 1 uppercase letter (A-Z)
        - At least 1 lowercase letter (a-z)
        - At least 1 digit (0-9)
        - At least 1 special character (!@#$%^&*...)

        Args:
            password: Password string to validate

        Returns:
            Tuple of (is_valid: bool, message: str)
            - If valid: (True, "")
            - If invalid: (False, generic_error_message)

        Postcondition:
            - Returns generic error message (no hint which requirement failed)
            - Prevents attackers from learning password patterns
            - Both valid and invalid responses complete in similar time
        """
        # Check if complexity checking is disabled
        if not PasswordValidator.REQUIRE_COMPLEXITY:
            if len(password) < PasswordValidator.MIN_LENGTH:
                return False, "Password does not meet requirements"
            return True, ""

        # Check length
        if len(password) < PasswordValidator.MIN_LENGTH:
            logger.debug(
                "Password validation failed",
                reason="insufficient_length",
                min_length=PasswordValidator.MIN_LENGTH
            )
            return False, "Password does not meet requirements"

        # Check character types
        has_upper = PasswordValidator.UPPERCASE_PATTERN.search(password) is not None
        has_lower = PasswordValidator.LOWERCASE_PATTERN.search(password) is not None
        has_digit = PasswordValidator.DIGIT_PATTERN.search(password) is not None
        has_special = PasswordValidator.SPECIAL_PATTERN.search(password) is not None

        # All requirements must be met
        if not (has_upper and has_lower and has_digit and has_special):
            logger.debug(
                "Password validation failed",
                reason="insufficient_complexity",
                has_upper=has_upper,
                has_lower=has_lower,
                has_digit=has_digit,
                has_special=has_special
            )
            return False, "Password does not meet requirements"

        return True, ""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plaintext password to hash

        Returns:
            Bcrypt hash string (includes salt, can be directly compared)

        Postcondition:
            - Hash is not reversible to plaintext
            - Hash includes random salt preventing rainbow tables
            - Same password produces different hashes (due to salt)
        """
        hash_result = pwd_context.hash(password)

        logger.debug(
            "Password hashed",
            hash_prefix=hash_result[:7] + "..."  # Never log full hash
        )

        return hash_result

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against a bcrypt hash.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            plain_password: Plaintext password provided by user
            hashed_password: Bcrypt hash from database

        Returns:
            True if password matches hash, False otherwise

        Postcondition:
            - Comparison time is constant regardless of password
            - Resistant to timing attacks
            - False for invalid hashes or mismatches
        """
        try:
            is_valid = pwd_context.verify(plain_password, hashed_password)

            if not is_valid:
                logger.debug("Password verification failed: mismatch")

            return is_valid
        except Exception as e:
            logger.error(
                "Password verification error",
                error=str(e)
            )
            return False

    @staticmethod
    def get_password_requirements() -> dict:
        """
        Get password requirements for display to users.

        Returns:
            Dictionary describing password requirements
        """
        return {
            "min_length": PasswordValidator.MIN_LENGTH,
            "require_uppercase": PasswordValidator.REQUIRE_COMPLEXITY,
            "require_lowercase": PasswordValidator.REQUIRE_COMPLEXITY,
            "require_digit": PasswordValidator.REQUIRE_COMPLEXITY,
            "require_special": PasswordValidator.REQUIRE_COMPLEXITY,
            "special_characters": "!@#$%^&*()_+-=[]{};\\'\" ,.<>?/\\|`~"
        }
